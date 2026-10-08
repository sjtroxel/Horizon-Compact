"""The verdict rule's simulations without failures (Phase 3 IMPLEMENTATION doc section 14.1).

Shares use the exact lattice bootstrap (``exact.py``); choice rates are enumerated exactly, since their
verdict depends only on the two counts. Every verdict is the analysis's own ``verdict.decide`` on the
analysis's own interval (``newcombe_difference`` for choice rates). Two objectives, three wordings, equal
cells; the first objective has the larger true mean, so a split with a negative difference is a split in
the wrong direction and is counted apart.

**Decision 10's candidates** are scored beside the rule as written, on the same replicates, without changing
the analysis. When the candidate's trigger holds, the share is also tested as a choice rate (the share of runs
at the boundary value, by Newcombe, at the share threshold), and the comparison takes the less certain verdict
(the same verdict when both agree, inconclusive when they do not):

- ``c1``, the candidate as written in decision 10: every run of both objectives sits at one boundary value;
- ``c2``, a wider reading: every run of *either* objective sits at one boundary value.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from functools import cache
from typing import Any

import numpy as np
from scipy import stats

from horizon_compact.analysis.intervals import ALPHA, newcombe_difference
from horizon_compact.analysis.outcomes import CHOICE_THRESHOLD, SHARE_THRESHOLD
from horizon_compact.analysis.verdict import BOUNDARY_TOLERANCE, decide
from horizon_compact.simulation.exact import draw, exact_intervals

VERDICTS = ("split", "no_split", "inconclusive")
WORDINGS = 3
NARROW = 0.25  # a "near-zero-width" no split: half-width below a quarter of the threshold
# An interval end this close to a boundary (0 or plus or minus the threshold) can move across it with the
# engine's seed: its Monte Carlo error at 100,000 resamples is about 0.001 (section 14.3).
NEAR_BOUNDARY = (0.001, 0.003)


@cache
def newcombe_verdict(c1: int, n1: int, c2: int, n2: int, threshold: float) -> str:
    """The analysis's verdict on two counts, as ``verdict.compare_cells`` reaches it for a choice rate."""
    interval = newcombe_difference(c1, n1, c2, n2, alpha=ALPHA)
    return decide(interval.estimate, interval.low, interval.high, threshold).verdict


def less_certain(a: str, b: str) -> str:
    return a if a == b else "inconclusive"


def _boundary_trigger(first: np.ndarray, second: np.ndarray, grid: int) -> tuple[str, int | None]:
    """Which candidate fires on one replicate, and at which boundary value: ``("c1", v)`` when every run of
    both sides is ``v``; ``("c2", v)`` when every run of one side is ``v`` (the first side's, if both);
    ``("", None)`` otherwise. ``v`` is 0 or ``grid``."""

    def all_at(side: np.ndarray) -> int | None:
        for v in (0, grid):
            if np.all(side == v):
                return v
        return None

    a, b = all_at(first), all_at(second)
    if a is not None and a == b:
        return "c1", a
    if a is not None:
        return "c2", a
    if b is not None:
        return "c2", b
    return "", None


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
    side), each judged by the rule as written and by decision 10's candidates."""
    rng = np.random.Generator(np.random.PCG64(seed))
    first = np.stack([draw(p, (reps, n), rng) for p in first_pmfs], axis=1)
    second = np.stack([draw(p, (reps, n), rng) for p in second_pmfs], axis=1)
    ex = exact_intervals(first, second, grid=grid, alpha=ALPHA)
    counts: Counter[str] = Counter()
    wrong_sign = degenerate = narrow = 0
    near = dict.fromkeys(NEAR_BOUNDARY, 0)
    rule_when: dict[str, Counter[str]] = {"c1": Counter(), "c2": Counter()}
    combined_when: dict[str, Counter[str]] = {"c1": Counter(), "c2": Counter()}
    half_widths = (ex.high - ex.low) / 2
    big_n = WORDINGS * n
    for r in range(reps):
        d, lo, hi = float(ex.estimate[r]), float(ex.low[r]), float(ex.high[r])
        verdict = decide(d, lo, hi, threshold).verdict
        counts[verdict] += 1
        closest = min(abs(end - b) for end in (lo, hi) for b in (-threshold, 0.0, threshold))
        for delta in NEAR_BOUNDARY:
            near[delta] += closest < delta
        if verdict == "split" and d < 0:
            wrong_sign += 1
        if verdict == "no_split":
            if hi - lo <= BOUNDARY_TOLERANCE:
                degenerate += 1
            if half_widths[r] < NARROW * threshold:
                narrow += 1
        trigger, value = _boundary_trigger(first[r], second[r], grid)
        if trigger:
            k1 = int(np.sum(first[r] == value))
            k2 = int(np.sum(second[r] == value))
            other = newcombe_verdict(k1, big_n, k2, big_n, threshold)
            combined = less_certain(verdict, other)
            for name in ("c1", "c2") if trigger == "c1" else ("c2",):  # c2's trigger includes c1's
                rule_when[name][verdict] += 1
                combined_when[name][combined] += 1
    return {
        "reps": reps,
        "seed": str(seed),
        "verdicts": {v: counts[v] for v in VERDICTS},
        "split_wrong_sign": wrong_sign,
        "no_split_degenerate": degenerate,
        "no_split_narrow": narrow,
        "mean_half_width": float(np.mean(half_widths)),
        "end_near_a_boundary": {f"{delta:g}": near[delta] for delta in NEAR_BOUNDARY},
        **{
            f"{name}_{part}": {v: table[name][v] for v in VERDICTS}
            for name in ("c1", "c2")
            for part, table in (("rule", rule_when), ("combined", combined_when))
        },
    }


def candidate_verdicts(point: dict[str, Any], name: str) -> dict[str, int]:
    """The verdict counts under candidate ``name``: the rule's counts, with each triggered replicate's verdict
    replaced by the combined one."""
    out = dict(point["verdicts"])
    for v in VERDICTS:
        out[v] += point[f"{name}_combined"][v] - point[f"{name}_rule"][v]
    return out


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
