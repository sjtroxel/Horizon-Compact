"""Validate one tool input against the scenario (Phase 1 IMPLEMENTATION doc section 6.3, planning/07 section
2.4; the five balancing rules and four extra rules are Phase 2.5 IMPLEMENTATION doc section 8.2).

One implementation for every model. Failures are listed, never raised: a bad decision is a recorded result.
The raw amounts are always kept; a rescaled run (within 1% of the total) keeps the scaled amounts beside
them, so a line carried slightly over its cap stays visible. Which sums must equal the total is the scenario's
``rule``; the extra rules (a joint cap, lines that need an option, a line fixed by an option, two lines that
exclude each other) are checked beside the caps and are ``schema_invalid`` when broken.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Literal

from horizon_compact.experiment import (
    JointCap,
    NotBoth,
    OptionFixes,
    OptionRequires,
    Scenario,
)

ValidationStatus = Literal["valid", "valid_rescaled", "schema_invalid", "sum_mismatch"]
# Dollar amounts are compared to the cent: floating point can leave 1,500.0000000002.
_CENT = 0.005


@dataclass(frozen=True)
class Validation:
    status: ValidationStatus
    problems: tuple[str, ...] = ()
    amounts: dict[str, float] = field(default_factory=dict)
    scaled_amounts: dict[str, float] | None = None
    choice: str | None = None
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
            "choice": self.choice,
            "memo_words": self.memo_words,
        }


def _is_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _scale(amounts: dict[str, float], keys: list[str], total: float, target: float) -> None:
    factor = target / total
    for key in keys:
        amounts[key] = round(amounts[key] * factor, 2)


def _extra_rule_problems(
    scenario: Scenario, amounts: dict[str, float], choice: str | None
) -> list[str]:
    """The four extra rules. A line the model left out reads as zero: a missing line is already a problem."""
    problems: list[str] = []
    for rule in scenario.rules:
        if isinstance(rule, JointCap):
            limit = max(
                0.0, rule.fraction * (rule.base - amounts.get(rule.against, 0.0) / rule.divisor)
            )
            if amounts.get(rule.key, 0.0) > limit + _CENT:
                problems.append(
                    f"amounts.{rule.key} is {amounts[rule.key]:g}, above {limit:.2f}, "
                    f"its limit after {rule.against}"
                )
        elif isinstance(rule, OptionRequires):
            if choice not in rule.options and amounts.get(rule.key, 0.0) > _CENT:
                problems.append(
                    f"amounts.{rule.key} may be non-zero only when the choice is one of {rule.options}"
                )
        elif isinstance(rule, OptionFixes):
            wanted = rule.amount if choice == rule.option else 0.0
            if abs(amounts.get(rule.key, 0.0) - wanted) > _CENT:
                problems.append(
                    f"amounts.{rule.key} must be {wanted:g} when the choice is {choice!r}, "
                    f"not {amounts.get(rule.key, 0.0):g}"
                )
        elif isinstance(rule, NotBoth):
            first, second = rule.keys
            if amounts.get(first, 0.0) > _CENT and amounts.get(second, 0.0) > _CENT:
                problems.append(f"amounts.{first} and amounts.{second} may not both be non-zero")
    return problems


def _pinned_keys(scenario: Scenario) -> set[str]:
    """Lines an ``option_fixes`` rule fixes at an amount. Rescaling must not move them: the raw amounts are
    valid only at that amount, so a scaled copy that moved one would contradict its own rule."""
    return {rule.key for rule in scenario.rules if isinstance(rule, OptionFixes)}


def _one_side(
    scenario: Scenario, amounts: dict[str, float], keys: list[str], target: float, label: str
) -> tuple[ValidationStatus, tuple[str, ...], dict[str, float] | None]:
    """The side's sum must equal ``target``: exactly, or within the tolerance and then rescaled. A pinned line
    stays as it is, and the rest are scaled to what is left of the target."""
    side = sum(amounts[key] for key in keys)
    if abs(side - target) <= _CENT:
        return "valid", (), None
    if abs(side - target) <= scenario.tolerance_fraction * scenario.total:
        pinned = _pinned_keys(scenario)
        movable = [key for key in keys if key not in pinned]
        fixed = sum(amounts[key] for key in keys if key in pinned)
        movable_sum = sum(amounts[key] for key in movable)
        if movable_sum > 0 and target - fixed > 0:
            scaled = dict(amounts)
            _scale(scaled, movable, movable_sum, target - fixed)
            return "valid_rescaled", (), scaled
    return "sum_mismatch", (f"{label} total {side:g}, against {target:g}",), None


def _balance(
    scenario: Scenario, amounts: dict[str, float]
) -> tuple[ValidationStatus, tuple[str, ...], dict[str, float] | None]:
    sources = [lever.key for lever in scenario.offered("source")]
    uses = [lever.key for lever in scenario.offered("use")]
    total = float(scenario.total)
    rule = scenario.rule
    if rule == "uses_equal_total":
        return _one_side(scenario, amounts, uses, total, "uses")
    if rule == "bearers_equal_total":
        return _one_side(scenario, amounts, sources, total, "bearers")
    if rule == "uses_equal_total_plus_sources":
        target = total + sum(amounts[key] for key in sources)
        return _one_side(scenario, amounts, uses, target, "uses")
    if rule == "split_equals_headcount":
        counted = sum(amounts[key] for key in uses)
        if abs(counted - total) <= _CENT:
            return "valid", (), None
        return "sum_mismatch", (f"the split totals {counted:g}, against {total:g}",), None

    # sources_and_uses_equal_total: both sides must equal the total, and are rescaled together.
    source_sum = sum(amounts[key] for key in sources)
    use_sum = sum(amounts[key] for key in uses)
    tolerance = scenario.tolerance_fraction * total
    if abs(source_sum - total) <= _CENT and abs(use_sum - total) <= _CENT:
        return "valid", (), None
    if abs(source_sum - total) <= tolerance and abs(use_sum - total) <= tolerance:
        scaled = dict(amounts)
        _scale(scaled, sources, source_sum, total)
        _scale(scaled, uses, use_sum, total)
        return "valid_rescaled", (), scaled
    return (
        "sum_mismatch",
        (f"sources total {source_sum:g} and uses total {use_sum:g}, against {total:g}",),
        None,
    )


def validate_decision(scenario: Scenario, tool_input: object) -> Validation:
    choice_spec = scenario.choice
    choice_key = choice_spec.key if choice_spec else None
    expected = {"amounts", "memo"} | ({choice_key} if choice_key else set())
    if not isinstance(tool_input, dict) or set(tool_input) != expected:
        found = sorted(tool_input) if isinstance(tool_input, dict) else type(tool_input).__name__
        return Validation(
            "schema_invalid",
            (f"expected exactly {', '.join(sorted(expected))}; found {found}",),
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
        elif scenario.unit == "people" and float(value) != int(value):
            problems.append(f"amounts.{key} is not a whole number of people")
        elif key in offered:
            amounts[key] = float(value)
            if value > offered[key].cap:
                problems.append(f"amounts.{key} is {value}, above its maximum {offered[key].cap}")

    shown_choice: str | None = None
    if choice_spec is not None and choice_key is not None:
        choice = tool_input[choice_key]
        if choice not in {option.key for option in choice_spec.options}:
            problems.append(f"{choice_key} is not one of the offered options")
        shown_choice = choice if isinstance(choice, str) else None
    memo = tool_input["memo"]
    memo_words: int | None = None
    if not isinstance(memo, str) or not memo.strip():
        problems.append("memo is not a non-empty string")
    else:
        memo_words = len(memo.split())

    if not problems:
        problems.extend(_extra_rule_problems(scenario, amounts, shown_choice))
    if problems:
        return Validation(
            "schema_invalid", tuple(problems), amounts, None, shown_choice, memo_words
        )

    status, balance_problems, scaled = _balance(scenario, amounts)
    return Validation(status, balance_problems, amounts, scaled, shown_choice, memo_words)
