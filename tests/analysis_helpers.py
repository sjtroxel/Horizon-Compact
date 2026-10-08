"""Records for the analysis tests, written by the runner itself so the format cannot drift (Phase 3 doc 18).

``run_company`` plays a scripted provider through ``run_session`` on the real company scenario files, which
writes under ``development/company/<sweep>/``: exactly the place the reader must refuse. ``relocate`` copies a
sweep's objects to a prefix the reader accepts, so a test can score a run as it would arrive from a pilot.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from horizon_compact.experiment import Experiment, load_experiment
from horizon_compact.sweep.plan import SweepPlan, build_plan
from horizon_compact.sweep.runner import sweep_prefix
from horizon_compact.sweep.store import LocalStore
from sweep_helpers import ScriptedProvider, raw_ok, session

DEVELOPMENT_MODEL = "gpt-oss-openrouter"
PILOT_PREFIX = "pilot-test/"


def memo() -> str:
    return " ".join(["word"] * 160)


def decision(amounts: dict[str, Any], **choice: str) -> dict[str, Any]:
    """A tool input in the shape the scenarios ask for: amounts, an optional choice, a memo."""
    return {"amounts": amounts, **choice, "memo": memo()}


def run_company(
    tmp_path: Path, scenario_id: str, inputs: Sequence[dict[str, Any]], *, repeats: int = 1
) -> tuple[Experiment, SweepPlan, LocalStore]:
    """One wording (w1) of one company scenario; the n-th call returns ``inputs[n-1]``."""
    exp = load_experiment("company")
    plan = build_plan(
        exp,
        model_key=DEVELOPMENT_MODEL,
        label="analysis-test",
        repeats=repeats,
        seed=3,
        scenarios=[scenario_id],
        templates=["w1"],
    )
    assert len(plan.runs) == len(inputs)
    store = LocalStore(tmp_path)
    provider = ScriptedProvider(
        lambda n, request: raw_ok(request, tool_input=inputs[(n - 1) % len(inputs)])
    )
    session(exp, plan, provider, store)
    return exp, plan, store


def relocate(store: LocalStore, plan: SweepPlan, to_prefix: str = PILOT_PREFIX) -> str:
    """Copy one development sweep's objects under ``to_prefix``; returns the new sweep prefix."""
    old = sweep_prefix(plan.experiment, plan.sweep_id)
    new = f"{to_prefix}{plan.experiment}/{plan.sweep_id}/"
    for key in store.list_keys(old):
        text = store.get(key)
        assert text is not None
        assert store.put_new(new + key[len(old) :], text)
    return new
