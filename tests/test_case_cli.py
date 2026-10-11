"""``hc case foreshadow`` and ``hc case hashes`` (Phase 5 code half, build step 6)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

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
