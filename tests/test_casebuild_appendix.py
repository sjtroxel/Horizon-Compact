"""The private appendix: configuration, the refusal to write where git would track, write-once."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from horizon_compact.casebuild.appendix import (
    AppendixError,
    CaseAppendix,
    appendix_dir,
    ensure_untracked,
    open_case,
    would_be_tracked,
)
from horizon_compact.casebuild.config import setting


def _no_git_config(key: str) -> str:
    return ""


def _init_repo(path: Path, ignore: str) -> None:
    path.mkdir()
    subprocess.run(["git", "init", "-q", str(path)], check=True, capture_output=True)
    (path / ".gitignore").write_text(ignore, encoding="utf-8")


def test_the_environment_wins_over_git_config() -> None:
    value = setting(
        "HC_X", "hc.x", environ={"HC_X": " from-env "}, git_config=lambda key: "from-git"
    )
    assert value == "from-env"


def test_git_config_is_the_fallback_and_blank_env_does_not_count() -> None:
    value = setting("HC_X", "hc.x", environ={"HC_X": "  "}, git_config=lambda key: "from-git\n")
    assert value == "from-git"


def test_no_appendix_configured_is_an_error_with_no_default() -> None:
    with pytest.raises(AppendixError, match="no appendix directory"):
        appendix_dir(environ={}, git_config=_no_git_config)


def test_a_relative_appendix_path_is_refused() -> None:
    with pytest.raises(AppendixError, match="absolute"):
        appendix_dir(environ={"HC_APPENDIX_DIR": "relative/here"}, git_config=_no_git_config)


def test_the_appendix_is_found_from_the_environment(tmp_path: Path) -> None:
    found = appendix_dir(environ={"HC_APPENDIX_DIR": str(tmp_path)}, git_config=_no_git_config)
    assert found == tmp_path


@pytest.mark.parametrize(
    "label", ["Closure-1", "closure_1", "closure--1", "1-closure", "", "a b", "../x"]
)
def test_a_label_must_be_a_neutral_slug(label: str, tmp_path: Path) -> None:
    with pytest.raises(AppendixError, match="label"):
        CaseAppendix(root=tmp_path, label=label)


def test_a_path_outside_any_repository_is_not_tracked(tmp_path: Path) -> None:
    assert would_be_tracked(tmp_path / "not" / "yet" / "made.json") is False


def test_a_git_dir_in_the_callers_environment_does_not_change_the_answer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With GIT_DIR inherited, git would treat any folder as a work tree of that repository."""
    repo = tmp_path / "clone"
    _init_repo(repo, ignore="")
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    monkeypatch.setenv("GIT_DIR", str(repo / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(outside))
    assert would_be_tracked(outside / "closure-1" / "build.json") is False


def test_a_path_in_a_repository_with_no_ignore_rule_is_tracked(tmp_path: Path) -> None:
    repo = tmp_path / "clone"
    _init_repo(repo, ignore="something-else/\n")
    assert would_be_tracked(repo / "appendix" / "closure-1" / "dossier.toml") is True
    with pytest.raises(AppendixError, match="git would track"):
        ensure_untracked(repo / "appendix")


def test_a_path_in_a_repository_under_an_ignore_rule_is_not_tracked(tmp_path: Path) -> None:
    repo = tmp_path / "clone"
    _init_repo(repo, ignore="private-area/\n")
    assert would_be_tracked(repo / "private-area" / "closure-1" / "cache" / "a.body") is False


def test_open_case_refuses_a_root_git_would_track(tmp_path: Path) -> None:
    repo = tmp_path / "clone"
    _init_repo(repo, ignore="")
    with pytest.raises(AppendixError, match="git would track"):
        open_case(
            "closure-1",
            environ={"HC_APPENDIX_DIR": str(repo / "appendix")},
            git_config=_no_git_config,
        )


def test_a_write_to_a_tracked_location_is_refused_and_leaves_nothing(tmp_path: Path) -> None:
    repo = tmp_path / "clone"
    _init_repo(repo, ignore="")
    case = CaseAppendix(root=repo / "appendix", label="closure-1")
    with pytest.raises(AppendixError, match="git would track"):
        case.write_once(case.dossier_path, b"x")
    assert not (repo / "appendix").exists()


def test_write_once_writes_and_then_refuses_to_replace(tmp_path: Path) -> None:
    case = open_case(
        "closure-1", environ={"HC_APPENDIX_DIR": str(tmp_path)}, git_config=_no_git_config
    )
    case.write_once(case.build_path, b"first")
    with pytest.raises(AppendixError, match="write-once"):
        case.write_once(case.build_path, b"second")
    assert case.build_path.read_bytes() == b"first"
    assert [p.name for p in case.directory.iterdir()] == [
        "build.json"
    ]  # no temporary file left behind


def test_a_write_outside_the_case_directory_is_refused(tmp_path: Path) -> None:
    case = CaseAppendix(root=tmp_path, label="closure-1")
    with pytest.raises(AppendixError, match="outside the case"):
        case.write_once(tmp_path / "closure-2" / "dossier.toml", b"x")
    with pytest.raises(AppendixError, match="outside the case"):
        case.write_once(case.directory / ".." / "closure-2" / "x", b"x")
