"""Dates and numbers in one pass: relative dates, scaled dollars and headcounts, and a flag for the rest.

IMPLEMENTATION §4.8. One regular expression with the forms in priority order, so every span of the text is
decided once and a replacement is never itself re-read (a "fiscal year N-1" is not flagged as a number).
**Nothing is left silently:** every number the patterns do not classify, every date in a form they do not
know, every per-share figure and share count, and every unit volume is a flag for the human, and the text
keeps it as written. The builder's assembly (step 6) refuses a dossier while flags stand.

What is scaled: dollar figures (``$11.4 million``, ``$56,050``) and headcounts (a number before a word such
as employees or people, or after "employs", "headcount of", "of whom"). What is not: percentages, durations,
structure labels (Item 7, Note 12), and **a dollar figure stated per employee or per hour or as an average
wage** (a ratio of two scaled quantities). Per-share figures and share counts are flagged for removal (§4.8).

The headcount and ratio patterns are heuristics tested on synthetic text only (§10); a miss is a number that
falls to "unclassified" and is flagged, never one that is scaled wrongly without notice.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from horizon_compact.casebuild import dates as d
from horizon_compact.casebuild.scale import (
    PayCheck,
    PayFigure,
    check_pay_per_head,
    format_number,
    scale_dollars,
    scale_heads,
)

# A number with proper thousands groups, so a trailing comma ("Plant 6, ...") is not part of it.
_INT = r"(?:\d{1,3}(?:,\d{3})+|\d+)"
_NUM = rf"{_INT}(?:\.\d+)?"
_HEAD_NOUN = (
    r"(?:employees|associates|workers|people|persons|team\s+members|positions|jobs|roles|staff|technicians|"
    r"engineers|operators|members)"
)
_HEAD_ADJ = (
    r"(?:(?:full[- ]time|part[- ]time|hourly|salaried|union|unionized|non-union|represented|permanent|"
    r"temporary|seasonal|production|manufacturing|skilled|engineering)\s+){0,3}"
)
_HEDGE = r"(?:(?:about|approximately|roughly|around|nearly|over|some|more\s+than|almost)\s+)?"
_NUMBER_WORD = (
    r"(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|thirty|forty|fifty|sixty|"
    r"seventy|eighty|ninety|hundred|thousand|million)"
)
_VOLUME_UNIT = (
    r"(?:tons?|tonnes?|units?|pounds|lbs|barrels|vehicles|trucks|cars|acres|square\s+feet|sq\.?\s*ft\.?|"
    r"miles|megawatts|MW|gallons|bushels|ounces)"
)

_PATTERN = re.compile(
    "|".join(
        [
            rf"(?P<ended>{d.ENDED})",
            rf"(?P<date>{d.DATE})",
            rf"(?P<quarter>{d.QUARTER})",
            rf"(?P<fiscal>{d.FISCAL_YEAR})",
            rf"(?P<monthday>{d.MONTH_DAY_WITHOUT_YEAR})",
            rf"(?P<pct>{_NUM}\s*(?:%|percent\b|per\s*cent\b|basis\s+points?\b|bps\b))",
            rf"(?P<dollar>(?:US)?\$\s?(?P<d_num>{_NUM})"
            r"(?:\s?(?P<d_unit>thousand|million|billion|trillion|mm|bn|[kKmMbB])\b)?)",
            rf"(?P<shares>{_NUM}\s*(?:(?:thousand|million|billion)\s+)?shares\b)",
            rf"(?P<heads>(?P<h_hedge>{_HEDGE})(?P<h_num>{_INT})(?=\s+{_HEAD_ADJ}{_HEAD_NOUN}\b))",
            r"(?P<heads2>(?P<h2_pre>(?:employ(?:s|ed)|headcount\s+of|workforce\s+of|staff\s+of|"
            r"of\s+(?:whom|which))\s+)(?P<h2_hedge>(?:about|approximately|roughly|around|nearly|over)\s+)?"
            rf"(?P<h2_num>{_INT}))",
            rf"(?P<words>\b(?:{_NUMBER_WORD}[-\s]+){{1,4}}{_HEAD_NOUN}\b)",
            rf"(?P<volume>{_NUM}\s*(?:(?:thousand|million)\s+)?{_VOLUME_UNIT}\b)",
            rf"(?P<duration>{_NUM}[\s-]+(?:years?|months?|weeks?|days?|quarters?)\b)",
            r"(?P<relative>\bfiscal\s+year\s+N(?:[+-]\d+)?\b)",
            r"(?P<struct>(?:Item|Note|Part|Section|Exhibit|Table|Figure|Schedule|Page)\s+\d+[A-Za-z]?)",
            r"(?P<form>\b\d{1,2}-[KQ]\b|\b401\(k\))",
            r"(?P<ordinal>\d+(?:st|nd|rd|th)\b)",
            rf"(?P<year>{d.BARE_YEAR})",
            rf"(?P<other>(?<![\w.]){_NUM})",
        ]
    ),
    re.IGNORECASE,
)

_RATIO_AFTER = re.compile(
    r"^\s*(?:(?:per|an?|each)\s+(?:employee|worker|person|head|hour|unit)\b"
    r"|/\s*(?:hr|hour)\b|(?:an?\s+)?(?:year|annum)\s+(?:on\s+average|per\s+(?:employee|worker)))",
    re.IGNORECASE,
)
# "per diluted share" and "per basic and diluted common share" too (closure-07's first build, 2026-10-22).
_PER_SHARE_AFTER = re.compile(
    r"^\s*(?:(?:per|an?|each)\s+(?:(?:basic|diluted|common|ordinary|and)\s+){0,4}share\b"
    r"|/\s*(?:diluted\s+)?share\b)",
    re.IGNORECASE,
)
_RATIO_BEFORE = re.compile(
    r"(?:(?:average|mean|median|typical)\s+(?:annual\s+|hourly\s+|base\s+|weekly\s+)?"
    r"(?:pay|wages?|salary|compensation|earnings)|hourly\s+(?:wage|pay|rate)|wage\s+rate"
    r"|\bper\s+(?:employee|worker|person|head|hour|capita))"
    r"\s*(?:per\s+\w+\s+)?(?:of|is|was|were|averaged|at|:)?\s*$",
    re.IGNORECASE,
)
_PAY_WORDS = re.compile(
    r"\b(?:payroll|wages?|salar(?:y|ies)|compensation|labou?r\s+costs?|pay)\b", re.IGNORECASE
)
_UNIT_MULTIPLIER = {
    "thousand": 1_000, "k": 1_000, "million": 1_000_000, "mm": 1_000_000, "m": 1_000_000,
    "billion": 1_000_000_000, "bn": 1_000_000_000, "b": 1_000_000_000, "trillion": 10**12,
}  # fmt: skip


@dataclass(frozen=True)
class Flag:
    kind: str
    line: int
    text: str


@dataclass
class Transformed:
    text: str
    flags: list[Flag] = field(default_factory=list)
    pay_checks: list[PayCheck] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)

    def record(self) -> dict[str, object]:
        return {
            "counts": dict(sorted(self.counts.items())),
            "flags": [{"kind": f.kind, "line": f.line, "text": f.text} for f in self.flags],
            "pay_checks": [c.record() for c in self.pay_checks],
        }


def _line_of(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1


def _same_line(text: str, start: int, end: int, before: int = 60, after: int = 40) -> str:
    lo = max(0, start - before)
    hi = min(len(text), end + after)
    window = text[lo:hi]
    anchor = start - lo
    left = window.rfind("\n", 0, anchor) + 1
    right = window.find("\n", anchor)
    return window[left : right if right != -1 else len(window)]


def transform(text: str, *, calendar: d.FiscalCalendar, factor: float) -> Transformed:
    """Relative dates, scaled dollars and headcounts, and flags, in one pass over ``text``."""
    result = Transformed(text="")
    pay_by_line: dict[int, list[tuple[Decimal, Decimal]]] = {}
    heads_by_line: dict[int, list[tuple[int, int | None]]] = {}

    def count(name: str) -> None:
        result.counts[name] = result.counts.get(name, 0) + 1

    def flag(kind: str, match: re.Match[str]) -> None:
        result.flags.append(Flag(kind, _line_of(text, match.start()), match.group(0)))

    def date_in(snippet: str) -> date | None:
        try:
            return d.parse_date(snippet)
        except d.DateError:
            return None

    def year_reading(year: int, match: re.Match[str]) -> str:
        if not calendar.december:
            flag(
                "fiscal-year convention assumed: read as the year ending in that calendar year",
                match,
            )
        return calendar.year_ending_in(year)

    def replace(match: re.Match[str]) -> str:
        kind = match.lastgroup
        whole = match.group(0)
        if kind == "ended":
            found = re.search(d.DATE, whole)
            when = date_in(found.group(0)) if found else None
            if when is None:
                flag("date that is not a real date", match)
                return whole
            count("date")
            if re.search(r"period\s+end", whole, re.IGNORECASE):
                return calendar.label(when)  # a period of any length: the day itself
            offset, quarter = calendar.locate_period_end(when)
            if re.search(r"year\s+end", whole, re.IGNORECASE):
                return calendar.year_label(offset)
            stated = match.group("e_ordinal")
            if stated is not None and d.quarter_number(stated) != quarter:
                flag("quarter named does not match its end date: check it", match)
            return f"{calendar.year_label(offset)}, {d.quarter_word(quarter)} quarter"
        if kind == "date":
            when = date_in(whole)
            if when is None:
                flag("date that is not a real date", match)
                return whole
            count("date")
            return calendar.label(when)
        if kind == "quarter":
            quarter, year = d.quarter_year(whole)
            count("date")
            return f"{year_reading(year, match)}, {d.quarter_word(quarter)} quarter"
        if kind == "fiscal":
            count("date")
            return year_reading(d.year_in(whole), match)
        if kind == "year":
            count("date")
            return year_reading(int(whole), match)
        if kind == "monthday":
            flag("date without a year: not relative-able", match)
            return whole
        if kind in ("pct", "duration", "struct", "form", "ordinal", "relative"):
            return whole
        if kind == "dollar":
            return _dollar(match)
        if kind in ("heads", "heads2"):
            return _heads(match, kind)
        if kind == "shares":
            flag("share count: remove it (§4.8)", match)
            return whole
        if kind == "words":
            flag("headcount in words: scale and write it by hand", match)
            return whole
        if kind == "volume":
            flag("unit volume: not scaled, decide in the search half (§10)", match)
            return whole
        flag("unclassified number", match)
        return whole

    def _dollar(match: re.Match[str]) -> str:
        whole = match.group(0)
        after = text[match.end() : match.end() + 40]
        before = text[max(0, match.start() - 60) : match.start()]
        if _PER_SHARE_AFTER.match(after):
            flag("per-share figure: remove it (§4.8)", match)
            return whole
        if _RATIO_AFTER.match(after) or _RATIO_BEFORE.search(before):
            count("dollar_ratio_unscaled")
            return whole
        number = Decimal(match.group("d_num").replace(",", ""))
        scaled = scale_dollars(number, factor)
        unit = (match.group("d_unit") or "").lower()
        start, end = match.span("d_num")
        out = whole[: start - match.start()] + format_number(scaled) + whole[end - match.start() :]
        count("dollar")
        if _PAY_WORDS.search(_same_line(text, match.start(), match.end())):
            multiplier = Decimal(_UNIT_MULTIPLIER.get(unit, 1))
            line = _line_of(text, match.start())
            pay_by_line.setdefault(line, []).append((number * multiplier, scaled * multiplier))
        return out

    def _heads(match: re.Match[str], kind: str) -> str:
        number_group = "h_num" if kind == "heads" else "h2_num"
        heads = int(match.group(number_group).replace(",", ""))
        scaled = scale_heads(heads, factor)
        count("headcount")
        line = _line_of(text, match.start())
        heads_by_line.setdefault(line, []).append((heads, scaled.value))
        if kind == "heads":
            hedge = match.group("h_hedge") or ""
            return f"{hedge}{scaled.text}" if scaled.value is not None else scaled.text
        hedge = match.group("h2_hedge") or ""
        if (
            scaled.value is None
        ):  # "employs approximately fewer than 100" reads wrong; the hedge goes
            hedge = ""
        return f"{match.group('h2_pre')}{hedge}{scaled.text}"

    result.text = _PATTERN.sub(replace, text)

    for line in sorted(set(pay_by_line) & set(heads_by_line)):
        pays, heads = pay_by_line[line], heads_by_line[line]
        if len(pays) == 1 and len(heads) == 1:
            (pay_before, pay_after), (heads_before, heads_after) = pays[0], heads[0]
            result.pay_checks.append(
                check_pay_per_head(
                    PayFigure(line, pay_before, pay_after, heads_before, heads_after)
                )
            )
        else:
            result.pay_checks.append(
                PayCheck(
                    line,
                    None,
                    None,
                    None,
                    True,
                    "several pay or headcount figures on this line: check by hand",
                )
            )
            result.flags.append(
                Flag("pay per head not checked: several figures on one line", line, "")
            )
    return result
