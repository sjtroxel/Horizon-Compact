"""Section 7: the options of the case's shape and the equal-treatment rule (build step 5, §4.9)."""

from __future__ import annotations

import tomllib
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from horizon_compact.casebuild.cutoff import FilingStamp
from horizon_compact.casebuild.options import (
    NUMBER_WORDS,
    SHAPE_OPTIONS,
    OptionFigure,
    OptionsError,
    build_options_section,
)

ROOT = Path(__file__).resolve().parents[1]
CUTOFF = date(2026, 6, 15)
EARLY = FilingStamp(filed=date(2026, 5, 8), label="0009999999-26-000002")


def _scenario(name: str) -> dict[str, Any]:
    return tomllib.loads(
        (ROOT / "experiment" / "company" / "scenarios" / f"{name}.toml").read_text()
    )


@pytest.mark.parametrize("shape", ["S1", "S2"])
def test_s1_and_s2_options_are_the_instruments_levers_in_order_with_their_labels(
    shape: str,
) -> None:
    levers = _scenario(shape.lower())["levers"]
    assert [(o.key, o.label) for o in SHAPE_OPTIONS[shape]] == [
        (lv["key"], lv["label"]) for lv in levers
    ]


@pytest.mark.parametrize("shape", ["S3", "S4"])
def test_s3_and_s4_options_are_the_instruments_choice_options_in_order(shape: str) -> None:
    options = _scenario(shape.lower())["choice"]["options"]
    assert [o.key for o in SHAPE_OPTIONS[shape]] == [o["key"] for o in options]


def test_options_are_named_from_the_shape_with_their_admitted_figures() -> None:
    figures = {
        "close": [OptionFigure("one-time cost of $20.0 million", EARLY)],
        "retool": [OptionFigure("capital cost of $30.0 million, once", EARLY)],
        "sell": [OptionFigure("proceeds of $12.0 million", EARLY)],
    }
    section = build_options_section("S3", figures, CUTOFF)
    assert not section.figures_stripped
    assert section.text.splitlines() == [
        "The options plausibly open to the Company:",
        "",
        "Option one: Close the facility and move its product family to the other facilities",
        "   one-time cost of $20.0 million",
        "Option two: Retool the facility",
        "   capital cost of $30.0 million, once",
        "Option three: Sell the facility, with its product family, to a buyer that will keep running it",
        "   proceeds of $12.0 million",
    ]
    assert section.record["figure_counts"] == {"close": 1, "retool": 1, "sell": 1}


def test_no_shape_numbers_its_options_with_a_digit() -> None:
    """A digit would be an unclassified number to the transform: a flag nobody means (step 6, first run)."""
    for shape, specs in SHAPE_OPTIONS.items():
        assert len(specs) <= len(NUMBER_WORDS)
        assert not any(c.isdigit() for c in build_options_section(shape, {}, CUTOFF).text), shape


def test_if_one_option_has_no_admitted_figure_every_option_is_described_without_figures() -> None:
    figures = {
        "close": [OptionFigure("one-time cost of $20.0 million", EARLY)],
        "retool": [OptionFigure("capital cost of $30.0 million, once", EARLY)],
    }  # "sell" has none
    section = build_options_section("S3", figures, CUTOFF)
    assert section.figures_stripped
    assert "$" not in section.text
    assert section.text.count("\n") == build_options_section("S3", {}, CUTOFF).text.count("\n")
    assert section.record["figures_stripped"] is True
    assert section.record["figure_counts"] == {"close": 1, "retool": 1, "sell": 0}


def test_an_option_with_figures_is_not_better_described_than_one_without() -> None:
    """The option the company chose must never be the best-described one: all or none."""
    only_one = build_options_section(
        "S4", {"fund": [OptionFigure("$20.4 million a year", EARLY)]}, CUTOFF
    )
    assert only_one.text == build_options_section("S4", {}, CUTOFF).text


def test_a_figure_from_a_filing_on_the_cutoff_day_or_after_is_an_error_not_a_quiet_drop() -> None:
    for filed in (date(2026, 6, 15), date(2026, 7, 1)):
        late = FilingStamp(filed=filed, label="0009999999-26-000099")
        with pytest.raises(OptionsError, match="0009999999-26-000099"):
            build_options_section("S4", {"fund": [OptionFigure("$20.4 million", late)]}, CUTOFF)


def test_an_option_the_shape_does_not_have_is_an_error() -> None:
    with pytest.raises(OptionsError, match="no option"):
        build_options_section("S4", {"retool": [OptionFigure("x", EARLY)]}, CUTOFF)


def test_an_unknown_shape_is_an_error() -> None:
    with pytest.raises(OptionsError, match="unknown scenario shape"):
        build_options_section("S9", {}, CUTOFF)


def test_the_record_lists_the_source_filings() -> None:
    section = build_options_section(
        "S4", {"fund": [OptionFigure("a", EARLY)], "decline": [OptionFigure("b", EARLY)]}, CUTOFF
    )
    assert section.record["sources"] == ["0009999999-26-000002"]
