"""The private appendix: where a case's raw responses, sources and dossier are written (IMPLEMENTATION §4.1).

Found the way the name guard finds its term file: ``HC_APPENDIX_DIR`` or local git config ``hc.appendixDir``,
no default, and no path in any tracked file. **Before writing anything it asks git whether the target would be
tracked** (``git check-ignore``) and refuses if so, so a misconfigured directory inside a clone cannot put a
case into history. Every write is write-once: a file that exists is never replaced.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from horizon_compact.casebuild.config import git_config_value, setting

ENV_VAR = "HC_APPENDIX_DIR"
GIT_CONFIG_KEY = "hc.appendixDir"

# A neutral label such as "closure-1" or "retool-2": lower case, digits, single hyphens.
LABEL = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")


class AppendixError(Exception):
    """The appendix is not configured, would be tracked, or a write would replace something."""


def appendix_dir(
    *,
    environ: Mapping[str, str] | None = None,
    git_config: Callable[[str], str] = git_config_value,
) -> Path:
    value = setting(ENV_VAR, GIT_CONFIG_KEY, environ=environ, git_config=git_config)
    if not value:
        raise AppendixError(
            f"no appendix directory is configured: set {ENV_VAR} or local git config {GIT_CONFIG_KEY}. "
            "There is no default."
        )
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise AppendixError("the appendix directory must be an absolute path")
    return path


def _git(directory: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    # Drop every GIT_* variable: a GIT_DIR or GIT_WORK_TREE from the caller's shell would make git answer
    # for the wrong repository. Messages forced to English, since one is matched below.
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["LC_ALL"] = "C"
    try:
        return subprocess.run(
            ["git", "-C", str(directory), *args], capture_output=True, check=False, env=env
        )
    except OSError as exc:
        raise AppendixError(f"cannot run git to check the target: {type(exc).__name__}") from exc


def would_be_tracked(path: Path) -> bool:
    """Whether git would track ``path``: it is inside a repository and no ignore rule covers it.

    A path in no repository is not tracked. Anything git cannot answer is an error, never a pass.
    """
    probe = path.absolute()
    while not probe.exists():
        if probe.parent == probe:
            raise AppendixError("no part of the target path exists")
        probe = probe.parent
    directory = probe if probe.is_dir() else probe.parent
    top = _git(directory, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        if b"not a git repository" in top.stderr:
            return False
        raise AppendixError("git could not say whether the target is inside a repository")
    ignored = _git(directory, "check-ignore", "-q", "--no-index", "--", str(path.absolute()))
    if ignored.returncode == 0:
        return False
    if ignored.returncode == 1:
        return True
    raise AppendixError("git check-ignore failed; refusing to write")


def ensure_untracked(path: Path) -> None:
    if would_be_tracked(path):
        raise AppendixError(
            "refusing to write: git would track that location. Point the appendix at a directory "
            "outside the repository or one an ignore rule covers."
        )


@dataclass(frozen=True)
class CaseAppendix:
    """One case's directory inside the appendix, addressed by its neutral label."""

    root: Path
    label: str

    def __post_init__(self) -> None:
        if not LABEL.fullmatch(self.label):
            raise AppendixError(
                "a case label is lower case words joined by hyphens, such as closure-1"
            )

    @property
    def directory(self) -> Path:
        return self.root / self.label

    @property
    def cache_dir(self) -> Path:
        return self.directory / "cache"

    @property
    def sources_path(self) -> Path:
        return self.directory / "sources.json"

    @property
    def build_path(self) -> Path:
        return self.directory / "build.json"

    @property
    def dossier_path(self) -> Path:
        return self.directory / "dossier.toml"

    @property
    def scenario_path(self) -> Path:
        return self.directory / "scenario.toml"

    @property
    def terms_path(self) -> Path:
        """The case's private term list (`term: Name => role` lines), written by hand before the build."""
        return self.directory / "terms.txt"

    @property
    def hand_boundaries_path(self) -> Path:
        """Item boundaries for a filing the splitter refuses, written by hand; absent when none is needed."""
        return self.directory / "hand-boundaries.json"

    @property
    def sections_path(self) -> Path:
        return self.directory / "sections.json"

    @property
    def flags_template_path(self) -> Path:
        return self.directory / "reviewed-flags.template.json"

    @property
    def reviewed_flags_path(self) -> Path:
        return self.directory / "reviewed-flags.json"

    @property
    def assembly_path(self) -> Path:
        return self.directory / "assembly.json"

    def write_once(self, path: Path, data: bytes) -> None:
        """Write ``data`` inside this case's directory; refuse if it exists or git would track it."""
        target = Path(os.path.normpath(path.absolute()))  # collapses any ".."
        if not target.is_relative_to(Path(os.path.normpath(self.directory.absolute()))):
            raise AppendixError("a write outside the case's directory was refused")
        ensure_untracked(target)
        if target.exists():
            raise AppendixError(f"{target.name} already exists; the appendix is write-once")
        target.parent.mkdir(parents=True, exist_ok=True)
        # Complete the file under a temporary name, then link it into place: link fails if the name exists,
        # and a crash leaves no half-written target.
        fd, temp_name = tempfile.mkstemp(dir=target.parent, prefix=".partial-")
        temp = Path(temp_name)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
            try:
                os.link(temp, target)
            except FileExistsError as exc:
                raise AppendixError(
                    f"{target.name} already exists; the appendix is write-once"
                ) from exc
        finally:
            temp.unlink(missing_ok=True)


def open_case(
    label: str,
    *,
    environ: Mapping[str, str] | None = None,
    git_config: Callable[[str], str] = git_config_value,
) -> CaseAppendix:
    root = appendix_dir(environ=environ, git_config=git_config)
    ensure_untracked(root)
    return CaseAppendix(root=root, label=label)
