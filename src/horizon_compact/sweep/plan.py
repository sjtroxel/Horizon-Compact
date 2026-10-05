"""Expand a sweep into run specs (Phase 1 IMPLEMENTATION doc section 6.2).

Ids are derived, never drawn: re-launching the same sweep yields the same ``sweep_id``, which is what lets
it resume. The run order is shuffled once by ``random.Random(seed)`` and kept in the manifest, so a sweep
stopped early is a balanced subset (planning/07 section 11). The preflight bound refuses a sweep that could
pass its cap (section 6.5).
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import asdict, dataclass
from typing import Any

from horizon_compact.experiment import Experiment
from horizon_compact.sweep.classify import MAX_MODEL_ATTEMPTS
from horizon_compact.sweep.prompt import build_tool, menu_order_seed, render_prompt
from horizon_compact.sweep.spend import estimate_input_tokens, worst_case_attempt_usd


class SweepRefusal(Exception):
    """The sweep or session was refused before any model call. The message says why."""


# Phase 1 has one wording per objective; Phase 2 brings the variants.
WORDING_ID = "w1"
MANIFEST_VERSION = 1


@dataclass(frozen=True)
class RunSpec:
    run_id: str
    scenario_id: str
    objective_id: str
    wording_id: str
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
            "runs": [asdict(run) for run in self.runs],
        }


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_sweep_id(content_hash: str, model_key: str, label: str, repeats: int, seed: int) -> str:
    digest = _sha256("|".join([content_hash, model_key, label, str(repeats), str(seed)]))
    return f"{label}-{model_key}-{digest[:8]}"


def make_run_id(
    sweep_id: str, scenario_id: str, objective_id: str, wording_id: str, repeat: int
) -> str:
    digest = _sha256("|".join([sweep_id, scenario_id, objective_id, wording_id, str(repeat)]))
    return f"r-{digest[:12]}"


def build_plan(
    experiment: Experiment, *, model_key: str, label: str, repeats: int, seed: int
) -> SweepPlan:
    experiment.model(model_key)  # an unknown model is an error naming the choices
    if repeats < 1:
        raise ValueError("repeats must be at least 1")
    sweep_id = make_sweep_id(experiment.content_hash, model_key, label, repeats, seed)
    scenario_id = experiment.scenario.id
    runs: list[RunSpec] = []
    for objective in experiment.objectives:
        for repeat in range(repeats):
            run_id = make_run_id(sweep_id, scenario_id, objective.id, WORDING_ID, repeat)
            runs.append(
                RunSpec(
                    run_id=run_id,
                    scenario_id=scenario_id,
                    objective_id=objective.id,
                    wording_id=WORDING_ID,
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
    )


def worst_case_per_attempt_usd(experiment: Experiment, plan: SweepPlan) -> float:
    """The most one attempt can cost: the longest rendered prompt at full price, and the whole output
    allowance."""
    scenario = experiment.scenario
    tool = build_tool(scenario)
    objectives = {o.id: o for o in experiment.objectives}
    largest = 0
    for run in plan.runs:
        prompt = render_prompt(experiment, objectives[run.objective_id], run.menu_order_seed)
        largest = max(largest, estimate_input_tokens(prompt.system, prompt.user, tool))
    prices = experiment.model(plan.model_key).prices
    return worst_case_attempt_usd(largest, scenario.max_tokens, prices)


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
