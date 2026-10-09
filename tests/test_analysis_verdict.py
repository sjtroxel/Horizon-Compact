"""The verdict engine (Phase 3 IMPLEMENTATION doc section 8; step 4).

Two layers. ``decide`` is tested on every boundary of `planning/07` section 6.2 with hand-written numbers.
The engine is tested on **known-answer sets built independently of it**: share cases whose interval comes
from the test's own Welch arithmetic (``hand_welch``, written from the formula with the standard library's
exact variance), and choice-rate cases whose interval comes from the test's own Newcombe formula, never
from the engine. Decision 10's two rules (step 12) are tested on cases that isolate each.
"""

from __future__ import annotations

import math

import pytest

from analysis_helpers import W3, hand_newcombe, hand_welch, run, s1_runs, s3_runs
from horizon_compact.analysis import verdict as verdict_module
from horizon_compact.analysis.intervals import FAMILY_SIZE
from horizon_compact.analysis.outcomes import outcomes_for
from horizon_compact.analysis.records import RunRow
from horizon_compact.analysis.verdict import (
    BOUNDARY_TOLERANCE,
    PRIMARY_PAIRS,
    SECONDARY_PAIRS,
    SHARE_FLOOR,
    Comparison,
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


# --- known answers, shares (S1, Welch) ---------------------------------------------------------------------


def shares(kept: dict[str, list[int]]) -> dict[str, list[float]]:
    return {w: [k / 125 for k in ks] for w, ks in kept.items()}


def check_welch(got: Comparison, first: dict[str, list[int]], second: dict[str, list[int]]) -> None:
    """The engine's interval against the test's own Welch arithmetic, on the same people counts."""
    d, lo, hi, df = hand_welch(shares(first), shares(second))
    assert got.interval.method == "welch"
    assert got.difference == pytest.approx(d, abs=1e-12)
    assert got.interval.low == pytest.approx(lo, abs=1e-12)
    assert got.interval.high == pytest.approx(hi, abs=1e-12)
    assert got.interval.df == (None if df is None else pytest.approx(df))


def test_share_split_known_by_the_tests_own_welch() -> None:
    """A keeps 100-124 people, C 0-24, nine runs a wording: a difference of 100 / 125 = 0.8 with a standard
    error near 0.03. Split, with the sign of first named minus second named."""
    a = {w: list(range(100, 126, 3)) for w in W3}
    c = {w: list(range(0, 26, 3)) for w in W3}
    got = compare(S1, s1_runs("A", a) + s1_runs("C", c), "A", "C")
    check_welch(got, a, c)
    assert got.difference == pytest.approx(0.8) and got.verdict == "split"
    assert not got.degenerate_interval and not got.floor_applied and got.constant_value is None


def test_share_no_split_known_by_the_tests_own_welch() -> None:
    """C keeps 60-64, D 61-65, ten runs a wording: a difference of -1 / 125 and an interval about 0.02 either
    side, strictly inside plus or minus 0.10 and wider than the floor of 1 / 125. No split."""
    c = {w: [60, 61, 62, 63, 64] * 2 for w in W3}
    d = {w: [61, 62, 63, 64, 65] * 2 for w in W3}
    got = compare(S1, s1_runs("C", c) + s1_runs("D", d), "C", "D")
    check_welch(got, c, d)
    assert got.interval.width > SHARE_FLOOR
    assert got.verdict == "no_split" and not got.floor_applied and got.constant_check is None


def test_share_inconclusive_when_runs_go_all_in_both_ways() -> None:
    """Each objective keeps everyone on half its runs and no one on the other half: the difference is 0
    and its standard error is about sqrt(2 x 0.25 / 30) = 0.13, so a 99.7% interval reaches about 0.4
    either side, far past 0.10. Inconclusive, and the reason says the interval includes zero."""
    a = {w: [0, 125] * 5 for w in W3}
    b = {w: [125, 0] * 5 for w in W3}
    got = compare(S1, s1_runs("A", a) + s1_runs("B", b), "A", "B")
    check_welch(got, a, b)
    assert got.difference == pytest.approx(0.0)
    assert got.interval.low < -0.2 and got.interval.high > 0.2
    assert got.verdict == "inconclusive" and "includes zero" in got.decision.reason


def test_share_with_unequal_cells_weights_wordings_equally() -> None:
    """Decision 5: each wording's mean counts once, whatever its cell holds, and Welch-Satterthwaite reads
    each cell's own size."""
    a = {"w1": [100, 110, 120], "w2": [90, 95, 100, 105, 110, 115], "w3": [80, 100]}
    c = {"w1": [40, 50], "w2": [30, 60, 45, 35], "w3": [20, 30, 40, 50, 60]}
    got = compare(S1, s1_runs("A", a) + s1_runs("C", c), "A", "C")
    check_welch(got, a, c)
    assert got.valid_runs == (("w1", 3, 2), ("w2", 6, 4), ("w3", 2, 5))


# --- decision 10: the two all-agree rules (section 20b) -------------------------------------------------


def test_share_all_agree_is_never_a_no_split_by_both_rules() -> None:
    """Every run under both objectives keeps all 125 people: Welch's [0, 0], which reads as a no split. Rule
    (a) refuses it, since the interval is narrower than one person; rule (b) compares the share of runs at
    125, 30 of 30 against 30 of 30, by Newcombe, whose interval reaches past 0.10. Inconclusive both ways,
    and the zero width is still flagged."""
    c = d = {w: [125] * 10 for w in W3}
    got = compare(S1, s1_runs("C", c) + s1_runs("D", d), "C", "D")
    check_welch(got, c, d)
    assert (got.interval.low, got.interval.high) == (0.0, 0.0) and got.degenerate_interval
    assert got.floor_applied and got.constant_value == 1.0
    lo, hi = hand_newcombe(30, 30, 30, 30)
    assert lo < -T_SHARE and hi > T_SHARE
    assert got.constant_check is not None and got.constant_check.verdict == "inconclusive"
    assert got.verdict == "inconclusive" and "decision 10" in got.decision.reason


def test_the_floor_turns_a_narrow_no_split_inconclusive_even_without_a_constant_side() -> None:
    """C and D each keep 62 or 63 people, alternately: a difference of 0 and a half-width about 0.004, so
    the interval is narrower than 1 / 125 though neither side is constant. Rule (a) alone."""
    c = d = {w: [62, 63] * 10 for w in W3}
    got = compare(S1, s1_runs("C", c) + s1_runs("D", d), "C", "D")
    check_welch(got, c, d)
    assert 0 < got.interval.width < SHARE_FLOOR
    assert got.floor_applied and got.constant_value is None and got.constant_check is None
    assert got.verdict == "inconclusive" and "rule (a)" in got.decision.reason


def test_the_floor_counts_a_width_at_the_floor_as_narrower(monkeypatch: pytest.MonkeyPatch) -> None:
    """A boundary counts against the stronger verdict (section 6.2): a width equal to the floor, within the
    tolerance, cannot support a no split; one a hair wider than the tolerance can."""
    c = {w: [60, 61, 62, 63, 64] * 2 for w in W3}
    d = {w: [61, 62, 63, 64, 65] * 2 for w in W3}
    rows = s1_runs("C", c) + s1_runs("D", d)
    width = compare(S1, rows, "C", "D").interval.width
    monkeypatch.setattr(verdict_module, "SHARE_FLOOR", width)
    assert compare(S1, rows, "C", "D").floor_applied
    monkeypatch.setattr(verdict_module, "SHARE_FLOOR", width - 2 * EPS)
    assert not compare(S1, rows, "C", "D").floor_applied


def test_the_constant_check_keeps_a_split_both_methods_agree_on() -> None:
    """A keeps everyone, C no one: Welch gives [1, 1] and a split; rule (b) reads A's value, 1, and compares
    30 of 30 against 0 of 30, also a split. The same verdict, kept."""
    a = {w: [125] * 10 for w in W3}
    c = {w: [0] * 10 for w in W3}
    got = compare(S1, s1_runs("A", a) + s1_runs("C", c), "A", "C")
    assert got.degenerate_interval and not got.floor_applied
    assert got.constant_value == 1.0  # the first objective's value, when both are constant
    assert got.constant_check is not None and got.constant_check.verdict == "split"
    assert got.verdict == "split"


def test_the_constant_check_reads_the_second_side_when_only_it_is_constant() -> None:
    """D keeps 100 people on every run; C varies around 100 with a third of its runs at exactly 100. Welch
    calls it a no split (difference 0, interval about 0.02 either side). Rule (b) compares the share of runs
    at 100: 36 of 36 for D, 12 of 36 for C, a split. The two disagree, so the comparison is inconclusive."""
    c = {w: [95, 100, 105] * 4 for w in W3}
    d = {w: [100] * 12 for w in W3}
    got = compare(S1, s1_runs("C", c) + s1_runs("D", d), "C", "D")
    check_welch(got, c, d)
    assert not got.floor_applied and got.constant_value == pytest.approx(0.8)
    assert got.constant_check is not None and got.constant_check.verdict == "split"
    lo, _ = hand_newcombe(12, 36, 36, 36)
    assert lo < 0  # the test's own Newcombe: C's 12 of 36 against D's 36 of 36, well apart
    assert got.verdict == "inconclusive" and "disagree" in got.decision.reason


def test_the_constant_check_reads_an_interior_value_not_only_a_boundary() -> None:
    """Every run of both objectives keeps exactly 100 people (0.8): rule (b) applies away from 0 and 1."""
    c = d = {w: [100] * 10 for w in W3}
    got = compare(S1, s1_runs("C", c) + s1_runs("D", d), "C", "D")
    assert got.constant_value == pytest.approx(0.8) and got.verdict == "inconclusive"


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
    # Decision 10's rules are for shares; Newcombe needs neither.
    assert not got.floor_applied and got.constant_value is None and got.constant_check is None


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


# --- determinism, the sealed wording, and the whole scenario ------------------------------------------------


def test_a_comparison_is_fixed_by_its_data_and_can_be_narrowed_to_named_wordings() -> None:
    rows = s1_runs("A", {w: [10, 50, 90] for w in W3}) + s1_runs(
        "C", {w: [20, 60, 100] for w in W3}
    )
    assert compare(S1, rows, "A", "C") == compare(S1, rows, "A", "C")
    sealed = compare(S1, rows, "A", "C", wordings=["w2"])
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
