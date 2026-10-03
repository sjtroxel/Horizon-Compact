"""The name guard's command line: ``python -m horizon_compact.privacy.guard <mode>``.

Modes (Phase 0 IMPLEMENTATION doc §5):

- ``pre-commit``   every staged path being added, copied, modified or renamed, and its full staged content
- ``commit-msg``   the commit message file git passes to the hook
- ``pre-push``     every commit on any local branch, tag or HEAD the remote lacks (message, changed paths,
                   full content of each), plus branch and tag names and annotated tag messages
- ``history``      every commit reachable from any branch, tag or HEAD, the same way as ``pre-push``
- ``paths-check``  fails if any tracked path is under ``methods-appendix/``; needs no private file
- ``doctor``       the three hooks are installed and the term file loads and passes its fingerprint
- ``fingerprint``  prints the current longlist's SHA-256, for updating the term file

Exit codes: 0 clean, 1 a term or a private path was found, 2 the guard could not run and so **fails
closed** (no setting, unreadable or stale term file, a git error).

Output never prints a matched term when the ``CI`` environment variable is set. Locally it does, because
the terminal is private and the person fixing the problem needs to see what matched.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from horizon_compact.privacy.names import (
    TermFile,
    TermFileError,
    find_terms,
    load_term_file,
    parse_term_file,
    sha256_of,
)

ENV_VAR = "HC_NAME_GUARD_TERMS"
GIT_CONFIG_KEY = "hc.nameGuardTerms"
HOOK_TYPES = ("pre-commit", "commit-msg", "pre-push")
HOOK_MARKER = b"pre-commit"  # every hook script the pre-commit framework installs names itself

CLEAN, FOUND, FAILED = 0, 1, 2

FIX_HINT = (
    "To fix: reword it. If it is a false positive, add an 'allow:' line with a reason comment to the "
    "private term file. Never remove a term to make a commit pass."
)


class GuardError(Exception):
    """The guard cannot do its job. It refuses rather than passing."""


@dataclass(frozen=True)
class Finding:
    where: str
    line: int
    column: int
    detail: str


# --- small helpers -----------------------------------------------------------


def _redacting() -> bool:
    return bool(os.environ.get("CI"))


def _say(message: str) -> None:
    print(message, file=sys.stderr)


def _git(*args: str, input_bytes: bytes | None = None) -> bytes:
    try:
        result = subprocess.run(["git", *args], input=input_bytes, capture_output=True, check=False)
    except OSError as exc:
        raise GuardError(f"cannot run git: {type(exc).__name__}") from exc
    if result.returncode != 0:
        raise GuardError(f"git {args[0]} failed: {result.stderr.decode(errors='replace').strip()}")
    return result.stdout


def _split_z(output: bytes) -> list[str]:
    return [p.decode("utf-8", errors="replace") for p in output.split(b"\0") if p]


def is_private_path(path: str) -> bool:
    """A path under ``methods-appendix/``, in any capitalization or separator style."""
    normalized = path.lower().replace("_", "-").replace(" ", "-")
    return "methods-appendix" in normalized


def _is_binary(content: bytes) -> bool:
    return b"\0" in content[:8192]


# --- the term file -----------------------------------------------------------


def term_file_path() -> Path:
    """The private term file's location: the environment variable, else local git config."""
    from_env = os.environ.get(ENV_VAR, "").strip()
    if from_env:
        return Path(from_env)
    try:
        value = _git("config", "--get", GIT_CONFIG_KEY).decode().strip()
    except GuardError:
        value = ""
    if not value:
        raise GuardError(
            f"no term file is configured: run 'make setup', or set {ENV_VAR}. "
            "The guard refuses to pass without its list."
        )
    return Path(value)


def load_configured_term_file() -> TermFile:
    try:
        return load_term_file(term_file_path())
    except TermFileError as exc:
        raise GuardError(str(exc)) from exc


# --- scanning ----------------------------------------------------------------


def scan_text(where: str, text: str, term_file: TermFile) -> list[Finding]:
    return [
        Finding(where=where, line=m.line, column=m.column, detail=m.term)
        for m in find_terms(text, term_file)
    ]


def scan_path_and_content(
    where: str, path: str, content: bytes | None, term_file: TermFile
) -> list[Finding]:
    findings: list[Finding] = []
    if is_private_path(path):
        findings.append(Finding(where=f"{where}{path}", line=0, column=0, detail="private path"))
    findings.extend(scan_text(f"{where}{path} (the path itself)", path, term_file))
    if content is None:
        return findings
    if _is_binary(content):
        _say(f"name guard: not scanned, binary: {where}{path}")
        return findings
    findings.extend(
        scan_text(f"{where}{path}", content.decode("utf-8", errors="replace"), term_file)
    )
    return findings


def scan_staged(term_file: TermFile) -> list[Finding]:
    paths = _split_z(_git("diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR"))
    findings: list[Finding] = []
    for path in paths:
        content = _git("cat-file", "blob", f":{path}")
        findings.extend(scan_path_and_content("staged ", path, content, term_file))
    return findings


def _empty_tree() -> str:
    return _git("hash-object", "-t", "tree", "--stdin", input_bytes=b"").decode().strip()


def scan_commit(commit: str, term_file: TermFile, empty_tree: str) -> list[Finding]:
    """A commit's message, and every path it adds or changes with that path's full content at the commit.

    Merges are compared with their first parent; the root commit with the empty tree.
    """
    short = commit[:7]
    message = _git("log", "-1", "--format=%B", commit).decode("utf-8", errors="replace")
    findings = scan_text(f"commit {short} message", message, term_file)
    parents = _git("rev-list", "--parents", "-n", "1", commit).decode().split()[1:]
    base = parents[0] if parents else empty_tree
    changed = _split_z(
        _git("diff", "--name-only", "-z", "--no-renames", "--diff-filter=ACMRT", base, commit)
    )
    for path in changed:
        content = _git("cat-file", "blob", f"{commit}:{path}")
        findings.extend(scan_path_and_content(f"commit {short} ", path, content, term_file))
    return findings


def scan_commits(commits: Iterable[str], term_file: TermFile) -> list[Finding]:
    empty_tree = _empty_tree()
    findings: list[Finding] = []
    for commit in commits:
        findings.extend(scan_commit(commit, term_file, empty_tree))
    return findings


def _has_head() -> bool:
    try:
        _git("rev-parse", "--verify", "--quiet", "HEAD")
    except GuardError:
        return False
    return True


def commits_to_push(remote_arg: str | None = None) -> list[str]:
    """Every commit on any local branch, tag or HEAD that the remote does not already have.

    Deliberately wider than "the ref being pushed". pre-commit 4.6.2 hands a pre-push hook only the
    FIRST ref of a multi-ref push that has new commits (``hook_impl.py``, ``_pre_push_ns`` returns on
    it), and sets no to-ref at all for a first push that includes the root commit. Scanning every local
    ref the remote lacks covers both. The cost is refusing a push while some unpushed local branch holds a
    name, which is the safe direction to be wrong in. The remote comes from the framework's environment,
    else git's own first hook argument, else ``origin``.
    """
    to_ref = os.environ.get("PRE_COMMIT_TO_REF", "").strip()
    if to_ref and set(to_ref) == {"0"}:  # deleting a remote branch pushes no content
        return []
    remote = os.environ.get("PRE_COMMIT_REMOTE_NAME", "").strip() or remote_arg or "origin"
    positive = ["--branches", "--tags"]
    if _has_head():
        positive.append("HEAD")  # a detached HEAD can be pushed without being on a branch
    if to_ref:
        positive.append(to_ref)
    if not _git("for-each-ref", "--count=1", "refs/heads", "refs/tags").strip() and not _has_head():
        return []
    output = _git("rev-list", *positive, "--not", f"--remotes={remote}")
    return output.decode().split()


def scan_ref_names_and_tag_messages(term_file: TermFile) -> list[Finding]:
    """Branch and tag names, and annotated tags' own messages: all are public once pushed."""
    findings: list[Finding] = []
    refs = _git("for-each-ref", "--format=%(objecttype) %(refname)", "refs/heads", "refs/tags")
    for line in refs.decode("utf-8", errors="replace").splitlines():
        object_type, _, refname = line.partition(" ")
        findings.extend(scan_text(f"ref name {refname}", refname, term_file))
        if object_type == "tag":
            body = _git("cat-file", "tag", refname).decode("utf-8", errors="replace")
            findings.extend(scan_text(f"tag {refname} message", body, term_file))
    return findings


# --- reporting ---------------------------------------------------------------


def report(findings: Sequence[Finding], what: str) -> int:
    if not findings:
        return CLEAN
    redact = _redacting()
    _say(f"name guard: REFUSED. {len(findings)} finding(s) in {what}:")
    for f in findings:
        where = "[location redacted]" if redact else f.where
        detail = "[redacted]" if redact else f.detail
        position = f":{f.line}:{f.column}" if f.line else ""
        _say(f"  {where}{position}: {detail}")
    _say(FIX_HINT)
    return FOUND


# --- modes -------------------------------------------------------------------


def mode_pre_commit() -> int:
    return report(scan_staged(load_configured_term_file()), "the staged changes")


def mode_commit_msg(message_file: str) -> int:
    term_file = load_configured_term_file()
    try:
        text = Path(message_file).read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise GuardError(f"cannot read the commit message: {type(exc).__name__}") from exc
    return report(scan_text("commit message", text, term_file), "the commit message")


def mode_pre_push(remote_arg: str | None = None) -> int:
    term_file = load_configured_term_file()
    commits = commits_to_push(remote_arg)
    findings = scan_ref_names_and_tag_messages(term_file) + scan_commits(commits, term_file)
    return report(
        findings, f"{len(commits)} unpushed commit(s), branch and tag names, tag messages"
    )


def mode_history() -> int:
    """Every commit reachable from any branch, tag or HEAD, plus ref names and tag messages."""
    term_file = load_configured_term_file()
    positive = ["--branches", "--tags"] + (["HEAD"] if _has_head() else [])
    has_refs = bool(_git("for-each-ref", "--count=1", "refs/heads", "refs/tags").strip())
    commits = _git("rev-list", *positive).decode().split() if has_refs or _has_head() else []
    findings = scan_ref_names_and_tag_messages(term_file) + scan_commits(commits, term_file)
    code = report(findings, f"the history ({len(commits)} commits)")
    if code == CLEAN:
        print(f"name guard: history clean, {len(commits)} commit(s) scanned.")
    return code


def mode_paths_check() -> int:
    tracked = _split_z(_git("ls-files", "-z"))
    private = [p for p in tracked if is_private_path(p)]
    if not private:
        print(
            f"paths-check: no tracked path under methods-appendix/ ({len(tracked)} tracked files)."
        )
        return CLEAN
    _say(f"paths-check: FAILED. {len(private)} tracked path(s) under methods-appendix/:")
    for path in private:
        _say(f"  {'[path redacted]' if _redacting() else path}")
    _say("Untrack them with 'git rm --cached', and check .gitignore.")
    return FOUND


def mode_doctor() -> int:
    hooks_dir = Path(_git("rev-parse", "--git-path", "hooks").decode().strip())
    missing = []
    for hook in HOOK_TYPES:
        script = hooks_dir / hook
        try:
            installed = HOOK_MARKER in script.read_bytes()
        except OSError:
            installed = False
        if not installed:
            missing.append(hook)
    if missing:
        raise GuardError(f"hooks not installed: {', '.join(missing)}. Run 'make setup'.")
    term_file = load_configured_term_file()
    print(
        f"doctor: hooks installed ({', '.join(HOOK_TYPES)}); term file loads with "
        f"{len(term_file.terms)} terms and {len(term_file.allows)} allowed phrases; "
        "longlist fingerprint matches."
    )
    return CLEAN


def mode_fingerprint() -> int:
    """Print the longlist's current hash. Parses without the fingerprint check, which is the point."""
    path = term_file_path()
    try:
        term_file = parse_term_file(path.read_text(encoding="utf-8"))
        current = sha256_of(term_file.longlist)
    except (OSError, UnicodeDecodeError, TermFileError) as exc:
        raise GuardError(f"cannot fingerprint: {exc}") from exc
    status = "matches" if current == term_file.longlist_sha256 else "DIFFERS from"
    print(f"longlist-sha256: {current}")
    print(f"(this {status} the value recorded in the term file)")
    return CLEAN


USAGE = (
    "usage: python -m horizon_compact.privacy.guard "
    "{pre-commit | commit-msg <file> | pre-push | history | paths-check | doctor | fingerprint}"
)


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        _say(USAGE)
        return FAILED
    mode, rest = args[0], args[1:]
    try:
        if mode == "pre-commit" and not rest:
            return mode_pre_commit()
        if mode == "commit-msg" and len(rest) == 1:
            return mode_commit_msg(rest[0])
        if mode == "pre-push" and len(rest) <= 2:  # git passes the remote's name and URL
            return mode_pre_push(rest[0] if rest else None)
        if mode == "history" and not rest:
            return mode_history()
        if mode == "paths-check" and not rest:
            return mode_paths_check()
        if mode == "doctor" and not rest:
            return mode_doctor()
        if mode == "fingerprint" and not rest:
            return mode_fingerprint()
    except GuardError as exc:
        _say(f"name guard: CANNOT RUN, so refusing. {exc}")
        return FAILED
    _say(USAGE)
    return FAILED


if __name__ == "__main__":
    sys.exit(main())
