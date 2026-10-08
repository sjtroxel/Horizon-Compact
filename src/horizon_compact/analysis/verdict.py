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
difference must sit inside its own interval (a percentile interval can, rarely, exclude its own estimate).
It also keeps a split's difference on the side of zero its interval is on, and keeps split and no split
from ever both holding.

This step returns the verdict **among valid runs**. The worst-case bound (section 9.4) and the wording
direction (section 10.1) are later steps that may downgrade it; nothing here reads a failed run.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from horizon_compact.analysis.intervals import (
    ALPHA,
    RESAMPLES,
    Interval,
    comparison_seed,
    newcombe_difference,
    stratified_bootstrap_difference,
)
from horizon_compact.analysis.outcomes import ScenarioOutcomes
from horizon_compact.analysis.records import RunRow

PRIMARY_PAIRS: tuple[tuple[str, str], ...] = (("A", "C"), ("A", "B"), ("C", "D"), ("B", "D"))
SECONDARY_PAIRS: tuple[tuple[str, str], ...] = (("A", "D"),)
# Far below anything a difference of rates or shares can mean (the finest grid is 1/125 = 0.008), far above
# floating-point noise on numbers between -1 and 1 (about 1e-16).
BOUNDARY_TOLERANCE = 1e-9

Verdict = Literal["split", "no_split", "inconclusive"]
Role = Literal["primary", "secondary"]


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
    decision: Decision
    # True when the interval has (almost) no width: the case decision 10 settles. Never silent.
    degenerate_interval: bool

    @property
    def verdict(self) -> Verdict:
        return self.decision.verdict

    @property
    def difference(self) -> float:
        return self.interval.estimate


def _one_value(rows: Sequence[RunRow], field: str) -> str:
    values = {getattr(row, field) for row in rows}
    if len(values) != 1:
        raise ValueError(
            f"a comparison reads one sweep of one model; the runs hold {field}s {sorted(values)}"
        )
    return str(values.pop())


def compare(
    outcomes: ScenarioOutcomes,
    rows: Sequence[RunRow],
    first: str,
    second: str,
    *,
    role: Role = "primary",
    wordings: Sequence[str] | None = None,
    alpha: float = ALPHA,
    resamples: int = RESAMPLES,
    name: str | None = None,
) -> Comparison:
    """``first`` minus ``second`` on the scenario's primary outcome, over ``wordings`` (default: every wording
    either side has a valid run in). Every wording compared must have a valid run on both sides: dropping a
    wording is the failure rules' decision (decision 6), made before this is called, never here.

    The bootstrap's seed comes from the sweep id and ``name`` (default ``"<scenario>:<first>-<second>"``).
    """
    scenario_id = outcomes.scenario.id
    if first == second:
        raise ValueError("a comparison needs two different objectives")
    scoped = [r for r in rows if r.scenario_id == scenario_id and r.objective_id in (first, second)]
    if not scoped:
        raise ValueError(f"no runs of {first} or {second} on {scenario_id}")
    sweep_id = _one_value(scoped, "sweep_id")
    _one_value(scoped, "model_key")
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

    if outcomes.kind == "share":
        seed = comparison_seed(sweep_id, name or f"{scenario_id}:{first}-{second}")
        interval = stratified_bootstrap_difference(
            cells[first], cells[second], seed=seed, alpha=alpha, resamples=resamples
        )
    else:
        counts = {
            side: (
                sum(1 for w in chosen for v in cells[side][w] if v == 1.0),
                sum(len(cells[side][w]) for w in chosen),
            )
            for side in (first, second)
        }
        interval = newcombe_difference(*counts[first], *counts[second], alpha=alpha)

    sizes = {side: Counter({w: len(cells[side][w]) for w in chosen}) for side in (first, second)}
    return Comparison(
        scenario_id=scenario_id,
        first=first,
        second=second,
        role=role,
        label="primary" if role == "primary" else "secondary: the expected comparison",
        outcome=outcomes.primary_name,
        kind=outcomes.kind,
        threshold=outcomes.threshold,
        wordings=chosen,
        valid_runs=tuple((w, sizes[first][w], sizes[second][w]) for w in chosen),
        interval=interval,
        decision=decide(interval.estimate, interval.low, interval.high, outcomes.threshold),
        degenerate_interval=interval.width <= BOUNDARY_TOLERANCE,
    )


def compare_scenario(
    outcomes: ScenarioOutcomes,
    rows: Sequence[RunRow],
    *,
    wordings: Sequence[str] | None = None,
    alpha: float = ALPHA,
    resamples: int = RESAMPLES,
) -> tuple[Comparison, ...]:
    """The four primary comparisons, then the secondary one, on one scenario, in `planning/07` section 6.1's
    order."""
    pairs: list[tuple[tuple[str, str], Role]] = [(p, "primary") for p in PRIMARY_PAIRS]
    pairs += [(p, "secondary") for p in SECONDARY_PAIRS]
    return tuple(
        compare(
            outcomes,
            rows,
            first,
            second,
            role=role,
            wordings=wordings,
            alpha=alpha,
            resamples=resamples,
        )
        for (first, second), role in pairs
    )
