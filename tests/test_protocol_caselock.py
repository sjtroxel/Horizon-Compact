"""``hc case lock`` (search half, Stage C step 8a). Fictional canaries only; the check is injected.

The code lives in ``protocol/``: ``casebuild/`` may not import the case record (test_architecture).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from horizon_compact import cli
from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.cli import CLEAN_EXIT, REFUSED_EXIT, main
from horizon_compact.protocol.caselock import CaseLockError, lock_case, scenario_check_passes
from horizon_compact.protocol.cases import (
    CaseContent,
    case_lock_text,
    check_case_content,
    content_hashes,
    parse_case,
)

DOSSIER = b'title = "t"\ntext = """canary dossier"""\n'
COARSE = b'title = "t"\ntext = """canary dossier, coarsened"""\n'
SCENARIO = b'title = "s"\ntext = """canary scenario"""\n'
RUBRIC = b"canary rubric\n"
LOCK = "experiment/cases/closure-1/case.lock"


@pytest.fixture
def setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """(appendix, repo root), with a passing scenario check injected."""
    appendix = tmp_path / "appendix"
    repo = tmp_path / "repo"
    case = appendix / "closure-1"
    case.mkdir(parents=True)
    repo.mkdir()
    (case / "dossier.toml").write_bytes(DOSSIER)
    (case / "scenario.toml").write_bytes(SCENARIO)
    (case / "rubric.toml").write_bytes(RUBRIC)
    (case / "assembly.json").write_text(
        json.dumps({"dossier_sha256": hashlib.sha256(DOSSIER).hexdigest()}), encoding="utf-8"
    )
    monkeypatch.setenv("HC_APPENDIX_DIR", str(appendix))
    monkeypatch.setattr(cli, "scenario_check_passes", lambda case: None)
    return appendix, repo


def _lock(repo: Path, *extra: str, label: str = "closure-1") -> int:
    return main(["case", "lock", label, "--root", str(repo), *extra])


def test_lock_writes_the_record_the_gate_reads_back_and_accepts(
    setup: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    _, repo = setup
    assert _lock(repo) == CLEAN_EXIT
    record = parse_case((repo / LOCK).read_text(encoding="utf-8"), "closure-1")
    assert record.probe_set == 1
    assert check_case_content(record, CaseContent(DOSSIER, SCENARIO, RUBRIC)) == []
    out = capsys.readouterr().out
    assert "wrote experiment/cases/closure-1/case.lock" in out
    assert "canary" not in out


def test_lock_and_hashes_produce_the_same_text(
    setup: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    appendix, repo = setup
    main(["case", "hashes", "closure-1", "--rubric", str(appendix / "closure-1" / "rubric.toml")])
    printed = capsys.readouterr().out
    assert _lock(repo) == CLEAN_EXIT
    assert (repo / LOCK).read_text(encoding="utf-8") == printed
    assert printed == case_lock_text(
        "closure-1", 1, content_hashes(CaseContent(DOSSIER, SCENARIO, RUBRIC))
    )


def test_lock_holds_hashes_only(setup: tuple[Path, Path]) -> None:
    _, repo = setup
    _lock(repo)
    text = (repo / LOCK).read_text(encoding="utf-8")
    assert "canary" not in text
    assert {line.split(" = ")[0] for line in text.splitlines()} == {
        "case_version",
        "label",
        "probe_set",
        "dossier_sha256",
        "rubric_sha256",
        "scenario_sha256",
    }


@pytest.mark.parametrize("missing", ["dossier.toml", "scenario.toml", "rubric.toml"])
def test_lock_refuses_a_missing_file_and_writes_nothing(
    setup: tuple[Path, Path], missing: str, capsys: pytest.CaptureFixture[str]
) -> None:
    appendix, repo = setup
    (appendix / "closure-1" / missing).unlink()
    assert _lock(repo) == REFUSED_EXIT
    assert f"{missing} is not in the case's folder" in capsys.readouterr().err
    assert not (repo / "experiment").exists()


def test_lock_refuses_a_bad_label_and_writes_nothing(
    setup: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    _, repo = setup
    assert _lock(repo, label="Bad Label") == REFUSED_EXIT
    assert not (repo / "experiment").exists()


def test_lock_refuses_until_the_scenario_check_passes(
    setup: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _, repo = setup

    def failing(case: CaseAppendix) -> None:
        raise CaseLockError("scenario check failed: criterion 3")

    monkeypatch.setattr(cli, "scenario_check_passes", failing)
    assert _lock(repo) == REFUSED_EXIT
    assert "scenario check failed: criterion 3" in capsys.readouterr().err
    assert not (repo / "experiment").exists()


def test_the_real_scenario_check_refuses_a_case_with_no_render(
    setup: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The real check (step 8b) reads build.json, which this fixture's case does not have."""
    _, repo = setup
    monkeypatch.setattr(cli, "scenario_check_passes", scenario_check_passes)
    assert _lock(repo) == REFUSED_EXIT
    assert "the scenario check failed" in capsys.readouterr().err
    assert not (repo / "experiment").exists()


def test_probe_set_1_is_write_once(
    setup: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    appendix, repo = setup
    _lock(repo)
    before = (repo / LOCK).read_text(encoding="utf-8")
    (appendix / "closure-1" / "dossier.toml").write_bytes(COARSE)
    assert _lock(repo) == REFUSED_EXIT
    assert "probe set 1 is write-once" in capsys.readouterr().err
    assert (repo / LOCK).read_text(encoding="utf-8") == before


def test_probe_set_2_replaces_the_lock_after_a_coarsening(setup: tuple[Path, Path]) -> None:
    appendix, repo = setup
    _lock(repo)
    (appendix / "closure-1" / "dossier.toml").write_bytes(COARSE)
    assert _lock(repo, "--probe-set", "2") == CLEAN_EXIT
    record = parse_case((repo / LOCK).read_text(encoding="utf-8"), "closure-1")
    assert record.probe_set == 2
    assert check_case_content(record, CaseContent(COARSE, SCENARIO, RUBRIC)) == []


def test_probe_set_2_refuses_with_no_set_1(
    setup: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    _, repo = setup
    assert _lock(repo, "--probe-set", "2") == REFUSED_EXIT
    assert "no set 1 to coarsen from" in capsys.readouterr().err
    assert not (repo / LOCK).exists()


def test_probe_set_2_refuses_the_dossier_set_1_was_locked_on(
    setup: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    _, repo = setup
    _lock(repo)
    before = (repo / LOCK).read_text(encoding="utf-8")
    assert _lock(repo, "--probe-set", "2") == REFUSED_EXIT
    assert "needs a coarsened dossier" in capsys.readouterr().err
    assert (repo / LOCK).read_text(encoding="utf-8") == before


def test_probe_set_2_refuses_a_changed_rubric(
    setup: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    appendix, repo = setup
    _lock(repo)
    before = (repo / LOCK).read_text(encoding="utf-8")
    (appendix / "closure-1" / "dossier.toml").write_bytes(COARSE)
    (appendix / "closure-1" / "rubric.toml").write_bytes(RUBRIC + b"changed\n")
    assert _lock(repo, "--probe-set", "2") == REFUSED_EXIT
    assert "never the rubric" in capsys.readouterr().err
    assert (repo / LOCK).read_text(encoding="utf-8") == before


def test_a_case_is_locked_for_set_2_once(
    setup: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    appendix, repo = setup
    _lock(repo)
    (appendix / "closure-1" / "dossier.toml").write_bytes(COARSE)
    _lock(repo, "--probe-set", "2")
    (appendix / "closure-1" / "dossier.toml").write_bytes(COARSE + b"# again\n")
    assert _lock(repo, "--probe-set", "2") == REFUSED_EXIT
    assert "re-probed once" in capsys.readouterr().err


def test_probe_set_2_refuses_an_unreadable_existing_lock(
    setup: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    _, repo = setup
    (repo / LOCK).parent.mkdir(parents=True)
    (repo / LOCK).write_text("not toml [", encoding="utf-8")
    assert _lock(repo, "--probe-set", "2") == REFUSED_EXIT
    assert "the existing lock cannot be read" in capsys.readouterr().err


def test_lock_case_refuses_a_probe_set_outside_one_and_two(setup: tuple[Path, Path]) -> None:
    appendix, repo = setup
    case = CaseAppendix(appendix, "closure-1")
    with pytest.raises(CaseLockError, match="not 1 or 2"):
        lock_case(case, repo, probe_set=3, scenario_check=lambda c: None)
    assert not (repo / "experiment").exists()


def test_lock_refuses_a_dossier_that_was_not_assembled(
    setup: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    appendix, repo = setup
    (appendix / "closure-1" / "assembly.json").unlink()
    assert _lock(repo) == REFUSED_EXIT
    assert "the dossier was not assembled" in capsys.readouterr().err
    assert not (repo / "experiment").exists()


def test_lock_refuses_a_dossier_edited_after_assembly(
    setup: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    appendix, repo = setup
    (appendix / "closure-1" / "dossier.toml").write_bytes(DOSSIER + b"# edited by hand\n")
    assert _lock(repo) == REFUSED_EXIT
    assert "not the dossier `hc case assemble` wrote" in capsys.readouterr().err
    assert not (repo / "experiment").exists()


def test_set_1_never_replaces_a_lock_that_appears_before_the_write(
    setup: tuple[Path, Path],
) -> None:
    appendix, repo = setup
    target = repo / LOCK

    def racing(case: CaseAppendix) -> None:  # another lock lands after the checks, before the write
        target.parent.mkdir(parents=True)
        target.write_text("theirs\n", encoding="utf-8")

    with pytest.raises(CaseLockError, match="write-once"):
        lock_case(CaseAppendix(appendix, "closure-1"), repo, scenario_check=racing)
    assert target.read_text(encoding="utf-8") == "theirs\n"
    assert [p.name for p in target.parent.iterdir()] == ["case.lock"]
