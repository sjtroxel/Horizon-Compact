"""The exact stratified bootstrap on a lattice, and the share distributions the simulations draw from.

**Why exact** (Phase 3 IMPLEMENTATION doc section 14.1, finding at step 10). The engine's bootstrap draws
100,000 resamples and takes the ``ALPHA / 2`` and ``1 - ALPHA / 2`` quantiles of the resampled differences.
Its cost is about 50 ms a comparison, and section 14.1's grid is about 17 million replicates, so running the
engine itself would take about 240 hours on one core. On a lattice the bootstrap distribution it samples can
be computed exactly instead: when every run's value is an integer ``k`` over ``grid``, a cell's resampled
sum is the ``n``-fold convolution of the cell's empirical distribution, each side's total is the convolution
of its wordings' sums, and the difference is one more convolution, all done at once by FFT. The quantiles of
that exact distribution are the limit of the engine's quantiles as its resample count grows, so the exact
interval is the engine's interval without its Monte Carlo error. The simulation validates this against the
engine itself (``real.validation``), and section 14.3 measures what the engine's finite resample count does
near a boundary. The verdict is always the analysis's own ``verdict.decide``.

Cells must hold equal numbers of runs (the failure simulations, where they do not, run the engine itself).

**The share distributions** (section 14.1). A run's share is, with probability ``pi``, "all in": 1 with
probability ``m`` and 0 otherwise, so the all-in part has mean ``m``; otherwise it is a Beta draw rounded to
the lattice. The Beta's mean is solved so that the *rounded* draw has mean exactly ``m``, so the mixture's
mean is exactly ``m`` and two sides set ``d`` apart differ by exactly ``d`` on the lattice. ``sigma`` is the
Beta's standard deviation before rounding. S1's lattice is 1/125 (its people); 1/1000 stands in for S2's
continuous share.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy import fft, optimize, stats

S1_GRID = 125
FINE_GRID = 1000
_TOLERANCE = 1e-12  # a cumulative probability within this of a level has reached it


@dataclass(frozen=True)
class ExactIntervals:
    """Per replicate: the difference (first minus second, the mean of wording means) and the exact percentile
    interval's ends, all in share units."""

    estimate: np.ndarray
    low: np.ndarray
    high: np.ndarray


def _length(points: int) -> int:
    """A transform length at least ``points`` that the FFT handles quickly (a product of 2, 3 and 5)."""
    length: int = fft.next_fast_len(points, real=True)
    return length


def _power(z: np.ndarray, n: int) -> np.ndarray:
    """``z ** n`` by repeated squaring: exact multiplications, faster than a complex power."""
    result = np.ones_like(z)
    base = z.copy()
    while n:
        if n & 1:
            result *= base
        n >>= 1
        if n:
            base *= base
    return result


def _side_transform(shifted: np.ndarray, length: int) -> np.ndarray:
    """The Fourier transform of one side's resampled total: per wording the empirical distribution's transform
    raised to the cell size (n resamples), then the product over wordings. Values are already shifted so
    each cell starts at 0."""
    reps, wordings, n = shifted.shape
    cell = np.arange(reps * wordings).reshape(reps, wordings, 1) * length
    counts = np.bincount((cell + shifted).ravel(), minlength=reps * wordings * length)
    pmf = counts.reshape(reps, wordings, length) / n
    transform: np.ndarray = np.prod(_power(fft.rfft(pmf, axis=-1), n), axis=1)
    return transform


def exact_intervals(
    first: np.ndarray, second: np.ndarray, *, grid: int, alpha: float, chunk: int = 4
) -> ExactIntervals:
    """The exact stratified percentile bootstrap for each replicate. ``first`` and ``second`` are integer
    arrays of shape (replicates, wordings, runs per cell) on ``0..grid``.

    Each cell is shifted to start at 0, so a side's resampled total spans only ``n`` times the sum of its
    cells' ranges, and the transform is sized to that rather than to the whole lattice; replicates are
    taken in order of the size they need, ``chunk`` at a time, so the arrays stay small. The shift is added
    back exactly."""
    if first.shape != second.shape or first.ndim != 3:
        raise ValueError("both sides need the same (replicates, wordings, runs) shape")
    if min(first.min(), second.min()) < 0 or max(first.max(), second.max()) > grid:
        raise ValueError(f"values must lie on the lattice 0..{grid}")
    reps, wordings, n = first.shape
    scale = wordings * n * grid
    estimate = (first.sum(axis=(1, 2)) - second.sum(axis=(1, 2))) / scale
    low_first, low_second = first.min(axis=2), second.min(axis=2)
    shifted_first = first - low_first[:, :, None]
    shifted_second = second - low_second[:, :, None]
    span_first = n * (first.max(axis=2) - low_first).sum(
        axis=1
    )  # the shifted totals' largest values
    span_second = n * (second.max(axis=2) - low_second).sum(axis=1)
    offset = n * (low_first.sum(axis=1) - low_second.sum(axis=1))
    need = span_first + span_second + 1
    low = np.empty(reps)
    high = np.empty(reps)
    order = np.argsort(need, kind="stable")
    for start in range(0, reps, chunk):
        rows = order[start : start + chunk]
        length = _length(max(16, int(need[rows].max())))
        a = _side_transform(shifted_first[rows], length)
        b = _side_transform(shifted_second[rows], length)
        pmf = fft.irfft(
            a * np.conj(b), n=length, axis=-1
        )  # index k: a shifted difference of k, mod length
        s2 = span_second[rows]
        # Rotate each row so position j is the shifted difference j - s2, which runs from -s2 to s1.
        index = (np.arange(length)[None, :] - s2[:, None]) % length
        cdf = np.cumsum(np.take_along_axis(pmf, index, axis=1), axis=1)
        total = cdf[:, -1:]
        j_low = np.argmax(cdf >= (alpha / 2 - _TOLERANCE) * total, axis=1)
        j_high = np.argmax(cdf >= (1 - alpha / 2 - _TOLERANCE) * total, axis=1)
        low[rows] = (j_low - s2 + offset[rows]) / scale
        high[rows] = (j_high - s2 + offset[rows]) / scale
    return ExactIntervals(estimate, low, high)


# --- the share distributions --------------------------------------------------------------------------------


def rounded_beta_pmf(mean: float, sigma: float, grid: int) -> np.ndarray:
    """A Beta with this mean and standard deviation, rounded to the nearest point of ``0..grid``."""
    nu = mean * (1 - mean) / sigma**2 - 1
    if nu <= 0:
        raise ValueError(f"no Beta has mean {mean} and sd {sigma}")
    edges = (np.arange(grid + 2) - 0.5) / grid
    cdf = stats.beta.cdf(np.clip(edges, 0, 1), mean * nu, (1 - mean) * nu)
    pmf: np.ndarray = np.diff(cdf)
    result: np.ndarray = pmf / pmf.sum()
    return result


def _feasible(sigma: float) -> tuple[float, float]:
    """The Beta means at which a standard deviation of ``sigma`` exists, with a small margin."""
    if not 0 < sigma < 0.5:
        raise ValueError(f"sigma must be in (0, 0.5), not {sigma}")
    root = math.sqrt(1 - 4 * sigma**2)
    margin = 1e-6
    return (1 - root) / 2 + margin, (1 + root) / 2 - margin


def share_pmf(mean: float, sigma: float, pi: float, grid: int) -> np.ndarray | None:
    """The mixture's distribution on ``0..grid`` with mean exactly ``mean``; ``None`` when no Beta with this
    spread can give it."""
    if not 0 < mean < 1:
        return None
    lo, hi = _feasible(sigma)
    values = np.arange(grid + 1) / grid

    def gap(b: float) -> float:
        return float(rounded_beta_pmf(b, sigma, grid) @ values) - mean

    if not lo < hi or gap(lo) > 0 or gap(hi) < 0:
        return None
    b = optimize.brentq(gap, lo, hi, xtol=1e-14, rtol=1e-14)
    pmf = (1 - pi) * rounded_beta_pmf(b, sigma, grid)
    pmf[grid] += pi * mean
    pmf[0] += pi * (1 - mean)
    result: np.ndarray = pmf / pmf.sum()
    return result


def pmf_mean_sd(pmf: np.ndarray) -> tuple[float, float]:
    values = np.arange(pmf.size) / (pmf.size - 1)
    mean = float(pmf @ values)
    return mean, math.sqrt(max(0.0, float(pmf @ (values - mean) ** 2)))


def draw(pmf: np.ndarray, size: tuple[int, ...], rng: np.random.Generator) -> np.ndarray:
    """Lattice values (integers) drawn from ``pmf``."""
    drawn: np.ndarray = rng.choice(pmf.size, size=size, p=pmf)
    return drawn
