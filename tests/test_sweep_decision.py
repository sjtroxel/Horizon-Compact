"""Validation, one rule at a time (Phase 1 IMPLEMENTATION doc section 6.3)."""

from __future__ import annotations

from typing import Any

import pytest

from horizon_compact.sweep.decision import validate_decision
from sweep_helpers import VALID_AMOUNTS, experiment, valid_input

SCENARIO = experiment().scenario


def check(data: Any) -> Any:
    return validate_decision(SCENARIO, data)


def amounts(**changes: Any) -> dict[str, Any]:
    out = dict(VALID_AMOUNTS)
    out.update(changes)
    return out


def test_an_exactly_balanced_decision_is_valid() -> None:
    result = check(valid_input())
    assert result.status == "valid"
    assert result.problems == ()
    assert result.scaled_amounts is None
    assert result.season == "spring"
    assert result.memo_words == 160


def test_cents_that_float_arithmetic_leaves_behind_are_still_exact() -> None:
    result = check(valid_input(amounts=amounts(raffle=199.99999999, herbs=500.00000001)))
    assert result.status == "valid"


def test_both_sides_inside_one_percent_are_rescaled_and_both_sets_are_kept() -> None:
    raw = amounts(yearly_fund=1000, plant_sale=300, raffle=190)  # sources 1,490, uses 1,500
    result = check(valid_input(amounts=raw))
    assert result.status == "valid_rescaled"
    assert result.amounts == {k: float(v) for k, v in raw.items()}
    assert result.scaled_amounts is not None
    sources = ("yearly_fund", "plant_sale", "raffle")
    assert sum(result.scaled_amounts[k] for k in sources) == pytest.approx(1500, abs=0.05)
    assert result.scaled_amounts["bulbs"] == 700  # the side that balanced is untouched


def test_a_side_outside_one_percent_is_a_sum_mismatch() -> None:
    result = check(valid_input(amounts=amounts(raffle=100)))  # sources 1,400
    assert result.status == "sum_mismatch"
    assert "sources total 1400" in result.problems[0]


def test_one_percent_is_inclusive_at_fifteen_dollars() -> None:
    assert check(valid_input(amounts=amounts(raffle=185))).status == "valid_rescaled"
    assert check(valid_input(amounts=amounts(raffle=184))).status == "sum_mismatch"


def test_an_amount_above_its_cap_is_schema_invalid_on_the_amounts_as_given() -> None:
    result = check(valid_input(amounts=amounts(raffle=301, herbs=499)))
    assert result.status == "schema_invalid"
    assert any("raffle" in p and "above its maximum 300" in p for p in result.problems)


def test_a_boolean_is_not_a_number() -> None:
    result = check(valid_input(amounts=amounts(bulbs=True)))
    assert result.status == "schema_invalid"
    assert any("bulbs" in p for p in result.problems)


@pytest.mark.parametrize("bad", [-1, float("nan"), float("inf"), "700", None])
def test_negative_non_finite_and_non_numeric_amounts_are_schema_invalid(bad: Any) -> None:
    assert check(valid_input(amounts=amounts(bulbs=bad))).status == "schema_invalid"


def test_an_extra_key_a_missing_key_and_the_not_offered_lever_are_schema_invalid() -> None:
    extra = check(valid_input(amounts=amounts(extra=5)))
    assert extra.status == "schema_invalid"
    assert "extra ['extra']" in extra.problems[0]
    missing_amounts = amounts()
    del missing_amounts["herbs"]
    assert "missing ['herbs']" in check(valid_input(amounts=missing_amounts)).problems[0]
    assert check(valid_input(amounts=amounts(tool_shed=0))).status == "schema_invalid"


def test_the_top_level_must_be_exactly_the_three_fields() -> None:
    data = valid_input()
    del data["memo"]
    assert check(data).status == "schema_invalid"
    assert check({**valid_input(), "extra": 1}).status == "schema_invalid"
    assert check("not an object").status == "schema_invalid"
    assert check(None).status == "schema_invalid"


def test_the_season_must_be_one_of_the_two_options() -> None:
    assert check(valid_input(open_day_season="winter")).status == "schema_invalid"
    assert check(valid_input(open_day_season="autumn")).status == "valid"


@pytest.mark.parametrize("memo", ["", "   ", 5, None])
def test_the_memo_must_be_a_non_empty_string(memo: Any) -> None:
    assert check(valid_input(memo=memo)).status == "schema_invalid"


def test_the_memo_length_is_recorded_never_enforced() -> None:
    assert check(valid_input(memo="short")).memo_words == 1
    assert check(valid_input(memo="short")).status == "valid"
    assert check(valid_input(memo=" ".join(["w"] * 900))).status == "valid"


def test_as_dict_is_json_ready() -> None:
    import json

    assert json.dumps(check(valid_input()).as_dict())
