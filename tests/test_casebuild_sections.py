"""The section map applied (Phase 5 code half, build step 4, §4.5)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from edgar_helpers import (
    CANARY_CIK,
    FACTS_URL,
    accession,
    annual,
    archive_url,
    facts_file,
    world,
)
from horizon_compact.casebuild.documents import build_document_set
from horizon_compact.casebuild.sections import (
    HUMAN_CAPITAL,
    HandBoundaries,
    SectionInputs,
    build_section_inputs,
)
from horizon_compact.casebuild.splitter import SplitRefused

CUTOFF = date(2026, 6, 15)
FACTS = json.dumps(
    facts_file(
        {
            "Revenues": [
                annual(2024, 800, "2024-03-04"),
                annual(2025, 900, "2025-03-03"),
                annual(2026, 1000, "2026-03-02"),
            ]
        }
    )
).encode()


def _inputs(
    tmp_path: Path,
    cutoff: date = CUTOFF,
    extra: dict[str, bytes] | None = None,
    hand: HandBoundaries | None = None,
    shape: str = "S3",
) -> SectionInputs:
    client, _ = world(tmp_path, {FACTS_URL: FACTS, **(extra or {})})
    docset = build_document_set(client, CANARY_CIK, cutoff)
    return build_section_inputs(docset, shape=shape, hand=hand)


def _joined(inputs: SectionInputs, number: int) -> str:
    return "\n".join(part.text for part in inputs.parts[number])


def test_sections_1_to_3_come_from_the_annual_report(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    assert "two segments" in _joined(inputs, 1)
    assert "One plant in the Midwest" in _joined(inputs, 2)
    assert "Cages revenue was 900" in _joined(inputs, 2)  # the segment note, found after Item 15
    workforce = _joined(inputs, 3)
    assert "1,240 people" in workforce
    assert "Available Information" not in workforce


def test_section_5_carries_item_7_for_acquisitions_and_the_figures_stand_alone(
    tmp_path: Path,
) -> None:
    inputs = _inputs(tmp_path)
    assert "perch maker" in _joined(inputs, 5)
    assert inputs.parts[4] == []  # section 4 is figures only
    assert inputs.figures.lines["revenue"].by_year[date(2026, 1, 31)].value == 1000


def test_section_6_reads_the_quarterly_report_when_it_is_the_later_one(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    labels = [part.label for part in inputs.parts[6]]
    assert labels[0] == f"quarterly report {accession(2)}, Part I Item 2"
    text = _joined(inputs, 6)
    assert "Quarterly demand fell" in text
    assert "must not be mistaken" not in text
    assert inputs.record["latest_periodic"] == accession(2)


def test_section_6_has_every_admitted_current_report_and_its_exhibits_in_order(
    tmp_path: Path,
) -> None:
    inputs = _inputs(tmp_path)
    texts = [part.text for part in inputs.parts[6][1:]]
    assert texts == [
        "report 4",
        "press release one",
        "press release two",
        "report 5",
        "report 6",
        "closure release",
    ]
    assert inputs.parts[6][1].label == f"8-K {accession(4)} filed 2026-04-10"
    assert inputs.parts[6][2].label.startswith("EX-99 ")


def test_section_6_reads_the_annual_reports_item_7_when_it_is_the_later_one(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path, cutoff=date(2026, 4, 1))
    assert inputs.parts[6][0].label.endswith("Item 7")
    assert "Demand for cages softened" in _joined(inputs, 6)
    assert len(inputs.parts[6]) == 1  # no current report is after the 10-K and before April 1
    assert "quarterly_split" not in inputs.record


def test_section_7_is_left_to_the_scenario_shape(tmp_path: Path) -> None:
    assert 7 not in _inputs(tmp_path).parts


def test_the_record_lists_both_splits_and_the_figures(tmp_path: Path) -> None:
    record = _inputs(tmp_path).record
    assert record["annual_split"]["by_hand"] is False
    assert record["quarterly_split"]["table_of_contents_headings_skipped"] == 8
    assert record["segment_note_found"] is True
    assert record["figures"]["lines"]["revenue"]["tag"] == "Revenues"


def test_a_filing_the_splitter_cannot_split_is_refused_not_guessed(tmp_path: Path) -> None:
    unsplittable = {
        archive_url(1, "canary-10-k-1.htm"): b"<p>Prose with no item headings at all.</p>"
    }
    with pytest.raises(SplitRefused, match="no item headings"):
        _inputs(tmp_path, extra=unsplittable)


def test_hand_boundaries_stand_in_for_a_refused_split_and_are_recorded(tmp_path: Path) -> None:
    lines = [
        "Business section text.",
        "Our Employees",
        "50 people.",
        "Property text.",
        "Results text.",
    ]
    text = "\n".join(lines)  # what html_to_text makes of one paragraph per line

    def span(first: str, last: str) -> tuple[int, int]:
        return text.index(first), text.index(last) + len(last)

    hand = {
        accession(1): {
            "1": span(lines[0], lines[2]),
            "2": span(lines[3], lines[3]),
            "7": span(lines[4], lines[4]),
        }
    }
    prose = "".join(f"<p>{line}</p>" for line in lines)
    inputs = _inputs(
        tmp_path, extra={archive_url(1, "canary-10-k-1.htm"): prose.encode()}, hand=hand
    )
    assert inputs.record["annual_split"]["by_hand"] is True
    assert _joined(inputs, 2) == "Property text."
    assert "50 people." in _joined(inputs, 3)
    assert _joined(inputs, 5) == "Results text."


def test_hand_boundaries_that_lack_a_wanted_item_are_refused(tmp_path: Path) -> None:
    prose = "<p>Business text.</p><p>Property text.</p>"
    hand = {accession(1): {"1": (0, 5), "2": (6, 10)}}  # no Item 7
    with pytest.raises(SplitRefused, match="lack item"):
        _inputs(tmp_path, extra={archive_url(1, "canary-10-k-1.htm"): prose.encode()}, hand=hand)


# --- only the sections the scenario shape needs (protocol §12.6) ------------------------------------------

# An annual report with Items 1 and 7 only: no Item 2, and no human-capital heading in Item 1.
LEAN_10K = (
    "<p><b>Item 1.</b> Business</p><p>We make canary cages.</p>"
    "<p><b>Item 7.</b> Management&#8217;s Discussion and Analysis</p><p>Demand softened.</p>"
)


@pytest.mark.parametrize(
    ("shape", "sections"),
    [
        ("S1", [1, 3, 4, 6]),
        ("S2", [1, 3, 4, 5, 6]),
        ("S3", [1, 2, 3, 4, 5, 6]),
        ("S4", [1, 4, 5, 6]),
    ],
)
def test_only_the_shapes_sections_are_built(
    tmp_path: Path, shape: str, sections: list[int]
) -> None:
    inputs = _inputs(tmp_path, shape=shape)
    assert sorted(inputs.parts) == sections
    assert inputs.record["sections"] == sections
    assert inputs.shape == shape


def test_a_shape_that_needs_no_item_2_or_workforce_is_not_refused_over_them(tmp_path: Path) -> None:
    lean = {archive_url(1, "canary-10-k-1.htm"): LEAN_10K.encode()}
    inputs = _inputs(tmp_path, extra=lean, shape="S4")
    assert "canary cages" in _joined(inputs, 1)
    assert "Demand softened" in _joined(inputs, 5)
    with pytest.raises(SplitRefused, match=r"wanted item\(s\) 2"):
        _inputs(tmp_path / "s3", extra=lean, shape="S3")


def test_item_7_is_wanted_for_section_6_alone_when_the_annual_report_is_the_latest(
    tmp_path: Path,
) -> None:
    """S1 has no section 5, but its section 6 reads Item 7 when no quarterly report came after."""
    no_item_7 = {
        archive_url(1, "canary-10-k-1.htm"): (
            b"<p><b>Item 1.</b> Business</p><p>Cages.</p><p>Our Employees</p><p>50 people.</p>"
        )
    }
    _inputs(tmp_path, extra=no_item_7, shape="S1")  # the 10-Q is later: Item 7 not needed
    with pytest.raises(SplitRefused, match=r"wanted item\(s\) 7"):
        _inputs(tmp_path / "early", cutoff=date(2026, 4, 1), extra=no_item_7, shape="S1")


def test_an_unknown_shape_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown scenario shape"):
        _inputs(tmp_path, shape="S9")


# --- the human-capital part cut by hand, alone ------------------------------------------------------------


def test_the_human_capital_part_can_be_cut_by_hand_while_the_items_split_automatically(
    tmp_path: Path,
) -> None:
    lean = {archive_url(1, "canary-10-k-1.htm"): LEAN_10K.encode()}
    with pytest.raises(SplitRefused, match="human-capital"):
        _inputs(tmp_path, extra=lean, shape="S1")
    text = "Item 1. Business\nWe make canary cages.\nItem 7. Management\u2019s Discussion and Analysis\nDemand softened."
    start = text.index("We make")
    cut = {accession(1): {HUMAN_CAPITAL: (start, start + len("We make canary cages."))}}
    inputs = _inputs(tmp_path / "again", extra=lean, shape="S1", hand=cut)
    assert _joined(inputs, 3) == "We make canary cages."
    assert inputs.record["human_capital_by_hand"] is True
    assert (
        inputs.record["annual_split"]["by_hand"] is False
    )  # the items were still split automatically


def test_a_hand_cut_outside_the_text_is_refused(tmp_path: Path) -> None:
    cut = {accession(1): {HUMAN_CAPITAL: (0, 10**9)}}
    with pytest.raises(SplitRefused, match="human-capital part is outside"):
        _inputs(tmp_path, hand=cut)
