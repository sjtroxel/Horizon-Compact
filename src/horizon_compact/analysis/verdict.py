"""The comparisons and their three verdicts (Phase 3 IMPLEMENTATION doc section 8, `planning/07` 6.1-6.3).

For each scenario, on its primary outcome: **A vs C, A vs B, C vs D, B vs D** are the primary comparisons
(four scenarios times four pairs: the family of 16 per model); **A vs D** is secondary, labeled as the
expected comparison, computed the same way and outside the family. The difference is always the first named
minus the second named. E's distance to each objective is descriptive and lives with the descriptive analyses.

**The three verdicts** (`planning/07` section 6.2), with ``T`` the practical threshold, ``d`` the observed
difference and ``[lo, hi]`` its interval:

- **split:** the interval excludes zero and the difference is at least ``T``, both on the same side of zero;
- **no split:** the whole interval lies strictly inside ``(-T, T)``;
- **inconclusive:** anything else.

A boundary value counts against the stronger verdict: an interval end exactly at zero does not exclude it,
and an end exactly at plus or minus ``T`` is not inside. "At least ``T``" includes ``T``. Every comparison is
made with a tolerance of ``BOUNDARY_TOLERANCE``, because floating point puts exact boundaries a hair off:
57/60 - 45/60 is 0.19999999999999996, not 0.2. One further guard, which can only weaken a verdict: the
difference must sit inside its own interval (a percentile interval can, rarely, exclude its own estimate;
Welch's cannot, but the guard costs nothing and stays).
It also keeps a split's difference on the side of zero its interval is on, and keeps split and no split
from ever both holding.

**Shares: two all-agree rules** (decision 10, as decided at step 12 from the simulations; section 20b),
applied after the interval's verdict, each of which can only weaken it:

- **(a) the floor:** a share interval narrower than ``SHARE_FLOOR`` (1/125, one person of S1's 125) is never a
  "no split"; it becomes inconclusive. A width at the floor, within the tolerance, counts as narrower: a
  boundary counts against the stronger verdict. Runs that nearly all agree give an interval too narrow to
  mean anything, which without this rule reads as a confident "no split" (step 10: up to 15% false "no
  split" where the true difference was the threshold).
- **(b) the constant check:** when every valid run of either objective, over the wordings compared, holds one
  value ``v`` (the first objective's, if both do), the share of each side's runs at ``v`` is also compared, by
  Newcombe at ``alpha`` and the share threshold, and the comparison takes the less certain of the two
  verdicts: the same verdict when they agree, inconclusive when they do not.

Choice rates use Newcombe, which never has zero width, and neither rule applies to them.

This step returns the verdict **among valid runs**. The worst-case bound (section 9.4) and the wording
direction (section 10.1) are later steps that may downgrade it; nothing here reads a failed run. The bound's
recomputations go through ``compare_cells`` too, so both rules apply there as well.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from horizon_compact.analysis.intervals import (
    ALPHA,
    Interval,
    newcombe_difference,
    welch_difference,
)
from horizon_compact.analysis.outcomes import ScenarioOutcomes
from horizon_compact.analysis.records import RunRow

PRIMARY_PAIRS: tuple[tuple[str, str], ...] = (("A", "C"), ("A", "B"), ("C", "D"), ("B", "D"))
SECONDARY_PAIRS: tuple[tuple[str, str], ...] = (("A", "D"),)
# Far below anything a difference of rates or shares can mean (the finest grid is 1/125 = 0.008), far above
# floating-point noise on numbers between -1 and 1 (about 1e-16).
BOUNDARY_TOLERANCE = 1e-9
# Decision 10, rule (a): one step of S1's lattice (125 people). A share interval narrower than this is never a
# "no split". Used for every share, S2's continuous one included: the simulations set it on S1's lattice and
# checked it on a 1/1000 one (section 20b).
SHARE_FLOOR = 1 / 125

Verdict = Literal["split", "no_split", "inconclusive"]
Role = Literal["primary", "secondary"]


def label_for(role: Role) -> str:
    return "primary" if role == "primary" else "secondary: the expected comparison"


@dataclass(frozen=True)
class Decision:
    verdict: Verdict
    reason: str


def _check_numbers(d: float, lo: float, hi: float, threshold: float) -> None:
    if not all(math.isfinite(x) for x in (d, lo, hi, threshold)):
        raise ValueError(f"a verdict needs finite numbers; got d={d}, [{lo}, {hi}], T={threshold}")
    if threshold <= 0:
        raise ValueError(f"the threshold must be positive; got {threshold}")
    if lo > hi:
        raise ValueError(f"the interval is reversed: [{lo}, {hi}]")


def decide(d: float, lo: float, hi: float, threshold: float) -> Decision:
    """One verdict from the difference, its interval and the threshold (`planning/07` section 6.2)."""
    _check_numbers(d, lo, hi, threshold)
    eps = BOUNDARY_TOLERANCE
    t = threshold
    span = f"difference {d:+.4f}, interval [{lo:+.4f}, {hi:+.4f}], threshold {t:.2f}"

    if d < lo - eps or d > hi + eps:
        return Decision("inconclusive", f"the difference lies outside its own interval ({span})")
    above, below = lo > eps, hi < -eps  # the interval excludes zero, upward or downward
    if (above and d >= t - eps) or (below and d <= -t + eps):
        return Decision(
            "split", f"the interval excludes zero and the difference reaches the threshold ({span})"
        )
    if lo > -t + eps and hi < t - eps:
        return Decision(
            "no_split", f"the whole interval lies inside plus or minus the threshold ({span})"
        )
    if above or below:
        return Decision(
            "inconclusive",
            f"the interval excludes zero, but the difference is below the threshold and the interval "
            f"reaches past it ({span})",
        )
    return Decision(
        "inconclusive",
        f"the interval includes zero and reaches to or past the threshold ({span})",
    )


def less_certain(first: Decision, second: Decision) -> Decision:
    """Two verdicts on one comparison: the same verdict when they agree (the first's reason kept), otherwise
    inconclusive, naming both."""
    if first.verdict == second.verdict:
        return first
    return Decision(
        "inconclusive",
        f"two verdicts disagree, so the less certain is kept: {first.verdict} ({first.reason}); "
        f"{second.verdict} ({second.reason})",
    )


@dataclass(frozen=True)
class Comparison:
    """One comparison of two objectives on one scenario's primary outcome, among valid runs."""

    scenario_id: str
    first: str
    second: str
    role: Role
    label: str  # "primary", or "secondary: the expected comparison"
    outcome: str  # the primary outcome's name
    kind: Literal["share", "choice_rate"]
    threshold: float
    wordings: tuple[str, ...]  # the verdict is "over these wordings"
    valid_runs: tuple[tuple[str, int, int], ...]  # (wording, first's valid runs, second's)
    interval: Interval
    decision: Decision  # the final verdict among valid runs, after the two all-agree rules
    # True when the interval has (almost) no width: the case decision 10 settles. Never silent.
    degenerate_interval: bool
    # Decision 10 (shares only): rule (a) turned a no split into inconclusive; rule (b)'s value and verdict.
    floor_applied: bool = False
    constant_value: float | None = None
    constant_check: Decision | None = None

    @property
    def verdict(self) -> Verdict:
        return self.decision.verdict

    @property
    def difference(self) -> float:
        return self.interval.estimate


def one_value(rows: Sequence[RunRow], field: str) -> str:
    values = {getattr(row, field) for row in rows}
    if len(values) != 1:
        raise ValueError(
            f"a comparison reads one sweep of one model; the runs hold {field}s {sorted(values)}"
        )
    return str(values.pop())


@dataclass(frozen=True)
class CellSet:
    """The outcomes a comparison reads, as objective -> wording -> one number per run. The failure rules build
    a second set from the first with failed runs filled in at 0 or 1 (the worst-case bound, section 9.4)."""

    scenario_id: str
    sweep_id: str
    first: str
    second: str
    wordings: tuple[str, ...]
    cells: Mapping[str, Mapping[str, Sequence[float]]]


def gather_cells(
    outcomes: ScenarioOutcomes,
    rows: Sequence[RunRow],
    first: str,
    second: str,
    *,
    wordings: Sequence[str] | None = None,
) -> CellSet:
    """The valid runs' primary outcomes of ``first`` and ``second``, by wording, over ``wordings`` (default:
    every wording either side has a valid run in). Every wording compared must have a valid run on both
    sides: dropping a wording is the failure rules' decision (decision 6), made before this is called, never
    here."""
    scenario_id = outcomes.scenario.id
    if first == second:
        raise ValueError("a comparison needs two different objectives")
    scoped = [r for r in rows if r.scenario_id == scenario_id and r.objective_id in (first, second)]
    if not scoped:
        raise ValueError(f"no runs of {first} or {second} on {scenario_id}")
    sweep_id = one_value(scoped, "sweep_id")
    one_value(scoped, "model_key")
    valid = [r for r in scoped if r.valid]

    by_side: dict[str, dict[str, list[float]]] = {first: {}, second: {}}
    for row in valid:
        by_side[row.objective_id].setdefault(row.wording_id, []).append(outcomes.score(row).primary)
    chosen = (
        tuple(sorted(wordings))
        if wordings is not None
        else tuple(sorted(set(by_side[first]) | set(by_side[second])))
    )
    if not chosen:
        raise ValueError(f"{scenario_id} {first}-{second}: no wording to compare")
    for wording in chosen:
        for side in (first, second):
            if not by_side[side].get(wording):
                raise ValueError(
                    f"{scenario_id} {first}-{second}: {side} has no valid run under {wording}; the failure "
                    "rules drop a wording from both sides before a comparison, never inside it"
                )
    cells = {side: {w: by_side[side][w] for w in chosen} for side in (first, second)}
    return CellSet(scenario_id, sweep_id, first, second, chosen, cells)


def _constant_value(cells: Mapping[str, Sequence[float]]) -> float | None:
    """The one value every run of one side holds (within the tolerance), or None."""
    values = [v for runs in cells.values() for v in runs]
    first = values[0]
    return first if all(abs(v - first) <= BOUNDARY_TOLERANCE for v in values) else None


def _count_at(cells: Mapping[str, Sequence[float]], value: float) -> tuple[int, int]:
    values = [v for runs in cells.values() for v in runs]
    return sum(1 for v in values if abs(v - value) <= BOUNDARY_TOLERANCE), len(values)


def compare_cells(
    outcomes: ScenarioOutcomes,
    cellset: CellSet,
    *,
    role: Role = "primary",
    alpha: float = ALPHA,
) -> Comparison:
    """The interval and the verdict from a set of cells: Welch and decision 10's two rules for a share,
    Newcombe for a choice rate."""
    scenario_id, first, second = cellset.scenario_id, cellset.first, cellset.second
    chosen, cells = cellset.wordings, cellset.cells
    threshold = outcomes.threshold
    floor_applied = False
    constant_value: float | None = None
    constant_check: Decision | None = None
    if outcomes.kind == "share":
        interval = welch_difference(cells[first], cells[second], alpha=alpha)
        decision = decide(interval.estimate, interval.low, interval.high, threshold)
        if decision.verdict == "no_split" and interval.width < SHARE_FLOOR + BOUNDARY_TOLERANCE:
            floor_applied = True
            decision = Decision(
                "inconclusive",
                f"the interval is narrower than {SHARE_FLOOR:g} (decision 10, rule (a)), so it cannot "
                f"support a no split ({decision.reason})",
            )
        for side in (first, second):
            constant_value = _constant_value(cells[side])
            if constant_value is not None:
                break
        if constant_value is not None:
            counted = newcombe_difference(
                *_count_at(cells[first], constant_value),
                *_count_at(cells[second], constant_value),
                alpha=alpha,
            )
            check = decide(counted.estimate, counted.low, counted.high, threshold)
            constant_check = Decision(
                check.verdict,
                f"every run of one objective holds {constant_value:g}; the share of runs at it, by "
                f"Newcombe (decision 10, rule (b)): {check.reason}",
            )
            decision = less_certain(decision, constant_check)
    else:
        counts = {
            side: (
                sum(1 for w in chosen for v in cells[side][w] if v == 1.0),
                sum(len(cells[side][w]) for w in chosen),
            )
            for side in (first, second)
        }
        interval = newcombe_difference(*counts[first], *counts[second], alpha=alpha)
        decision = decide(interval.estimate, interval.low, interval.high, threshold)

    sizes = {side: Counter({w: len(cells[side][w]) for w in chosen}) for side in (first, second)}
    return Comparison(
        scenario_id=scenario_id,
        first=first,
        second=second,
        role=role,
        label=label_for(role),
        outcome=outcomes.primary_name,
        kind=outcomes.kind,
        threshold=threshold,
        wordings=chosen,
        valid_runs=tuple((w, sizes[first][w], sizes[second][w]) for w in chosen),
        interval=interval,
        decision=decision,
        degenerate_interval=interval.width <= BOUNDARY_TOLERANCE,
        floor_applied=floor_applied,
        constant_value=constant_value,
        constant_check=constant_check,
    )


def compare(
    outcomes: ScenarioOutcomes,
    rows: Sequence[RunRow],
    first: str,
    second: str,
    *,
    role: Role = "primary",
    wordings: Sequence[str] | None = None,
    alpha: float = ALPHA,
) -> Comparison:
    """``first`` minus ``second`` on the scenario's primary outcome, among valid runs, over ``wordings``
    (default: every wording either side has a valid run in): ``gather_cells`` then ``compare_cells``."""
    cellset = gather_cells(outcomes, rows, first, second, wordings=wordings)
    return compare_cells(outcomes, cellset, role=role, alpha=alpha)


def compare_scenario(
    outcomes: ScenarioOutcomes,
    rows: Sequence[RunRow],
    *,
    wordings: Sequence[str] | None = None,
    alpha: float = ALPHA,
) -> tuple[Comparison, ...]:
    """The four primary comparisons, then the secondary one, on one scenario, in `planning/07` section 6.1's
    order."""
    pairs: list[tuple[tuple[str, str], Role]] = [(p, "primary") for p in PRIMARY_PAIRS]
    pairs += [(p, "secondary") for p in SECONDARY_PAIRS]
    return tuple(
        compare(outcomes, rows, first, second, role=role, wordings=wordings, alpha=alpha)
        for (first, second), role in pairs
    )
