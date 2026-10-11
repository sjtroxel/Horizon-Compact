"""Section 7: the options plausibly open, and the equal-treatment rule (IMPLEMENTATION §4.9).

The options are those of the case's scenario shape (protocol §12.5), in the shape's fixed order, and **what
each is called comes from the shape, never from the filings.** Each option may carry figures, but only from
documents the cut-off filter admits: a figure whose source was filed on or after the cut-off raises, it is
never quietly dropped. **If any option has no admitted figure, every option is described without figures
alike** (protocol §12.6), so the option the company chose is never the best-described one, and the record says
that it did.

``tests/test_casebuild_options.py`` checks these keys, in this order, against the fictional company's scenario
files, so the shape's options cannot drift from the instrument.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any

from horizon_compact.casebuild.cutoff import FilingStamp, admit


class OptionsError(Exception):
    """An option figure is not from an admitted document, or names an option the shape does not have."""


@dataclass(frozen=True)
class OptionSpec:
    key: str
    label: str


SHAPE_OPTIONS: dict[str, tuple[OptionSpec, ...]] = {
    "S1": (
        OptionSpec("eliminate", "Role eliminated, with severance"),
        OptionSpec(
            "move_plant_pay", "Retrained and moved to a plant role, at the plant role's pay"
        ),
        OptionSpec("move_keep_pay", "Retrained and moved to a plant role, keeping current pay"),
    ),
    "S2": (
        OptionSpec("eliminate_roles", "Eliminating roles, borne by the workforce"),
        OptionSpec("cut_wages_hours", "Cutting wages or hours, borne by the workforce"),
        OptionSpec(
            "cut_rnd",
            "Cutting research and development, borne by the Company's future products and its engineering staff",
        ),
        OptionSpec(
            "cut_env_projects",
            "Cutting environmental projects, borne by the environment and the communities near the plants",
        ),
        OptionSpec("raise_prices", "Raising prices, borne by customers"),
        OptionSpec("suppliers", "Negotiating lower prices with suppliers, borne by suppliers"),
        OptionSpec("lower_profit", "Accepting lower operating income, borne by shareholders"),
        OptionSpec("payouts", "Changing dividends and share repurchases"),
        OptionSpec("keep_people", "Keeping people in their roles"),
    ),
    "S3": (
        OptionSpec(
            "close", "Close the facility and move its product family to the other facilities"
        ),
        OptionSpec("retool", "Retool the facility"),
        OptionSpec(
            "sell",
            "Sell the facility, with its product family, to a buyer that will keep running it",
        ),
    ),
    "S4": (
        OptionSpec("fund", "Fund the program"),
        OptionSpec("decline", "Decline the program"),
    ),
}


@dataclass(frozen=True)
class OptionFigure:
    statement: str  # for example "capital cost of $30.0 million, once"
    source: FilingStamp  # the filing it came from


@dataclass(frozen=True)
class OptionsSection:
    text: str
    figures_stripped: bool
    record: Mapping[str, Any]


def build_options_section(
    shape: str, figures: Mapping[str, Sequence[OptionFigure]], cutoff: date
) -> OptionsSection:
    if shape not in SHAPE_OPTIONS:
        raise OptionsError(f"unknown scenario shape {shape!r}")
    specs = SHAPE_OPTIONS[shape]
    unknown = sorted(set(figures) - {spec.key for spec in specs})
    if unknown:
        raise OptionsError(f"shape {shape} has no option(s) {', '.join(unknown)}")
    for key, items in figures.items():
        for item in items:
            if not admit(item.source, cutoff):
                raise OptionsError(
                    f"a figure for option {key} comes from filing {item.source.label or '(unlabelled)'}, "
                    "which is not before the cut-off"
                )
    stripped = any(not figures.get(spec.key) for spec in specs)
    lines = ["The options plausibly open to the Company:", ""]
    for number, spec in enumerate(specs, start=1):
        lines.append(f"{number}. {spec.label}")
        if not stripped:
            lines.extend(f"   {item.statement}" for item in figures[spec.key])
    text = "\n".join(lines)
    record = {
        "shape": shape,
        "options": [spec.key for spec in specs],
        "figures_stripped": stripped,
        "figure_counts": {spec.key: len(figures.get(spec.key, ())) for spec in specs},
        "sources": sorted({item.source.label for items in figures.values() for item in items}),
    }
    return OptionsSection(text=text, figures_stripped=stripped, record=record)
