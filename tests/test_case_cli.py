"""``hc case foreshadow`` and ``hc case hashes`` (Phase 5 code half, build step 6); ``hc case search``
(search half, Stage A)."""

from __future__ import annotations

import functools
import hashlib
import json
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from edgar_helpers import (
    CUTOFF_FILINGS,
    FACTS_URL,
    SUBMISSIONS_URL,
    USER_AGENT,
    FakeTransport,
    archive_url,
    doc_name,
    filing_table,
    world,
)
from horizon_compact import cli
from horizon_compact.casebuild import assemble as assemble_module
from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.edgar import EdgarClient
from horizon_compact.casebuild.exploratory import (
    ExploratoryLog,
    ExploratoryRow,
    candidate_records,
    newest_selection_log_name,
    read_source_log,
    row_for,
    write_exploratory_version,
)
from horizon_compact.casebuild.extract import instructions_sha256
from horizon_compact.casebuild.scenario import _disclosure_failures
from horizon_compact.casebuild.search import (
    CRITERIA,
    FALLBACK_START,
    QUERIES,
    RULE_DATE,
    LogError,
    Row,
    SelectionLog,
    search_url,
    write_log_version,
)
from horizon_compact.cli import CHECK_FAILED_EXIT, CLEAN_EXIT, REFUSED_EXIT, main
from horizon_compact.protocol.cases import (
    CaseContent,
    check_case_content,
    content_hashes,
    parse_case,
)
from horizon_compact.reader.read import ReaderError, probe_read_ready, rejection_ready
from test_casebuild_assemble import COUNTS, PLAIN, Scripted, fill_in
from test_casebuild_extract import FACTS, FakeTextProvider, ok
from test_casebuild_frozen import fake_git
from test_casebuild_search import AGREED, DISPUTED

DOSSIER = b'title = "t"\ntext = """x"""\n'
SCENARIO = b'title = "s"\ntext = """y"""\n'
RUBRIC = b"rubric, not a dossier\n"


@pytest.fixture
def appendix(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("HC_APPENDIX_DIR", str(tmp_path))
    case = tmp_path / "closure-1"
    case.mkdir()
    (case / "dossier.toml").write_bytes(DOSSIER)
    (case / "scenario.toml").write_bytes(SCENARIO)
    (tmp_path / "rubric.md").write_bytes(RUBRIC)
    return tmp_path


def test_hashes_prints_a_case_lock_the_gate_reads_back_and_accepts(
    appendix: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert (
        main(["case", "hashes", "closure-1", "--rubric", str(appendix / "rubric.md")]) == CLEAN_EXIT
    )
    record = parse_case(capsys.readouterr().out, "closure-1")
    assert record.probe_set == 1
    assert check_case_content(record, CaseContent(DOSSIER, SCENARIO, RUBRIC)) == []


def test_hashes_agree_with_the_function_the_gate_uses_and_with_sha256(
    appendix: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    main(
        ["case", "hashes", "closure-1", "--rubric", str(appendix / "rubric.md"), "--probe-set", "2"]
    )
    record = parse_case(capsys.readouterr().out, "closure-1")
    expected = content_hashes(CaseContent(DOSSIER, SCENARIO, RUBRIC))
    assert record.probe_set == 2
    assert (record.dossier_sha256, record.scenario_sha256, record.rubric_sha256) == (
        expected["dossier_sha256"],
        expected["scenario_sha256"],
        expected["rubric_sha256"],
    )
    assert record.dossier_sha256 == hashlib.sha256(DOSSIER).hexdigest()


def test_a_changed_dossier_no_longer_hashes_to_the_printed_record(
    appendix: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    main(["case", "hashes", "closure-1", "--rubric", str(appendix / "rubric.md")])
    record = parse_case(capsys.readouterr().out, "closure-1")
    failures = check_case_content(record, CaseContent(DOSSIER + b" ", SCENARIO, RUBRIC))
    assert failures == ["the dossier does not hash to experiment/cases/closure-1/case.lock"]


def test_hashes_refuses_a_missing_file_or_a_bad_label(
    appendix: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert (
        main(["case", "hashes", "closure-1", "--rubric", str(appendix / "none.md")]) == REFUSED_EXIT
    )
    assert "refused: cannot read a case file" in capsys.readouterr().err
    assert (
        main(["case", "hashes", "Bad Label", "--rubric", str(appendix / "rubric.md")])
        == REFUSED_EXIT
    )


def test_foreshadow_fails_on_a_hit_and_writes_it_down(
    appendix: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    terms = appendix / "terms.txt"
    terms.write_text("# key terms\nwidgets\n", encoding="utf-8")
    (appendix / "closure-1" / "scenario.toml").write_text(
        'text = "about widgets"\n', encoding="utf-8"
    )
    assert main(["case", "foreshadow", "closure-1", "--terms", str(terms)]) == CHECK_FAILED_EXIT
    captured = capsys.readouterr()
    assert "scenario line 1: 'widgets'" in captured.err and "foreshadow-1.json" in captured.out
    assert (appendix / "closure-1" / "foreshadow-1.json").is_file()


def test_foreshadow_with_no_hit_is_clean_and_still_writes_a_record(
    appendix: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    terms = appendix / "terms.txt"
    terms.write_text("widgets\n", encoding="utf-8")
    assert main(["case", "foreshadow", "closure-1", "--terms", str(terms)]) == CLEAN_EXIT
    assert "no hits (foreshadow-1.json)" in capsys.readouterr().out


def test_foreshadow_refuses_without_a_scenario_text(
    appendix: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    terms = appendix / "terms.txt"
    terms.write_text("widgets\n", encoding="utf-8")
    (appendix / "closure-1" / "scenario.toml").unlink()
    assert main(["case", "foreshadow", "closure-1", "--terms", str(terms)]) == REFUSED_EXIT
    assert "scenario.toml" in capsys.readouterr().err


# --- hc case search (search-half IMPLEMENTATION doc §4.4) ------------------------------------------------


def _search_setup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, today: date
) -> tuple[Path, FakeTransport]:
    """Every query answered on the real reply's shape (read 2026-10-15, doc §11): one closure hit in the
    window, one in the fallback month, one dropped by the SIC filter, and an 8-K/A the form filter drops."""
    from test_casebuild_search import page, raw_hit

    end = RULE_DATE - timedelta(days=1)
    replies = {search_url(q, FALLBACK_START, end, 0): page([], 0) for q in QUERIES}
    replies[search_url(QUERIES[0], FALLBACK_START, end, 0)] = page(
        [
            raw_hit("0009999999-26-000030", "2026-08-20", items=["2.05", "7.01"]),
            raw_hit("0009999999-26-000010", "2026-07-15"),
            raw_hit("0009999999-26-000050", "2026-09-03", sics=["5311"]),
            raw_hit("0009999999-26-000060", "2026-09-04", form="8-K/A"),
        ],
        4,
    )
    transport = FakeTransport(replies)
    monkeypatch.setenv("HC_APPENDIX_DIR", str(tmp_path))
    monkeypatch.setenv("HC_SEC_USER_AGENT", USER_AGENT)
    monkeypatch.setattr(cli, "_today", lambda: today)
    monkeypatch.setattr(cli, "UrllibTransport", lambda: transport)
    monkeypatch.setattr(
        cli, "EdgarClient", functools.partial(EdgarClient, clock=lambda: 0.0, sleep=lambda s: None)
    )
    return tmp_path / "search", transport


def test_search_on_the_rule_date_writes_candidates_and_a_log_and_prints_no_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder, transport = _search_setup(tmp_path, monkeypatch, RULE_DATE)
    assert main(["case", "search", "--date", RULE_DATE.isoformat()]) == CLEAN_EXIT
    out = capsys.readouterr().out
    assert "Canary" not in out and "0009999999" not in out
    assert "closure/window: 1 candidates" in out and "closure/fallback: 1 candidates" in out
    assert "form is 8-K/A, not 8-K" in out
    assert len(transport.requests) == len(QUERIES)
    record = json.loads((folder / "candidates.json").read_text())
    assert record["end"] == "2026-10-15" and record["run_on"] == "2026-10-16"
    assert record["deviation"] is None
    assert [c["id"] for c in record["list"]] == ["closure-f01", "closure-01"]  # by filing date
    assert (folder / "selection-log-1.json").exists()
    assert (folder / "selection-public-1.json").exists()


def test_search_runs_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _search_setup(tmp_path, monkeypatch, RULE_DATE)
    assert main(["case", "search", "--date", RULE_DATE.isoformat()]) == CLEAN_EXIT
    assert main(["case", "search", "--date", RULE_DATE.isoformat()]) == REFUSED_EXIT
    assert "already run" in capsys.readouterr().err


def test_search_refuses_a_date_that_is_not_today_and_any_day_before_the_rule_date(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder, transport = _search_setup(tmp_path, monkeypatch, RULE_DATE - timedelta(days=1))
    assert main(["case", "search", "--date", RULE_DATE.isoformat()]) == REFUSED_EXIT
    assert "is not today" in capsys.readouterr().err
    assert main(["case", "search", "--date", "2026-10-15"]) == REFUSED_EXIT
    assert "not before" in capsys.readouterr().err
    assert transport.requests == [] and not folder.exists()


def test_a_late_search_needs_a_reason_and_keeps_the_rule_dates_window(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    late = RULE_DATE + timedelta(days=2)
    folder, transport = _search_setup(tmp_path, monkeypatch, late)
    assert main(["case", "search", "--date", late.isoformat()]) == REFUSED_EXIT
    assert "deviation" in capsys.readouterr().err
    assert transport.requests == []
    assert (
        main(["case", "search", "--date", late.isoformat(), "--deviation", "the SEC was down"])
        == CLEAN_EXIT
    )
    record = json.loads((folder / "candidates.json").read_text())
    assert record["end"] == "2026-10-15" and record["search_date"] == "2026-10-16"
    assert record["run_on"] == late.isoformat() and record["deviation"] == "the SEC was down"


def test_the_rule_date_is_the_day_after_the_results_commit() -> None:
    assert date(2026, 10, 16) == RULE_DATE


# --- hc case log (search-half IMPLEMENTATION doc §4.3) ------------------------------------------------------


def _log_setup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> Path:
    """A search run on fake replies: closure-01 in the window, closure-f01 in the fallback month."""
    folder, _ = _search_setup(tmp_path, monkeypatch, RULE_DATE)
    assert main(["case", "search", "--date", RULE_DATE.isoformat()]) == CLEAN_EXIT
    capsys.readouterr()
    return folder


def _log(*words: str) -> int:
    return main(["case", "log", *words])


def _guard_terms(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A fictional term file, set explicitly so no test ever reads the real one through git config."""
    folder = tmp_path / "guard"
    folder.mkdir()
    longlist = folder / "longlist.md"
    longlist.write_text("a fictional longlist\n", encoding="utf-8")
    digest = hashlib.sha256(longlist.read_bytes()).hexdigest()
    terms = folder / "terms.txt"
    terms.write_text(
        f"longlist: {longlist}\nlonglist-sha256: {digest}\nterm-i: Zarnothic\n", encoding="utf-8"
    )
    monkeypatch.setenv("HC_NAME_GUARD_TERMS", str(terms))


def test_log_record_writes_the_next_version_and_leaves_the_earlier_one_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _log_setup(tmp_path, monkeypatch, capsys)
    first = (folder / "selection-log-1.json").read_bytes()
    args = ["closure", "record", "closure-01", "first_disclosure", "pass"]
    assert _log(*args, "--reason", "first said here", "--disclosed", "2026-08-18") == CLEAN_EXIT
    assert "wrote selection-log-2.json" in capsys.readouterr().out
    assert (folder / "selection-log-1.json").read_bytes() == first
    assert (folder / "selection-public-2.json").is_file()
    assert (
        _log("closure", "record", "closure-01", "public_and_filing", "fail", "--reason", "x") == 0
    )
    assert "wrote selection-log-3.json" in capsys.readouterr().out
    rows = json.loads((folder / "selection-log-3.json").read_text())["rows"]
    done = next(r for r in rows if r["id"] == "closure-01")
    assert list(done["results"]) == ["first_disclosure", "public_and_filing"]


def test_log_loads_the_newest_version_by_number_not_by_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _log_setup(tmp_path, monkeypatch, capsys)
    text = (folder / "selection-log-1.json").read_text()
    for n in range(2, 11):  # copies of the empty log, so only the highest number is newest
        (folder / f"selection-log-{n}.json").write_text(text)
    args = ["closure", "record", "closure-01", "first_disclosure", "pass", "--reason", "r"]
    assert _log(*args, "--disclosed", "2026-08-18") == CLEAN_EXIT
    assert "wrote selection-log-11.json" in capsys.readouterr().out


def test_log_refuses_what_the_log_refuses_and_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _log_setup(tmp_path, monkeypatch, capsys)
    before = sorted(p.name for p in folder.iterdir())
    refused = [
        # out of order: the first criterion is first_disclosure
        ["closure", "record", "closure-01", "public_and_filing", "pass", "--reason", "r"],
        # a passed first_disclosure with no date
        ["closure", "record", "closure-01", "first_disclosure", "pass", "--reason", "r"],
        # a date on a result that carries none
        [
            "closure",
            "record",
            "closure-01",
            "first_disclosure",
            "fail",
            "--reason",
            "r",
            "--disclosed",
            "2026-08-18",
        ],
        # a blank reason
        ["closure", "record", "closure-01", "first_disclosure", "fail", "--reason", "  "],
        # a fallback candidate while the window is unchecked
        ["closure", "record", "closure-f01", "first_disclosure", "fail", "--reason", "r"],
        # no such candidate
        ["closure", "record", "closure-99", "first_disclosure", "fail", "--reason", "r"],
        # a read of a candidate that was not rejected
        ["closure", "read", "closure-01", "real_decision"],
    ]
    for words in refused:
        assert _log(*words) == REFUSED_EXIT, words
        assert capsys.readouterr().err.startswith("refused:")
    assert sorted(p.name for p in folder.iterdir()) == before


def test_log_refuses_an_id_of_another_type(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _log_setup(tmp_path, monkeypatch, capsys)
    words = ["retool", "record", "closure-01", "first_disclosure", "fail", "--reason", "r"]
    assert _log(*words) == REFUSED_EXIT
    assert "is a closure candidate, not retool" in capsys.readouterr().err
    assert not (folder / "selection-log-2.json").exists()


def _reply_on_disk(
    folder: Path, reading: str, criterion: str = "real_decision", decision_type: str | None = None
) -> None:
    """A usable reader reply in closure-01's folder, as `hc case reader` writes it."""
    case = folder.parent / "closure-01"
    case.mkdir(exist_ok=True)
    stem = case / f"reader-rejection-{criterion}-1"
    Path(f"{stem}-request.json").write_text(json.dumps({"material_sha256": {}}), encoding="utf-8")
    parsed = {"reading": reading, "type": decision_type}
    reply = {"usable": True, "parsed": parsed, "estimated_usd": "0.01"}
    Path(f"{stem}-reply.json").write_text(json.dumps(reply), encoding="utf-8")


def _rejected_on_real_decision(capsys: pytest.CaptureFixture[str]) -> None:
    assert _log("closure", "record", "closure-01", "first_disclosure", "pass", "--reason", "r",
                "--disclosed", "2026-08-18") == CLEAN_EXIT  # fmt: skip
    assert (
        _log("closure", "record", "closure-01", "public_and_filing", "pass", "--reason", "r") == 0
    )
    assert _log("closure", "record", "closure-01", "inside_window", "pass", "--reason", "r") == 0
    assert _log("closure", "record", "closure-01", "real_decision", "fail", "--reason", "r") == 0
    capsys.readouterr()


def test_log_read_takes_its_verdict_from_the_readers_reply_and_needs_a_resolution_on_a_dispute(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _log_setup(tmp_path, monkeypatch, capsys)
    _rejected_on_real_decision(capsys)
    assert _log("closure", "read", "closure-01", "real_decision") == REFUSED_EXIT
    assert "no usable read" in capsys.readouterr().err  # a read never made cannot be logged
    _reply_on_disk(folder, "pass")
    assert _log("closure", "read", "closure-01", "real_decision") == REFUSED_EXIT
    assert "resolved by him" in capsys.readouterr().err
    words = ["closure", "read", "closure-01", "real_decision"]
    assert _log(*words, "--resolution", "his call, and why") == CLEAN_EXIT
    out = capsys.readouterr().out
    assert "real_decision: pass (disputes)" in out
    assert "read: DISAGREES" in out and "wrote selection-log-6.json" in out
    assert "from reader-rejection-real_decision-1-reply.json" in out
    saved = json.loads((folder / "selection-log-6.json").read_text())["rows"]
    read = next(r for r in saved if r["id"] == "closure-01")["reads"]["real_decision"]
    assert read["reading"] == "pass" and read["agrees"] is False and len(read["reply_sha256"]) == 64


def test_log_read_of_a_pass_of_another_type_says_it_agrees(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # A pass whose decision is retool, on the closure list, agrees with the rejection (search-half doc
    # §4.6.4): the line he reads says so, as the record does.
    folder = _log_setup(tmp_path, monkeypatch, capsys)
    assert _log("closure", "record", "closure-01", "first_disclosure", "pass", "--reason", "r",
                "--disclosed", "2026-08-18") == CLEAN_EXIT  # fmt: skip
    for criterion in ("public_and_filing", "inside_window", "real_decision"):
        assert _log("closure", "record", "closure-01", criterion, "pass", "--reason", "r") == 0
    assert _log("closure", "record", "closure-01", "maps_to_shape", "fail", "--reason", "r") == 0
    capsys.readouterr()
    _reply_on_disk(folder, "pass", "maps_to_shape", "retool")
    assert _log("closure", "read", "closure-01", "maps_to_shape") == CLEAN_EXIT
    out = capsys.readouterr().out
    assert "maps_to_shape: pass (agrees)" in out and "disputes" not in out
    assert "read: agrees" in out and "finished: rejected" in out


def test_log_read_of_a_reader_who_could_not_tell_lets_the_rejection_stand(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _log_setup(tmp_path, monkeypatch, capsys)
    _rejected_on_real_decision(capsys)
    _reply_on_disk(folder, "cannot_tell")
    assert _log("closure", "read", "closure-01", "real_decision") == CLEAN_EXIT
    out = capsys.readouterr().out
    assert "read: could not tell (stands)" in out and "finished: rejected" in out


def test_log_public_prints_the_public_view_with_no_name_and_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _log_setup(tmp_path, monkeypatch, capsys)
    _guard_terms(tmp_path, monkeypatch)
    words = ["closure", "record", "closure-01", "first_disclosure", "fail"]
    secret = "the Canary Cages Inc filing was not first"
    assert _log(*words, "--reason", secret, "--public-reason", "an earlier public mention") == 0
    capsys.readouterr()
    before = sorted(p.name for p in folder.iterdir())
    assert _log("closure", "public") == CLEAN_EXIT
    out = capsys.readouterr().out
    for private in ("Canary", "0009999999", "2026-08", "2026-07", secret, "3990", "ciks"):
        assert private not in out, private
    view = json.loads(out)
    assert set(view) == {"closure"}  # the type named, not every type
    row = next(r for r in view["closure"]["rows"] if r["id"] == "closure-01")
    assert row["criteria"]["first_disclosure"] == {
        "result": "fail",
        "reason": "an earlier public mention",
    }
    assert sorted(p.name for p in folder.iterdir()) == before


def test_log_without_a_public_reason_leaves_the_public_reason_empty_not_the_private_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _log_setup(tmp_path, monkeypatch, capsys)
    secret = "the Canary Cages Inc filing was not first"
    assert (
        _log("closure", "record", "closure-01", "first_disclosure", "fail", "--reason", secret) == 0
    )
    capsys.readouterr()
    assert _log("closure", "public") == CLEAN_EXIT
    out = capsys.readouterr().out
    assert "Canary" not in out
    row = next(r for r in json.loads(out)["closure"]["rows"] if r["id"] == "closure-01")
    assert row["criteria"]["first_disclosure"]["reason"] is None


def test_log_show_prints_the_candidates_with_their_names_and_their_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _log_setup(tmp_path, monkeypatch, capsys)
    before = sorted(p.name for p in folder.iterdir())
    assert _log("closure", "show") == CLEAN_EXIT
    out = capsys.readouterr().out
    assert "closure-01 window filed 2026-08-20 0009999999-26-000030 Canary Cages Inc" in out
    assert "closure-f01 fallback" in out and "next: first_disclosure" in out
    assert "waiting: closure-01: no first-disclosure result" in out
    assert out.count("filed ") == 2  # the two closure candidates; no other type's
    assert sorted(p.name for p in folder.iterdir()) == before


def test_log_refuses_before_the_search_has_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("HC_APPENDIX_DIR", str(tmp_path))
    assert _log("closure", "show") == REFUSED_EXIT
    assert "the search has not run" in capsys.readouterr().err


@pytest.mark.parametrize(
    "reason",
    [
        "Canary Cages said so first",  # the display name without its legal form
        "canary cages said so first",  # in any case
        "found under 0009999999-26-000030",  # the accession number
        "the filer 9999999 said so",  # the CIK without its leading zeros
        "a Zarnothic report came first",  # a term from the name guard's list
        "an earlier mention on 2026-07-02",  # a date
        "   ",  # blank
    ],
)
def test_log_refuses_a_public_reason_that_identifies_and_writes_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    reason: str,
) -> None:
    folder = _log_setup(tmp_path, monkeypatch, capsys)
    _guard_terms(tmp_path, monkeypatch)
    before = sorted(p.name for p in folder.iterdir())
    words = ["closure", "record", "closure-01", "first_disclosure", "fail", "--reason", "r"]
    assert _log(*words, "--public-reason", reason) == REFUSED_EXIT
    err = capsys.readouterr().err
    assert err.startswith("refused:") and "Canary" not in err and "Zarnothic" not in err
    assert sorted(p.name for p in folder.iterdir()) == before


def test_log_refuses_a_public_reason_it_cannot_check_without_the_term_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _log_setup(tmp_path, monkeypatch, capsys)
    monkeypatch.setenv("HC_NAME_GUARD_TERMS", str(tmp_path / "no-such-file"))
    words = ["closure", "record", "closure-01", "first_disclosure", "fail", "--reason", "r"]
    assert _log(*words, "--public-reason", "an earlier public mention") == REFUSED_EXIT
    assert "without the name guard" in capsys.readouterr().err
    assert not (folder / "selection-log-2.json").exists()


def test_candidate_terms_catch_the_name_tickers_and_numbers_not_ordinary_words() -> None:
    from horizon_compact.casebuild.search import candidate_terms

    record = {
        "names": ["Zarnoth Widget Works, Inc.  (ZWW, ZWWP)  (CIK 0000123456)"],
        "ciks": ["0000123456"],
        "accession": "0000123456-26-000001",
    }
    terms = candidate_terms(record)

    def hit(text: str) -> bool:
        return any(term.pattern.search(text) for term in terms)

    for text in ("zarnoth widget works", "ZWW", "ZWWP", "123456", "0000123456-26-000001"):
        assert hit(text), text
    for text in ("a widget plant", "zww", "an earlier public mention", "1234567"):
        assert not hit(text), text
    short = candidate_terms({"names": ["QX INC  (CIK 0000000042)"]})
    assert any(term.pattern.search("filed by QX") for term in short)
    assert not any(term.pattern.search("a qx b") for term in short)


# --- hc case build and hc case assemble (search-half IMPLEMENTATION doc §4.5) ---------------------------

BUILD_CUTOFF = date(2026, 6, 15)


class _Providers:
    """The extraction provider the build asks for: ``made`` holds each one given (none before a refusal)."""

    def __init__(self, provider: Any) -> None:
        self.provider = provider
        self.made: list[Any] = []

    def __call__(self) -> Any:
        self.made.append(self.provider)
        return self.provider


def _build_setup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    provider: Any = None,
    extra: dict[str, Any] | None = None,
    passes: int = 5,
    disputed: str | None = None,
    agreed: str | None = None,
    disclosed: date = date(2026, 6, 16),
    ciks: tuple[str, ...] = ("0009999999",),
    remotes: str = "  origin/main\n",
    terms: bool = True,
) -> tuple[Path, FakeTransport, _Providers]:
    """A search folder with one candidate that passed ``passes`` criteria, a case folder with its term list, a
    fake SEC and a fake extraction provider. Fictional canaries throughout; nothing real is read or called."""
    _, transport = world(tmp_path / "unused", {FACTS_URL: FACTS, **(extra or {})})
    app = tmp_path / "appendix"
    search = CaseAppendix(root=app, label="search")
    record = {
        "list": [{"id": "closure-01", "ciks": list(ciks), "names": ["Fernwick Canary Holdings"]}]
    }
    search.write_once(search.directory / "candidates.json", json.dumps(record).encode())
    log = SelectionLog(
        {"closure-01": Row("closure-01", "closure", "window", "0009999999-26-000099")}
    )
    log.record("closure-01", "first_disclosure", "pass", "r", disclosed=disclosed)
    for criterion in CRITERIA[1:passes]:
        if criterion == agreed:  # rejected, and the independent reader agrees: nothing follows
            log.record("closure-01", criterion, "fail", "r")
            log.record_read("closure-01", criterion, reply=AGREED)
            break
        if criterion == disputed:  # rejected, and the independent reader disputes it
            log.record("closure-01", criterion, "fail", "r")
            log.record_read("closure-01", criterion, reply=DISPUTED, resolution="he finds it holds")
        else:
            log.record("closure-01", criterion, "pass", "r")
    write_log_version(search, log)
    if terms:
        (app / "closure-01").mkdir(exist_ok=True)
        (app / "closure-01" / "terms.txt").write_text(
            "term: Fernwick Canary Holdings => the Company\n", encoding="utf-8"
        )
    providers = _Providers(provider or Scripted(PLAIN))
    monkeypatch.setenv("HC_APPENDIX_DIR", str(app))
    monkeypatch.setenv("HC_SEC_USER_AGENT", USER_AGENT)
    monkeypatch.setattr(cli, "UrllibTransport", lambda: transport)
    monkeypatch.setattr(
        cli, "EdgarClient", functools.partial(EdgarClient, clock=lambda: 0.0, sleep=lambda s: None)
    )
    monkeypatch.setattr(cli, "git_in", lambda repo: fake_git(remotes=remotes))
    monkeypatch.setattr(cli, "_extraction_provider", providers)
    return app, transport, providers


def _build(*extra: str, cutoff: date = BUILD_CUTOFF, shape: str = "S3") -> int:
    return main(
        ["case", "build", "closure-01", "--cutoff", cutoff.isoformat(), "--shape", shape, *extra]
    )


def test_build_writes_the_case_from_the_candidates_cik_and_records_where_it_came_from(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    app, transport, providers = _build_setup(tmp_path, monkeypatch)
    assert _build() == CLEAN_EXIT
    out = capsys.readouterr().out
    assert "Fernwick" not in out and "0009999999" not in out and "the Company" not in out
    folder = app / "closure-01"
    for name in ("sources.json", "sections.json", "build.json", "reviewed-flags.template.json"):
        assert (folder / name).is_file(), name
    assert transport.requests[0][0] == SUBMISSIONS_URL  # the CIK came from candidates.json
    build = json.loads((folder / "build.json").read_text())
    provenance = build["provenance"]
    assert provenance["extraction_inputs_commit"] == "a" * 40
    assert provenance["instructions_sha256"] == instructions_sha256()
    assert provenance["extraction_model"] == "sonnet-5-5-extraction"
    assert provenance["extraction_entry_sha256"] and provenance["hand_boundaries_sha256"] is None
    assert build["extraction"]["instructions_sha256"] == instructions_sha256()
    assert build["extraction"]["max_tokens"] == 4096
    assert isinstance(build["seed"], int) and build["shape"] == "S3"
    sent = providers.provider.requests
    assert {r.route.model_id for r in sent} == {"claude-sonnet-5-5"}
    assert all(
        r.route.thinking_between_tools and not r.route.thinking_off and r.max_tokens == 4096
        for r in sent
    )
    assert "about $" in out and "hc case assemble closure-01" in out


@pytest.mark.parametrize("criterion", ["real_decision", "maps_to_shape"])
def test_build_accepts_a_candidate_whose_rejection_the_reader_disputed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, criterion: str
) -> None:
    _build_setup(tmp_path, monkeypatch, disputed=criterion)
    assert _build() == CLEAN_EXIT


def test_build_still_refuses_a_rejection_that_stands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _, transport, providers = _build_setup(tmp_path, monkeypatch, agreed="real_decision")
    assert _build() == REFUSED_EXIT
    assert "has not passed real_decision" in capsys.readouterr().err
    assert transport.requests == [] and providers.made == []


def test_build_cannot_be_given_a_seed_or_a_cik_and_never_passes_one_on(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _build_setup(tmp_path, monkeypatch)
    for flag in ("--seed", "--cik", "--model", "--max-tokens"):
        with pytest.raises(SystemExit):
            _build(flag, "1")
    seen: dict[str, Any] = {}
    real = assemble_module.prepare_case

    def spy(*args: Any, **kwargs: Any) -> Any:
        seen.update(kwargs)
        return real(*args, **kwargs)

    monkeypatch.setattr(cli, "prepare_case", spy)
    assert _build() == CLEAN_EXIT
    assert "new_seed" not in seen  # the default, scale.new_seed, is what ran
    assert seen["max_tokens"] == 4096


@pytest.mark.parametrize(
    ("setup", "words"),
    [
        ({"passes": 4}, "has not passed maps_to_shape"),
        ({"passes": 3}, "has not passed real_decision, maps_to_shape"),
        (
            {"passes": 1},
            "has not passed public_and_filing, inside_window, real_decision, maps_to_shape",
        ),
        ({"terms": False}, "term list"),
        ({"remotes": ""}, "not on any remote branch"),
        ({"ciks": ("0009999999", "0008888888")}, "exactly one"),
    ],
)
def test_build_refuses_before_any_fetch_or_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    setup: dict[str, Any],
    words: str,
) -> None:
    app, transport, providers = _build_setup(tmp_path, monkeypatch, **setup)
    assert _build() == REFUSED_EXIT
    assert words in capsys.readouterr().err
    assert transport.requests == [] and providers.made == []
    assert not (app / "closure-01" / "sources.json").exists()


def test_build_refuses_a_cutoff_that_is_not_the_day_before_first_disclosure_and_an_unknown_label(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _, transport, providers = _build_setup(tmp_path, monkeypatch)
    assert _build(cutoff=date(2026, 6, 16)) == REFUSED_EXIT
    assert "day before first disclosure" in capsys.readouterr().err
    assert (
        main(["case", "build", "closure-09", "--cutoff", "2026-06-15", "--shape", "S3"])
        == REFUSED_EXIT
    )
    assert "not a candidate" in capsys.readouterr().err
    assert transport.requests == [] and providers.made == []


def test_build_stops_for_hand_boundaries_before_the_key_and_writes_nothing_but_the_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    name = doc_name(filing_table(CUTOFF_FILINGS), 1)  # the annual report's file
    unsplittable = {archive_url(1, name): b"<p>one paragraph, no items</p>"}
    app, _, providers = _build_setup(tmp_path, monkeypatch, extra=unsplittable)
    assert _build() == REFUSED_EXIT
    err = capsys.readouterr().err
    assert "needs hand boundaries" in err and "hand-boundaries.json" in err
    assert providers.made == []
    assert not (app / "closure-01" / "sources.json").exists()
    assert (app / "closure-01" / "cache").is_dir()  # the filings are cached for the rerun


def test_build_refuses_a_malformed_hand_boundaries_file_before_any_fetch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    app, transport, _ = _build_setup(tmp_path, monkeypatch)
    (app / "closure-01" / "hand-boundaries.json").write_text("[]", encoding="utf-8")
    assert _build() == REFUSED_EXIT
    assert "hand-boundaries.json" in capsys.readouterr().err and transport.requests == []


def test_a_failed_extraction_writes_no_sections_and_a_rerun_reads_the_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    app, transport, providers = _build_setup(
        tmp_path, monkeypatch, provider=FakeTextProvider(ok("cut off", stop="max_tokens"))
    )
    assert _build() == REFUSED_EXIT
    assert "cut off at the token limit" in capsys.readouterr().err
    folder = app / "closure-01"
    assert (folder / "sources.json").is_file() and not (folder / "sections.json").exists()
    fetched = len(transport.requests)
    providers.provider = Scripted(PLAIN)
    assert _build() == CLEAN_EXIT
    assert len(transport.requests) == fetched  # nothing fetched twice
    assert (folder / "sections.json").is_file()


def test_build_refuses_a_case_that_was_already_prepared_before_any_fetch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _, transport, _ = _build_setup(tmp_path, monkeypatch)
    assert _build() == CLEAN_EXIT
    capsys.readouterr()
    fetched = len(transport.requests)
    assert _build() == REFUSED_EXIT
    assert "already exists" in capsys.readouterr().err and len(transport.requests) == fetched


# --- hc case documents (search-half IMPLEMENTATION doc §4.6.2 A.3) ----------------------------------------


def _documents() -> int:
    return main(["case", "documents", "closure-01"])


def test_documents_fetches_the_filings_and_writes_sources_with_no_key_and_no_extraction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    app, transport, providers = _build_setup(tmp_path, monkeypatch, passes=4)
    assert _documents() == CLEAN_EXIT
    out = capsys.readouterr().out
    assert "Fernwick" not in out and "0009999999" not in out and "the Company" not in out
    assert f"cut-off {BUILD_CUTOFF.isoformat()}" in out and "total-search.txt" in out
    folder = app / "closure-01"
    sources = json.loads((folder / "sources.json").read_text())
    assert sources["cutoff"] == BUILD_CUTOFF.isoformat() and sources["sources"]
    assert transport.requests[0][0] == SUBMISSIONS_URL  # the CIK came from candidates.json
    assert providers.made == []
    for name in ("sections.json", "build.json", "reviewed-flags.template.json"):
        assert not (folder / name).exists(), name


def test_the_build_after_documents_reads_the_same_sources_from_the_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app, _, _ = _build_setup(tmp_path, monkeypatch)
    assert _documents() == CLEAN_EXIT
    before = (app / "closure-01" / "sources.json").read_bytes()
    assert _build() == CLEAN_EXIT
    assert (app / "closure-01" / "sources.json").read_bytes() == before


@pytest.mark.parametrize(
    ("setup", "words"),
    [
        ({"passes": 3}, "has not passed real_decision"),
        ({"passes": 1}, "has not passed public_and_filing, inside_window, real_decision"),
        ({"agreed": "real_decision"}, "has not passed real_decision"),
        ({"ciks": ("0009999999", "0008888888")}, "exactly one"),
    ],
)
def test_documents_refuses_before_any_fetch_until_the_criteria_before_4_are_met(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    setup: dict[str, Any],
    words: str,
) -> None:
    app, transport, _ = _build_setup(tmp_path, monkeypatch, **setup)
    assert _documents() == REFUSED_EXIT
    assert words in capsys.readouterr().err
    assert transport.requests == []
    assert not (app / "closure-01" / "sources.json").exists()


def test_documents_takes_the_cutoff_from_the_log_and_refuses_an_unknown_label(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _, transport, _ = _build_setup(tmp_path, monkeypatch, disclosed=date(2026, 7, 2))
    with pytest.raises(SystemExit):
        main(["case", "documents", "closure-01", "--cutoff", "2026-06-15"])
    assert main(["case", "documents", "closure-09"]) == REFUSED_EXIT
    assert "not a candidate" in capsys.readouterr().err
    assert transport.requests == []


def test_assemble_needs_every_flag_decided_then_writes_the_dossier_and_prints_no_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    app, _, _ = _build_setup(tmp_path, monkeypatch, provider=Scripted(COUNTS))
    assert _build() == CLEAN_EXIT
    case = CaseAppendix(root=app, label="closure-01")
    assert json.loads(case.build_path.read_text())["flags"]  # the reply's country count is a flag
    capsys.readouterr()
    assert main(["case", "assemble", "closure-01"]) == REFUSED_EXIT
    assert "no decision" in capsys.readouterr().err
    assert not case.dossier_path.exists()
    fill_in(case)
    assert main(["case", "assemble", "closure-01"]) == CLEAN_EXIT
    out = capsys.readouterr().out
    assert "Fernwick" not in out and "dossier.toml" in out
    assert case.dossier_path.is_file() and case.assembly_path.is_file()


def test_assemble_refuses_without_a_term_list_or_a_built_case(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _build_setup(tmp_path, monkeypatch, terms=False)
    assert main(["case", "assemble", "closure-01"]) == REFUSED_EXIT
    assert "term list" in capsys.readouterr().err


# --- hc case xlog (exploratory IMPLEMENTATION doc, stage 1 step 2; §4.6.5) -------------------------


def _xlog(*words: str) -> int:
    return main(["case", "xlog", *words])


def _through_real_decision() -> None:
    """closure-01 in the pre-registered log, met through the criterion before the shape."""
    assert _log("closure", "record", "closure-01", "first_disclosure", "pass", "--reason", "r",
                "--disclosed", "2026-08-18") == CLEAN_EXIT  # fmt: skip
    for criterion in ("public_and_filing", "inside_window", "real_decision"):
        assert _log("closure", "record", "closure-01", criterion, "pass", "--reason", "r") == 0


def _xlog_setup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> Path:
    folder = _log_setup(tmp_path, monkeypatch, capsys)
    _through_real_decision()
    capsys.readouterr()
    return folder


def test_xlog_carry_writes_the_exploratory_log_and_never_touches_the_selection_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _xlog_setup(tmp_path, monkeypatch, capsys)
    before = {p.name: p.read_bytes() for p in folder.glob("selection-*.json")}
    assert _xlog("carry", "closure-01") == CLEAN_EXIT
    out = capsys.readouterr().out
    assert "carried from selection-log-5.json; wrote exploratory-log-1.json" in out
    assert "next: maps_to_shape" in out
    assert (folder / "exploratory-public-1.json").is_file()
    assert {p.name: p.read_bytes() for p in folder.glob("selection-*.json")} == before


def test_xlog_record_settles_the_list_at_the_shape_and_writes_the_next_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _xlog_setup(tmp_path, monkeypatch, capsys)
    assert _xlog("carry", "closure-01") == CLEAN_EXIT
    words = ["record", "closure-01", "maps_to_shape", "pass", "--reason", "S3 under 4.6.5"]
    assert _xlog(*words, "--list", "retool") == CLEAN_EXIT
    assert "wrote exploratory-log-2.json" in capsys.readouterr().out
    assert _xlog("record", "closure-01", "not_recognizable", "pass", "--reason", "r") == CLEAN_EXIT
    out = capsys.readouterr().out
    assert "wrote exploratory-log-3.json" in out and "finished: passed all" in out
    assert _xlog("public") == CLEAN_EXIT
    view = json.loads(capsys.readouterr().out)
    row = next(r for r in view["rows"] if r["id"] == "closure-01")
    assert row["type"] == "retool" and row["carried"] and row["case"]
    assert row["label"].startswith("exploratory: selected by §4.6.5 step 2")
    assert not (folder / "exploratory-log-4.json").exists()


def test_xlog_loads_the_newest_version_by_number_not_by_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _xlog_setup(tmp_path, monkeypatch, capsys)
    assert _xlog("carry", "closure-01") == CLEAN_EXIT
    text = (folder / "exploratory-log-1.json").read_text()
    for n in range(2, 11):
        (folder / f"exploratory-log-{n}.json").write_text(text)
    capsys.readouterr()
    assert _xlog("record", "closure-01", "maps_to_shape", "pass", "--reason", "r") == CLEAN_EXIT
    assert "wrote exploratory-log-11.json" in capsys.readouterr().out


def test_xlog_refuses_what_the_log_refuses_and_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _xlog_setup(tmp_path, monkeypatch, capsys)
    assert _xlog("carry", "closure-01") == CLEAN_EXIT
    capsys.readouterr()
    before = sorted(p.name for p in folder.iterdir())
    refused = [
        ["carry", "closure-01"],  # already carried
        ["carry", "closure-f01"],  # never got to criterion 4 in the pre-registered log
        ["carry", "closure-99"],  # no such row
        # out of order: the next criterion is maps_to_shape
        ["record", "closure-01", "real_decision", "pass", "--reason", "r"],
        # a list on a criterion other than maps_to_shape
        ["record", "closure-01", "not_recognizable", "pass", "--reason", "r", "--list", "retool"],
        # a blank reason
        ["record", "closure-01", "maps_to_shape", "pass", "--reason", "  "],
        # a read of a criterion that was not rejected, and of one that is carried
        ["read", "closure-01", "maps_to_shape"],
        ["read", "closure-01", "real_decision"],
        # no such row
        ["record", "closure-99", "maps_to_shape", "pass", "--reason", "r"],
    ]
    for words in refused:
        assert _xlog(*words) == REFUSED_EXIT, words
        assert capsys.readouterr().err.startswith("refused:"), words
    assert sorted(p.name for p in folder.iterdir()) == before


def test_xlog_read_takes_its_verdict_from_the_readers_reply(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _xlog_setup(tmp_path, monkeypatch, capsys)
    assert _xlog("carry", "closure-01") == CLEAN_EXIT
    assert _xlog("record", "closure-01", "maps_to_shape", "fail", "--reason", "no shape") == 0
    capsys.readouterr()
    assert _xlog("read", "closure-01", "maps_to_shape") == REFUSED_EXIT
    assert "no usable read" in capsys.readouterr().err
    _reply_on_disk(folder, "pass", "maps_to_shape", "retool")
    assert _xlog("read", "closure-01", "maps_to_shape") == REFUSED_EXIT
    assert "resolved by him" in capsys.readouterr().err
    words = ["read", "closure-01", "maps_to_shape", "--resolution", "it is a retool"]
    assert _xlog(*words) == CLEAN_EXIT
    out = capsys.readouterr().out
    assert "maps_to_shape: pass (disputes)" in out and "read: DISAGREES" in out
    assert _xlog("public") == CLEAN_EXIT
    row = next(r for r in json.loads(capsys.readouterr().out)["rows"] if r["id"] == "closure-01")
    assert (
        row["type"] == "retool"
    )  # a dispute that names a type sets the list; no list to fail on here


def test_xlog_public_has_no_name_and_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _xlog_setup(tmp_path, monkeypatch, capsys)
    _guard_terms(tmp_path, monkeypatch)
    assert _xlog("carry", "closure-01") == CLEAN_EXIT
    secret = "the Canary Cages Inc filing was not first"
    words = ["record", "closure-01", "maps_to_shape", "fail", "--reason", secret]
    assert _xlog(*words, "--public-reason", "matches no shape") == CLEAN_EXIT
    capsys.readouterr()
    before = sorted(p.name for p in folder.iterdir())
    assert _xlog("public") == CLEAN_EXIT
    out = capsys.readouterr().out
    for private in ("Canary", "0009999999", "2026-08", secret, "3990", "ciks", "selection-log"):
        assert private not in out, private
    assert sorted(p.name for p in folder.iterdir()) == before


def test_xlog_show_prints_names_steps_and_the_selection_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _xlog_setup(tmp_path, monkeypatch, capsys)
    assert _xlog("show") == CLEAN_EXIT  # an empty log shows, and nothing is written
    assert "cases none yet" in capsys.readouterr().out
    assert not list(folder.glob("exploratory-*"))
    assert _xlog("carry", "closure-01") == CLEAN_EXIT
    capsys.readouterr()
    assert _xlog("show") == CLEAN_EXIT
    out = capsys.readouterr().out
    assert "closure-01 step 2 closure carried from selection-log-5.json" in out
    assert "Canary Cages Inc" in out and "next: maps_to_shape" in out
    assert "waiting: closure-01: not finished" in out


@pytest.mark.parametrize(
    "reason",
    [
        "Canary Cages said so first",  # a name
        "a Zarnothic report came first",  # a term from the name guard's list
        "an earlier mention on 2026-07-02",  # a date
        "   ",  # blank
    ],
)
def test_xlog_refuses_a_public_reason_that_identifies_and_writes_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    reason: str,
) -> None:
    folder = _xlog_setup(tmp_path, monkeypatch, capsys)
    _guard_terms(tmp_path, monkeypatch)
    assert _xlog("carry", "closure-01") == CLEAN_EXIT
    capsys.readouterr()
    before = sorted(p.name for p in folder.iterdir())
    words = ["record", "closure-01", "maps_to_shape", "fail", "--reason", "r"]
    assert _xlog(*words, "--public-reason", reason) == REFUSED_EXIT
    err = capsys.readouterr().err
    assert err.startswith("refused:") and "Canary" not in err and "Zarnothic" not in err
    assert sorted(p.name for p in folder.iterdir()) == before


def test_xlog_refuses_before_the_search_has_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("HC_APPENDIX_DIR", str(tmp_path))
    assert _xlog("carry", "closure-01") == REFUSED_EXIT
    assert "the search has not run" in capsys.readouterr().err


def _rejected_on_the_shape_in_the_pre_registered_log(folder: Path) -> None:
    """closure-01's criterion 4 rejected and read in the pre-registered log, as every step 2 row was."""
    assert _log("closure", "record", "closure-01", "maps_to_shape", "fail", "--reason", "r") == 0
    _reply_on_disk(folder, "fail", "maps_to_shape")
    assert _log("closure", "read", "closure-01", "maps_to_shape") == CLEAN_EXIT


def test_xlog_read_refuses_the_pre_registered_records_read_of_an_earlier_rejection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _xlog_setup(tmp_path, monkeypatch, capsys)
    _rejected_on_the_shape_in_the_pre_registered_log(folder)
    assert _xlog("carry", "closure-01") == CLEAN_EXIT
    assert _xlog("record", "closure-01", "maps_to_shape", "fail", "--reason", "still none") == 0
    capsys.readouterr()
    before = sorted(p.name for p in folder.iterdir())
    assert _xlog("read", "closure-01", "maps_to_shape") == REFUSED_EXIT
    assert "pre-registered record's read" in capsys.readouterr().err
    assert sorted(p.name for p in folder.iterdir()) == before


def test_the_selection_log_is_closed_to_changes_once_the_exploratory_log_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # §4.6.5 A.1: no row of the pre-registered record is edited or written again. A read of the
    # exploratory rejection, logged through `hc case log` by mistake, would replace the old read.
    folder = _xlog_setup(tmp_path, monkeypatch, capsys)
    _rejected_on_the_shape_in_the_pre_registered_log(folder)
    assert _xlog("carry", "closure-01") == CLEAN_EXIT
    capsys.readouterr()
    newest = sorted(folder.glob("selection-log-*.json"))
    for words in (
        ["closure", "read", "closure-01", "maps_to_shape"],
        ["closure", "record", "closure-f01", "first_disclosure", "fail", "--reason", "r"],
    ):
        assert _log(*words) == REFUSED_EXIT, words
        assert "closed (§4.6.5 A.1)" in capsys.readouterr().err
    assert sorted(folder.glob("selection-log-*.json")) == newest
    assert _log("closure", "show") == CLEAN_EXIT  # reading it is still allowed


# --- one answer to "which row is this label's" (exploratory IMPLEMENTATION doc, step 3; §4.6.5 B.4) -------


def _explore_closure_01(app: Path, *, shape: str | None = None) -> CaseAppendix:
    """closure-01 carried into the exploratory log; ``shape`` (pass or fail) is its maps_to_shape there."""
    search = CaseAppendix(root=app, label="search")
    name = newest_selection_log_name(search)
    log = ExploratoryLog()
    log.carry("closure-01", read_source_log(search, name), name)
    if shape is not None:
        log.record("closure-01", "maps_to_shape", shape, "r", case_type="closure")
    write_exploratory_version(search, log)
    return search


def test_the_exploratory_row_is_the_row_of_record_when_the_label_has_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app, _, _ = _build_setup(
        tmp_path, monkeypatch
    )  # the pre-registered row has passed maps_to_shape
    search = _explore_closure_01(app, shape="fail")
    row = row_for(search, "closure-01")
    assert isinstance(row, ExploratoryRow) and row.source is not None
    assert row.results["maps_to_shape"].result == "fail"
    assert row_for(search, "closure-09") is None


def test_the_pre_registered_row_is_read_when_the_exploratory_log_lacks_the_label(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app, _, _ = _build_setup(tmp_path, monkeypatch)
    search = CaseAppendix(root=app, label="search")
    row = row_for(search, "closure-01")  # no exploratory log at all
    assert row is not None and not isinstance(row, ExploratoryRow)
    log = ExploratoryLog()
    log.add("closure-02", "closure", "2", "window", "0009999999-26-000098")
    write_exploratory_version(search, log)
    row = row_for(search, "closure-01")  # an exploratory log that does not hold it
    assert row is not None and not isinstance(row, ExploratoryRow)


def test_build_and_documents_read_the_exploratory_row_not_the_old_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    app, transport, providers = _build_setup(tmp_path, monkeypatch)
    _explore_closure_01(app, shape="fail")
    assert _build() == REFUSED_EXIT
    assert "has not passed maps_to_shape" in capsys.readouterr().err
    assert transport.requests == [] and providers.made == []


def test_documents_and_build_go_ahead_on_an_exploratory_row_that_has_passed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app, _, _ = _build_setup(tmp_path, monkeypatch, passes=4)
    _explore_closure_01(app)  # carried, criterion 4 not yet recorded: documents is for exactly this
    assert _documents() == CLEAN_EXIT
    assert (app / "closure-01" / "sources.json").is_file()
    assert _build() == REFUSED_EXIT  # but the build needs the shape too


def test_the_reader_finds_an_exploratory_rejection_and_not_the_old_logs_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app, _, _ = _build_setup(tmp_path, monkeypatch)  # old log: maps_to_shape passed
    search = _explore_closure_01(app, shape="fail")
    assert rejection_ready(search, "closure-01", "maps_to_shape") == "closure"
    assert probe_read_ready(search, "closure-01") == "closure"


def test_the_scenario_check_takes_the_first_disclosure_date_from_the_exploratory_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app, _, _ = _build_setup(tmp_path, monkeypatch, disclosed=date(2026, 6, 16))
    _explore_closure_01(app)
    case = CaseAppendix(root=app, label="closure-01")
    inputs = SimpleNamespace(cutoff=date(2026, 6, 15))
    assert _disclosure_failures(inputs, case) == []  # type: ignore[arg-type]
    inputs = SimpleNamespace(cutoff=date(2026, 6, 1))
    assert _disclosure_failures(inputs, case)  # type: ignore[arg-type]


def test_candidate_records_join_the_press_channels_list_and_say_nothing_when_there_is_none(
    tmp_path: Path,
) -> None:
    search = CaseAppendix(root=tmp_path, label="search")
    assert candidate_records(search) is None
    search.write_once(search.directory / "candidates.json", b'{"list": [{"id": "closure-01"}]}')
    assert set(candidate_records(search) or {}) == {"closure-01"}
    search.write_once(search.directory / "press-candidates.json", b'{"list": [{"id": "press-01"}]}')
    assert set(candidate_records(search) or {}) == {"closure-01", "press-01"}


def test_the_log_command_named_for_a_label_follows_the_row_of_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app, _, _ = _build_setup(tmp_path, monkeypatch)
    assert cli._log_command("closure-01", "closure") == "hc case log closure"
    _explore_closure_01(app)
    assert cli._log_command("closure-01", "closure") == "hc case xlog"
    assert cli._log_command("closure-09", None) == "hc case log <type>"


def _pool_closure_30(app: Path, *, known: bool = False) -> CaseAppendix:
    """closure-30, a step 3 pool row in the exploratory log only, its details in the press channel's list;
    first disclosed 2026-07-01, a date the pre-registered log holds for no row."""
    search = CaseAppendix(root=app, label="search")
    record = {
        "list": [
            {"id": "closure-30", "ciks": ["0009999999"], "names": ["Fernwick Canary Holdings"]}
        ]
    }
    search.write_once(search.directory / "press-candidates.json", json.dumps(record).encode())
    log = ExploratoryLog()
    log.add("closure-30", "closure", "3", "pre", "0009999999-26-000097")
    log.record("closure-30", "first_disclosure", "pass", "r", disclosed=date(2026, 7, 1))
    for criterion in ("public_and_filing", "inside_window", "real_decision"):
        log.record("closure-30", criterion, "pass", "r")
    log.record("closure-30", "maps_to_shape", "pass", "r", case_type="closure")
    if known:
        log.record("closure-30", "not_known", "pass", "r")
    write_exploratory_version(search, log)
    (app / "closure-30").mkdir(exist_ok=True)
    (app / "closure-30" / "terms.txt").write_text(
        "term: Fernwick Canary Holdings => the Company\n", encoding="utf-8"
    )
    return search


def test_a_pool_row_needs_not_known_before_the_build(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    app, transport, providers = _build_setup(tmp_path, monkeypatch)
    _pool_closure_30(app)
    argv = ["case", "build", "closure-30", "--cutoff", "2026-06-30", "--shape", "S3"]
    assert main(argv) == REFUSED_EXIT
    assert "has not passed not_known" in capsys.readouterr().err
    assert transport.requests == [] and providers.made == []


def test_the_scenario_check_finds_a_row_only_the_exploratory_log_holds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app, _, _ = _build_setup(tmp_path, monkeypatch)
    _pool_closure_30(app, known=True)
    case = CaseAppendix(root=app, label="closure-30")
    inputs = SimpleNamespace(cutoff=date(2026, 6, 30))
    assert _disclosure_failures(inputs, case) == []  # type: ignore[arg-type]


def test_the_reader_refuses_a_pre_registered_row_once_the_old_log_is_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A rejection in the closed log could be read, at a cost, but never logged (§4.6.5 A.1)."""
    app, _, _ = _build_setup(tmp_path, monkeypatch, passes=4)
    search = CaseAppendix(root=app, label="search")
    log = SelectionLog.from_text(
        (search.directory / newest_selection_log_name(search)).read_text(encoding="utf-8")
    )
    log.record("closure-01", "maps_to_shape", "fail", "r")
    write_log_version(search, log)
    assert rejection_ready(search, "closure-01", "maps_to_shape") == "closure"
    started = ExploratoryLog()
    started.add("closure-02", "closure", "2", "window", "0009999999-26-000098")
    write_exploratory_version(search, started)
    with pytest.raises(ReaderError, match="closed"):
        rejection_ready(search, "closure-01", "maps_to_shape")
    with pytest.raises(ReaderError, match="closed"):
        probe_read_ready(search, "closure-01")


def test_candidate_records_refuse_an_id_in_both_lists(tmp_path: Path) -> None:
    search = CaseAppendix(root=tmp_path, label="search")
    search.write_once(search.directory / "candidates.json", b'{"list": [{"id": "closure-01"}]}')
    search.write_once(
        search.directory / "press-candidates.json", b'{"list": [{"id": "closure-01"}]}'
    )
    with pytest.raises(LogError, match="closure-01"):
        candidate_records(search)
