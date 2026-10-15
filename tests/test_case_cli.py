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
