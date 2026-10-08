"""The failure rules (Phase 3 IMPLEMENTATION doc section 9, `planning/07` 5.1-5.2, decisions 3 and 6).

**Counting** (9.1). From each run's final status: ``valid`` and ``valid_rescaled`` are valid; ``refusal`` is a
refusal; every other final status is a failure by type. A ``no_tool_call`` becomes a refusal only by a logged
human call: a JSON file beside the sweep, ``refusal-calls.json``, an object of run id to the reason for it,

    {"r-0123456789ab": "the model wrote that it would not make this decision"}

A call must name a run in the data whose final status is ``no_tool_call``; anything else is refused, so a typo
cannot quietly change a count. ``possible_decline`` only lists candidates (``decline_candidates``); it never
decides. A refusal and a failure count the same toward the 10% rule and the worst-case bound; they differ only
in which column of the published table they sit in.

**Cells and the 10% rule** (9.2, decision 6). A cell is model x scenario x objective x wording. A cell whose
failure rate, refusals included, is strictly greater than 10% is unreliable (3 of 30 is not; 4 of 30 is;
compared with integers). Its wording is dropped from both sides of every comparison the cell is in, and the
result says which wordings it is over; a comparison left with no wording is ``not_assessable``.

**First attempt beside final** (9.3). The same assessment on a view of each run that takes its first attempt
as its result. Descriptive. A human refusal call is about a run's final status and is not applied to the view.

**The worst-case bound, both ways** (9.4, decision 3). With failed or refused runs in the wordings kept, each
one's outcome is set to 0 or 1 and the whole verdict is recomputed, interval included. A split is checked
against the setting that most narrows the difference. A no split is checked against the setting that most
widens it, in **both signs**: a no split's difference can sit near zero, so raising it and lowering it are
different tests, and either one overturning the verdict downgrades it. A verdict that is overturned becomes
inconclusive, with the reason. Failed runs in a dropped wording do not enter, and a comparison with no failed
run is untouched. This is a sensitivity bound, not imputation (`planning/07` 5.2: a failed run is never filled
in with a guess); the values it sets sit in the bound's cells like any other run, so its ``valid_runs`` counts
include them.

**Whether failures differ by objective** (9.5). Per scenario and objective, pooled over wordings, with a
Newcombe interval for each comparison pair at ``DESCRIPTIVE_ALPHA`` (95%). Descriptive, no verdict.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Literal

from horizon_compact.analysis.intervals import (
    ALPHA,
    DESCRIPTIVE_ALPHA,
    RESAMPLES,
    Interval,
    newcombe_difference,
)
from horizon_compact.analysis.outcomes import ScenarioOutcomes
from horizon_compact.analysis.records import (
    NON_MODEL_STATUSES,
    RecordSource,
    RunRow,
    check_readable,
)
from horizon_compact.analysis.verdict import (
    PRIMARY_PAIRS,
    SECONDARY_PAIRS,
    CellSet,
    Comparison,
    Role,
    Verdict,
    compare_cells,
    gather_cells,
    label_for,
    one_value,
)

FAILURE_LIMIT = (1, 10)  # a cell is unreliable when its failures exceed this fraction of its runs
REFUSAL_CALLS_FILE = "refusal-calls.json"
REFUSAL_STATUS = "refusal"
CALLABLE_STATUS = "no_tool_call"  # the only status a human call can turn into a refusal

RunClass = Literal["valid", "valid_rescaled", "refusal", "failure"]
FinalVerdict = Literal["split", "no_split", "inconclusive", "not_assessable"]


class RefusalCallError(ValueError):
    """The logged human calls are malformed or name a run they cannot apply to."""


# --- 9.1 counting ----------------------------------------------------------------------------------------

_RUN_ID = re.compile(r"r-[0-9a-f]{12}$")


def parse_refusal_calls(text: str) -> dict[str, str]:
    """The file's run id -> reason, refused unless every id is a run id and every reason is a sentence."""
    try:
        loaded = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RefusalCallError(f"{REFUSAL_CALLS_FILE} is not JSON: {exc}") from exc
    if not isinstance(loaded, dict):
        raise RefusalCallError(f"{REFUSAL_CALLS_FILE} must be an object of run id to reason")
    for run_id, reason in loaded.items():
        if not _RUN_ID.match(run_id):
            raise RefusalCallError(f"{REFUSAL_CALLS_FILE}: {run_id!r} is not a run id")
        if not isinstance(reason, str) or not reason.strip():
            raise RefusalCallError(f"{REFUSAL_CALLS_FILE}: {run_id} needs a reason for the call")
    return dict(loaded)


def read_refusal_calls(source: RecordSource, prefix: str) -> dict[str, str]:
    """The calls logged beside a sweep (``<prefix>refusal-calls.json``); none logged is an empty dict."""
    check_readable(prefix)
    prefix = prefix if prefix.endswith("/") or not prefix else prefix + "/"
    text = source.get(f"{prefix}{REFUSAL_CALLS_FILE}")
    return {} if text is None else parse_refusal_calls(text)


def check_refusal_calls(rows: Sequence[RunRow], calls: Mapping[str, str]) -> None:
    """Every call must name a run in ``rows`` whose final status is ``no_tool_call``."""
    by_id = {row.run_id: row for row in rows}
    for run_id in calls:
        row = by_id.get(run_id)
        if row is None:
            raise RefusalCallError(f"a logged call names {run_id}, which is not among the runs")
        if row.status != CALLABLE_STATUS:
            raise RefusalCallError(
                f"a logged call names {run_id}, whose final status is {row.status}; a human call can only "
                f"turn a {CALLABLE_STATUS} into a refusal"
            )


def classify_run(row: RunRow, calls: Mapping[str, str] | None = None) -> RunClass:
    """valid, valid_rescaled, refusal, or failure (by type: the row's own status)."""
    if row.status in NON_MODEL_STATUSES:
        raise ValueError(
            f"run {row.run_id} has final status {row.status}, which is never a final status"
        )
    if row.status == "valid":
        return "valid"
    if row.status == "valid_rescaled":
        return "valid_rescaled"
    if row.status == REFUSAL_STATUS or (
        row.status == CALLABLE_STATUS and calls is not None and row.run_id in calls
    ):
        return "refusal"
    return "failure"


def decline_candidates(
    rows: Sequence[RunRow], calls: Mapping[str, str] | None = None
) -> tuple[str, ...]:
    """Runs a human might call a refusal: ``no_tool_call`` with the flag set and no call logged yet."""
    logged = calls or {}
    return tuple(
        sorted(
            row.run_id
            for row in rows
            if row.status == CALLABLE_STATUS and row.possible_decline and row.run_id not in logged
        )
    )


# --- 9.2 cells and the 10% rule --------------------------------------------------------------------------


def exceeds_limit(failures: int, attempted: int) -> bool:
    """Strictly more than the limit's share, in integers: 3 of 30 is not over 10%, 4 of 30 is."""
    num, den = FAILURE_LIMIT
    return failures * den > attempted * num


@dataclass(frozen=True)
class CellRate:
    model_key: str
    scenario_id: str
    objective_id: str
    wording_id: str
    attempted: int
    valid: int  # valid and valid_rescaled
    rescaled: int  # of those, the rescaled ones
    refused: int
    failed_by_type: tuple[tuple[str, int], ...]  # (final status, runs), sorted

    @property
    def failed(self) -> int:
        """Failures by type, refusals not included."""
        return sum(n for _status, n in self.failed_by_type)

    @property
    def unsuccessful(self) -> int:
        """Failures plus refusals: what the 10% rule counts."""
        return self.failed + self.refused

    @property
    def failure_rate(self) -> float:
        return self.unsuccessful / self.attempted

    @property
    def unreliable(self) -> bool:
        return exceeds_limit(self.unsuccessful, self.attempted)


def cell_rates(
    rows: Sequence[RunRow], calls: Mapping[str, str] | None = None
) -> tuple[CellRate, ...]:
    """One ``CellRate`` per model x scenario x objective x wording that has any run, sorted by that key."""
    check_refusal_calls(rows, calls or {})
    groups: dict[tuple[str, str, str, str], list[RunRow]] = {}
    for row in rows:
        key = (row.model_key, row.scenario_id, row.objective_id, row.wording_id)
        groups.setdefault(key, []).append(row)
    out = []
    for key in sorted(groups):
        classes = [(row, classify_run(row, calls)) for row in groups[key]]
        by_type = Counter(row.status for row, cls in classes if cls == "failure")
        out.append(
            CellRate(
                *key,
                attempted=len(classes),
                valid=sum(1 for _r, cls in classes if cls in ("valid", "valid_rescaled")),
                rescaled=sum(1 for _r, cls in classes if cls == "valid_rescaled"),
                refused=sum(1 for _r, cls in classes if cls == "refusal"),
                failed_by_type=tuple(sorted(by_type.items())),
            )
        )
    return tuple(out)


# --- 9.4 the assessed comparison -------------------------------------------------------------------------


@dataclass(frozen=True)
class DroppedWording:
    wording_id: str
    cells: tuple[CellRate, ...]  # the unreliable cell or cells that dropped it


@dataclass(frozen=True)
class BoundCheck:
    """One recomputation of the whole verdict with the failed runs in the kept wordings set to 0 or 1."""

    label: str  # "narrowing", "widening: difference raised", "widening: difference lowered"
    first_value: float  # what the first objective's failed runs were set to
    second_value: float
    set_first: int  # failed runs of the first objective set to first_value
    set_second: int
    comparison: Comparison  # recomputed; its valid_runs counts include the runs set
    overturned: bool


@dataclass(frozen=True)
class AssessedComparison:
    scenario_id: str
    first: str
    second: str
    role: Role
    label: str
    wordings_considered: tuple[str, ...]
    dropped: tuple[DroppedWording, ...]
    among_valid: Comparison | None  # over the kept wordings; None when not assessable
    failed_first: int  # failed and refused runs in the kept wordings
    failed_second: int
    bound: tuple[BoundCheck, ...]  # empty: no failed run, or already inconclusive
    worst_case_verdict: Verdict | None  # None when no bound was applied
    final_verdict: FinalVerdict
    downgrade_reason: str | None

    @property
    def kept_wordings(self) -> tuple[str, ...]:
        dropped = {d.wording_id for d in self.dropped}
        return tuple(w for w in self.wordings_considered if w not in dropped)

    @property
    def scope(self) -> str:
        """Which wordings the verdict is over, and why any were dropped."""
        kept = self.kept_wordings
        if not kept:
            return "not assessable: every wording has a cell over the 10% failure limit"
        text = "over " + ("wording " if len(kept) == 1 else "wordings ") + _join(kept)
        for drop in self.dropped:
            cells = "; ".join(
                f"{c.objective_id}'s {c.wording_id} cell failed {c.unsuccessful} of {c.attempted}"
                for c in drop.cells
            )
            text += f" ({drop.wording_id} dropped from both sides: {cells}, over 10%)"
        return text


def _join(items: Sequence[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def _set_failed(
    cellset: CellSet, counts: Mapping[tuple[str, str], int], first_v: float, second_v: float
) -> CellSet:
    values = {cellset.first: first_v, cellset.second: second_v}
    cells = {
        side: {
            w: [*cellset.cells[side][w], *([values[side]] * counts.get((side, w), 0))]
            for w in cellset.wordings
        }
        for side in (cellset.first, cellset.second)
    }
    return replace(cellset, cells=cells)


def assess_comparison(
    outcomes: ScenarioOutcomes,
    rows: Sequence[RunRow],
    first: str,
    second: str,
    *,
    role: Role = "primary",
    calls: Mapping[str, str] | None = None,
    alpha: float = ALPHA,
    resamples: int = RESAMPLES,
    name: str | None = None,
) -> AssessedComparison:
    """One comparison with the failure rules applied: unreliable wordings dropped from both sides, the verdict
    among valid runs, then the worst-case bound, then the final verdict and, if it was downgraded, why."""
    scenario_id = outcomes.scenario.id
    if first == second:
        raise ValueError("a comparison needs two different objectives")
    check_refusal_calls(
        rows, calls or {}
    )  # against every run given, so a mistyped id cannot slip past
    scoped = [r for r in rows if r.scenario_id == scenario_id and r.objective_id in (first, second)]
    if not scoped:
        raise ValueError(f"no runs of {first} or {second} on {scenario_id}")
    one_value(scoped, "sweep_id")
    one_value(scoped, "model_key")
    rates = {
        (c.objective_id, c.wording_id): c for c in cell_rates(scoped, _scoped_calls(scoped, calls))
    }
    wordings = tuple(sorted({r.wording_id for r in scoped}))
    for wording in wordings:
        for side in (first, second):
            if (side, wording) not in rates:
                raise ValueError(
                    f"{scenario_id} {first}-{second}: {side} has no run at all under {wording}; the design "
                    "is unbalanced and the cell's failure rate is undefined"
                )
    dropped = tuple(
        DroppedWording(w, tuple(rates[(s, w)] for s in (first, second) if rates[(s, w)].unreliable))
        for w in wordings
        if rates[(first, w)].unreliable or rates[(second, w)].unreliable
    )
    kept = tuple(w for w in wordings if w not in {d.wording_id for d in dropped})
    proto = AssessedComparison(
        scenario_id=scenario_id,
        first=first,
        second=second,
        role=role,
        label=label_for(role),
        wordings_considered=wordings,
        dropped=dropped,
        among_valid=None,
        failed_first=0,
        failed_second=0,
        bound=(),
        worst_case_verdict=None,
        final_verdict="not_assessable",
        downgrade_reason="every wording has a cell over the 10% failure limit",
    )
    if not kept:
        return proto

    seed_name = name or f"{scenario_id}:{first}-{second}"
    cellset = gather_cells(outcomes, scoped, first, second, wordings=kept)
    valid = compare_cells(
        outcomes, cellset, role=role, alpha=alpha, resamples=resamples, name=seed_name
    )
    failed = {(side, w): rates[(side, w)].unsuccessful for side in (first, second) for w in kept}
    n_first = sum(n for (side, _w), n in failed.items() if side == first)
    n_second = sum(n for (side, _w), n in failed.items() if side == second)
    proto = replace(
        proto,
        among_valid=valid,
        failed_first=n_first,
        failed_second=n_second,
        final_verdict=valid.verdict,
        downgrade_reason=None,
    )

    if n_first + n_second == 0 or valid.verdict == "inconclusive":
        return proto

    if valid.verdict == "split":  # narrow: the sign of the difference decides which way is narrower
        settings = [("narrowing", 0.0, 1.0)] if valid.difference > 0 else [("narrowing", 1.0, 0.0)]
    else:  # no split: widen, in both signs
        settings = [
            ("widening: difference raised", 1.0, 0.0),
            ("widening: difference lowered", 0.0, 1.0),
        ]
    checks = []
    for label, first_v, second_v in settings:
        recomputed = compare_cells(
            outcomes,
            _set_failed(cellset, failed, first_v, second_v),
            role=role,
            alpha=alpha,
            resamples=resamples,
            name=f"{seed_name}:bound:{label}",
        )
        checks.append(
            BoundCheck(
                label,
                first_v,
                second_v,
                n_first,
                n_second,
                recomputed,
                recomputed.verdict != valid.verdict,
            )
        )
    overturning = next((c for c in checks if c.overturned), None)
    proto = replace(proto, bound=tuple(checks), worst_case_verdict=valid.verdict)
    if overturning is None:
        return proto
    reason = (
        f"{valid.verdict} among valid runs, overturned by the worst-case bound ({overturning.label}): "
        f"with the {n_first} failed or refused runs of {first} set to {overturning.first_value:g} and the "
        f"{n_second} of {second} set to {overturning.second_value:g}, the verdict becomes "
        f"{overturning.comparison.verdict}: {overturning.comparison.decision.reason}"
    )
    return replace(
        proto,
        worst_case_verdict=overturning.comparison.verdict,
        final_verdict="inconclusive",
        downgrade_reason=reason,
    )


def _scoped_calls(rows: Sequence[RunRow], calls: Mapping[str, str] | None) -> dict[str, str]:
    ids = {r.run_id for r in rows}
    return {k: v for k, v in (calls or {}).items() if k in ids}


# --- 9.3 first attempt beside final ----------------------------------------------------------------------


def first_attempt_rows(rows: Sequence[RunRow]) -> tuple[RunRow, ...]:
    """Each run as if its first attempt were its result: its status, amounts and choice."""
    return tuple(
        replace(
            row,
            status=row.first_attempt_status,
            amounts=row.first_amounts,
            choice=row.first_choice,
        )
        for row in rows
    )


# --- 9.5 whether failures differ by objective ------------------------------------------------------------


@dataclass(frozen=True)
class ObjectiveRates:
    objective_id: str
    attempted: int
    failed: int  # by type, refusals not included
    refused: int

    @property
    def unsuccessful(self) -> int:
        return self.failed + self.refused


@dataclass(frozen=True)
class PairRates:
    """Failure, refusal and either, as first minus second, each with a Newcombe interval. No verdict."""

    first: str
    second: str
    role: Role
    failed: Interval
    refused: Interval
    unsuccessful: Interval


def objective_rates(
    rows: Sequence[RunRow], scenario_id: str, calls: Mapping[str, str] | None = None
) -> tuple[ObjectiveRates, ...]:
    """Per objective on one scenario, pooled over wordings (every cell, the unreliable ones included)."""
    pooled: dict[str, list[int]] = {}
    for cell in cell_rates(
        [r for r in rows if r.scenario_id == scenario_id], _scoped_calls(rows, calls)
    ):
        n = pooled.setdefault(cell.objective_id, [0, 0, 0])
        n[0] += cell.attempted
        n[1] += cell.failed
        n[2] += cell.refused
    return tuple(ObjectiveRates(o, *pooled[o]) for o in sorted(pooled))


def pair_rates(
    rates: Sequence[ObjectiveRates], *, alpha: float = DESCRIPTIVE_ALPHA
) -> tuple[PairRates, ...]:
    """A Newcombe interval for each comparison pair that both has runs, primary pairs first."""
    by_id = {r.objective_id: r for r in rates}
    pairs: list[tuple[tuple[str, str], Role]] = [(p, "primary") for p in PRIMARY_PAIRS]
    pairs += [(p, "secondary") for p in SECONDARY_PAIRS]
    out = []
    for (first, second), role in pairs:
        if first not in by_id or second not in by_id:
            continue
        a, b = by_id[first], by_id[second]

        def diff(x: int, y: int, a: ObjectiveRates = a, b: ObjectiveRates = b) -> Interval:
            return newcombe_difference(x, a.attempted, y, b.attempted, alpha=alpha)

        out.append(
            PairRates(
                first,
                second,
                role,
                diff(a.failed, b.failed),
                diff(a.refused, b.refused),
                diff(a.unsuccessful, b.unsuccessful),
            )
        )
    return tuple(out)


# --- one scenario ------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ScenarioAssessment:
    scenario_id: str
    cells: tuple[CellRate, ...]
    comparisons: tuple[AssessedComparison, ...]  # A-C, A-B, C-D, B-D, then A-D
    first_attempt: tuple[AssessedComparison, ...]  # the same, on first attempts (descriptive)
    objective_rates: tuple[ObjectiveRates, ...]
    pair_rates: tuple[PairRates, ...]


def assess_scenario(
    outcomes: ScenarioOutcomes,
    rows: Sequence[RunRow],
    *,
    calls: Mapping[str, str] | None = None,
    alpha: float = ALPHA,
    descriptive_alpha: float = DESCRIPTIVE_ALPHA,
    resamples: int = RESAMPLES,
) -> ScenarioAssessment:
    """Every failure-rule output for one scenario of one sweep of one model."""
    scenario_id = outcomes.scenario.id
    scoped = [r for r in rows if r.scenario_id == scenario_id]
    if not scoped:
        raise ValueError(f"no runs on {scenario_id}")
    one_value(scoped, "sweep_id")
    one_value(scoped, "model_key")
    check_refusal_calls(rows, calls or {})
    mine = _scoped_calls(scoped, calls)
    pairs: list[tuple[tuple[str, str], Role]] = [(p, "primary") for p in PRIMARY_PAIRS]
    pairs += [(p, "secondary") for p in SECONDARY_PAIRS]
    firsts = first_attempt_rows(scoped)

    def run_all(
        view: Sequence[RunRow], suffix: str, use_calls: Mapping[str, str]
    ) -> tuple[AssessedComparison, ...]:
        return tuple(
            assess_comparison(
                outcomes,
                view,
                first,
                second,
                role=role,
                calls=use_calls,
                alpha=alpha,
                resamples=resamples,
                name=f"{scenario_id}:{first}-{second}{suffix}",
            )
            for (first, second), role in pairs
        )

    rates = objective_rates(scoped, scenario_id, mine)
    return ScenarioAssessment(
        scenario_id=scenario_id,
        cells=cell_rates(scoped, mine),
        comparisons=run_all(scoped, "", mine),
        first_attempt=run_all(firsts, ":first-attempt", {}),
        objective_rates=rates,
        pair_rates=pair_rates(rates, alpha=descriptive_alpha),
    )
