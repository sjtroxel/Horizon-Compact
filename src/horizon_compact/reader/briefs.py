"""The reader's three fixed briefs, and the proof they were committed and pushed before the first read.

A brief is the system text of one kind of read (``experiment/readers/<kind>.txt``). Its sha256 goes into every
request record. ``frozen_reader_inputs`` refuses unless the briefs, ``experiment/models.toml`` (the reader's
entry) and this package are unchanged since a commit on a remote branch, so what a read ran on is what was
committed before it (search-half doc §4.9: "the briefs are committed before the first read").
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from horizon_compact.casebuild.frozen import FrozenInputsError, Git

KINDS = ("rejection", "scenario", "rubric")
# A rejection on this criterion is read with its own brief (step 3 item 4); the three above are unchanged.
CRITERION_BRIEFS = {"not_known": "knowledge"}
BRIEFS_DIR = "experiment/readers"
FROZEN_PATHS = (BRIEFS_DIR, "experiment/models.toml", "src/horizon_compact/reader")


class BriefError(Exception):
    """A brief cannot be read, or is empty."""


@dataclass(frozen=True)
class Brief:
    kind: str
    name: str
    text: str
    sha256: str


def load_brief(root: Path, kind: str, criterion: str | None = None) -> Brief:
    if kind not in KINDS:
        raise BriefError(f"{kind!r} is not a kind of read: {', '.join(KINDS)}")
    name = CRITERION_BRIEFS.get(criterion or "", kind) if kind == "rejection" else kind
    path = root / BRIEFS_DIR / f"{name}.txt"
    try:
        data = path.read_bytes()
        text = data.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise BriefError(
            f"the {name} brief cannot be read: {path.name} ({type(exc).__name__})"
        ) from exc
    if not text.strip():
        raise BriefError(f"the {name} brief is empty: {path.name}")
    return Brief(kind=kind, name=path.name, text=text, sha256=hashlib.sha256(data).hexdigest())


def frozen_reader_inputs(git: Git) -> dict[str, Any]:
    """The commit that last changed the briefs, the reader's entry and the reader's code, proved pushed."""
    if git(["status", "--porcelain", "--", *FROZEN_PATHS]).strip():
        raise FrozenInputsError(
            "the reader's inputs have uncommitted changes (" + ", ".join(FROZEN_PATHS) + "): "
            "commit and push them before the first read (search-half doc §4.9)"
        )
    commit = git(["log", "-1", "--format=%H", "--", *FROZEN_PATHS]).strip()
    if not commit:
        raise FrozenInputsError("the reader's inputs have no commit yet")
    if not git(["branch", "-r", "--contains", commit]).strip():
        raise FrozenInputsError(
            f"the reader's inputs' commit {commit[:12]} is not on any remote branch: push it before "
            "the first read (search-half doc §4.9)"
        )
    return {"reader_inputs_commit": commit, "reader_inputs_paths": list(FROZEN_PATHS)}
