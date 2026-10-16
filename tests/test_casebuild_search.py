"""The search runner and the selection log on fake replies (Phase 5 code half, build step 7)."""

from __future__ import annotations

import json
import re
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest

from edgar_helpers import USER_AGENT, FakeTransport
from horizon_compact.casebuild.appendix import AppendixError, CaseAppendix
from horizon_compact.casebuild.edgar import EdgarClient
from horizon_compact.casebuild.search import (
    CRITERIA,
    EFTS_URL,
    FALLBACK_START,
    QUERIES,
    WINDOW_START,
    K,
    LogError,
    Query,
    ReaderReply,
    Row,
    SearchError,
    SelectionLog,
    filter_reason,
    parse_hit,
    read_query,
    run_search,
    search_url,
    write_candidates,
    write_log_version,
)

ROOT = Path(__file__).resolve().parents[1]
SEARCH_DATE = date(2026, 11, 1)
END = date(2026, 10, 31)
CLOSURE = QUERIES[0]


# A reader's reply as the log stores it (the file itself is the reader's test's business).
AGREED = ReaderReply("reader-rejection-x-1-reply.json", "a" * 64, "fail")
DISPUTED = ReaderReply("reader-rejection-x-1-reply.json", "b" * 64, "pass")
UNSURE = ReaderReply("reader-rejection-x-1-reply.json", "c" * 64, "cannot_tell")


def raw_hit(
    adsh: str,
    filed: str,
    *,
    items: list[str] | str | None = None,
    sics: list[str] | None = None,
    form: str = "8-K",
    name: str = "Canary Cages Inc",
    document: str = "main.htm",
) -> dict[str, Any]:
    return {
        "_id": f"{adsh}:{document}",
        "_source": {
            "adsh": adsh,
            "form": form,
            "file_date": filed,
            "items": ["2.05", "9.01"] if items is None else items,
            "sics": ["3990"] if sics is None else sics,
            "ciks": ["0009999999"],
            "display_names": [name],
        },
    }


def page(hits: list[dict[str, Any]], total: int, relation: str = "eq") -> bytes:
    return json.dumps(
        {"hits": {"total": {"value": total, "relation": relation}, "hits": hits}}
    ).encode()


def client_for(tmp_path: Path, replies: dict[str, bytes]) -> tuple[EdgarClient, FakeTransport]:
    transport = FakeTransport(replies)
    client = EdgarClient(
        appendix=CaseAppendix(root=tmp_path, label="search"),
        transport=transport,
        user_agent=USER_AGENT,
        clock=lambda: 0.0,
        sleep=lambda s: None,
        now=lambda: datetime(2026, 11, 1, tzinfo=UTC),
    )
    return client, transport


def every_query_empty(skip: set[str] | None = None) -> dict[str, bytes]:
    return {
        search_url(q, FALLBACK_START, END, 0): page([], 0)
        for q in QUERIES
        if q.text not in (skip or set())
    }


# --- the queries are the protocol's ---------------------------------------------------------------------


def protocol_rows() -> list[tuple[int, list[str], str]]:
    text = (ROOT / "experiment/protocol/protocol-v1.md").read_text(encoding="utf-8")
    section = text.split("### 12.3 The search, query by query")[1].split("**WARN notices")[0]
    rows = []
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("| **") and len(cells) == 4:
            rows.append((int(cells[0][2]), re.findall(r"`([^`]+)`", cells[2]), cells[3]))
    return rows


def test_the_queries_are_the_protocols_table_run_as_written() -> None:
    rows = protocol_rows()
    assert [channel for channel, _, _ in rows] == [1, 2, 3]
    assert [q.text for q in QUERIES] == [text for _, texts, _ in rows for text in texts]
    assert [q.channel for q in QUERIES] == [1] + [2] * 6 + [3] * 5


def test_the_filters_are_the_protocols() -> None:
    by_channel = {q.channel: q for q in QUERIES}
    assert (by_channel[1].items_any, by_channel[1].sic_range) == (("2.05",), (2000, 3999))
    assert (by_channel[2].items_any, by_channel[2].sic_range) == (("7.01", "8.01"), (2000, 3999))
    assert (by_channel[3].items_any, by_channel[3].sic_range) == ((), None)
    rows = {channel: filter_text for channel, _, filter_text in protocol_rows()}
    assert "2.05" in rows[1] and "2000-3999" in rows[1]
    assert "7.01" in rows[2] and "8.01" in rows[2]
    assert "any `items`" in rows[3]


def test_the_dates_are_the_protocols() -> None:
    text = (ROOT / "experiment/protocol/protocol-v1.md").read_text(encoding="utf-8")
    assert WINDOW_START.isoformat() in text and "July 2026" in text
    assert (date(2026, 7, 1), date(2026, 8, 1)) == (FALLBACK_START, WINDOW_START)


def test_a_query_url_carries_the_forms_dates_and_offset() -> None:
    url = search_url(QUERIES[1], FALLBACK_START, END, 200)
    assert url.startswith(f"{EFTS_URL}?")
    for part in ("q=%22new+manufacturing+facility%22", "forms=8-K", "dateRange=custom",
                 "startdt=2026-07-01", "enddt=2026-10-31", "from=200"):  # fmt: skip
        assert part in url


# --- reading one query -----------------------------------------------------------------------------------


def test_every_page_of_a_query_is_read(tmp_path: Path) -> None:
    first = [raw_hit(f"0009999999-26-0000{n:02d}", "2026-08-10") for n in range(2)]
    second = [raw_hit("0009999999-26-000050", "2026-08-11")]
    client, transport = client_for(
        tmp_path,
        {
            search_url(CLOSURE, FALLBACK_START, END, 0): page(first, 3),
            search_url(CLOSURE, FALLBACK_START, END, 2): page(second, 3),
        },
    )
    hits, record = read_query(client, CLOSURE, FALLBACK_START, END)
    assert [h.accession for h in hits] == [
        "0009999999-26-000000",
        "0009999999-26-000001",
        "0009999999-26-000050",
    ]
    assert record["pages"] == 2 and record["total"] == 3
    assert len(transport.requests) == 2


def test_a_query_that_cannot_be_read_to_its_end_is_an_error_not_a_quiet_stop(
    tmp_path: Path,
) -> None:
    url = search_url(CLOSURE, FALLBACK_START, END, 0)
    short, _ = client_for(tmp_path / "a", {url: page([], 5)})
    with pytest.raises(SearchError, match="short read"):
        read_query(short, CLOSURE, FALLBACK_START, END)
    inexact, _ = client_for(
        tmp_path / "b", {url: page([raw_hit("0009999999-26-000001", "2026-08-10")], 10_000, "gte")}
    )
    with pytest.raises(SearchError, match="cannot be read to its end"):
        read_query(inexact, CLOSURE, FALLBACK_START, END)
    huge, _ = client_for(tmp_path / "c", {url: page([], 10_001)})
    with pytest.raises(SearchError, match="cannot be read to its end"):
        read_query(huge, CLOSURE, FALLBACK_START, END)


@pytest.mark.parametrize(
    "reply",
    [
        b"{}",
        b'{"hits": {"total": {"value": "3"}, "hits": []}}',
        b'{"hits": {"total": {"value": 1}, "hits": {}}}',
    ],
)
def test_a_reply_of_another_shape_raises(tmp_path: Path, reply: bytes) -> None:
    client, _ = client_for(tmp_path, {search_url(CLOSURE, FALLBACK_START, END, 0): reply})
    with pytest.raises(SearchError):
        read_query(client, CLOSURE, FALLBACK_START, END)


def test_a_hit_is_parsed_strictly() -> None:
    hit = parse_hit(raw_hit("0009999999-26-000001", "2026-08-10", items="2.05, 9.01"))
    assert (hit.accession, hit.items, hit.sics, hit.file_date) == (
        "0009999999-26-000001",
        ("2.05", "9.01"),
        (3990,),
        date(2026, 8, 10),
    )
    from_id = raw_hit("0009999999-26-000001", "2026-08-10")
    del from_id["_source"]["adsh"]
    assert parse_hit(from_id).accession == "0009999999-26-000001"
    broken_hits: list[dict[str, Any]] = [
        {},
        {"_source": {}},
        {"_source": {"adsh": "a", "form": "8-K", "file_date": "soon"}},
        {"_source": {"adsh": "a", "form": "8-K", "file_date": "2026-08-10", "sics": ["abc"]}},
        {"_source": {"adsh": "a", "file_date": "2026-08-10"}},
        {"_source": {"file_date": "2026-08-10", "form": "8-K"}, "_id": "no-colon"},
    ]
    for broken in broken_hits:
        with pytest.raises(SearchError):
            parse_hit(broken)


# --- the filters, in code --------------------------------------------------------------------------------


def hit_of(**changes: Any) -> Any:
    return parse_hit(raw_hit("0009999999-26-000001", **{"filed": "2026-08-10", **changes}))


def test_each_filter_is_applied_and_names_its_reason() -> None:
    assert filter_reason(CLOSURE, hit_of(), FALLBACK_START, END) is None
    assert "form" in str(filter_reason(CLOSURE, hit_of(form="8-K/A"), FALLBACK_START, END))
    assert "outside" in str(filter_reason(CLOSURE, hit_of(filed="2026-06-30"), FALLBACK_START, END))
    assert "outside" in str(filter_reason(CLOSURE, hit_of(filed="2026-11-01"), FALLBACK_START, END))
    assert "items lack 2.05" in str(
        filter_reason(CLOSURE, hit_of(items=["8.01"]), FALLBACK_START, END)
    )
    assert "no sic in 2000-3999" in str(
        filter_reason(CLOSURE, hit_of(sics=["6021"]), FALLBACK_START, END)
    )
    assert filter_reason(CLOSURE, hit_of(sics=[]), FALLBACK_START, END) == "no sic"
    retool = QUERIES[1]
    assert filter_reason(retool, hit_of(items=["7.01"]), FALLBACK_START, END) is None
    assert filter_reason(retool, hit_of(items=["8.01"]), FALLBACK_START, END) is None
    assert filter_reason(retool, hit_of(items=["2.05"]), FALLBACK_START, END) is not None
    ai = QUERIES[-1]
    assert filter_reason(ai, hit_of(items=[], sics=["6021"]), FALLBACK_START, END) is None
    assert filter_reason(ai, hit_of(items=[], sics=[]), FALLBACK_START, END) is None


def test_the_boundaries_of_the_dates_and_the_sic_range_are_inclusive() -> None:
    for filed in ("2026-07-01", "2026-10-31"):
        assert filter_reason(CLOSURE, hit_of(filed=filed), FALLBACK_START, END) is None
    for sic in ("2000", "3999"):
        assert filter_reason(CLOSURE, hit_of(sics=[sic]), FALLBACK_START, END) is None
    for sic in ("1999", "4000"):
        assert filter_reason(CLOSURE, hit_of(sics=[sic]), FALLBACK_START, END) is not None


# --- the whole search ------------------------------------------------------------------------------------


def a_search(tmp_path: Path) -> tuple[Any, FakeTransport, CaseAppendix]:
    closure = [
        raw_hit("0009999999-26-000030", "2026-08-20"),  # window
        raw_hit(
            "0009999999-26-000030", "2026-08-20", document="ex99.htm"
        ),  # the same filing, an exhibit
        raw_hit("0009999999-26-000010", "2026-07-15", name="Fallback Cages Inc"),  # fallback month
        raw_hit("0009999999-26-000040", "2026-09-02", items=["8.01"]),  # fails the item filter
        raw_hit("0009999999-26-000050", "2026-09-03", sics=["6021"]),  # fails the sic filter
    ]
    retool_one = [raw_hit("0009999999-26-000060", "2026-08-05", items=["7.01"])]
    retool_two = [
        raw_hit("0009999999-26-000060", "2026-08-05", items=["7.01"])
    ]  # found by a second query
    ai = [
        raw_hit(
            "0009999999-26-000030", "2026-08-20", items=["2.05"], sics=["6021"]
        ),  # also a closure filing
        raw_hit("0009999999-26-000070", "2026-10-01", items=[], sics=["7372"]),
    ]
    replies = every_query_empty({CLOSURE.text, QUERIES[1].text, QUERIES[2].text, QUERIES[7].text})
    replies[search_url(CLOSURE, FALLBACK_START, END, 0)] = page(closure, 5)
    replies[search_url(QUERIES[1], FALLBACK_START, END, 0)] = page(retool_one, 1)
    replies[search_url(QUERIES[2], FALLBACK_START, END, 0)] = page(retool_two, 1)
    replies[search_url(QUERIES[7], FALLBACK_START, END, 0)] = page(ai, 2)
    client, transport = client_for(tmp_path, replies)
    return run_search(client, SEARCH_DATE), transport, CaseAppendix(root=tmp_path, label="search")


def test_every_query_is_run_separately_and_once(tmp_path: Path) -> None:
    result, transport, _ = a_search(tmp_path)
    urls = [url for url, _ in transport.requests]
    assert len(urls) == len(QUERIES) == len(set(urls))
    assert [q["query"] for q in result.record["queries"]] == [q.text for q in QUERIES]
    assert all(headers["User-Agent"] == USER_AGENT for _, headers in transport.requests)


def test_a_filing_found_twice_counts_once_and_remembers_every_query_that_found_it(
    tmp_path: Path,
) -> None:
    result, _, _ = a_search(tmp_path)
    closure = result.pool("closure", "window")
    assert [c.hit.accession for c in closure] == [
        "0009999999-26-000030"
    ]  # main document and exhibit: one
    retool = result.pool("retool", "window")
    assert len(retool) == 1
    assert retool[0].found_by == (QUERIES[1].text, QUERIES[2].text)


def test_the_filters_drop_what_fails_and_the_record_says_why(tmp_path: Path) -> None:
    result, _, _ = a_search(tmp_path)
    closure_record = result.record["queries"][0]
    assert closure_record["documents_read"] == 5 and closure_record["filings_kept"] == 2
    assert sorted(closure_record["dropped"]) == ["items lack 2.05", "no sic in 2000-3999"]
    assert {c.hit.accession for c in result.candidates if c.type == "closure"} == {
        "0009999999-26-000030",
        "0009999999-26-000010",
    }


def test_the_fallback_months_hits_are_held_apart_from_the_windows(tmp_path: Path) -> None:
    result, _, _ = a_search(tmp_path)
    assert [c.hit.accession for c in result.pool("closure", "fallback")] == ["0009999999-26-000010"]
    assert [c.hit.accession for c in result.pool("closure", "window")] == ["0009999999-26-000030"]
    assert result.record["candidates"]["closure/fallback"] == 1
    assert [c.id for c in result.candidates if c.type == "closure"] == ["closure-f01", "closure-01"]


def test_candidates_are_in_order_of_filing_date_then_accession_within_a_type(
    tmp_path: Path,
) -> None:
    result, _, _ = a_search(tmp_path)
    ai = result.pool("ai", "window")
    assert [c.hit.file_date for c in ai] == [date(2026, 8, 20), date(2026, 10, 1)]
    assert [c.id for c in ai] == ["ai-01", "ai-02"]
    assert "first-disclosure" in result.record["order"]


def test_a_filing_in_two_types_is_a_candidate_in_each_and_channel_3_labels_the_company(
    tmp_path: Path,
) -> None:
    result, _, _ = a_search(tmp_path)
    same = "0009999999-26-000030"
    assert {c.type for c in result.candidates if c.hit.accession == same} == {"closure", "ai"}
    ai = {c.hit.accession: c.company_type for c in result.pool("ai", "window")}
    assert ai == {same: "other", "0009999999-26-000070": "other"}
    closure = result.pool("closure", "window")[0]
    assert closure.company_type == "manufacturing"


def test_a_search_with_misordered_dates_is_refused(tmp_path: Path) -> None:
    client, _ = client_for(tmp_path, {})
    with pytest.raises(SearchError, match="in that order"):
        run_search(client, date(2026, 7, 20))


def test_the_search_writes_its_candidates_once_and_a_rerun_reads_the_cache(tmp_path: Path) -> None:
    result, transport, case = a_search(tmp_path)
    write_candidates(case, result)
    written = json.loads((case.directory / "candidates.json").read_text(encoding="utf-8"))
    assert len(written["list"]) == len(result.candidates)
    assert written["list"][0]["names"]  # private: names live here and nowhere public
    with pytest.raises(AppendixError, match="write-once"):
        write_candidates(case, result)
    before = len(transport.requests)
    client = EdgarClient(
        appendix=case, transport=FakeTransport({}), user_agent=USER_AGENT,
        clock=lambda: 0.0, sleep=lambda s: None,
    )  # fmt: skip
    again = run_search(
        client, SEARCH_DATE
    )  # every URL is cached: the empty fake would fail any request
    assert [c.record() for c in again.candidates] == [c.record() for c in result.candidates]
    assert before == len(QUERIES)


# --- the selection log -----------------------------------------------------------------------------------

D = date(2026, 8, 1)


def a_log(tmp_path: Path) -> SelectionLog:
    result, _, _ = a_search(tmp_path)
    return SelectionLog.start(result.candidates)


def log_of(*ids: str, same: dict[str, str] | None = None) -> SelectionLog:
    """Rows by id: "closure-01" is in the window, "closure-f01" in the fallback month."""
    rows = {}
    for n, candidate_id in enumerate(ids):
        case_type, number = candidate_id.split("-")
        accession = (same or {}).get(candidate_id, f"0009999999-26-{n:06d}")
        pool = "fallback" if number.startswith("f") else "window"
        rows[candidate_id] = Row(candidate_id, case_type, pool, accession)
    return SelectionLog(rows)


def take(log: SelectionLog, candidate_id: str, day: int = 1) -> None:
    log.record(
        candidate_id, "first_disclosure", "pass", "first said here", disclosed=D.replace(day=day)
    )
    for criterion in CRITERIA[1:]:
        log.record(candidate_id, criterion, "pass", f"{criterion} ok")


def reject(log: SelectionLog, candidate_id: str, day: int = 1) -> None:
    log.record(
        candidate_id, "first_disclosure", "pass", "first said here", disclosed=D.replace(day=day)
    )
    log.record(candidate_id, "public_and_filing", "fail", "not publicly traded")


def test_a_log_starts_with_a_row_per_candidate_and_nothing_decided(tmp_path: Path) -> None:
    log = a_log(tmp_path)
    assert "closure-01" in log.rows and "closure-f01" in log.rows
    assert all(not row.results and not row.passed for row in log.rows.values())
    assert log.problems() == []


def test_criteria_are_recorded_in_order_none_skipped_and_nothing_after_a_failure() -> None:
    log = log_of("closure-01", "closure-02")
    with pytest.raises(LogError, match="next criterion is first_disclosure"):
        log.record("closure-01", "inside_window", "pass", "r")
    log.record("closure-01", "first_disclosure", "pass", "the filing itself", disclosed=D)
    with pytest.raises(LogError, match="public_and_filing"):
        log.record("closure-01", "maps_to_shape", "pass", "r")
    log.record("closure-01", "public_and_filing", "fail", "not publicly traded")
    with pytest.raises(LogError, match="nothing follows a failure"):
        log.record("closure-01", "inside_window", "pass", "r")
    with pytest.raises(LogError, match="reason"):
        log.record("closure-02", "first_disclosure", "pass", "  ", disclosed=D)
    with pytest.raises(LogError, match="'pass' or 'fail'"):
        log.record("closure-02", "first_disclosure", "maybe", "r")
    with pytest.raises(LogError, match="not a criterion"):
        log.record("closure-02", "vibes", "pass", "r")
    with pytest.raises(LogError, match="no candidate"):
        log.record("closure-99", "first_disclosure", "pass", "r", disclosed=D)


def test_a_passed_first_disclosure_check_carries_its_date_and_nothing_else_does() -> None:
    log = log_of("closure-01", "closure-02")
    with pytest.raises(LogError, match="carries its date"):
        log.record("closure-01", "first_disclosure", "pass", "r")
    with pytest.raises(LogError, match="carries its date"):
        log.record("closure-01", "first_disclosure", "fail", "said in June", disclosed=D)
    log.record("closure-01", "first_disclosure", "pass", "r", disclosed=D)
    with pytest.raises(LogError, match="carries its date"):
        log.record("closure-01", "public_and_filing", "pass", "r", disclosed=D)
    assert log.rows["closure-01"].disclosed == D


def test_the_cases_are_the_first_k_that_pass_by_disclosure_date_not_by_checking_order() -> None:
    log = log_of("closure-01", "closure-02", "closure-03")
    take(log, "closure-02", day=20)  # checked first, disclosed last
    take(log, "closure-01", day=10)
    take(log, "closure-03", day=5)
    chosen = log.selection("closure")
    assert (
        chosen.cases == ("closure-03", "closure-01") and chosen.complete and chosen.shortfall == 0
    )
    assert log.rows["closure-02"].passed  # it passed, but it is not a case


def test_the_selection_waits_while_an_earlier_candidate_is_unfinished_or_any_is_undated() -> None:
    log = log_of("closure-01", "closure-02", "closure-03")
    take(log, "closure-02", day=20)
    assert not log.selection("closure").complete  # 01 and 03 have no place in the order yet
    log.record("closure-01", "first_disclosure", "pass", "r", disclosed=D.replace(day=10))
    reject(log, "closure-03", day=5)
    chosen = log.selection("closure")
    assert chosen.cases == () and chosen.waiting == (
        "closure-01: not finished, and it comes before any later case",
    )
    for criterion in CRITERIA[1:]:
        log.record("closure-01", criterion, "pass", "ok")
    assert log.selection("closure").cases == ("closure-01", "closure-02")


def test_a_candidate_after_the_kth_case_need_not_be_finished() -> None:
    log = log_of("ai-01", "ai-02")
    take(log, "ai-01", day=3)
    log.record("ai-02", "first_disclosure", "pass", "r", disclosed=D.replace(day=9))
    chosen = log.selection("ai")
    assert chosen.cases == ("ai-01",) and chosen.complete


def test_a_failed_first_disclosure_check_takes_no_place_in_the_order() -> None:
    log = log_of("ai-01", "ai-02")
    log.record("ai-01", "first_disclosure", "fail", "an earlier mention")
    take(log, "ai-02", day=9)
    assert log.selection("ai").cases == ("ai-02",)


def test_a_fallback_candidate_waits_until_the_window_is_checked_and_short() -> None:
    log = log_of("closure-01", "closure-02", "closure-f01", "closure-f02")
    with pytest.raises(LogError, match="fallback candidate"):
        log.record("closure-f01", "first_disclosure", "pass", "r", disclosed=date(2026, 7, 9))
    take(log, "closure-01")
    with pytest.raises(LogError, match="fallback candidate"):  # closure-02 is not checked yet
        log.record("closure-f01", "first_disclosure", "pass", "r", disclosed=date(2026, 7, 9))
    reject(log, "closure-02", day=2)
    take(log, "closure-f02", day=20)
    log.record("closure-f01", "first_disclosure", "pass", "r", disclosed=date(2026, 7, 9))
    chosen = log.selection("closure")
    assert (
        chosen.cases == ("closure-01",) and chosen.waiting
    )  # f01 is earlier than f02 and unfinished
    for criterion in CRITERIA[1:]:
        log.record(
            "closure-f01", criterion, "fail" if criterion == "inside_window" else "pass", "r"
        )
        if criterion == "inside_window":
            break
    chosen = log.selection("closure")
    assert chosen.cases == ("closure-01", "closure-f02") and chosen.fallback == ("closure-f02",)


def test_a_fallback_candidate_is_never_checked_when_the_window_gave_k() -> None:
    log = log_of("ai-01", "ai-f01")
    take(log, "ai-01")
    with pytest.raises(LogError, match="fallback candidate"):
        log.record("ai-f01", "first_disclosure", "pass", "r", disclosed=date(2026, 7, 9))


def test_a_type_that_runs_out_reports_its_shortfall() -> None:
    log = log_of("retool-01", "retool-f01")
    take(log, "retool-01")
    log.record("retool-f01", "first_disclosure", "fail", "an earlier mention")
    chosen = log.selection("retool")
    assert chosen.complete and chosen.cases == ("retool-01",) and chosen.shortfall == 1


def test_one_filing_taken_as_a_case_in_two_types_is_a_problem() -> None:
    log = log_of(
        "closure-01",
        "ai-01",
        same={"closure-01": "0009999999-26-000777", "ai-01": "0009999999-26-000777"},
    )
    take(log, "closure-01")
    take(log, "ai-01")
    assert log.problems() == [
        "one filing is a case twice (closure-01, ai-01): one decision is one case"
    ]


def test_a_rejection_on_criterion_3_4_or_5_needs_an_independent_read_and_a_disagreement_a_resolution() -> (
    None
):
    log = log_of("closure-01", "closure-02")
    log.record("closure-01", "first_disclosure", "pass", "ok", disclosed=D)
    for criterion in CRITERIA[1:3]:
        log.record("closure-01", criterion, "pass", "ok")
    log.record("closure-01", "real_decision", "fail", "a forced wind-down")
    assert log.problems() == [
        "closure-01: its rejection on real_decision has not been read by the independent reader"
    ]
    with pytest.raises(LogError, match="resolved by him"):
        log.record_read("closure-01", "real_decision", reply=DISPUTED)
    with pytest.raises(LogError, match="did not fail"):
        log.record_read("closure-01", "maps_to_shape", reply=AGREED)
    log.record_read(
        "closure-01", "real_decision", reply=DISPUTED, resolution="he finds real alternatives"
    )
    assert log.problems() == []
    log.record(
        "closure-02", "first_disclosure", "fail", "mentioned in June"
    )  # not 3, 4 or 5: not read
    assert log.problems() == []
    with pytest.raises(LogError, match="only a rejection on"):
        log.record_read("closure-02", "first_disclosure", reply=AGREED)


def fail_at(log: SelectionLog, candidate_id: str, criterion: str, day: int = 1) -> None:
    """Passes every criterion before ``criterion`` and fails it, unread."""
    log.record(
        candidate_id, "first_disclosure", "pass", "first said here", disclosed=D.replace(day=day)
    )
    for earlier in CRITERIA[1 : CRITERIA.index(criterion)]:
        log.record(candidate_id, earlier, "pass", f"{earlier} ok")
    log.record(candidate_id, criterion, "fail", f"{criterion} fails")


def dispute(log: SelectionLog, candidate_id: str, criterion: str) -> None:
    log.record_read(candidate_id, criterion, reply=DISPUTED, resolution="he finds it holds")


def test_a_rejection_the_reader_disputes_does_not_stand_and_the_candidate_goes_on() -> None:
    log = log_of("closure-01", "closure-02")
    fail_at(log, "closure-01", "real_decision")
    row = log.rows["closure-01"]
    assert row.failed == "real_decision" and not row.passed
    assert not row.finished  # unread, so not final: a dispute would let it go on
    with pytest.raises(LogError, match="nothing follows a failure"):
        log.record("closure-01", "maps_to_shape", "pass", "ok")
    dispute(log, "closure-01", "real_decision")
    assert row.failed is None and row.disputed("real_decision") and row.met("real_decision")
    assert not row.finished and not row.passed  # four criteria still to go
    assert row.results["real_decision"].result == "fail"  # the fail and its reason are kept
    assert row.results["real_decision"].reason == "real_decision fails"
    assert row.reads["real_decision"].resolution == "he finds it holds"
    for criterion in CRITERIA[CRITERIA.index("real_decision") + 1 :]:
        log.record("closure-01", criterion, "pass", f"{criterion} ok")
    assert row.passed and row.finished and row.failed is None
    assert log.selection("closure").waiting  # closure-02 is still undated
    assert log.problems() == []


def test_a_rejection_the_reader_agrees_with_still_stands() -> None:
    log = log_of("closure-01")
    fail_at(log, "closure-01", "maps_to_shape")
    log.record_read("closure-01", "maps_to_shape", reply=AGREED)
    row = log.rows["closure-01"]
    assert row.failed == "maps_to_shape" and not row.disputed("maps_to_shape")
    with pytest.raises(LogError, match="nothing follows a failure"):
        log.record("closure-01", "not_recognizable", "pass", "ok")


def test_a_disputed_rejection_can_be_followed_by_a_rejection_that_stands() -> None:
    log = log_of("closure-01")
    fail_at(log, "closure-01", "real_decision")
    dispute(log, "closure-01", "real_decision")
    log.record("closure-01", "maps_to_shape", "fail", "no shape fits")
    row = log.rows["closure-01"]
    assert row.failed == "maps_to_shape" and not row.passed and not row.finished  # unread
    assert log.problems() == [
        "closure-01: its rejection on maps_to_shape has not been read by the independent reader"
    ]


def test_a_disputed_rejection_on_the_last_criterion_counts_as_passing_it() -> None:
    log = log_of("closure-01")
    fail_at(log, "closure-01", "not_recognizable")
    row = log.rows["closure-01"]
    assert row.failed == "not_recognizable" and not row.passed
    dispute(log, "closure-01", "not_recognizable")
    assert row.failed is None and row.passed and row.finished
    assert log.selection("closure").cases == ("closure-01",)


def test_a_disputed_candidate_takes_its_place_in_the_order_of_first_disclosure() -> None:
    log = log_of("closure-01", "closure-02", "closure-03")
    fail_at(log, "closure-01", "real_decision", day=2)
    dispute(log, "closure-01", "real_decision")
    for criterion in CRITERIA[CRITERIA.index("real_decision") + 1 :]:
        log.record("closure-01", criterion, "pass", "ok")
    take(log, "closure-02", day=5)
    take(log, "closure-03", day=3)
    assert log.selection("closure").cases == ("closure-01", "closure-03")


def test_an_unread_rejection_on_3_4_or_5_holds_the_selection_and_the_fallback_open() -> None:
    log = log_of("ai-01", "ai-02", "ai-f01")  # k = 1
    fail_at(log, "ai-01", "maps_to_shape", day=2)
    take(log, "ai-02", day=5)
    row = log.rows["ai-01"]
    assert row.awaiting_read == "maps_to_shape" and not row.finished
    chosen = log.selection("ai")
    assert chosen.cases == () and not chosen.complete  # a dispute could still make ai-01 the case
    assert chosen.waiting == (
        "ai-01: its rejection on maps_to_shape awaits the independent read, "
        "and it comes before any later case",
    )
    with pytest.raises(LogError, match="fallback candidate"):  # the window is not known to be short
        log.record("ai-f01", "first_disclosure", "pass", "ok", disclosed=D)
    log.record_read("ai-01", "maps_to_shape", reply=AGREED)
    assert row.finished and log.selection("ai").cases == ("ai-02",)


def test_a_read_cannot_change_once_a_later_criterion_is_recorded() -> None:
    log = log_of("closure-01")
    fail_at(log, "closure-01", "real_decision")
    log.record_read("closure-01", "real_decision", reply=AGREED)
    dispute(log, "closure-01", "real_decision")  # no later criterion yet: a changed read is allowed
    log.record("closure-01", "maps_to_shape", "pass", "ok")
    dispute(log, "closure-01", "real_decision")  # the same read again changes nothing
    with pytest.raises(LogError, match="a read cannot change now"):
        log.record_read("closure-01", "real_decision", reply=AGREED)


def test_a_disputed_log_round_trips_and_a_hand_edit_cannot_dispute_without_a_resolution() -> None:
    log = log_of("closure-01")
    fail_at(log, "closure-01", "real_decision")
    dispute(log, "closure-01", "real_decision")
    for criterion in CRITERIA[CRITERIA.index("real_decision") + 1 :]:
        log.record("closure-01", criterion, "pass", "ok")
    again = SelectionLog.from_text(log.to_text())
    assert again.to_text() == log.to_text()
    assert again.rows["closure-01"].passed and again.rows["closure-01"].disputed("real_decision")
    saved = json.loads(log.to_text())
    del saved["rows"][0]["reads"]["real_decision"]["resolution"]
    with pytest.raises(LogError, match="resolved by him"):
        SelectionLog.from_text(json.dumps(saved))
    saved = json.loads(log.to_text())
    saved["rows"][0]["reads"]["first_disclosure"] = {
        **saved["rows"][0]["reads"]["real_decision"],
        "resolution": "x",
    }
    with pytest.raises(LogError, match="only a rejection"):
        SelectionLog.from_text(json.dumps(saved))
    for edit in ({"agrees": True}, {"reading": "fail"}):  # a verdict that differs from its reading
        saved = json.loads(log.to_text())
        saved["rows"][0]["reads"]["real_decision"].update(edit)
        with pytest.raises(LogError, match="differs from its reading"):
            SelectionLog.from_text(json.dumps(saved))
    saved = json.loads(log.to_text())
    del saved["rows"][0]["reads"]["real_decision"]["reply_sha256"]
    with pytest.raises(LogError, match="cannot be read"):  # a read with no reply is refused
        SelectionLog.from_text(json.dumps(saved))


def test_the_public_view_marks_a_disputed_rejection_and_still_carries_no_name() -> None:
    log = log_of("closure-01", "closure-02")
    fail_at(log, "closure-01", "real_decision")
    dispute(log, "closure-01", "real_decision")
    fail_at(log, "closure-02", "maps_to_shape", day=2)
    log.record_read("closure-02", "maps_to_shape", reply=AGREED)
    rows = {r["id"]: r for r in log.public_view()["closure"]["rows"]}
    assert rows["closure-01"]["criteria"]["real_decision"] == {
        "result": "fail",
        "reason": None,
        "disputed": True,
    }
    assert rows["closure-01"]["independent_read"] == {"real_decision": {"agrees": False}}
    assert "disputed" not in rows["closure-02"]["criteria"]["maps_to_shape"]
    assert "he finds it holds" not in json.dumps(log.public_view())  # the resolution is private


def test_the_log_round_trips_through_its_text() -> None:
    log = log_of("closure-01", "closure-02", "closure-f01", "ai-01")
    take(log, "closure-01", day=4)
    reject(log, "closure-02")
    log.record(
        "closure-f01", "first_disclosure", "fail", "said in June", public_reason="earlier mention"
    )
    log.record("ai-01", "first_disclosure", "pass", "ok", disclosed=D)
    for criterion in CRITERIA[1:3]:
        log.record("ai-01", criterion, "pass", "ok")
    log.record("ai-01", "real_decision", "fail", "forced")
    log.record_read("ai-01", "real_decision", reply=AGREED)
    again = SelectionLog.from_text(log.to_text())
    assert again.to_text() == log.to_text()
    assert again.selection("closure") == log.selection("closure")
    with pytest.raises(LogError, match="cannot be read"):
        SelectionLog.from_text("{")
    with pytest.raises(LogError):
        SelectionLog.from_text(json.dumps({"log_version": 99, "rows": []}))


def test_a_hand_edited_log_cannot_step_around_the_rules() -> None:
    log = log_of("ai-01", "ai-f01")
    take(log, "ai-01")  # k = 1, so the window gave k
    saved = json.loads(log.to_text())
    skipped = json.loads(json.dumps(saved))
    del skipped["rows"][0]["results"]["first_disclosure"]
    with pytest.raises(LogError, match="next criterion is first_disclosure"):
        SelectionLog.from_text(json.dumps(skipped))
    early = json.loads(json.dumps(saved))
    early["rows"][1]["results"] = {
        "first_disclosure": {
            "result": "pass",
            "reason": "r",
            "public_reason": None,
            "disclosed": "2026-07-02",
        }
    }
    with pytest.raises(LogError, match="fallback candidate"):
        SelectionLog.from_text(json.dumps(early))


def test_the_public_view_is_by_type_and_carries_no_name_accession_date_or_industry_code(
    tmp_path: Path,
) -> None:
    result, _, _ = a_search(tmp_path)
    log = SelectionLog.start(result.candidates)
    take(log, "closure-01", day=21)
    log.record("ai-01", "first_disclosure", "fail", "the Canary Cages Inc filing was not first",
               public_reason="an earlier public mention")  # fmt: skip
    take(log, "ai-02", day=17)
    text = json.dumps(log.public_view())
    for private in (
        "Canary Cages", "Fallback Cages", "0009999999", "2026-08-20", "2026-07-15", "2026-08-21",
        "2026-08-17", "3990", "6021", "7372", "ciks", "first said here",
    ):  # fmt: skip
        assert private not in text, private
    view = log.public_view()
    assert set(view) == {"closure", "retool", "ai"}
    assert view["closure"]["cases"] == 1 and view["closure"]["k"] == 2
    assert view["closure"]["complete"] is False  # the fallback candidate is not checked yet
    assert (
        view["ai"]["cases"] == 1 and view["ai"]["complete"] is True and view["ai"]["shortfall"] == 0
    )
    rows = {row["id"]: row for row in view["ai"]["rows"]}
    assert rows["ai-01"]["criteria"]["first_disclosure"] == {
        "result": "fail",
        "reason": "an earlier public mention",
    }
    assert (
        rows["ai-02"]["case"] is True
        and rows["ai-02"]["criteria"]["first_disclosure"]["reason"] is None
    )


def test_k_per_type_is_the_protocols() -> None:
    text = (ROOT / "experiment/protocol/protocol-v1.md").read_text(encoding="utf-8")
    assert "Closure or restructuring, k = 2" in text
    assert "an AI-attributed workforce change, k = 1" in text
    assert "invest or retool, k = 2" in text
    assert K == {"closure": 2, "ai": 1, "retool": 2}


def test_each_save_is_a_new_numbered_pair_of_files(tmp_path: Path) -> None:
    result, _, case = a_search(tmp_path)
    log = SelectionLog.start(result.candidates)
    assert write_log_version(case, log) == "selection-log-1.json"
    take(log, "closure-01")
    assert write_log_version(case, log) == "selection-log-2.json"
    assert (case.directory / "selection-public-2.json").is_file()
    first = SelectionLog.from_text(
        (case.directory / "selection-log-1.json").read_text(encoding="utf-8")
    )
    assert not first.rows["closure-01"].passed  # the earlier version is unchanged


def test_a_query_dataclass_is_frozen() -> None:
    with pytest.raises(AttributeError):
        CLOSURE.text = "x"  # type: ignore[misc]
    assert isinstance(CLOSURE, Query)
