"""Records for the analysis tests, written by the runner itself so the format cannot drift (Phase 3 doc 18).

``run_company`` plays a scripted provider through ``run_session`` on the real company scenario files, which
writes under ``development/company/<sweep>/``: exactly the place the reader must refuse. ``relocate`` copies a
sweep's objects to a prefix the reader accepts, so a test can score a run as it would arrive from a pilot.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from scipy import stats

from horizon_compact.analysis.intervals import ALPHA
from horizon_compact.analysis.records import RunRow
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


# --- hand-built runs (no files, no runner): a RunRow written directly -------------------------------------

_counter = iter(range(10**9))


def run(
    scenario: str, objective: str, wording: str, amounts: Mapping[str, float] | None, **kw: Any
) -> RunRow:
    choice = kw.pop("choice", None)
    base: dict[str, Any] = {
        "run_id": f"r-{next(_counter):012x}",
        "sweep_id": "pilot-test-sweep",
        "model_key": "sonnet-4-6",
        "scenario_id": scenario,
        "objective_id": objective,
        "wording_id": wording,
        "repeat": 0,
        "status": "valid" if amounts is not None else "sum_mismatch",
        "first_attempt_status": "valid" if amounts is not None else "sum_mismatch",
        "attempts": 1,
        "possible_decline": False,
        "menu_order": (),
        "option_order": (),
        "amounts": amounts,
        "choice": choice,
        "first_amounts": amounts,
        "first_choice": choice,
    }
    base.update(kw)
    return RunRow(**base)


def s1_runs(objective: str, kept_per_wording: dict[str, Iterable[int]]) -> list[RunRow]:
    """S1 runs keeping the given number of the 125 people (moved at the plant role's pay), the rest
    eliminated."""
    return [
        run("s1", objective, w, {"eliminate": 125 - k, "move_plant_pay": k, "move_keep_pay": 0})
        for w, kept in kept_per_wording.items()
        for k in kept
    ]


def s3_runs(
    objective: str, closes: int, total: int, wordings: tuple[str, ...] = ("w1", "w2", "w3")
) -> list[RunRow]:
    """``total`` S3 runs spread over the wordings in turn, the first ``closes`` of them choosing to close."""
    out = []
    for i in range(total):
        if i < closes:
            amounts, choice = (
                {
                    "eliminated": 161,
                    "moved_other_plants": 29,
                    "kept_at_plant": 0,
                    "transferred_to_buyer": 0,
                },
                "close",
            )
        else:
            amounts, choice = (
                {
                    "eliminated": 0,
                    "moved_other_plants": 29,
                    "kept_at_plant": 161,
                    "transferred_to_buyer": 0,
                },
                "retool",
            )
        out.append(run("s3", objective, wordings[i % len(wordings)], amounts, choice=choice))
    return out


def _wilson(c: int, n: int, z: float) -> tuple[float, float]:
    p = c / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z / (1 + z * z / n) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return centre - half, centre + half


def hand_newcombe(c1: int, n1: int, c2: int, n2: int, alpha: float = ALPHA) -> tuple[float, float]:
    """The test's own Newcombe (Fagerland et al. 2011, eq. 7) at the family alpha: independent of the
    engine."""
    z = float(stats.norm.ppf(1 - alpha / 2))
    p1, p2 = c1 / n1, c2 / n2
    l1, u1 = _wilson(c1, n1, z)
    l2, u2 = _wilson(c2, n2, z)
    d = p1 - p2
    return d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), d + math.sqrt(
        (p2 - l2) ** 2 + (u1 - p1) ** 2
    )


W3 = ("w1", "w2", "w3")


def failed(
    scenario: str, objective: str, wording: str, n: int, status: str = "sum_mismatch", **kw: Any
) -> list[RunRow]:
    """``n`` runs whose final status is ``status`` (default a format failure): never scored, only counted."""
    kw.setdefault("first_attempt_status", status)
    return [
        run(scenario, objective, wording, None, status=status, first_amounts=None, **kw)
        for _ in range(n)
    ]


def s3_cell(
    objective: str, wording: str, closes: int, valid: int, *, fail: int = 0, **kw: Any
) -> list[RunRow]:
    """One S3 cell: ``valid`` valid runs of which ``closes`` chose to close, plus ``fail`` failed runs."""
    rows = s3_runs(objective, closes, valid, (wording,))
    return rows + failed("s3", objective, wording, fail, **kw)


def s3_design(
    objective: str, closes: Sequence[int], valid: Sequence[int], fail: Sequence[int] = (0, 0, 0)
) -> list[RunRow]:
    """S3 runs over w1-w3: per wording, ``valid`` valid runs (``closes`` closing) and ``fail`` failed."""
    rows: list[RunRow] = []
    for w, c, v, f in zip(W3, closes, valid, fail, strict=True):
        rows += s3_cell(objective, w, c, v, fail=f)
    return rows


def with_failures(
    objective: str, closes_total: int, valid_each: int, fail_each: int
) -> list[RunRow]:
    """S3 runs, ``valid_each`` valid per wording (closes spread as evenly as possible) plus failures each."""
    base, extra = divmod(closes_total, 3)
    closes = [base + (1 if i < extra else 0) for i in range(3)]
    return s3_design(objective, closes, [valid_each] * 3, [fail_each] * 3)
