"""The gate's GitHub reader (protocol §12.10 check (2); search-half doc §4.10).

One ``CiRun`` per GitHub Actions run of the repository: the run's ``created_at`` (GitHub's clock, which
nobody here can set) and the case record as it stood at the run's head commit (``git show``), or None where
that commit holds none. A commit's own date is never read.

**Fails closed on a missing run.** The check takes the earliest run whose commit holds a record carrying the
hash; a run that GitHub has expired or deleted is simply absent, so the check then finds a later run or none,
and refuses. What the listing still holds after retention expires is the first thing to check live
(search-half doc §4.10); until then this reader makes no claim about it.

``gh`` and ``git`` are injected, so the tests run on canned output and nothing here touches the network.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path

from horizon_compact.protocol.cases import CiRun, case_path

Runner = Callable[[Sequence[str]], str]

# One JSON object per run, one per line, whatever the page: `gh api --paginate` would otherwise concatenate
# whole pages.
RUNS_ARGS = (
    "api",
    "--paginate",
    "repos/{owner}/{repo}/actions/runs?per_page=100",
    "--jq",
    ".workflow_runs[] | {id: .id, created_at: .created_at, head_sha: .head_sha}",
)


class GithubReadError(Exception):
    """GitHub or git did not answer, or answered in a shape this reader does not know."""


def command_runner(program: str, cwd: Path | None = None) -> Runner:
    """``program`` run in ``cwd`` (the process's own directory if None), so ``gh``'s ``{owner}/{repo}`` and
    ``git show`` answer for the repository whatever directory the command was started in."""

    def run(args: Sequence[str]) -> str:
        try:
            result = subprocess.run([program, *args], capture_output=True, check=False, cwd=cwd)
        except OSError as exc:
            raise GithubReadError(f"{program} cannot run: {type(exc).__name__}") from exc
        if result.returncode != 0:
            raise GithubReadError(f"{program} {' '.join(args[:2])} failed ({result.returncode})")
        return result.stdout.decode("utf-8", errors="replace")

    return run


def parse_time(text: str) -> datetime:
    """GitHub's ISO time (``2026-10-16T21:04:05Z``) as an aware datetime."""
    try:
        moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GithubReadError(f"a run's created_at is not a time: {text!r}") from exc
    if moment.tzinfo is None:
        raise GithubReadError(f"a run's created_at has no time zone: {text!r}")
    return moment


def read_ci_runs(label: str, *, gh: Runner, git: Runner) -> list[CiRun]:
    path = case_path(label)
    runs: list[CiRun] = []
    seen: set[str] = set()
    for line in gh(RUNS_ARGS).splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
            run_id, created, sha = str(item["id"]), str(item["created_at"]), str(item["head_sha"])
        except (ValueError, KeyError, TypeError) as exc:
            raise GithubReadError(
                f"a run listing line is not a run ({type(exc).__name__})"
            ) from exc
        if run_id in seen:
            continue
        seen.add(run_id)
        try:
            record: str | None = git(["show", f"{sha}:{path}"])
        except GithubReadError:
            record = (
                None  # the commit holds no record, or is not in this clone: it attests to nothing
            )
        runs.append(CiRun(run_id=run_id, created_at=parse_time(created), record_text=record))
    return runs
