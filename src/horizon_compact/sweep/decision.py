"""Validate one tool input against the scenario (Phase 1 IMPLEMENTATION doc section 6.3, planning/07 section
2.4).

One implementation for every model. Failures are listed, never raised: a bad decision is a recorded result.
The raw amounts are always kept; a rescaled run (both sides within 1% of the total) keeps the scaled amounts
beside them, so a line carried slightly over its cap stays visible.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Literal

from horizon_compact.experiment import Scenario

ValidationStatus = Literal["valid", "valid_rescaled", "schema_invalid", "sum_mismatch"]
# Dollar amounts are compared to the cent: floating point can leave 1,500.0000000002.
_CENT = 0.005


@dataclass(frozen=True)
class Validation:
    status: ValidationStatus
    problems: tuple[str, ...] = ()
    amounts: dict[str, float] = field(default_factory=dict)
    scaled_amounts: dict[str, float] | None = None
    season: str | None = None
    memo_words: int | None = None

    @property
    def ok(self) -> bool:
        return self.status in ("valid", "valid_rescaled")

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "problems": list(self.problems),
            "amounts": self.amounts,
            "scaled_amounts": self.scaled_amounts,
            "season": self.season,
            "memo_words": self.memo_words,
        }


def _is_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _scale(amounts: dict[str, float], keys: list[str], total: float, target: float) -> None:
    factor = target / total
    for key in keys:
        amounts[key] = round(amounts[key] * factor, 2)


def validate_decision(scenario: Scenario, tool_input: object) -> Validation:
    choice_key = scenario.choice.key
    if not isinstance(tool_input, dict) or set(tool_input) != {"amounts", choice_key, "memo"}:
        found = sorted(tool_input) if isinstance(tool_input, dict) else type(tool_input).__name__
        return Validation(
            "schema_invalid",
            (f"expected exactly amounts, {choice_key} and memo; found {found}",),
        )

    problems: list[str] = []
    offered = {lever.key: lever for lever in scenario.offered()}
    raw_amounts = tool_input["amounts"]
    amounts: dict[str, float] = {}
    if not isinstance(raw_amounts, dict):
        return Validation("schema_invalid", ("amounts is not an object",))
    if set(raw_amounts) != set(offered):
        missing = sorted(set(offered) - set(raw_amounts))
        extra = sorted(set(raw_amounts) - set(offered))
        problems.append(
            f"amounts keys differ from the offered lines (missing {missing}, extra {extra})"
        )
    for key, value in raw_amounts.items():
        if not _is_number(value) or not math.isfinite(value) or value < 0:
            problems.append(f"amounts.{key} is not a finite non-negative number")
        elif key in offered:
            amounts[key] = float(value)
            if value > offered[key].cap:
                problems.append(f"amounts.{key} is {value}, above its maximum {offered[key].cap}")

    season = tool_input[choice_key]
    if season not in {option.key for option in scenario.choice.options}:
        problems.append(f"{choice_key} is not one of the offered options")
    memo = tool_input["memo"]
    memo_words: int | None = None
    if not isinstance(memo, str) or not memo.strip():
        problems.append("memo is not a non-empty string")
    else:
        memo_words = len(memo.split())

    shown_season = season if isinstance(season, str) else None
    if problems:
        return Validation(
            "schema_invalid", tuple(problems), amounts, None, shown_season, memo_words
        )

    sources = [lever.key for lever in scenario.offered("source")]
    uses = [lever.key for lever in scenario.offered("use")]
    total = float(scenario.total)
    source_sum = sum(amounts[key] for key in sources)
    use_sum = sum(amounts[key] for key in uses)
    tolerance = scenario.tolerance_fraction * total

    if abs(source_sum - total) <= _CENT and abs(use_sum - total) <= _CENT:
        return Validation("valid", (), amounts, None, shown_season, memo_words)
    if abs(source_sum - total) <= tolerance and abs(use_sum - total) <= tolerance:
        scaled = dict(amounts)
        _scale(scaled, sources, source_sum, total)
        _scale(scaled, uses, use_sum, total)
        return Validation("valid_rescaled", (), amounts, scaled, shown_season, memo_words)
    return Validation(
        "sum_mismatch",
        (f"sources total {source_sum:g} and uses total {use_sum:g}, against {total:g}",),
        amounts,
        None,
        shown_season,
        memo_words,
    )
