"""``hc case foreshadow`` and ``hc case hashes`` (Phase 5 code half, build step 6); ``hc case search``
(search half, Stage A)."""

from __future__ import annotations

import functools
import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from edgar_helpers import USER_AGENT, FakeTransport
from horizon_compact import cli
from horizon_compact.casebuild.edgar import EdgarClient
from horizon_compact.casebuild.search import FALLBACK_START, QUERIES, RULE_DATE, search_url
from horizon_compact.cli import CHECK_FAILED_EXIT, CLEAN_EXIT, REFUSED_EXIT, main
from horizon_compact.protocol.cases import (
    CaseContent,
    check_case_content,
    content_hashes,
    parse_case,
)

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
        ["closure", "read", "closure-01", "real_decision", "agree"],
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


def test_log_read_needs_a_resolution_on_a_disagreement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _log_setup(tmp_path, monkeypatch, capsys)
    assert _log("closure", "record", "closure-01", "first_disclosure", "pass", "--reason", "r",
                "--disclosed", "2026-08-18") == CLEAN_EXIT  # fmt: skip
    assert (
        _log("closure", "record", "closure-01", "public_and_filing", "pass", "--reason", "r") == 0
    )
    assert _log("closure", "record", "closure-01", "inside_window", "pass", "--reason", "r") == 0
    assert _log("closure", "record", "closure-01", "real_decision", "fail", "--reason", "r") == 0
    capsys.readouterr()
    assert _log("closure", "read", "closure-01", "real_decision", "disagree") == REFUSED_EXIT
    assert "resolved by him" in capsys.readouterr().err
    words = ["closure", "read", "closure-01", "real_decision", "disagree"]
    assert _log(*words, "--resolution", "his call, and why") == CLEAN_EXIT
    out = capsys.readouterr().out
    assert "read: DISAGREES" in out and "wrote selection-log-6.json" in out
    assert (folder / "selection-log-6.json").is_file()


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
