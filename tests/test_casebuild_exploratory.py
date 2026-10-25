"""The exploratory record on fake rows (exploratory IMPLEMENTATION doc stage 1 step 1; §4.6.5)."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.exploratory import (
    AT_MOST,
    HELD_FILL,
    LABEL,
    POOL_CRITERIA,
    PROBE_LABEL,
    ExploratoryLog,
    load_newest_exploratory,
    read_source_log,
    write_exploratory_version,
)
from horizon_compact.casebuild.search import CRITERIA, LogError, ReaderReply, Row, SelectionLog

D = date(2026, 8, 1)
SOURCE = "selection-log-1.json"
AGREED = ReaderReply("reader-x-1-reply.json", "a" * 64, "fail")
DISPUTED = ReaderReply("reader-x-1-reply.json", "b" * 64, "pass")


def day(n: int) -> date:
    return D.replace(day=n)


def a_log(*ids: tuple[str, str, str, str]) -> ExploratoryLog:
    """Rows added as (id, type, step, pool); accessions are made up."""
    log = ExploratoryLog()
    for n, (row_id, case_type, step, pool) in enumerate(ids):
        log.add(row_id, case_type, step, pool, f"0009999999-26-{n:06d}")
    return log


def window(row_id: str) -> tuple[str, str, str, str]:
    return (row_id, row_id.split("-")[0], "2", "window")


def take(log: ExploratoryLog, row_id: str, n: int = 1) -> None:
    """Every criterion passed, in the row's own order, disclosed on August ``n``."""
    row = log.rows[row_id]
    log.record(row_id, "first_disclosure", "pass", "first said here", disclosed=day(n))
    for criterion in row.criteria[1:]:
        log.record(row_id, criterion, "pass", f"{criterion} ok")


def reject(log: ExploratoryLog, row_id: str, n: int = 1) -> None:
    log.record(row_id, "first_disclosure", "pass", "first said here", disclosed=day(n))
    log.record(row_id, "public_and_filing", "fail", "not publicly traded")


def source_text(*ids: str, stop_at: str = "real_decision") -> str:
    """A pre-registered log with each row taken through ``stop_at``."""
    rows = {}
    for n, row_id in enumerate(ids):
        case_type = row_id.split("-")[0]
        rows[row_id] = Row(row_id, case_type, "window", f"0001111111-26-{n:06d}")
    log = SelectionLog(rows)
    for n, row_id in enumerate(ids):
        log.record(row_id, "first_disclosure", "pass", "first said here", disclosed=day(n + 1))
        for criterion in CRITERIA[1 : CRITERIA.index(stop_at) + 1]:
            log.record(row_id, criterion, "pass", f"{criterion} ok")
    return log.to_text()


# --- rows ---------------------------------------------------------------------------------------------


def test_a_row_is_added_once_with_a_known_type_step_and_pool() -> None:
    log = a_log(window("closure-01"))
    with pytest.raises(LogError, match="already in the log"):
        log.add("closure-01", "closure", "2", "window", "x")
    with pytest.raises(LogError, match="a type is one of"):
        log.add("closure-02", "invest", "2", "window", "x")
    with pytest.raises(LogError, match="not one of"):
        log.add("closure-02", "closure", "3", "window", "x")
    with pytest.raises(LogError, match="not one of"):
        log.add("closure-02", "closure", "6", "pre", "x")
    with pytest.raises(LogError, match="accession"):
        log.add("closure-02", "closure", "2", "window", "  ")
    assert list(log.rows) == ["closure-01"] and len(log.events) == 1


def test_a_pool_row_has_the_knowledge_criterion_after_the_shape_and_other_rows_do_not() -> None:
    log = a_log(("pre-01", "closure", "3", "pre"), window("closure-01"))
    assert log.rows["pre-01"].criteria == POOL_CRITERIA
    assert POOL_CRITERIA.index("not_known") == CRITERIA.index("maps_to_shape") + 1
    assert log.rows["closure-01"].criteria == CRITERIA
    take(log, "pre-01")
    assert log.rows["pre-01"].passed and set(log.rows["pre-01"].results) == set(POOL_CRITERIA)
    with pytest.raises(LogError, match="not a criterion"):
        log.record("closure-01", "not_known", "pass", "r")
    log.record("closure-01", "first_disclosure", "pass", "r", disclosed=D)
    for criterion in CRITERIA[1:5]:
        log.record("closure-01", criterion, "pass", "r")
    log.record("closure-01", "not_recognizable", "pass", "r")
    assert log.rows["closure-01"].passed


def test_the_knowledge_criterion_cannot_be_skipped_and_its_rejection_must_be_read() -> None:
    log = a_log(("pre-01", "closure", "3", "pre"))
    log.record("pre-01", "first_disclosure", "pass", "r", disclosed=D)
    for criterion in CRITERIA[1:5]:
        log.record("pre-01", criterion, "pass", "r")
    with pytest.raises(LogError, match="next criterion is not_known"):
        log.record("pre-01", "not_recognizable", "pass", "r")
    log.record("pre-01", "not_known", "fail", "the model knew the plant closed")
    assert log.rows["pre-01"].awaiting_read == "not_known"
    assert not log.rows["pre-01"].finished and log.problems() == [
        "pre-01: its rejection on not_known has not been read by the independent reader"
    ]
    log.record_read("pre-01", "not_known", reply=AGREED)
    assert log.rows["pre-01"].finished and log.problems() == []


def test_a_criterion_is_recorded_as_the_selection_log_records_it() -> None:
    log = a_log(window("closure-01"))
    with pytest.raises(LogError, match="next criterion is first_disclosure"):
        log.record("closure-01", "inside_window", "pass", "r")
    with pytest.raises(LogError, match="carries its date"):
        log.record("closure-01", "first_disclosure", "pass", "r")
    with pytest.raises(LogError, match="reason"):
        log.record("closure-01", "first_disclosure", "pass", " ", disclosed=D)
    with pytest.raises(LogError, match="'pass' or 'fail'"):
        log.record("closure-01", "first_disclosure", "maybe", "r")
    with pytest.raises(LogError, match="no candidate"):
        log.record("closure-99", "first_disclosure", "pass", "r", disclosed=D)
    log.record("closure-01", "first_disclosure", "pass", "r", disclosed=D)
    log.record("closure-01", "public_and_filing", "fail", "not publicly traded")
    with pytest.raises(LogError, match="nothing follows a failure"):
        log.record("closure-01", "inside_window", "pass", "r")


def test_the_list_is_settled_at_the_shape_criterion_and_nowhere_else() -> None:
    log = a_log(window("closure-01"))
    log.record("closure-01", "first_disclosure", "pass", "r", disclosed=D)
    with pytest.raises(LogError, match="settled at maps_to_shape"):
        log.record("closure-01", "public_and_filing", "pass", "r", case_type="retool")
    for criterion in CRITERIA[1:4]:
        log.record("closure-01", criterion, "pass", "r")
    with pytest.raises(LogError, match="a list is one of"):
        log.record("closure-01", "maps_to_shape", "pass", "r", case_type="invest")
    log.record("closure-01", "maps_to_shape", "pass", "it is a retool by 12.1", case_type="retool")
    assert log.rows["closure-01"].type == "retool"


# --- carried rows -------------------------------------------------------------------------------------


def test_a_carried_row_brings_its_results_before_the_shape_and_the_shape_is_recorded_again() -> (
    None
):
    text = source_text("closure-04", "closure-05")
    log = ExploratoryLog()
    log.carry("closure-04", text, SOURCE)
    row = log.rows["closure-04"]
    assert list(row.results) == list(CRITERIA[:4]) and row.step == "2"
    assert row.source == (SOURCE, hashlib.sha256(text.encode()).hexdigest())
    assert (row.type, row.pool, row.disclosed) == ("closure", "window", day(1))
    with pytest.raises(LogError, match="next criterion is maps_to_shape"):
        log.record("closure-04", "real_decision", "pass", "again")
    with pytest.raises(LogError, match="next criterion is maps_to_shape"):
        log.record("closure-04", "first_disclosure", "pass", "again", disclosed=day(9))
    log.record("closure-04", "maps_to_shape", "pass", "S3 under 4.6.5", case_type="retool")
    log.record("closure-04", "not_recognizable", "pass", "r")
    assert row.passed and row.type == "retool"


def test_a_carried_row_is_not_carried_twice_nor_from_a_row_that_did_not_get_there() -> None:
    text = source_text("closure-04", "closure-05")
    log = ExploratoryLog()
    log.carry("closure-04", text, SOURCE)
    with pytest.raises(LogError, match="already in the log"):
        log.carry("closure-04", text, SOURCE)
    with pytest.raises(LogError, match="no candidate 'closure-99'"):
        log.carry("closure-99", text, SOURCE)
    early = source_text("closure-06", stop_at="inside_window")
    with pytest.raises(LogError, match="did not meet every criterion"):
        log.carry("closure-06", early, SOURCE)
    with pytest.raises(LogError, match=r"selection-log-<n>\.json"):
        log.carry("closure-05", text, "../elsewhere.json")
    assert list(log.rows) == ["closure-04"] and len(log.events) == 1


def test_a_carried_rejection_the_reader_disputed_carries_with_its_read() -> None:
    old = SelectionLog(
        {"closure-07": Row("closure-07", "closure", "window", "0001111111-26-000009")}
    )
    old.record("closure-07", "first_disclosure", "pass", "r", disclosed=D)
    for criterion in CRITERIA[1:3]:
        old.record("closure-07", criterion, "pass", "r")
    old.record("closure-07", "real_decision", "fail", "a forced wind-down")
    old.record_read("closure-07", "real_decision", reply=DISPUTED, resolution="his call, and why")
    log = ExploratoryLog()
    log.carry("closure-07", old.to_text(), SOURCE)
    assert log.rows["closure-07"].disputed("real_decision")
    assert log.rows["closure-07"].reads["real_decision"].resolution == "his call, and why"
    with pytest.raises(LogError, match=r"is carried from selection-log-1\.json"):
        log.record_read(  # the dispute cannot be undone here, even by a new read
            "closure-07",
            "real_decision",
            reply=ReaderReply("reader-x-2-reply.json", "e" * 64, "fail"),
        )
    assert log.rows["closure-07"].disputed("real_decision") and len(log.events) == 1


def test_a_reply_the_pre_registered_record_logged_is_never_a_read_here() -> None:
    """A carried row was rejected at criterion 4 under the old rules and read; that reply is still in its
    folder, and is a read of a different rejection."""
    old = SelectionLog(
        {"closure-04": Row("closure-04", "closure", "window", "0001111111-26-000004")}
    )
    old.record("closure-04", "first_disclosure", "pass", "r", disclosed=D)
    for criterion in CRITERIA[1:4]:
        old.record("closure-04", criterion, "pass", "r")
    old.record("closure-04", "maps_to_shape", "fail", "under 167")
    old.record_read("closure-04", "maps_to_shape", reply=AGREED)
    log = ExploratoryLog()
    log.carry("closure-04", old.to_text(), SOURCE)
    assert log.rows["closure-04"].prior_replies == {AGREED.reply}
    log.record("closure-04", "maps_to_shape", "fail", "two facilities")
    with pytest.raises(LogError, match="pre-registered record's read of an earlier rejection"):
        log.record_read("closure-04", "maps_to_shape", reply=AGREED)
    fresh = ReaderReply("reader-x-2-reply.json", "f" * 64, "fail")
    log.record_read("closure-04", "maps_to_shape", reply=fresh)
    assert log.rows["closure-04"].finished and log.rows["closure-04"].failed == "maps_to_shape"
    again = ExploratoryLog.from_text(log.to_text(), {SOURCE: old.to_text()})
    assert again.rows["closure-04"].prior_replies == {AGREED.reply}


def test_a_saved_log_replays_only_with_the_exact_source_it_carried_from() -> None:
    text = source_text("closure-04")
    log = ExploratoryLog()
    log.carry("closure-04", text, SOURCE)
    saved = log.to_text()
    assert ExploratoryLog.source_names(saved) == [SOURCE]
    assert ExploratoryLog.from_text(saved, {SOURCE: text}).rows["closure-04"].passed is False
    with pytest.raises(LogError, match="is needed"):
        ExploratoryLog.from_text(saved)
    edited = text.replace('"reason": "real_decision ok"', '"reason": "real_decision changed"')
    assert edited != text
    with pytest.raises(LogError, match="sha256 differs"):
        ExploratoryLog.from_text(saved, {SOURCE: edited})
    forged = json.loads(saved)
    forged["events"][0]["log_sha256"] = hashlib.sha256(edited.encode()).hexdigest()
    with pytest.raises(LogError, match="sha256 differs"):
        ExploratoryLog.from_text(json.dumps(forged), {SOURCE: text})


# --- the order, the fill and the stop ------------------------------------------------------------------


def test_one_order_across_types_the_window_before_the_fallback_then_the_pool_then_the_search() -> (
    None
):
    log = a_log(
        ("late-01", "closure", "5", "late"),
        ("pre-03", "closure", "4", "pre"),
        ("pre-01", "closure", "3", "pre"),
        ("closure-f01", "closure", "2", "fallback"),
        ("retool-01", "retool", "2", "window"),
        ("closure-01", "closure", "2", "window"),
    )
    take(log, "late-01", 1)
    take(log, "pre-03", 2)
    take(log, "pre-01", 3)
    take(log, "closure-f01", 4)
    take(log, "retool-01", 20)
    take(log, "closure-01", 25)
    assert [r.id for r in log.ordered()] == [
        "retool-01",  # step 2 by first disclosure, whatever the type: the 20th comes before the 25th
        "closure-01",
        "closure-f01",  # the fallback month after the window, though disclosed earlier
        "pre-01",  # then step 3 by id, then step 4's, then step 5
        "pre-03",
        "late-01",
    ]
    # the fill waits for step 5's search: until then only each type's own cases are cases
    assert log.selection().cases == ("retool-01", "closure-01", "closure-f01")
    assert log.selection().pending == ("pre-01", "pre-03", "late-01")
    log.mark_searched()
    chosen = log.selection()
    assert chosen.cases == ("retool-01", "closure-01", "closure-f01", "pre-01", "pre-03")
    assert chosen.pending == ()


def test_the_first_k_per_type_are_the_cases_and_the_rest_fill_a_short_types_slots() -> None:
    ids = [window(f"closure-{n:02d}") for n in range(1, 6)] + [window("retool-01")]
    log = a_log(*ids)
    for n in range(1, 6):
        take(log, f"closure-{n:02d}", n)
    take(log, "retool-01", 6)
    log.mark_searched()
    chosen = log.selection()
    # closure k = 2, retool k = 2 (one found), ai k = 1 (none): three slots short, one of them retool's second
    assert chosen.short_types == {"retool": 1, "ai": 1}
    assert chosen.cases == ("closure-01", "closure-02", "closure-03", "closure-04", "retool-01")
    assert chosen.filled == ("closure-03", "closure-04")
    assert chosen.complete and chosen.shortfall == 0 and len(chosen.cases) == AT_MOST


def test_a_shortfall_is_reported_when_no_candidate_is_left_to_fill_it() -> None:
    log = a_log(window("closure-01"), window("closure-02"), window("retool-01"))
    take(log, "closure-01", 1)
    take(log, "closure-02", 2)
    take(log, "retool-01", 3)
    log.mark_searched()
    chosen = log.selection()
    assert chosen.cases == ("closure-01", "closure-02", "retool-01") and chosen.filled == ()
    assert chosen.complete and chosen.shortfall == 2
    assert chosen.short_types == {"retool": 1, "ai": 1}
    log2 = a_log(window("closure-01"), window("closure-02"))
    reject(log2, "closure-01")
    take(log2, "closure-02", 2)
    log2.mark_searched()
    assert log2.selection().cases == ("closure-02",) and log2.selection().shortfall == 4


def test_the_selection_waits_while_an_earlier_candidate_is_unfinished() -> None:
    log = a_log(window("closure-01"), window("closure-02"), window("closure-03"))
    take(log, "closure-02", 5)
    take(log, "closure-03", 9)
    held = log.selection()
    assert not held.complete and held.shortfall == 0
    assert any(
        "closure-01" in line and "no first-disclosure result" in line for line in held.waiting
    )
    assert (
        held.cases == ()
    )  # closure-01 comes first and is not dated: nothing behind it is selected
    log.record("closure-01", "first_disclosure", "pass", "r", disclosed=day(2))
    still = log.selection()
    assert not still.complete and "closure-01: not finished" in still.waiting[0]
    for criterion in CRITERIA[1:3]:
        log.record("closure-01", criterion, "pass", "r")
    log.record("closure-01", "real_decision", "fail", "forced")
    assert "awaits the independent read" in log.selection().waiting[0]
    log.record_read("closure-01", "real_decision", reply=AGREED)
    assert HELD_FILL in log.selection().waiting  # nothing earlier is open now: only step 5 is
    log.mark_searched()
    assert log.selection().complete


def test_the_fill_waits_on_an_unfinished_candidate_of_a_full_type_that_comes_first() -> None:
    log = a_log(
        window("closure-01"), window("closure-02"), window("closure-03"), window("closure-04")
    )
    take(log, "closure-01", 1)
    take(log, "closure-02", 2)
    log.record("closure-03", "first_disclosure", "pass", "r", disclosed=day(3))
    take(log, "closure-04", 4)
    chosen = log.selection()
    assert not chosen.complete and chosen.filled == ()
    assert chosen.waiting[0].startswith("closure-03: not finished")
    for criterion in CRITERIA[1:]:
        log.record("closure-03", criterion, "pass", "r")
    log.mark_searched()
    assert log.selection().filled == ("closure-03", "closure-04")


def test_a_type_still_open_holds_the_fill_open() -> None:
    log = a_log(
        window("closure-01"), window("closure-02"), window("closure-03"), window("retool-01")
    )
    take(log, "closure-01", 1)
    take(log, "closure-02", 2)
    take(log, "closure-03", 3)
    log.record("retool-01", "first_disclosure", "pass", "r", disclosed=day(4))
    chosen = log.selection()
    assert not chosen.complete and chosen.filled == ()
    assert any("a type is still open" in line for line in chosen.waiting)


def test_a_row_whose_list_is_not_settled_holds_every_list_until_it_is() -> None:
    """A row's list is settled at maps_to_shape, so before then it may take any type's place (D.4): a
    complete selection must never change."""
    rows = ["closure-01", "closure-02", "closure-03", "retool-01", "retool-02", "ai-01"]
    log = a_log(*[window(r) for r in rows])
    for n, row_id in enumerate(rows, start=1):
        if row_id != "closure-03":
            take(log, row_id, n)
    log.record("closure-03", "first_disclosure", "pass", "r", disclosed=day(3))
    held = log.selection()
    assert not held.complete and held.cases == ("closure-01", "closure-02")
    assert held.waiting[0].startswith("closure-03: not finished")  # it may yet be any type
    for criterion in CRITERIA[1:4]:
        log.record("closure-03", criterion, "pass", "r")
    log.record("closure-03", "maps_to_shape", "pass", "a retool by 12.1", case_type="retool")
    still = log.selection()  # settled as retool: it now holds retool alone, and ai goes ahead
    assert not still.complete and still.cases == ("closure-01", "closure-02", "ai-01")
    log.record("closure-03", "not_recognizable", "pass", "r")
    done = log.selection()
    assert done.complete
    assert done.cases == ("closure-01", "closure-02", "closure-03", "retool-01", "ai-01")


def test_checking_stops_at_five_cases_and_not_before() -> None:
    rows = ["closure-01", "closure-02", "retool-01", "retool-02", "ai-01"]
    log = a_log(*[window(r) for r in rows])
    log.add("pre-01", "closure", "3", "pre", "0009999999-26-000099")
    log.add("pre-02", "closure", "3", "pre", "0009999999-26-000098")
    for n, row_id in enumerate(rows[:4], start=1):
        take(log, row_id, n)
    reject(log, "pre-02", 20)  # four cases, so a later candidate may still be checked
    take(log, "ai-01", 5)
    assert len(log.selection().cases) == AT_MOST and log.selection().complete
    with pytest.raises(LogError, match="after the fifth case"):
        log.record("pre-01", "first_disclosure", "pass", "r", disclosed=day(21))
    assert log.rows["pre-01"].results == {}


def test_an_unchecked_later_candidate_keeps_a_type_from_being_short() -> None:
    """D.3: a type is short only when it cannot reach k, and an unchecked row may yet be of that type."""
    log = a_log(*[window(f"closure-{n:02d}") for n in range(1, 4)])
    log.add("pre-01", "closure", "3", "pre", "0009999999-26-000099")
    for n in range(1, 4):
        take(log, f"closure-{n:02d}", n)
    waiting = log.selection()
    assert not waiting.complete and waiting.filled == ()
    reject(log, "pre-01", 9)
    log.mark_searched()
    done = log.selection()
    assert done.complete and done.filled == ("closure-03",) and done.shortfall == 2


def test_a_row_is_checked_ahead_of_an_earlier_one_but_not_past_the_fifth_case() -> None:
    log = a_log(
        window("closure-01"), ("pre-01", "closure", "3", "pre"), ("pre-02", "closure", "3", "pre")
    )
    take(log, "pre-01")  # step 3 opened early: allowed while step 2 is unfinished
    take(log, "pre-02")
    chosen = log.selection()
    assert not chosen.complete and chosen.cases == ()  # closure-01 comes first and is unfinished
    take(log, "closure-01", 4)
    log.mark_searched()
    after = log.selection()
    # the order decides, not the checking pace: closure-01, then pre-01; pre-02 fills a short slot
    assert after.cases == ("closure-01", "pre-01", "pre-02") and after.filled == ("pre-02",)
    assert after.complete and after.shortfall == 2


def test_the_fill_is_held_until_step_5_has_searched_and_pending_rows_are_not_cases() -> None:
    """His decision, 2026-10-25: a type is short only when no step left can give it a row, so a passed row
    that no type's own slots took waits, in D.1's order, and is not one of the five."""
    log = a_log(
        window("closure-01"),
        window("closure-02"),
        ("pre-01", "closure", "3", "pre"),
        ("pre-02", "closure", "3", "pre"),
    )
    for n, row_id in enumerate(["closure-01", "closure-02", "pre-01", "pre-02"], start=1):
        take(log, row_id, n)
    held = log.selection()
    assert held.cases == ("closure-01", "closure-02") and held.filled == ()
    assert held.pending == ("pre-01", "pre-02") and not held.complete and held.shortfall == 0
    assert HELD_FILL in held.waiting
    assert (
        log.public_view()["pending"] == ["pre-01", "pre-02"] and not log.public_view()["complete"]
    )
    log.mark_searched()
    done = log.selection()
    assert done.cases == ("closure-01", "closure-02", "pre-01", "pre-02")
    assert done.filled == ("pre-01", "pre-02") and done.pending == ()
    assert done.complete and done.shortfall == 1


@pytest.mark.parametrize(
    ("found", "filled"),
    [
        (
            [],
            ["pre-01", "pre-02"],
        ),  # none found: three short slots, both pending rows fill, one open
        (["retool-91"], ["pre-01", "pre-02"]),  # one found: two short slots, both fill
        (["retool-91", "retool-92"], ["pre-01"]),  # two found: one short slot, the earlier row only
        (["retool-91", "retool-92", "ai-91"], []),  # three found: no short slot, both stay out
    ],
)
def test_step_5_decides_how_many_pending_rows_fill_by_how_many_retool_and_ai_were_found(
    found: list[str], filled: list[str]
) -> None:
    log = a_log(
        window("closure-01"),
        window("closure-02"),
        ("pre-01", "closure", "3", "pre"),
        ("pre-02", "closure", "3", "pre"),
        *[(row_id, row_id.split("-")[0], "4", "pre") for row_id in found],
    )
    for n, row_id in enumerate(["closure-01", "closure-02", "pre-01", "pre-02", *found], start=1):
        take(log, row_id, n)
    log.mark_searched()
    chosen = log.selection()
    assert list(chosen.filled) == filled
    assert chosen.cases == tuple(
        r.id for r in log.ordered() if r.id in {"closure-01", "closure-02", *found, *filled}
    )
    assert chosen.complete and len(chosen.cases) == 2 + len(found) + len(filled)


def test_a_selection_with_five_own_cases_needs_no_step_5_search() -> None:
    rows = ["closure-01", "closure-02", "retool-01", "retool-02", "ai-01"]
    log = a_log(*[window(r) for r in rows])
    for n, row_id in enumerate(rows, start=1):
        take(log, row_id, n)
    assert log.selection().complete and not log.step5_searched and log.selection().pending == ()


def test_step_5s_search_is_recorded_once_and_brings_no_row_after_it() -> None:
    log = a_log(window("closure-01"), ("late-01", "closure", "5", "late"))
    log.mark_searched()
    assert log.step5_searched
    with pytest.raises(LogError, match="already recorded"):
        log.mark_searched()
    with pytest.raises(LogError, match="brings no row after that"):
        log.add("late-02", "closure", "5", "late", "0009999999-26-000099")
    log.add(
        "pre-01", "closure", "3", "pre", "0009999999-26-000098"
    )  # other steps are not held by it
    again = ExploratoryLog.from_text(log.to_text())  # and a saved log replays the mark
    assert again.step5_searched and again.selection() == log.selection()
    events = json.loads(log.to_text())["events"]
    forged = json.dumps(
        {"exploratory_version": 1, "events": [*events, {"event": "searched", "step": "4"}]}
    )
    with pytest.raises(LogError, match="only step 5's search"):
        ExploratoryLog.from_text(forged)
    # a hand-edited file with the mark put before a step 5 row is refused on replay
    early = [events[0], {"event": "searched", "step": "5"}, events[1]]
    with pytest.raises(LogError, match="brings no row after that"):
        ExploratoryLog.from_text(json.dumps({"exploratory_version": 1, "events": early}))


# --- reads --------------------------------------------------------------------------------------------


def test_a_read_takes_its_verdict_from_the_reply_and_a_dispute_needs_his_reason() -> None:
    log = a_log(window("closure-01"))
    log.record("closure-01", "first_disclosure", "pass", "r", disclosed=D)
    for criterion in CRITERIA[1:3]:
        log.record("closure-01", criterion, "pass", "r")
    log.record("closure-01", "real_decision", "fail", "forced")
    with pytest.raises(LogError, match="only a rejection on"):
        log.record_read("closure-01", "inside_window", reply=AGREED)
    with pytest.raises(LogError, match="did not fail"):
        log.record_read("closure-01", "maps_to_shape", reply=AGREED)
    with pytest.raises(LogError, match="resolved by him"):
        log.record_read("closure-01", "real_decision", reply=DISPUTED)
    with pytest.raises(LogError, match="sha256"):
        log.record_read("closure-01", "real_decision", reply=ReaderReply("r.json", "xyz", "fail"))
    log.record_read(
        "closure-01", "real_decision", reply=DISPUTED, resolution="a real choice existed"
    )
    assert log.rows["closure-01"].disputed("real_decision") and not log.rows["closure-01"].failed
    log.record("closure-01", "maps_to_shape", "pass", "r")
    with pytest.raises(LogError, match="a read cannot change now"):
        log.record_read("closure-01", "real_decision", reply=AGREED)


def test_a_type_is_read_on_the_shape_criterion_and_a_dispute_that_names_one_sets_the_list() -> None:
    log = a_log(window("closure-01"))
    log.record("closure-01", "first_disclosure", "pass", "r", disclosed=D)
    for criterion in CRITERIA[1:4]:
        log.record("closure-01", criterion, "pass", "r")
    log.record("closure-01", "maps_to_shape", "fail", "matches no shape")
    typed = ReaderReply("reader-x-1-reply.json", "b" * 64, "pass", "retool")
    with pytest.raises(LogError, match="carries no type"):
        log.record_read("closure-01", "real_decision", reply=typed)
    bad = ReaderReply("reader-x-1-reply.json", "b" * 64, "pass", "invest")
    with pytest.raises(LogError, match="a type is one of the lists"):
        log.record_read("closure-01", "maps_to_shape", reply=bad, resolution="why")
    log.record_read("closure-01", "maps_to_shape", reply=typed, resolution="it is a retool")
    row = log.rows["closure-01"]
    assert row.type == "retool" and row.disputed("maps_to_shape")  # no list restriction here
    agreed = a_log(window("closure-02"))
    agreed.record("closure-02", "first_disclosure", "pass", "r", disclosed=D)
    for criterion in CRITERIA[1:4]:
        agreed.record("closure-02", criterion, "pass", "r")
    agreed.record("closure-02", "maps_to_shape", "fail", "matches no shape")
    agreed.record_read(
        "closure-02", "maps_to_shape", reply=ReaderReply("r.json", "c" * 64, "fail", "retool")
    )
    assert agreed.rows["closure-02"].type == "closure" and agreed.rows["closure-02"].failed


def test_a_reader_who_could_not_tell_lets_the_rejection_stand() -> None:
    log2 = a_log(window("closure-02"))
    log2.record("closure-02", "first_disclosure", "pass", "r", disclosed=D)
    for criterion in CRITERIA[1:3]:
        log2.record("closure-02", criterion, "pass", "r")
    log2.record("closure-02", "real_decision", "fail", "forced")
    log2.record_read(
        "closure-02", "real_decision", reply=ReaderReply("r.json", "d" * 64, "cannot_tell")
    )
    assert log2.rows["closure-02"].failed == "real_decision" and log2.rows["closure-02"].finished


def test_one_filing_taken_as_a_case_twice_is_a_problem() -> None:
    log = ExploratoryLog()
    log.add("closure-01", "closure", "2", "window", "0001111111-26-000001")
    log.add("retool-01", "retool", "2", "window", "0001111111-26-000001")
    take(log, "closure-01", 1)
    take(log, "retool-01", 2)
    assert log.problems() == [
        "one filing is a case twice (closure-01, retool-01): one decision is one case"
    ]


# --- saving -------------------------------------------------------------------------------------------


def busy_log() -> tuple[ExploratoryLog, str]:
    text = source_text("closure-04")
    log = ExploratoryLog()
    log.carry("closure-04", text, SOURCE)
    log.record("closure-04", "maps_to_shape", "pass", "S3 under 4.6.5")
    log.record("closure-04", "not_recognizable", "pass", "not recognized")
    log.add("pre-01", "retool", "3", "pre", "0002222222-25-000001")
    take(log, "pre-01", 2)
    log.add("press-01", "closure", "2", "window", "0003333333-26-000001")
    reject(log, "press-01", 3)
    return log, text


def test_the_log_round_trips_through_its_text() -> None:
    log, text = busy_log()
    again = ExploratoryLog.from_text(log.to_text(), {SOURCE: text})
    assert again.to_text() == log.to_text()
    assert again.selection() == log.selection() and again.public_view() == log.public_view()
    assert again.rows["pre-01"].passed and again.rows["closure-04"].source is not None


def test_a_hand_edited_log_cannot_step_around_the_rules() -> None:
    log, text = busy_log()
    sources = {SOURCE: text}
    events = json.loads(log.to_text())["events"]

    def edited(change: Callable[[list[dict[str, Any]]], object]) -> str:
        copied = json.loads(json.dumps(events))
        change(copied)
        return json.dumps({"exploratory_version": 1, "events": copied})

    with pytest.raises(LogError, match="next criterion is"):  # a criterion skipped
        ExploratoryLog.from_text(edited(lambda e: e.pop(1)), sources)
    with pytest.raises(LogError, match="reason"):  # a reason blanked
        ExploratoryLog.from_text(edited(lambda e: e[1].update(reason=" ")), sources)
    with pytest.raises(LogError, match="nothing follows a failure"):
        ExploratoryLog.from_text(
            edited(lambda e: e.append({**e[-1], "criterion": "inside_window", "result": "pass"})),
            sources,
        )
    with pytest.raises(LogError, match="not an event"):
        ExploratoryLog.from_text(edited(lambda e: e[0].update(event="delete")), sources)
    with pytest.raises(LogError, match="cannot be read"):
        ExploratoryLog.from_text(edited(lambda e: e[0].pop("id")), sources)
    with pytest.raises(LogError, match="version"):
        ExploratoryLog.from_text(json.dumps({"exploratory_version": 2, "events": []}))
    with pytest.raises(LogError, match="cannot be read"):
        ExploratoryLog.from_text("not json")


def test_the_failed_change_leaves_nothing_behind() -> None:
    log = a_log(window("closure-01"))
    before = log.to_text()
    with pytest.raises(LogError):
        log.record("closure-01", "inside_window", "pass", "r")
    assert log.to_text() == before


def test_each_save_is_a_new_numbered_pair_and_the_newest_loads_with_its_source(
    tmp_path: Path,
) -> None:
    case = CaseAppendix(root=tmp_path, label="search")
    case.directory.mkdir(parents=True)
    assert load_newest_exploratory(case).rows == {}  # none written yet
    text = source_text("closure-04")
    (case.directory / SOURCE).write_text(text, encoding="utf-8")
    log = ExploratoryLog()
    log.carry("closure-04", read_source_log(case, SOURCE), SOURCE)
    assert write_exploratory_version(case, log) == "exploratory-log-1.json"
    log.record("closure-04", "maps_to_shape", "pass", "r")
    assert write_exploratory_version(case, log) == "exploratory-log-2.json"
    assert (case.directory / "exploratory-public-2.json").is_file()
    for n in range(3, 11):  # copies, so only the highest number is the newest
        (case.directory / f"exploratory-log-{n}.json").write_text(log.to_text(), encoding="utf-8")
    assert write_exploratory_version(case, log) == "exploratory-log-11.json"
    loaded = load_newest_exploratory(case)
    assert "maps_to_shape" in loaded.rows["closure-04"].results
    first = json.loads((case.directory / "exploratory-log-1.json").read_text())["events"]
    assert len(first) == 1  # the earlier version is unchanged
    (case.directory / SOURCE).write_text(text + " ", encoding="utf-8")  # the source changed
    with pytest.raises(LogError, match="sha256 differs"):
        load_newest_exploratory(case)
    with pytest.raises(LogError, match=r"selection-log-<n>\.json"):
        read_source_log(case, "candidates.json")


# --- the public view ----------------------------------------------------------------------------------


def test_the_public_view_labels_every_case_and_carries_no_name_accession_or_date() -> None:
    log, _ = busy_log()
    log.mark_searched()
    view = log.public_view()
    text = json.dumps(view)
    for private in ("0001111111", "0002222222", "0003333333", "2026-08", "first said here"):
        assert private not in text
    by_id = {r["id"]: r for r in view["rows"]}
    assert by_id["closure-04"]["label"] == LABEL.format(step="2") and by_id["closure-04"]["carried"]
    assert by_id["pre-01"]["label"] == f"{LABEL.format(step='3')}; {PROBE_LABEL}"
    assert "label" not in by_id["press-01"] and not by_id["press-01"]["case"]
    assert view["cases"] == ["closure-04", "pre-01"] and view["at_most"] == AT_MOST
    assert view["types"]["retool"] == {"k": 2, "cases": 1} and view["shortfall"] == 3
    assert "not_known" in by_id["pre-01"]["criteria"]


def test_the_probe_label_states_both_cut_offs_as_the_protocol_does() -> None:
    assert "Haiku 5.5, June 2026" in PROBE_LABEL and "gpt-oss-120b, June 2024" in PROBE_LABEL
    assert "both official models and the extraction model" in PROBE_LABEL
    assert (
        LABEL
        == "exploratory: selected by §4.6.5 step {step}, after the pre-registered rule found none"
    )


def test_a_public_reason_appears_only_where_one_was_written() -> None:
    log = a_log(window("closure-01"))
    log.record(
        "closure-01",
        "first_disclosure",
        "fail",
        "private words",
        public_reason="an earlier public mention",
    )
    row = log.public_view()["rows"][0]
    assert row["criteria"]["first_disclosure"]["reason"] == "an earlier public mention"
    assert "private words" not in json.dumps(log.public_view())
