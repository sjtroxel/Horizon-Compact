"""The section map applied: which admitted text feeds which dossier section (§4.5, protocol §12.6).

| Section | From |
|---|---|
| 1 overview | the annual report's Item 1 |
| 2 segments and facilities | its Item 2, and the segment note |
| 3 workforce | Item 1's human-capital part |
| 4 financial position | XBRL figures (``figures.py``) |
| 5 capital allocation | XBRL figures, and the annual report's Item 7 for acquisitions |
| 6 the situation at the cut-off | the later periodic report's discussion of results (the quarterly report's
  Part I Item 2, or the annual report's Item 7), and every admitted current report with its exhibits |
| 7 the options | the scenario shape (step 5), not here |

This module only gathers text, and only for the sections the case's scenario shape needs (``SHAPE_SECTIONS``,
protocol §12.6). The extraction request (step 5) is what reads a section's parts.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from horizon_compact.casebuild.documents import DocumentSet, SourceDocument
from horizon_compact.casebuild.figures import FigureTable, extract_figures
from horizon_compact.casebuild.splitter import (
    Split,
    SplitRefused,
    cut_by_hand,
    html_to_text,
    human_capital_part,
    segment_note,
    split_by_hand,
    split_items,
)

# Protocol §12.6: the sections each scenario shape (§12.5) needs. Only those are built, so a filing is never
# refused over a part its case does not use (Opus review, 2026-10-11).
SHAPE_SECTIONS: dict[str, tuple[int, ...]] = {
    "S1": (1, 3, 4, 6, 7),
    "S2": (1, 3, 4, 5, 6, 7),
    "S3": (1, 2, 3, 4, 5, 6, 7),
    "S4": (1, 4, 5, 6, 7),
}
QUARTERLY_WANTED = ("I.2",)
# A hand boundary for Item 1's human-capital part alone, beside or instead of hand-cut items.
HUMAN_CAPITAL = "human-capital"

# Per accession number: item key (or HUMAN_CAPITAL) to (start, end) offsets in the filing's extracted text.
HandBoundaries = Mapping[str, Mapping[str, tuple[int, int]]]


@dataclass(frozen=True)
class TextPart:
    label: str
    text: str


@dataclass
class SectionInputs:
    shape: str
    parts: dict[int, list[TextPart]]
    figures: FigureTable
    record: dict[str, Any] = field(default_factory=dict)


def _split(
    document: SourceDocument, form: str, wanted: tuple[str, ...], hand: HandBoundaries
) -> tuple[str, Split]:
    """The filing's text and its items: cut by hand where item boundaries are given, else split."""
    text = html_to_text(document.text())
    items = {k: v for k, v in hand.get(document.accession, {}).items() if k != HUMAN_CAPITAL}
    if not items:
        return text, split_items(text, form=form, wanted=wanted)
    split = split_by_hand(text, items)
    missing = [w for w in wanted if w not in split.sections]
    if missing:
        raise SplitRefused(
            f"hand boundaries for {document.accession} lack item(s) {', '.join(missing)}"
        )
    return text, split


def _annual_items(needed: tuple[int, ...], annual_is_latest: bool) -> tuple[str, ...]:
    wanted: list[str] = []
    if 1 in needed or 3 in needed:
        wanted.append("1")
    if 2 in needed:
        wanted.append("2")
    if 5 in needed or (6 in needed and annual_is_latest):
        wanted.append("7")
    return tuple(wanted)


def build_section_inputs(
    docset: DocumentSet, *, shape: str, hand: HandBoundaries | None = None
) -> SectionInputs:
    """Gather the admitted text of each section the shape needs.

    Raises ``SplitRefused`` where a filing, or Item 1's human-capital part, must be cut by hand.
    """
    if shape not in SHAPE_SECTIONS:
        raise ValueError(
            f"unknown scenario shape {shape!r}; expected one of {sorted(SHAPE_SECTIONS)}"
        )
    hand = hand or {}
    needed = tuple(n for n in SHAPE_SECTIONS[shape] if n != 7)
    periodic = docset.latest_periodic()
    annual_is_latest = periodic is docset.annual
    annual_text, annual = _split(
        docset.annual, "10-K", _annual_items(needed, annual_is_latest), hand
    )
    label = f"annual report {docset.annual.accession}"
    parts: dict[int, list[TextPart]] = {n: [] for n in needed}
    record: dict[str, Any] = {
        "shape": shape,
        "sections": list(needed),
        "annual_split": annual.record(),
    }

    if 1 in parts:
        parts[1].append(TextPart(f"{label}, Item 1", annual.sections["1"]))
    if 2 in parts:
        parts[2].append(TextPart(f"{label}, Item 2", annual.sections["2"]))
        segments = segment_note(*(annual.sections.get(i, "") for i in ("8", "15", "16")))
        if segments is not None:
            parts[2].append(TextPart(f"{label}, segment note", segments))
        record["segment_note_found"] = segments is not None
    if 3 in parts:
        cut = hand.get(docset.annual.accession, {}).get(HUMAN_CAPITAL)
        if cut is not None:
            workforce = cut_by_hand(annual_text, *cut, what="the human-capital part")
        else:
            workforce = human_capital_part(annual.sections["1"])
        parts[3].append(TextPart(f"{label}, human capital", workforce))
        record["human_capital_by_hand"] = cut is not None
    if 5 in parts:
        parts[5].append(TextPart(f"{label}, Item 7", annual.sections["7"]))
    if 6 in parts:
        if annual_is_latest:
            parts[6].append(TextPart(f"{label}, Item 7", annual.sections["7"]))
        else:
            _, quarterly = _split(periodic, "10-Q", QUARTERLY_WANTED, hand)
            parts[6].append(
                TextPart(
                    f"quarterly report {periodic.accession}, Part I Item 2",
                    quarterly.sections["I.2"],
                )
            )
            record["quarterly_split"] = quarterly.record()
        for report in docset.current:
            for source in (report.main, *report.exhibits):
                parts[6].append(
                    TextPart(
                        f"{source.form} {source.accession} filed {source.filed}",
                        html_to_text(source.text()),
                    )
                )
    figures = extract_figures(docset.facts.json(), docset.cutoff)
    record["figures"] = figures.record()
    record["latest_periodic"] = periodic.accession
    return SectionInputs(shape=shape, parts=parts, figures=figures, record=record)
