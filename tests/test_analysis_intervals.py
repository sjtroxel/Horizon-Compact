"""The interval methods against published values, an independent formula, scipy, and an exact enumeration
(Phase 3 IMPLEMENTATION doc section 7; sources in docs/phases/evidence/phase-3/worked-examples.md)."""

from __future__ import annotations

import itertools
import math

import numpy as np
import pytest
from scipy import stats

from horizon_compact.analysis.intervals import (
    ALPHA,
    FAMILY_SIZE,
    RESAMPLES,
    Z,
    comparison_seed,
    mean_of_wording_means,
    newcombe_difference,
    stratified_bootstrap_difference,
)

# --- the frozen fine print (decision 7) ------------------------------------------------------------------


def test_alpha_is_exactly_005_over_16_and_z_follows_from_it() -> None:
    assert FAMILY_SIZE == 16
    assert ALPHA == 0.003125
    assert pytest.approx(2.9552, abs=5e-5) == Z
    assert RESAMPLES == 100_000


# --- Newcombe: published values ----------------------------------------------------------------------------

# Newcombe (1998) Table II, method 10 (score, no continuity correction), 95%, as reproduced in the pairwiseCI
# package's documentation with a citation to page 877. Columns (a), (b) and (h).
TABLE_II = [
    ((56, 70, 48, 80), (0.0524, 0.3339)),
    ((9, 10, 3, 10), (0.1705, 0.8090)),
    ((10, 10, 0, 10), (0.6075, 1.0000)),
]


@pytest.mark.parametrize(("counts", "published"), TABLE_II)
def test_newcombe_matches_newcombe_1998_table_ii(
    counts: tuple[int, int, int, int], published: tuple[float, float]
) -> None:
    got = newcombe_difference(*counts, alpha=0.05)
    assert (round(got.low, 4), round(got.high, 4)) == published


def test_newcombe_matches_fagerland_lydersen_laake_2011_table_3() -> None:
    """7/34 against 1/34: 0.019 to 0.34, estimate 0.18, as printed (two significant figures)."""
    got = newcombe_difference(7, 34, 1, 34, alpha=0.05)
    assert round(got.estimate, 2) == 0.18
    assert (round(got.low, 3), round(got.high, 2)) == (0.019, 0.34)


# --- Newcombe: against the formula, written independently ------------------------------------------------


def _wilson(count: int, total: int, z: float) -> tuple[float, float]:
    p = count / total
    centre = (p + z * z / (2 * total)) / (1 + z * z / total)
    half = z / (1 + z * z / total) * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total))
    return centre - half, centre + half


def _hybrid(c1: int, n1: int, c2: int, n2: int, alpha: float) -> tuple[float, float]:
    """Fagerland, Lydersen and Laake (2011), equation 7: two Wilson intervals combined."""
    z = float(stats.norm.ppf(1 - alpha / 2))
    p1, p2 = c1 / n1, c2 / n2
    l1, u1 = _wilson(c1, n1, z)
    l2, u2 = _wilson(c2, n2, z)
    d = p1 - p2
    return (
        d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2),
        d + math.sqrt((p2 - l2) ** 2 + (u1 - p1) ** 2),
    )


# Newcombe (1998) Table II's eight columns, (a) to (h), plus Fagerland's example.
FORMULA_CASES = [
    (56, 70, 48, 80),
    (9, 10, 3, 10),
    (6, 7, 2, 7),
    (5, 56, 0, 29),
    (0, 10, 0, 20),
    (0, 10, 0, 10),
    (10, 10, 0, 20),
    (10, 10, 0, 10),
    (7, 34, 1, 34),
]


@pytest.mark.parametrize("alpha", [0.05, ALPHA])
@pytest.mark.parametrize("counts", FORMULA_CASES)
def test_newcombe_matches_the_hand_written_formula(
    counts: tuple[int, int, int, int], alpha: float
) -> None:
    got = newcombe_difference(*counts, alpha=alpha)
    low, high = _hybrid(*counts, alpha)
    assert got.low == pytest.approx(low, abs=1e-12)
    assert got.high == pytest.approx(high, abs=1e-12)


def test_newcombe_defaults_to_the_family_alpha_and_is_wider_than_95() -> None:
    narrow = newcombe_difference(56, 70, 48, 80, alpha=0.05)
    wide = newcombe_difference(56, 70, 48, 80)
    assert wide.alpha == ALPHA and wide.method == "newcombe"
    assert wide.low < narrow.low and wide.high > narrow.high


# --- Newcombe: the edges, where a bootstrap would collapse --------------------------------------------------


@pytest.mark.parametrize(
    "counts",
    [
        (0, 20, 0, 20),
        (20, 20, 20, 20),
        (0, 20, 20, 20),
        (20, 20, 0, 20),
        (0, 6, 6, 6),
        (1, 60, 0, 60),
    ],
)
def test_newcombe_never_has_zero_width_and_stays_inside_minus_one_to_one(
    counts: tuple[int, int, int, int],
) -> None:
    got = newcombe_difference(*counts)
    assert got.width > 0.05
    assert -1.0 <= got.low <= got.estimate <= got.high <= 1.0


def test_newcombe_all_agree_is_symmetric_around_zero() -> None:
    """Every run in both groups makes the same choice: the estimate is 0 and the interval is not."""
    got = newcombe_difference(20, 20, 20, 20)
    assert got.estimate == 0.0
    assert got.low == pytest.approx(-got.high)


@pytest.mark.parametrize("counts", [(1, 0, 0, 5), (6, 5, 0, 5), (-1, 5, 0, 5), (0, 5, 0, 0)])
def test_newcombe_refuses_impossible_counts(counts: tuple[int, int, int, int]) -> None:
    with pytest.raises(ValueError):
        newcombe_difference(*counts)


# --- the bootstrap: the objective's value (decision 5) -----------------------------------------------------


def test_each_wording_counts_equally_however_many_runs_it_holds() -> None:
    cells = {"w1": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0], "w2": [0.0], "w3": [0.5, 0.5]}
    assert mean_of_wording_means(cells) == pytest.approx(0.5)
    pooled = sum(sum(v) for v in cells.values()) / sum(len(v) for v in cells.values())
    assert pooled != pytest.approx(0.5)  # the pooled mean would weight w1 six times


# --- the bootstrap: an exact answer, by enumeration --------------------------------------------------------


def _exact_quantile(first: list[float], second: list[float], p: float) -> tuple[float, float]:
    """The p quantile of the exact bootstrap distribution (every equally likely resample enumerated), and how
    far the cumulative probability is from p at that point (the margin a Monte Carlo estimate needs)."""

    def means(values: list[float]) -> list[float]:
        return [sum(draw) / len(draw) for draw in itertools.product(values, repeat=len(values))]

    diffs = sorted(a - b for a in means(first) for b in means(second))
    support = sorted(set(diffs))
    total = len(diffs)
    cdf = 0.0
    for value in support:
        below = cdf
        cdf += diffs.count(value) / total
        if cdf >= p:
            return value, min(p - below, cdf - p)
    return support[-1], 0.0


def test_one_wording_three_runs_each_matches_the_enumerated_distribution() -> None:
    first, second = [0.0, 0.5, 1.0], [0.0, 0.0, 1.0]
    got = stratified_bootstrap_difference(
        {"w1": first}, {"w1": second}, seed=11, alpha=0.05, resamples=RESAMPLES
    )
    low, low_margin = _exact_quantile(first, second, 0.025)
    high, high_margin = _exact_quantile(first, second, 0.975)
    # A Monte Carlo quantile lands on the exact value when the CDF is not within its error of p.
    assert low_margin > 0.003 and high_margin > 0.003
    assert got.low == pytest.approx(low, abs=1e-12)
    assert got.high == pytest.approx(high, abs=1e-12)
    assert got.estimate == pytest.approx(0.5 - 1 / 3)


# --- the bootstrap: against scipy on unstratified data -----------------------------------------------------


@pytest.mark.parametrize("alpha", [0.05, ALPHA])
def test_one_wording_agrees_with_scipy_percentile_bootstrap(alpha: float) -> None:
    data = np.random.default_rng(2026)
    first = data.beta(2, 5, size=20)
    second = data.beta(3, 4, size=15)

    def difference(x: np.ndarray, y: np.ndarray, axis: int) -> np.ndarray:
        result: np.ndarray = np.mean(x, axis=axis) - np.mean(y, axis=axis)
        return result

    reference = stats.bootstrap(
        (first, second),
        difference,
        n_resamples=RESAMPLES,
        confidence_level=1 - alpha,
        method="percentile",
        vectorized=True,
        rng=np.random.default_rng(5),
    ).confidence_interval
    got = stratified_bootstrap_difference(
        {"w1": first.tolist()}, {"w1": second.tolist()}, seed=5, alpha=alpha
    )
    # Different generators draw differently, so the two agree within Monte Carlo error, not exactly.
    tolerance = 0.006 if alpha == 0.05 else 0.012
    assert got.low == pytest.approx(reference.low, abs=tolerance)
    assert got.high == pytest.approx(reference.high, abs=tolerance)


# --- the bootstrap: stratification, seeds, refusals --------------------------------------------------------


def test_stratification_resamples_within_wording_only() -> None:
    """Each wording's runs are constant, so a within-wording resample never changes a wording's mean: the
    interval has zero width. A pooled resample would mix wordings and give a wide interval."""
    first = {"w1": [0.2] * 5, "w2": [0.8] * 5}
    second = {"w1": [0.1] * 5, "w2": [0.3] * 5}
    got = stratified_bootstrap_difference(first, second, seed=1, resamples=2_000)
    assert got.low == pytest.approx(0.3) and got.high == pytest.approx(0.3)


def test_all_agree_gives_a_zero_width_interval_the_known_failure_for_decision_10() -> None:
    """Every run on both sides keeps all 125 people: the bootstrap returns [0, 0]. Kept visible on purpose;
    decision 10 decides from the simulations what the engine does in this case."""
    first = {w: [1.0] * 10 for w in ("w1", "w2", "w3")}
    got = stratified_bootstrap_difference(first, dict(first), seed=3, resamples=1_000)
    assert (got.low, got.high, got.width) == (0.0, 0.0, 0.0)


def test_the_same_seed_gives_the_same_interval_and_the_seed_comes_from_names() -> None:
    first = {"w1": [0.1, 0.4, 0.5], "w3": [0.2, 0.9]}
    second = {"w1": [0.3, 0.3, 0.6], "w3": [0.0, 0.1, 0.2]}
    seed = comparison_seed("pilot-sonnet-4-6-abcd1234", "s1:A-C")
    one = stratified_bootstrap_difference(first, second, seed=seed, resamples=5_000)
    two = stratified_bootstrap_difference(first, second, seed=seed, resamples=5_000)
    assert one == two and one.seed == seed and one.resamples == 5_000
    assert seed == comparison_seed("pilot-sonnet-4-6-abcd1234", "s1:A-C")
    assert seed != comparison_seed("pilot-sonnet-4-6-abcd1234", "s1:C-D")
    assert seed != comparison_seed("pilot-sonnet-4-6-abcd1235", "s1:A-C")


def test_the_bootstrap_defaults_to_the_family_alpha_and_the_resample_count() -> None:
    got = stratified_bootstrap_difference({"w1": [0.0, 1.0]}, {"w1": [0.0, 0.5]}, seed=2)
    assert (got.alpha, got.resamples, got.method) == (ALPHA, RESAMPLES, "stratified_bootstrap")


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ({"w1": [0.1]}, {"w2": [0.1]}),  # different wordings: not like with like
        ({"w1": [0.1], "w3": [0.2]}, {"w1": [0.1]}),
        ({"w1": []}, {"w1": [0.1]}),  # an empty cell
        ({}, {}),
        ({"w1": [float("nan")]}, {"w1": [0.1]}),
    ],
)
def test_the_bootstrap_refuses_what_is_not_a_like_with_like_comparison(
    first: dict[str, list[float]], second: dict[str, list[float]]
) -> None:
    with pytest.raises(ValueError):
        stratified_bootstrap_difference(first, second, seed=1, resamples=10)
