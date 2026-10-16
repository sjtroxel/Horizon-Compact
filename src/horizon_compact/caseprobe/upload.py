"""``hc case upload``: put a locked case's content in private storage, write-once (search-half doc §4.8).

The content (dossier, scenario, rubric) goes under ``cases/<label>/set-<n>/``. In order, every refusal before
the first write: the label; the committed ``case.lock`` for this label, unchanged since a commit on a remote
branch (a lock only he has on his disk proves nothing); the lock's probe set; the three files hashing to the
lock. Then three exclusive puts. A re-run is allowed only where the object stored is byte-for-byte the file:
an object that differs is never replaced, and the run refuses.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.frozen import FrozenInputsError, Git
from horizon_compact.caseprobe.layout import CONTENT_FILES, content_key
from horizon_compact.protocol.cases import (
    CaseContent,
    CaseError,
    case_path,
    check_case_content,
    read_case,
)
from horizon_compact.sweep.store import Store


class UploadError(Exception):
    """The content cannot be uploaded, and nothing further was. The message names a file and a rule, never
    a value."""


@dataclass(frozen=True)
class Uploaded:
    probe_set: int
    written: tuple[str, ...]
    already_there: tuple[str, ...]


def lock_pushed(git: Git, label: str) -> str:
    """The commit that last changed the label's ``case.lock``, proved on a remote branch with the working
    copy unchanged since."""
    path = case_path(label)
    if git(["status", "--porcelain", "--", path]).strip():
        raise FrozenInputsError(f"{path} has uncommitted changes: commit and push it first")
    commit = git(["log", "-1", "--format=%H", "--", path]).strip()
    if not commit:
        raise FrozenInputsError(f"{path} is not committed")
    if not git(["branch", "-r", "--contains", commit]).strip():
        raise FrozenInputsError(
            f"{path}'s commit {commit[:12]} is not on any remote branch: push it first"
        )
    return commit


def _files(case: CaseAppendix) -> dict[str, bytes]:
    paths = {
        "dossier.toml": case.dossier_path,
        "scenario.toml": case.scenario_path,
        "rubric.toml": case.rubric_path,
    }
    found: dict[str, bytes] = {}
    for name in CONTENT_FILES:
        path = paths[name]
        try:
            found[name] = path.read_bytes()
        except OSError as exc:
            raise UploadError(
                f"cannot read {path.name}: {exc.strerror or type(exc).__name__}"
            ) from exc
    return found


def upload_case(
    case: CaseAppendix, repo_root: Path, *, probe_set: int, git: Git, store: Store
) -> Uploaded:
    try:
        record = read_case(repo_root, case.label)
    except CaseError as exc:
        raise UploadError(str(exc)) from exc
    lock_pushed(git, case.label)
    if record.probe_set != probe_set:
        raise UploadError(
            f"{case_path(case.label)} is for probe set {record.probe_set}, not {probe_set}: lock the "
            "content of the set you are uploading first"
        )
    files = _files(case)
    mismatched = check_case_content(
        record, CaseContent(files["dossier.toml"], files["scenario.toml"], files["rubric.toml"])
    )
    if mismatched:
        raise UploadError("; ".join(mismatched) + ": nothing was uploaded")
    texts = {}
    for name, data in files.items():
        try:
            texts[name] = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise UploadError(f"{name} is not UTF-8") from exc
    # Look before writing anything: a stored object that differs from the file stops the run with no put made.
    stored = {name: store.get(content_key(case.label, probe_set, name)) for name in files}
    for name, text in texts.items():
        if stored[name] is not None and stored[name] != text:
            raise UploadError(
                f"{name} is already stored for set {probe_set} and differs from the file: stored "
                "content is never replaced"
            )
    written: list[str] = []
    there: list[str] = []
    for name, text in texts.items():
        if stored[name] is not None:
            there.append(name)
        elif store.put_new(content_key(case.label, probe_set, name), text):
            written.append(name)
        else:
            raise UploadError(
                f"{name} was stored by someone else while this ran: look before going on"
            )
    return Uploaded(probe_set, tuple(written), tuple(there))
