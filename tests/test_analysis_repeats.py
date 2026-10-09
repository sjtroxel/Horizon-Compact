"""The repeat rule (Phase 3 doc 12, step 8; on the t quantile since step 12, section 20b item 5) on hand-built
runs, answers worked out by hand: each count is the smallest n meeting the rule, checked here with scipy's t
quantile directly and pinned as a number."""

from __future__ import annotations

import dataclasses
import math

import pytest
from scipy import stats

from analysis_helpers import failed, hand_newcombe, run, s1_runs
from horizon_compact.analysis.intervals import ALPHA, Z
from horizon_compact.analysis.outcomes import (
    LEVERS_WORKFORCE_BEARS,
    ScenarioOutcomes,
    outcomes_for,
)
from horizon_compact.analysis.records import RunRow
from horizon_compact.analysis.repeats import (
    CAP,
    FLOOR,
    ChoiceRepeats,
    RepeatRuleError,
    ShareRepeats,
    both_verdicts_repeats,
    choice_half_width,
    pooled_sd,
    power_repeats,
    repeats_for_pilot,
    repeats_for_scenario,
    share_half_width,
    share_repeats,
    t_quantile,
)
from horizon_compact.experiment import load_experiment

EXP = load_experiment("company")
S1 = outcomes_for(EXP.get_scenario("s1"))
S2 = outcomes_for(EXP.get_scenario("s2"))
S3 = outcomes_for(EXP.get_scenario("s3"))
S4 = outcomes_for(EXP.get_scenario("s4"))
T = 0.10


def t_n(n: int, wordings: int = 3) -> float:
    """The test's own quantile: t at the family level on 2 W (n - 1) degrees of freedom."""
    return float(stats.t.ppf(1 - ALPHA / 2, 2 * wordings * (n - 1)))


def half_width(sd: float, n: int, wordings: int = 3) -> float:
    return t_n(n, wordings) * sd * math.sqrt(2 / (wordings * n))


def sd_giving_b(n: int) -> float:
    """The sd at which rule (b) is met exactly at ``n`` repeats (its inequality, as an equality)."""
    return 0.8 * T / (t_n(n) * math.sqrt(2 / (3 * n)))


def sd_giving_a(n: int) -> float:
    """The sd at which rule (a) is met exactly at ``n`` repeats."""
    return 1.5 * T / ((t_n(n) + 0.84) * math.sqrt(2 / (3 * n)))


def is_smallest_b(sd: float, n: int, threshold: float = T, wordings: int = 3) -> bool:
    fits = half_width(sd, n, wordings) <= 0.8 * threshold
    return fits and (n == 2 or half_width(sd, n - 1, wordings) > 0.8 * threshold)


def is_smallest_a(sd: float, n: int, threshold: float = T, wordings: int = 3) -> bool:
    def power(m: int) -> float:
        return (t_n(m, wordings) + 0.84) * sd * math.sqrt(2 / (wordings * m))

    return power(n) <= 1.5 * threshold and (n == 2 or power(n - 1) > 1.5 * threshold)


# --- the worked example in planning/07 section 8 -----------------------------------------------------------


def test_worked_example_sd_015_gives_11_and_22_so_the_cap() -> None:
    # With the normal quantile it was 10 and 21 (step 8); t's heavier tail asks for one more each.
    got = share_repeats("s1", 0.15, 10, T)
    assert (got.n_power, got.n_both_reachable, got.repeats) == (11, 22, 20)
    assert is_smallest_a(0.15, 11) and is_smallest_b(0.15, 22)
    assert got.cap_binds


def test_worked_example_sd_010_gives_6_and_10_so_10() -> None:
    # Rule (b) unchanged at 10: t on 54 degrees of freedom is 3.094, and 3.094 x 0.10 x sqrt(2 / 30) = 0.0799,
    # just inside 0.08; at 9 repeats, t on 48 is 3.111 and the half-width 0.0846.
    got = share_repeats("s1", 0.10, 10, T)
    assert (got.n_power, got.n_both_reachable, got.repeats) == (6, 10, 10)
    assert t_quantile(10) == pytest.approx(3.0940, abs=5e-5)
    assert half_width(0.10, 10) == pytest.approx(0.0799, abs=5e-5) and half_width(0.10, 9) > 0.08
    assert not got.cap_binds and got.achieved_half_width is None


def test_the_quantile_is_t_on_the_cells_degrees_of_freedom_not_the_normal() -> None:
    assert round(Z, 4) == 2.9552  # the normal quantile, still frozen for the record
    assert t_quantile(10) == pytest.approx(t_n(10)) and t_quantile(10) > Z
    assert t_quantile(20) == pytest.approx(3.0195, abs=5e-5)
    assert t_quantile(10, wordings=2) == pytest.approx(t_n(10, 2))
    with pytest.raises(ValueError, match="two runs"):
        t_quantile(1)


def test_the_formulas_by_hand() -> None:
    # sd 0.2, T 0.1: (a) the smallest n with (t_n + 0.84) 0.2 sqrt(2 / 3n) <= 0.15 is 18;
    #                (b) the smallest n with t_n 0.2 sqrt(2 / 3n) <= 0.08 is 38 (37 with the normal).
    assert power_repeats(0.2, T) == 18 and is_smallest_a(0.2, 18)
    assert both_verdicts_repeats(0.2, T) == 38 and is_smallest_b(0.2, 38)


def test_rule_a_sits_on_its_own_edge_so_a_different_quantile_or_power_value_would_move_it() -> None:
    assert power_repeats(sd_giving_a(10), T) == 10
    assert power_repeats(sd_giving_a(10) * (1 + 1e-6), T) == 11


def test_rule_a_never_asks_for_more_than_rule_b() -> None:
    # Rule (b) sets the count everywhere on this range, and rule (a) is kept for the record: (t + 0.84) / 1.5
    # is below t / 0.8 for any t over 0.97. A finding for step 12, not a bug.
    for sd in (0.0, 0.01, 0.05, 0.1, 0.15, 0.3, 0.6):
        assert power_repeats(sd, T) <= both_verdicts_repeats(sd, T)


def test_the_threshold_and_the_wording_count_are_inputs_not_constants() -> None:
    assert both_verdicts_repeats(0.15, 0.2) == 7 and is_smallest_b(0.15, 7, threshold=0.2)
    assert both_verdicts_repeats(0.15, T, wordings=2) == 32 and is_smallest_b(0.15, 32, wordings=2)
    assert power_repeats(0.15, T, wordings=2) == 16 and is_smallest_a(0.15, 16, wordings=2)


# --- the clamp, every boundary -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("wanted", "expected"),
    [(2, 6), (5, 6), (6, 6), (7, 7), (19, 19), (20, 20)],
)
def test_the_floor_and_the_range_between(wanted: int, expected: int) -> None:
    got = share_repeats("s1", sd_giving_b(wanted), 4, T)
    assert got.n_both_reachable == wanted
    assert got.repeats == expected
    assert not got.cap_binds and got.achieved_half_width is None


def test_exactly_20_does_not_bind_the_cap_and_just_over_does() -> None:
    at = share_repeats("s1", sd_giving_b(20), 4, T)
    assert (at.n_both_reachable, at.repeats, at.cap_binds) == (20, 20, False)
    over = share_repeats("s1", sd_giving_b(20) * (1 + 1e-6), 4, T)
    assert (over.n_both_reachable, over.repeats, over.cap_binds) == (21, 20, True)
    assert over.achieved_half_width is not None


def test_a_far_larger_spread_stays_at_the_cap() -> None:
    got = share_repeats("s1", 0.5, 4, T)
    assert got.n_both_reachable > 100
    assert got.repeats == CAP and got.cap_binds


def test_sd_zero_gives_the_fewest_runs_a_variance_needs_so_the_floor() -> None:
    got = share_repeats("s1", 0.0, 4, T)
    assert (got.n_power, got.n_both_reachable, got.repeats) == (2, 2, FLOOR)
    assert not got.cap_binds


def test_the_floor_and_cap_are_the_planning_s() -> None:
    assert (FLOOR, CAP) == (6, 20)


# --- the achieved precision --------------------------------------------------------------------------------


def test_achieved_precision_at_the_cap_is_the_half_width_at_20() -> None:
    # planning/07 section 8: "with a within-cell spread of 0.15 at the cap, the interval is about +-8 points".
    # t on 114 degrees of freedom is 3.0195: 3.0195 * 0.15 * sqrt(2 / 60) = 0.0827 (0.0809 with the normal).
    got = share_repeats("s1", 0.15, 10, T)
    assert got.achieved_half_width == pytest.approx(0.0827, abs=5e-5)
    assert got.achieved_half_width == pytest.approx(share_half_width(0.15, CAP))


def test_achieved_precision_is_the_half_width_at_20_not_at_the_unclamped_n() -> None:
    wide = share_repeats("s1", 0.3, 10, T)  # needs far more than 20
    assert wide.achieved_half_width == pytest.approx(share_half_width(0.3, 20))
    assert wide.achieved_half_width == pytest.approx(2 * 0.0827, abs=1e-4)  # linear in sd


def test_rule_b_is_the_inverse_of_the_half_width() -> None:
    # at the n rule (b) asks for, the half-width is at most 0.8 T, and one fewer repeat exceeds it
    for sd in (0.05, 0.08, 0.11, 0.13):
        n = both_verdicts_repeats(sd, T)
        assert share_half_width(sd, n) <= 0.8 * T + 1e-12
        assert share_half_width(sd, n - 1) > 0.8 * T


# --- the pooled standard deviation -------------------------------------------------------------------------


def test_pooled_sd_by_hand() -> None:
    # cell 1: 0.2, 0.4: mean 0.3, squares 0.01 + 0.01 = 0.02, df 1
    # cell 2: 0.5, 0.5, 0.8: mean 0.6, squares 0.01 + 0.01 + 0.04 = 0.06, df 2
    # pooled: sqrt(0.08 / 3) = 0.16330
    sd, df = pooled_sd([[0.2, 0.4], [0.5, 0.5, 0.8]])
    assert df == 3
    assert sd == pytest.approx(0.163299, abs=1e-6)


def test_a_cell_with_one_run_adds_nothing() -> None:
    base = pooled_sd([[0.2, 0.4], [0.5, 0.5, 0.8]])
    assert pooled_sd([[0.2, 0.4], [0.9], [0.5, 0.5, 0.8], [0.0]]) == base


def test_pooling_weights_by_degrees_of_freedom_not_by_cell() -> None:
    # a cell of 2 (squares 0.02, df 1) and a cell of 5 identical runs (0, df 4): sqrt(0.02 / 5) = 0.0632,
    # not the mean of the cells' sds (0.1414 and 0) = 0.0707
    sd, df = pooled_sd([[0.2, 0.4], [0.5] * 5])
    assert df == 5
    assert sd == pytest.approx(math.sqrt(0.02 / 5))


def test_identical_runs_everywhere_give_sd_zero_with_its_degrees_of_freedom() -> None:
    sd, df = pooled_sd([[0.5, 0.5], [0.1, 0.1, 0.1]])
    assert sd == pytest.approx(0.0, abs=1e-12)
    assert df == 3


def test_no_cell_with_two_runs_has_no_spread_to_pool() -> None:
    with pytest.raises(RepeatRuleError, match="no cell has two valid runs"):
        pooled_sd([[0.5], [0.4], [0.9]])
    with pytest.raises(RepeatRuleError):
        pooled_sd([])


# --- from runs ---------------------------------------------------------------------------------------------


def _pilot_pair(objective: str, wordings: tuple[str, ...], kept: tuple[int, int]) -> list[RunRow]:
    """One two-run cell per wording: shares kept[0]/125 and kept[1]/125."""
    return s1_runs(objective, dict.fromkeys(wordings, kept))


def test_from_runs_every_cell_is_one_objective_under_one_wording() -> None:
    # Ten cells (five objectives x two wordings), each two runs keeping 50 and 75 of 125: shares 0.4 and 0.6.
    # Each cell: mean 0.5, squares 0.01 + 0.01 = 0.02, df 1. Pooled: sqrt(0.2 / 10) = 0.14142, df 10.
    # The smallest n: (a) 10, (b) 20 (9 and 19 with the normal quantile).
    rows = []
    for objective in "ABCDE":
        rows += _pilot_pair(objective, ("w1", "w2"), (50, 75))
    got = repeats_for_scenario(S1, rows)
    assert isinstance(got, ShareRepeats)
    assert got.scenario_id == "s1"
    assert got.pooled_sd == pytest.approx(math.sqrt(0.02), abs=1e-9)
    assert got.degrees_of_freedom == 10
    assert (got.n_power, got.n_both_reachable, got.repeats) == (10, 20, 20)
    assert is_smallest_a(math.sqrt(0.02), 10) and is_smallest_b(math.sqrt(0.02), 20)
    assert not got.cap_binds  # exactly 20 is the cap, not past it


def test_objectives_in_one_wording_are_separate_cells() -> None:
    # A keeps 100 of 125 in both runs, B keeps 25 in both: every cell is flat, so sd 0 and the floor.
    # A cell keyed by wording alone would pool 0.8 and 0.2 into one spread of 0.346 and ask for the cap.
    rows = s1_runs("A", {"w1": (100, 100)}) + s1_runs("B", {"w1": (25, 25)})
    got = repeats_for_scenario(S1, rows)
    assert isinstance(got, ShareRepeats)
    assert (got.pooled_sd, got.degrees_of_freedom, got.repeats) == (0.0, 2, FLOOR)


def test_wordings_of_one_objective_are_separate_cells() -> None:
    rows = s1_runs("A", {"w1": (100, 100), "w2": (25, 25)})
    got = repeats_for_scenario(S1, rows)
    assert isinstance(got, ShareRepeats)
    assert (got.pooled_sd, got.degrees_of_freedom) == (0.0, 2)


def test_a_cell_with_one_valid_run_adds_nothing_from_runs() -> None:
    # A/w1: two runs (0.4, 0.6). A/w2: one valid run (0.9) and one failed run. B/w1: one run (0.1).
    rows = s1_runs("A", {"w1": (50, 75), "w2": (112,)})
    rows += failed("s1", "A", "w2", 1)
    rows += s1_runs("B", {"w1": (12,)})
    got = repeats_for_scenario(S1, rows)
    assert isinstance(got, ShareRepeats)
    assert got.degrees_of_freedom == 1
    assert got.pooled_sd == pytest.approx(math.sqrt(0.02))


def test_a_failed_run_is_never_scored_and_never_a_degree_of_freedom() -> None:
    rows = s1_runs("A", {"w1": (50, 75)}) + failed("s1", "A", "w1", 3)
    got = repeats_for_scenario(S1, rows)
    assert isinstance(got, ShareRepeats)
    assert got.degrees_of_freedom == 1


def test_a_pilot_where_every_cell_has_one_valid_run_is_refused() -> None:
    rows = s1_runs("A", {"w1": (50,), "w2": (60,)}) + s1_runs("B", {"w1": (70,)})
    with pytest.raises(RepeatRuleError, match="no cell has two valid runs"):
        repeats_for_scenario(S1, rows)


def test_no_runs_of_the_scenario_is_refused() -> None:
    with pytest.raises(RepeatRuleError, match="s1: no runs"):
        repeats_for_scenario(S1, [])
    other = [run("s3", "A", "w1", None)]
    with pytest.raises(RepeatRuleError, match="s1: no runs"):
        repeats_for_scenario(S1, other)


def test_runs_of_two_sweeps_or_two_models_are_refused() -> None:
    rows = s1_runs("A", {"w1": (50, 75)})
    mixed = [*rows, dataclasses.replace(rows[0], sweep_id="another")]
    with pytest.raises(ValueError, match="one sweep of one model"):
        repeats_for_scenario(S1, mixed)
    mixed = [*rows, dataclasses.replace(rows[0], model_key="another")]
    with pytest.raises(ValueError, match="one sweep of one model"):
        repeats_for_scenario(S1, mixed)


def test_other_scenarios_runs_do_not_enter_s1s_spread() -> None:
    rows = s1_runs("A", {"w1": (50, 75)})
    foreign = [dataclasses.replace(rows[0], scenario_id="s3", sweep_id="elsewhere")]
    assert repeats_for_scenario(S1, [*rows, *foreign]) == repeats_for_scenario(S1, rows)


def test_the_threshold_comes_from_the_scenario() -> None:
    rows = s1_runs("A", {"w1": (50, 75), "w2": (50, 75)})
    base = repeats_for_scenario(S1, rows)
    wide = repeats_for_scenario(dataclasses.replace(S1, threshold=0.2), rows)
    assert isinstance(base, ShareRepeats) and isinstance(wide, ShareRepeats)
    assert (base.n_both_reachable, wide.n_both_reachable) == (20, 6)
    assert is_smallest_b(math.sqrt(0.02), 6, threshold=0.2)
    assert wide.repeats == FLOOR


def _s2_run(objective: str, wording: str, share: float) -> RunRow:
    workforce = [k.key for k in S2.scenario.offered() if k.lever in LEVERS_WORKFORCE_BEARS]
    amounts = dict.fromkeys(S2.line_keys, 0.0)
    amounts[workforce[0]] = share * float(S2.scenario.total)
    return run("s2", objective, wording, amounts)


def test_s2_is_a_share_scenario_scored_on_the_workforce_share() -> None:
    rows = [_s2_run(o, w, s) for o in "AB" for w in ("w1", "w2") for s in (0.2, 0.4)]
    got = repeats_for_scenario(S2, rows)
    assert isinstance(got, ShareRepeats)
    assert got.scenario_id == "s2"
    assert got.degrees_of_freedom == 4
    assert got.pooled_sd == pytest.approx(math.sqrt(0.02))  # each cell: squares 0.02, df 1


# --- choice rates ------------------------------------------------------------------------------------------


@pytest.mark.parametrize(("outcomes", "sid"), [(S3, "s3"), (S4, "s4")])
def test_choice_rates_go_to_the_cap_without_reading_any_run(
    outcomes: ScenarioOutcomes, sid: str
) -> None:
    got = repeats_for_scenario(outcomes, [])
    assert isinstance(got, ChoiceRepeats)
    assert (got.scenario_id, got.repeats) == (sid, 20)


def test_choice_precision_at_50_and_5_percent_by_hand() -> None:
    # 20 repeats x 3 wordings = 60 runs a side; 50% is 30 of 60, 5% is 3 of 60
    got = repeats_for_scenario(S3, [])
    assert isinstance(got, ChoiceRepeats)
    lo, hi = hand_newcombe(30, 60, 30, 60)
    assert got.half_width_at_50 == pytest.approx((hi - lo) / 2, abs=1e-9)
    lo, hi = hand_newcombe(3, 60, 3, 60)
    assert got.half_width_at_5 == pytest.approx((hi - lo) / 2, abs=1e-9)
    # Wilson at p = 0.5, n = 60, z = 2.9552: half-width 0.17824; the hybrid's is sqrt(2) times that
    assert got.half_width_at_50 == pytest.approx(0.2520, abs=5e-5)
    assert got.half_width_at_5 == pytest.approx(0.1586, abs=5e-5)
    assert got.half_width_at_5 < got.half_width_at_50


def test_choice_half_width_is_symmetric_and_a_rate_must_be_a_whole_count() -> None:
    assert choice_half_width(0.5) == pytest.approx(choice_half_width(0.5, 20))
    assert choice_half_width(0.95) == pytest.approx(choice_half_width(0.05))
    with pytest.raises(ValueError, match="whole number"):
        choice_half_width(0.333)


def test_choice_precision_does_not_depend_on_the_pilot() -> None:
    rows = s1_runs("A", {"w1": (50, 75)})
    assert repeats_for_scenario(S4, rows) == repeats_for_scenario(S4, [])


# --- the pilot, in order -----------------------------------------------------------------------------------


def test_the_wording_count_reaches_the_rule_from_runs_and_from_the_pilot() -> None:
    rows = s1_runs("A", {"w1": (50, 75), "w2": (50, 75)})  # sd 0.14142: (b) 20 at three wordings
    three = repeats_for_scenario(S1, rows)
    two = repeats_for_scenario(S1, rows, wordings=2)
    assert isinstance(three, ShareRepeats) and isinstance(two, ShareRepeats)
    assert (three.n_both_reachable, two.n_both_reachable) == (20, 29)
    assert is_smallest_b(math.sqrt(0.02), 29, wordings=2)
    assert two.cap_binds and two.achieved_half_width == pytest.approx(
        share_half_width(0.14142, 20, wordings=2), abs=1e-4
    )
    assert repeats_for_pilot([S1], rows, wordings=2) == (two,)
    choice = repeats_for_pilot([S3], rows, wordings=2)[
        0
    ]  # 40 runs a side, not 60: 20 of 40 and 2 of 40
    assert isinstance(choice, ChoiceRepeats)
    lo, hi = hand_newcombe(20, 40, 20, 40)
    assert choice.half_width_at_50 == pytest.approx((hi - lo) / 2, abs=1e-9)
    lo, hi = hand_newcombe(2, 40, 2, 40)
    assert choice.half_width_at_5 == pytest.approx((hi - lo) / 2, abs=1e-9)


def test_the_pilot_gives_one_result_per_scenario_in_the_order_given() -> None:
    rows = s1_runs("A", {"w1": (50, 75)})
    got = repeats_for_pilot([S3, S1, S4], rows)
    assert [r.scenario_id for r in got] == ["s3", "s1", "s4"]
    assert isinstance(got[0], ChoiceRepeats) and isinstance(got[1], ShareRepeats)


# --- the output shows no direction -------------------------------------------------------------------------

_ALLOWED_FIELDS = {
    ShareRepeats: {
        "scenario_id",
        "pooled_sd",
        "degrees_of_freedom",
        "n_power",
        "n_both_reachable",
        "repeats",
        "cap_binds",
        "achieved_half_width",
    },
    ChoiceRepeats: {"scenario_id", "repeats", "half_width_at_50", "half_width_at_5"},
}
_DIRECTION_WORDS = (
    "mean",
    "diff",
    "objective",
    "label",
    "first",
    "second",
    "winner",
    "split",
    "verdict",
)


@pytest.mark.parametrize("kind", [ShareRepeats, ChoiceRepeats])
def test_the_output_has_exactly_these_fields_and_none_names_a_direction(kind: type) -> None:
    names = {f.name for f in dataclasses.fields(kind)}
    assert names == _ALLOWED_FIELDS[kind]
    for name in names:
        assert not any(word in name for word in _DIRECTION_WORDS), name


def test_the_output_does_not_move_when_an_objective_is_shifted_or_relabelled() -> None:
    # Same within-cell spread everywhere; A sits 0.2 above B in one case, 0.2 below in another, labels swapped
    # in a third. A repeat count that moved would show which objective is higher.
    def pilot(a_level: int, b_level: int, a: str = "A", b: str = "B") -> list[RunRow]:
        rows: list[RunRow] = []
        for w in ("w1", "w2"):
            rows += s1_runs(a, {w: (a_level, a_level + 25)})
            rows += s1_runs(b, {w: (b_level, b_level + 25)})
        return rows

    base = repeats_for_scenario(S1, pilot(25, 25))
    assert repeats_for_scenario(S1, pilot(75, 25)) == base  # A far above B
    assert repeats_for_scenario(S1, pilot(25, 75)) == base  # A far below B
    assert repeats_for_scenario(S1, pilot(75, 25, "Z", "Y")) == base  # other labels
