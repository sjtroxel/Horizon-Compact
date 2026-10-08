"""The matcher (Phase 3 doc 13, step 9) on hand-built runs, every expected number worked out by hand."""

from __future__ import annotations

import dataclasses
from collections.abc import Sequence

import pytest

from analysis_helpers import failed, run
from horizon_compact.analysis import matcher
from horizon_compact.analysis.descriptive import RunDistance, distance, run_distance
from horizon_compact.analysis.intervals import DESCRIPTIVE_ALPHA, stratified_bootstrap_value
from horizon_compact.analysis.matcher import (
    CompanyDecision,
    MatcherError,
    match_case,
    observable_vector,
)
from horizon_compact.analysis.outcomes import RunOutcome
from horizon_compact.analysis.records import RunRow
from horizon_compact.experiment import Scenario, load_experiment

EXP = load_experiment("company")
S2 = EXP.get_scenario("s2")
S3 = EXP.get_scenario("s3")
S4 = EXP.get_scenario("s4")
B = 4_000  # resamples: enough for the bounded cases below, quick to run


def s3(objective: str, wording: str, elim: int, kept: int, moved: int, choice: str) -> RunRow:
    assert elim + kept + moved == 190
    amounts = {
        "eliminated": elim,
        "moved_other_plants": moved,
        "kept_at_plant": kept,
        "transferred_to_buyer": 0,
    }
    return run("s3", objective, wording, amounts, choice=choice)


def s2(objective: str, wording: str, **lines: float) -> RunRow:
    amounts = {lever.key: 0.0 for lever in S2.offered()}
    amounts.update(lines)
    return run("s2", objective, wording, amounts)


# The S3 case used throughout. The company: eliminated 100 and kept 100 (observable), chose to close.
# Observable vector {eliminated: 0.5, kept_at_plant: 0.5}.
COMPANY = CompanyDecision("primary", {"eliminated": 100, "kept_at_plant": 100}, "close")
# A, per wording: a run eliminating all 190 and closing (TV 0.5, choice 0: distance 0.25) and a run
#   eliminating 95, keeping 95 and closing (TV 0, choice 0: distance 0). Cell mean 0.125; A = 0.125.
# B, per wording: two runs keeping all 190 and retooling (TV 0.5, choice 1: distance 0.75). B = 0.75.
# C: like A. D: like B. E, per wording: one run of each of A's and B's kinds. E = (0.25 + 0.75) / 2 = 0.5.


def a_like(objective: str, wording: str) -> list[RunRow]:
    return [s3(objective, wording, 190, 0, 0, "close"), s3(objective, wording, 95, 95, 0, "close")]


def b_like(objective: str, wording: str) -> list[RunRow]:
    return [s3(objective, wording, 0, 190, 0, "retool")] * 2


def case_rows(objectives: str = "ABDE", wordings: Sequence[str] = ("w1", "w2")) -> list[RunRow]:
    rows: list[RunRow] = []
    for w in wordings:
        for o in objectives:
            if o in "AC":
                rows += a_like(o, w)
            elif o in "BD":
                rows += b_like(o, w)
            else:
                rows += [s3(o, w, 190, 0, 0, "close"), s3(o, w, 0, 190, 0, "retool")]
    return rows


def match(
    rows: Sequence[RunRow],
    *readings: CompanyDecision,
    objectives: str = "ABDE",
    d_star: float = 1.0,
    k_star: int = 1,
    scenario: Scenario = S3,
) -> matcher.CaseMatch:
    return match_case(
        scenario,
        rows,
        list(readings) or [COMPANY],
        case_id="case-test",
        objectives=list(objectives),
        d_star=d_star,
        k_star=k_star,
        resamples=B,
    )


def by_objective(m: matcher.ReadingMatch) -> dict[str, matcher.ObjectiveDistance]:
    return {d.objective_id: d for d in m.distances}


# --- the per-run distance ----------------------------------------------------------------------------------


def test_observable_vector_restricts_and_renormalizes() -> None:
    amounts = {"a": 10.0, "b": 30.0, "c": 60.0}
    assert observable_vector(amounts, ["a", "b"]) == {"a": 0.25, "b": 0.75}
    assert observable_vector(amounts, ["c"]) == {"c": 1.0}
    assert observable_vector({"a": 0.0, "b": 0.0, "c": 5.0}, ["a", "b"]) is None


def test_the_distance_has_one_definition() -> None:
    v1, v2 = {"x": 1.0, "y": 0.0}, {"x": 0.5, "y": 0.5}
    assert distance(v1, v2, "close", "close") == RunDistance(0.25, "both")
    assert distance(v1, v2, "close", "sell") == RunDistance(0.75, "both")
    assert distance(v1, v2, None, None) == RunDistance(0.5, "vector")
    assert distance(None, v2, "close", "sell") == RunDistance(1.0, "choice")
    assert distance(None, v2, None, "sell") is None
    # run_distance (section 11) is the same function on two runs' outcomes
    a, b = RunOutcome(0.0, {}, v1, "close"), RunOutcome(0.0, {}, v2, "sell")
    assert run_distance(a, b, has_choice=True) == RunDistance(0.75, "both")
    assert run_distance(a, b, has_choice=False) == RunDistance(0.5, "vector")
    with pytest.raises(ValueError, match="neither"):
        run_distance(RunOutcome(0.0, {}, None, None), b, has_choice=False)


# --- distances, the label and the gap ----------------------------------------------------------------------


def test_the_distances_by_hand_and_a_clear_match() -> None:
    m = match(case_rows()).readings[0]
    d = by_objective(m)
    assert d["A"].distance == pytest.approx(0.125)
    assert d["B"].distance == pytest.approx(0.75)
    assert d["D"].distance == pytest.approx(0.75)
    assert d["E"].distance == pytest.approx(0.5)
    assert [x.objective_id for x in m.distances] == [
        "A",
        "B",
        "D",
        "E",
    ]  # objective order, not ranked
    assert (m.label, m.nearest, m.tied_with) == ("match", "A", None)
    assert m.company_basis == "both" and m.dimensions == 3
    assert m.observable_lines == ("eliminated", "kept_at_plant")  # file order
    # gap E - A: A's resampled values lie in [0, 0.25], E's in [0.25, 0.75] (each cell's mean of two runs),
    # so the gap's interval sits in [0, 0.75]; the estimate is 0.5 - 0.125 = 0.375
    assert m.gap is not None
    assert (m.gap.nearest, m.gap.second) == ("A", "E")
    assert m.gap.estimate == pytest.approx(0.375)
    assert 0 < m.gap.low <= m.gap.estimate <= m.gap.high <= 0.75


def test_the_spread_is_a_95_percent_stratified_bootstrap_of_the_runs_distances() -> None:
    m = match(case_rows()).readings[0]
    a = by_objective(m)["A"]
    expected = stratified_bootstrap_value(
        {"w1": [0.25, 0.0], "w2": [0.25, 0.0]}, seed=a.seed, alpha=DESCRIPTIVE_ALPHA, resamples=B
    )
    assert (a.low, a.high) == (expected.low, expected.high)
    assert 0.0 <= a.low < a.distance < a.high <= 0.25
    b = by_objective(m)["B"]  # every run 0.75: zero width
    assert (b.low, b.high) == (0.75, 0.75)


def test_two_identical_nearest_objectives_tie_and_the_id_breaks_the_order() -> None:
    m = match(case_rows("ABCD"), objectives="ABCD").readings[0]
    assert (m.label, m.nearest, m.tied_with) == ("tie", "A", "C")
    assert m.gap is not None and m.gap.estimate == pytest.approx(0.0)
    assert m.gap.low <= 0 <= m.gap.high


def test_an_objective_is_the_mean_of_its_wording_means() -> None:
    # A: w1 holds three runs at 0 (eliminate 95, keep 95, close), w2 one run at 0.25 (eliminate 190, close).
    # Mean of wording means: (0 + 0.25) / 2 = 0.125; a plain mean would be 0.0625.
    rows = [s3("A", "w1", 95, 95, 0, "close")] * 3 + [s3("A", "w2", 190, 0, 0, "close")]
    rows += b_like("B", "w1") + b_like("B", "w2")
    m = match(rows, objectives="AB").readings[0]
    assert by_objective(m)["A"].distance == pytest.approx(0.125)


def test_failed_runs_are_never_distanced() -> None:
    rows = case_rows() + failed("s3", "A", "w1", 4)
    m = match(rows).readings[0]
    assert by_objective(m)["A"].runs == 4
    assert by_objective(m)["A"].distance == pytest.approx(0.125)


def test_runs_of_other_scenarios_are_not_read() -> None:
    rows = [*case_rows(), s2("A", "w1", cut_rnd=1.0)]
    assert match(rows) == match(case_rows())


# --- no good match: the threshold, strictly above ----------------------------------------------------------


def test_no_good_match_only_strictly_above_d_star() -> None:
    at = match(case_rows(), d_star=0.125).readings[0]  # A's distance is exactly 0.125
    assert at.label == "match"
    above = match(case_rows(), d_star=0.125 - 1e-6).readings[0]
    assert (above.label, above.nearest) == ("no_good_match", "A")
    assert "0.1250 is above" in above.reason
    assert above.distances == at.distances  # all five still shown


def test_no_good_match_comes_before_tie() -> None:
    m = match(case_rows("ABCD"), objectives="ABCD", d_star=0.1).readings[0]
    assert (m.label, m.tied_with) == ("no_good_match", None)


# --- minimum evidence --------------------------------------------------------------------------------------


def test_not_enough_disclosed_below_k_star_and_matched_at_it() -> None:
    below = match(case_rows(), k_star=4).readings[0]  # three dimensions: two lines and the choice
    assert below.label == "not_enough_disclosed"
    assert (below.nearest, below.gap, below.distances) == (None, None, ())
    assert "3 observable dimension(s), fewer than the 4" in below.reason
    assert match(case_rows(), k_star=3).readings[0].label == "match"


def test_the_choice_counts_as_one_dimension_and_each_line_as_one() -> None:
    assert COMPANY.dimensions == 3
    assert CompanyDecision("r", {"eliminated": 1}, None).dimensions == 1
    assert CompanyDecision("r", {}, "close").dimensions == 1


def test_a_company_with_nothing_to_distance_on_is_not_enough_disclosed() -> None:
    # S2 has no choice; the disclosed lines are both zero, so the money dimension is undefined
    nothing = CompanyDecision("primary", {"cut_rnd": 0, "raise_prices": 0}, None)
    rows = [s2(o, "w1", cut_rnd=1.0) for o in "AB"]
    m = match(rows, nothing, objectives="AB", scenario=S2).readings[0]
    assert m.label == "not_enough_disclosed" and m.company_basis is None
    assert "sum to zero and no choice" in m.reason


# --- choice only, and runs with nothing to distance ---------------------------------------------------------


def test_a_company_whose_observable_lines_sum_to_zero_is_matched_on_the_choice() -> None:
    company = CompanyDecision("primary", {"transferred_to_buyer": 0}, "close")
    m = match(case_rows(), company).readings[0]
    assert m.company_basis == "choice"
    d = by_objective(m)
    # A always closes: 0. B always retools: 1. E: one of each per wording: 0.5.
    assert (d["A"].distance, d["B"].distance, d["E"].distance) == (0.0, 1.0, 0.5)
    assert (
        d["A"].choice_only_runs == 0
    )  # counted only when the company has a vector and the run has not


def test_a_run_with_nothing_on_the_observable_lines_is_distanced_on_its_choice() -> None:
    # moved all 190 elsewhere, closed: observable lines (eliminated, kept) sum to 0, so choice alone: 0
    rows = [*case_rows(), s3("A", "w1", 0, 0, 190, "close")]
    m = match(rows).readings[0]
    a = by_objective(m)["A"]
    assert a.choice_only_runs == 1 and a.runs == 5
    # w1: (0.25 + 0 + 0) / 3; w2: 0.125. Mean: (0.08333 + 0.125) / 2 = 0.10417
    assert a.distance == pytest.approx((0.25 / 3 + 0.125) / 2)


def test_a_run_with_no_observable_choice_and_nothing_on_the_lines_is_left_out_and_counted() -> None:
    company = CompanyDecision("primary", {"cut_rnd": 10, "raise_prices": 30}, None)  # 0.25 / 0.75
    rows = [
        s2("A", "w1", cut_rnd=10, raise_prices=30),  # 0
        s2("A", "w1", cut_rnd=40),  # TV: |1 - 0.25| / 2 + |0 - 0.75| / 2 = 0.75
        s2("A", "w1", lower_profit=1e6),  # nothing observable: left out
        s2("B", "w1", raise_prices=5),  # TV 0.25
    ]
    m = match(rows, company, objectives="AB", scenario=S2).readings[0]
    a = by_objective(m)["A"]
    assert (a.runs, a.undistanced_runs) == (2, 1)
    assert a.distance == pytest.approx(0.375)
    assert by_objective(m)["B"].distance == pytest.approx(0.25)
    assert m.nearest == "B"


def test_one_observable_line_and_no_choice_puts_every_run_at_zero() -> None:
    # A finding for step 12, held here: renormalized over a single line, every run that puts anything
    # there is identical to the company, so a lone line carries no information.
    company = CompanyDecision("primary", {"cut_rnd": 10}, None)
    rows = [s2("A", "w1", cut_rnd=1, raise_prices=99), s2("B", "w1", cut_rnd=50)]
    rows += [s2("A", "w2", cut_rnd=7), s2("B", "w2", cut_rnd=1e6)]
    m = match(rows, company, objectives="AB", scenario=S2).readings[0]
    assert [d.distance for d in m.distances] == [0.0, 0.0]
    assert m.label == "tie"


def test_an_objective_none_of_whose_runs_can_be_distanced_is_refused() -> None:
    company = CompanyDecision("primary", {"cut_rnd": 10, "raise_prices": 30}, None)
    rows = [s2("A", "w1", cut_rnd=10), s2("B", "w1", lower_profit=5)]
    with pytest.raises(MatcherError, match="no run of objective B can be distanced"):
        match(rows, company, objectives="AB", scenario=S2)


# --- readings ----------------------------------------------------------------------------------------------


def test_an_alternative_reading_that_moves_the_nearest_objective_depends_on_reading() -> None:
    # Read as "retool, kept all": B and D (always retool, keep 190) are at 0; A far.
    alt = CompanyDecision("kept-not-eliminated", {"eliminated": 0, "kept_at_plant": 190}, "retool")
    m = match(case_rows(), COMPANY, alt)
    assert [r.reading for r in m.readings] == ["primary", "kept-not-eliminated"]
    assert m.readings[0].nearest == "A"
    assert m.readings[1].nearest == "B" and m.readings[1].label == "tie"  # B and D identical
    assert m.depends_on_reading


def test_an_alternative_reading_with_the_same_nearest_does_not() -> None:
    alt = CompanyDecision("more-eliminated", {"eliminated": 150, "kept_at_plant": 50}, "close")
    m = match(case_rows(), COMPANY, alt)
    assert [r.nearest for r in m.readings] == ["A", "A"]
    assert not m.depends_on_reading


def test_a_reading_with_too_little_disclosed_does_not_count_toward_depends_on_reading() -> None:
    alt = CompanyDecision("choice-only", {}, "retool")  # one dimension, below k* = 2
    m = match(case_rows(), COMPANY, alt, k_star=2)
    assert m.readings[1].label == "not_enough_disclosed"
    assert not m.depends_on_reading


def test_each_reading_and_each_objective_has_its_own_seed() -> None:
    alt = CompanyDecision("more-eliminated", {"eliminated": 150, "kept_at_plant": 50}, "close")
    m = match(case_rows(), COMPANY, alt)
    seeds = [d.seed for r in m.readings for d in r.distances]
    seeds += [r.gap.seed for r in m.readings if r.gap is not None]
    assert len(set(seeds)) == len(seeds)


def test_the_match_is_reproducible() -> None:
    assert match(case_rows()) == match(case_rows())


# --- refusals ----------------------------------------------------------------------------------------------


def test_the_matcher_refuses_without_calibration() -> None:
    assert matcher.D_STAR is None and matcher.K_STAR is None  # set by step 10
    with pytest.raises(MatcherError, match="not calibrated"):
        match_case(S3, case_rows(), [COMPANY], case_id="c", objectives=list("ABDE"))
    with pytest.raises(MatcherError, match="not calibrated"):
        match_case(S3, case_rows(), [COMPANY], case_id="c", objectives=list("ABDE"), d_star=0.5)


@pytest.mark.parametrize(
    ("decision", "message"),
    [
        (CompanyDecision("r", {"no_such_line": 1}, "close"), "does not offer"),
        (CompanyDecision("r", {"eliminated": -1, "kept_at_plant": 1}, "close"), "negative"),
        (CompanyDecision("r", {"eliminated": float("nan")}, "close"), "negative or missing"),
        (CompanyDecision("r", {"eliminated": 1}, "liquidate"), "offers"),
    ],
)
def test_a_reading_naming_what_the_scenario_lacks_is_refused(
    decision: CompanyDecision, message: str
) -> None:
    with pytest.raises(MatcherError, match=message):
        match(case_rows(), decision)


def test_a_choice_on_a_scenario_without_one_is_refused() -> None:
    with pytest.raises(MatcherError, match="has none"):
        match(
            [s2("A", "w1", cut_rnd=1)],
            CompanyDecision("r", {"cut_rnd": 1}, "close"),
            objectives="AB",
            scenario=S2,
        )


def test_the_case_level_refusals() -> None:
    with pytest.raises(MatcherError, match="no reading"):
        match_case(S3, case_rows(), [], case_id="c", objectives=list("AB"), d_star=1, k_star=1)
    with pytest.raises(MatcherError, match="repeat"):
        match(case_rows(), COMPANY, COMPANY)
    with pytest.raises(MatcherError, match="at least two distinct"):
        match(case_rows(), objectives="A")
    with pytest.raises(MatcherError, match="at least two distinct"):
        match(case_rows(), objectives="AA")
    with pytest.raises(MatcherError, match="no runs on s3"):
        match([s2("A", "w1", cut_rnd=1)])
    with pytest.raises(MatcherError, match="objective C has no valid run"):
        match(case_rows(), objectives="ABC")


def test_two_sweeps_or_two_models_are_refused() -> None:
    rows = case_rows()
    for odd in (
        dataclasses.replace(rows[0], sweep_id="another"),
        dataclasses.replace(rows[0], model_key="another"),
    ):
        with pytest.raises(ValueError, match="one sweep of one model"):
            match([*rows, odd])


def test_objectives_with_different_wordings_are_refused() -> None:
    rows = case_rows("AB", ("w1", "w2")) + a_like("A", "w3")
    with pytest.raises(MatcherError, match="different wordings"):
        match(rows, objectives="AB")


def test_the_s4_vector_holds_uses_and_sources_together() -> None:
    # decision 9: S4's observable uses and sources are renormalized together.
    # Company: add_rnd 3, cut_payouts 1 -> {0.75, 0.25}. Run: add_rnd 1, cut_payouts 1 -> {0.5, 0.5}: TV 0.25.
    lines = {lever.key: 0.0 for lever in S4.offered()}
    company = CompanyDecision("primary", {"add_rnd": 3, "cut_payouts": 1}, None)
    rows = [
        run(
            "s4",
            o,
            "w1",
            {**lines, "add_rnd": 1.0, "cut_payouts": 1.0, "program": 5.0},
            choice="fund",
        )
        for o in "AB"
    ]
    m = match(rows, company, objectives="AB", scenario=S4).readings[0]
    assert [d.distance for d in m.distances] == [pytest.approx(0.25)] * 2


# --- gaps the mutation check showed ------------------------------------------------------------------------


def test_observable_lines_are_kept_in_file_order_whatever_order_the_rubric_gives() -> None:
    company = CompanyDecision("primary", {"kept_at_plant": 100, "eliminated": 100}, "close")
    m = match(case_rows(), company).readings[0]
    assert m.observable_lines == ("eliminated", "kept_at_plant")


def test_a_run_that_is_not_valid_is_never_distanced_even_if_it_carries_amounts() -> None:
    odd = dataclasses.replace(s3("A", "w1", 0, 190, 0, "retool"), status="refusal")
    m = match([*case_rows(), odd]).readings[0]
    assert by_objective(m)["A"].runs == 4
    assert by_objective(m)["A"].distance == pytest.approx(0.125)


def test_the_spread_is_at_95_percent_not_at_the_family_level() -> None:
    # A: per wording, ten runs whose distances are 0 or 0.5 (S2, no choice, company 0.5 / 0.5): the
    # resampled values are fine enough that the 95% and 99.7% intervals differ.
    company = CompanyDecision("primary", {"cut_rnd": 1, "raise_prices": 1}, None)
    rows = []
    for w in ("w1", "w2"):
        rows += [s2("A", w, cut_rnd=1, raise_prices=1)] * 5 + [s2("A", w, cut_rnd=1)] * 5
        rows += [s2("B", w, raise_prices=1)] * 3
    m = match(rows, company, objectives="AB", scenario=S2).readings[0]
    a = by_objective(m)["A"]
    cells = {"w1": [0.0] * 5 + [0.5] * 5, "w2": [0.0] * 5 + [0.5] * 5}
    at_95 = stratified_bootstrap_value(cells, seed=a.seed, alpha=0.05, resamples=B)
    at_family = stratified_bootstrap_value(cells, seed=a.seed, alpha=0.05 / 16, resamples=B)
    assert (a.low, a.high) == (at_95.low, at_95.high)
    assert (at_family.low, at_family.high) != (at_95.low, at_95.high)


def test_a_positive_gap_whose_interval_includes_zero_is_a_tie() -> None:
    # S2, company 0.5 / 0.5. A run at (1, 0) is 0.5 away, a run at (0.5, 0.5) is 0.
    # A: per wording one of each, 0.25. B: per wording one at 0 and two at 0.5, 1/3. Gap 0.0833 > 0, but
    # each side's resamples overlap widely, so the gap's interval includes zero.
    company = CompanyDecision("primary", {"cut_rnd": 1, "raise_prices": 1}, None)
    rows = []
    for w in ("w1", "w2"):
        rows += [s2("A", w, cut_rnd=1, raise_prices=1), s2("A", w, cut_rnd=1)]
        rows += [
            s2("B", w, cut_rnd=1, raise_prices=1),
            s2("B", w, cut_rnd=1),
            s2("B", w, raise_prices=1),
        ]
    m = match(rows, company, objectives="AB", scenario=S2).readings[0]
    assert m.gap is not None
    assert m.gap.estimate == pytest.approx(1 / 3 - 0.25)
    assert m.gap.low < 0 < m.gap.estimate
    assert (m.label, m.nearest, m.tied_with) == ("tie", "A", "B")
