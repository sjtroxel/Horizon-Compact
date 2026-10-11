"""The search runner and the selection log (IMPLEMENTATION §4.11, protocol §12.2-12.4).

**The queries are data, copied from protocol §12.3's table and run as written** (a test reads the table and
compares). Each query is run separately and every page of its results is read; a filing found twice counts
once; the filters on ``form``, ``items``, ``sics`` and ``file_date`` are applied here, in code, never by a
person. The fallback month's hits (filed from 2026-07-01 to 2026-07-31) are held apart from the window's
(from 2026-08-01) and never mixed into one list (§12.2).

The output is the candidate list, per type, in order of filing date then accession number. **That is not yet
first-disclosure order**: a decision is dated by its first public disclosure, never its filing date (§12.2),
and finding that date is the first check on each candidate, done by a person. The list is where the checks
start.

**The endpoint's reply shape is not verified.** §12.3's live check on 2026-10-09 covered the query syntax
and parameters, not the reply. This module reads ``hits.total.value`` and ``hits.hits[]._source`` with
``adsh``, ``form``, ``file_date``, ``items``, ``sics``, ``ciks`` and ``display_names`` (the accession number
may instead be the front of ``_id``), as the SEC's search page has returned them. Anything missing or of
another shape raises: nothing is guessed. One read-only request, before the rule date, settles it (as step 1
did for the submissions and company-facts files).

The selection log (``SelectionLog``) is one row per candidate, with the criteria of §12.4 in order, each
passed or failed with its reason. A person records the results; the code enforces the order (no skipping,
nothing after a failure) and that every rejection on criterion 3, 4 or 5 has an independent read, with a
resolution when the reader disagreed. Its **public view is by case type and carries no name, accession
number, date or industry code**: a row's neutral number, its pool, each criterion's result and the reason
only where a person wrote a separate ``public_reason`` for publication.

Nothing here makes a request except through the ``EdgarClient`` it is given, so a test serves fake replies
and fails on any other.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any
from urllib.parse import urlencode

from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.cutoff import CutoffError, parse_date
from horizon_compact.casebuild.edgar import EdgarClient

EFTS_URL = "https://efts.sec.gov/LATEST/search-index"
WINDOW_START = date(2026, 8, 1)  # protocol §12.2
FALLBACK_START = date(2026, 7, 1)  # the month after the latest cutoff, held apart
FORM = "8-K"
MANUFACTURING = (2000, 3999)
MAX_RESULTS = 10_000  # the most a query can be paged through; more is a deviation to report
TYPES = ("closure", "retool", "ai")
POOLS = ("window", "fallback")


class SearchError(Exception):
    """The endpoint answered in a shape this module does not know, or a query cannot be read to the end."""


@dataclass(frozen=True)
class Query:
    channel: int
    type: str
    text: str  # exactly as protocol §12.3 writes it, quotes included
    items_any: tuple[str, ...]  # the hit's items must include one of these; empty means any
    sic_range: (
        tuple[int, int] | None
    )  # the hit's sics must include one in this range; None means any


def _queries() -> tuple[Query, ...]:
    retool = (
        '"new manufacturing facility"',
        '"new production facility"',
        '"expand production"',
        '"expansion of our manufacturing"',
        '"capacity expansion"',
        '"retool"',
    )
    ai = (
        '"artificial intelligence" "reduction in force"',
        '"artificial intelligence" "workforce reduction"',
        '"artificial intelligence" "reduce our workforce"',
        '"AI" "reduction in force"',
        '"automation" "workforce reduction"',
    )
    return (
        Query(1, "closure", '"Item 2.05"', ("2.05",), MANUFACTURING),
        *(Query(2, "retool", text, ("7.01", "8.01"), MANUFACTURING) for text in retool),
        *(Query(3, "ai", text, (), None) for text in ai),
    )


QUERIES = _queries()


# --- one query, every page ----------------------------------------------------------------------------------


@dataclass(frozen=True)
class Hit:
    accession: str
    ciks: tuple[str, ...]
    names: tuple[str, ...]
    form: str
    file_date: date
    items: tuple[str, ...]
    sics: tuple[int, ...]


def _texts(value: object, what: str) -> tuple[str, ...]:
    """A list of strings, or one comma-separated string (the submissions file writes ``items`` that way)."""
    if value is None:
        return ()
    if isinstance(value, str):
        return tuple(part.strip() for part in value.split(",") if part.strip())
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        return tuple(value)
    raise SearchError(f"a hit's {what} is neither a list of text nor text")


def parse_hit(raw: Any) -> Hit:
    if not isinstance(raw, dict) or not isinstance(raw.get("_source"), dict):
        raise SearchError("a hit has no _source")
    source: dict[str, Any] = raw["_source"]
    accession = source.get("adsh")
    if not isinstance(accession, str) or not accession:
        identifier = raw.get("_id")
        if not isinstance(identifier, str) or ":" not in identifier:
            raise SearchError("a hit has no accession number (neither adsh nor an _id with one)")
        accession = identifier.split(":", 1)[0]
    form = source.get("form")
    if not isinstance(form, str) or not form:
        raise SearchError(f"hit {accession} has no form")
    try:
        filed = parse_date(source.get("file_date"), what="file_date")
        sics = tuple(int(s) for s in _texts(source.get("sics"), "sics"))
    except (CutoffError, ValueError) as exc:
        raise SearchError(f"hit {accession}: {exc}") from exc
    return Hit(
        accession=accession,
        ciks=_texts(source.get("ciks"), "ciks"),
        names=_texts(source.get("display_names"), "display_names"),
        form=form,
        file_date=filed,
        items=_texts(source.get("items"), "items"),
        sics=sics,
    )


def search_url(query: Query, start: date, end: date, offset: int) -> str:
    parameters = {
        "q": query.text,
        "forms": FORM,
        "dateRange": "custom",
        "startdt": start.isoformat(),
        "enddt": end.isoformat(),
        "from": str(offset),
    }
    return f"{EFTS_URL}?{urlencode(parameters)}"


def read_query(
    client: EdgarClient, query: Query, start: date, end: date
) -> tuple[list[Hit], dict[str, Any]]:
    """Every page of one query, as parsed hits (one per document, so a filing can appear more than once) and
    a record of what was read. Raises if the query cannot be paged through to its end."""
    hits: list[Hit] = []
    offset, pages, total = 0, 0, None
    while total is None or offset < total:
        reply = client.get(search_url(query, start, end, offset)).json()
        try:
            outer = reply["hits"]
            count, relation = outer["total"]["value"], outer["total"].get("relation", "eq")
            page = outer["hits"]
        except (KeyError, TypeError) as exc:
            raise SearchError("the reply has no hits.total.value or hits.hits") from exc
        if not isinstance(count, int) or not isinstance(page, list):
            raise SearchError("the reply's total is not a number or its hits are not a list")
        if relation != "eq" or count > MAX_RESULTS:
            raise SearchError(
                f"query {query.text} has more than {MAX_RESULTS} hits or an inexact total: it cannot be read "
                "to its end, which is a deviation to report (protocol §12.3)"
            )
        total = count
        if not page:
            if offset < total:
                raise SearchError(
                    f"query {query.text} ended at {offset} of {total} hits: a short read"
                )
            break
        hits.extend(parse_hit(raw) for raw in page)
        offset += len(page)
        pages += 1
    return hits, {
        "query": query.text,
        "channel": query.channel,
        "pages": pages,
        "total": total or 0,
    }


# --- the filters, in code -----------------------------------------------------------------------------------


def filter_reason(query: Query, hit: Hit, start: date, end: date) -> str | None:
    """Why a hit does not pass its channel's filter, or None if it does."""
    if hit.form != FORM:
        return f"form is {hit.form}, not {FORM}"
    if not start <= hit.file_date <= end:
        return "filed outside the search dates"
    if query.items_any and not set(query.items_any) & set(hit.items):
        return f"items lack {' or '.join(query.items_any)}"
    if query.sic_range is not None:
        low, high = query.sic_range
        if not hit.sics:
            return "no sic"
        if not any(low <= sic <= high for sic in hit.sics):
            return f"no sic in {low}-{high}"
    return None


def company_type(hit: Hit) -> str:
    """Channel 3 labels the company by type (§12.3): manufacturing by SIC 2000-3999, else other."""
    if not hit.sics:
        return "unknown"
    low, high = MANUFACTURING
    return "manufacturing" if any(low <= sic <= high for sic in hit.sics) else "other"


# --- the candidate list -------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Candidate:
    id: str  # neutral: "closure-03", or "closure-f03" in the fallback pool
    type: str
    pool: str  # "window" or "fallback"
    hit: Hit
    company_type: str
    found_by: tuple[str, ...]  # the queries that found it

    def record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "pool": self.pool,
            "accession": self.hit.accession,
            "ciks": list(self.hit.ciks),
            "names": list(self.hit.names),
            "file_date": self.hit.file_date.isoformat(),
            "items": list(self.hit.items),
            "sics": list(self.hit.sics),
            "company_type": self.company_type,
            "found_by": list(self.found_by),
        }


@dataclass(frozen=True)
class SearchResult:
    search_date: date
    start: date
    end: date
    candidates: tuple[Candidate, ...]
    record: dict[str, Any]

    def pool(self, case_type: str, pool: str) -> list[Candidate]:
        return [c for c in self.candidates if c.type == case_type and c.pool == pool]


def _pool(filed: date, window_start: date) -> str:
    return "window" if filed >= window_start else "fallback"


def run_search(
    client: EdgarClient,
    search_date: date,
    *,
    queries: Sequence[Query] = QUERIES,
    window_start: date = WINDOW_START,
    fallback_start: date = FALLBACK_START,
) -> SearchResult:
    """Run every query, read every page, filter in code, union by accession number within a type, and hold the
    fallback month's hits apart. ``search_date`` is the day of the search; dates run to the day before."""
    if not fallback_start < window_start < search_date:
        raise SearchError(
            "the dates must run fallback start, window start, search date, in that order"
        )
    end = search_date - timedelta(days=1)
    found: dict[tuple[str, str], tuple[Hit, list[str]]] = {}
    per_query: list[dict[str, Any]] = []
    for query in queries:
        hits, record = read_query(client, query, fallback_start, end)
        dropped: dict[str, int] = {}
        kept: set[str] = set()
        for hit in hits:
            reason = filter_reason(query, hit, fallback_start, end)
            if reason is not None:
                dropped[reason] = dropped.get(reason, 0) + 1
                continue
            kept.add(hit.accession)
            entry = found.setdefault((query.type, hit.accession), (hit, []))
            if query.text not in entry[1]:
                entry[1].append(query.text)
        per_query.append(
            {**record, "documents_read": len(hits), "filings_kept": len(kept), "dropped": dropped}
        )
    candidates: list[Candidate] = []
    for case_type in TYPES:
        ordered = sorted(
            ((hit, queries_) for (kind, _), (hit, queries_) in found.items() if kind == case_type),
            key=lambda pair: (pair[0].file_date, pair[0].accession),
        )
        counts = dict.fromkeys(POOLS, 0)
        for hit, queries_ in ordered:
            pool = _pool(hit.file_date, window_start)
            counts[pool] += 1
            number = f"{counts[pool]:02d}"
            candidates.append(
                Candidate(
                    id=f"{case_type}-{'f' if pool == 'fallback' else ''}{number}",
                    type=case_type,
                    pool=pool,
                    hit=hit,
                    company_type=company_type(hit),
                    found_by=tuple(queries_),
                )
            )
    summary = {
        "search_date": search_date.isoformat(),
        "start": fallback_start.isoformat(),
        "end": end.isoformat(),
        "window_start": window_start.isoformat(),
        "queries": per_query,
        "candidates": {
            f"{case_type}/{pool}": sum(
                1 for c in candidates if (c.type, c.pool) == (case_type, pool)
            )
            for case_type in TYPES
            for pool in POOLS
        },
        "order": "filing date, then accession number; first-disclosure dating is a person's, per candidate",
    }
    return SearchResult(search_date, fallback_start, end, tuple(candidates), summary)


def write_candidates(case: CaseAppendix, result: SearchResult) -> None:
    """``candidates.json`` in the appendix, once: names and accession numbers, private."""
    record = {**result.record, "list": [c.record() for c in result.candidates]}
    case.write_once(
        case.directory / "candidates.json",
        (json.dumps(record, indent=2, ensure_ascii=False) + "\n").encode("utf-8"),
    )


# --- the selection log --------------------------------------------------------------------------------------

# §12.2 puts the first-disclosure check before every other criterion; §12.4 lists the five that follow.
CRITERIA = (
    "first_disclosure",
    "public_and_filing",
    "inside_window",
    "real_decision",
    "maps_to_shape",
    "not_recognizable",
)
READ_REQUIRED = (
    "real_decision",
    "maps_to_shape",
    "not_recognizable",
)  # §12.4: read by the independent reader
K = {"closure": 2, "retool": 2, "ai": 1}  # protocol §12.1
LOG_VERSION = 1


class LogError(Exception):
    """A result recorded out of order, without a reason, for a candidate the log lacks, and so on."""


@dataclass
class Result:
    result: str  # "pass" or "fail"
    reason: str
    public_reason: str | None = None
    disclosed: str | None = (
        None  # ISO date of first public disclosure; on a passed first_disclosure only
    )


@dataclass
class Read:
    agrees: bool
    resolution: str | None = None


@dataclass
class Row:
    id: str
    type: str
    pool: str
    accession: str
    results: dict[str, Result] = field(default_factory=dict)
    reads: dict[str, Read] = field(default_factory=dict)

    @property
    def failed(self) -> str | None:
        return next(
            (c for c in CRITERIA if c in self.results and self.results[c].result == "fail"), None
        )

    @property
    def passed(self) -> bool:
        """Every criterion passed. Not the same as being a case: only the first k in order are (§12.4)."""
        return all(c in self.results and self.results[c].result == "pass" for c in CRITERIA)

    @property
    def finished(self) -> bool:
        return self.passed or self.failed is not None

    @property
    def disclosed(self) -> date | None:
        first = self.results.get("first_disclosure")
        return date.fromisoformat(first.disclosed) if first and first.disclosed else None


@dataclass(frozen=True)
class Selection:
    """One type's cases so far: the first k that passed, in order of first disclosure, the window's before any
    fallback candidate's. ``waiting`` names what must be checked before the selection can be read."""

    case_type: str
    cases: tuple[str, ...]
    fallback: tuple[
        str, ...
    ]  # the cases taken from the fallback month, labeled so wherever reported
    waiting: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return not self.waiting

    @property
    def shortfall(self) -> int:
        return K[self.case_type] - len(self.cases) if self.complete else 0


class SelectionLog:
    """The selection log of §12.4. ``record`` enforces each candidate's criteria in order; ``selection``
    applies "the first k that pass are the cases" in order of first disclosure, so the cases are never a
    matter of which candidates a person happened to check first; a fallback candidate cannot be checked until
    its type's window candidates are all checked and fewer than k passed (§12.2)."""

    def __init__(self, rows: Mapping[str, Row]) -> None:
        self.rows = dict(rows)

    @classmethod
    def start(cls, candidates: Sequence[Candidate]) -> SelectionLog:
        return cls({c.id: Row(c.id, c.type, c.pool, c.hit.accession) for c in candidates})

    def _row(self, candidate_id: str) -> Row:
        if candidate_id not in self.rows:
            raise LogError(f"no candidate {candidate_id!r} in the log")
        return self.rows[candidate_id]

    def _pool(self, case_type: str, pool: str) -> list[Row]:
        return [r for r in self.rows.values() if r.type == case_type and r.pool == pool]

    def _window_short(self, case_type: str) -> bool:
        window = self._pool(case_type, "window")
        return all(r.finished for r in window) and sum(r.passed for r in window) < K[case_type]

    def record(
        self,
        candidate_id: str,
        criterion: str,
        result: str,
        reason: str,
        *,
        public_reason: str | None = None,
        disclosed: date | None = None,
    ) -> None:
        """The next criterion in order, passed or failed, with a reason. Nothing is skipped, and nothing
        follows a failure. A passed first-disclosure check carries the date it found."""
        row = self._row(candidate_id)
        if criterion not in CRITERIA:
            raise LogError(f"{criterion!r} is not a criterion: {', '.join(CRITERIA)}")
        if result not in ("pass", "fail"):
            raise LogError("a result is 'pass' or 'fail'")
        if not reason.strip():
            raise LogError("every result needs its reason")
        if row.failed is not None:
            raise LogError(f"{candidate_id} already failed {row.failed}; nothing follows a failure")
        expected = next((c for c in CRITERIA if c not in row.results), None)
        if criterion != expected:
            raise LogError(
                f"{candidate_id}: the next criterion is {expected}, not {criterion} "
                "(they are checked in order, none skipped)"
            )
        if (criterion == "first_disclosure" and result == "pass") != (disclosed is not None):
            raise LogError(
                "a passed first-disclosure check carries its date (the order the cases are taken in), "
                "and no other result does"
            )
        if row.pool == "fallback" and not self._window_short(row.type):
            raise LogError(
                f"{candidate_id} is a fallback candidate: it is checked only after every {row.type} "
                f"candidate in the window is checked and fewer than {K[row.type]} passed (§12.2)"
            )
        row.results[criterion] = Result(
            result, reason, public_reason, disclosed.isoformat() if disclosed else None
        )

    def record_read(
        self, candidate_id: str, criterion: str, *, agrees: bool, resolution: str | None = None
    ) -> None:
        """The independent reader's read of a rejection on criterion 3, 4 or 5. A disagreement is resolved by
        him and logged with the reason."""
        row = self._row(candidate_id)
        if criterion not in READ_REQUIRED:
            raise LogError(f"only a rejection on {', '.join(READ_REQUIRED)} is read")
        if row.failed != criterion:
            raise LogError(f"{candidate_id} did not fail {criterion}")
        if not agrees and not (resolution and resolution.strip()):
            raise LogError("a disagreement is resolved by him and logged with the reason")
        row.reads[criterion] = Read(agrees, resolution)

    def selection(self, case_type: str) -> Selection:
        """The first k that passed, in order of first disclosure (ties by id), window first. A candidate
        whose first-disclosure check is not done has no place in the order yet, and an unfinished one ahead
        of the k-th case could still displace it: either holds the selection open, named in ``waiting``."""
        k = K[case_type]
        cases: list[str] = []
        fallback: list[str] = []
        waiting: list[str] = []
        for pool in POOLS:
            if len(cases) >= k or waiting:
                break
            rows = self._pool(case_type, pool)
            undated = [r.id for r in rows if "first_disclosure" not in r.results]
            if undated:
                waiting.extend(
                    f"{i}: no first-disclosure result, so its place in the order is unknown"
                    for i in undated
                )
                break
            dated = sorted(
                (r for r in rows if r.disclosed is not None), key=lambda r: (r.disclosed, r.id)
            )
            for row in dated:
                if len(cases) >= k:
                    break
                if not row.finished:
                    waiting.append(f"{row.id}: not finished, and it comes before any later case")
                    break
                if row.passed:
                    cases.append(row.id)
                    if pool == "fallback":
                        fallback.append(row.id)
        return Selection(case_type, tuple(cases), tuple(fallback), tuple(waiting))

    def problems(self) -> list[str]:
        """What stops the log being complete: a rejection on criterion 3, 4 or 5 with no independent read, and
        one filing taken as a case in two types (one decision is one case; §12.5 decides its shape)."""
        lines = [
            f"{row.id}: its rejection on {row.failed} has not been read by the independent reader"
            for row in self.rows.values()
            if row.failed in READ_REQUIRED and row.failed not in row.reads
        ]
        taken: dict[str, list[str]] = {}
        for case_type in TYPES:
            for case_id in self.selection(case_type).cases:
                taken.setdefault(self.rows[case_id].accession, []).append(case_id)
        lines.extend(
            f"one filing is a case twice ({', '.join(ids)}): one decision is one case"
            for ids in taken.values()
            if len(ids) > 1
        )
        return lines

    def to_text(self) -> str:
        rows = [
            {
                "id": r.id,
                "type": r.type,
                "pool": r.pool,
                "accession": r.accession,
                "results": {c: vars(r.results[c]) for c in CRITERIA if c in r.results},
                "reads": {c: vars(read) for c, read in r.reads.items()},
            }
            for r in self.rows.values()
        ]
        return (
            json.dumps({"log_version": LOG_VERSION, "rows": rows}, indent=2, ensure_ascii=False)
            + "\n"
        )

    @classmethod
    def from_text(cls, text: str) -> SelectionLog:
        """A saved log, rebuilt through ``record`` and ``record_read`` so a hand-edited file cannot step
        around the rules: the window's rows first, then the fallback month's."""
        try:
            raw = json.loads(text)
            if raw["log_version"] != LOG_VERSION:
                raise LogError(
                    f"the log has version {raw['log_version']!r}; this reader knows {LOG_VERSION}"
                )
            saved = list(raw["rows"])
            log = cls({r["id"]: Row(r["id"], r["type"], r["pool"], r["accession"]) for r in saved})
            for pool in POOLS:
                for r in (r for r in saved if r["pool"] == pool):
                    for criterion, v in r["results"].items():
                        log.record(
                            r["id"],
                            criterion,
                            v["result"],
                            v["reason"],
                            public_reason=v.get("public_reason"),
                            disclosed=date.fromisoformat(v["disclosed"])
                            if v.get("disclosed")
                            else None,
                        )
                    for criterion, v in r["reads"].items():
                        log.record_read(
                            r["id"], criterion, agrees=v["agrees"], resolution=v.get("resolution")
                        )
            return log
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            raise LogError(f"the selection log cannot be read: {type(exc).__name__}") from exc

    def public_view(self) -> dict[str, Any]:
        """By case type, with no name, accession number, date or industry code. A row is its neutral number,
        its pool and each criterion's result; a reason appears only where a ``public_reason`` was written."""
        view: dict[str, Any] = {}
        for case_type in TYPES:
            chosen = self.selection(case_type)
            considered = [r for r in self.rows.values() if r.type == case_type and r.results]
            view[case_type] = {
                "k": K[case_type],
                "in_list": sum(1 for r in self.rows.values() if r.type == case_type),
                "considered": len(considered),
                "cases": len(chosen.cases),
                "fallback_cases": len(chosen.fallback),
                "complete": chosen.complete,
                "shortfall": chosen.shortfall,
                "rows": [
                    {
                        "id": r.id,
                        "pool": r.pool,
                        "passed": r.passed,
                        "case": r.id in chosen.cases,
                        "criteria": {
                            c: {"result": r.results[c].result, "reason": r.results[c].public_reason}
                            for c in CRITERIA
                            if c in r.results
                        },
                        "independent_read": {
                            c: {"agrees": read.agrees} for c, read in sorted(r.reads.items())
                        },
                    }
                    for r in considered
                ],
            }
        return view


def write_log_version(case: CaseAppendix, log: SelectionLog) -> str:
    """The next ``selection-log-<n>.json`` and ``selection-public-<n>.json``, never overwriting an earlier
    one. Returns the private log's file name."""
    number = 1
    while (case.directory / f"selection-log-{number}.json").exists():
        number += 1
    name = f"selection-log-{number}.json"
    case.write_once(case.directory / name, log.to_text().encode("utf-8"))
    public = json.dumps(log.public_view(), indent=2, ensure_ascii=False) + "\n"
    case.write_once(case.directory / f"selection-public-{number}.json", public.encode("utf-8"))
    return name
