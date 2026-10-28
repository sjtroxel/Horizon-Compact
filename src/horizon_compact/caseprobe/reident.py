"""``hc case reident``: the re-identification check of a frozen case's dossier (Phase 5.5 IMPLEMENTATION doc
§5.5, K5; protocol §12.11). No model call, and no run is read.

Scaling hides sizes, not shapes: one factor multiplies every dollar figure, so the ratios between them
survive to rounding (§3 finding 9). The **figure half** rebuilds the dossier's own dollars from the case's
``build.json`` (the raw XBRL value, as ``figures.py`` renders it, times the case's factor, to three
significant digits: ``scale.py``'s own functions), forms the ratios the factor cancels out of (revenue
growth between consecutive years, operating margin and operating cash flow over revenue, each year; at most
eight), and gives each one the interval its rounding allows. It then compares every filer in SEC's XBRL
frames for the same periods against those intervals. The case's own filer must be found in the frames and
match (else the check cannot confirm the case and the dossier is withheld); the dossier is withheld too if
fewer than 20 filers, the case's own included, match every ratio. Only a positive match counts: a filer
missing a value a ratio needs is not a match.

**The description half** runs only after a passed figure half. The command writes a private template
(``reident-search.toml`` in the case's folder): the overview's first sentence, and three empty slots for
distinctive phrases of the situation section. He searches each as written, fills in the engine, the date and
whether the company is on the first page, and runs the command again. Any ``true`` withholds the dossier;
the first sentence and every filled slot answered ``false`` passes it; anything less is pending, and nothing
public is written.

**What is written.** Privately, once, in the case's folder: ``reident-record.json`` (the ratios and their
intervals, every frame used with its URL, hash and fetch time, who matched, what was dropped and why); a
rerun recomputes it from the cached frames and refuses if it differs. Publicly, once, by a link:
``experiment/results/cases/<label>/reident.json``: the label, ``exploratory``, the status, one of three
fixed reasons, the threshold and provenance by hash only. **No count, CIK, name, ticker, year, period or
frame URL** (a URL holds the year) goes into it. What the command prints is the status, the number of ratios
used, the matching count and whether the case's own filer was confirmed; never a name, CIK, ticker or URL.

**Limits, all recorded.** Every figure is assumed stated in the dossier at its full three significant digits
(an attacker with less would match more filers, so this errs toward withholding). A coarsened case (probe
set 2) states its figures to two significant digits (protocol §12.8), rounded by hand from the three-digit
ones, so each is checked at that two-digit figure with both roundings' half-units (Opus's review). There is no
headcount frame (``dei/EntityNumberOfEmployees`` is a 404), so per-employee figures are not compared. A
frame's revenue is the first tag, in ``figures.LINES``' order, with a row for the filer.

Imports nothing that needs scipy.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tomllib
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from fractions import Fraction
from itertools import pairwise
from pathlib import Path
from typing import Any

from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.assemble import HEADINGS
from horizon_compact.casebuild.edgar import EdgarClient, EdgarNotFound
from horizon_compact.casebuild.figures import LINES, _dollars
from horizon_compact.casebuild.scale import round_significant, scale_dollars
from horizon_compact.caseprobe.session import check_frozen
from horizon_compact.protocol.cases import CaseError, read_case
from horizon_compact.sweep.plan import SweepRefusal

RECORD_VERSION = 1
PUBLIC_VERSION = 1
THRESHOLD = 20
FRAMES_HOST = "https://data.sec.gov/api/xbrl/frames/us-gaap"
PUBLIC_DIR = Path("experiment") / "results" / "cases"
RECORD_FILE = "reident-record.json"
SEARCH_FILE = "reident-search.toml"
SEARCH_SLOTS = 4  # the overview's first sentence, and three phrases of the situation section

PASSED = "passed"
WITHHELD = "withheld"
PENDING = "pending"
# The three reasons, word for word: nothing else (no count, no name) goes into the public file.
REASON_UNCONFIRMED = (
    "withheld: the re-identification check could not confirm the case in SEC's structured data"
)
REASON_FEW = "withheld: its scale-free figures match fewer than 20 filers in SEC's structured data"
REASON_SEARCH = "withheld: its description found the company in a web search"

OVERVIEW, SITUATION = 1, 6  # the dossier's sections, by number (assemble.HEADINGS)
GROWTH, MARGIN, CASH_FLOW = "revenue_growth", "operating_margin", "cash_flow_over_revenue"
ASSUMPTIONS = (
    "every figure is taken as stated in the dossier at three significant digits (an attacker with less "
    "matches more filers: errs toward withholding)",
    "per-employee figures are not compared: SEC publishes no headcount frame (dei/EntityNumberOfEmployees "
    "returned 404)",
)
COARSENED = (
    "probe set above 1: each figure is taken as the coarsened dossier states it, the three-digit figure "
    "rounded to two significant digits (protocol 12.8); its interval is both roundings' half-units plus "
    "the rendering's"
)

_MILLION = Decimal(1_000_000)
_STATED = re.compile(r"(?P<sign>-?)\$(?P<number>[\d,]+(?:\.\d+)?)(?P<million> million)?")
_ABBREVIATIONS = frozenset({"inc", "corp", "co", "ltd", "llc", "no", "st", "mr", "mrs", "dr", "vs"})
_INITIALS = re.compile(r"(?:[A-Za-z]\.)+[A-Za-z]|[A-Z]")


class ReidentRefused(SweepRefusal):
    """The check cannot run, or its record cannot be trusted. The message holds a kind of failure and a file
    name, never a figure, a name or a CIK. A ``SweepRefusal`` so ``cli.py`` catches it by that name."""


# --- intervals ---------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Interval:
    """A closed interval of exact rationals."""

    lo: Fraction
    hi: Fraction

    def contains(self, x: Fraction) -> bool:
        return self.lo <= x <= self.hi

    @property
    def has_zero(self) -> bool:
        return self.lo <= 0 <= self.hi


def divide(numerator: Interval, denominator: Interval) -> Interval | None:
    """The quotient's interval; None when the denominator's holds zero. With zero out, each corner is an
    extreme, signs and all."""
    if denominator.has_zero:
        return None
    corners = [
        n / d for n in (numerator.lo, numerator.hi) for d in (denominator.lo, denominator.hi)
    ]
    return Interval(min(corners), max(corners))


def stated_interval(value: float, factor: float, *, coarsened: bool = False) -> Interval:
    """The dollars in which the true scaled value of a raw XBRL ``value`` lies, given the dossier states it at
    three significant digits.

    The dossier's number is ``scale_dollars`` of the figure as ``figures.py`` renders it (to $0.1 million, or
    whole dollars under $1 million), so the interval is the stated number plus or minus half a unit of its
    third digit (the rounding's own interval) and, wider, that rendering's half-unit times the factor: the
    true value went through both. A ``coarsened`` dossier (probe set 2) states that three-digit number rounded
    again to two digits, by hand: the interval is centred on the two-digit number and widened by its half-unit
    too (a rounding of a rounding can land more than one half-unit away: 1,545 goes to 1,550, then 1,600).
    """
    found = _STATED.fullmatch(_dollars(value))
    if found is None:
        raise ReidentRefused(
            "a dollar figure of build.json does not render the way the dossier's text does"
        )
    number = Decimal(found["number"].replace(",", ""))
    unit, rendering = (
        (_MILLION, Decimal("0.05")) if found["million"] else (Decimal(1), Decimal("0.5"))
    )
    scaled = scale_dollars(number, factor)
    third_digit = Decimal(1).scaleb(scaled.adjusted() - 2) / 2 if scaled else Decimal(0)
    width = third_digit + rendering * Decimal(repr(factor))
    if coarsened:
        scaled = round_significant(scaled, 2)
        width += Decimal(1).scaleb(scaled.adjusted() - 1) / 2 if scaled else Decimal(0)
    width *= unit
    centre = scaled * unit * (-1 if found["sign"] else 1)
    return Interval(Fraction(centre - width), Fraction(centre + width))


# --- the ratios --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Ratio:
    kind: str
    ends: tuple[date, ...]  # growth: (later, earlier); the others: the one year
    interval: Interval

    def record(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "ends": [end.isoformat() for end in self.ends],
            "low": float(self.interval.lo),
            "high": float(self.interval.hi),
        }


def _figures_of(build: dict[str, Any]) -> dict[str, Any]:
    figures = build.get("section_inputs", {}).get("figures")
    if not isinstance(figures, dict):
        raise ReidentRefused("build.json holds no figures record")
    return figures


def _line_values(figures: dict[str, Any], name: str) -> dict[date, float]:
    try:
        line = figures["lines"].get(name)
        if line is None:
            return {}
        values = {date.fromisoformat(end): year["value"] for end, year in line["years"].items()}
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise ReidentRefused("build.json's figures cannot be read") from exc
    if not all(isinstance(v, int | float) and not isinstance(v, bool) for v in values.values()):
        raise ReidentRefused("build.json's figures cannot be read")
    return values


def year_ends(build: dict[str, Any]) -> list[date]:
    try:
        return [date.fromisoformat(end) for end in _figures_of(build)["year_ends"]]
    except (KeyError, TypeError, ValueError) as exc:
        raise ReidentRefused("build.json's fiscal year ends cannot be read") from exc


def build_ratios(
    build: dict[str, Any], *, coarsened: bool = False
) -> tuple[list[Ratio], list[dict[str, Any]]]:
    """The ratios the dossier's figures allow, and the ones dropped with the reason: a line or year build.json
    lacks, or a denominator whose interval holds zero."""
    figures, ends = _figures_of(build), year_ends(build)
    try:
        factor = float(build["factor"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ReidentRefused("build.json holds no factor") from exc
    if not factor > 0:
        raise ReidentRefused("build.json's factor is not positive")
    stated = {
        name: {
            end: stated_interval(v, factor, coarsened=coarsened)
            for end, v in _line_values(figures, name).items()
        }
        for name in ("revenue", "operating_income", "operating_cash_flow")
    }
    ratios: list[Ratio] = []
    dropped: list[dict[str, Any]] = []

    def add(
        kind: str, years: tuple[date, ...], num: tuple[str, date], den: tuple[str, date]
    ) -> None:
        where = [e.isoformat() for e in years]
        parts = [stated[name].get(end) for name, end in (num, den)]
        if parts[0] is None or parts[1] is None:
            dropped.append(
                {"kind": kind, "ends": where, "why": "a figure it needs is not in build.json"}
            )
            return
        quotient = divide(parts[0], parts[1])
        if quotient is None:
            dropped.append(
                {"kind": kind, "ends": where, "why": "the denominator's interval holds zero"}
            )
            return
        if kind == GROWTH:
            quotient = Interval(quotient.lo - 1, quotient.hi - 1)
        ratios.append(Ratio(kind, years, quotient))

    for later, earlier in pairwise(ends):
        add(GROWTH, (later, earlier), ("revenue", later), ("revenue", earlier))
    for end in ends:
        add(MARGIN, (end,), ("operating_income", end), ("revenue", end))
    for end in ends:
        add(CASH_FLOW, (end,), ("operating_cash_flow", end), ("revenue", end))
    return ratios, dropped


# --- SEC's frames ------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class FrameRow:
    end: date
    value: Fraction


@dataclass(frozen=True)
class Frame:
    tag: str
    year: int
    url: str
    sha256: str | None  # None: SEC has no such frame (404)
    fetched_at: str | None
    rows: dict[int, FrameRow]  # by CIK

    def record(self) -> dict[str, Any]:
        return {
            "tag": self.tag,
            "year": self.year,
            "url": self.url,
            "found": self.sha256 is not None,
            "sha256": self.sha256,
            "fetched_at": self.fetched_at,
            "filers": len(self.rows),
        }


def frame_url(tag: str, year: int) -> str:
    return f"{FRAMES_HOST}/{tag}/USD/CY{year}.json"


def _parse_frame(tag: str, year: int, body: bytes) -> dict[int, FrameRow]:
    rows: dict[int, FrameRow] = {}
    try:
        for row in json.loads(body)["data"]:
            cik, end, value = row["cik"], date.fromisoformat(row["end"]), row["val"]
            if isinstance(cik, bool) or not isinstance(cik, int) or isinstance(value, bool):
                raise TypeError("cik or val")
            if cik in rows:
                raise ValueError("a filer twice")
            rows[cik] = FrameRow(end, Fraction(str(value)))
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise ReidentRefused(f"a frame of {tag} is not shaped as expected") from exc
    return rows


class FrameBook:
    """The frames asked for so far, each fetched once (the client also caches them in the case's folder)."""

    def __init__(self, sec: EdgarClient) -> None:
        self._sec = sec
        self._frames: dict[tuple[str, int], Frame] = {}

    def get(self, tag: str, year: int) -> Frame:
        key = (tag, year)
        if key not in self._frames:
            url = frame_url(tag, year)
            try:
                document = self._sec.get(url)
            except EdgarNotFound:
                self._frames[key] = Frame(tag, year, url, None, None, {})
            else:
                rows = _parse_frame(tag, year, document.body)
                self._frames[key] = Frame(
                    tag, year, url, document.sha256, document.fetched_at, rows
                )
        return self._frames[key]

    def records(self) -> list[dict[str, Any]]:
        return [frame.record() for frame in self._frames.values()]


def _tags(line: str) -> tuple[str, ...]:
    return next(spec.tags for spec in LINES if spec.name == line)


def locate(book: FrameBook, tag: str, end: date, cik: int) -> int | None:
    """The calendar-year frame that holds the filer's row for the fiscal year ending ``end``. A CY frame is
    the closest calendar fit, not the December year (a June year end can sit in the frame before or after), so
    the three nearest are asked for in turn, the first only if it does not hold it."""
    for year in (end.year, end.year - 1, end.year + 1):
        row = book.get(tag, year).rows.get(cik)
        if row is not None and row.end == end:
            return year
    return None


@dataclass
class YearFrames:
    """Every filer's three lines in the frames of one fiscal year."""

    revenue: dict[int, FrameRow]
    operating_income: dict[int, FrameRow]
    operating_cash_flow: dict[int, FrameRow]


def _year_frames(book: FrameBook, year: int, ratios: list[Ratio], end: date) -> YearFrames:
    revenue: dict[int, FrameRow] = {}
    for tag in _tags("revenue"):  # the first tag, in order, with a row for the filer
        for cik, row in book.get(tag, year).rows.items():
            revenue.setdefault(cik, row)
    needs = {r.kind for r in ratios if end in r.ends}
    income = book.get(_tags("operating_income")[0], year).rows if MARGIN in needs else {}
    cash = book.get(_tags("operating_cash_flow")[0], year).rows if CASH_FLOW in needs else {}
    return YearFrames(revenue, income, cash)


def _ratio_of(ratio: Ratio, cik: int, data: dict[date, YearFrames]) -> Fraction | None:
    """The filer's value of the ratio; None if a value it needs is missing or its denominator is zero."""
    if ratio.kind == GROWTH:
        later, earlier = (data[end].revenue.get(cik) for end in ratio.ends)
        if later is None or earlier is None or earlier.value == 0:
            return None
        return later.value / earlier.value - 1
    year = data[ratio.ends[0]]
    top = (year.operating_income if ratio.kind == MARGIN else year.operating_cash_flow).get(cik)
    bottom = year.revenue.get(cik)
    if top is None or bottom is None or top.end != bottom.end or bottom.value == 0:
        return None
    return top.value / bottom.value


def matches(ratios: list[Ratio], cik: int, data: dict[date, YearFrames]) -> bool:
    for ratio in ratios:
        value = _ratio_of(ratio, cik, data)
        if value is None or not ratio.interval.contains(value):
            return False
    return True


@dataclass(frozen=True)
class FigureHalf:
    record: dict[str, Any]
    ratios_used: int
    own_found: bool
    own_matched: bool
    matching: int | None  # None: the own filer was not found, so no year was compared

    @property
    def reason(self) -> str | None:
        """Why the figure half withholds the dossier, or None if it passes."""
        if not (self.ratios_used and self.own_found and self.own_matched):
            return REASON_UNCONFIRMED
        if self.matching is None or self.matching < THRESHOLD:
            return REASON_FEW
        return None


def figure_half(
    sec: EdgarClient, *, cik: int, build: dict[str, Any], probe_set: int = 1
) -> FigureHalf:
    ratios, dropped = build_ratios(build, coarsened=probe_set > 1)
    book = FrameBook(sec)
    needed = sorted({end for r in ratios for end in r.ends}, reverse=True)
    revenue_tag = _line_tag(build, "revenue")
    located: dict[date, int] = {}
    missing: list[date] = []
    if ratios:
        for end in needed:
            year = locate(book, revenue_tag, end, cik)
            if year is None:
                missing.append(end)
                break
            located[end] = year
    own_found = bool(ratios) and not missing
    matching: list[int] | None = None
    if own_found:
        data = {end: _year_frames(book, located[end], ratios, end) for end in needed}
        candidates = sorted({c for d in data.values() for c in d.revenue})
        matching = [c for c in candidates if matches(ratios, c, data)]
    record: dict[str, Any] = {
        "record_version": RECORD_VERSION,
        "probe_set": probe_set,
        "assumptions": [*ASSUMPTIONS, *([COARSENED] if probe_set > 1 else [])],
        "ratios": [r.record() for r in ratios],
        "dropped": dropped,
        "frames": book.records(),
        "fiscal_year_frames": {end.isoformat(): located[end] for end in sorted(located)},
        "own": {
            "found": own_found,
            "not_found_for": [end.isoformat() for end in missing],
            "matched": None if matching is None else cik in matching,
        },
        "matching": None if matching is None else {"count": len(matching), "ciks": matching},
    }
    return FigureHalf(
        record,
        len(ratios),
        own_found,
        matching is not None and cik in matching,
        None if matching is None else len(matching),
    )


def _line_tag(build: dict[str, Any], name: str) -> str:
    """The tag the case's own figures used. Another tag than the line's list would not be an attacker's."""
    try:
        tag = _figures_of(build)["lines"][name]["tag"]
    except (KeyError, TypeError):
        return _tags(name)[0]  # no such line: no ratio needs it, so it is never asked for
    if tag not in _tags(name):
        raise ReidentRefused(
            f"build.json's {name} tag is not one of the tags the case builder tries"
        )
    return str(tag)


# --- the description half ----------------------------------------------------------------------------------


def split_sections(text: str) -> dict[int, str]:
    """The dossier's sections by number, each without its heading."""
    marks = sorted(
        (m.start(), m.end(), number)
        for number, heading in HEADINGS.items()
        if (m := re.search(rf"^{re.escape(heading)}[ \t]*$", text, flags=re.MULTILINE))
    )
    ends = [start for start, _, _ in marks[1:]] + [len(text)]
    return {
        number: text[end:stop].strip() for (_, end, number), stop in zip(marks, ends, strict=True)
    }


def _flat(text: str) -> str:
    return " ".join(text.split())


def first_sentence(text: str) -> str:
    """The text up to its first full stop that is not an abbreviation ("U.S.", "Inc.", an initial). He may
    shorten or lengthen the query in his template: it need only stay the start of the overview."""
    flat = _flat(text)
    for mark in re.finditer(r"[.!?](?=\s|$)", flat):
        word = flat[: mark.start()].rsplit(" ", 1)[-1].strip("\"'(")
        if word.lower() in _ABBREVIATIONS or _INITIALS.fullmatch(word):
            continue
        return flat[: mark.end()]
    return flat


def search_template(label: str, dossier_sha256: str, overview: str) -> str:
    slot = (
        '[[search]]\nquery = {query}\nengine = ""\nsearched_on = ""\n'
        "# company_on_first_page = false\n"
    )
    lines = [
        "# The re-identification check's description half (Phase 5.5 K5; protocol 12.11). Private.",
        "# Search each query as written in a web search engine. For each, fill in engine and searched_on, and",
        "# uncomment company_on_first_page: true if the company is on the first page of results, else false.",
        "# Query 1 is the overview's first sentence (shorten or lengthen it, but it must stay the start of the",
        "# overview). Queries 2 to 4 are distinctive phrases of the situation section, as written there; leave",
        "# a slot's query empty to skip it. Then run the command again.",
        f"case = {json.dumps(label)}",
        f"dossier_sha256 = {json.dumps(dossier_sha256)}",
        "",
        slot.format(query=json.dumps(first_sentence(overview))),
        *[slot.format(query='""')] * (SEARCH_SLOTS - 1),
    ]
    return "\n".join(lines)


@dataclass(frozen=True)
class SearchState:
    status: str  # PASSED, WITHHELD or PENDING
    note: str


def read_search(
    text: str, *, label: str, dossier_sha256: str, overview: str, situation: str
) -> SearchState:
    """His filled-in template. Refuses a file that is not this case's or whose queries are not as written in
    the dossier; any ``true`` withholds, even beside unanswered entries."""
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ReidentRefused(f"{SEARCH_FILE} is not valid TOML") from exc
    if data.get("case") != label or data.get("dossier_sha256") != dossier_sha256:
        raise ReidentRefused(f"{SEARCH_FILE} is not this case's, or not for this dossier")
    entries = data.get("search")
    if not (isinstance(entries, list) and 1 <= len(entries) <= SEARCH_SLOTS):
        raise ReidentRefused(f"{SEARCH_FILE} needs one to {SEARCH_SLOTS} [[search]] entries")
    answered: list[bool] = []  # per filled entry: whether it is answered, and then what it said
    found: list[bool] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or set(entry) - {
            "query",
            "engine",
            "searched_on",
            "company_on_first_page",
        }:
            raise ReidentRefused(f"{SEARCH_FILE} entry {index + 1} has keys this form does not")
        query, engine, day = (
            entry.get("query"),
            entry.get("engine", ""),
            entry.get("searched_on", ""),
        )
        seen = entry.get("company_on_first_page")
        if not (isinstance(query, str) and isinstance(engine, str) and isinstance(day, str)):
            raise ReidentRefused(f"{SEARCH_FILE} entry {index + 1} has a value of the wrong type")
        if seen is not None and not isinstance(seen, bool):
            raise ReidentRefused(
                f"{SEARCH_FILE} entry {index + 1}: company_on_first_page is true or false"
            )
        if not query.strip():
            if index == 0:
                raise ReidentRefused(f"{SEARCH_FILE}: query 1 may not be empty")
            if engine.strip() or day.strip() or seen is not None:
                raise ReidentRefused(f"{SEARCH_FILE} entry {index + 1} has an answer but no query")
            continue
        if index == 0:
            if not _flat(overview).startswith(_flat(query)):
                raise ReidentRefused(f"{SEARCH_FILE}: query 1 is not the start of the overview")
        elif _flat(query) not in _flat(situation):
            raise ReidentRefused(
                f"{SEARCH_FILE}: query {index + 1} is not as written in the situation section"
            )
        answered.append(bool(engine.strip() and day.strip() and seen is not None))
        found.append(seen is True)
    if any(found):
        return SearchState(WITHHELD, "the company appeared on a first page")
    if all(
        answered
    ):  # query 1 is always filled, so this is "query 1 and every filled slot answered false"
        return SearchState(PASSED, "every query answered: not on a first page")
    unanswered = answered.count(False)
    return SearchState(
        PENDING, f"{unanswered} filled query(ies) still need an engine, a date and an answer"
    )


# --- the case ----------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class FrozenCase:
    label: str
    probe_set: int
    cik: int
    build: dict[str, Any]
    build_sha256: str
    dossier_sha256: str
    overview: str
    situation: str


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def public_path(root: Path, label: str) -> Path:
    return root / PUBLIC_DIR / label / "reident.json"


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_bytes())
    except (OSError, ValueError):
        return None


def load_frozen(root: Path, case: CaseAppendix) -> FrozenCase:
    """The frozen case as the appendix holds it, refused (with every reason found) unless it is in the freeze,
    its dossier hashes to ``case.lock``, ``build.json`` is the case's and the case's CIK can be read."""
    label = case.label
    reasons: list[str] = []
    try:
        record = read_case(root, label)
    except (CaseError, ValueError) as exc:
        raise ReidentRefused(str(exc)) from exc
    reasons += check_frozen(root, label, record)
    dossier_path = case.dossier_path_for(record.probe_set)
    try:
        dossier = dossier_path.read_bytes()
    except OSError:
        dossier = b""
        reasons.append(f"the case's dossier cannot be read ({dossier_path.name})")
    dossier_sha256 = _sha256(dossier)
    if dossier and dossier_sha256 != record.dossier_sha256:
        reasons.append("the dossier in the appendix does not hash to case.lock")
    build = _read_json(case.build_path)
    if not isinstance(build, dict) or build.get("label") != label:
        reasons.append(f"{case.build_path.name} cannot be read as this case's build record")
        build = {}
    sources = _read_json(case.sources_path)
    cik = sources.get("cik") if isinstance(sources, dict) else None
    if not (isinstance(cik, str) and re.fullmatch(r"\d{1,10}", cik)):
        reasons.append(f"{case.sources_path.name} holds no CIK for the case")
    overview = situation = ""
    try:
        sections = split_sections(tomllib.loads(dossier.decode("utf-8"))["text"])
        overview, situation = sections[OVERVIEW], sections[SITUATION]
    except (UnicodeDecodeError, tomllib.TOMLDecodeError, KeyError, TypeError):
        if dossier:
            reasons.append("the dossier has no overview or no situation section to search by")
    if reasons:
        raise ReidentRefused("\n".join(dict.fromkeys(reasons)))
    assert isinstance(cik, str)
    return FrozenCase(
        label,
        record.probe_set,
        int(cik),
        build,
        _sha256(case.build_path.read_bytes()),
        dossier_sha256,
        overview,
        situation,
    )


# --- the command -------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ReidentResult:
    status: str
    ratios_used: int
    matching: int | None
    own_confirmed: bool
    public: Path | None  # the public file, when this run wrote it
    template: Path | None  # the description half's template, when this run wrote it
    note: str


def _dump(record: dict[str, Any]) -> bytes:
    return (json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def _keep_record(case: CaseAppendix, record: dict[str, Any]) -> str:
    """The figure half's record, written once; a rerun recomputes it from the cached frames and refuses unless
    it is the same. Returns its sha256."""
    path = case.directory / RECORD_FILE
    data = _dump(record)
    if not path.exists():
        case.write_once(path, data)
        return _sha256(data)
    stored = path.read_bytes()
    if _read_json(path) != json.loads(data):
        raise ReidentRefused(
            f"{path.name} differs from what this run found: the frames or build.json changed since the "
            "first run; look before going on"
        )
    return _sha256(stored)


def _write_public(path: Path, record: dict[str, Any]) -> None:
    """Written beside itself and linked into place: an existing file (or a second command racing this one) is
    refused and never replaced."""
    text = json.dumps(record, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    try:
        os.link(temporary, path)
    except FileExistsError as exc:
        raise ReidentRefused(f"{path.name} exists: it is never overwritten") from exc
    finally:
        temporary.unlink(missing_ok=True)


def run_reident(
    root: Path, label: str, *, appendix: Path, head: str, sec: EdgarClient
) -> ReidentResult:
    case = CaseAppendix(appendix, label)
    public = public_path(root, label)
    if public.exists():
        raise ReidentRefused(
            f"{public.relative_to(root).as_posix()} exists: it is never overwritten (delete it, "
            "uncommitted, to go on from the records)"
        )
    frozen = load_frozen(root, case)
    half = figure_half(sec, cik=frozen.cik, build=frozen.build, probe_set=frozen.probe_set)
    record_sha256 = _keep_record(case, half.record)
    own_confirmed = half.own_found and half.own_matched

    def finish(
        status: str, reason: str | None, search_sha256: str | None, note: str
    ) -> ReidentResult:
        _write_public(
            public,
            {
                "reident_version": PUBLIC_VERSION,
                "case": label,
                "exploratory": True,
                "status": status,
                "reason": reason,
                "threshold": THRESHOLD,
                "provenance": {
                    "head": head,
                    "build_sha256": frozen.build_sha256,
                    "dossier_sha256": frozen.dossier_sha256,
                    "record_sha256": record_sha256,
                    "search_sha256": search_sha256,
                },
            },
        )
        return ReidentResult(
            status, half.ratios_used, half.matching, own_confirmed, public, None, note
        )

    reason = half.reason
    if reason is not None:
        return finish(WITHHELD, reason, None, "the figure half withholds it")

    path = case.directory / SEARCH_FILE
    if not path.exists():
        case.write_once(
            path, search_template(label, frozen.dossier_sha256, frozen.overview).encode("utf-8")
        )
        note = "the figure half passed; the description half's template is written (see below)"
        return ReidentResult(
            PENDING, half.ratios_used, half.matching, own_confirmed, None, path, note
        )
    data = path.read_bytes()
    state = read_search(
        data.decode("utf-8", errors="replace"),
        label=label,
        dossier_sha256=frozen.dossier_sha256,
        overview=frozen.overview,
        situation=frozen.situation,
    )
    if state.status == PENDING:
        return ReidentResult(
            PENDING, half.ratios_used, half.matching, own_confirmed, None, None, state.note
        )
    return finish(
        state.status,
        REASON_SEARCH if state.status == WITHHELD else None,
        _sha256(data),
        state.note,
    )
