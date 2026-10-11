"""Filing HTML to text and items (Phase 5 code half, build step 4, §4.5). Synthetic filings only (§10)."""

from __future__ import annotations

import pytest

from edgar_helpers import TEN_K_HTML, TEN_Q_HTML
from horizon_compact.casebuild.splitter import (
    SplitRefused,
    find_headings,
    html_to_text,
    human_capital_part,
    segment_note,
    split_by_hand,
    split_items,
)


def _text(html: str) -> str:
    return html_to_text(html)


def test_html_to_text_keeps_one_block_per_line_and_joins_table_cells() -> None:
    text = _text(
        "<table><tr><td>Item&nbsp;1.</td><td>Business</td><td>3</td></tr></table><p>A<br>B</p>"
    )
    assert text.split("\n") == ["Item 1. Business 3", "A", "B"]


def test_html_to_text_drops_scripts_styles_and_the_hidden_xbrl_header() -> None:
    text = _text(
        "<style>.x{}</style><script>var a = 'Item 9';</script>"
        "<ix:header><div>hidden</div></ix:header><p>shown &amp; kept</p>"
    )
    assert text == "shown & kept"


def test_the_annual_report_splits_past_its_table_of_contents() -> None:
    split = split_items(_text(TEN_K_HTML), form="10-K", wanted=("1", "2", "7"))
    assert [h.key for h in split.headings] == ["1", "1A", "2", "7", "8", "15"]
    assert split.toc_headings == 6
    assert "two segments" in split.sections["1"]
    assert "Business" not in split.sections["1"].split("\n")[0]
    assert "One plant in the Midwest" in split.sections["2"]
    assert "perch maker" in split.sections["7"]
    assert "Item 7" not in split.sections["2"]  # the contents' line is not in a section


def test_a_line_that_starts_with_an_item_number_in_prose_is_not_a_heading() -> None:
    split = split_items(_text(TEN_K_HTML), form="10-K")
    assert "Item 7 discusses our results" in split.sections["1A"]


def test_a_heading_whose_title_sits_on_the_next_line_is_found() -> None:
    """Item 8 in the fixture is ``Item 8.`` then, in the next block, its title."""
    split = split_items(_text(TEN_K_HTML), form="10-K")
    assert split.sections["8"].startswith("Financial Statements and Supplementary Data")
    assert "follow Item 15" in split.sections["8"]


def test_a_filing_with_no_table_of_contents_splits_too() -> None:
    body = _text(TEN_K_HTML).split("\n")
    start = next(i for i, line in enumerate(body) if line.startswith("Cautionary"))
    split = split_items("\n".join(body[start:]), form="10-K", wanted=("1", "7"))
    assert split.toc_headings == 0
    assert "perch maker" in split.sections["7"]


def test_a_wanted_item_that_is_missing_is_refused() -> None:
    text = _text(TEN_K_HTML).replace("Item 2. Properties\nOne plant", "Properties\nOne plant")
    with pytest.raises(SplitRefused, match=r"wanted item\(s\) 2"):
        split_items(text, form="10-K", wanted=("2",))


def test_an_item_found_twice_in_the_body_is_refused() -> None:
    text = _text(TEN_K_HTML) + "\nItem 2. Properties\nA second properties section."
    with pytest.raises(SplitRefused, match=r"more than once|out of order"):
        split_items(text, form="10-K")


def test_an_item_out_of_order_in_the_body_is_refused() -> None:
    text = _text(TEN_K_HTML)
    text = text.replace(
        "Item 2. Properties\nOne plant",
        "Item 9. Changes in and Disagreements with Accountants\nOne plant",
    )
    with pytest.raises(SplitRefused, match="out of order"):
        split_items(text, form="10-K")


def test_a_restart_that_is_not_a_table_of_contents_is_refused() -> None:
    body = "\n".join(
        [
            "Item 1. Business",
            "Real business text, a good deal of it, " * 20,
            "Item 1A. Risk Factors",
            "Real risk text, " * 40,
            "Item 2. Properties",
            "Real property text, " * 40,
            "Item 1. Business",
            "Again.",
        ]
    )
    with pytest.raises(SplitRefused, match="too early to be a table of contents"):
        split_items(body, form="10-K")


def test_no_headings_at_all_is_refused() -> None:
    with pytest.raises(SplitRefused, match="no item headings"):
        split_items("just prose\nand more prose", form="10-K")


def test_an_unsupported_form_is_refused() -> None:
    with pytest.raises(SplitRefused, match="no item rules"):
        find_headings("x", form="8-K")


def test_the_quarterly_report_keeps_its_two_parts_apart() -> None:
    split = split_items(_text(TEN_Q_HTML), form="10-Q", wanted=("I.2",))
    assert [h.key for h in split.headings] == ["I.1", "I.2", "I.3", "I.4", "II.1", "II.2", "II.6"]
    assert "Quarterly demand fell" in split.sections["I.2"]
    assert "must not be mistaken" in split.sections["II.2"]
    assert "must not be mistaken" not in split.sections["I.2"]


def test_a_quarterly_report_item_outside_any_part_is_not_a_heading() -> None:
    assert find_headings("Item 2. Management's Discussion and Analysis\ntext", form="10-Q") == []


def test_the_split_record_lists_headings_and_section_sizes() -> None:
    record = split_items(_text(TEN_K_HTML), form="10-K").record()
    assert record["by_hand"] is False
    assert record["table_of_contents_headings_skipped"] == 6
    assert [h["item"] for h in record["headings"]][:2] == ["1", "1A"]
    assert record["sections"]["2"] > 0


def test_a_hand_split_is_recorded_as_by_hand_and_checks_its_bounds() -> None:
    text = "alpha beta gamma delta"
    split = split_by_hand(text, {"1": (0, 10), "7": (11, 22)})
    assert split.sections == {"1": "alpha beta", "7": "gamma delta"}
    assert split.record()["by_hand"] is True
    assert [h.offset for h in split.headings] == [0, 11]
    for bad in ((5, 5), (-1, 3), (0, 99)):
        with pytest.raises(SplitRefused, match="outside the text or empty"):
            split_by_hand(text, {"1": bad})


def test_human_capital_runs_to_the_next_usual_subheading() -> None:
    item_1 = split_items(_text(TEN_K_HTML), form="10-K").sections["1"]
    part = human_capital_part(item_1)
    assert part.startswith("Human Capital")
    assert "1,240 people" in part
    assert "Available Information" not in part
    assert "two segments" not in part


def test_human_capital_runs_to_the_end_of_item_1_when_nothing_follows() -> None:
    assert human_capital_part("Overview\nText.\nOur Employees\nWe have 50 people.\nMore.") == (
        "Our Employees\nWe have 50 people.\nMore."
    )


def test_a_missing_human_capital_heading_is_refused() -> None:
    with pytest.raises(SplitRefused, match="human-capital"):
        human_capital_part("Overview\nWe make things.\nNothing about people here.")


def test_the_segment_note_is_found_after_item_15_when_item_8_only_points_to_it() -> None:
    sections = split_items(_text(TEN_K_HTML), form="10-K").sections
    note = segment_note(sections["8"], sections["15"])
    assert note is not None
    assert note.startswith("Note 12 - Segment Information")
    assert "Cages revenue was 900" in note
    assert "Subsequent Events" not in note


def test_a_table_row_that_mentions_segments_is_not_taken_for_the_note() -> None:
    item_8 = "\n".join(
        [
            "Consolidated Statements of Operations",
            "Total segment revenue",
            "1,000 900",
            "Note 1 - Basis",
            "text",
            "Note 17 - Segment Information",
            "the real note",
        ]
    )
    assert segment_note(item_8) == "Note 17 - Segment Information\nthe real note"


@pytest.mark.parametrize(
    "heading",
    [
        "Note 17 - Segment Information",
        "NOTE 17. SEGMENT REPORTING",
        "17. Segment Information",
        "Segment Information",
        "Reportable Segments",
        "Note 5 - Segment and Geographic Information",
    ],
)
def test_note_headings_in_the_usual_forms_are_found(heading: str) -> None:
    assert segment_note(f"{heading}\nbody") == f"{heading}\nbody"


def test_a_numbered_note_ends_at_the_next_numbered_heading_not_at_a_row_of_figures() -> None:
    text = "17. Segment Information\n12 600\n18. Subsequent Events\nlater"
    assert segment_note(text) == "17. Segment Information\n12 600"


def test_a_hand_boundary_key_that_is_not_an_item_is_refused() -> None:
    with pytest.raises(SplitRefused, match="not an item"):
        split_by_hand("some text here", {"workforce": (0, 4)})


def test_no_segment_note_gives_none_not_a_guess() -> None:
    assert segment_note("Note 1 - Basis\ntext", "nothing here") is None
