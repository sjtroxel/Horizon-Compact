"""The document set and its source list (IMPLEMENTATION §4.4).

For a filer and a cut-off: the most recent 10-K and the most recent 10-Q admitted by the cut-off filter, and
every 8-K (and 8-K/A) filed after that 10-K and before the cut-off, each with its press-release exhibits
(protocol §12.6). Every filing passes ``cutoff.admit`` before anything is chosen or fetched.

Choices made here, for review:

- Only rows of the forms used here (10-K, 10-Q, 8-K, 8-K/A) are parsed; any other row is skipped unread, so a
  malformed row of an unused form cannot stop a build (Opus review, 2026-10-11).
- Only the plain forms ``10-K`` and ``10-Q`` are picked as the periodic reports. An amendment can be a partial
  document (a Part III-only 10-K/A), so it is never taken as the report itself; an 8-K/A counts as an 8-K,
  as protocol §12.6 says.
- "After the most recent annual report" compares filing dates strictly: an 8-K filed on the same day as the
  10-K is not after it, and the 10-K's own text already covers that day.
- ``filings.recent`` is not the whole history (§11 finding 3). Older pages listed under ``filings.files`` are
  followed, newest first, only until an admitted 10-K and an admitted 10-Q are both in hand.

**Unverified against a real filer:** the shape of an older submissions page (assumed: the same parallel lists
as ``recent``, at the top level, named in ``filings.files[].name``) and of a filing's ``index.json`` (assumed:
``directory.item[].name``). Step 1 fetched neither. Both are built on fakes and marked in §11 of the doc.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.cutoff import (
    EASTERN,
    FilingStamp,
    admit,
    stamp_from_submissions_row,
)
from horizon_compact.casebuild.edgar import Document, EdgarClient

SUBMISSIONS_HOST = "https://data.sec.gov"
ARCHIVE_HOST = "https://www.sec.gov"
CURRENT_FORMS = frozenset({"8-K", "8-K/A"})
# The only forms the set is built from. Rows of every other form are not parsed, so a malformed row of a form
# that is never used cannot stop a build; a malformed row of one of these still refuses the table.
USED_FORMS = frozenset({"10-K", "10-Q"}) | CURRENT_FORMS
_REQUIRED_COLUMNS = (
    "accessionNumber",
    "filingDate",
    "acceptanceDateTime",
    "form",
    "primaryDocument",
)
_CIK = re.compile(r"\d{1,10}")
_PAGE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\.json")
# An exhibit 99 under any of the usual file-naming habits: ex99-1.htm, ex-99_1.htm, d123dex991.htm.
_EXHIBIT_99 = re.compile(r"ex[-_]?99.*\.(?:htm|html|txt)$", re.IGNORECASE)


class DocumentsError(Exception):
    """The filer's filings do not support a document set, or a table is malformed."""


@dataclass(frozen=True)
class Filing:
    form: str
    accession: str
    filed: date
    accepted: datetime
    report_date: str
    items: tuple[str, ...]
    primary_document: str

    @property
    def stamp(self) -> FilingStamp:
        return FilingStamp(filed=self.filed, accepted=self.accepted, label=self.accession)

    @property
    def order(self) -> tuple[date, datetime]:
        return (self.filed, self.accepted)


def cik10(cik: str) -> str:
    if not _CIK.fullmatch(cik):
        raise DocumentsError("a CIK is up to ten digits")
    return cik.zfill(10)


def submissions_url(cik: str) -> str:
    return f"{SUBMISSIONS_HOST}/submissions/CIK{cik10(cik)}.json"


def facts_url(cik: str) -> str:
    return f"{SUBMISSIONS_HOST}/api/xbrl/companyfacts/CIK{cik10(cik)}.json"


def page_url(name: str) -> str:
    if not _PAGE_NAME.fullmatch(name):
        raise DocumentsError(
            "an older-filings page has an unexpected name; refusing to build a URL from it"
        )
    return f"{SUBMISSIONS_HOST}/submissions/{name}"


def document_url(cik: str, accession: str, name: str) -> str:
    if "/" in name or name.startswith("."):
        raise DocumentsError("a filing's document name is not a plain file name")
    return f"{ARCHIVE_HOST}/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/{name}"


def index_url(cik: str, accession: str) -> str:
    return f"{ARCHIVE_HOST}/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/index.json"


def parse_filings(table: Mapping[str, Sequence[Any]]) -> list[Filing]:
    """The rows of the forms the set uses (``USED_FORMS``), from a table of parallel lists.

    Every such row passes the cut-off parser, which refuses one without a valid acceptance time.
    """
    for column in _REQUIRED_COLUMNS:
        if column not in table:
            raise DocumentsError(f"the filings table has no '{column}' column")
    length = len(table["accessionNumber"])
    for column, values in table.items():
        if len(values) != length:
            raise DocumentsError(f"the filings table's '{column}' column has a different length")
    filings: list[Filing] = []
    for index in range(length):
        row = {column: values[index] for column, values in table.items()}
        if str(row["form"]) not in USED_FORMS:
            continue
        stamp = stamp_from_submissions_row(row)
        assert stamp.accepted is not None  # the parser refuses a row without one
        items = str(row.get("items") or "")
        filings.append(
            Filing(
                form=str(row["form"]),
                accession=str(row["accessionNumber"]),
                filed=stamp.filed,
                accepted=stamp.accepted,
                report_date=str(row.get("reportDate") or ""),
                items=tuple(part.strip() for part in items.split(",") if part.strip()),
                primary_document=str(row["primaryDocument"]),
            )
        )
    return filings


def _latest(filings: Sequence[Filing], form: str, cutoff: date) -> Filing | None:
    candidates = [f for f in filings if f.form == form and admit(f.stamp, cutoff)]
    return max(candidates, key=lambda f: f.order, default=None)


def load_filings(
    client: EdgarClient, cik: str, cutoff: date
) -> tuple[list[Filing], list[Document]]:
    """Every filing needed to pick the set, and the submissions documents read to get them."""
    submissions = client.get(submissions_url(cik))
    read = [submissions]
    filings_block = submissions.json().get("filings", {})
    filings = parse_filings(filings_block.get("recent", {}))
    pages = sorted(
        filings_block.get("files", []), key=lambda p: str(p.get("filingTo", "")), reverse=True
    )
    for page in pages:
        if _latest(filings, "10-K", cutoff) and _latest(filings, "10-Q", cutoff):
            break
        document = client.get(page_url(str(page.get("name", ""))))
        read.append(document)
        filings.extend(parse_filings(document.json()))
    unique: list[Filing] = []
    seen: set[str] = set()
    for filing in filings:
        if filing.accession not in seen:
            seen.add(filing.accession)
            unique.append(filing)
    return unique, read


def exhibit_names(index: Mapping[str, Any], *, main_document: str) -> list[str]:
    """The press-release exhibits of a filing, from its ``index.json``, by file name. Unverified shape."""
    items = index.get("directory", {}).get("item", [])
    names = [str(item.get("name", "")) for item in items if isinstance(item, Mapping)]
    chosen = [n for n in names if n != main_document and _EXHIBIT_99.search(n)]
    return sorted(chosen, key=_natural)


def _natural(name: str) -> list[tuple[int, int | str]]:
    """Sort key that orders ex99-2 before ex99-10."""
    return [(0, int(t)) if t.isdigit() else (1, t.lower()) for t in re.split(r"(\d+)", name) if t]


@dataclass(frozen=True)
class SourceDocument:
    role: str
    form: str
    accession: str
    filed: date | None
    accepted: datetime | None
    url: str
    document: Document

    def record(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "form": self.form,
            "accession": self.accession,
            "filed": self.filed.isoformat() if self.filed else None,
            "accepted": self.accepted.astimezone(EASTERN).isoformat() if self.accepted else None,
            "url": self.url,
            "sha256": self.document.sha256,
        }

    def text(self) -> str:
        return self.document.body.decode("utf-8", errors="replace")


@dataclass(frozen=True)
class CurrentReport:
    filing: Filing
    main: SourceDocument
    exhibits: tuple[SourceDocument, ...]


@dataclass(frozen=True)
class DocumentSet:
    cik: str
    cutoff: date
    annual: SourceDocument
    quarterly: SourceDocument | None
    current: tuple[CurrentReport, ...]
    support: tuple[SourceDocument, ...]
    facts: Document

    def latest_periodic(self) -> SourceDocument:
        """The later of the annual and quarterly reports, by filing date then acceptance time."""
        if self.quarterly is None:
            return self.annual
        floor = datetime.min.replace(tzinfo=UTC)
        return max(
            (self.annual, self.quarterly),
            key=lambda d: (d.filed or date.min, d.accepted or floor),
        )

    def source_records(self) -> list[dict[str, Any]]:
        records = [d.record() for d in (self.annual, self.quarterly) if d is not None]
        for report in self.current:
            records.append(report.main.record())
            records.extend(e.record() for e in report.exhibits)
        records.extend(d.record() for d in self.support)
        records.append(
            {
                "role": "company-facts",
                "form": None,
                "accession": None,
                "filed": None,
                "accepted": None,
                "url": self.facts.url,
                "sha256": self.facts.sha256,
            }
        )
        return records


def _source(
    role: str, filing: Filing, url: str, document: Document, *, form: str | None = None
) -> SourceDocument:
    return SourceDocument(
        role=role,
        form=form or filing.form,
        accession=filing.accession,
        filed=filing.filed,
        accepted=filing.accepted,
        url=url,
        document=document,
    )


def build_document_set(client: EdgarClient, cik: str, cutoff: date) -> DocumentSet:
    filings, read = load_filings(client, cik, cutoff)
    annual = _latest(filings, "10-K", cutoff)
    if annual is None:
        raise DocumentsError("no 10-K filed before the cut-off was found for this filer")
    quarterly = _latest(filings, "10-Q", cutoff)
    current = sorted(
        (
            f
            for f in filings
            if f.form in CURRENT_FORMS and admit(f.stamp, cutoff) and f.filed > annual.filed
        ),
        key=lambda f: (f.filed, f.accepted, f.accession),
    )

    def fetch(role: str, filing: Filing) -> SourceDocument:
        url = document_url(cik, filing.accession, filing.primary_document)
        return _source(role, filing, url, client.get(url))

    reports: list[CurrentReport] = []
    for filing in current:
        main = fetch("current-report", filing)
        listing = client.get(index_url(cik, filing.accession)).json()
        exhibits = tuple(
            _source(
                "press-release-exhibit",
                filing,
                url := document_url(cik, filing.accession, name),
                client.get(url),
                form="EX-99",
            )
            for name in exhibit_names(listing, main_document=filing.primary_document)
        )
        reports.append(CurrentReport(filing=filing, main=main, exhibits=exhibits))

    support = tuple(
        SourceDocument(
            role="submissions",
            form="",
            accession="",
            filed=None,
            accepted=None,
            url=d.url,
            document=d,
        )
        for d in read
    )
    return DocumentSet(
        cik=cik10(cik),
        cutoff=cutoff,
        annual=fetch("annual-report", annual),
        quarterly=fetch("quarterly-report", quarterly) if quarterly else None,
        current=tuple(reports),
        support=support,
        facts=client.get(facts_url(cik)),
    )


def write_sources(case: CaseAppendix, docset: DocumentSet) -> None:
    """The builder's source list (scope doc DoD 3), written once into the case's appendix directory."""
    payload = {
        "cik": docset.cik,
        "cutoff": docset.cutoff.isoformat(),
        "sources": docset.source_records(),
    }
    case.write_once(case.sources_path, json.dumps(payload, indent=2).encode("utf-8"))
