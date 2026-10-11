"""Dates become relative to the cut-off's fiscal year (IMPLEMENTATION §4.8; protocol §12.6).

"Fiscal year N" is the fiscal year of the latest annual figure (the year just ended), earlier years are
"N-1", "N-2", the year in progress at the cut-off is "N+1", and a quarter is named within its year:
"fiscal year N-1, third quarter". The patterns are fixed; a date in a form they do not know is flagged for the
human, never left silently (``transform.py`` flags it).

**Assumption, flagged whenever it matters:** a bare "2025" or "fiscal 2025" is read as the fiscal year ENDING
in 2025. That is unambiguous for a December year-end. A filer with another year-end may call the year ending
in January 2026 "fiscal 2025"; for those filers every such reading is flagged for the human to confirm.
"""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, timedelta

_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12, "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}  # fmt: skip
_ORDINALS = {1: "first", 2: "second", 3: "third", 4: "fourth"}
_ORDINAL_NUMBERS = {word: number for number, word in _ORDINALS.items()}

# A month name only as a whole word: "codec 2025" and "Dismay 3, 2025" hold no month (Opus review).
_MONTH = (
    r"(?<![A-Za-z])(?:January|February|March|April|May|June|July|August|September|October|November|December"
    r"|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept|Sep|Oct|Nov|Dec)\.?"
)
_YEAR = r"(?:19|20)\d{2}"
DATE = (
    rf"(?:{_MONTH}\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+{_YEAR}"  # March 31, 2026
    rf"|\d{{1,2}}\s+{_MONTH}\s+{_YEAR}"  # 31 March 2026
    rf"|{_MONTH}\s+(?:of\s+)?{_YEAR}"  # March 2026
    rf"|{_YEAR}-\d{{2}}-\d{{2}}"  # 2026-03-31
    rf"|\d{{1,2}}/\d{{1,2}}/(?:19|20)?\d{{2}})"  # 3/31/2026
)
MONTH_DAY_WITHOUT_YEAR = rf"{_MONTH}\s+\d{{1,2}}(?:st|nd|rd|th)?\b(?!,?\s*{_YEAR})"
ENDED = rf"(?:the\s+)?(?:fiscal\s+)?(?:year|quarter|period)\s+ended\s+{DATE}"
QUARTER = (
    rf"(?:(?:first|second|third|fourth)\s+(?:fiscal\s+)?quarter(?:\s+of)?(?:\s+fiscal(?:\s+year)?)?\s+{_YEAR}"
    rf"|Q[1-4]\s+(?:FY\s*)?{_YEAR})"
)
FISCAL_YEAR = rf"(?:fiscal(?:\s+year)?|FY)\s*{_YEAR}"
BARE_YEAR = rf"(?<![\d,.$/-]){_YEAR}(?!\d|,\d|\.\d|-\d|/)"


class DateError(Exception):
    """A date the patterns matched but that is not a real date, or a calendar that cannot be built."""


def _shift(day: date, years: int) -> date:
    """The same month and day ``years`` away; a month-end stays a month-end (Feb 28 and 29, Jan 31)."""
    target_year = day.year + years
    last = calendar.monthrange(target_year, day.month)[1]
    was_month_end = day.day == calendar.monthrange(day.year, day.month)[1]
    return date(target_year, day.month, last if was_month_end else min(day.day, last))


@dataclass(frozen=True)
class FiscalCalendar:
    """Fiscal years laid out from the latest annual year end (``year_end``), each ending a year apart."""

    year_end: date

    @property
    def december(self) -> bool:
        return self.year_end.month == 12 and self.year_end.day == 31

    def locate(self, day: date) -> tuple[int, int]:
        """(offset, quarter): the fiscal year of ``day`` (0 is year N) and its quarter, 1 to 4."""
        offset = day.year - self.year_end.year
        while _shift(self.year_end, offset) < day:
            offset += 1
        while _shift(self.year_end, offset - 1) >= day:
            offset -= 1
        first = _shift(self.year_end, offset - 1) + timedelta(days=1)  # the year's first day
        months = (day.year - first.year) * 12 + day.month - first.month
        if day.day < first.day:
            months -= 1
        return offset, min(max(months // 3 + 1, 1), 4)

    def year_label(self, offset: int) -> str:
        if offset == 0:
            return "fiscal year N"
        return f"fiscal year N{offset:+d}"

    def label(self, day: date) -> str:
        offset, quarter = self.locate(day)
        return f"{self.year_label(offset)}, {_ORDINALS[quarter]} quarter"

    def year_ending_in(self, year: int) -> str:
        """The label of the fiscal year ending in calendar ``year`` (the stated assumption)."""
        return self.year_label(year - self.year_end.year)


def parse_date(text: str) -> date:
    """A matched date string (any form in ``DATE``) as a date."""
    text = text.strip().rstrip(".")
    iso = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", text)
    numeric = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})", text)
    try:
        if iso:
            return date(int(iso.group(1)), int(iso.group(2)), int(iso.group(3)))
        if numeric:
            year = int(numeric.group(3))
            return date(
                year + 2000 if year < 100 else year, int(numeric.group(1)), int(numeric.group(2))
            )
        words = re.sub(
            r"(?<=\d)(?:st|nd|rd|th)", "", text.replace(",", " ").replace(".", " ")
        ).split()
        words = [w for w in words if w.lower() != "of"]
        month_first = [w for w in words if w.lower() in _MONTHS]
        if not month_first:
            raise DateError("no month in a date")
        month = _MONTHS[month_first[0].lower()]
        numbers = [int(w) for w in words if w.isdigit()]
        year = next(n for n in numbers if n >= 1000)
        days = [n for n in numbers if n < 1000]
        # A month and year alone ("March 2026") is read at the month's end, its last day.
        day = days[0] if days else calendar.monthrange(year, month)[1]
        return date(year, month, day)
    except (ValueError, StopIteration) as exc:
        raise DateError("a matched date is not a real date") from exc


def quarter_word(quarter: int) -> str:
    return _ORDINALS[quarter]


def year_in(text: str) -> int:
    """The first four-digit year in ``text``."""
    found = re.search(_YEAR, text)
    if found is None:
        raise DateError("no year in a matched date")
    return int(found.group(0))


def quarter_year(text: str) -> tuple[int, int]:
    """(quarter, calendar year) from "third quarter of fiscal 2025" or "Q3 2025"."""
    year = year_in(text)
    short = re.match(r"Q([1-4])", text, re.IGNORECASE)
    if short:
        return int(short.group(1)), year
    return _ORDINAL_NUMBERS[text.split()[0].lower()], year
