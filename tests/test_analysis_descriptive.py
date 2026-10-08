"""The descriptive analyses (Phase 3 IMPLEMENTATION doc section 11; step 7).

Hand-built runs with every expected number worked out by hand in the comments.
"""

from __future__ import annotations

import math
from typing import Any

import pytest

from analysis_helpers import failed, run
from horizon_compact.analysis.descriptive import (
    DISPLAY_GROUPS,
    groups_of,
    run_distance,
    summarize,
    total_variation,
)
from horizon_compact.analysis.descriptive import describe_scenario as describe
from horizon_compact.analysis.outcomes import RunOutcome, outcomes_for
from horizon_compact.analysis.records import RunRow
from horizon_compact.experiment import load_experiment

EXP = load_experiment("company")
S1 = outcomes_for(EXP.get_scenario("s1"))
S2 = outcomes_for(EXP.get_scenario("s2"))
S3 = outcomes_for(EXP.get_scenario("s3"))
S4 = outcomes_for(EXP.get_scenario("s4"))


# --- summaries and the display groups ------------------------------------------------------------------


def test_summary_is_the_count_mean_sample_sd_median_and_range() -> None:
    got = summarize([0.2, 0.6, 1.0])
    assert (got.n, got.median, got.minimum, got.maximum) == (3, 0.6, 0.2, 1.0)
    assert got.mean == pytest.approx(0.6) and got.sd == pytest.approx(0.4)  # sample: n - 1
    assert summarize([0.5]).sd is None
    assert summarize([1.0, 3.0]).median == 2.0  # the mean of the middle two
    skewed = summarize([1.0, 2.0, 9.0])
    assert skewed.median == 2.0 and skewed.mean == pytest.approx(4.0)  # the median is not the mean
    with pytest.raises(ValueError, match="nothing"):
        summarize([])


def test_the_groups_follow_planning_07_section_3_3() -> None:
    assert groups_of("s1", "L1") == ("workforce",)
    assert groups_of("s1", "L2") == ("workforce", "future_capability")  # redeployment is both
    assert groups_of("s1", "L3") == ("future_capability",)
    assert groups_of("s1", "L4") == ("workforce",)
    assert groups_of("s1", "L5") == ("customers",)
    assert groups_of("s1", "L6") == ("environment_communities",)
    assert groups_of("s1", "L7") == ("shareholders",)
    assert groups_of("s1", "L9") == ("suppliers",)
    # L8 is lower profit borne by shareholders in S2, and the balance sheet everywhere else.
    assert groups_of("s2", "L8") == ("shareholders",)
    for scenario in ("s1", "s3", "s4"):
        assert groups_of(scenario, "L8") == ("balance_sheet",)
    assert groups_of("s4", "") == ()  # S4's program has no canonical lever
    assert set(DISPLAY_GROUPS) == {
        "workforce",
        "customers",
        "suppliers",
        "future_capability",
        "environment_communities",
        "shareholders",
        "balance_sheet",
    }


# --- S1: allocation, groups, secondary, distances, worked out by hand ------------------------------------


def s1_amounts(eliminate: int, plant: int, keep: int) -> dict[str, float]:
    assert eliminate + plant + keep == 125
    return {"eliminate": eliminate, "move_plant_pay": plant, "move_keep_pay": keep}


def s1_set() -> list[RunRow]:
    """A: w1 has two runs, w2 one. A also has a failed run (never read).
    a1 = (25, 50, 50) shares (.2, .4, .4); a2 = (75, 50, 0) (.6, .4, 0); a3 = (125, 0, 0) (1, 0, 0), in w2.
    E: e1 = (25, 50, 50), e2 = (75, 50, 0), both w1."""
    return [
        run("s1", "A", "w1", s1_amounts(25, 50, 50)),
        run("s1", "A", "w1", s1_amounts(75, 50, 0)),
        run("s1", "A", "w2", s1_amounts(125, 0, 0)),
        *failed("s1", "A", "w1", 2),
        run("s1", "E", "w1", s1_amounts(25, 50, 50)),
        run("s1", "E", "w1", s1_amounts(75, 50, 0)),
    ]


def test_allocation_cells_pool_objective_wording_and_say_how_many_runs() -> None:
    got = describe(S1, s1_set())
    assert got.runs == 5  # the two failed runs are not read
    cells = {(c.objective_id, c.wording_id, c.choice): c for c in got.cells}
    assert set(cells) == {
        ("A", None, None),
        ("A", "w1", None),
        ("A", "w2", None),
        ("E", None, None),
        ("E", "w1", None),
    }
    pooled = {line.key: line for line in cells[("A", None, None)].lines}
    assert cells[("A", None, None)].runs == 3
    elim = pooled["eliminate"].summary  # shares .2, .6, 1.0
    assert (elim.n, elim.median, elim.minimum, elim.maximum) == (3, 0.6, 0.2, 1.0)
    assert elim.mean == pytest.approx(0.6)
    assert elim.sd == pytest.approx(0.4)
    assert pooled["move_plant_pay"].summary.mean == pytest.approx((0.4 + 0.4 + 0.0) / 3)
    assert pooled["move_keep_pay"].summary.mean == pytest.approx(0.4 / 3)
    assert {line.kind for line in cells[("A", None, None)].lines} == {"use"}
    w1 = {line.key: line.summary for line in cells[("A", "w1", None)].lines}
    assert w1["eliminate"].mean == pytest.approx(0.4) and w1["eliminate"].sd == pytest.approx(
        math.sqrt(0.08)
    )
    w2 = {line.key: line.summary for line in cells[("A", "w2", None)].lines}
    assert w2["eliminate"].n == 1 and w2["eliminate"].sd is None and w2["eliminate"].mean == 1.0


def test_display_groups_are_each_runs_lines_summed_and_overlap() -> None:
    got = describe(S1, s1_set())
    cell = next(c for c in got.cells if (c.objective_id, c.wording_id) == ("A", None))
    groups = {(g.group, g.kind): g.summary for g in cell.groups}
    assert list(groups) == [("workforce", "use"), ("future_capability", "use")]
    # workforce = L1 + both L2 lines: every person, so 1.0 on every run; the groups overlap by design.
    assert groups[("workforce", "use")].mean == pytest.approx(1.0)
    assert groups[("workforce", "use")].sd == pytest.approx(0.0)
    # future capability = the two L2 lines only: .8, .4, 0 per run.
    fc = groups[("future_capability", "use")]
    assert (
        fc.mean == pytest.approx(0.4)
        and fc.minimum == pytest.approx(0.0)
        and fc.maximum == pytest.approx(0.8)
    )
    assert fc.median == pytest.approx(0.4)


def test_the_s1_secondary_is_undefined_for_a_run_that_moved_no_one_and_says_so() -> None:
    got = describe(S1, s1_set())
    rows = {(r.objective_id, r.wording_id, r.choice): r for r in got.secondaries}
    pooled = rows[("A", None, None)]
    # keep-pay share of those moved: a1 = 50/100 = .5, a2 = 0/50 = 0, a3 moved no one: undefined.
    assert pooled.name == "keep_pay_share_of_moved"
    assert pooled.mean == pytest.approx(0.25) and (pooled.n_defined, pooled.n_runs) == (2, 3)
    w2 = rows[("A", "w2", None)]
    assert (w2.mean, w2.n_defined, w2.n_runs) == (None, 0, 1)


def test_distances_between_e_and_each_objective_and_each_objectives_own_spread() -> None:
    got = describe(S1, s1_set())
    by = {d.objective_id: d for d in got.distances}
    # Total variation, half the sum of absolute differences of the vectors:
    # e1-a1 = 0, e1-a2 = .5 x (.4 + 0 + .4) = .4, e1-a3 = .5 x (.8 + .4 + .4) = .8,
    # e2-a1 = .4, e2-a2 = 0, e2-a3 = .5 x (.4 + .4 + 0) = .4: six pairs summing to 2.0.
    assert by["A"].e_to_objective == pytest.approx(2.0 / 6) and by["A"].e_pairs == 6
    # A against itself: (a1,a2) = .4, (a1,a3) = .8, (a2,a3) = .4.
    assert by["A"].self_distance == pytest.approx(1.6 / 3) and by["A"].self_pairs == 3
    # E against itself: (e1, e2) = .4. Its distance "to E" is not reported.
    assert by["E"].e_to_objective is None and by["E"].e_pairs == 0
    assert by["E"].self_distance == pytest.approx(0.4) and by["E"].self_pairs == 1
    assert by["A"].e_choice_only_pairs == 0


def test_no_baseline_runs_means_no_distances_and_one_run_has_no_self_distance() -> None:
    rows = [run("s1", "A", "w1", s1_amounts(25, 50, 50))]
    assert describe(S1, rows).distances == ()
    rows.append(run("s1", "E", "w1", s1_amounts(25, 50, 50)))
    by = {d.objective_id: d for d in describe(S1, rows).distances}
    assert by["A"].self_distance is None and by["A"].self_pairs == 0
    assert by["A"].e_to_objective == pytest.approx(0.0)


def test_per_run_values_are_kept_whole_and_sorted() -> None:
    got = describe(S1, s1_set())
    assert [r.run_id for r in got.per_run] == sorted(r.run_id for r in got.per_run) and len(
        got.per_run
    ) == 5
    first = next(r for r in got.per_run if (r.objective_id, r.wording_id) == ("A", "w2"))
    assert first.primary == pytest.approx(0.0)  # share kept: nobody
    assert dict(first.shares) == {"eliminate": 1.0, "move_plant_pay": 0.0, "move_keep_pay": 0.0}
    assert dict(first.secondary) == {"keep_pay_share_of_moved": None}
    assert (first.repeat, first.choice) == (0, None)


# --- S3: choices, lines by choice, retained share --------------------------------------------------------

S3_LINES = ("eliminated", "moved_other_plants", "kept_at_plant", "transferred_to_buyer")


def s3_run(objective: str, wording: str, choice: str, *people: int, **kw: Any) -> RunRow:
    assert sum(people) == 190
    return run(
        "s3", objective, wording, dict(zip(S3_LINES, people, strict=True)), choice=choice, **kw
    )


def s3_set() -> list[RunRow]:
    """A, w1: c1 close (95, 95, 0, 0); c2 retool (0, 0, 190, 0); c3 close (190, 0, 0, 0). E, w1: one
    retool run with the same people as c2."""
    return [
        s3_run("A", "w1", "close", 95, 95, 0, 0),
        s3_run("A", "w1", "retool", 0, 0, 190, 0),
        s3_run("A", "w1", "close", 190, 0, 0, 0),
        s3_run("E", "w1", "retool", 0, 0, 190, 0),
    ]


def test_the_choice_split_counts_every_option_including_zeros() -> None:
    got = describe(S3, s3_set())
    splits = {(s.objective_id, s.wording_id): s for s in got.choice_splits}
    assert splits[("A", None)].counts == (("close", 2), ("retool", 1), ("sell", 0))
    assert (
        splits[("A", "w1")].counts == (("close", 2), ("retool", 1), ("sell", 0))
        and splits[("A", "w1")].runs == 3
    )
    assert splits[("E", None)].counts == (("close", 0), ("retool", 1), ("sell", 0))


def test_the_lines_by_choice_are_cells_with_a_choice_named() -> None:
    got = describe(S3, s3_set())
    cells = {(c.objective_id, c.wording_id, c.choice): c for c in got.cells}
    close = {line.key: line.summary for line in cells[("A", None, "close")].lines}
    assert cells[("A", None, "close")].runs == 2  # c1 and c3
    assert close["eliminated"].mean == pytest.approx((0.5 + 1.0) / 2)
    assert close["moved_other_plants"].mean == pytest.approx(0.25)
    retool = {line.key: line.summary for line in cells[("A", None, "retool")].lines}
    assert retool["kept_at_plant"].mean == pytest.approx(1.0)
    assert ("A", None, "sell") not in cells  # no run chose it: no empty cell
    assert ("A", "w1", "close") not in cells  # by choice is pooled over wordings, not per wording


def test_the_retained_share_is_summarized_overall_and_by_choice() -> None:
    got = describe(S3, s3_set())
    rows = {(r.objective_id, r.wording_id, r.choice): r for r in got.secondaries}
    # retained share = 1 - eliminated / 190: c1 .5, c2 1.0, c3 0.
    assert rows[("A", None, None)].mean == pytest.approx(0.5)
    assert (
        rows[("A", None, "close")].mean == pytest.approx(0.25)
        and rows[("A", None, "close")].n_defined == 2
    )
    assert rows[("A", None, "retool")].mean == pytest.approx(1.0)


def test_distance_uses_the_choice_where_there_is_one() -> None:
    got = describe(S3, s3_set())
    by = {d.objective_id: d for d in got.distances}
    # e vector (0, 0, 1, 0), retool. c1 (.5, .5, 0, 0) close: TV 1.0, choice 1, mean 1.0.
    # c2 identical, retool: 0 and 0. c3 (1, 0, 0, 0) close: TV 1.0, choice 1, mean 1.0. Mean 2/3.
    assert by["A"].e_to_objective == pytest.approx(2 / 3) and by["A"].e_pairs == 3
    # A against itself: (c1,c2): TV 1.0, choices differ: 1.0. (c1,c3): TV .5, same choice: mean .25.
    # (c2,c3): TV 1.0, choices differ: 1.0. Mean .75.
    assert by["A"].self_distance == pytest.approx(0.75)


# --- S4: uses and sources apart, by choice ----------------------------------------------------------------


def s4_run(objective: str, choice: str, **lines: int) -> RunRow:
    keys = [lever.key for lever in EXP.get_scenario("s4").offered()]
    amounts = dict.fromkeys(keys, 0) | lines
    return run("s4", objective, "w1", amounts, choice=choice)


def test_s4_sums_uses_and_sources_apart_and_leaves_the_program_ungrouped() -> None:
    rows = [
        s4_run(
            "C", "fund", program=5_100_000, increase_payouts=10_200_000, eliminate_roles=5_100_000
        ),
        s4_run("C", "decline", cut_payouts=2_040_000, cut_wages_hours=2_040_000),
    ]
    got = describe(S4, rows)
    cells = {(c.objective_id, c.wording_id, c.choice): c for c in got.cells}
    fund = cells[("C", None, "fund")]
    assert [(g.group, g.kind) for g in fund.groups] == [
        ("workforce", "use"),
        ("workforce", "source"),
        ("customers", "use"),
        ("customers", "source"),
        ("suppliers", "source"),
        ("future_capability", "use"),
        ("future_capability", "source"),
        ("environment_communities", "use"),
        ("environment_communities", "source"),
        ("shareholders", "use"),
        ("shareholders", "source"),
        ("balance_sheet", "use"),
    ]
    by = {(g.group, g.kind): g.summary.mean for g in fund.groups}
    assert by[("shareholders", "use")] == pytest.approx(0.5)  # 10.2M of 20.4M
    assert by[("workforce", "source")] == pytest.approx(0.25)  # 5.1M of 20.4M
    assert by[("workforce", "use")] == pytest.approx(0.0)
    lines = {line.key: line for line in fund.lines}
    assert lines["program"].summary.mean == pytest.approx(0.25) and lines["program"].kind == "use"
    assert lines["eliminate_roles"].kind == "source"  # the funding sources among funding runs
    decline = {line.key: line.summary.mean for line in cells[("C", None, "decline")].lines}
    assert decline["cut_payouts"] == pytest.approx(0.1) and decline[
        "cut_wages_hours"
    ] == pytest.approx(0.1)


def test_s4_any_cuts_among_funding_runs_and_among_declining_runs() -> None:
    rows = [
        s4_run("C", "fund", program=5_100_000),
        s4_run("C", "fund", program=5_100_000, cut_rnd=1_000_000),
        s4_run("C", "decline"),
    ]
    got = describe(S4, rows)
    secondary = {(r.choice, r.name): r for r in got.secondaries if r.wording_id is None}
    assert (secondary[("fund", "any_cuts")].mean, secondary[("fund", "any_cuts")].n_runs) == (
        0.5,
        2,
    )
    assert secondary[("decline", "any_cuts")].mean == 0.0
    assert secondary[(None, "any_cuts")].mean == pytest.approx(1 / 3)


def test_s2_has_a_cell_per_bearer_and_no_secondary_and_no_choice() -> None:
    keys = [lever.key for lever in EXP.get_scenario("s2").offered()]
    amounts = dict.fromkeys(keys, 0) | {"eliminate_roles": 56_050_000, "cut_rnd": 56_050_000}
    got = describe(S2, [run("s2", "B", "w1", amounts)])
    (pooled, w1) = got.cells
    assert (pooled.wording_id, w1.wording_id) == (None, "w1")
    assert {line.key: line.summary.mean for line in pooled.lines}[
        "eliminate_roles"
    ] == pytest.approx(0.5)
    assert got.secondaries == () and got.choice_splits == ()
    assert {g.group for g in pooled.groups} == {
        "workforce",
        "future_capability",
        "environment_communities",
        "customers",
        "suppliers",
        "shareholders",
    }


# --- the distance itself, on every branch -----------------------------------------------------------------


def outcome(vector: dict[str, float] | None, choice: str | None) -> RunOutcome:
    return RunOutcome(0.0, {}, vector, choice)


def test_total_variation_is_half_the_sum_of_absolute_differences() -> None:
    assert total_variation({"a": 1.0, "b": 0.0}, {"a": 0.0, "b": 1.0}) == 1.0
    assert total_variation({"a": 0.5, "b": 0.5}, {"a": 0.5, "b": 0.5}) == 0.0
    assert total_variation({"a": 0.7, "b": 0.3}, {"a": 0.4, "b": 0.6}) == pytest.approx(0.3)
    with pytest.raises(ValueError, match="same lines"):
        total_variation({"a": 1.0}, {"b": 1.0})


def test_run_distance_basis_is_both_vector_or_choice() -> None:
    a, b = {"x": 1.0, "y": 0.0}, {"x": 0.0, "y": 1.0}
    both = run_distance(outcome(a, "fund"), outcome(b, "fund"), has_choice=True)
    assert both.value == pytest.approx(0.5) and both.basis == "both"  # mean of 1.0 and 0.0
    assert run_distance(outcome(a, "fund"), outcome(b, "decline"), has_choice=True).value == 1.0
    only_vector = run_distance(outcome(a, None), outcome(b, None), has_choice=False)
    assert (only_vector.value, only_vector.basis) == (1.0, "vector")
    # A scenario with no choice ignores a choice a run happens to carry: only the vectors count.
    near, nearer = {"x": 0.5, "y": 0.5}, {"x": 0.4, "y": 0.6}
    ignored = run_distance(outcome(near, "fund"), outcome(nearer, "decline"), has_choice=False)
    assert ignored.value == pytest.approx(0.1) and ignored.basis == "vector"
    # S4 with every line zero has no vector: the choice alone, recorded.
    choice_only = run_distance(outcome(None, "fund"), outcome(a, "decline"), has_choice=True)
    assert (choice_only.value, choice_only.basis) == (1.0, "choice")
    assert run_distance(outcome(None, "fund"), outcome(None, "fund"), has_choice=True).value == 0.0
    with pytest.raises(ValueError, match="neither a vector nor a choice"):
        run_distance(outcome(None, None), outcome(a, "fund"), has_choice=True)


def test_a_choice_only_pair_is_counted_in_the_distance_row() -> None:
    zero = dict.fromkeys((lever.key for lever in EXP.get_scenario("s4").offered()), 0)
    rows = [
        run("s4", "E", "w1", zero, choice="decline"),
        run("s4", "A", "w1", zero | {"program": 1_000_000}, choice="fund"),
        run("s4", "A", "w1", zero, choice="decline"),
    ]
    by = {d.objective_id: d for d in describe(S4, rows).distances}
    # e vs the program run: vector undefined for e (all zero), so the choice alone: fund vs decline, 1.0.
    # e vs the zero run: choice alone, same choice: 0. Both pairs are choice-only.
    assert by["A"].e_pairs == 2 and by["A"].e_choice_only_pairs == 2
    assert by["A"].e_to_objective == pytest.approx(0.5)


# --- what it refuses ------------------------------------------------------------------------------------


def test_describe_refuses_nothing_to_describe_and_mixed_sweeps() -> None:
    with pytest.raises(ValueError, match="no runs on s1"):
        describe(S1, [])
    with pytest.raises(ValueError, match="no valid run"):
        describe(S1, failed("s1", "A", "w1", 2))
    rows = [*s1_set(), run("s1", "A", "w1", s1_amounts(25, 50, 50), sweep_id="another")]
    with pytest.raises(ValueError, match="sweep_ids"):
        describe(S1, rows)
