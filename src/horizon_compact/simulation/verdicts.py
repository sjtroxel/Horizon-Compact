"""The verdict rule's simulations without failures (Phase 3 IMPLEMENTATION doc section 14.1; step 12).

**Shares** use the rule as adopted at step 12 (section 20b): the stratified Welch t-interval, then decision
10's two rules, the floor (an interval narrower than ``SHARE_FLOOR`` is never a no split) and the constant
check (when every run of either objective holds one value, the share of runs at it is compared by Newcombe
and the less certain verdict kept). The interval is vectorized over replicates; the rules are written here
again, not called from ``verdict.compare_cells``, so that ``real.validation_point``, which checks every
replicate of a sample against the analysis itself, compares two implementations rather than one with
itself. Values are integers on the lattice, so each cell's variance comes from exact integer sums: a cell
whose runs agree has a variance of exactly zero, as in the analysis. **Choice rates** are enumerated exactly,
since their verdict depends only on the two counts. Every verdict is the analysis's own ``verdict.decide``.
Two objectives, three wordings, equal cells; the first objective has the larger true mean, so a split with a
negative difference is a split in the wrong direction and is counted apart.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cache
from typing import Any

import numpy as np
from scipy import stats

from horizon_compact.analysis.intervals import ALPHA, newcombe_difference
from horizon_compact.analysis.outcomes import CHOICE_THRESHOLD, SHARE_THRESHOLD
from horizon_compact.analysis.verdict import BOUNDARY_TOLERANCE, SHARE_FLOOR, decide
from horizon_compact.simulation.exact import draw

VERDICTS = ("split", "no_split", "inconclusive")
WORDINGS = 3
NARROW = 0.25  # a "near-zero-width" no split: half-width below a quarter of the threshold


@cache
def newcombe_verdict(c1: int, n1: int, c2: int, n2: int, threshold: float) -> str:
    """The analysis's verdict on two counts, as ``verdict.compare_cells`` reaches it for a choice rate."""
    interval = newcombe_difference(c1, n1, c2, n2, alpha=ALPHA)
    return decide(interval.estimate, interval.low, interval.high, threshold).verdict


def less_certain(a: str, b: str) -> str:
    return a if a == b else "inconclusive"


def welch_arrays(
    first: np.ndarray, second: np.ndarray, grid: int, alpha: float = ALPHA
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per replicate, from integer lattice values of shape (replicates, wordings, n): the difference of the
    mean of wording means, and the Welch interval's ends, all in share units. With no spread in any cell the
    interval is the difference alone."""
    _, wordings, n = first.shape
    a, b = first.astype(np.int64), second.astype(np.int64)
    d = (a.sum(axis=2).sum(axis=1) - b.sum(axis=2).sum(axis=1)) / (wordings * n * grid)

    def cell_variance(x: np.ndarray) -> np.ndarray:  # exact in integers, then scaled
        sums, squares = x.sum(axis=2), (x * x).sum(axis=2)
        variance: np.ndarray = (n * squares - sums * sums) / (n * (n - 1) * grid * grid)
        return variance

    terms = np.concatenate([cell_variance(a), cell_variance(b)], axis=1) / (wordings**2 * n)
    se2 = terms.sum(axis=1)
    denominator = (terms**2 / (n - 1)).sum(axis=1)
    spread = se2 > 0
    df = np.ones_like(se2)
    df[spread] = se2[spread] ** 2 / denominator[spread]
    half = np.where(spread, stats.t.ppf(1 - alpha / 2, df) * np.sqrt(se2), 0.0)
    return d, d - half, d + half


@dataclass(frozen=True)
class ShareVerdicts:
    """Per replicate: the difference, the interval, the interval's own verdict, the final verdict, and
    which of decision 10's rules fired (``constant`` is the value rule (b) read, or -1)."""

    estimate: np.ndarray
    low: np.ndarray
    high: np.ndarray
    interval_verdict: list[str]
    final: list[str]
    floor_fired: list[bool]
    constant: list[int]


def _constant(first: np.ndarray, second: np.ndarray) -> int:
    """The lattice value every run of one side holds (the first side's, if both), or -1."""
    for side in (first, second):
        if np.all(side == side.flat[0]):
            return int(side.flat[0])
    return -1


def share_verdicts(
    first: np.ndarray, second: np.ndarray, *, grid: int, threshold: float = SHARE_THRESHOLD
) -> ShareVerdicts:
    """The adopted rule on every replicate of integer lattice values, shape (replicates, wordings, n)."""
    reps, wordings, n = first.shape
    d, lo, hi = welch_arrays(first, second, grid)
    big_n = wordings * n
    interval_verdict: list[str] = []
    final: list[str] = []
    floor_fired: list[bool] = []
    constant: list[int] = []
    for r in range(reps):
        verdict: str = decide(float(d[r]), float(lo[r]), float(hi[r]), threshold).verdict
        interval_verdict.append(verdict)
        floored = bool(verdict == "no_split" and hi[r] - lo[r] < SHARE_FLOOR + BOUNDARY_TOLERANCE)
        if floored:
            verdict = "inconclusive"
        value = _constant(first[r], second[r])
        if value >= 0:
            k1, k2 = int((first[r] == value).sum()), int((second[r] == value).sum())
            verdict = less_certain(verdict, newcombe_verdict(k1, big_n, k2, big_n, threshold))
        final.append(verdict)
        floor_fired.append(floored)
        constant.append(value)
    return ShareVerdicts(d, lo, hi, interval_verdict, final, floor_fired, constant)


def share_point(
    first_pmfs: Sequence[np.ndarray],
    second_pmfs: Sequence[np.ndarray],
    *,
    n: int,
    reps: int,
    seed: int,
    grid: int,
    threshold: float = SHARE_THRESHOLD,
) -> dict[str, Any]:
    """One grid point: ``reps`` replicates of two objectives over three wordings (one pmf per wording and
    side), each judged by the adopted rule, with the Welch interval's own verdict kept beside it."""
    rng = np.random.Generator(np.random.PCG64(seed))
    first = np.stack([draw(p, (reps, n), rng) for p in first_pmfs], axis=1)
    second = np.stack([draw(p, (reps, n), rng) for p in second_pmfs], axis=1)
    got = share_verdicts(first, second, grid=grid, threshold=threshold)
    half_widths = (got.high - got.low) / 2
    counts = Counter(got.final)
    interval_counts = Counter(got.interval_verdict)
    wrong_sign = degenerate = narrow = constant_fired = constant_changed = 0
    for r in range(reps):
        final, alone = got.final[r], got.interval_verdict[r]
        if final == "split" and got.estimate[r] < 0:
            wrong_sign += 1
        if alone == "no_split" and got.high[r] - got.low[r] <= BOUNDARY_TOLERANCE:
            degenerate += 1
        if final == "no_split" and half_widths[r] < NARROW * threshold:
            narrow += 1
        if got.constant[r] >= 0:
            constant_fired += 1
            floored = "inconclusive" if got.floor_fired[r] else alone
            constant_changed += final != floored
    return {
        "reps": reps,
        "seed": str(seed),
        "verdicts": {v: counts[v] for v in VERDICTS},
        "interval_alone": {v: interval_counts[v] for v in VERDICTS},
        "split_wrong_sign": wrong_sign,
        "interval_alone_no_split_degenerate": degenerate,
        "no_split_narrow": narrow,
        "floor_fired": int(sum(got.floor_fired)),
        "constant_fired": constant_fired,
        "constant_changed": constant_changed,
        "mean_half_width": float(np.mean(half_widths)),
    }


def choice_point(
    p_first: float, p_second: float, *, n: int, threshold: float = CHOICE_THRESHOLD
) -> dict[str, Any]:
    """Exact verdict probabilities for two Bernoulli rates, ``WORDINGS * n`` runs a side, counts pooled over
    the wordings (as the analysis pools them): a sum over every pair of counts of the binomial probabilities
    times the analysis's verdict on that pair."""
    big_n = WORDINGS * n
    k = np.arange(big_n + 1)
    pa = stats.binom.pmf(k, big_n, p_first)
    pb = stats.binom.pmf(k, big_n, p_second)
    probability = dict.fromkeys(VERDICTS, 0.0)
    wrong = 0.0
    for c1 in range(big_n + 1):
        if pa[c1] == 0:
            continue
        for c2 in range(big_n + 1):
            weight = float(pa[c1] * pb[c2])
            if weight == 0:
                continue
            verdict = newcombe_verdict(c1, big_n, c2, big_n, threshold)
            probability[verdict] += weight
            if verdict == "split" and c1 < c2:
                wrong += weight
    return {"exact": True, "probability": probability, "split_wrong_sign": wrong}
