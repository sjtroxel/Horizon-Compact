"""``hc case lock``: write a case's ``case.lock`` (search-half doc §4.1 step 7, §5 step 8a).

The lock is the gate's check 1 record (protocol §12.10): the sha256 of the dossier, the scenario text and the
rubric, hashes only, never content. It is written by ``content_hashes`` and ``case_lock_text``, the two
functions the gate and ``hc case hashes`` use, so what is written is what the gate recomputes.

Every refusal comes before the write: the label, the three files, the state of an existing lock, at set 1
the dossier's hash against ``assembly.json``, and the scenario check (``casebuild/scenario.py``). A write is
atomic (a temporary file linked into place at set 1, so it never replaces one; replaced at set 2), so a
crash leaves no half lock.

**Probe set 1 is write-once.** A second lock is allowed only as probe set 2 after a coarsening (protocol
§12.8): the existing lock must be set 1, the rubric must hash the same (no model sees a case before its
rubric, and the rubric does not change with coarsening) and the dossier must hash differently (a re-probe
needs a coarsened dossier; the gate refuses a set 2 on a dossier set 1 was probed on). **What this cannot
check:** that set 1 actually failed. That is read from the probe records, which exist at step 10; here it
rests on him. The gate's ``check_case_probes`` refuses a re-probe whose first set passed.
"""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.scenario import check_scenario, format_failures
from horizon_compact.dossier.check import default_repo_root
from horizon_compact.protocol.cases import (
    CaseContent,
    CaseError,
    case_lock_text,
    case_path,
    content_hashes,
    parse_case,
)


class CaseLockError(Exception):
    """The lock cannot be written, and nothing was. The message names the reason, never a name or a figure."""


@dataclass(frozen=True)
class WrittenLock:
    path: Path
    probe_set: int
    text: str


def scenario_check_passes(case: CaseAppendix, repo_root: Path | None = None) -> None:
    """Refuse unless the case's scenario passes ``hc case scenario check`` (§4.6.1 item 9): every source
    re-checked, and ``scenario.toml`` equal to a fresh render byte for byte. The templates are the
    repository's own; the message names criteria and row ids, never a figure."""
    failures = check_scenario(case, repo_root or default_repo_root())
    if failures:
        raise CaseLockError("the scenario check failed: " + "; ".join(format_failures(failures)))


def _read(path: Path, what: str) -> bytes:
    if not path.is_file():
        raise CaseLockError(f"{what} does not exist: {path.name} is not in the case's folder")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise CaseLockError(f"cannot read {what}: {exc.strerror or type(exc).__name__}") from exc


def lock_case(
    case: CaseAppendix,
    repo_root: Path,
    *,
    probe_set: int = 1,
    scenario_check: Callable[[CaseAppendix], None] = scenario_check_passes,
) -> WrittenLock:
    try:
        relative = case_path(case.label)
    except CaseError as exc:
        raise CaseLockError(str(exc)) from exc
    content = CaseContent(
        dossier=_read(case.dossier_path, "the dossier"),
        scenario=_read(case.scenario_path, "the scenario"),
        rubric=_read(case.rubric_path, "the rubric"),
    )
    hashes = content_hashes(content)
    target = repo_root / relative

    if probe_set == 1:
        if target.exists():
            raise CaseLockError(_EXISTS.format(relative=relative))
        _check_assembled(case, hashes["dossier_sha256"])
    elif probe_set == 2:
        if not target.is_file():
            raise CaseLockError(f"{relative} does not exist: there is no set 1 to coarsen from")
        try:
            earlier = parse_case(target.read_text(encoding="utf-8"), case.label)
        except (CaseError, OSError) as exc:
            raise CaseLockError(f"the existing lock cannot be read: {exc}") from exc
        if earlier.probe_set != 1:
            raise CaseLockError(
                f"{relative} is already probe set {earlier.probe_set}: a case is re-probed once"
            )
        if earlier.rubric_sha256 != hashes["rubric_sha256"]:
            raise CaseLockError(
                "the rubric differs from set 1's: coarsening changes the dossier, never the rubric"
            )
        if earlier.dossier_sha256 == hashes["dossier_sha256"]:
            raise CaseLockError(
                "the dossier is the one set 1 was locked on: a re-probe needs a coarsened dossier "
                "(protocol §12.8)"
            )
    else:
        raise CaseLockError(f"probe set {probe_set} is not 1 or 2")

    scenario_check(case)

    text = case_lock_text(case.label, probe_set, hashes)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(dir=target.parent, prefix=".partial-")
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        if probe_set == 1:
            # link fails if the name exists, so set 1 stays write-once even against a lock written meanwhile
            try:
                os.link(temp, target)
            except FileExistsError as exc:
                raise CaseLockError(_EXISTS.format(relative=relative)) from exc
        else:
            temp.replace(target)
    finally:
        temp.unlink(missing_ok=True)
    return WrittenLock(target, probe_set, text)


_EXISTS = (
    "{relative} already exists: probe set 1 is write-once. A second lock is only `--probe-set 2` after a "
    "coarsening (protocol §12.8)"
)


def _check_assembled(case: CaseAppendix, dossier_sha256: str) -> None:
    """The dossier is the one ``hc case assemble`` wrote: its hash is ``assembly.json``'s. A hand-edited
    dossier would skip the flag review and the term check; and ``assembly.json`` exists only for a candidate
    ``hc case build`` accepted."""
    path = case.assembly_path
    if not path.is_file():
        raise CaseLockError(
            f"{path.name} does not exist: the dossier was not assembled by `hc case assemble`"
        )
    try:
        recorded = json.loads(path.read_bytes()).get("dossier_sha256")
    except (OSError, json.JSONDecodeError, AttributeError) as exc:
        raise CaseLockError(f"cannot read {path.name}: {type(exc).__name__}") from exc
    if recorded != dossier_sha256:
        raise CaseLockError(
            f"the dossier does not hash to {path.name}: it is not the dossier `hc case assemble` wrote"
        )
