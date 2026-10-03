"""Tests for the name guard against real, temporary git repositories.

Hermetic: the user's global and system git config are switched off, so no local setting (a hooks path, a
signing key, a template directory) can change the result. No network. Every name is a fictional canary
(Phase 0 IMPLEMENTATION doc §7); this file is itself committed through the guard.
"""

from __future__ import annotations

import hashlib
import os
import stat
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from horizon_compact.privacy import guard

CANARY = "Quillmere Fastening"
CLEAN_TEXT = "A fictional company closes a plant in a Midwest town.\n"


# --- fixtures ----------------------------------------------------------------


@pytest.fixture(autouse=True)
def hermetic_git(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Test")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "test@example.invalid")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "Test")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "test@example.invalid")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    for name in ("CI", guard.ENV_VAR, "PRE_COMMIT_TO_REF", "PRE_COMMIT_REMOTE_NAME"):
        monkeypatch.delenv(name, raising=False)


def write_term_file(directory: Path, terms: str = f"term: {CANARY}\nterm-i: Zarnothic\n") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    longlist = directory / "longlist.md"
    longlist.write_text("a fictional longlist\n", encoding="utf-8")
    digest = hashlib.sha256(longlist.read_bytes()).hexdigest()
    path = directory / "terms.txt"
    path.write_text(f"longlist: {longlist}\nlonglist-sha256: {digest}\n{terms}", encoding="utf-8")
    return path


@pytest.fixture
def terms(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = write_term_file(tmp_path / "private")
    monkeypatch.setenv(guard.ENV_VAR, str(path))
    return path


def git(
    *args: str, cwd: Path | None = None, check: bool = True
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=check)


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    path = tmp_path / "repo"
    path.mkdir()
    git("init", "-q", "-b", "main", cwd=path)
    monkeypatch.chdir(path)
    yield path


def commit_file(name: str, text: str, message: str = "add") -> None:
    path = Path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    git("add", "--", name)
    git("commit", "-q", "--no-verify", "-m", message)


def stage(name: str, text: str) -> None:
    path = Path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    git("add", "--", name)


# --- pre-commit: what is staged ----------------------------------------------


def test_staged_content_with_a_canary_is_refused(
    repo: Path, terms: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    stage("notes.md", f"line one\nthe {CANARY} plant\n")
    assert guard.main(["pre-commit"]) == guard.FOUND
    err = capsys.readouterr().err
    assert "staged notes.md:2:5" in err
    assert CANARY in err  # locally the term is shown; the terminal is private


def test_staged_path_with_a_canary_is_refused(repo: Path, terms: Path) -> None:
    stage("cases/zarnothic_closure.md", CLEAN_TEXT)
    assert guard.main(["pre-commit"]) == guard.FOUND


@pytest.mark.parametrize(
    "path", ["methods-appendix/a.md", "Methods-Appendix/a.md", "docs/methods_appendix/a.md"]
)
def test_staged_private_path_is_refused(repo: Path, terms: Path, path: str) -> None:
    stage(path, CLEAN_TEXT)
    assert guard.main(["pre-commit"]) == guard.FOUND


def test_clean_staged_change_passes(repo: Path, terms: Path) -> None:
    stage("notes.md", CLEAN_TEXT)
    assert guard.main(["pre-commit"]) == guard.CLEAN


def test_nothing_staged_passes(repo: Path, terms: Path) -> None:
    assert guard.main(["pre-commit"]) == guard.CLEAN


def test_deleting_a_file_that_holds_a_canary_passes(repo: Path, terms: Path) -> None:
    commit_file("old.md", f"{CANARY}\n")
    git("rm", "-q", "old.md")
    assert guard.main(["pre-commit"]) == guard.CLEAN


def test_renaming_into_a_canary_path_is_refused(repo: Path, terms: Path) -> None:
    commit_file("clean.md", CLEAN_TEXT)
    git("mv", "clean.md", "zarnothic.md")
    assert guard.main(["pre-commit"]) == guard.FOUND


def test_the_index_is_scanned_not_the_working_tree(repo: Path, terms: Path) -> None:
    stage("notes.md", CLEAN_TEXT)
    Path("notes.md").write_text(f"{CANARY}\n", encoding="utf-8")  # unstaged: not being committed
    assert guard.main(["pre-commit"]) == guard.CLEAN

    stage("notes.md", f"{CANARY}\n")
    Path("notes.md").write_text(CLEAN_TEXT, encoding="utf-8")  # the staged version still holds it
    assert guard.main(["pre-commit"]) == guard.FOUND


def test_a_binary_file_is_reported_as_not_scanned(
    repo: Path, terms: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    Path("image.bin").write_bytes(b"\x00\x01" + CANARY.encode())
    git("add", "image.bin")
    assert guard.main(["pre-commit"]) == guard.CLEAN
    assert "not scanned, binary" in capsys.readouterr().err


def test_ci_output_is_redacted(
    repo: Path, terms: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("CI", "true")
    stage("zarnothic.md", f"{CANARY}\n")
    assert guard.main(["pre-commit"]) == guard.FOUND
    err = capsys.readouterr().err
    assert "[redacted]" in err
    assert "Quillmere" not in err
    assert "arnothic" not in err.lower()


# --- commit-msg --------------------------------------------------------------


def test_commit_message_with_a_canary_is_refused(repo: Path, terms: Path, tmp_path: Path) -> None:
    message = tmp_path / "MSG"
    message.write_text(f"phase 5: add the {CANARY} case\n", encoding="utf-8")
    assert guard.main(["commit-msg", str(message)]) == guard.FOUND


def test_clean_commit_message_passes(repo: Path, terms: Path, tmp_path: Path) -> None:
    message = tmp_path / "MSG"
    message.write_text("phase 0 step 3: the name guard\n", encoding="utf-8")
    assert guard.main(["commit-msg", str(message)]) == guard.CLEAN


def test_unreadable_commit_message_fails_closed(repo: Path, terms: Path, tmp_path: Path) -> None:
    assert guard.main(["commit-msg", str(tmp_path / "absent")]) == guard.FAILED


# --- pre-push and history ----------------------------------------------------


@pytest.fixture
def remote(repo: Path, tmp_path: Path) -> Path:
    bare = tmp_path / "remote.git"
    git("init", "-q", "--bare", "-b", "main", str(bare))
    git("remote", "add", "origin", str(bare))
    return bare


def test_push_catches_a_commit_made_with_no_verify(repo: Path, terms: Path, remote: Path) -> None:
    commit_file("a.md", CLEAN_TEXT)
    git("push", "-q", "--no-verify", "origin", "main")
    commit_file("b.md", f"{CANARY}\n")  # --no-verify: the commit-time scan never ran
    assert guard.main(["pre-push", "origin", str(remote)]) == guard.FOUND


def test_push_scans_only_what_the_remote_lacks(repo: Path, terms: Path, remote: Path) -> None:
    commit_file("a.md", f"{CANARY}\n")
    git("push", "-q", "--no-verify", "origin", "main")  # already public: not this push's content
    commit_file("b.md", CLEAN_TEXT)
    assert guard.main(["pre-push", "origin", str(remote)]) == guard.CLEAN


def test_first_push_scans_every_commit(repo: Path, terms: Path, remote: Path) -> None:
    commit_file("a.md", f"{CANARY}\n")
    commit_file("a.md", CLEAN_TEXT, message="remove it")
    assert guard.main(["pre-push", "origin", str(remote)]) == guard.FOUND


def test_push_catches_a_canary_in_a_commit_message(repo: Path, terms: Path, remote: Path) -> None:
    commit_file("a.md", CLEAN_TEXT, message=f"add the {CANARY} notes")
    assert guard.main(["pre-push", "origin", str(remote)]) == guard.FOUND


def test_push_scans_every_local_ref_not_only_the_one_named(
    repo: Path, terms: Path, remote: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """pre-commit passes only the first ref of a multi-ref push, so the guard looks wider on purpose."""
    commit_file("a.md", CLEAN_TEXT)
    clean_head = git("rev-parse", "HEAD").stdout.strip()
    commit_file("b.md", f"{CANARY}\n")
    monkeypatch.setenv("PRE_COMMIT_REMOTE_NAME", "origin")
    monkeypatch.setenv("PRE_COMMIT_TO_REF", clean_head)  # the framework names only the clean commit
    assert guard.main(["pre-push"]) == guard.FOUND


def test_push_catches_a_canary_on_an_unpushed_side_branch(
    repo: Path, terms: Path, remote: Path
) -> None:
    commit_file("a.md", CLEAN_TEXT)
    git("push", "-q", "--no-verify", "origin", "main")
    git("checkout", "-q", "-b", "experiment")
    commit_file("x.md", f"{CANARY}\n")
    git("checkout", "-q", "main")
    assert guard.main(["pre-push", "origin"]) == guard.FOUND


def test_push_catches_a_canary_in_a_branch_name(repo: Path, terms: Path, remote: Path) -> None:
    commit_file("a.md", CLEAN_TEXT)
    git("branch", "zarnothic-case")
    assert guard.main(["pre-push", "origin"]) == guard.FOUND


def test_push_catches_a_canary_in_a_tag_name(repo: Path, terms: Path, remote: Path) -> None:
    commit_file("a.md", CLEAN_TEXT)
    git("push", "-q", "--no-verify", "origin", "main")
    git("tag", "zarnothic-v1")
    assert guard.main(["pre-push", "origin"]) == guard.FOUND


def test_push_catches_a_canary_in_an_annotated_tag_message(
    repo: Path, terms: Path, remote: Path
) -> None:
    commit_file("a.md", CLEAN_TEXT)
    git("push", "-q", "--no-verify", "origin", "main")  # the commit itself is already public
    git("tag", "-a", "prereg-v1", "-m", f"protocol, with the {CANARY} case")
    assert guard.main(["pre-push", "origin"]) == guard.FOUND


def test_a_clean_annotated_tag_passes(repo: Path, terms: Path, remote: Path) -> None:
    commit_file("a.md", CLEAN_TEXT)
    git("tag", "-a", "prereg-v1", "-m", "the protocol, frozen")
    assert guard.main(["pre-push", "origin"]) == guard.CLEAN


def test_push_on_a_detached_head_scans_it(repo: Path, terms: Path, remote: Path) -> None:
    commit_file("a.md", CLEAN_TEXT)
    git("push", "-q", "--no-verify", "origin", "main")
    git("checkout", "-q", "--detach")
    commit_file("d.md", f"{CANARY}\n")
    assert guard.main(["pre-push", "origin"]) == guard.FOUND


def test_deleting_a_remote_branch_scans_nothing(
    repo: Path, terms: Path, remote: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    commit_file("a.md", f"{CANARY}\n")
    monkeypatch.setenv("PRE_COMMIT_TO_REF", "0" * 40)
    assert guard.main(["pre-push"]) == guard.CLEAN


def test_history_finds_a_canary_removed_long_ago(
    repo: Path, terms: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    commit_file("a.md", f"{CANARY}\n")
    commit_file("a.md", CLEAN_TEXT, message="remove it")
    commit_file("b.md", CLEAN_TEXT)
    assert guard.main(["history"]) == guard.FOUND
    assert "a.md:1:1" in capsys.readouterr().err


def test_history_finds_a_canary_that_arrived_by_merge(repo: Path, terms: Path) -> None:
    commit_file("a.md", CLEAN_TEXT)
    git("checkout", "-q", "-b", "side")
    commit_file("side.md", f"{CANARY}\n")
    git("checkout", "-q", "main")
    commit_file("main.md", CLEAN_TEXT)
    git("merge", "-q", "--no-ff", "--no-verify", "-m", "merge", "side")
    git("branch", "-q", "-D", "side")
    assert guard.main(["history"]) == guard.FOUND


def test_history_scans_side_branches_and_tag_messages(repo: Path, terms: Path) -> None:
    commit_file("a.md", CLEAN_TEXT)
    git("tag", "-a", "v0", "-m", f"note about {CANARY}")
    assert guard.main(["history"]) == guard.FOUND
    git("tag", "-d", "v0")
    git("checkout", "-q", "-b", "side")
    commit_file("s.md", f"{CANARY}\n")
    git("checkout", "-q", "main")
    assert guard.main(["history"]) == guard.FOUND


def test_clean_history_passes(repo: Path, terms: Path, capsys: pytest.CaptureFixture[str]) -> None:
    commit_file("a.md", CLEAN_TEXT)
    commit_file("b.md", CLEAN_TEXT)
    assert guard.main(["history"]) == guard.CLEAN
    assert "history clean, 2 commit(s) scanned" in capsys.readouterr().out


def test_history_of_an_empty_repo_passes(repo: Path, terms: Path) -> None:
    assert guard.main(["history"]) == guard.CLEAN


# --- paths-check (CI) --------------------------------------------------------


@pytest.mark.parametrize(
    "path", ["methods-appendix/x.md", "Methods-Appendix/x.md", "a/methods_appendix/x"]
)
def test_paths_check_fails_on_a_tracked_private_path(repo: Path, path: str) -> None:
    commit_file(path, CLEAN_TEXT)
    assert guard.main(["paths-check"]) == guard.FOUND


def test_paths_check_passes_without_one(repo: Path) -> None:
    commit_file("docs/methods.md", CLEAN_TEXT)
    assert guard.main(["paths-check"]) == guard.CLEAN


def test_paths_check_needs_no_term_file(repo: Path) -> None:
    """CI never has the private file; paths-check must not ask for it."""
    commit_file("a.md", CLEAN_TEXT)
    assert os.environ.get(guard.ENV_VAR) is None
    assert guard.main(["paths-check"]) == guard.CLEAN


def test_paths_check_redacts_in_ci(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    commit_file("methods-appendix/zarnothic.md", CLEAN_TEXT)
    monkeypatch.setenv("CI", "true")
    assert guard.main(["paths-check"]) == guard.FOUND
    err = capsys.readouterr().err
    assert "[path redacted]" in err
    assert "zarnothic" not in err


# --- fail closed -------------------------------------------------------------


def test_no_setting_fails_closed(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    stage("notes.md", CLEAN_TEXT)
    assert guard.main(["pre-commit"]) == guard.FAILED
    assert "no term file is configured" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("terms_text", "expected"),
    [
        ("", "no terms"),
        ("allow: Something\n", "no terms"),
    ],
)
def test_term_file_without_terms_fails_closed(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    terms_text: str,
    expected: str,
) -> None:
    monkeypatch.setenv(guard.ENV_VAR, str(write_term_file(tmp_path / "p", terms_text)))
    stage("notes.md", CLEAN_TEXT)
    assert guard.main(["pre-commit"]) == guard.FAILED
    assert expected in capsys.readouterr().err


def test_missing_term_file_fails_closed(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(guard.ENV_VAR, str(tmp_path / "absent.txt"))
    stage("notes.md", CLEAN_TEXT)
    assert guard.main(["pre-commit"]) == guard.FAILED


def test_missing_hash_line_fails_closed(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "terms.txt"
    path.write_text(f"longlist: {tmp_path}/l.md\nterm: {CANARY}\n", encoding="utf-8")
    monkeypatch.setenv(guard.ENV_VAR, str(path))
    stage("notes.md", CLEAN_TEXT)
    assert guard.main(["pre-commit"]) == guard.FAILED


def test_changed_longlist_fails_closed(
    repo: Path, terms: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (terms.parent / "longlist.md").write_text("one more candidate\n", encoding="utf-8")
    stage("notes.md", CLEAN_TEXT)
    assert guard.main(["pre-commit"]) == guard.FAILED
    assert "longlist has changed" in capsys.readouterr().err


def test_missing_longlist_fails_closed(repo: Path, terms: Path) -> None:
    (terms.parent / "longlist.md").unlink()
    stage("notes.md", CLEAN_TEXT)
    assert guard.main(["pre-commit"]) == guard.FAILED


@pytest.mark.parametrize("mode", [["pre-commit"], ["pre-push"], ["history"]])
def test_every_scanning_mode_fails_closed_without_a_setting(repo: Path, mode: list[str]) -> None:
    assert guard.main(mode) == guard.FAILED


def test_outside_a_git_repo_fails_closed(
    tmp_path: Path, terms: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    outside = tmp_path / "not-a-repo"
    outside.mkdir()
    monkeypatch.chdir(outside)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    assert guard.main(["pre-commit"]) == guard.FAILED


# --- where the setting comes from (decision 2) --------------------------------


def test_local_git_config_is_used(repo: Path, tmp_path: Path) -> None:
    path = write_term_file(tmp_path / "p")
    git("config", "--local", guard.GIT_CONFIG_KEY, str(path))
    stage("notes.md", f"{CANARY}\n")
    assert guard.main(["pre-commit"]) == guard.FOUND


def test_environment_variable_overrides_git_config(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    git("config", "--local", guard.GIT_CONFIG_KEY, str(tmp_path / "absent.txt"))
    monkeypatch.setenv(guard.ENV_VAR, str(write_term_file(tmp_path / "p")))
    stage("notes.md", f"{CANARY}\n")
    assert guard.main(["pre-commit"]) == guard.FOUND


# --- doctor and fingerprint --------------------------------------------------


def install_marker_hooks(repo: Path) -> None:
    for hook in guard.HOOK_TYPES:
        script = repo / ".git" / "hooks" / hook
        script.write_text("#!/bin/sh\n# File generated by pre-commit\n", encoding="utf-8")


def test_doctor_fails_without_hooks(
    repo: Path, terms: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert guard.main(["doctor"]) == guard.FAILED
    assert "hooks not installed: pre-commit, commit-msg, pre-push" in capsys.readouterr().err


def test_doctor_fails_with_one_hook_missing(repo: Path, terms: Path) -> None:
    install_marker_hooks(repo)
    (repo / ".git" / "hooks" / "pre-push").unlink()
    assert guard.main(["doctor"]) == guard.FAILED


def test_doctor_fails_without_a_term_file(repo: Path) -> None:
    install_marker_hooks(repo)
    assert guard.main(["doctor"]) == guard.FAILED


def test_doctor_passes_when_everything_is_in_place(
    repo: Path, terms: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    install_marker_hooks(repo)
    assert guard.main(["doctor"]) == guard.CLEAN
    assert "2 terms and 0 allowed phrases" in capsys.readouterr().out


def test_fingerprint_reports_a_changed_longlist(
    repo: Path, terms: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    longlist = terms.parent / "longlist.md"
    longlist.write_text("one more candidate\n", encoding="utf-8")
    assert guard.main(["fingerprint"]) == guard.CLEAN
    out = capsys.readouterr().out
    assert hashlib.sha256(longlist.read_bytes()).hexdigest() in out
    assert "DIFFERS" in out


@pytest.mark.parametrize("argv", [[], ["nonsense"], ["commit-msg"], ["history", "extra"]])
def test_bad_usage_fails_closed(argv: list[str]) -> None:
    assert guard.main(argv) == guard.FAILED


# --- end to end: real git hooks, real commits and pushes ----------------------


@pytest.fixture
def hooked_repo(repo: Path, terms: Path, remote: Path) -> Path:
    """Plain git hooks calling the guard, so a real ``git commit`` and ``git push`` exercise it."""
    for hook, args in (
        ("pre-commit", "pre-commit"),
        ("commit-msg", 'commit-msg "$1"'),
        ("pre-push", 'pre-push "$1" "$2"'),
    ):
        script = repo / ".git" / "hooks" / hook
        script.write_text(
            f'#!/bin/sh\nexec "{sys.executable}" -m horizon_compact.privacy.guard {args}\n',
            encoding="utf-8",
        )
        script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return repo


def head_exists() -> bool:
    return git("rev-parse", "--verify", "--quiet", "HEAD", check=False).returncode == 0


def test_real_commit_with_a_canary_is_refused(hooked_repo: Path) -> None:
    stage("notes.md", f"the {CANARY} plant\n")
    result = git("commit", "-m", "add notes", check=False)
    assert result.returncode != 0
    assert "REFUSED" in result.stderr
    assert not head_exists()


def test_real_commit_with_a_canary_message_is_refused(hooked_repo: Path) -> None:
    stage("notes.md", CLEAN_TEXT)
    result = git("commit", "-m", f"add the {CANARY} notes", check=False)
    assert result.returncode != 0
    assert not head_exists()


def test_real_clean_commit_and_push_pass(hooked_repo: Path, remote: Path) -> None:
    stage("notes.md", CLEAN_TEXT)
    assert git("commit", "-m", "add notes", check=False).returncode == 0
    assert git("push", "origin", "main", check=False).returncode == 0
    assert (
        git("rev-parse", "main", cwd=remote).stdout.strip()
        == git("rev-parse", "HEAD").stdout.strip()
    )


def test_real_push_refuses_a_no_verify_commit(hooked_repo: Path, remote: Path) -> None:
    stage("notes.md", f"{CANARY}\n")
    assert git("commit", "--no-verify", "-m", "sneak", check=False).returncode == 0
    result = git("push", "origin", "main", check=False)
    assert result.returncode != 0
    assert "REFUSED" in result.stderr
    assert git("rev-parse", "--verify", "--quiet", "main", cwd=remote, check=False).returncode != 0
