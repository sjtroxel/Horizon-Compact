"""The document set and source list (Phase 5 code half, build step 4, §4.4)."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from edgar_helpers import (
    CANARY_CIK,
    CUTOFF_FILINGS,
    accession,
    archive_url,
    filing_table,
    world,
)
from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.cutoff import CutoffError
from horizon_compact.casebuild.documents import (
    DocumentsError,
    build_document_set,
    exhibit_names,
    page_url,
    parse_filings,
    write_sources,
)

CUTOFF = date(2026, 6, 15)


def test_parse_filings_reads_the_real_fields() -> None:
    filings = parse_filings(filing_table(CUTOFF_FILINGS))
    eight_k = next(f for f in filings if f.accession == accession(4))
    assert eight_k.items == ("2.02", "9.01")
    assert eight_k.filed == date(2026, 4, 10)
    assert eight_k.accepted == datetime(2026, 4, 10, 20, 0, tzinfo=UTC)
    assert next(f for f in filings if f.accession == accession(1)).items == ()


def test_parse_filings_refuses_a_table_with_columns_of_different_lengths() -> None:
    table = filing_table(CUTOFF_FILINGS)
    table["form"] = table["form"][:-1]
    with pytest.raises(DocumentsError, match="different length"):
        parse_filings(table)


def test_parse_filings_refuses_a_table_missing_a_required_column() -> None:
    table = filing_table(CUTOFF_FILINGS)
    del table["acceptanceDateTime"]
    with pytest.raises(DocumentsError, match="acceptanceDateTime"):
        parse_filings(table)


def test_one_bad_row_refuses_the_table_rather_than_being_skipped() -> None:
    table = filing_table(CUTOFF_FILINGS)
    table["filingDate"][3] = "not a date"
    with pytest.raises(CutoffError):
        parse_filings(table)


def test_the_set_is_the_latest_admitted_annual_and_quarterly_and_the_8ks_between(
    tmp_path: Path,
) -> None:
    client, _ = world(tmp_path)
    docset = build_document_set(client, CANARY_CIK, CUTOFF)
    assert docset.annual.accession == accession(1)  # not the 10-K/A, not the older 10-K
    assert docset.quarterly is not None
    assert docset.quarterly.accession == accession(2)
    assert [r.filing.accession for r in docset.current] == [
        accession(4),
        accession(5),
        accession(6),
    ]


def test_an_8k_on_the_annual_reports_day_the_cutoff_day_or_after_is_out(tmp_path: Path) -> None:
    """Each is absent from the set, and (the fake fails on an unexpected URL) never fetched."""
    client, transport = world(tmp_path)
    build_document_set(client, CANARY_CIK, CUTOFF)
    fetched = {url for url, _ in transport.requests}
    for n in (3, 7, 8, 11):
        assert not any(accession(n).replace("-", "") in url for url in fetched)


def test_exhibits_are_the_ex99_files_only_in_name_order(tmp_path: Path) -> None:
    client, _ = world(tmp_path)
    docset = build_document_set(client, CANARY_CIK, CUTOFF)
    by_n = {r.filing.accession: r for r in docset.current}
    assert [e.url.rsplit("/", 1)[1] for e in by_n[accession(4)].exhibits] == [
        "ex99-1.htm",
        "ex99-2.htm",
    ]
    assert by_n[accession(5)].exhibits == ()
    assert [e.url.rsplit("/", 1)[1] for e in by_n[accession(6)].exhibits] == ["d123dex991.htm"]
    assert by_n[accession(4)].exhibits[0].form == "EX-99"


def test_exhibit_names_skips_the_main_document_and_other_files() -> None:
    index = {
        "directory": {
            "item": [
                {"name": "main.htm"},
                {"name": "ex99.htm"},
                {"name": "EX-99_1.HTM"},
                {"name": "x.xml"},
            ]
        }
    }
    assert exhibit_names(index, main_document="main.htm") == ["ex99.htm", "EX-99_1.HTM"]
    assert exhibit_names({}, main_document="main.htm") == []


def test_the_source_list_records_form_accession_dates_url_and_hash(tmp_path: Path) -> None:
    client, _ = world(tmp_path)
    docset = build_document_set(client, CANARY_CIK, CUTOFF)
    records = docset.source_records()
    annual = next(r for r in records if r["role"] == "annual-report")
    assert annual["form"] == "10-K"
    assert annual["accession"] == accession(1)
    assert annual["filed"] == "2026-03-02"
    assert annual["accepted"].startswith("2026-03-02T")  # US Eastern, not UTC
    assert annual["url"] == archive_url(1, "canary-10-k-1.htm")
    assert len(annual["sha256"]) == 64
    roles = {r["role"] for r in records}
    assert {
        "quarterly-report",
        "current-report",
        "press-release-exhibit",
        "submissions",
        "company-facts",
    } <= roles
    assert len([r for r in records if r["role"] == "current-report"]) == 3


def test_write_sources_writes_once_into_the_case(tmp_path: Path) -> None:
    client, _ = world(tmp_path)
    docset = build_document_set(client, CANARY_CIK, CUTOFF)
    case = CaseAppendix(root=tmp_path, label="closure-1")
    write_sources(case, docset)
    payload = json.loads(case.sources_path.read_text())
    assert payload["cutoff"] == "2026-06-15"
    assert payload["cik"] == CANARY_CIK
    assert payload["sources"] == docset.source_records()
    before = case.sources_path.read_bytes()
    write_sources(case, docset)  # the same list again (a rerun from the cache): nothing to write
    assert case.sources_path.read_bytes() == before
    other = build_document_set(client, CANARY_CIK, date(2026, 6, 14))
    with pytest.raises(Exception, match="write-once"):  # a different list is still refused
        write_sources(case, other)
    assert case.sources_path.read_bytes() == before


def test_latest_periodic_is_the_later_of_the_two(tmp_path: Path) -> None:
    client, _ = world(tmp_path)
    assert build_document_set(client, CANARY_CIK, CUTOFF).latest_periodic().form == "10-Q"
    earlier_cutoff = date(2026, 4, 1)  # the 10-Q (May) is not yet filed
    client, _ = world(tmp_path / "again")
    only_annual = build_document_set(client, CANARY_CIK, earlier_cutoff)
    assert only_annual.quarterly is None  # the only 10-Q was filed after April 1
    assert only_annual.latest_periodic().form == "10-K"


def test_older_pages_are_followed_only_until_both_reports_are_in_hand(tmp_path: Path) -> None:
    recent = filing_table([r for r in CUTOFF_FILINGS if r[0] not in (1, 9, 10)])
    page = filing_table([r for r in CUTOFF_FILINGS if r[0] in (1, 9, 10)])
    files = [
        {
            "name": "CIK0009999999-submissions-001.json",
            "filingFrom": "2025-03-03",
            "filingTo": "2026-05-30",
        },
        {
            "name": "CIK0009999999-submissions-002.json",
            "filingFrom": "2019-01-01",
            "filingTo": "2025-03-02",
        },
    ]
    client, transport = world(
        tmp_path,
        {page_url("CIK0009999999-submissions-001.json"): json.dumps(page).encode()},
        recent=recent,
        files=files,
    )
    docset = build_document_set(client, CANARY_CIK, CUTOFF)
    assert docset.annual.accession == accession(1)
    fetched = [url for url, _ in transport.requests]
    assert page_url("CIK0009999999-submissions-001.json") in fetched
    assert (
        page_url("CIK0009999999-submissions-002.json") not in fetched
    )  # the fake would have failed anyway


def test_a_page_name_that_is_not_a_plain_file_name_is_refused() -> None:
    for bad in ("../x.json", "a/b.json", "", "x.json?y=1", ".hidden.json"):
        with pytest.raises(DocumentsError):
            page_url(bad)


def test_no_annual_report_before_the_cutoff_is_an_error(tmp_path: Path) -> None:
    client, _ = world(tmp_path)
    with pytest.raises(DocumentsError, match="no 10-K"):
        build_document_set(client, CANARY_CIK, date(2025, 1, 1))


def test_a_cik_must_be_digits(tmp_path: Path) -> None:
    client, _ = world(tmp_path)
    with pytest.raises(DocumentsError, match="CIK"):
        build_document_set(client, "../etc", CUTOFF)


def test_a_malformed_row_of_a_form_the_set_never_uses_is_skipped_unread() -> None:
    table = filing_table([*CUTOFF_FILINGS, (12, "SC 13G", "2026-02-01", "")])
    table["acceptanceDateTime"][-1] = ""
    filings = parse_filings(table)
    assert accession(12) not in {f.accession for f in filings}
    assert {f.form for f in filings} == {"10-K", "10-Q", "8-K", "8-K/A"}


def test_a_malformed_row_of_a_form_the_set_uses_still_refuses_the_table() -> None:
    table = filing_table(CUTOFF_FILINGS)
    table["acceptanceDateTime"][3] = ""  # an 8-K
    with pytest.raises(CutoffError, match="acceptance time"):
        parse_filings(table)


def test_exhibits_sort_by_number_not_by_text() -> None:
    names = ["ex99-10.htm", "ex99-2.htm", "ex99-1.htm"]
    index = {"directory": {"item": [{"name": n} for n in names]}}
    assert exhibit_names(index, main_document="main.htm") == [
        "ex99-1.htm",
        "ex99-2.htm",
        "ex99-10.htm",
    ]
