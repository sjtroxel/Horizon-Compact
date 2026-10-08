"""The failure rules (Phase 3 IMPLEMENTATION doc section 9; step 5).

Hand-built runs only, with answers worked out by hand or by the test's own Newcombe (``hand_newcombe``), never
by the engine. The boundaries tested: a cell at exactly 10% and just over; a failure that does or does not
overturn a split, including a narrowed difference of exactly the threshold; a no split overturned only by the
widening of one sign; failed runs in a dropped wording.
"""

from __future__ import annotations

import json

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
    REFUSAL_CALLS_FILE,
    RefusalCallError,
    ScenarioAssessment,
    assess_comparison,
    assess_scenario,
    cell_rates,
    check_refusal_calls,
    classify_run,
    decline_candidates,
    exceeds_limit,
    first_attempt_rows,
    objective_rates,
    pair_rates,
    parse_refusal_calls,
    read_refusal_calls,
)
from horizon_compact.analysis.intervals import DESCRIPTIVE_ALPHA
from horizon_compact.analysis.outcomes import outcomes_for
from horizon_compact.analysis.records import RecordRefusal, RunRow
from horizon_compact.analysis.verdict import compare, compare_scenario
from horizon_compact.experiment import load_experiment

EXP = load_experiment("company")
S1 = outcomes_for(EXP.get_scenario("s1"))
S3 = outcomes_for(EXP.get_scenario("s3"))
N = 3_000  # bootstrap resamples: enough for the share tests, whose answers are fixed by the data


# --- 9.1 counting ---------------------------------------------------------------------------------


def test_every_final_status_is_valid_refusal_or_a_failure_by_type() -> None:
    assert classify_run(run("s3", "A", "w1", {"x": 1.0}, status="valid")) == "valid"
    assert (
        classify_run(run("s3", "A", "w1", {"x": 1.0}, status="valid_rescaled")) == "valid_rescaled"
    )
    assert classify_run(run("s3", "A", "w1", None, status="refusal")) == "refusal"
    for status in ("no_tool_call", "multiple_calls", "schema_invalid", "sum_mismatch", "truncated"):
        assert classify_run(run("s3", "A", "w1", None, status=status)) == "failure", status
    assert classify_run(run("s3", "A", "w1", None, status="malformed_tool_use")) == "failure"
    with pytest.raises(ValueError, match="never a final status"):
        classify_run(run("s3", "A", "w1", None, status="api_error"))


def test_a_no_tool_call_is_a_refusal_only_by_a_logged_call() -> None:
    row = run("s3", "A", "w1", None, status=CALLABLE_STATUS, possible_decline=True)
    assert classify_run(row) == "failure"
    assert classify_run(row, {}) == "failure"
    assert classify_run(row, {row.run_id: "it wrote that it would not decide"}) == "refusal"
    other = run("s3", "A", "w1", None, status=CALLABLE_STATUS)
    assert classify_run(other, {row.run_id: "x"}) == "failure"  # a call covers its own run only


def test_the_flag_only_lists_candidates_and_a_logged_call_removes_one() -> None:
    flagged = run("s3", "A", "w1", None, status=CALLABLE_STATUS, possible_decline=True)
    unflagged = run("s3", "A", "w1", None, status=CALLABLE_STATUS)
    wrong_status = run("s3", "A", "w1", None, status="schema_invalid", possible_decline=True)
    rows = [flagged, unflagged, wrong_status]
    assert decline_candidates(rows) == (flagged.run_id,)
    assert decline_candidates(rows, {flagged.run_id: "called"}) == ()
    # Listing a candidate decides nothing: counts are unchanged until a call is logged.
    assert cell_rates(rows)[0].refused == 0


def test_the_calls_file_parses_and_refuses_what_it_cannot_trust() -> None:
    good = {"r-0123456789ab": "the model said it would not make this decision"}
    assert parse_refusal_calls(json.dumps(good)) == good
    assert parse_refusal_calls("{}") == {}
    for bad in (
        "not json",
        "[]",
        json.dumps({"abc": "reason"}),  # not a run id
        json.dumps({"r-0123456789ab": ""}),  # a call needs its reason
        json.dumps({"r-0123456789ab": "  "}),
        json.dumps({"r-0123456789ab": 3}),
        json.dumps({"r-0123456789AB": "uppercase is not a run id"}),
    ):
        with pytest.raises(RefusalCallError):
            parse_refusal_calls(bad)


def test_a_call_must_name_a_no_tool_call_run_in_the_data() -> None:
    row = run("s3", "A", "w1", None, status=CALLABLE_STATUS)
    check_refusal_calls([row], {row.run_id: "ok"})
    with pytest.raises(RefusalCallError, match="not among the runs"):
        check_refusal_calls([row], {"r-ffffffffffff": "typo"})
    for status in ("schema_invalid", "refusal", "valid"):
        bad = run("s3", "A", "w1", {"x": 1.0} if status == "valid" else None, status=status)
        with pytest.raises(RefusalCallError, match=f"final status is {status}"):
            check_refusal_calls([bad], {bad.run_id: "wrong"})
    # Every entry point checks, so a call that names nothing never goes unnoticed.
    with pytest.raises(RefusalCallError):
        cell_rates([row], {"r-ffffffffffff": "typo"})


class _Source:
    def __init__(self, objects: dict[str, str]) -> None:
        self.objects = objects

    def get(self, key: str) -> str | None:
        return self.objects.get(key)

    def list_keys(self, prefix: str) -> list[str]:
        return [k for k in self.objects if k.startswith(prefix)]


def test_the_calls_are_read_from_beside_the_sweep() -> None:
    body = json.dumps({"r-0123456789ab": "declined in words"})
    assert read_refusal_calls(
        _Source({"pilot/x/sw/" + REFUSAL_CALLS_FILE: body}), "pilot/x/sw"
    ) == {"r-0123456789ab": "declined in words"}
    assert read_refusal_calls(_Source({}), "pilot/x/sw/") == {}  # none logged
    with pytest.raises(
        RecordRefusal
    ):  # the reader's refusal of development records on real content holds
        read_refusal_calls(_Source({}), "development/company/sw/")


# --- 9.2 cells and the 10% rule -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("failures", "attempted", "over"),
    [
        (3, 30, False),  # exactly 10%: not excluded
        (4, 30, True),
        (2, 20, False),
        (3, 20, True),
        (1, 10, False),
        (2, 10, True),
        (10, 100, False),
        (11, 100, True),
        (0, 1, False),
        (1, 1, True),
        (0, 30, False),
    ],
)
def test_the_limit_is_strictly_greater_than_ten_percent(
    failures: int, attempted: int, over: bool
) -> None:
    assert exceeds_limit(failures, attempted) is over


def test_a_cell_counts_valid_rescaled_refused_and_failed_by_type() -> None:
    rows = s3_runs("A", 0, 5, ("w1",))
    rows[0] = run("s3", "A", "w1", rows[0].amounts, status="valid_rescaled", choice="retool")
    rows += failed("s3", "A", "w1", 2, status="sum_mismatch")
    rows += failed("s3", "A", "w1", 1, status="schema_invalid")
    rows += failed("s3", "A", "w1", 1, status="refusal")
    nt = failed("s3", "A", "w1", 1, status=CALLABLE_STATUS)
    rows += nt
    (plain,) = cell_rates(rows)
    assert (plain.attempted, plain.valid, plain.rescaled, plain.refused) == (10, 5, 1, 1)
    assert plain.failed_by_type == (
        (CALLABLE_STATUS, 1),
        ("schema_invalid", 1),
        ("sum_mismatch", 2),
    )
    assert (plain.failed, plain.unsuccessful) == (4, 5)
    # The human call moves one no_tool_call from failures to refusals; the cell's total does not change.
    (called,) = cell_rates(rows, {nt[0].run_id: "declined"})
    assert (called.failed, called.refused, called.unsuccessful) == (3, 2, 5)
    assert called.unreliable and plain.unreliable
    assert called.failure_rate == pytest.approx(5 / 10)


def test_refusals_count_toward_the_limit() -> None:
    rows = s3_runs("A", 0, 18, ("w1",)) + failed("s3", "A", "w1", 1)
    rows += failed("s3", "A", "w1", 1, status="refusal")
    assert not cell_rates(rows)[0].unreliable  # 1 failure + 1 refusal of 20: exactly 10%
    rows += failed("s3", "A", "w1", 1, status="refusal")
    assert cell_rates(rows)[0].unreliable  # 3 of 21


def test_cells_are_kept_apart_by_model_scenario_objective_and_wording() -> None:
    rows = s3_runs("A", 1, 4, ("w1",)) + s3_runs("C", 1, 4, ("w1",)) + s3_runs("A", 1, 4, ("w2",))
    rows += s1_runs("A", {"w1": [3, 4]})
    rows += [run("s3", "A", "w1", rows[0].amounts, choice="close", model_key="nova-pro")]
    keys = [(c.model_key, c.scenario_id, c.objective_id, c.wording_id) for c in cell_rates(rows)]
    assert keys == sorted(set(keys)) and len(keys) == 5


# --- decision 6: an excluded cell drops its wording from both sides -------------------------------


def test_a_cell_at_exactly_ten_percent_is_kept_and_one_over_is_dropped_from_both_sides() -> None:
    def build(a_w1_failures: int) -> list[RunRow]:
        a = s3_design("A", [10, 10, 10], [30 - a_w1_failures, 30, 30], [a_w1_failures, 0, 0])
        c = s3_design("C", [3, 3, 3], [30, 30, 30])
        return a + c

    kept = assess_comparison(S3, build(3), "A", "C")
    assert kept.dropped == () and kept.kept_wordings == W3
    assert kept.scope == "over wordings w1, w2 and w3"

    over = assess_comparison(S3, build(4), "A", "C")
    assert [d.wording_id for d in over.dropped] == ["w1"]
    assert over.kept_wordings == ("w2", "w3")
    assert over.among_valid is not None and over.among_valid.wordings == ("w2", "w3")
    # w1 is gone from BOTH sides: C's w1 runs (all valid) do not count, so the counts are w2 and w3 only.
    assert over.among_valid.valid_runs == (("w2", 30, 30), ("w3", 30, 30))
    lo, hi = hand_newcombe(20, 60, 6, 60)
    assert over.among_valid.interval.low == pytest.approx(lo)
    assert over.among_valid.interval.high == pytest.approx(hi)
    assert "w1 dropped from both sides" in over.scope and "A's w1 cell failed 4 of 30" in over.scope
    assert over.scope.startswith("over wordings w2 and w3")


def test_the_other_side_can_drop_a_wording_and_other_comparisons_are_untouched() -> None:
    rows = (
        s3_design("A", [6, 6, 6], [20, 20, 20])
        + s3_design("B", [6, 6, 6], [20, 20, 20])
        + s3_design("C", [10, 2, 2], [20, 14, 20], [0, 6, 0])  # C's w2: 6 of 20 failed
    )
    ac = assess_comparison(S3, rows, "A", "C")
    assert [d.wording_id for d in ac.dropped] == ["w2"]
    assert [c.objective_id for c in ac.dropped[0].cells] == ["C"]
    assert ac.among_valid is not None
    assert ac.among_valid.valid_runs == (("w1", 20, 20), ("w3", 20, 20))
    ab = assess_comparison(S3, rows, "A", "B")  # C's cell is not in this comparison
    assert ab.dropped == () and ab.kept_wordings == W3


def test_a_comparison_left_with_no_wording_is_not_assessable() -> None:
    rows = s3_design("A", [1, 1, 1], [8, 8, 8], [2, 2, 2]) + s3_design("C", [1, 1, 1], [10, 10, 10])
    got = assess_comparison(S3, rows, "A", "C")
    assert got.final_verdict == "not_assessable" and got.among_valid is None
    assert got.kept_wordings == () and len(got.dropped) == 3
    assert got.bound == () and got.worst_case_verdict is None
    assert got.scope.startswith("not assessable")


def test_the_unreliable_cell_may_be_on_either_side_or_both() -> None:
    rows = s3_design("A", [5, 5, 5], [10, 20, 20], [10, 0, 0]) + s3_design(
        "C", [1, 1, 1], [20, 10, 20], [0, 10, 0]
    )
    got = assess_comparison(S3, rows, "A", "C")
    assert [d.wording_id for d in got.dropped] == ["w1", "w2"]
    assert got.kept_wordings == ("w3",)


def test_a_wording_with_no_run_at_all_on_one_side_is_refused_not_dropped() -> None:
    rows = (
        s3_design("A", [1, 1, 1], [10, 10, 10])
        + s3_cell("C", "w1", 1, 10)
        + s3_cell("C", "w2", 1, 10)
    )
    with pytest.raises(ValueError, match="C has no run at all under w3"):
        assess_comparison(S3, rows, "A", "C")


def test_runs_from_two_sweeps_are_refused_even_before_the_rates() -> None:
    rows = s3_design("A", [1, 1, 1], [10, 10, 10]) + s3_design("C", [1, 1, 1], [10, 10, 10])
    rows.append(run("s3", "C", "w1", rows[-1].amounts, choice="close", sweep_id="another"))
    with pytest.raises(ValueError, match="sweep_ids"):
        assess_comparison(S3, rows, "A", "C")


# --- 9.4 the worst-case bound, split --------------------------------------------------------------
# Every design: three wordings, 20 attempted per cell (18 valid + 2 failed = exactly 10%, kept).


def test_a_split_the_bound_does_not_overturn_is_kept_and_the_bound_is_recorded() -> None:
    rows = with_failures("A", 51, 18, 2) + with_failures("C", 3, 18, 2)
    got = assess_comparison(S3, rows, "A", "C")
    assert got.among_valid is not None and got.among_valid.verdict == "split"
    assert (got.failed_first, got.failed_second) == (6, 6)
    (check,) = got.bound
    assert (check.label, check.first_value, check.second_value) == ("narrowing", 0.0, 1.0)
    lo, hi = hand_newcombe(51, 60, 9, 60)  # A's 6 failed set to 0, C's 6 set to 1
    assert check.comparison.interval.low == pytest.approx(lo)
    assert check.comparison.interval.high == pytest.approx(hi)
    assert check.comparison.difference == pytest.approx(0.7)
    assert not check.overturned
    assert got.worst_case_verdict == "split" and got.final_verdict == "split"
    assert got.downgrade_reason is None


def test_a_split_the_bound_overturns_becomes_inconclusive_with_the_reason() -> None:
    rows = with_failures("A", 36, 18, 2) + with_failures("C", 18, 18, 2)
    got = assess_comparison(S3, rows, "A", "C")
    assert got.among_valid is not None and got.among_valid.verdict == "split"
    lo, _ = hand_newcombe(36, 54, 18, 54)
    assert got.among_valid.interval.low == pytest.approx(lo) and lo > 0
    (check,) = got.bound
    nlo, nhi = hand_newcombe(
        36, 60, 24, 60
    )  # A: 36 of 60 (failed to 0); C: 18 + 6 of 60 (failed to 1)
    assert check.comparison.interval.low == pytest.approx(nlo) and nlo < 0
    assert check.comparison.interval.high == pytest.approx(nhi)
    assert check.overturned and check.comparison.verdict == "inconclusive"
    assert got.worst_case_verdict == "inconclusive" and got.final_verdict == "inconclusive"
    assert got.downgrade_reason is not None
    assert (
        "split among valid runs, overturned by the worst-case bound (narrowing)"
        in got.downgrade_reason
    )
    assert "6 failed or refused runs of A set to 0" in got.downgrade_reason
    assert "6 of C set to 1" in got.downgrade_reason


def test_the_direction_is_the_one_that_narrows_so_a_negative_split_flips_it() -> None:
    rows = with_failures("A", 3, 18, 2) + with_failures("C", 51, 18, 2)  # A - C is about -0.89
    got = assess_comparison(S3, rows, "A", "C")
    assert got.among_valid is not None and got.among_valid.difference < 0
    (check,) = got.bound
    assert (check.first_value, check.second_value) == (1.0, 0.0)  # A's failures to 1, C's to 0
    assert check.comparison.difference == pytest.approx(9 / 60 - 51 / 60)
    assert got.final_verdict == "split"


def test_a_bound_difference_of_exactly_the_threshold_still_counts_as_a_split() -> None:
    # A: 12 of 54 valid close and 6 failed; C: 0 of 60. Bound: A 12/60 - C 0/60 = 0.20 exactly,
    # with the interval still above 0.
    rows = s3_design("A", [4, 4, 4], [18, 18, 18], [2, 2, 2]) + s3_design(
        "C", [0, 0, 0], [20, 20, 20]
    )
    got = assess_comparison(S3, rows, "A", "C")
    (check,) = got.bound
    assert check.comparison.difference == pytest.approx(0.2)
    lo, _ = hand_newcombe(12, 60, 0, 60)
    assert check.comparison.interval.low == pytest.approx(lo) and lo > 0
    assert not check.overturned and got.final_verdict == "split"


def test_one_run_short_of_the_threshold_under_the_bound_is_overturned() -> None:
    # 11 of 54 close: valid difference 11/54 = 0.2037 (a split); bound 11/60 = 0.1833 is below the threshold.
    rows = s3_design("A", [4, 4, 3], [18, 18, 18], [2, 2, 2]) + s3_design(
        "C", [0, 0, 0], [20, 20, 20]
    )
    got = assess_comparison(S3, rows, "A", "C")
    assert got.among_valid is not None and got.among_valid.verdict == "split"
    (check,) = got.bound
    assert check.comparison.difference == pytest.approx(11 / 60)
    assert check.overturned and got.final_verdict == "inconclusive"


def test_failures_only_on_the_second_side_narrow_that_side_alone() -> None:
    rows = s3_design("A", [18, 18, 18], [18, 18, 18]) + s3_design(
        "C", [0, 0, 0], [18, 18, 18], [2, 2, 2]
    )
    got = assess_comparison(S3, rows, "A", "C")
    assert (got.failed_first, got.failed_second) == (0, 6)
    (check,) = got.bound
    assert (check.set_first, check.set_second) == (0, 6)
    assert check.comparison.difference == pytest.approx(54 / 54 - 6 / 60)
    assert got.final_verdict == "split"


# --- 9.4 the worst-case bound, no split (decision 3) ----------------------------------------------


def test_a_no_split_is_checked_in_both_signs_and_the_raising_one_can_overturn_it() -> None:
    rows = with_failures("C", 0, 18, 2) + with_failures("D", 0, 18, 2)
    got = assess_comparison(S3, rows, "C", "D")
    assert got.among_valid is not None and got.among_valid.verdict == "no_split"
    raised, lowered = got.bound
    assert (raised.label, lowered.label) == (
        "widening: difference raised",
        "widening: difference lowered",
    )
    rlo, rhi = hand_newcombe(6, 60, 0, 60)  # C's failures to 1, D's to 0
    assert raised.comparison.interval.low == pytest.approx(rlo)
    assert raised.comparison.interval.high == pytest.approx(rhi) and rhi > 0.20
    llo, _ = hand_newcombe(0, 60, 6, 60)
    assert lowered.comparison.interval.low == pytest.approx(llo) and llo < -0.20
    assert raised.overturned and lowered.overturned
    assert got.final_verdict == "inconclusive" and got.worst_case_verdict == "inconclusive"
    assert got.downgrade_reason is not None and "no_split among valid runs" in got.downgrade_reason


def test_a_no_split_overturned_only_by_the_negative_sign_widening_is_downgraded() -> None:
    """C and D never close. Only D has failures. Setting D's failures to 0 changes nothing that matters;
    setting them to 1 pulls the difference to -0.10 and the interval past -0.20."""
    rows = with_failures("C", 0, 20, 0) + with_failures("D", 0, 18, 2)
    got = assess_comparison(S3, rows, "C", "D")
    assert got.among_valid is not None and got.among_valid.verdict == "no_split"
    raised, lowered = got.bound
    assert not raised.overturned and raised.comparison.verdict == "no_split"
    assert lowered.overturned
    llo, _ = hand_newcombe(0, 60, 6, 60)
    assert lowered.comparison.interval.low == pytest.approx(llo) and llo < -0.20
    assert got.final_verdict == "inconclusive"
    assert got.downgrade_reason is not None and "difference lowered" in got.downgrade_reason


def test_a_no_split_overturned_only_by_the_positive_sign_widening_is_downgraded() -> None:
    rows = with_failures("C", 0, 18, 2) + with_failures("D", 0, 20, 0)
    got = assess_comparison(S3, rows, "C", "D")
    raised, lowered = got.bound
    assert raised.overturned and not lowered.overturned
    assert got.final_verdict == "inconclusive"
    assert got.downgrade_reason is not None and "difference raised" in got.downgrade_reason


def test_a_no_split_the_bound_cannot_overturn_is_kept() -> None:
    def fail_two(objective: str) -> list[RunRow]:
        return s3_design(objective, [0, 0, 0], [19, 19, 20], [1, 1, 0])  # 2 failed in 60

    got = assess_comparison(S3, fail_two("C") + fail_two("D"), "C", "D")
    raised, lowered = got.bound
    assert not raised.overturned and not lowered.overturned
    _, rhi = hand_newcombe(2, 60, 0, 60)
    assert raised.comparison.interval.high == pytest.approx(rhi) and rhi < 0.20
    assert got.final_verdict == "no_split" and got.worst_case_verdict == "no_split"
    assert got.downgrade_reason is None


def test_an_inconclusive_verdict_is_not_bounded_and_stays_inconclusive() -> None:
    rows = with_failures("A", 27, 18, 2) + with_failures("B", 27, 18, 2)
    got = assess_comparison(S3, rows, "A", "B")
    assert got.among_valid is not None and got.among_valid.verdict == "inconclusive"
    assert got.bound == () and got.worst_case_verdict is None
    assert got.final_verdict == "inconclusive" and got.downgrade_reason is None
    assert (got.failed_first, got.failed_second) == (6, 6)


def test_a_comparison_with_no_failed_run_is_untouched() -> None:
    rows = s3_design("A", [10, 10, 10], [20, 20, 20]) + s3_design("C", [2, 2, 2], [20, 20, 20])
    got = assess_comparison(S3, rows, "A", "C")
    assert got.bound == () and got.worst_case_verdict is None
    assert got.among_valid == compare(S3, rows, "A", "C")
    assert got.final_verdict == got.among_valid.verdict == "split"


def test_a_refusal_enters_the_bound_like_a_failure() -> None:
    rows = with_failures("A", 36, 18, 0) + with_failures("C", 18, 18, 0)
    rows += failed("s3", "A", "w1", 2, status="refusal") + failed(
        "s3", "A", "w2", 2, status="refusal"
    )
    rows += failed("s3", "A", "w3", 2, status="refusal")
    rows += failed("s3", "C", "w1", 2) + failed("s3", "C", "w2", 2) + failed("s3", "C", "w3", 2)
    got = assess_comparison(S3, rows, "A", "C")
    assert (got.failed_first, got.failed_second) == (6, 6) and got.final_verdict == "inconclusive"


def test_failed_runs_in_a_dropped_wording_do_not_enter_the_bound() -> None:
    # w3: A's cell is 5 failed of 25, dropped. Of the kept wordings only w1 has a failure (1 of 20 for A).
    a = s3_design("A", [9, 9, 9], [19, 20, 20], [1, 0, 5])
    c = s3_design("C", [1, 1, 1], [20, 20, 20])
    got = assess_comparison(S3, a + c, "A", "C")
    assert [d.wording_id for d in got.dropped] == ["w3"]
    assert (got.failed_first, got.failed_second) == (1, 0)
    (check,) = got.bound
    assert check.comparison.wordings == ("w1", "w2")
    assert check.comparison.valid_runs == (
        ("w1", 20, 20),
        ("w2", 20, 20),
    )  # 19 valid + 1 set by the bound
    assert check.comparison.difference == pytest.approx(18 / 40 - 2 / 40)
    # And with every failure in the dropped wording, there is nothing to bound at all.
    a = s3_design("A", [9, 9, 9], [20, 20, 20], [0, 0, 5])
    only_dropped = assess_comparison(S3, a + c, "A", "C")
    assert only_dropped.bound == () and only_dropped.worst_case_verdict is None
    assert only_dropped.final_verdict == "split"


def test_the_bound_seeds_are_named_apart_from_the_verdict_and_from_each_other() -> None:
    s1_rows = s1_runs("C", {w: [125] * 18 for w in W3}) + s1_runs("D", {w: [125] * 18 for w in W3})
    s1_rows += [r for w in W3 for r in failed("s1", "C", w, 2)] + [
        r for w in W3 for r in failed("s1", "D", w, 2)
    ]
    got = assess_comparison(S1, s1_rows, "C", "D", resamples=500)
    assert got.among_valid is not None
    seeds = {got.among_valid.interval.seed} | {c.comparison.interval.seed for c in got.bound}
    assert len(seeds) == 3 and None not in seeds


# --- the bound on shares (S1, bootstrap) ----------------------------------------------------------


def share_cells(objective: str, kept_valid: int, kept_failed: int, people: int) -> list[RunRow]:
    rows = s1_runs(objective, {w: [people] * kept_valid for w in W3})
    return rows + [r for w in W3 for r in failed("s1", objective, w, kept_failed)]


def test_a_share_split_that_the_bound_pulls_below_the_threshold_is_overturned() -> None:
    """A keeps all 125 on every valid run, C keeps 100: a zero-width split of exactly 0.20. With 2 failures
    in each cell of 20, the bound sets A's to 0 (wording mean 0.9) and C's to 1 (0.8 x 0.9 + 0.1 = 0.82):
    0.08, under the 0.10 threshold, so it cannot be a split."""
    rows = share_cells("A", 18, 2, 125) + share_cells("C", 18, 2, 100)
    got = assess_comparison(S1, rows, "A", "C", resamples=N)
    assert got.among_valid is not None
    assert got.among_valid.difference == pytest.approx(0.2) and got.among_valid.degenerate_interval
    assert got.among_valid.verdict == "split"
    (check,) = got.bound
    assert check.comparison.difference == pytest.approx(0.9 - 0.82)
    assert check.overturned and got.final_verdict == "inconclusive"


def test_a_share_split_far_above_the_threshold_survives_the_bound() -> None:
    rows = share_cells("A", 18, 2, 125) + share_cells("C", 18, 2, 0)
    got = assess_comparison(S1, rows, "A", "C", resamples=N)
    (check,) = got.bound
    assert check.comparison.difference == pytest.approx(0.9 - 0.1)  # A's failures to 0; C's to 1
    assert got.final_verdict == "split" and got.worst_case_verdict == "split"


def test_the_all_agree_no_split_with_failures_is_downgraded_by_the_widening() -> None:
    """Every valid run of C and D keeps all 125: the bootstrap's [0, 0] and a no split (decision 10's case).
    With failures present the raising bound puts C at 1.0 and D at 0.9: a difference of 0.10, which no
    interval around it can call a no split."""
    rows = share_cells("C", 18, 2, 125) + share_cells("D", 18, 2, 125)
    got = assess_comparison(S1, rows, "C", "D", resamples=N)
    assert got.among_valid is not None
    assert got.among_valid.degenerate_interval and got.among_valid.verdict == "no_split"
    raised, lowered = got.bound
    assert raised.comparison.difference == pytest.approx(0.1)
    # C's failures to 0 (wording mean 0.9), D's to 1 (wording mean 1.0)
    assert lowered.comparison.difference == pytest.approx(0.9 - 1.0)
    assert raised.overturned and lowered.overturned
    assert got.final_verdict == "inconclusive"


def test_a_no_split_the_bound_turns_into_a_split_is_still_downgraded() -> None:
    """C keeps all 125 on every valid run, D keeps 119: a 0.048 difference, no split. The raising bound sets
    D's failures to 0 (wording mean 0.9 x 0.952), a difference of 0.143 with an interval above 0.048: a split.
    Anything but the verdict that was claimed overturns it, and the final verdict is inconclusive."""
    rows = share_cells("C", 18, 2, 125) + share_cells("D", 18, 2, 119)
    got = assess_comparison(S1, rows, "C", "D", resamples=N)
    assert got.among_valid is not None and got.among_valid.verdict == "no_split"
    raised, _ = got.bound
    assert raised.comparison.difference == pytest.approx(1.0 - 0.9 * 119 / 125)
    assert raised.comparison.verdict == "split" and raised.overturned
    assert got.worst_case_verdict == "split" and got.final_verdict == "inconclusive"
    assert got.downgrade_reason is not None and "the verdict becomes split" in got.downgrade_reason


# --- 9.3 first attempt beside final ---------------------------------------------------------------


def with_first_attempt_failures(
    rows: list[RunRow], objective: str, wording: str, n: int
) -> list[RunRow]:
    """Make the first ``n`` runs of one cell valid only on a retry: the first attempt failed."""
    out, changed = [], 0
    for row in rows:
        if row.objective_id == objective and row.wording_id == wording and changed < n:
            row = run(
                row.scenario_id,
                objective,
                wording,
                row.amounts,
                choice=row.choice,
                first_attempt_status="schema_invalid",
                first_amounts=None,
                first_choice=None,
                attempts=2,
            )
            changed += 1
        out.append(row)
    return out


def test_first_attempt_rows_take_the_first_attempts_result() -> None:
    rows = with_first_attempt_failures(s3_design("A", [4, 4, 4], [20, 20, 20]), "A", "w1", 5)
    view = first_attempt_rows(rows)
    assert [r.status for r in view].count("schema_invalid") == 5 and all(
        r.amounts is None and r.choice is None for r in view if r.status == "schema_invalid"
    )
    originals = {r.run_id: r for r in rows}
    for row in view:
        if row.valid:
            # The view scores exactly as the outcomes' own first-attempt scoring does.
            assert S3.score(row) == S3.score_first_attempt(originals[row.run_id])


def test_a_first_attempt_that_chose_differently_is_scored_on_its_own_choice() -> None:
    closing = {
        "eliminated": 161,
        "moved_other_plants": 29,
        "kept_at_plant": 0,
        "transferred_to_buyer": 0,
    }
    retool = {
        "eliminated": 0,
        "moved_other_plants": 29,
        "kept_at_plant": 161,
        "transferred_to_buyer": 0,
    }
    row = run("s3", "A", "w1", retool, choice="retool", first_amounts=closing, first_choice="close")
    (view,) = first_attempt_rows([row])
    assert S3.score(row).primary == 0.0 and S3.score(view).primary == 1.0
    assert S3.score(view) == S3.score_first_attempt(row)


def test_first_attempt_verdicts_sit_beside_final_ones_with_their_own_exclusions() -> None:
    a = with_first_attempt_failures(s3_design("A", [10, 10, 10], [20, 20, 20]), "A", "w1", 5)
    c = s3_design("C", [2, 2, 2], [20, 20, 20])
    got = assess_scenario_for(a + c)
    final = got.comparisons[0]
    first = got.first_attempt[0]
    assert (
        final.dropped == () and final.final_verdict == "split"
    )  # retries made every final run valid
    assert [d.wording_id for d in first.dropped] == ["w1"]  # 5 of 20 first attempts failed
    assert first.among_valid is not None
    assert first.among_valid.valid_runs == (("w2", 20, 20), ("w3", 20, 20))
    lo, hi = hand_newcombe(20, 40, 4, 40)
    assert first.among_valid.interval.low == pytest.approx(lo)
    assert first.among_valid.interval.high == pytest.approx(hi)


def assess_scenario_for(rows: list[RunRow]) -> ScenarioAssessment:
    objectives = {r.objective_id for r in rows}
    needed = {"A", "B", "C", "D"} - objectives
    extra: list[RunRow] = []
    for objective in sorted(needed):  # pad the missing objectives so all five pairs exist
        extra += s3_design(objective, [5, 5, 5], [20, 20, 20])
    return assess_scenario(S3, rows + extra, resamples=500)


def test_a_human_call_is_not_applied_to_the_first_attempt_view() -> None:
    row = run("s3", "A", "w1", None, status=CALLABLE_STATUS, first_attempt_status=CALLABLE_STATUS)
    (final_cell,) = cell_rates([row], {row.run_id: "declined"})
    (first_cell,) = cell_rates(first_attempt_rows([row]))
    assert final_cell.refused == 1 and first_cell.refused == 0 and first_cell.failed == 1


# --- 9.5 whether failures differ by objective -----------------------------------------------------


def test_objective_rates_pool_the_wordings_and_split_failures_from_refusals() -> None:
    rows = s3_design("A", [1, 1, 1], [8, 9, 10], [2, 1, 0])
    rows += failed("s3", "A", "w1", 1, status="refusal")
    rows += s3_design("C", [1, 1, 1], [10, 10, 10])
    rows += failed("s3", "C", "w2", 3, status="refusal")
    got = {r.objective_id: r for r in objective_rates(rows, "s3")}
    assert (got["A"].attempted, got["A"].failed, got["A"].refused) == (31, 3, 1)
    assert (got["C"].attempted, got["C"].failed, got["C"].refused) == (33, 0, 3)
    assert got["A"].unsuccessful == 4


def test_pair_rates_are_newcombe_intervals_in_the_comparison_order() -> None:
    rows: list[RunRow] = []
    for objective, nfail, nref in (("A", 6, 0), ("B", 3, 3), ("C", 0, 6), ("D", 0, 0), ("E", 9, 9)):
        rows += s3_runs(objective, 0, 60 - nfail - nref)
        rows += failed("s3", objective, "w1", nfail) + failed(
            "s3", objective, "w2", nref, status="refusal"
        )
    pairs = pair_rates(objective_rates(rows, "s3"))
    assert [(p.first, p.second, p.role) for p in pairs] == [
        ("A", "C", "primary"),
        ("A", "B", "primary"),
        ("C", "D", "primary"),
        ("B", "D", "primary"),
        ("A", "D", "secondary"),
    ]  # E is in the rates, in no pair
    ac = pairs[0]
    assert ac.failed.estimate == pytest.approx(6 / 60 - 0 / 60)
    lo, hi = hand_newcombe(6, 60, 0, 60, alpha=0.05)  # descriptive: 95%, not the family's 99.7%
    assert ac.failed.low == pytest.approx(lo) and ac.failed.high == pytest.approx(hi)
    assert ac.failed.alpha == DESCRIPTIVE_ALPHA == 0.05
    lo, hi = hand_newcombe(0, 60, 6, 60, alpha=0.05)
    assert ac.refused.low == pytest.approx(lo) and ac.refused.high == pytest.approx(hi)
    assert ac.unsuccessful.estimate == pytest.approx(0.0)
    assert ac.failed.width > 0 and pairs[2].failed.width > 0  # all-zero rates still have real width


# --- the whole scenario ---------------------------------------------------------------------------


def test_assess_scenario_orders_the_comparisons_and_matches_the_plain_engine_when_nothing_failed() -> (
    None
):
    rows: list[RunRow] = []
    for objective, closes in (("A", 50), ("B", 30), ("C", 40), ("D", 20), ("E", 33)):
        rows += s3_runs(objective, closes, 60)
    got = assess_scenario(S3, rows)
    assert [(c.first, c.second, c.role) for c in got.comparisons] == [
        ("A", "C", "primary"),
        ("A", "B", "primary"),
        ("C", "D", "primary"),
        ("B", "D", "primary"),
        ("A", "D", "secondary"),
    ]
    plain = compare_scenario(S3, rows)
    assert [c.among_valid for c in got.comparisons] == list(plain)
    assert all(c.bound == () for c in got.comparisons)
    assert all(
        c.among_valid is not None and c.final_verdict == c.among_valid.verdict
        for c in got.comparisons
    )
    assert got.comparisons[-1].label == "secondary: the expected comparison"
    assert len(got.cells) == 15 and not any(c.unreliable for c in got.cells)
    # No failures anywhere: the first-attempt view says the same thing.
    assert [c.final_verdict for c in got.first_attempt] == [
        c.final_verdict for c in got.comparisons
    ]
    assert len(got.objective_rates) == 5 and len(got.pair_rates) == 5
    # The family alpha drives the verdicts; it must not leak into the descriptive table.
    assert all(p.failed.alpha == DESCRIPTIVE_ALPHA for p in got.pair_rates)


def test_a_call_naming_a_run_on_another_scenario_is_checked_against_all_the_runs() -> None:
    s3 = s3_design("A", [1, 1, 1], [10, 10, 10]) + s3_design("C", [1, 1, 1], [10, 10, 10])
    other = failed("s1", "A", "w1", 1, status=CALLABLE_STATUS)
    calls = {other[0].run_id: "declined"}
    got = assess_comparison(
        S3, s3 + other, "A", "C", calls=calls
    )  # valid call, other scenario: fine
    assert got.final_verdict in ("split", "no_split", "inconclusive")
    with pytest.raises(RefusalCallError, match="not among the runs"):
        assess_comparison(S3, s3, "A", "C", calls=calls)
