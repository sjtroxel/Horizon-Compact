"""The robustness rules (Phase 3 IMPLEMENTATION doc section 10; step 6).

Hand-built runs only. Expected intervals come from the test's own Newcombe (``hand_newcombe``); position
effects are worked out by hand in the comments. The boundaries tested: a per-wording difference of exactly
zero (and of floating-point noise around zero), a reversed wording, a reversal in a wording the failure rules
dropped, a split the bound already overturned, and a sealed wording that disagrees with the pooled result.
"""

from __future__ import annotations

import tomllib
from dataclasses import replace
from typing import Any

import pytest

from analysis_helpers import (
    W3,
    failed,
    hand_newcombe,
    run,
    s1_runs,
    s3_cell,
    s3_design,
    s3_runs,
    with_failures,
)
from horizon_compact.analysis.failures import (
    CALLABLE_STATUS,
    RefusalCallError,
    assess_comparison,
    assess_scenario,
)
from horizon_compact.analysis.intervals import ALPHA, DESCRIPTIVE_ALPHA, comparison_seed
from horizon_compact.analysis.outcomes import outcomes_for
from horizon_compact.analysis.records import RunRow
from horizon_compact.analysis.robustness import (
    SEALED_LABEL,
    RobustComparison,
    position_effects,
    relate,
    robustness_scenario,
    sealed_result,
    sealed_wording_of,
    wording_direction,
)
from horizon_compact.analysis.verdict import BOUNDARY_TOLERANCE
from horizon_compact.experiment import PLACEHOLDER_EXPERIMENT, load_experiment

EXP = load_experiment("company")
S1 = outcomes_for(EXP.get_scenario("s1"))
S3 = outcomes_for(EXP.get_scenario("s3"))
N = 3_000


def robust(rows: list[RunRow], first: str, second: str, outcomes: Any = S3) -> RobustComparison:
    assessed = assess_comparison(outcomes, rows, first, second, resamples=N)
    return RobustComparison(assessed, wording_direction(outcomes, rows, assessed))


# --- 10.1 wording direction ----------------------------------------------------------------------------


def test_a_split_whose_direction_holds_under_every_wording_is_robust() -> None:
    rows = s3_design("A", [9, 9, 9], [10, 10, 10]) + s3_design("C", [1, 1, 1], [10, 10, 10])
    got = robust(rows, "A", "C")
    assert got.final_verdict == "split" and got.wording is not None
    assert got.wording.label == "robust" and got.wording.reversed_wordings == ()
    assert [(d.wording_id, d.n_first, d.n_second) for d in got.wording.differences] == [
        ("w1", 10, 10),
        ("w2", 10, 10),
        ("w3", 10, 10),
    ]
    for d in got.wording.differences:
        assert d.first_value == pytest.approx(0.9) and d.second_value == pytest.approx(0.1)
        assert d.difference == pytest.approx(0.8) and d.direction == "same"
    assert got.wording.pooled_difference == pytest.approx(0.8)
    assert got.headline.startswith("split, robust: the direction holds under every wording")


def test_a_wording_that_reverses_the_pooled_split_makes_it_wording_sensitive() -> None:
    # Pooled: A 22 of 30, C 8 of 30, a difference of 0.467 (a split). Under w3 A closes 2 of 10 and C 8.
    rows = s3_design("A", [10, 10, 2], [10, 10, 10]) + s3_design("C", [0, 0, 8], [10, 10, 10])
    got = robust(rows, "A", "C")
    assert got.final_verdict == "split"  # the label does not change the verdict
    assert got.wording is not None and got.wording.label == "wording_sensitive"
    assert got.wording.pooled_difference == pytest.approx(22 / 30 - 8 / 30)
    by = {d.wording_id: d for d in got.wording.differences}
    assert by["w3"].difference == pytest.approx(-0.6) and by["w3"].direction == "opposite"
    assert by["w1"].direction == by["w2"].direction == "same"
    assert got.wording.reversed_wordings == ("w3",)
    assert got.headline.startswith("split, wording-sensitive: w3 reverses (-0.600)")
    assert got.downgrade_reason is None


def test_a_wording_difference_of_exactly_zero_is_not_robust() -> None:
    rows = s3_design("A", [10, 10, 5], [10, 10, 10]) + s3_design("C", [0, 0, 5], [10, 10, 10])
    got = robust(rows, "A", "C")
    assert got.final_verdict == "split" and got.wording is not None
    by = {d.wording_id: d for d in got.wording.differences}
    assert by["w3"].difference == 0.0 and by["w3"].direction == "zero"
    assert got.wording.label == "wording_sensitive" and got.wording.reversed_wordings == ("w3",)
    assert "w3 zero (+0.000)" in got.headline


def test_floating_point_noise_around_zero_still_counts_as_zero() -> None:
    """A keeps 7 and 13 people on alternate runs, C keeps 10: both wording means are 0.08, and in
    floating point they differ by -1.4e-17. That is zero, not a reversal and not agreement."""
    w3_a, w3_c = [7, 13] * 5, [10] * 10
    rows = s1_runs("A", {"w1": [125] * 10, "w2": [125] * 10, "w3": w3_a})
    rows += s1_runs("C", {"w1": [0] * 10, "w2": [0] * 10, "w3": w3_c})
    got = robust(rows, "A", "C", S1)
    assert got.final_verdict == "split" and got.wording is not None
    d3 = got.wording.differences[2]
    assert d3.difference != 0.0 and abs(d3.difference) < 1e-15  # the noise is really there
    assert d3.direction == "zero" and got.wording.label == "wording_sensitive"


def test_share_wording_values_are_the_means_of_the_valid_runs() -> None:
    rows = s1_runs("A", {w: [100, 110] for w in W3}) + s1_runs("C", {w: [20, 30] for w in W3})
    got = robust(rows, "A", "C", S1)
    for d in got.wording.differences:  # type: ignore[union-attr]
        assert d.first_value == pytest.approx(105 / 125) and d.second_value == pytest.approx(
            25 / 125
        )
        assert d.difference == pytest.approx(80 / 125) and (d.n_first, d.n_second) == (2, 2)
    assert got.wording.label == "robust"  # type: ignore[union-attr]


def test_no_split_and_inconclusive_carry_the_differences_without_a_label() -> None:
    quiet = robust(
        s3_design("C", [2, 2, 2], [20, 20, 20]) + s3_design("D", [2, 2, 2], [20, 20, 20]), "C", "D"
    )
    assert quiet.final_verdict == "no_split" and quiet.wording is not None
    assert quiet.wording.label is None
    assert [d.direction for d in quiet.wording.differences] == ["zero"] * 3
    assert quiet.headline.startswith("no split, over wordings w1, w2 and w3")

    # A pooled difference of exactly zero from opposite wordings: no sign to agree with.
    rows = s3_design("A", [4, 0, 2], [20, 20, 20]) + s3_design("B", [0, 4, 2], [20, 20, 20])
    mixed = robust(rows, "A", "B")
    assert mixed.final_verdict != "split" and mixed.wording is not None
    assert mixed.wording.label is None and mixed.wording.pooled_difference == pytest.approx(0.0)
    assert [d.direction for d in mixed.wording.differences] == ["undefined", "undefined", "zero"]
    assert [round(d.difference, 3) for d in mixed.wording.differences] == [0.2, -0.2, 0.0]


def test_a_split_the_bound_overturned_has_differences_but_no_label() -> None:
    rows = with_failures("A", 36, 18, 2) + with_failures("C", 18, 18, 2)
    got = robust(rows, "A", "C")
    assert got.assessed.among_valid is not None and got.assessed.among_valid.verdict == "split"
    assert got.final_verdict == "inconclusive" and got.downgrade_reason is not None
    assert got.wording is not None and got.wording.label is None
    assert all(d.direction == "same" for d in got.wording.differences)
    assert got.headline.startswith("inconclusive")


def test_a_reversal_in_a_dropped_wording_is_never_read() -> None:
    # w3 is reversed (A closes 0 of 26, C 27 of 30) but A's w3 cell failed 4 of 30 and was dropped.
    a = s3_design("A", [27, 27, 0], [30, 30, 26], [0, 0, 4])
    c = s3_design("C", [3, 3, 27], [30, 30, 30])
    got = robust(a + c, "A", "C")
    assert [d.wording_id for d in got.assessed.dropped] == ["w3"]
    assert got.final_verdict == "split" and got.wording is not None
    assert [d.wording_id for d in got.wording.differences] == ["w1", "w2"]
    assert got.wording.label == "robust"
    assert "w3 dropped from both sides" in got.headline


def test_a_split_over_one_kept_wording_is_labeled_robust_and_says_so_in_its_scope() -> None:
    a = s3_design("A", [27, 0, 0], [30, 20, 20], [0, 8, 8])
    c = s3_design("C", [3, 0, 0], [30, 20, 20], [0, 8, 8])
    got = robust(a + c, "A", "C")
    assert got.assessed.kept_wordings == ("w1",) and got.final_verdict == "split"
    assert (
        got.wording is not None
        and got.wording.label == "robust"
        and len(got.wording.differences) == 1
    )
    assert "over wording w1" in got.headline


def test_a_comparison_that_is_not_assessable_has_no_wording_direction() -> None:
    rows = s3_design("A", [1, 1, 1], [8, 8, 8], [2, 2, 2]) + s3_design("C", [1, 1, 1], [10, 10, 10])
    got = robust(rows, "A", "C")
    assert got.final_verdict == "not_assessable" and got.wording is None
    assert got.headline.startswith("not assessable")


# --- 10.2 the sealed wording ---------------------------------------------------------------------------


def test_the_sealed_wording_is_read_from_the_experiment_not_typed() -> None:
    on_disk = tomllib.loads((EXP.root / EXP.name / "objectives.toml").read_text())[
        "sealed_template"
    ]
    assert sealed_wording_of(EXP) == on_disk == EXP.sealed_template and on_disk in EXP.templates
    with pytest.raises(ValueError, match="no sealed template"):
        sealed_wording_of(load_experiment(PLACEHOLDER_EXPERIMENT))


def pooled_for(rows: list[RunRow], first: str = "A", second: str = "C", outcomes: Any = S3) -> Any:
    return assess_comparison(outcomes, rows, first, second, resamples=N)


def test_the_sealed_result_uses_only_the_sealed_wordings_runs_and_agrees_when_it_holds() -> None:
    sealed = sealed_wording_of(EXP)
    rows = s3_design("A", [9, 9, 9], [10, 10, 10]) + s3_design("C", [1, 1, 1], [10, 10, 10])
    got = sealed_result(S3, rows, pooled_for(rows), sealed, resamples=N)
    assert got.label == SEALED_LABEL and "outside the family" in got.label
    assert got.sealed_wording == sealed
    assert got.assessed.among_valid is not None
    assert got.assessed.among_valid.wordings == (sealed,)
    assert got.assessed.among_valid.valid_runs == ((sealed, 10, 10),)
    lo, hi = hand_newcombe(9, 10, 1, 10)
    assert got.assessed.among_valid.interval.low == pytest.approx(lo)
    assert got.assessed.among_valid.interval.high == pytest.approx(hi)
    assert (got.pooled_verdict, got.assessed.final_verdict) == ("split", "split")
    assert got.relation == "same_verdict"


def test_the_wording_is_whatever_is_passed_and_the_pairs_role_carries_into_the_rerun() -> None:
    """Nothing in the rerun may assume which template is sealed: the id is an argument."""
    rows = s3_design("A", [9, 9, 9], [10, 10, 10]) + s3_design("D", [1, 1, 1], [10, 10, 10])
    pooled = assess_comparison(S3, rows, "A", "D", role="secondary", resamples=N)
    for wording in W3:
        got = sealed_result(S3, rows, pooled, wording, resamples=N)
        assert got.sealed_wording == wording and got.assessed.kept_wordings == (wording,)
    assert (
        got.assessed.role == "secondary"
        and got.assessed.label == "secondary: the expected comparison"
    )


def test_a_sealed_wording_that_does_not_hold_is_reported_beside_the_pooled_split() -> None:
    sealed = sealed_wording_of(EXP)
    closes_a = [9 if w != sealed else 5 for w in W3]
    closes_c = [1 if w != sealed else 5 for w in W3]
    rows = s3_design("A", closes_a, [10, 10, 10]) + s3_design("C", closes_c, [10, 10, 10])
    got = sealed_result(S3, rows, pooled_for(rows), sealed, resamples=N)
    assert got.pooled_verdict == "split" and got.assessed.final_verdict == "inconclusive"
    assert got.relation == "different" and "zero" in got.relation_reason
    assert got.assessed.among_valid is not None and got.assessed.among_valid.difference == 0.0


def test_the_sealed_rerun_has_its_own_seed_name() -> None:
    sealed = sealed_wording_of(EXP)
    rows = s1_runs("A", {w: [10, 50, 90] for w in W3}) + s1_runs(
        "C", {w: [20, 60, 100] for w in W3}
    )
    got = sealed_result(S1, rows, pooled_for(rows, outcomes=S1), sealed, resamples=500)
    assert got.assessed.among_valid is not None
    assert got.assessed.among_valid.interval.seed == comparison_seed(
        "pilot-test-sweep", "s1:A-C:sealed"
    )
    pooled = pooled_for(rows, outcomes=S1)
    assert pooled.among_valid.interval.seed == comparison_seed("pilot-test-sweep", "s1:A-C")


def test_the_sealed_rerun_applies_the_failure_rules_to_its_own_wording_only() -> None:
    sealed = sealed_wording_of(EXP)
    others = [w for w in W3 if w != sealed]
    a = s3_design("A", [18, 18, 18], [18, 18, 18], [2, 2, 2])  # every cell has 2 failed
    c = s3_design("C", [0, 0, 0], [20, 20, 20])
    got = sealed_result(S3, a + c, pooled_for(a + c), sealed, resamples=N)
    assert got.assessed.failed_first == 2  # the sealed cell's two, not the six across wordings
    (check,) = got.assessed.bound
    assert (check.set_first, check.set_second) == (2, 0)
    assert got.assessed.kept_wordings == (sealed,) and others  # the other wordings were never read


def test_a_sealed_cell_over_the_failure_limit_is_not_assessable_even_if_the_pooled_is_fine() -> (
    None
):
    sealed = sealed_wording_of(EXP)
    fail = [4 if w == sealed else 0 for w in W3]
    rows = s3_design("A", [9, 9, 9], [10, 10, 10], fail) + s3_design("C", [1, 1, 1], [10, 10, 10])
    pooled = pooled_for(rows)
    assert pooled.final_verdict == "split" and [d.wording_id for d in pooled.dropped] == [sealed]
    got = sealed_result(S3, rows, pooled, sealed, resamples=N)
    assert got.assessed.final_verdict == "not_assessable" and got.relation == "not_comparable"


def test_the_sealed_rerun_needs_runs_under_the_sealed_wording_on_both_sides() -> None:
    sealed = sealed_wording_of(EXP)
    others = [w for w in W3 if w != sealed]
    rows = s3_cell("A", others[0], 9, 10) + s3_cell("C", others[0], 1, 10)
    with pytest.raises(ValueError, match="no run under the sealed wording"):
        sealed_result(S3, rows, pooled_for(rows), sealed, resamples=N)
    rows += s3_cell("A", sealed, 9, 10)  # only A has the sealed wording
    with pytest.raises(ValueError, match=f"C has no run at all under {sealed}"):
        sealed_result(S3, rows, pooled_for(rows), sealed, resamples=N)


def test_a_logged_call_on_another_wording_is_fine_and_an_unknown_one_is_not() -> None:
    sealed = sealed_wording_of(EXP)
    others = [w for w in W3 if w != sealed]
    rows = s3_design("A", [9, 9, 9], [10, 10, 10]) + s3_design("C", [1, 1, 1], [10, 10, 10])
    extra = failed("s3", "A", others[0], 1, status=CALLABLE_STATUS)
    rows += extra
    calls = {extra[0].run_id: "declined in words"}
    got = sealed_result(S3, rows, pooled_for(rows, "A", "C"), sealed, calls=calls, resamples=N)
    assert got.assessed.failed_first == 0  # that run is under another wording
    with pytest.raises(RefusalCallError, match="not among the runs"):
        sealed_result(
            S3, rows, pooled_for(rows), sealed, calls={"r-ffffffffffff": "typo"}, resamples=N
        )


# --- 10.3 position effects -----------------------------------------------------------------------------

S1_LINES = ("eliminate", "move_plant_pay", "move_keep_pay")


def s1_run(objective: str, order: tuple[str, ...], eliminated: int, **kw: Any) -> RunRow:
    """An S1 run keeping the rest as moved-at-plant-pay, with the menu in ``order``."""
    amounts = {"eliminate": eliminated, "move_plant_pay": 125 - eliminated, "move_keep_pay": 0}
    return run("s1", objective, "w1", amounts, menu_order=order, **kw)


def test_lever_shares_by_position_and_the_slope_are_worked_out_by_hand() -> None:
    # eliminate: 75, 50, 25 of 125 (0.6, 0.4, 0.2) at menu positions 1, 2, 3.
    # move_plant_pay: 50, 75, 100 (0.4, 0.6, 0.8) at positions 2, 1, 1.
    # move_keep_pay: always 0, at positions 3, 3, 2.
    rows = [
        s1_run("A", ("eliminate", "move_plant_pay", "move_keep_pay"), 75),
        s1_run("A", ("move_plant_pay", "eliminate", "move_keep_pay"), 50),
        s1_run("A", ("move_plant_pay", "move_keep_pay", "eliminate"), 25),
    ]
    got = position_effects(S1, rows)
    assert (got.scenario_id, got.runs, got.menu_size, got.options) == ("s1", 3, 3, ())
    by = {lever.key: lever for lever in got.levers}
    elim = by["eliminate"]
    assert [(b.position, b.runs) for b in elim.by_position] == [(1, 1), (2, 1), (3, 1)]
    assert [b.mean_share for b in elim.by_position] == pytest.approx([0.6, 0.4, 0.2])
    assert elim.slope == pytest.approx(-0.2) and elim.runs == 3
    plant = by["move_plant_pay"]
    assert [(b.position, b.runs) for b in plant.by_position] == [(1, 2), (2, 1)]
    assert [b.mean_share for b in plant.by_position] == pytest.approx([0.7, 0.4])
    assert plant.slope == pytest.approx(-0.3)  # sxy = -0.2, sxx = 2/3
    keep = by["move_keep_pay"]
    assert (
        keep.slope == pytest.approx(0.0) and keep.slope is not None
    )  # varying position, flat share


def test_a_line_that_never_moves_has_no_slope() -> None:
    order = ("eliminate", "move_plant_pay", "move_keep_pay")
    rows = [s1_run("A", order, 75), s1_run("C", order, 50), s1_run("D", order, 25)]
    got = position_effects(S1, rows)
    assert all(lever.slope is None for lever in got.levers)
    assert [b.runs for b in got.levers[0].by_position] == [3]
    assert position_effects(S1, rows[:1]).levers[0].slope is None  # one run


def test_failed_runs_are_not_read_and_pooling_crosses_objectives_and_wordings() -> None:
    order = ("eliminate", "move_plant_pay", "move_keep_pay")
    rows = [s1_run("A", order, 75), s1_run("D", order, 25, wording_id="w3")]
    rows += failed("s1", "A", "w1", 2)  # menu_order is empty on these; they are not read
    got = position_effects(S1, rows)
    assert got.runs == 2 and got.levers[0].by_position[0].mean_share == pytest.approx(0.4)


def s3_choice_run(order: tuple[str, str, str], chose: str) -> RunRow:
    amounts = {
        "eliminated": 0,
        "moved_other_plants": 29,
        "kept_at_plant": 161,
        "transferred_to_buyer": 0,
    }
    menu = ("eliminated", "moved_other_plants", "kept_at_plant", "transferred_to_buyer")
    return run("s3", "A", "w1", amounts, choice=chose, menu_order=menu, option_order=order)


def test_option_choice_rates_when_listed_first_against_not_first_with_newcombe_intervals() -> None:
    rows = [s3_choice_run(("close", "retool", "sell"), c) for c in ["close"] * 5 + ["retool"]]
    rows += [
        s3_choice_run(("retool", "close", "sell"), c) for c in ["close", "retool", "retool", "sell"]
    ]
    got = position_effects(S3, rows)
    assert got.alpha == DESCRIPTIVE_ALPHA == 0.05 and got.runs == 10
    by = {o.option: o for o in got.options}
    assert list(by) == ["close", "retool", "sell"]  # the scenario file's order
    close = by["close"]  # first in 6 runs (chosen 5); not first in 4 (chosen 1)
    assert (close.chosen_first, close.runs_first, close.chosen_not_first, close.runs_not_first) == (
        5,
        6,
        1,
        4,
    )
    assert close.interval is not None
    lo, hi = hand_newcombe(5, 6, 1, 4, alpha=0.05)
    assert close.interval.estimate == pytest.approx(5 / 6 - 1 / 4)
    assert close.interval.low == pytest.approx(lo) and close.interval.high == pytest.approx(hi)
    assert close.interval.alpha == 0.05
    family_lo, _ = hand_newcombe(5, 6, 1, 4, alpha=ALPHA)
    assert close.interval.low != pytest.approx(family_lo)  # the descriptive level, not the family's
    retool = by["retool"]  # first in 4 runs (chosen 2); not first in 6 (chosen 1)
    assert (
        retool.chosen_first,
        retool.runs_first,
        retool.chosen_not_first,
        retool.runs_not_first,
    ) == (2, 4, 1, 6)
    assert retool.interval is not None
    lo, hi = hand_newcombe(2, 4, 1, 6, alpha=0.05)
    assert retool.interval.low == pytest.approx(lo) and retool.interval.high == pytest.approx(hi)
    sell = by["sell"]  # never listed first: nothing to compare, and no interval invented
    assert (sell.runs_first, sell.runs_not_first, sell.chosen_not_first) == (0, 10, 1)
    assert sell.interval is None


def test_the_descriptive_level_can_be_overridden_but_defaults_to_95_percent() -> None:
    rows = [s3_choice_run(("close", "retool", "sell"), c) for c in ["close", "close", "retool"]]
    rows += [s3_choice_run(("retool", "close", "sell"), c) for c in ["retool", "close", "retool"]]
    default, family = position_effects(S3, rows), position_effects(S3, rows, alpha=ALPHA)
    assert default.options[0].interval is not None and family.options[0].interval is not None
    assert family.options[0].interval.width > default.options[0].interval.width
    assert family.alpha == ALPHA


def test_position_effects_refuse_runs_that_did_not_record_where_things_were() -> None:
    row = run("s1", "A", "w1", {"eliminate": 1, "move_plant_pay": 124, "move_keep_pay": 0})
    with pytest.raises(ValueError, match="menu_order lacks"):
        position_effects(S1, [row])
    ok = s3_choice_run(("close", "retool", "sell"), "close")
    with pytest.raises(ValueError, match="option_order lacks"):
        position_effects(S3, [ok, replace(ok, option_order=("close", "retool"))])
    with pytest.raises(ValueError, match="no runs on s1"):
        position_effects(S1, [ok])
    with pytest.raises(ValueError, match="no valid run"):
        position_effects(S3, [failed("s3", "A", "w1", 1)[0]])
    other = replace(ok, sweep_id="another")
    with pytest.raises(ValueError, match="sweep_ids"):
        position_effects(S3, [ok, other])


# --- the whole scenario --------------------------------------------------------------------------------


def test_robustness_scenario_covers_every_comparison_and_the_sealed_wording() -> None:
    rows: list[RunRow] = []
    for objective, closes in (("A", 50), ("B", 30), ("C", 40), ("D", 20)):
        rows += s3_runs(objective, closes, 60)
    menu = ("eliminated", "moved_other_plants", "kept_at_plant", "transferred_to_buyer")
    options = ("close", "retool", "sell")
    rows = [replace(r, menu_order=menu, option_order=options) for r in rows]
    assessment = assess_scenario(S3, rows, resamples=500)
    got = robustness_scenario(S3, rows, assessment, sealed_wording_of(EXP), resamples=500)
    assert got.scenario_id == "s3"
    pairs = [(c.assessed.first, c.assessed.second) for c in got.comparisons]
    assert pairs == [("A", "C"), ("A", "B"), ("C", "D"), ("B", "D"), ("A", "D")]
    assert [(s.assessed.first, s.assessed.second) for s in got.sealed] == pairs
    assert all(s.sealed_wording == EXP.sealed_template for s in got.sealed)
    assert all(
        s.assessed.among_valid is not None
        and s.assessed.among_valid.wordings == (EXP.sealed_template,)
        for s in got.sealed
    )
    assert all(c.wording is not None for c in got.comparisons)
    assert got.position.runs == 240 and got.position.alpha == DESCRIPTIVE_ALPHA
    # The family alpha must not reach the descriptive intervals through the scenario call either.
    assert all(
        o.interval is None or o.interval.alpha == DESCRIPTIVE_ALPHA for o in got.position.options
    )


# --- the sealed relation: every boundary of the definition in the module docstring -----------------------

T = 0.20  # a choice-rate threshold; the relation only needs a threshold, not a scenario
EPS = BOUNDARY_TOLERANCE


@pytest.mark.parametrize(
    ("pooled", "d_p", "sealed", "d_s", "relation"),
    [
        # same verdict
        ("split", 0.5, "split", 0.4, "same_verdict"),
        ("split", -0.5, "split", -0.25, "same_verdict"),
        ("no_split", 0.01, "no_split", -0.02, "no_split_is_same"),
        ("inconclusive", 0.1, "inconclusive", -0.3, "same_verdict"),
        # two splits in opposite directions are different, though the verdict name matches
        ("split", 0.5, "split", -0.4, "different"),
        ("split", -0.5, "split", 0.4, "different"),
        # a pooled split, sealed inconclusive: the direction decides
        ("split", 0.5, "inconclusive", 0.3, "same_direction_less_certain"),
        ("split", -0.5, "inconclusive", -0.3, "same_direction_less_certain"),
        ("split", 0.5, "inconclusive", 2 * EPS, "same_direction_less_certain"),  # just past zero
        ("split", 0.5, "inconclusive", EPS, "different"),  # exactly at the tolerance is zero
        ("split", 0.5, "inconclusive", 0.0, "different"),  # exactly zero
        ("split", 0.5, "inconclusive", -2 * EPS, "different"),
        ("split", 0.5, "inconclusive", -0.3, "different"),
        ("split", -0.5, "inconclusive", 0.3, "different"),
        # a pooled no split, sealed inconclusive: the point estimate against the threshold
        ("no_split", 0.0, "inconclusive", 0.0, "same_direction_less_certain"),
        ("no_split", 0.0, "inconclusive", T - 1e-6, "same_direction_less_certain"),
        ("no_split", 0.0, "inconclusive", -(T - 1e-6), "same_direction_less_certain"),
        ("no_split", 0.0, "inconclusive", T - EPS / 2, "different"),  # within tolerance of T: at it
        ("no_split", 0.0, "inconclusive", T, "different"),
        ("no_split", 0.0, "inconclusive", -T, "different"),
        ("no_split", 0.0, "inconclusive", 0.3, "different"),
        # everything else is different
        ("split", 0.5, "no_split", 0.0, "different"),
        ("no_split", 0.0, "split", 0.5, "different"),
        ("inconclusive", 0.1, "split", 0.5, "different"),
        ("inconclusive", 0.1, "no_split", 0.0, "different"),
        # not comparable: nothing to compare is not a disagreement
        ("split", 0.5, "not_assessable", None, "not_comparable"),
        ("not_assessable", None, "split", 0.5, "not_comparable"),
        ("not_assessable", None, "not_assessable", None, "not_comparable"),
    ],
)
def test_the_sealed_relation_on_every_boundary(
    pooled: str, d_p: float | None, sealed: str, d_s: float | None, relation: str
) -> None:
    got, reason = relate(pooled, d_p, sealed, d_s, T)  # type: ignore[arg-type]
    assert got == ("same_verdict" if relation == "no_split_is_same" else relation)
    assert reason  # every relation says why


def test_a_missing_difference_on_an_assessable_result_is_a_bug_not_a_relation() -> None:
    with pytest.raises(ValueError, match="has a difference"):
        relate("split", None, "split", 0.4, T)


def test_a_sealed_result_inconclusive_but_in_the_pooled_direction_is_less_certain_not_different() -> (
    None
):
    sealed = sealed_wording_of(EXP)
    # Pooled: A 24 of 30, C 5 of 30 (a split). Under the sealed wording alone A closes 6 of 10 and C 3 of 10:
    # a difference of 0.3 whose interval, on 10 runs a side, includes zero.
    closes_a = [9 if w != sealed else 6 for w in W3]
    closes_c = [1 if w != sealed else 3 for w in W3]
    rows = s3_design("A", closes_a, [10, 10, 10]) + s3_design("C", closes_c, [10, 10, 10])
    pooled = pooled_for(rows)
    got = sealed_result(S3, rows, pooled, sealed, resamples=N)
    assert pooled.final_verdict == "split" and got.assessed.final_verdict == "inconclusive"
    assert (
        got.assessed.among_valid is not None
        and got.assessed.among_valid.difference == pytest.approx(0.3)
    )
    assert got.relation == "same_direction_less_certain"
    assert "too wide" in got.relation_reason


def test_a_sealed_result_pointing_the_other_way_is_different_even_when_it_is_only_inconclusive() -> (
    None
):
    sealed = sealed_wording_of(EXP)
    closes_a = [9 if w != sealed else 3 for w in W3]
    closes_c = [1 if w != sealed else 6 for w in W3]
    rows = s3_design("A", closes_a, [10, 10, 10]) + s3_design("C", closes_c, [10, 10, 10])
    pooled = pooled_for(rows)
    got = sealed_result(S3, rows, pooled, sealed, resamples=N)
    assert pooled.final_verdict == "split" and got.assessed.final_verdict == "inconclusive"
    assert (
        got.assessed.among_valid is not None
        and got.assessed.among_valid.difference == pytest.approx(-0.3)
    )
    assert got.relation == "different" and "other way" in got.relation_reason


def test_a_pooled_no_split_beside_a_sealed_point_estimate_at_the_threshold_is_different() -> None:
    """Pooled: C 49 of 230, D 43 of 230, no split. Sealed: C 9 of 30, D 3 of 30, exactly 0.20 on 30 runs
    a side, which is inconclusive. The threshold is the choice-rate one (0.20): at it, the point
    estimate is not inside."""
    sealed = sealed_wording_of(EXP)
    sizes = [30 if w == sealed else 100 for w in W3]
    closes_c = [9 if w == sealed else 20 for w in W3]
    closes_d = [3 if w == sealed else 20 for w in W3]
    rows = s3_design("C", closes_c, sizes) + s3_design("D", closes_d, sizes)
    pooled = pooled_for(rows, "C", "D")
    got = sealed_result(S3, rows, pooled, sealed, resamples=N)
    assert pooled.final_verdict == "no_split" and got.assessed.final_verdict == "inconclusive"
    assert got.relation == "different" and "threshold" in got.relation_reason
