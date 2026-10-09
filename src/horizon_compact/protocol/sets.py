"""The three kinds of code and how a frozen set is hashed (Phase 3.5 IMPLEMENTATION doc sections 5.1-5.2).

**Instrument** (what the model reads, and which replies count): the prompt, the validation, the
classification. **Analysis**: every file in ``analysis/`` and the loader it reads scenarios through,
``experiment.py``. Both are frozen at ``prereg-v1``; a change to either is ``prereg-v2``. **Run**: every
other file in the package, which may be fixed after the tag with each fix logged.

The universe is the package, ``src/horizon_compact/``. A file is in exactly one set: instrument if it
matches an instrument pattern, else analysis if it matches an analysis pattern, else run. Bytecode
(``__pycache__``, ``.pyc``) is never in any set.

**Listing.** A set is listed by pattern from the files on disk. In a git checkout (the laptop, CI, a
worktree of the tag) the list is then filtered through ``git ls-files``, so an untracked scratch file is
never hashed. The container has no ``.git``; its copy of ``src/`` comes from CI's clean checkout
(``infra/docker/Dockerfile``, ``.github/workflows/deploy.yml``) and holds no untracked files, so the pattern
alone gives the same list. A file that is tracked but missing on disk drops out of the list; the lock's
per-file hashes then name it.

**Hashing** is the scheme ``simulation/runner.py``'s ``code_hash`` uses: sha256 over each file's
repo-relative POSIX path, a zero byte, its bytes, a zero byte, in sorted path order. The path is in the
hash, so a rename changes it. Sorting is by the path string.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from collections.abc import Iterable
from pathlib import Path, PurePosixPath
from typing import Literal

SetName = Literal["instrument", "analysis", "run"]
SET_NAMES: tuple[SetName, ...] = ("instrument", "analysis", "run")
FROZEN_SETS: tuple[SetName, ...] = ("instrument", "analysis")

PACKAGE = "src/horizon_compact"

INSTRUMENT_PATTERNS: tuple[str, ...] = (
    f"{PACKAGE}/sweep/prompt.py",
    f"{PACKAGE}/sweep/decision.py",
    f"{PACKAGE}/sweep/classify.py",
)
ANALYSIS_PATTERNS: tuple[str, ...] = (
    f"{PACKAGE}/analysis/**",
    f"{PACKAGE}/experiment.py",
)
# Variables that point git at another repository or index (a hook sets them). The listing asks about ``root``.
_GIT_REDIRECTS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR")

PATTERNS: dict[SetName, tuple[str, ...]] = {
    "instrument": INSTRUMENT_PATTERNS,
    "analysis": ANALYSIS_PATTERNS,
}


class SetError(Exception):
    """The sets cannot be listed: git failed in a checkout, or a frozen set came back empty."""


def is_bytecode(path: str) -> bool:
    pure = PurePosixPath(path)
    return "__pycache__" in pure.parts or pure.suffix in {".pyc", ".pyo"}


def _matches(path: str, patterns: Iterable[str]) -> bool:
    pure = PurePosixPath(path)
    return any(pure.full_match(pattern) for pattern in patterns)


def set_of(path: str) -> SetName:
    """The one set a repo-relative POSIX path under the package belongs to."""
    if not PurePosixPath(path).is_relative_to(PACKAGE) or is_bytecode(path):
        raise ValueError(f"{path} is not a source file in {PACKAGE}/")
    if _matches(path, INSTRUMENT_PATTERNS):
        return "instrument"
    if _matches(path, ANALYSIS_PATTERNS):
        return "analysis"
    return "run"


def tracked_files(root: Path, under: str = PACKAGE) -> frozenset[str] | None:
    """The files git tracks under ``under`` (the package by default), or None where there is no git checkout
    (the container).

    A checkout whose git cannot answer is an error, never "no filter": the filter is what keeps an untracked
    file out of a hash.
    """
    if not (root / ".git").exists():
        return None
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--", under],
            capture_output=True,
            check=False,
            env={k: v for k, v in os.environ.items() if k not in _GIT_REDIRECTS},
        )
    except OSError as exc:
        raise SetError(f"cannot run git: {type(exc).__name__}") from exc
    if result.returncode != 0:
        raise SetError(f"git ls-files failed: {result.stderr.decode(errors='replace').strip()}")
    return frozenset(p.decode("utf-8") for p in result.stdout.split(b"\0") if p)


def package_files(root: Path) -> tuple[str, ...]:
    """Every source file of the package on disk, as sorted repo-relative POSIX paths.

    In a checkout, tracked files only.
    """
    base = root / PACKAGE
    if not base.is_dir():
        raise SetError(f"no {PACKAGE}/ under {root}")
    on_disk = (path.relative_to(root).as_posix() for path in base.rglob("*") if path.is_file())
    tracked = tracked_files(root)
    return tuple(
        sorted(p for p in on_disk if not is_bytecode(p) and (tracked is None or p in tracked))
    )


def list_set(root: Path, name: SetName) -> tuple[str, ...]:
    """The set's files, sorted. A frozen set that comes back empty is an error: the root is wrong."""
    files = tuple(p for p in package_files(root) if set_of(p) == name)
    if not files and name in FROZEN_SETS:
        raise SetError(f"the {name} set is empty under {root}")
    return files


def unmatched_patterns(root: Path) -> tuple[str, ...]:
    """Frozen-set patterns that match no file.

    A renamed or deleted file would otherwise leave its set silently smaller.
    """
    files = package_files(root)
    return tuple(
        pattern
        for name in FROZEN_SETS
        for pattern in PATTERNS[name]
        if not any(PurePosixPath(p).full_match(pattern) for p in files)
    )


def file_sha256(root: Path, path: str) -> str:
    return hashlib.sha256((root / path).read_bytes()).hexdigest()


def set_sha256(root: Path, paths: Iterable[str]) -> str:
    """sha256 over path, zero byte, bytes, zero byte, for each file in sorted path order."""
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update((root / path).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()
