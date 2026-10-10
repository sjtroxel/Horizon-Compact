"""The versioned results object (Phase 3 IMPLEMENTATION doc sections 4 and 8.3, decision 1; step 7).

Hand-built runs, answers worked out by hand or by the test's own Newcombe. The field names of each result
type are pinned: if one of those tests fails, the object's shape changed, and ``RESULTS_VERSION`` goes up.
"""

from __future__ import annotations

import dataclasses
import json
import math
from pathlib import Path
from typing import Any

import pytest
from scipy import stats

from analysis_helpers import (
    W3,
    failed,
    hand_newcombe,
    run,
    s1_runs,
    s3_design,
    with_failures,
)
from horizon_compact.analysis import RESULTS_VERSION
from horizon_compact.analysis.failures import CALLABLE_STATUS, RefusalCallError
from horizon_compact.analysis.records import RunRow, RunSet
from horizon_compact.analysis.results import (
    BoundResult,
    ComparisonResult,
    FirstAttemptSummary,
    ModelResults,
    ScenarioResult,
    SealedSummary,
    build_results,
    results_path,
    to_record,
    write_results,
)
from horizon_compact.experiment import PLACEHOLDER_EXPERIMENT, load_experiment

EXP = load_experiment("company")


def s3_four(
    a: tuple[list[int], list[int]],
    c: tuple[list[int], list[int]] | None = None,
    **extra: Any,
) -> list[RunRow]:
    """S3 for A, B, C, D (E left out): A and C as given (closes, valid per wording), B and D mirror C."""
    c = c or a
    rows = s3_design("A", *a, **extra) + s3_design("C", *c)
    rows += s3_design("B", *c) + s3_design("D", *c)
    return rows


def with_orders(rows: list[RunRow]) -> list[RunRow]:
    """The runner records where every line and option sat; hand-built rows get the scenario file's order."""
    out = []
    for row in rows:
        scenario = EXP.scenarios.get(row.scenario_id)
        if scenario is None or row.menu_order:
            out.append(row)
            continue
        options = tuple(o.key for o in scenario.choice.options) if scenario.choice else ()
        out.append(
            dataclasses.replace(
                row, menu_order=tuple(lever.key for lever in scenario.levers), option_order=options
            )
        )
    return out


def results_of(rows: list[RunRow], **kw: Any) -> ModelResults:
    return build_results(EXP, RunSet(tuple(with_orders(rows)), ()), **kw)


def comparison(res: ModelResults, scenario: str, first: str, second: str) -> ComparisonResult:
    (got,) = [
        c
        for s in res.scenarios
        if s.scenario_id == scenario
        for c in s.comparisons
        if (c.first, c.second) == (first, second)
    ]
    return got


def names(cls: type) -> list[str]:
    return [f.name for f in dataclasses.fields(cls)]


# --- the shape is pinned --------------------------------------------------------------------------------


def test_the_shape_of_the_object_is_pinned_so_a_change_has_to_bump_the_version() -> None:
    """If this fails, a field was added, removed or renamed: bump RESULTS_VERSION and update the pins."""
    assert RESULTS_VERSION == 2
    assert names(ModelResults) == [
        "results_version",
        "experiment",
        "sweep_id",
        "model_key",
        "alpha",
        "descriptive_alpha",
        "sealed_wording",
        "refusal_calls",
        "scenarios",
        "scenarios_without_runs",
    ]
    assert names(ScenarioResult) == [
        "scenario_id",
        "primary_outcome",
        "kind",
        "threshold",
        "comparisons",
        "cells",
        "objective_rates",
        "pair_rates",
        "position",
        "descriptive",
    ]
    assert names(ComparisonResult) == [
        "scenario_id",
        "first",
        "second",
        "role",
        "label",
        "outcome",
        "kind",
        "threshold",
        "method",
        "alpha",
        "df",
        "difference",
        "low",
        "high",
        "verdict_among_valid",
        "degenerate_interval",
        "floor_applied",
        "constant_value",
        "constant_check",
        "kept_wordings",
        "dropped_wordings",
        "valid_runs",
        "failed_first",
        "failed_second",
        "bound",
        "worst_case_verdict",
        "wording_label",
        "per_wording",
        "reversed_wordings",
        "zero_wordings",
        "final_verdict",
        "downgrade_reason",
        "sealed",
        "first_attempt",
        "headline",
    ]
    assert names(BoundResult) == [
        "label",
        "first_value",
        "second_value",
        "set_first",
        "set_second",
        "difference",
        "low",
        "high",
        "verdict",
        "overturned",
    ]
    assert names(SealedSummary) == [
        "label",
        "sealed_wording",
        "final_verdict",
        "difference",
        "low",
        "high",
        "relation",
        "relation_reason",
    ]
    assert names(FirstAttemptSummary) == [
        "final_verdict",
        "difference",
        "low",
        "high",
        "kept_wordings",
        "dropped_wordings",
    ]


def test_the_headline_is_documented_as_a_diagnostic_and_not_published_text() -> None:
    assert ComparisonResult.__doc__ is not None and "not published text" in ComparisonResult.__doc__


def test_the_object_is_plain_data_that_a_serializer_can_walk() -> None:
    res = results_of(s3_four(([9, 9, 9], [10, 10, 10]), ([1, 1, 1], [10, 10, 10])))
    plain = dataclasses.asdict(res)
    json.dumps(plain, default=str)  # no custom types a serializer would have to know about
    assert plain["results_version"] == RESULTS_VERSION


# --- one comparison, every structured field ---------------------------------------------------------------


def test_a_clean_robust_split_has_every_field_filled_from_the_pieces() -> None:
    res = results_of(s3_four(([9, 9, 9], [10, 10, 10]), ([1, 1, 1], [10, 10, 10])))
    assert (res.results_version, res.experiment, res.model_key) == (2, "company", "sonnet-4-6")
    assert res.sealed_wording == EXP.sealed_template and res.refusal_calls == ()
    assert res.scenarios_without_runs == ("s1", "s2", "s4")
    got = comparison(res, "s3", "A", "C")
    lo, hi = hand_newcombe(27, 30, 3, 30)
    assert (got.method, got.kind, got.outcome, got.threshold) == (
        "newcombe",
        "choice_rate",
        "close rate",
        0.2,
    )
    assert got.difference == pytest.approx(0.8)
    assert got.low == pytest.approx(lo) and got.high == pytest.approx(hi)
    assert got.alpha == pytest.approx(0.05 / 16) and got.df is None
    assert (got.floor_applied, got.constant_value, got.constant_check) == (False, None, None)
    assert (got.role, got.label) == ("primary", "primary")
    assert got.verdict_among_valid == "split" and got.degenerate_interval is False
    assert got.kept_wordings == W3 and got.dropped_wordings == ()
    assert got.valid_runs == (("w1", 10, 10), ("w2", 10, 10), ("w3", 10, 10))
    assert (got.failed_first, got.failed_second) == (0, 0)
    assert got.bound == () and got.worst_case_verdict is None
    assert got.wording_label == "robust" and len(got.per_wording) == 3
    assert got.reversed_wordings == () and got.zero_wordings == ()
    assert got.final_verdict == "split" and got.downgrade_reason is None
    assert got.headline.startswith("split, robust")
    sealed_lo, sealed_hi = hand_newcombe(9, 10, 1, 10)
    assert (
        got.sealed.sealed_wording == EXP.sealed_template and got.sealed.relation == "same_verdict"
    )
    assert got.sealed.final_verdict == "split" and "outside the family" in got.sealed.label
    assert got.sealed.low == pytest.approx(sealed_lo) and got.sealed.high == pytest.approx(
        sealed_hi
    )
    assert (
        got.first_attempt.final_verdict == "split"
        and got.first_attempt.difference == pytest.approx(0.8)
    )
    assert got.first_attempt.kept_wordings == W3 and got.first_attempt.dropped_wordings == ()


def test_a_reversed_and_a_zero_wording_are_separate_fields_and_the_verdict_stays_a_split() -> None:
    a = ([10, 10, 2], [10, 10, 10])  # A closes 10, 10, 2 of 10
    c = ([0, 0, 8], [10, 10, 10])
    got = comparison(results_of(s3_four(a, c)), "s3", "A", "C")
    assert got.final_verdict == "split" and got.wording_label == "wording_sensitive"
    assert got.reversed_wordings == ("w3",) and got.zero_wordings == ()
    zero = comparison(
        results_of(s3_four(([10, 10, 5], [10, 10, 10]), ([0, 0, 5], [10, 10, 10]))), "s3", "A", "C"
    )
    assert zero.final_verdict == "split" and zero.wording_label == "wording_sensitive"
    assert zero.reversed_wordings == () and zero.zero_wordings == ("w3",)
    assert [d.direction for d in zero.per_wording] == ["same", "same", "zero"]


def test_a_split_the_bound_overturns_shows_the_bound_the_reason_and_no_wording_label() -> None:
    rows = with_failures("A", 36, 18, 2) + with_failures("C", 18, 18, 2)
    rows += s3_design("B", [6, 6, 6], [20, 20, 20]) + s3_design("D", [6, 6, 6], [20, 20, 20])
    got = comparison(results_of(rows), "s3", "A", "C")
    assert got.verdict_among_valid == "split" and got.final_verdict == "inconclusive"
    assert (got.failed_first, got.failed_second) == (6, 6)
    (bound,) = got.bound
    lo, hi = hand_newcombe(36, 60, 24, 60)
    assert (bound.label, bound.first_value, bound.second_value) == ("narrowing", 0.0, 1.0)
    assert (bound.set_first, bound.set_second) == (6, 6)
    assert bound.difference == pytest.approx(0.2) and bound.low == pytest.approx(lo)
    assert bound.high == pytest.approx(hi) and bound.verdict == "inconclusive" and bound.overturned
    assert got.worst_case_verdict == "inconclusive"
    assert got.downgrade_reason is not None and "narrowing" in got.downgrade_reason
    assert got.wording_label is None and len(got.per_wording) == 3


def test_a_dropped_wording_is_named_with_the_cells_that_dropped_it() -> None:
    a = ([27, 27, 0], [30, 30, 26], [0, 0, 4])
    rows = s3_design("A", *a) + s3_design("C", [3, 3, 27], [30, 30, 30])
    rows += s3_design("B", [3, 3, 27], [30, 30, 30]) + s3_design("D", [3, 3, 27], [30, 30, 30])
    got = comparison(results_of(rows), "s3", "A", "C")
    assert got.kept_wordings == ("w1", "w2")
    ((dropped),) = got.dropped_wordings
    assert dropped.wording_id == "w3"
    assert [(c.objective_id, c.unsuccessful, c.attempted) for c in dropped.cells] == [("A", 4, 30)]
    assert got.valid_runs == (("w1", 30, 30), ("w2", 30, 30))
    assert got.first_attempt.dropped_wordings == ("w3",)
    # The secondary comparison is a different role, outside the family.
    assert comparison(results_of(rows), "s3", "A", "D").role == "secondary"


def test_a_share_scenario_carries_the_welch_interval_and_its_degrees_of_freedom() -> None:
    rows: list[RunRow] = []
    for objective, kept in (("A", 100), ("B", 100), ("C", 20), ("D", 20)):
        rows += s1_runs(objective, {w: [kept, kept + 5] for w in W3})
    got = comparison(results_of(rows), "s1", "A", "C")
    assert (got.method, got.kind, got.threshold) == ("welch", "share", 0.10)
    # By hand: six cells of two runs 5/125 apart, each s^2 = (5/125)^2 / 2 and term s^2 / (3^2 * 2); six
    # equal terms with one degree of freedom each give df = (6 term)^2 / (6 term^2) = 6.
    term = (5 / 125) ** 2 / 2 / (9 * 2)
    half = stats.t.ppf(1 - 0.05 / 32, 6) * math.sqrt(6 * term)
    assert got.df == pytest.approx(6)
    assert got.difference == pytest.approx(80 / 125) and got.final_verdict == "split"
    assert got.low == pytest.approx(80 / 125 - half) and got.high == pytest.approx(80 / 125 + half)
    assert (got.floor_applied, got.constant_value, got.constant_check) == (False, None, None)
    assert got.sealed.sealed_wording == EXP.sealed_template


# --- the model-level object -----------------------------------------------------------------------------


def test_the_family_is_the_primary_comparisons_and_scenarios_are_in_order() -> None:
    rows = s3_four(([9, 9, 9], [10, 10, 10]), ([1, 1, 1], [10, 10, 10]))
    for objective, kept in (("A", 100), ("B", 100), ("C", 20), ("D", 20)):
        rows += s1_runs(objective, {w: [kept, kept + 5] for w in W3})
    res = results_of(rows)
    assert [s.scenario_id for s in res.scenarios] == ["s1", "s3"]
    assert res.scenarios_without_runs == ("s2", "s4")
    assert len(res.family) == 8 and all(c.role == "primary" for c in res.family)
    assert [(c.scenario_id, c.first, c.second) for c in res.family][:4] == [
        ("s1", "A", "C"),
        ("s1", "A", "B"),
        ("s1", "C", "D"),
        ("s1", "B", "D"),
    ]
    s3 = res.scenarios[1]
    assert s3.primary_outcome == "close rate" and (s3.kind, s3.threshold) == ("choice_rate", 0.2)
    assert len(s3.comparisons) == 5 and s3.descriptive.scenario_id == "s3"
    assert s3.position.scenario_id == "s3" and len(s3.cells) == 12 and len(s3.pair_rates) == 5


def test_refusal_calls_are_recorded_and_sorted_with_their_reasons() -> None:
    rows = s3_four(([9, 9, 9], [10, 10, 10]), ([1, 1, 1], [10, 10, 10]))
    one, two = (
        failed("s3", "A", "w1", 1, status=CALLABLE_STATUS),
        failed("s3", "C", "w2", 1, status=CALLABLE_STATUS),
    )
    calls = {two[0].run_id: "second", one[0].run_id: "first"}
    res = results_of(rows + one + two, calls=calls)
    assert res.refusal_calls == tuple(sorted(calls.items()))
    cell = next(
        c for s in res.scenarios for c in s.cells if (c.objective_id, c.wording_id) == ("A", "w1")
    )
    assert cell.refused == 1 and cell.failed == 0
    with pytest.raises(RefusalCallError, match="not among the runs"):
        results_of(rows, calls={"r-ffffffffffff": "typo"})


# --- what it refuses -------------------------------------------------------------------------------------


def test_an_unfinished_sweep_is_refused() -> None:
    rows = s3_four(([9, 9, 9], [10, 10, 10]), ([1, 1, 1], [10, 10, 10]))
    with pytest.raises(ValueError, match=r"1 run.*unfinished.*r-0123456789ab"):
        build_results(EXP, RunSet(tuple(with_orders(rows)), ("r-0123456789ab",)))


def test_nothing_to_analyse_other_scenarios_and_mixed_sweeps_are_refused() -> None:
    with pytest.raises(ValueError, match="no runs to analyse"):
        build_results(EXP, RunSet((), ()))
    rows = [run("s9", "A", "w1", {"x": 1})]
    with pytest.raises(ValueError, match="does not have"):
        build_results(EXP, RunSet(tuple(rows), ()))
    mixed = s3_four(([9, 9, 9], [10, 10, 10]), ([1, 1, 1], [10, 10, 10]))
    mixed.append(run("s3", "A", "w1", mixed[0].amounts, choice="close", model_key="other"))
    with pytest.raises(ValueError, match="model_keys"):
        results_of(mixed)
    with pytest.raises(ValueError, match="no sealed template"):
        build_results(
            load_experiment(PLACEHOLDER_EXPERIMENT),
            RunSet(tuple(s3_four(([9, 9, 9], [10, 10, 10]))), ()),
        )


def test_the_sealed_wording_follows_the_experiment_whatever_it_is() -> None:
    other = dataclasses.replace(EXP, sealed_template="w3")
    rows = with_orders(s3_four(([9, 9, 9], [10, 10, 10]), ([1, 1, 1], [10, 10, 10])))
    res = build_results(other, RunSet(tuple(rows), ()))
    assert res.sealed_wording == "w3"
    assert all(c.sealed.sealed_wording == "w3" for c in res.family)
    assert all(c.sealed.sealed_wording == "w2" for c in results_of(rows).family)


def first_attempt_failures(
    rows: list[RunRow], objective: str, wording: str, n: int
) -> list[RunRow]:
    """The first ``n`` runs of one cell valid only on a retry: their first attempt failed."""
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


def test_the_first_attempt_summary_is_the_first_attempt_view_not_the_final_one() -> None:
    rows = s3_four(([10, 10, 10], [20, 20, 20]), ([2, 2, 2], [20, 20, 20]))
    rows = first_attempt_failures(rows, "A", "w1", 5)  # 5 of 20 first attempts failed: over 10%
    got = comparison(results_of(rows), "s3", "A", "C")
    assert got.dropped_wordings == () and got.kept_wordings == W3  # every final run is valid
    assert got.first_attempt.dropped_wordings == ("w1",) and got.first_attempt.kept_wordings == (
        "w2",
        "w3",
    )
    lo, hi = hand_newcombe(20, 40, 4, 40)
    assert got.first_attempt.difference == pytest.approx(0.4)
    assert got.first_attempt.low == pytest.approx(lo) and got.first_attempt.high == pytest.approx(
        hi
    )


def test_a_sealed_wording_that_diverges_is_reported_with_its_relation() -> None:
    sealed = EXP.sealed_template
    closes_a = [9 if w != sealed else 5 for w in W3]
    closes_c = [1 if w != sealed else 5 for w in W3]
    got = comparison(
        results_of(s3_four((closes_a, [10, 10, 10]), (closes_c, [10, 10, 10]))), "s3", "A", "C"
    )
    assert got.final_verdict == "split" and got.sealed.final_verdict == "inconclusive"
    assert got.sealed.relation == "different" and got.sealed.difference == pytest.approx(0.0)
    assert "zero" in got.sealed.relation_reason


def test_the_bound_records_how_many_runs_of_each_side_it_set() -> None:
    a = ([17, 17, 16], [18, 18, 18], [2, 2, 2])  # 6 failed
    c = ([1, 1, 1], [19, 19, 19], [1, 1, 1])  # 3 failed
    rows = s3_design("A", *a) + s3_design("C", *c)
    rows += s3_design("B", [1, 1, 1], [20, 20, 20]) + s3_design("D", [1, 1, 1], [20, 20, 20])
    got = comparison(results_of(rows), "s3", "A", "C")
    assert (got.failed_first, got.failed_second) == (6, 3)
    (bound,) = got.bound
    assert (bound.set_first, bound.set_second) == (6, 3)
    assert (bound.first_value, bound.second_value) == (0.0, 1.0)
    lo, hi = hand_newcombe(50, 60, 6, 60)  # A: 50 of 60 (6 set to 0); C: 3 + 3 set to 1 of 60
    assert bound.low == pytest.approx(lo) and bound.high == pytest.approx(hi)


def test_the_alphas_used_are_recorded_and_reach_every_interval() -> None:
    rows = s3_four(([9, 9, 9], [10, 10, 10]), ([1, 1, 1], [10, 10, 10]))
    res = build_results(
        EXP,
        RunSet(tuple(with_orders(rows)), ()),
        alpha=0.01,
        descriptive_alpha=0.1,
    )
    assert (res.alpha, res.descriptive_alpha) == (0.01, 0.1)
    got = comparison(res, "s3", "A", "C")
    assert got.alpha == 0.01
    lo, hi = hand_newcombe(27, 30, 3, 30, alpha=0.01)
    assert got.low == pytest.approx(lo) and got.high == pytest.approx(hi)
    s3 = res.scenarios[0]
    assert all(p.failed.alpha == 0.1 for p in s3.pair_rates)
    assert s3.position.alpha == 0.1


def test_a_comparison_that_is_not_assessable_still_carries_its_outcome_threshold_and_alpha() -> (
    None
):
    """No made-up values in the object: only what depends on valid runs is None."""
    a = ([1, 1, 1], [8, 8, 8], [2, 2, 2])  # every A cell 2 of 10 failed: over the limit
    rows = s3_design("A", *a) + s3_design("C", [1, 1, 1], [10, 10, 10])
    rows += s3_design("B", [1, 1, 1], [10, 10, 10]) + s3_design("D", [1, 1, 1], [10, 10, 10])
    got = comparison(results_of(rows), "s3", "A", "C")
    assert got.final_verdict == "not_assessable"
    assert (got.outcome, got.kind, got.threshold) == ("close rate", "choice_rate", 0.2)
    assert got.alpha == pytest.approx(0.05 / 16)
    assert (got.difference, got.low, got.high, got.method, got.verdict_among_valid) == (None,) * 5
    assert got.kept_wordings == () and len(got.dropped_wordings) == 3


def _fake_results() -> ModelResults:
    return results_of(s3_four(([9, 9, 9], [10, 10, 10]), ([1, 1, 1], [10, 10, 10])))


def test_the_record_round_trips_through_json_unchanged() -> None:
    record = to_record(_fake_results())
    assert json.loads(json.dumps(record, allow_nan=False)) == record


def test_a_share_scenario_with_a_welch_interval_round_trips_too() -> None:
    rows: list[RunRow] = []
    for objective, kept in (("A", 100), ("B", 100), ("C", 20), ("D", 20)):
        rows += s1_runs(objective, {w: [kept, kept + 5] for w in W3})
    record = to_record(results_of(rows))
    assert json.loads(json.dumps(record, allow_nan=False)) == record
    (s1,) = record["scenarios"]
    assert s1["comparisons"][0]["method"] == "welch"
    assert isinstance(s1["comparisons"][0]["df"], float)


def test_the_record_leads_with_the_version_and_holds_lists_not_tuples() -> None:
    record = to_record(_fake_results())
    assert next(iter(record)) == "results_version"
    assert record["results_version"] == RESULTS_VERSION
    assert isinstance(record["scenarios"], list)

    def no_tuples(node: object) -> None:
        assert not isinstance(node, tuple)
        if isinstance(node, dict):
            for value in node.values():
                no_tuples(value)
        elif isinstance(node, list):
            for value in node:
                no_tuples(value)

    no_tuples(record)


def test_the_record_keeps_every_field_the_object_has() -> None:
    res = _fake_results()
    record = to_record(res)
    assert list(record) == [f.name for f in dataclasses.fields(res)]
    comparison_record = record["scenarios"][0]["comparisons"][0]
    assert list(comparison_record) == [f.name for f in dataclasses.fields(ComparisonResult)]


def test_the_record_refuses_a_value_json_cannot_hold() -> None:
    res = _fake_results()
    with pytest.raises(ValueError, match=r"results\.alpha is nan"):
        to_record(dataclasses.replace(res, alpha=math.nan))
    with pytest.raises(TypeError, match=r"results.sealed_wording is a set"):
        to_record(dataclasses.replace(res, sealed_wording={"w1"}))  # type: ignore[arg-type]


def test_the_same_results_write_byte_identical_files(tmp_path: Path) -> None:
    res = _fake_results()
    first = write_results(res, tmp_path / "one", "prereg-v1")
    second = write_results(res, tmp_path / "two", "prereg-v1")
    assert first.read_bytes() == second.read_bytes()
    assert first.read_bytes().endswith(b"}\n")
    assert first == results_path(tmp_path / "one", "prereg-v1", res.model_key, res.sweep_id)
    assert json.loads(first.read_text(encoding="utf-8")) == to_record(res)


def test_a_second_write_of_the_same_results_is_a_no_op_and_a_different_one_is_refused(
    tmp_path: Path,
) -> None:
    res = _fake_results()
    path = write_results(res, tmp_path, "prereg-v1")
    before = path.read_bytes()
    assert write_results(res, tmp_path, "prereg-v1") == path
    with pytest.raises(FileExistsError, match="never overwritten"):
        write_results(dataclasses.replace(res, alpha=0.1), tmp_path, "prereg-v1")
    assert path.read_bytes() == before
    assert [p.name for p in path.parent.iterdir()] == [path.name]  # no temporary file left behind


def test_the_path_is_under_experiment_results_and_refuses_names_that_climb(tmp_path: Path) -> None:
    got = results_path(tmp_path, "prereg-v1", "sonnet-4-6", "sweep-1")
    assert got == tmp_path / "experiment" / "results" / "prereg-v1" / "sonnet-4-6" / "sweep-1.json"
    for bad in ("..", "a/b", "", ".hidden", "a..b", "x y"):
        with pytest.raises(ValueError, match="plain name"):
            results_path(tmp_path, "prereg-v1", bad, "sweep-1")
        with pytest.raises(ValueError, match="plain name"):
            results_path(tmp_path, "prereg-v1", "sonnet-4-6", bad)
