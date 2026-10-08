"""The exact lattice bootstrap and the share distributions (Phase 3 doc 14.1, step 10)."""

from __future__ import annotations

import itertools

import numpy as np
import pytest

from horizon_compact.analysis.intervals import ALPHA, stratified_bootstrap_difference
from horizon_compact.simulation.exact import (
    S1_GRID,
    _length,
    _power,
    exact_intervals,
    pmf_mean_sd,
    rounded_beta_pmf,
    share_pmf,
)


def _totals(values: np.ndarray) -> dict[int, float]:
    """One side's resampled total, exactly: every one of each wording's n^n equally likely resamples."""
    wordings, n = values.shape
    dist = {0: 1.0}
    for w in range(wordings):
        cell: dict[int, float] = {}
        for picks in itertools.product(range(n), repeat=n):
            t = int(sum(values[w, i] for i in picks))
            cell[t] = cell.get(t, 0.0) + 1 / n**n
        nxt: dict[int, float] = {}
        for a, pa in dist.items():
            for b, pb in cell.items():
                nxt[a + b] = nxt.get(a + b, 0.0) + pa * pb
        dist = nxt
    return dist


def brute_force(
    first: np.ndarray, second: np.ndarray, grid: int, alpha: float
) -> tuple[float, float]:
    """The percentile interval of the difference, from the full enumeration (no FFT)."""
    a, b = _totals(first), _totals(second)
    diff: dict[int, float] = {}
    for x, px in a.items():
        for y, py in b.items():
            diff[x - y] = diff.get(x - y, 0.0) + px * py
    keys = sorted(diff)
    cdf = np.cumsum([diff[k] for k in keys])
    scale = first.size * grid
    lo = keys[int(np.argmax(cdf >= alpha / 2 - 1e-12))] / scale
    hi = keys[int(np.argmax(cdf >= 1 - alpha / 2 - 1e-12))] / scale
    return lo, hi


@pytest.mark.parametrize("alpha", [ALPHA, 0.05, 0.2])
def test_the_exact_interval_equals_a_full_enumeration(alpha: float) -> None:
    # Three wordings of three runs a side on a lattice of 10: 27^3 resamples per side, enumerated.
    rng = np.random.default_rng(4)
    for _ in range(4):
        first = rng.integers(0, 11, (3, 3))
        second = rng.integers(0, 11, (3, 3))
        got = exact_intervals(first[None], second[None], grid=10, alpha=alpha)
        assert (float(got.low[0]), float(got.high[0])) == pytest.approx(
            brute_force(first, second, 10, alpha), abs=1e-12
        )
        assert float(got.estimate[0]) == pytest.approx((first.mean() - second.mean()) / 10)


def test_the_exact_interval_is_the_engines_limit() -> None:
    # The engine at 1,000,000 resamples lands within its Monte Carlo error (about 0.001 here) of the exact
    # ends; at 100,000 the error is about three times larger. Both differences are measured, not assumed.
    rng = np.random.default_rng(9)
    pmf_a, pmf_b = share_pmf(0.5, 0.15, 0.2, S1_GRID), share_pmf(0.4, 0.15, 0.2, S1_GRID)
    assert pmf_a is not None and pmf_b is not None
    first = rng.choice(S1_GRID + 1, size=(2, 3, 10), p=pmf_a)
    second = rng.choice(S1_GRID + 1, size=(2, 3, 10), p=pmf_b)
    exact = exact_intervals(first, second, grid=S1_GRID, alpha=ALPHA)
    for r in range(2):
        iv = stratified_bootstrap_difference(
            {f"w{w}": list(first[r, w] / S1_GRID) for w in range(3)},
            {f"w{w}": list(second[r, w] / S1_GRID) for w in range(3)},
            seed=r,
            resamples=1_000_000,
        )
        assert iv.estimate == pytest.approx(float(exact.estimate[r]), abs=1e-12)
        assert abs(iv.low - float(exact.low[r])) < 0.004
        assert abs(iv.high - float(exact.high[r])) < 0.004


def test_identical_runs_give_a_zero_width_interval_as_the_engine_does() -> None:
    same = np.full((1, 3, 6), 125)
    got = exact_intervals(same, same, grid=S1_GRID, alpha=ALPHA)
    assert (float(got.low[0]), float(got.high[0]), float(got.estimate[0])) == (0.0, 0.0, 0.0)


def test_chunks_do_not_change_the_answer() -> None:
    rng = np.random.default_rng(1)
    first, second = rng.integers(0, 126, (7, 3, 6)), rng.integers(0, 126, (7, 3, 6))
    one = exact_intervals(first, second, grid=S1_GRID, alpha=ALPHA, chunk=7)
    two = exact_intervals(first, second, grid=S1_GRID, alpha=ALPHA, chunk=2)
    assert np.array_equal(one.low, two.low) and np.array_equal(one.high, two.high)


def test_off_lattice_values_and_mismatched_shapes_are_refused() -> None:
    with pytest.raises(ValueError, match="lattice"):
        exact_intervals(
            np.full((1, 3, 2), 126), np.zeros((1, 3, 2), int), grid=S1_GRID, alpha=ALPHA
        )
    with pytest.raises(ValueError, match="shape"):
        exact_intervals(
            np.zeros((1, 3, 2), int), np.zeros((1, 3, 3), int), grid=S1_GRID, alpha=ALPHA
        )


def test_power_by_squaring_and_the_transform_length() -> None:
    z = np.exp(1j * np.linspace(0, 3, 7)) * np.linspace(0.2, 1.0, 7)
    for n in (1, 2, 5, 6, 10, 15, 20):
        assert np.allclose(_power(z, n), z**n, rtol=1e-12, atol=1e-15)
    for points in (4501, 7501, 11251, 15001):
        length = _length(points)
        assert length >= points
        rest = length
        for f in (2, 3, 5):
            while rest % f == 0:
                rest //= f
        assert rest == 1


# --- the share distributions --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("mean", "sigma", "pi"),
    [(0.1, 0.02, 0.0), (0.1, 0.25, 0.5), (0.5, 0.15, 0.2), (0.9, 0.25, 0.2), (0.95, 0.2, 0.0)],
)
def test_the_mixture_mean_is_exact_on_the_lattice(mean: float, sigma: float, pi: float) -> None:
    pmf = share_pmf(mean, sigma, pi, S1_GRID)
    assert pmf is not None
    assert pmf.sum() == pytest.approx(1.0, abs=1e-12)
    assert pmf_mean_sd(pmf)[0] == pytest.approx(mean, abs=1e-12)
    assert pmf.min() >= 0


def test_without_all_in_the_spread_is_close_to_sigma() -> None:
    # Rounding to 1/125 adds a variance of about 1/(12 * 125^2): negligible beside sigma >= 0.05.
    for sigma in (0.05, 0.10, 0.15, 0.25):
        pmf = share_pmf(0.5, sigma, 0.0, S1_GRID)
        assert pmf is not None
        assert pmf_mean_sd(pmf)[1] == pytest.approx(sigma, rel=0.01)


def test_the_all_in_part_sits_at_0_and_1_in_proportion_to_the_mean() -> None:
    beta = share_pmf(0.3, 0.1, 0.0, S1_GRID)
    mixed = share_pmf(0.3, 0.1, 0.5, S1_GRID)
    assert beta is not None and mixed is not None
    assert mixed[S1_GRID] == pytest.approx(0.5 * beta[S1_GRID] + 0.5 * 0.3, abs=1e-12)
    assert mixed[0] == pytest.approx(0.5 * beta[0] + 0.5 * 0.7, abs=1e-12)


def test_an_impossible_mean_and_spread_is_none_not_faked() -> None:
    assert share_pmf(0.95, 0.25, 0.0, S1_GRID) is None  # 0.95 * 0.05 < 0.25^2
    assert share_pmf(0.0, 0.1, 0.0, S1_GRID) is None
    assert share_pmf(1.0, 0.1, 0.0, S1_GRID) is None
    with pytest.raises(ValueError):
        rounded_beta_pmf(0.5, 0.6, S1_GRID)
