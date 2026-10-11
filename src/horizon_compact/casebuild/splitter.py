"""Filing HTML to text, and text to items (IMPLEMENTATION §4.5).

**The fragile part, and untested on any real filing** (§10): filings are HTML with a table of contents that
repeats every heading. These rules are tested on synthetic filings only. The splitter therefore refuses rather
than guesses, and a refused split is done by hand with the boundaries recorded (``split_by_hand``).

The rules:

- A heading is a line that starts with ``Item <n>[A-C]``, is at most 200 characters, and whose title (the rest
  of the line, or the next line when the rest is empty) contains a keyword of that item's known title. A line
  that begins "Item 7" in the middle of prose without the title is not a heading.
- A 10-Q's items repeat across its two parts, so a 10-Q's key carries the part: ``I.2``, ``II.2``.
- The table of contents is the run of headings before the item order first restarts (the body's Item 1 after
  the contents' last item). It must be at least five headings, each with almost no text after it (the last
  one is exempt: the cover text sits between it and the body). A restart that is not that pattern is refused.
- In the body each item is found exactly once and in order. Otherwise the split is refused. So is a wanted
  item that is missing.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from itertools import pairwise
from typing import Any

MAX_HEADING_CHARS = 200
MIN_TOC_HEADINGS = 5
TOC_MAX_BODY_CHARS = 200

_BLOCK = frozenset(
    {
        "p",
        "div",
        "br",
        "tr",
        "li",
        "ul",
        "ol",
        "table",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "section",
    }
)
_CELL = frozenset({"td", "th"})
_SKIP = frozenset({"script", "style", "ix:header"})

KEYWORDS_10K: dict[str, tuple[str, ...]] = {
    "1": ("business",),
    "1A": ("risk factors",),
    "1B": ("unresolved",),
    "1C": ("cybersecurity",),
    "2": ("properties",),
    "3": ("legal proceedings",),
    "4": ("mine safety",),
    "5": ("market for",),
    "6": ("reserved", "selected financial"),
    "7": ("management",),
    "7A": ("quantitative and qualitative",),
    "8": ("financial statements",),
    "9": ("changes in and disagreements",),
    "9A": ("controls and procedures",),
    "9B": ("other information",),
    "9C": ("foreign jurisdictions",),
    "10": ("directors",),
    "11": ("executive compensation",),
    "12": ("security ownership",),
    "13": ("certain relationships",),
    "14": ("principal account",),
    "15": ("exhibit",),
    "16": ("form 10-k summary", "summary"),
}
KEYWORDS_10Q: dict[str, tuple[str, ...]] = {
    "I.1": ("financial statements",),
    "I.2": ("management",),
    "I.3": ("quantitative and qualitative",),
    "I.4": ("controls and procedures",),
    "II.1": ("legal proceedings",),
    "II.1A": ("risk factors",),
    "II.2": ("unregistered sales",),
    "II.3": ("defaults",),
    "II.4": ("mine safety",),
    "II.5": ("other information",),
    "II.6": ("exhibit",),
}

_PARTS = {"i": 1, "ii": 2, "iii": 3, "iv": 4}
_PART_LINE = re.compile(r"part\s+(iv|iii|ii|i)\b", re.IGNORECASE)
_ITEM_LINE = re.compile(
    r"item\s*(\d{1,2})(?:([a-c])(?![a-z]))?(?!\d)\s*[.:\u2013\u2014-]*\s*(.*)", re.IGNORECASE
)
_HUMAN_CAPITAL = re.compile(
    r"(?:our\s+)?(?:human\s+capital|human\s+resources|employees|our\s+people|workforce)\b.{0,50}",
    re.IGNORECASE,
)
# What usually follows the human-capital part in Item 1. Ending there, or at the end of Item 1, can only
# include too much, which is harmless: the extraction step is told to read the workforce.
_AFTER_HUMAN_CAPITAL = re.compile(
    r"(?:available information|information about our executive officers|executive officers of the registrant|"
    r"government regulation|regulation|competition|intellectual property|seasonality|environmental matters|"
    r"raw materials|backlog|corporate information|where you can find more information)\b.{0,50}",
    re.IGNORECASE,
)


class SplitRefused(Exception):
    """The splitter will not guess. The caller splits by hand and records the boundaries."""


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: Any) -> None:
        if tag in _SKIP:
            self._skip += 1
        elif tag in _BLOCK:
            self.parts.append("\n")
        elif tag in _CELL:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP:
            self._skip = max(0, self._skip - 1)
        elif tag in _BLOCK:
            self.parts.append("\n")
        elif tag in _CELL:
            self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    """Visible text, one block per line, table cells of a row joined by a space, blank lines dropped."""
    parser = _TextParser()
    parser.feed(html)
    parser.close()
    lines = []
    for raw in unescape("".join(parser.parts)).replace("\xa0", " ").splitlines():
        line = re.sub(r"[ \t\u2009\u200b]+", " ", raw).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


@dataclass(frozen=True)
class Heading:
    key: str
    line: int  # index into the text's lines
    offset: int  # character offset of the line's start
    order: tuple[int, int, str]


@dataclass(frozen=True)
class Split:
    sections: dict[str, str]
    headings: tuple[Heading, ...]  # the body's, in order
    toc_headings: int
    by_hand: bool = False

    def record(self) -> dict[str, Any]:
        return {
            "by_hand": self.by_hand,
            "table_of_contents_headings_skipped": self.toc_headings,
            "headings": [
                {"item": h.key, "line": h.line, "offset": h.offset} for h in self.headings
            ],
            "sections": {key: len(text) for key, text in self.sections.items()},
        }


_PART_ORDER = {"": 0, "I": 1, "II": 2}
_ITEM_KEY = re.compile(r"(?:(?:I|II)\.)?\d{1,2}[A-C]?")


def _item_order(key: str) -> tuple[int, int, str]:
    """Sort key for ``7A`` (a 10-K item) or ``II.1A`` (a 10-Q part and item)."""
    part, _, item = key.rpartition(".")
    match = re.fullmatch(r"(\d+)([A-C]?)", item)
    assert match is not None
    return (_PART_ORDER[part], int(match.group(1)), match.group(2))


def _title_matches(keywords: tuple[str, ...], title: str) -> bool:
    lowered = title.lower().replace("\u2019", "'")
    return any(word in lowered for word in keywords)


def find_headings(text: str, *, form: str) -> list[Heading]:
    """Every item heading by the rules above, in text order (the table of contents included)."""
    if form not in ("10-K", "10-Q"):
        raise SplitRefused(f"no item rules for form {form}")
    keywords = KEYWORDS_10K if form == "10-K" else KEYWORDS_10Q
    lines = text.split("\n")
    offsets: list[int] = []
    position = 0
    for line in lines:
        offsets.append(position)
        position += len(line) + 1
    headings: list[Heading] = []
    part = ""
    for index, line in enumerate(lines):
        if form == "10-Q" and len(line) <= MAX_HEADING_CHARS:
            part_match = _PART_LINE.match(line)
            if part_match:
                part = part_match.group(1).upper()
                continue
        if len(line) > MAX_HEADING_CHARS:
            continue
        match = _ITEM_LINE.fullmatch(line)
        if not match:
            continue
        number, letter, rest = match.group(1), (match.group(2) or "").upper(), match.group(3)
        item = f"{number}{letter}"
        key = f"{part}.{item}" if form == "10-Q" else item
        if form == "10-Q" and not part:
            continue
        wanted = keywords.get(key)
        if wanted is None:
            continue
        title = rest
        if len(re.sub(r"[^A-Za-z]", "", rest)) < 3 and index + 1 < len(lines):
            title = f"{rest} {lines[index + 1]}"
        if _title_matches(wanted, title):
            headings.append(
                Heading(key=key, line=index, offset=offsets[index], order=_item_order(key))
            )
    return headings


def _body_after_contents(text: str, headings: list[Heading]) -> tuple[list[Heading], int]:
    """Drop the table of contents. Refuse a restart in item order that is not one."""
    restart = next(
        (i for i in range(1, len(headings)) if headings[i].order <= headings[i - 1].order), None
    )
    if restart is None:
        return headings, 0
    if restart < MIN_TOC_HEADINGS:
        raise SplitRefused(
            "item headings restart in order, but too early to be a table of contents"
        )
    for i in range(restart - 1):
        end = headings[i + 1].offset
        first_line_end = text.find("\n", headings[i].offset)
        between = text[first_line_end:end] if first_line_end != -1 else ""
        if len(re.sub(r"[\s\d.]", "", between)) > TOC_MAX_BODY_CHARS:
            raise SplitRefused(
                f"item headings restart in order after {headings[i].key}, but the headings before it "
                "carry text, so they are not a table of contents"
            )
    return headings[restart:], restart


def split_items(text: str, *, form: str, wanted: Sequence[str] = ()) -> Split:
    """Split a filing's text into its items, or refuse."""
    found = find_headings(text, form=form)
    body, skipped = _body_after_contents(text, found)
    if not body:
        raise SplitRefused("no item headings were found")
    keys = [h.key for h in body]
    duplicates = sorted({k for k in keys if keys.count(k) > 1})
    if duplicates:
        raise SplitRefused(f"item(s) {', '.join(duplicates)} found more than once in the body")
    for earlier, later in pairwise(body):
        if later.order <= earlier.order:
            raise SplitRefused(f"item {later.key} found out of order, after {earlier.key}")
    missing = [w for w in wanted if w not in keys]
    if missing:
        raise SplitRefused(f"wanted item(s) {', '.join(missing)} not found")
    sections: dict[str, str] = {}
    for heading, following in zip(body, [*body[1:], None], strict=True):
        start = text.find("\n", heading.offset)
        start = len(text) if start == -1 else start + 1
        end = following.offset if following else len(text)
        sections[heading.key] = text[start:end].strip()
    return Split(sections=sections, headings=tuple(body), toc_headings=skipped)


def split_by_hand(text: str, boundaries: Mapping[str, tuple[int, int]]) -> Split:
    """Sections cut by a person: item key to (start, end) offsets in this text. Recorded in the split."""
    sections: dict[str, str] = {}
    for key, (start, end) in boundaries.items():
        if not _ITEM_KEY.fullmatch(key):
            raise SplitRefused(f"hand boundary key {key!r} is not an item such as 7, 1A or I.2")
        sections[key] = cut_by_hand(text, start, end, what=f"item {key}")
    headings = tuple(
        Heading(key=key, line=text.count("\n", 0, start), offset=start, order=_item_order(key))
        for key, (start, _) in sorted(boundaries.items(), key=lambda kv: kv[1][0])
    )
    return Split(sections=sections, headings=headings, toc_headings=0, by_hand=True)


def human_capital_part(item_1: str) -> str:
    """Item 1's human-capital part: from its heading to the next usual Item 1 subheading or the end."""
    lines = item_1.split("\n")
    start = next(
        (i for i, line in enumerate(lines) if len(line) <= 80 and _HUMAN_CAPITAL.fullmatch(line)),
        None,
    )
    if start is None:
        raise SplitRefused("no human-capital heading found in Item 1; cut it by hand")
    end = next(
        (
            i
            for i in range(start + 1, len(lines))
            if len(lines[i]) <= 80 and _AFTER_HUMAN_CAPITAL.fullmatch(lines[i])
        ),
        len(lines),
    )
    return "\n".join(lines[start:end]).strip()


_DASH = r"[.:)\u2013\u2014-]"
# A note heading: "Note 12 - Leases", "Note 12A", or a numbered heading "12. Leases". The numbered form needs
# a capital letter after the number, so a table row of figures is not one: only the "note" word ignores case.
_NOTE_HEADING = re.compile(
    rf"(?:(?i:note)\s+\d+[A-Za-z]?\b.{{0,100}}|\d{{1,2}}\s*{_DASH}\s+[A-Z].{{0,100}})"
)
_SEGMENT_HEADING = re.compile(
    rf"(?:note\s+\d+[a-z]?\s*{_DASH}?\s*|\d{{1,2}}\s*{_DASH}\s*)?"
    r"(?:reportable\s+|operating\s+|business\s+)?segments?"
    r"(?:\s+(?:information|reporting|data|disclosures?|results))?"
    r"(?:\s*(?:,|and)\s+[a-z ,]{0,60})?",
    re.IGNORECASE,
)


def segment_note(*texts: str) -> str | None:
    """The segment note: from its heading to the next note heading, searched in the texts in order.

    The heading must be shaped like one ("Note 17 - Segment Information", "17. Segment Information",
    "Segment Reporting"), so a table row such as "Total segment revenue" is not taken for it. Item 8 often
    only points to financial statements placed after Item 15, so the caller passes Items 8, 15 and 16. None
    when no heading is found: the section's segment figures are then cut by hand.
    """
    for text in texts:
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if len(line) <= 100 and _SEGMENT_HEADING.fullmatch(line):
                end = next(
                    (
                        j
                        for j in range(i + 1, len(lines))
                        if len(lines[j]) <= 100 and _NOTE_HEADING.fullmatch(lines[j])
                    ),
                    len(lines),
                )
                return "\n".join(lines[i:end]).strip()
    return None


def cut_by_hand(text: str, start: int, end: int, *, what: str) -> str:
    """One span cut by a person, by character offsets in this text."""
    if not 0 <= start < end <= len(text):
        raise SplitRefused(f"hand boundary for {what} is outside the text or empty")
    return text[start:end].strip()
