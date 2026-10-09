"""The interval methods (Phase 3 IMPLEMENTATION doc section 7, decisions 5 and 7; step 12, section 20b).

**Choice rates** (S3's close rate, S4's fund rate): Newcombe's hybrid score interval for a difference of two
proportions (Newcombe 1998, method 10), from statsmodels, on counts pooled across wordings. It never has zero
width, even when every run in both groups agrees, which is why `planning/07` section 6.3 chose it.

**Shares** (S1, S2 and every secondary share): a stratified Welch t-interval (step 12, replacing the
percentile bootstrap, which step 10's simulations found too narrow at these sample sizes). Each objective's
value is the mean of its per-wording means (decision 5), so every wording counts equally even when failures
leave the cells unequal. The difference's squared standard error is the sum, over every cell of both sides, of
``s^2 / (W^2 n)`` (``s^2`` the cell's sample variance, ``n`` its valid runs, ``W`` the wordings compared); its
degrees of freedom are Welch-Satterthwaite's over those same terms; the interval is the difference plus or
minus ``t(1 - ALPHA / 2, df)`` standard errors. When every cell has no spread the interval is the difference
alone, with no degrees of freedom: the verdict engine's two all-agree rules (decision 10, ``verdict.py``)
decide what that means.

**The matcher keeps a stratified percentile bootstrap** (section 13): a 95% reading, outside the family, for
which within each objective and each wording a cell's valid runs are drawn with replacement, as many as the
cell holds, and the interval is the ``alpha / 2`` and ``1 - alpha / 2`` quantiles of the resampled values.

**The fine print is frozen here** (decision 7): ``ALPHA`` is exactly 0.05 / 16, one primary family of 16
comparisons per model, called "99.7%" in prose. For the matcher's bootstrap: 100,000 resamples and one PCG64
generator per reading, seeded from the sweep id and the reading's name, so no one chooses a seed. A seeded
generator's draws can change between numpy versions, so "reproducible" means with the versions ``uv.lock``
pins.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy.stats import norm, t
from statsmodels.stats.proportion import confint_proportions_2indep

FAMILY_SIZE = 16  # 4 scenarios x 4 primary comparisons, per model (section 8.1)
ALPHA = 0.05 / FAMILY_SIZE  # 0.003125 exactly: a 99.6875% interval, "99.7%" in prose
Z = float(norm.ppf(1 - ALPHA / 2))  # 2.9552
RESAMPLES = 100_000
# Descriptive intervals (no verdict): failure rates by objective (section 9.5), position effects
# (section 10.3). 95%, as for the matcher's tie (decision 9): a reading, not a test. Here the narrower
# interval is the cautious one, since its job is to show a difference by objective that could bias the
# comparison. Decided 2026-10-08 (his).
DESCRIPTIVE_ALPHA = 0.05

Method = Literal["newcombe", "welch", "stratified_bootstrap"]


@dataclass(frozen=True)
class Interval:
    """A difference (first named minus second named) and its interval, with what produced it."""

    estimate: float
    low: float
    high: float
    method: Method
    alpha: float
    resamples: int | None = None  # bootstrap only
    seed: int | None = None  # bootstrap only
    df: float | None = None  # Welch only; None when every cell has no spread

    @property
    def width(self) -> float:
        return self.high - self.low


def _check_counts(count: int, total: int, side: str) -> None:
    if total < 1:
        raise ValueError(f"{side}: no runs to compare (n = {total})")
    if not 0 <= count <= total:
        raise ValueError(f"{side}: count {count} is outside 0..{total}")


def newcombe_difference(
    count1: int, total1: int, count2: int, total2: int, *, alpha: float = ALPHA
) -> Interval:
    """Newcombe's hybrid score interval for ``count1 / total1 - count2 / total2`` (method 10, no continuity
    correction). The one call to statsmodels, which ships no type information, is wrapped here."""
    _check_counts(count1, total1, "first")
    _check_counts(count2, total2, "second")
    low, high = confint_proportions_2indep(
        count1,
        total1,
        count2,
        total2,
        method="newcomb",
        compare="diff",
        alpha=alpha,
        correction=False,
    )
    return Interval(
        estimate=count1 / total1 - count2 / total2,
        low=float(low),
        high=float(high),
        method="newcombe",
        alpha=alpha,
    )


Cells = Mapping[str, Sequence[float]]  # wording id -> the valid runs' outcomes in that cell


def _arrays(cells: Cells, side: str) -> dict[str, np.ndarray]:
    if not cells:
        raise ValueError(f"{side}: no wording to compare")
    arrays: dict[str, np.ndarray] = {}
    for wording in sorted(cells):
        values = np.asarray(cells[wording], dtype=np.float64)
        if values.ndim != 1 or values.size == 0:
            raise ValueError(f"{side}: wording {wording} has no valid run")
        if not np.all(np.isfinite(values)):
            raise ValueError(f"{side}: wording {wording} holds a value that is not finite")
        arrays[wording] = values
    return arrays


def mean_of_wording_means(cells: Cells) -> float:
    """An objective's value (decision 5): each wording's mean, then their mean, so wordings weigh equally."""
    arrays = _arrays(cells, "cells")
    return float(np.mean([values.mean() for values in arrays.values()]))


def _cell_term(values: np.ndarray, wordings: int) -> float:
    """One cell's share of the difference's squared standard error, ``s^2 / (W^2 n)``. A cell whose runs all
    hold one value has no spread: exactly 0, not the rounding noise ``np.var`` can leave."""
    if np.all(values == values[0]):
        return 0.0
    return float(values.var(ddof=1)) / (wordings**2 * values.size)


def welch_difference(first: Cells, second: Cells, *, alpha: float = ALPHA) -> Interval:
    """The stratified Welch t-interval for (first's value - second's value), each the mean of its per-wording
    means (section 20b, item 1).

    Both sides must hold the same wordings, as for the bootstrap, and every cell needs at least two valid
    runs: a variance from one run would be a silent zero. That is unreachable in a real sweep (at 6 to 9
    repeats one failure already drops the wording; at 10 or more a kept cell holds at least 9), so it is
    refused rather than handled. When every cell has no spread the interval is ``[d, d]`` with ``df`` None.
    """
    a, b = _arrays(first, "first"), _arrays(second, "second")
    if set(a) != set(b):
        raise ValueError(
            f"the two sides must hold the same wordings; first has {sorted(a)}, second {sorted(b)}"
        )
    for side, arrays in (("first", a), ("second", b)):
        for wording, values in arrays.items():
            if values.size < 2:
                raise ValueError(
                    f"{side}: wording {wording} has {values.size} valid run; a cell's variance needs two"
                )
    wordings = len(a)
    cells = [*a.values(), *b.values()]
    terms = [_cell_term(values, wordings) for values in cells]
    se2 = sum(terms)
    estimate = mean_of_wording_means(first) - mean_of_wording_means(second)
    if se2 == 0:
        return Interval(estimate, estimate, estimate, "welch", alpha)
    df = se2**2 / sum(
        term**2 / (values.size - 1) for term, values in zip(terms, cells, strict=True)
    )
    half = float(t.ppf(1 - alpha / 2, df)) * se2**0.5
    return Interval(estimate, estimate - half, estimate + half, "welch", alpha, df=df)


def comparison_seed(sweep_id: str, comparison: str) -> int:
    """The seed for one comparison, derived from the sweep id and the comparison's name (decision 7)."""
    digest = hashlib.sha256(f"{sweep_id}|{comparison}".encode()).digest()
    return int.from_bytes(digest[:16], "big")


def _resampled_values(
    arrays: dict[str, np.ndarray], rng: np.random.Generator, b: int
) -> np.ndarray:
    """``b`` resampled objective values: per wording, ``b`` resamples of the cell's own size, averaged; then
    the mean over wordings. Wordings are drawn in sorted order, so the draws are fixed by the seed."""
    per_wording = np.empty((len(arrays), b))
    for row, values in enumerate(arrays.values()):
        picks = rng.integers(0, values.size, size=(b, values.size))
        per_wording[row] = values[picks].mean(axis=1)
    resampled: np.ndarray = per_wording.mean(axis=0)
    return resampled


def stratified_bootstrap_value(
    cells: Cells, *, seed: int, alpha: float, resamples: int = RESAMPLES
) -> Interval:
    """The percentile interval for one side's value (the mean of its per-wording means), resampling within
    each wording: the spread the matcher shows beside each objective's distance (section 13.1)."""
    if resamples < 1:
        raise ValueError("resamples must be at least 1")
    arrays = _arrays(cells, "cells")
    rng = np.random.Generator(np.random.PCG64(seed))
    low, high = np.quantile(_resampled_values(arrays, rng, resamples), [alpha / 2, 1 - alpha / 2])
    return Interval(
        estimate=mean_of_wording_means(cells),
        low=float(low),
        high=float(high),
        method="stratified_bootstrap",
        alpha=alpha,
        resamples=resamples,
        seed=seed,
    )


def stratified_bootstrap_difference(
    first: Cells,
    second: Cells,
    *,
    seed: int,
    alpha: float = ALPHA,
    resamples: int = RESAMPLES,
) -> Interval:
    """The percentile interval for (first's value - second's value), resampling within each wording.

    Both sides must hold the same wordings: like with like (`planning/07` section 7.1). A wording excluded for
    failures is dropped from both sides by the caller before this is called (decision 6).
    """
    if resamples < 1:
        raise ValueError("resamples must be at least 1")
    a, b = _arrays(first, "first"), _arrays(second, "second")
    if set(a) != set(b):
        raise ValueError(
            f"the two sides must hold the same wordings; first has {sorted(a)}, second {sorted(b)}"
        )
    rng = np.random.Generator(np.random.PCG64(seed))
    differences = _resampled_values(a, rng, resamples) - _resampled_values(b, rng, resamples)
    low, high = np.quantile(differences, [alpha / 2, 1 - alpha / 2])
    return Interval(
        estimate=mean_of_wording_means(first) - mean_of_wording_means(second),
        low=float(low),
        high=float(high),
        method="stratified_bootstrap",
        alpha=alpha,
        resamples=resamples,
        seed=seed,
    )
