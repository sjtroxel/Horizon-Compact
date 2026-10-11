"""Synthetic EDGAR data for the case builder's tests, shaped like the real fields read on 2026-10-11
(Phase 5 code-half IMPLEMENTATION doc §11). Every name is a fictional canary; nothing here is a real filing.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.edgar import EdgarClient, Response

CANARY_CIK = "0009999999"
SUBMISSIONS_URL = f"https://data.sec.gov/submissions/CIK{CANARY_CIK}.json"
FACTS_URL = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{CANARY_CIK}.json"
USER_AGENT = "Canary Test Harness canary@example.invalid"


class FakeTransport:
    """Serves synthetic bodies; any URL not given is an unexpected request and fails the test."""

    def __init__(self, responses: Mapping[str, Response | bytes]) -> None:
        self._responses = dict(responses)
        self.requests: list[tuple[str, dict[str, str]]] = []

    def get(self, url: str, headers: Mapping[str, str]) -> Response:
        self.requests.append((url, dict(headers)))
        if url not in self._responses:
            raise AssertionError(f"unexpected request: {url}")
        reply = self._responses[url]
        return reply if isinstance(reply, Response) else Response(status=200, body=reply)


def submissions_recent() -> dict[str, list[Any]]:
    """A ``filings.recent`` table: parallel lists, ``items`` one comma-separated string, acceptance in UTC."""
    return {
        "accessionNumber": [
            "0009999999-26-000003",
            "0009999999-26-000002",
            "0009999999-26-000001",
        ],
        "filingDate": ["2026-08-20", "2026-05-08", "2026-03-02"],
        "reportDate": ["2026-08-19", "2026-03-31", "2026-01-31"],
        "acceptanceDateTime": [
            "2026-08-21T02:00:00.000Z",  # 22:00 US Eastern on 2026-08-20: after the close, dated the 20th
            "2026-05-08T20:15:30.000Z",
            "2026-03-02T21:05:00.000Z",
        ],
        "form": ["8-K", "10-Q", "10-K"],
        "items": ["2.05,9.01", "", ""],
        "primaryDocument": ["canary-8k.htm", "canary-10q.htm", "canary-10k.htm"],
        "size": [1200, 52000, 90000],
        "isXBRL": [0, 1, 1],
    }


def submissions_row(index: int) -> dict[str, Any]:
    table = submissions_recent()
    return {name: values[index] for name, values in table.items()}


def company_fact(**overrides: Any) -> dict[str, Any]:
    """One tagged figure: ``fy`` and ``fp`` describe the filing, ``frame`` is added after the fact."""
    fact: dict[str, Any] = {
        "start": "2025-02-01",
        "end": "2026-01-31",
        "val": 1_234_000_000,
        "accn": "0009999999-26-000001",
        "fy": 2025,
        "fp": "FY",
        "form": "10-K",
        "filed": "2026-03-02",
    }
    fact.update(overrides)
    return fact


# --- step 4: a synthetic filer with a full set of filings -------------------------------------------------


def accession(n: int) -> str:
    return f"0009999999-26-{n:06d}"


def archive_url(n: int, name: str) -> str:
    return f"https://www.sec.gov/Archives/edgar/data/9999999/{accession(n).replace('-', '')}/{name}"


def index_url(n: int) -> str:
    return archive_url(n, "index.json")


def filing_table(rows: list[tuple[int, str, str, str]]) -> dict[str, list[Any]]:
    """Rows of (accession number, form, filing date, items) into a ``filings.recent``-shaped table.

    Acceptance is 20:00 UTC on the filing date (after the close in neither season: 15:00 or 16:00 Eastern).
    """
    return {
        "accessionNumber": [accession(n) for n, _, _, _ in rows],
        "filingDate": [filed for _, _, filed, _ in rows],
        "reportDate": ["" for _ in rows],
        "acceptanceDateTime": [f"{filed}T20:00:00.000Z" for _, _, filed, _ in rows],
        "form": [form for _, form, _, _ in rows],
        "items": [items for _, _, _, items in rows],
        "primaryDocument": [
            f"canary-{form.lower().replace('/', '')}-{n}.htm" for n, form, _, _ in rows
        ],
        "size": [1000 for _ in rows],
        "isXBRL": [0 for _ in rows],
    }


def submissions_json(
    recent: dict[str, list[Any]], files: list[dict[str, Any]] | None = None
) -> bytes:
    import json

    return json.dumps(
        {
            "name": "Fernwick Canary Holdings",
            "filings": {"recent": recent, "files": files or []},
        }
    ).encode()


def exhibit_index(*names: str) -> bytes:
    import json

    return json.dumps({"directory": {"item": [{"name": n} for n in names]}}).encode()


TEN_K_HTML = """
<html><body>
<ix:header><div>hidden xbrl fact Item 9 should never be read</div></ix:header>
<p>FORM 10-K for Fernwick Canary Holdings</p>
<table>
<tr><td>Item 1.</td><td>Business</td><td>3</td></tr>
<tr><td>Item 1A.</td><td>Risk Factors</td><td>9</td></tr>
<tr><td>Item 2.</td><td>Properties</td><td>14</td></tr>
<tr><td>Item 7.</td><td>Management&#8217;s Discussion and Analysis</td><td>20</td></tr>
<tr><td>Item 8.</td><td>Financial Statements and Supplementary Data</td><td>30</td></tr>
<tr><td>Item 15.</td><td>Exhibits and Financial Statement Schedules</td><td>60</td></tr>
</table>
<p>Cautionary note: statements here are forward looking. This paragraph is long enough to be real prose
and not a contents entry, which is the point of it, and it sits between the contents and the first heading.
It goes on to say several more things about risks and uncertainties, so it is plainly not a heading.</p>
<p><b>Item 1.</b> Business</p>
<p>We make canary cages in two segments.</p>
<p>Human Capital</p>
<p>We employ about 1,240 people, of whom 310 are represented by a union.</p>
<p>Available Information</p>
<p>Our reports are on our website.</p>
<p><b>Item 1A.</b> Risk Factors</p>
<p>Item 7 discusses our results in more detail.</p>
<p>Cage steel prices may rise.</p>
<p><b>Item 2.</b> Properties</p>
<p>One plant in the Midwest region and one distribution site.</p>
<p><b>Item 7.</b> Management&#8217;s Discussion and Analysis</p>
<p>Demand for cages softened. We acquired a small perch maker.</p>
<p><b>Item 8.</b></p>
<p>Financial Statements and Supplementary Data</p>
<p>The financial statements follow Item 15.</p>
<p><b>Item 15.</b> Exhibits and Financial Statement Schedules</p>
<p>Note 11 - Leases</p>
<p>Lease text.</p>
<p>Note 12 - Segment Information</p>
<p>Cages revenue was 900. Perches revenue was 334.</p>
<p>Note 13 - Subsequent Events</p>
<p>None.</p>
</body></html>
"""

TEN_Q_HTML = """
<html><body>
<p>FORM 10-Q for Fernwick Canary Holdings</p>
<p>PART I - FINANCIAL INFORMATION</p>
<table>
<tr><td>Item 1.</td><td>Financial Statements</td><td>3</td></tr>
<tr><td>Item 2.</td><td>Management&#8217;s Discussion and Analysis</td><td>8</td></tr>
<tr><td>Item 3.</td><td>Quantitative and Qualitative Disclosures About Market Risk</td><td>12</td></tr>
<tr><td>Item 4.</td><td>Controls and Procedures</td><td>12</td></tr>
</table>
<p>PART II - OTHER INFORMATION</p>
<table>
<tr><td>Item 1.</td><td>Legal Proceedings</td><td>13</td></tr>
<tr><td>Item 1A.</td><td>Risk Factors</td><td>13</td></tr>
<tr><td>Item 2.</td><td>Unregistered Sales of Equity Securities</td><td>13</td></tr>
<tr><td>Item 6.</td><td>Exhibits</td><td>14</td></tr>
</table>
<p>Cover prose that is long enough to separate the contents from the first real heading in this quarterly
report, which is the same pattern as the annual report's: a restart, not a heading, in the item order.</p>
<p>PART I - FINANCIAL INFORMATION</p>
<p><b>Item 1.</b> Financial Statements</p>
<p>Statements.</p>
<p><b>Item 2.</b> Management&#8217;s Discussion and Analysis</p>
<p>Quarterly demand fell again. Costs rose.</p>
<p><b>Item 3.</b> Quantitative and Qualitative Disclosures About Market Risk</p>
<p>None.</p>
<p><b>Item 4.</b> Controls and Procedures</p>
<p>Effective.</p>
<p>PART II - OTHER INFORMATION</p>
<p><b>Item 1.</b> Legal Proceedings</p>
<p>None.</p>
<p><b>Item 2.</b> Unregistered Sales of Equity Securities</p>
<p>Part two item two text that must not be mistaken for the MD&amp;A.</p>
<p><b>Item 6.</b> Exhibits</p>
<p>List.</p>
</body></html>
"""

CUTOFF_FILINGS: list[tuple[int, str, str, str]] = [
    (1, "10-K", "2026-03-02", ""),
    (2, "10-Q", "2026-05-08", ""),
    (3, "8-K", "2026-03-02", "7.01"),  # same day as the 10-K: not after it
    (4, "8-K", "2026-04-10", "2.02,9.01"),
    (5, "8-K/A", "2026-05-20", "2.02"),
    (6, "8-K", "2026-06-14", "2.05,9.01"),
    (7, "8-K", "2026-06-15", "8.01"),  # the cut-off day itself
    (8, "8-K", "2026-06-20", "8.01"),  # after the cut-off
    (9, "10-K/A", "2026-05-30", ""),  # an amendment is never the annual report
    (10, "10-K", "2025-03-03", ""),  # an older annual report
    (11, "8-K", "2026-01-15", "7.01"),  # before the annual report
]


def facts_file(
    tags: dict[str, list[dict[str, Any]]], *, taxonomy: str = "us-gaap"
) -> dict[str, Any]:
    """A company-facts file holding the given tags' USD figures."""
    return {
        "cik": 9999999,
        "facts": {taxonomy: {tag: {"units": {"USD": facts}} for tag, facts in tags.items()}},
    }


def annual(
    end_year: int, val: float, filed: str, accn: str = "a", **overrides: Any
) -> dict[str, Any]:
    """An annual figure for the year ending 31 January ``end_year``, as 10-K row of the real file looks."""
    fact = company_fact(
        start=f"{end_year - 1}-02-01",
        end=f"{end_year}-01-31",
        val=val,
        filed=filed,
        accn=accn,
        fy=end_year - 1,
        fp="FY",
        form="10-K",
    )
    fact.update(overrides)
    return fact


def balance(end_year: int, val: float, filed: str, accn: str = "a") -> dict[str, Any]:
    """A balance at 31 January ``end_year``: no ``start``."""
    fact = annual(end_year, val, filed, accn)
    del fact["start"]
    return fact


# --- a whole synthetic filer behind a fake transport -----------------------------------------------------


def doc_name(table: dict[str, list[object]], n: int) -> str:
    return str(table["primaryDocument"][table["accessionNumber"].index(accession(n))])


def world(
    tmp_path: Path,
    extra: dict[str, bytes | Response] | None = None,
    *,
    recent: dict[str, list[Any]] | None = None,
    files: list[dict[str, Any]] | None = None,
) -> tuple[EdgarClient, FakeTransport]:
    table = recent or filing_table(CUTOFF_FILINGS)
    names = filing_table(
        CUTOFF_FILINGS
    )  # file names depend on the filing, not on which page lists it
    responses: dict[str, bytes | Response] = {
        SUBMISSIONS_URL: submissions_json(table, files),
        FACTS_URL: b"{}",
        archive_url(1, doc_name(names, 1)): TEN_K_HTML.encode(),
        archive_url(2, doc_name(names, 2)): TEN_Q_HTML.encode(),
    }
    for n in (4, 5, 6):
        responses[archive_url(n, doc_name(names, n))] = f"<p>report {n}</p>".encode()
    responses[index_url(4)] = exhibit_index(
        "canary-8k-4.htm", "ex99-1.htm", "ex99-2.htm", "logo.jpg"
    )
    responses[index_url(5)] = exhibit_index("canary-8ka-5.htm")
    responses[index_url(6)] = exhibit_index("canary-8k-6.htm", "d123dex991.htm")
    responses[archive_url(4, "ex99-1.htm")] = b"<p>press release one</p>"
    responses[archive_url(4, "ex99-2.htm")] = b"<p>press release two</p>"
    responses[archive_url(6, "d123dex991.htm")] = b"<p>closure release</p>"
    responses.update(extra or {})
    transport = FakeTransport(responses)
    client = EdgarClient(
        appendix=CaseAppendix(root=tmp_path, label="closure-1"),
        transport=transport,
        user_agent=USER_AGENT,
        clock=lambda: 0.0,
        sleep=lambda s: None,
        now=lambda: datetime(2026, 10, 12, tzinfo=UTC),
    )
    return client, transport
