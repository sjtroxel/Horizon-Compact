"""The five balancing rules and the four extra rules (Phase 2.5 IMPLEMENTATION doc section 8.2).

Every scenario here is invented and fictional. The total is 1,000 (190 people for the split), so one
percent is 10: a side 10 off is rescaled, a side 11 off is a mismatch.
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from horizon_compact.experiment import Scenario
from horizon_compact.sweep.decision import Validation, validate_decision
from sweep_helpers import lever, scenario

MEMO = " ".join(["word"] * 160)


def decide(
    scn: Scenario, amounts: dict[str, Any], choice: str | None = None, **top: Any
) -> Validation:
    data: dict[str, Any] = {"amounts": amounts, "memo": MEMO}
    if scn.choice is not None:
        data[scn.choice.key] = choice
    data.update(top)
    return validate_decision(scn, data)


# --- sources_and_uses_equal_total (the placeholder's rule) ----------------------------------------

SOURCES_USES = scenario(
    "sources_and_uses_equal_total",
    [lever("s1", "source"), lever("s2", "source"), lever("u1", "use"), lever("u2", "use")],
)


@pytest.mark.parametrize(
    ("s1", "u1", "status"),
    [(600, 600, "valid"), (590, 600, "valid_rescaled"), (589, 600, "sum_mismatch")],
)
def test_sources_and_uses_both_sides_must_reach_the_total(s1: int, u1: int, status: str) -> None:
    result = decide(SOURCES_USES, {"s1": s1, "s2": 400, "u1": u1, "u2": 400})
    assert result.status == status


# --- uses_equal_total (S1: the freed amount is spent, and what is not kept is released) -----------

USES_ONLY = scenario(
    "uses_equal_total",
    [lever("keep", "use"), lever("fund", "use"), lever("roles", "not_offered", 0)],
)


@pytest.mark.parametrize(
    ("fund", "status"), [(600, "valid"), (610, "valid_rescaled"), (589, "sum_mismatch")]
)
def test_the_uses_alone_must_equal_the_total(fund: int, status: str) -> None:
    result = decide(USES_ONLY, {"keep": 400, "fund": fund})
    assert result.status == status
    if status == "valid_rescaled":
        assert result.scaled_amounts is not None
        assert sum(result.scaled_amounts.values()) == pytest.approx(1000, abs=0.05)
    if status == "sum_mismatch":
        assert "uses total 989" in result.problems[0]


def test_uses_equal_total_refuses_a_scenario_that_has_sources() -> None:
    with pytest.raises(ValidationError, match="takes uses only"):
        scenario("uses_equal_total", [lever("a", "use"), lever("b", "source")])


# --- bearers_equal_total (S2: who bears a fixed shortfall) ----------------------------------------

BEARERS = scenario(
    "bearers_equal_total",
    [
        lever("a", "source"),
        lever("b", "source"),
        lever("c", "source"),
        lever("pay", "not_offered", 0),
    ],
)


@pytest.mark.parametrize(
    ("c", "status"),
    [(500, "valid"), (490, "valid_rescaled"), (510, "valid_rescaled"), (511, "sum_mismatch")],
)
def test_the_bearers_must_cover_the_shortfall(c: int, status: str) -> None:
    result = decide(BEARERS, {"a": 300, "b": 200, "c": c})
    assert result.status == status
    if status == "sum_mismatch":
        assert "bearers total 1011" in result.problems[0]


def test_bearers_equal_total_refuses_a_scenario_that_has_uses() -> None:
    with pytest.raises(ValidationError, match="takes sources only"):
        scenario("bearers_equal_total", [lever("a", "source"), lever("b", "use")])


# --- uses_equal_total_plus_sources (S4: the cash, plus whatever is cut) ---------------------------

PLUS_SOURCES = scenario(
    "uses_equal_total_plus_sources",
    [lever("cut", "source", 200), lever("keep", "use"), lever("spend", "use")],
)


@pytest.mark.parametrize(
    ("spend", "status"), [(700, "valid"), (710, "valid_rescaled"), (711, "sum_mismatch")]
)
def test_the_uses_equal_the_total_plus_what_was_cut(spend: int, status: str) -> None:
    # 150 is cut, so the uses must reach 1,150: 450 + 700.
    result = decide(PLUS_SOURCES, {"cut": 150, "keep": 450, "spend": spend})
    assert result.status == status


def test_with_nothing_cut_the_uses_equal_the_total() -> None:
    assert decide(PLUS_SOURCES, {"cut": 0, "keep": 400, "spend": 600}).status == "valid"
    assert decide(PLUS_SOURCES, {"cut": 0, "keep": 400, "spend": 700}).status == "sum_mismatch"


def test_rescaling_leaves_the_sources_alone() -> None:
    result = decide(PLUS_SOURCES, {"cut": 150, "keep": 450, "spend": 710})
    assert result.scaled_amounts is not None
    assert result.scaled_amounts["cut"] == 150
    assert result.scaled_amounts["keep"] + result.scaled_amounts["spend"] == pytest.approx(
        1150, abs=0.05
    )


# --- split_equals_headcount (S3: people, whole numbers, exact) ------------------------------------

SPLIT = scenario(
    "split_equals_headcount",
    [
        lever("out", "use", 190),
        lever("moved", "use", 190),
        lever("kept", "use", 190),
        lever("sold", "use", 190),
    ],
    total=190,
    unit="people",
    options_heading="o",
    choice={
        "key": "plan",
        "label": "p",
        "options": [
            {"key": "close", "text": "c"},
            {"key": "retool", "text": "r"},
            {"key": "sell", "text": "s"},
        ],
    },
    rules=[
        {"kind": "option_requires", "key": "kept", "options": ["retool"]},
        {"kind": "option_requires", "key": "sold", "options": ["sell"]},
    ],
)


def test_a_split_of_exactly_the_headcount_is_valid() -> None:
    assert decide(SPLIT, {"out": 150, "moved": 40, "kept": 0, "sold": 0}, "close").status == "valid"


def test_a_split_is_never_rescaled_so_one_person_off_is_a_mismatch() -> None:
    result = decide(SPLIT, {"out": 150, "moved": 39, "kept": 0, "sold": 0}, "close")
    assert result.status == "sum_mismatch"
    assert "the split totals 189, against 190" in result.problems[0]
    assert result.scaled_amounts is None


def test_a_fraction_of_a_person_is_schema_invalid() -> None:
    result = decide(SPLIT, {"out": 150.5, "moved": 39.5, "kept": 0, "sold": 0}, "close")
    assert result.status == "schema_invalid"
    assert "whole number of people" in result.problems[0]


def test_a_line_that_needs_an_option_is_refused_under_the_others() -> None:
    assert (
        decide(SPLIT, {"out": 100, "moved": 40, "kept": 50, "sold": 0}, "retool").status == "valid"
    )
    refused = decide(SPLIT, {"out": 100, "moved": 40, "kept": 50, "sold": 0}, "close")
    assert refused.status == "schema_invalid"
    assert "'kept'" not in refused.problems[0]
    assert (
        "amounts.kept may be non-zero only when the choice is one of ['retool']" in refused.problems
    )
    assert decide(SPLIT, {"out": 100, "moved": 40, "kept": 0, "sold": 50}, "sell").status == "valid"
    assert (
        decide(SPLIT, {"out": 100, "moved": 40, "kept": 0, "sold": 50}, "retool").status
        == "schema_invalid"
    )


def test_split_equals_headcount_must_count_people() -> None:
    with pytest.raises(ValidationError, match="counts people"):
        scenario("split_equals_headcount", [lever("a", "use")], total=10)


# --- the extra rules ------------------------------------------------------------------------------

FUND = scenario(
    "uses_equal_total_plus_sources",
    [
        lever("cut_rd", "source", 100),
        lever("cut_roles", "source", 200),
        lever("program", "use", 600),
        lever("add_rd", "use", 400),
        lever("payout", "use", 1000),
    ],
    options_heading="o",
    choice={
        "key": "program_choice",
        "label": "p",
        "options": [{"key": "fund", "text": "f"}, {"key": "decline", "text": "d"}],
    },
    rules=[
        {"kind": "option_fixes", "key": "program", "option": "fund", "amount": 600},
        {"kind": "not_both", "keys": ["cut_rd", "add_rd"]},
    ],
)


def test_a_line_fixed_by_an_option_must_equal_its_amount_or_zero() -> None:
    funded = {"cut_rd": 0, "cut_roles": 0, "program": 600, "add_rd": 0, "payout": 400}
    assert decide(FUND, funded, "fund").status == "valid"
    assert (
        decide(FUND, {**funded, "program": 500, "payout": 500}, "fund").status == "schema_invalid"
    )
    declined = {"cut_rd": 0, "cut_roles": 0, "program": 0, "add_rd": 0, "payout": 1000}
    assert decide(FUND, declined, "decline").status == "valid"
    assert (
        decide(FUND, {**declined, "program": 600, "payout": 400}, "decline").status
        == "schema_invalid"
    )


def test_two_lines_that_exclude_each_other_cannot_both_be_used() -> None:
    both = {"cut_rd": 50, "cut_roles": 0, "program": 600, "add_rd": 50, "payout": 400}
    result = decide(FUND, both, "fund")
    assert result.status == "schema_invalid"
    assert "amounts.cut_rd and amounts.add_rd may not both be non-zero" in result.problems
    one = {"cut_rd": 50, "cut_roles": 0, "program": 600, "add_rd": 0, "payout": 450}
    assert decide(FUND, one, "fund").status == "valid"


# The wage cut applies to the payroll that remains after roles are eliminated, and roles are counted at
# employment cost: with base 800, divisor 1.25 and fraction 0.1, wages may reach 0.1 x (800 - roles / 1.25).
JOINT = scenario(
    "bearers_equal_total",
    [
        lever("roles", "source", 1000),
        lever("wages", "source", 1000),
        lever("profit", "source", 1000),
    ],
    rules=[
        {
            "kind": "joint_cap",
            "key": "wages",
            "against": "roles",
            "base": 800,
            "divisor": 1.25,
            "fraction": 0.1,
        }
    ],
)


@pytest.mark.parametrize(
    ("roles", "wages", "ok"),
    [
        (0, 80, True),  # 0.1 x 800
        (0, 81, False),
        (500, 40, True),  # 0.1 x (800 - 400)
        (500, 41, False),
        (1000, 0, True),  # 0.1 x (800 - 800)
        (1000, 1, False),
        (1000, 0.004, True),  # inside a cent
    ],
)
def test_a_joint_cap_follows_what_is_left_after_the_other_line(
    roles: int, wages: float, ok: bool
) -> None:
    profit = max(0.0, 1000 - roles - wages)  # a negative remainder would be its own error
    result = decide(JOINT, {"roles": roles, "wages": wages, "profit": profit})
    assert (result.status in ("valid", "valid_rescaled")) is ok
    if not ok:
        assert result.status == "schema_invalid"
        assert "its limit after roles" in result.problems[0]


# --- the rules must name real things --------------------------------------------------------------


def test_an_extra_rule_naming_a_line_that_is_not_offered_is_rejected() -> None:
    with pytest.raises(ValidationError, match="'ghost', which is not an offered line"):
        scenario(
            "bearers_equal_total",
            [lever("a", "source")],
            rules=[{"kind": "not_both", "keys": ["a", "ghost"]}],
        )


def test_an_option_rule_needs_a_scenario_with_a_choice() -> None:
    with pytest.raises(ValidationError, match="needs a scenario with a choice"):
        scenario(
            "bearers_equal_total",
            [lever("a", "source")],
            rules=[{"kind": "option_requires", "key": "a", "options": ["x"]}],
        )


def test_an_option_rule_naming_an_option_that_does_not_exist_is_rejected() -> None:
    with pytest.raises(ValidationError, match="option 'nope', which is not offered"):
        scenario(
            "bearers_equal_total",
            [lever("a", "source")],
            options_heading="o",
            choice={
                "key": "c",
                "label": "c",
                "options": [{"key": "x", "text": "x"}, {"key": "y", "text": "y"}],
            },
            rules=[{"kind": "option_fixes", "key": "a", "option": "nope", "amount": 1}],
        )


def test_a_choice_needs_an_options_heading_and_no_choice_means_none() -> None:
    options = [{"key": "x", "text": "x"}, {"key": "y", "text": "y"}]
    with pytest.raises(ValidationError, match="needs options_heading"):
        scenario(
            "bearers_equal_total",
            [lever("a", "source")],
            choice={"key": "c", "label": "c", "options": options},
        )
    with pytest.raises(ValidationError, match="options_heading is for a scenario with a choice"):
        scenario("bearers_equal_total", [lever("a", "source")], options_heading="o")


def test_a_scenario_without_a_choice_wants_exactly_amounts_and_memo() -> None:
    ok = validate_decision(BEARERS, {"amounts": {"a": 300, "b": 200, "c": 500}, "memo": MEMO})
    assert ok.status == "valid"
    assert ok.choice is None
    extra = validate_decision(
        BEARERS, {"amounts": {"a": 300, "b": 200, "c": 500}, "memo": MEMO, "plan": "x"}
    )
    assert extra.status == "schema_invalid"
