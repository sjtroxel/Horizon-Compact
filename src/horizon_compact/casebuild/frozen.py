"""The inputs that must be committed and pushed before the first real document is fetched (protocol §12.6).

Search-half doc §4.5: the extraction model's entry, ``extract.COMMON`` and ``SECTION_INSTRUCTIONS`` are
committed before any real filing is read, and each case's ``build.json`` records that commit and their hash.
This makes that structural: ``frozen_inputs`` refuses unless the two files are unchanged since a commit that
is on a remote branch, and returns the commit for the record. It runs before anything is fetched or any key
is read.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from horizon_compact.casebuild.extract import instructions_sha256

FROZEN_FILES = ("src/horizon_compact/casebuild/extract.py", "experiment/models.toml")

Git = Callable[[Sequence[str]], str]


class FrozenInputsError(Exception):
    """The extraction inputs are not committed and pushed, so no real document may be fetched yet."""


def git_in(repo: Path) -> Git:
    def run(args: Sequence[str]) -> str:
        try:
            result = subprocess.run(
                ["git", "-C", str(repo), *args], capture_output=True, check=False
            )
        except OSError as exc:
            raise FrozenInputsError(f"git cannot run: {type(exc).__name__}") from exc
        if result.returncode != 0:
            raise FrozenInputsError("git could not answer: " + " ".join(args[:2]))
        return result.stdout.decode("utf-8", errors="replace")

    return run


def frozen_inputs(git: Git) -> dict[str, Any]:
    """The commit that last changed the frozen files, proved pushed, and the instructions' hash."""
    if git(["status", "--porcelain", "--", *FROZEN_FILES]).strip():
        raise FrozenInputsError(
            "the extraction inputs have uncommitted changes (" + ", ".join(FROZEN_FILES) + "): "
            "commit and push them before the first real document is fetched (protocol §12.6)"
        )
    commit = git(["log", "-1", "--format=%H", "--", *FROZEN_FILES]).strip()
    if not commit:
        raise FrozenInputsError("the extraction inputs have no commit yet")
    if not git(["branch", "-r", "--contains", commit]).strip():
        raise FrozenInputsError(
            f"the extraction inputs' commit {commit[:12]} is not on any remote branch: push it before "
            "the first real document is fetched (protocol §12.6)"
        )
    return {
        "extraction_inputs_commit": commit,
        "extraction_inputs_files": list(FROZEN_FILES),
        "instructions_sha256": instructions_sha256(),
    }
