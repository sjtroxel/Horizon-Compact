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
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from horizon_compact.experiment import OFF_SUBJECT_EXPERIMENTS, Experiment
from horizon_compact.sweep.classify import MAX_MODEL_ATTEMPTS
from horizon_compact.sweep.prompt import build_tool, menu_order_seed, render_prompt
from horizon_compact.sweep.spend import estimate_input_tokens, worst_case_attempt_usd


class SweepRefusal(Exception):
    """The sweep or session was refused before any model call. The message says why."""


# 3 (Phase 4 code half, section 4.1): ``repeats`` is a mapping, scenario id to count. A version-2 manifest,
# whose ``repeats`` is one int for every scenario, is still read (``manifest_repeats``) and still resumed.
MANIFEST_VERSION = 3
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
    repeats: Mapping[str, int]  # scenario id to its count, in scenario order
    seed: int
    content_hash: str
    runs: tuple[RunSpec, ...]
    scenarios: tuple[str, ...] = ()
    templates: tuple[str, ...] = ()

    def repeats_text(self) -> str:
        """``3`` when every scenario has the same count, else ``s1=20, s2=10`` (for people reading output)."""
        return repeats_text(self.repeats)

    def manifest(self) -> dict[str, Any]:
        """Deterministic, with no timestamp: a later session recomputes it and refuses unless it matches
        exactly."""
        return {
            "manifest_version": MANIFEST_VERSION,
            "sweep_id": self.sweep_id,
            "label": self.label,
            "experiment": self.experiment,
            "model_key": self.model_key,
            "repeats": dict(self.repeats),
            "seed": self.seed,
            "content_hash": self.content_hash,
            "scenarios": list(self.scenarios),
            "templates": list(self.templates),
            "runs": [asdict(run) for run in self.runs],
        }


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def repeats_text(repeats: Mapping[str, int]) -> str:
    counts = set(repeats.values())
    if len(counts) == 1:
        return str(next(iter(counts)))
    return ", ".join(f"{scenario}={count}" for scenario, count in repeats.items())


def normalize_repeats(
    repeats: int | Mapping[str, int], scenario_ids: Sequence[str]
) -> dict[str, int]:
    """One count per selected scenario, in scenario order. An int means the same count everywhere. A mapping
    must name every selected scenario and no other, each at least 1: a missing or extra scenario is refused
    naming it, never filled in or ignored."""
    if not isinstance(repeats, Mapping):
        if isinstance(repeats, bool) or repeats < 1:
            raise ValueError("repeats must be at least 1")
        return dict.fromkeys(scenario_ids, repeats)
    missing = [sid for sid in scenario_ids if sid not in repeats]
    if missing:
        raise SweepRefusal(f"the repeats name no count for scenario(s) {missing}")
    extra = [sid for sid in repeats if sid not in scenario_ids]
    if extra:
        raise SweepRefusal(
            f"the repeats name scenario(s) {extra} that this plan does not run "
            f"(it runs {list(scenario_ids)})"
        )
    for sid in scenario_ids:
        count = repeats[sid]
        if isinstance(count, bool) or not isinstance(count, int) or count < 1:
            raise ValueError(
                f"repeats for {sid} must be a whole number of at least 1, not {count!r}"
            )
    return {sid: repeats[sid] for sid in scenario_ids}


def repeats_from_json(data: Any) -> dict[str, int]:
    """The mapping in a ``repeats.json`` record (a ``scenarios`` list of ``scenario_id`` and ``repeats``) or
    in a plain ``{"s1": 20, "s2": 10}``. Nothing else is accepted, and nothing is converted: a count of
    ``20.7``, ``"20"`` or ``true`` is refused, never read as 20 or 1."""
    if isinstance(data, dict) and isinstance(data.get("scenarios"), list):
        try:
            pairs = [(item["scenario_id"], item["repeats"]) for item in data["scenarios"]]
        except (KeyError, TypeError) as exc:
            raise SweepRefusal(
                f"the repeats record is not in the form repeats.json has: {exc!r}"
            ) from exc
    elif isinstance(data, dict) and data:
        pairs = list(data.items())
    else:
        raise SweepRefusal(
            "the repeats must be a repeats.json record or a mapping of scenario id to a count"
        )
    counts: dict[str, int] = {}
    for scenario_id, count in pairs:
        if not isinstance(scenario_id, str):
            raise SweepRefusal(f"a scenario id in the repeats is {scenario_id!r}, not a name")
        if isinstance(count, bool) or not isinstance(count, int):
            raise SweepRefusal(f"the count for {scenario_id} is {count!r}, not a whole number")
        if scenario_id in counts:
            raise SweepRefusal(f"the repeats name {scenario_id} twice")
        counts[scenario_id] = count
    return counts


def manifest_repeats(manifest: Mapping[str, Any]) -> dict[str, int]:
    """A manifest's repeats as a mapping, from any version: version 3 stores the mapping; version 2 stored one
    int for every scenario, which is read as that count everywhere."""
    stored = manifest["repeats"]
    if isinstance(stored, Mapping):
        return {str(k): int(v) for k, v in stored.items()}
    scenarios = list(manifest.get("scenarios") or [])
    if not scenarios:  # a manifest from before scenarios were listed
        scenarios = list(dict.fromkeys(run["scenario_id"] for run in manifest["runs"]))
    return dict.fromkeys(scenarios, int(stored))


def make_sweep_id(
    content_hash: str,
    model_key: str,
    label: str,
    repeats: int | Mapping[str, int],
    seed: int,
    scenarios: Sequence[str] = (),
    templates: Sequence[str] = (),
) -> str:
    """The selection is part of the id, so two plans that differ only in which scenarios or templates they
    cover are two sweeps, never one sweep refused on resume. So is a plan that differs in one scenario's
    count. The same count everywhere hashes as that one number, whether it came as an int or as a mapping, so
    a sweep keeps the id it had before counts could differ."""
    digest = _sha256(
        "|".join(
            [
                content_hash,
                model_key,
                label,
                str(repeats) if isinstance(repeats, int) else _repeats_for_id(repeats, scenarios),
                str(seed),
                ",".join(scenarios),
                ",".join(templates),
            ]
        )
    )
    return f"{label}-{model_key}-{digest[:8]}"


def _repeats_for_id(counts: Mapping[str, int], scenarios: Sequence[str]) -> str:
    ordered = [counts[sid] for sid in scenarios] if scenarios else list(counts.values())
    if len(set(ordered)) == 1:
        return str(ordered[0])
    return ",".join(f"{sid}={counts[sid]}" for sid in scenarios)


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
    repeats: int | Mapping[str, int],
    seed: int,
    scenarios: Sequence[str] | None = None,
    templates: Sequence[str] | None = None,
    official: bool = False,
) -> SweepPlan:
    experiment.model(model_key)  # an unknown model is an error naming the choices
    scenario_ids = _select(scenarios, list(experiment.scenarios), "scenario")
    counts = normalize_repeats(repeats, scenario_ids)
    template_ids = _select(templates, list(experiment.templates), "template")
    if not official:
        check_not_official_rules(experiment, model_key, template_ids)
    sweep_id = make_sweep_id(
        experiment.content_hash, model_key, label, counts, seed, scenario_ids, template_ids
    )
    runs: list[RunSpec] = []
    for scenario_id in scenario_ids:
        for objective in experiment.objectives:
            for template_id in template_ids:
                for repeat in range(counts[scenario_id]):
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
        repeats=counts,
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
