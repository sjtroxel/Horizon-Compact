"""The verdict engine (Phase 3 IMPLEMENTATION doc section 8; step 4).

Two layers. ``decide`` is tested on every boundary of `planning/07` section 6.2 with hand-written numbers.
The engine is tested on **known-answer sets built independently of it**: share cases whose verdict follows
from the range of the data alone (every resampled mean lies between a cell's smallest and largest value, so
the bootstrap's interval can be bounded by hand), and choice-rate cases whose interval comes from the test's
own Newcombe formula, never from the engine.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from typing import Any

import pytest
from scipy import stats

from horizon_compact.analysis.intervals import ALPHA, FAMILY_SIZE, comparison_seed
from horizon_compact.analysis.outcomes import outcomes_for
from horizon_compact.analysis.records import RunRow
from horizon_compact.analysis.verdict import (
    BOUNDARY_TOLERANCE,
    PRIMARY_PAIRS,
    SECONDARY_PAIRS,
    compare,
    compare_scenario,
    decide,
)
from horizon_compact.experiment import load_experiment

EXP = load_experiment("company")
S1 = outcomes_for(EXP.get_scenario("s1"))
S3 = outcomes_for(EXP.get_scenario("s3"))
T_SHARE, T_CHOICE = 0.10, 0.20
EPS = BOUNDARY_TOLERANCE

# --- decide(): every boundary of planning/07 section 6.2 ---------------------------------------------------


@pytest.mark.parametrize(
    ("d", "lo", "hi", "verdict"),
    [
        # split: excludes zero and reaches the threshold, either direction
        (0.30, 0.05, 0.55, "split"),
        (-0.30, -0.55, -0.05, "split"),
        # exactly at the threshold counts ("at least T")
        (0.10, 0.02, 0.18, "split"),
        (-0.10, -0.18, -0.02, "split"),
        # floating point a hair under the threshold still counts
        (0.10 - 1e-15, 0.02, 0.18, "split"),
        # but a real shortfall does not
        (0.10 - 1e-6, 0.02, 0.18, "inconclusive"),
        # an end exactly at zero does not exclude it, nor does one within the tolerance of it
        (0.30, 0.0, 0.55, "inconclusive"),
        (0.30, EPS / 2, 0.55, "inconclusive"),
        (-0.30, -0.55, 0.0, "inconclusive"),
        # just past zero does
        (0.30, 1e-6, 0.55, "split"),
        # no split: strictly inside plus or minus T
        (0.00, -0.08, 0.08, "no_split"),
        (0.02, -0.0999, 0.0999, "no_split"),
        # an end exactly at plus or minus T is not inside
        (0.00, -0.10, 0.08, "inconclusive"),
        (0.00, -0.08, 0.10, "inconclusive"),
        (0.00, -0.10 + EPS / 2, 0.08, "inconclusive"),
        # a real but small difference: excludes zero, inside plus or minus T, so no split
        (0.03, 0.01, 0.05, "no_split"),
        # excludes zero, below the threshold, reaching past it: inconclusive
        (0.06, 0.01, 0.12, "inconclusive"),
        # includes zero and reaches past the threshold
        (0.00, -0.25, 0.25, "inconclusive"),
        (0.05, -0.02, 0.14, "inconclusive"),
        # a zero-width interval at zero: no split (the all-agree case decision 10 settles)
        (0.00, 0.00, 0.00, "no_split"),
        # a zero-width interval far from zero: split
        (0.40, 0.40, 0.40, "split"),
    ],
)
def test_decide_on_every_boundary(d: float, lo: float, hi: float, verdict: str) -> None:
    assert decide(d, lo, hi, T_SHARE).verdict == verdict


def test_choice_rate_threshold_boundaries() -> None:
    assert decide(0.20, 0.01, 0.40, T_CHOICE).verdict == "split"
    assert decide(0.19999999999999996, 0.0014, 0.39, T_CHOICE).verdict == "split"
    assert decide(0.18, 0.01, 0.40, T_CHOICE).verdict == "inconclusive"
    assert decide(0.0, -0.19, 0.19, T_CHOICE).verdict == "no_split"
    assert decide(0.0, -0.20, 0.19, T_CHOICE).verdict == "inconclusive"


def test_a_difference_outside_its_own_interval_is_inconclusive_not_a_split() -> None:
    """A percentile interval can, rarely, exclude its own estimate. Neither verdict can then be trusted."""
    got = decide(0.30, 0.01, 0.20, T_SHARE)
    assert got.verdict == "inconclusive" and "outside its own interval" in got.reason
    # Without the guard this would also satisfy "no split" (inside plus or minus T) and "split" at once.
    assert decide(0.05, 0.06, 0.09, T_SHARE).verdict == "inconclusive"


def test_a_split_needs_the_difference_on_the_same_side_as_the_interval() -> None:
    """Held by the inside-its-own-interval guard: a negative difference cannot sit in an interval above 0."""
    assert decide(-0.30, 0.01, 0.40, T_SHARE).verdict == "inconclusive"


def test_split_and_no_split_never_both_hold() -> None:
    """Over a grid of numbers, a split always has hi >= T and so can never be inside plus or minus T."""
    grid = [x / 20 for x in range(-24, 25)]
    for lo in grid:
        for hi in grid:
            if lo > hi:
                continue
            for d in (lo, (lo + hi) / 2, hi):
                verdict = decide(d, lo, hi, T_SHARE).verdict
                if verdict == "split":
                    assert hi >= T_SHARE - EPS or lo <= -T_SHARE + EPS
                if verdict == "no_split":
                    assert lo > -T_SHARE and hi < T_SHARE


@pytest.mark.parametrize(
    ("d", "lo", "hi", "t"),
    [
        (0.1, 0.2, 0.1, 0.1),  # reversed interval
        (math.nan, 0.0, 0.1, 0.1),
        (0.1, -math.inf, 0.1, 0.1),
        (0.1, 0.0, 0.2, 0.0),  # no threshold
        (0.1, 0.0, 0.2, -0.1),
    ],
)
def test_decide_refuses_nonsense(d: float, lo: float, hi: float, t: float) -> None:
    with pytest.raises(ValueError):
        decide(d, lo, hi, t)


def test_every_decision_says_why() -> None:
    for args in [(0.3, 0.05, 0.55), (0.0, -0.08, 0.08), (0.0, -0.25, 0.25), (0.06, 0.01, 0.12)]:
        reason = decide(*args, T_SHARE).reason
        assert "threshold 0.10" in reason and "interval [" in reason


# --- the family -------------------------------------------------------------------------------------------


def test_the_family_is_four_pairs_times_four_scenarios() -> None:
    assert PRIMARY_PAIRS == (("A", "C"), ("A", "B"), ("C", "D"), ("B", "D"))
    assert SECONDARY_PAIRS == (("A", "D"),)
    assert len(PRIMARY_PAIRS) * len(EXP.scenarios) == FAMILY_SIZE
    named = {o.id for o in EXP.objectives}
    assert {x for pair in PRIMARY_PAIRS + SECONDARY_PAIRS for x in pair} <= named


# --- hand-built runs ---------------------------------------------------------------------------------------

_counter = iter(range(10**9))


def run(
    scenario: str, objective: str, wording: str, amounts: Mapping[str, float] | None, **kw: Any
) -> RunRow:
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
        "choice": kw.pop("choice", None),
        "first_amounts": amounts,
        "first_choice": None,
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


def hand_newcombe(c1: int, n1: int, c2: int, n2: int) -> tuple[float, float]:
    """The test's own Newcombe (Fagerland et al. 2011, eq. 7) at the family alpha: independent of the
    engine."""
    z = float(stats.norm.ppf(1 - ALPHA / 2))
    p1, p2 = c1 / n1, c2 / n2
    l1, u1 = _wilson(c1, n1, z)
    l2, u2 = _wilson(c2, n2, z)
    d = p1 - p2
    return d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), d + math.sqrt(
        (p2 - l2) ** 2 + (u1 - p1) ** 2
    )


W3 = ("w1", "w2", "w3")

# --- known answers, shares (S1, bootstrap) -----------------------------------------------------------------


def test_share_split_known_by_the_range_of_the_data() -> None:
    """Every A run keeps 100-125 people, every C run 0-25: any resampled difference is at least
    (100 - 25) / 125 = 0.6, so the interval's low end is at least 0.6. Split."""
    rows = s1_runs("A", {w: range(100, 126, 3) for w in W3}) + s1_runs(
        "C", {w: range(0, 26, 3) for w in W3}
    )
    got = compare(S1, rows, "A", "C", resamples=20_000)
    assert got.interval.low >= 0.6 and got.verdict == "split"
    assert got.difference > 0  # the sign convention: first named minus second named
    assert not got.degenerate_interval


def test_share_no_split_known_by_the_range_of_the_data() -> None:
    """A keeps 60-64, C 61-65: every resampled difference lies in [(60-65)/125, (64-61)/125] = [-0.04, 0.024],
    strictly inside plus or minus 0.10. No split."""
    rows = s1_runs("C", {w: [60, 61, 62, 63, 64] * 2 for w in W3}) + s1_runs(
        "D", {w: [61, 62, 63, 64, 65] * 2 for w in W3}
    )
    got = compare(S1, rows, "C", "D", resamples=20_000)
    assert got.interval.low >= -0.04 - EPS and got.interval.high <= 0.024 + EPS
    assert got.verdict == "no_split"


def test_share_inconclusive_when_runs_go_all_in_both_ways() -> None:
    """Each objective keeps everyone on half its runs and no one on the other half: the difference is 0
    and its standard error is about sqrt(2 x 0.25 / 30) = 0.13, so a 99.7% interval reaches about 0.38
    either side, far past 0.10. Inconclusive, and the reason says the interval includes zero."""
    rows = s1_runs("A", {w: [0, 125] * 5 for w in W3}) + s1_runs("B", {w: [125, 0] * 5 for w in W3})
    got = compare(S1, rows, "A", "B", resamples=20_000)
    assert got.difference == pytest.approx(0.0)
    assert got.interval.low < -0.2 and got.interval.high > 0.2
    assert got.verdict == "inconclusive" and "includes zero" in got.decision.reason


def test_share_all_agree_gives_a_zero_width_no_split_and_flags_it() -> None:
    """Every run under both objectives keeps all 125 people. The bootstrap returns [0, 0] and the rule, as
    written, says no split. This is the case decision 10 exists for: the engine does not hide it."""
    rows = s1_runs("C", {w: [125] * 10 for w in W3}) + s1_runs("D", {w: [125] * 10 for w in W3})
    got = compare(S1, rows, "C", "D", resamples=5_000)
    assert (got.interval.low, got.interval.high) == (0.0, 0.0)
    assert got.verdict == "no_split" and got.degenerate_interval


# --- known answers, choice rates (S3, Newcombe) -------------------------------------------------------------


@pytest.mark.parametrize(
    ("closes_first", "closes_second", "verdict"),
    [
        (54, 6, "split"),  # 90% against 10%
        (12, 0, "split"),  # exactly 20 points, interval excludes zero
        (57, 45, "split"),  # 0.19999999999999996 in floating point: exactly 20 points
        (0, 0, "no_split"),  # all agree, never close: still a real interval
        (60, 60, "no_split"),  # all agree, always close
        (3, 3, "no_split"),  # 5% each
        (30, 30, "inconclusive"),  # 50% each: the interval reaches about 25 points either side
        (8, 0, "inconclusive"),  # includes zero
        (10, 0, "inconclusive"),  # excludes zero, 16.7 points, interval past 20
    ],
)
def test_choice_rate_known_answers(closes_first: int, closes_second: int, verdict: str) -> None:
    rows = s3_runs("A", closes_first, 60) + s3_runs("C", closes_second, 60)
    got = compare(S3, rows, "A", "C")
    lo, hi = hand_newcombe(closes_first, 60, closes_second, 60)
    assert got.interval.low == pytest.approx(lo, abs=1e-12)
    assert got.interval.high == pytest.approx(hi, abs=1e-12)
    assert got.difference == pytest.approx((closes_first - closes_second) / 60)
    assert got.verdict == verdict
    assert not got.degenerate_interval  # Newcombe never collapses, even when all agree


def test_choice_rate_all_agree_has_real_width() -> None:
    got = compare(S3, s3_runs("C", 0, 60) + s3_runs("D", 0, 60), "C", "D")
    assert got.interval.width > 0.25
    assert got.verdict == "no_split"


def test_choice_rates_pool_counts_across_wordings() -> None:
    """Decision 5: choice rates pool counts, as Newcombe's method needs, even when wordings hold unequal
    runs."""
    a = s3_runs("A", 4, 5, ("w1",)) + s3_runs("A", 3, 15, ("w3",))
    b = s3_runs("B", 1, 10, ("w1",)) + s3_runs("B", 2, 10, ("w3",))
    got = compare(S3, a + b, "A", "B")
    assert got.difference == pytest.approx(7 / 20 - 3 / 20)
    lo, hi = hand_newcombe(7, 20, 3, 20)
    assert got.interval.low == pytest.approx(lo) and got.interval.high == pytest.approx(hi)
    assert got.valid_runs == (("w1", 5, 10), ("w3", 15, 10))


# --- what the engine reads, and what it refuses ------------------------------------------------------------


def test_failed_runs_are_not_read_and_valid_runs_are_counted_by_wording() -> None:
    rows = s3_runs("A", 30, 30) + s3_runs("C", 0, 30)
    rows += [run("s3", "A", "w1", None), run("s3", "C", "w2", None)]  # failures: never scored here
    got = compare(S3, rows, "A", "C")
    assert got.valid_runs == (("w1", 10, 10), ("w2", 10, 10), ("w3", 10, 10))


def test_other_scenarios_and_objectives_are_ignored() -> None:
    rows = s3_runs("A", 30, 30) + s3_runs("C", 0, 30) + s3_runs("B", 30, 30)
    rows += s1_runs("A", {"w1": [1, 2]})
    got = compare(S3, rows, "A", "C")
    assert sum(n for _w, n, _m in got.valid_runs) == 30


def test_a_wording_with_no_valid_run_on_one_side_is_refused_not_dropped_quietly() -> None:
    rows = s3_runs("A", 3, 9) + s3_runs("C", 1, 6, ("w1", "w2"))
    with pytest.raises(ValueError, match="no valid run under w3"):
        compare(S3, rows, "A", "C")
    # The failure rules drop it from both sides by naming the wordings to compare (decision 6).
    got = compare(S3, rows, "A", "C", wordings=["w1", "w2"])
    assert got.wordings == ("w1", "w2")


def test_runs_from_two_sweeps_or_two_models_are_refused() -> None:
    rows = s3_runs("A", 3, 9) + s3_runs("C", 1, 9)
    other = [run("s3", "C", "w1", rows[-1].amounts, choice="close", sweep_id="another")]
    with pytest.raises(ValueError, match="sweep_ids"):
        compare(S3, rows + other, "A", "C")
    other = [run("s3", "C", "w1", rows[-1].amounts, choice="close", model_key="nova-pro")]
    with pytest.raises(ValueError, match="model_keys"):
        compare(S3, rows + other, "A", "C")


def test_a_comparison_needs_two_objectives_and_some_runs() -> None:
    with pytest.raises(ValueError):
        compare(S3, s3_runs("A", 3, 9), "A", "A")
    with pytest.raises(ValueError, match="no runs"):
        compare(S3, s3_runs("A", 3, 9), "B", "D")


# --- seeds, the sealed wording, and the whole scenario ------------------------------------------------------


def test_the_bootstrap_seed_comes_from_the_sweep_and_the_comparison() -> None:
    rows = s1_runs("A", {w: [10, 50, 90] for w in W3}) + s1_runs(
        "C", {w: [20, 60, 100] for w in W3}
    )
    one = compare(S1, rows, "A", "C", resamples=5_000)
    again = compare(S1, rows, "A", "C", resamples=5_000)
    assert one == again
    assert one.interval.seed == comparison_seed("pilot-test-sweep", "s1:A-C")
    sealed = compare(S1, rows, "A", "C", wordings=["w2"], name="s1:A-C:sealed", resamples=5_000)
    assert sealed.interval.seed == comparison_seed("pilot-test-sweep", "s1:A-C:sealed")
    assert sealed.wordings == ("w2",) and sealed.valid_runs == (("w2", 3, 3),)


def test_compare_scenario_gives_the_four_primary_then_the_expected_comparison() -> None:
    rows: list[RunRow] = []
    for objective, closes in (("A", 50), ("B", 30), ("C", 40), ("D", 20)):
        rows += s3_runs(objective, closes, 60)
    got = compare_scenario(S3, rows)
    assert [(c.first, c.second, c.role) for c in got] == [
        ("A", "C", "primary"),
        ("A", "B", "primary"),
        ("C", "D", "primary"),
        ("B", "D", "primary"),
        ("A", "D", "secondary"),
    ]
    assert got[-1].label == "secondary: the expected comparison"
    assert [round(c.difference, 4) for c in got] == [round(x / 60, 4) for x in (10, 20, 20, 10, 30)]
    assert all(
        c.kind == "choice_rate" and c.threshold == T_CHOICE and c.outcome == "close rate"
        for c in got
    )
