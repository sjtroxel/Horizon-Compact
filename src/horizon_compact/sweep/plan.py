"""Expand a sweep into run specs (Phase 1 IMPLEMENTATION doc section 6.2).

Ids are derived, never drawn: re-launching the same sweep yields the same ``sweep_id``, which is what lets
it resume. The run order is shuffled once by ``random.Random(seed)`` and kept in the manifest, so a sweep
stopped early is a balanced subset (planning/07 section 11). The preflight bound refuses a sweep that could
pass its cap (section 6.5).

Phase 2.5 (its IMPLEMENTATION doc sections 8.4 and 9): a plan crosses scenarios, objectives, wording
templates and repeats, and a plan that is not official is refused in three cases, before any call: it
includes the sealed template; it has a stated objective while the experiment's sealed template is not drawn
yet; it would run real content on a model that is not the development model. The refusals are code, not
memory.
"""

from __future__ import annotations

import hashlib
import random
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Any

from horizon_compact.experiment import OFF_SUBJECT_EXPERIMENTS, Experiment
from horizon_compact.sweep.classify import MAX_MODEL_ATTEMPTS
from horizon_compact.sweep.prompt import build_tool, menu_order_seed, render_prompt
from horizon_compact.sweep.spend import estimate_input_tokens, worst_case_attempt_usd


class SweepRefusal(Exception):
    """The sweep or session was refused before any model call. The message says why."""


MANIFEST_VERSION = 2
DEVELOPMENT_ROLE = "development"


@dataclass(frozen=True)
class RunSpec:
    run_id: str
    scenario_id: str
    objective_id: str
    wording_id: str  # the wording template's id, w1 to w3
    repeat: int
    menu_order_seed: int


@dataclass(frozen=True)
class SweepPlan:
    sweep_id: str
    label: str
    experiment: str
    model_key: str
    repeats: int
    seed: int
    content_hash: str
    runs: tuple[RunSpec, ...]
    scenarios: tuple[str, ...] = ()
    templates: tuple[str, ...] = ()

    def manifest(self) -> dict[str, Any]:
        """Deterministic, with no timestamp: a later session recomputes it and refuses unless it matches
        exactly."""
        return {
            "manifest_version": MANIFEST_VERSION,
            "sweep_id": self.sweep_id,
            "label": self.label,
            "experiment": self.experiment,
            "model_key": self.model_key,
            "repeats": self.repeats,
            "seed": self.seed,
            "content_hash": self.content_hash,
            "scenarios": list(self.scenarios),
            "templates": list(self.templates),
            "runs": [asdict(run) for run in self.runs],
        }


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_sweep_id(
    content_hash: str,
    model_key: str,
    label: str,
    repeats: int,
    seed: int,
    scenarios: Sequence[str] = (),
    templates: Sequence[str] = (),
) -> str:
    """The selection is part of the id, so two plans that differ only in which scenarios or templates they
    cover are two sweeps, never one sweep refused on resume."""
    digest = _sha256(
        "|".join(
            [
                content_hash,
                model_key,
                label,
                str(repeats),
                str(seed),
                ",".join(scenarios),
                ",".join(templates),
            ]
        )
    )
    return f"{label}-{model_key}-{digest[:8]}"


def make_run_id(
    sweep_id: str, scenario_id: str, objective_id: str, wording_id: str, repeat: int
) -> str:
    digest = _sha256("|".join([sweep_id, scenario_id, objective_id, wording_id, str(repeat)]))
    return f"r-{digest[:12]}"


def _select(wanted: Sequence[str] | None, available: Sequence[str], what: str) -> tuple[str, ...]:
    if wanted is None:
        return tuple(available)
    unknown = [name for name in wanted if name not in available]
    if unknown:
        raise SweepRefusal(f"unknown {what} {unknown}; the choices are: {', '.join(available)}")
    if len(set(wanted)) != len(wanted):
        raise SweepRefusal(f"{what} named twice in {list(wanted)}")
    return tuple(name for name in available if name in wanted)


def check_not_official_rules(
    experiment: Experiment, model_key: str, templates: Sequence[str]
) -> None:
    """The three refusals for a plan that is not official (Phase 2.5 IMPLEMENTATION doc section 8.4).

    ``sealed_template`` is ``None`` for an experiment with no sealed template (the placeholder), ``""`` for
    one whose template is not drawn yet, otherwise the drawn template's id.
    """
    sealed = experiment.sealed_template
    if sealed and sealed in templates:
        raise SweepRefusal(
            f"the sealed template ({sealed}) is never part of a decision prompt before the official sweep"
        )
    if sealed == "" and any(not o.is_baseline for o in experiment.objectives):
        raise SweepRefusal(
            f"{experiment.name}'s sealed template is not drawn yet; until it is, any template might be "
            "the sealed one, so no decision run is allowed"
        )
    if (
        experiment.name not in OFF_SUBJECT_EXPERIMENTS
        and experiment.model(model_key).role != DEVELOPMENT_ROLE
    ):
        raise SweepRefusal(
            f"{model_key} is not the development model: real content runs only on the development "
            f"model until the official sweep ({experiment.name} is not off the subject)"
        )


def build_plan(
    experiment: Experiment,
    *,
    model_key: str,
    label: str,
    repeats: int,
    seed: int,
    scenarios: Sequence[str] | None = None,
    templates: Sequence[str] | None = None,
    official: bool = False,
) -> SweepPlan:
    experiment.model(model_key)  # an unknown model is an error naming the choices
    if repeats < 1:
        raise ValueError("repeats must be at least 1")
    scenario_ids = _select(scenarios, list(experiment.scenarios), "scenario")
    template_ids = _select(templates, list(experiment.templates), "template")
    if not official:
        check_not_official_rules(experiment, model_key, template_ids)
    sweep_id = make_sweep_id(
        experiment.content_hash, model_key, label, repeats, seed, scenario_ids, template_ids
    )
    runs: list[RunSpec] = []
    for scenario_id in scenario_ids:
        for objective in experiment.objectives:
            for template_id in template_ids:
                for repeat in range(repeats):
                    run_id = make_run_id(sweep_id, scenario_id, objective.id, template_id, repeat)
                    runs.append(
                        RunSpec(
                            run_id=run_id,
                            scenario_id=scenario_id,
                            objective_id=objective.id,
                            wording_id=template_id,
                            repeat=repeat,
                            menu_order_seed=menu_order_seed(seed, run_id),
                        )
                    )
    random.Random(seed).shuffle(runs)
    return SweepPlan(
        sweep_id=sweep_id,
        label=label,
        experiment=experiment.name,
        model_key=model_key,
        repeats=repeats,
        seed=seed,
        content_hash=experiment.content_hash,
        runs=tuple(runs),
        scenarios=scenario_ids,
        templates=template_ids,
    )


def worst_case_per_attempt_usd(experiment: Experiment, plan: SweepPlan) -> float:
    """The most one attempt can cost: for each run, its rendered prompt at full price and its scenario's whole
    output allowance; the largest of them."""
    objectives = {o.id: o for o in experiment.objectives}
    prices = experiment.model(plan.model_key).prices
    tools = {sid: build_tool(experiment.get_scenario(sid)) for sid in plan.scenarios}
    worst = 0.0
    for run in plan.runs:
        scenario = experiment.get_scenario(run.scenario_id)
        prompt = render_prompt(
            experiment,
            scenario,
            objectives[run.objective_id],
            run.wording_id,
            run.menu_order_seed,
        )
        tokens = estimate_input_tokens(prompt.system, prompt.user, tools[run.scenario_id])
        worst = max(worst, worst_case_attempt_usd(tokens, scenario.max_tokens, prices))
    return worst


def preflight_bound_usd(experiment: Experiment, plan: SweepPlan) -> float:
    """Runs x 3 attempts x one attempt's worst case. A sweep whose bound passes its cap is refused at the
    start."""
    return round(
        len(plan.runs) * MAX_MODEL_ATTEMPTS * worst_case_per_attempt_usd(experiment, plan), 4
    )


def check_preflight(experiment: Experiment, plan: SweepPlan, cap_usd: float) -> float:
    """Refuse to start above the cap. Returns the bound."""
    bound = preflight_bound_usd(experiment, plan)
    if bound > cap_usd:
        raise SweepRefusal(
            f"the worst case for {len(plan.runs)} runs is ${bound:.2f}, above the cap of ${cap_usd:.2f}; "
            "lower the repeats, or raise the cap with --cap-usd (above $5 also needs --allow-over-cap)"
        )
    return bound
