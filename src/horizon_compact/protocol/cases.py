"""The gate's case mode: when a real-case sweep may run (Phase 3.5 IMPLEMENTATION doc section 8, decision 10,
build step 6).

A real case's content did not exist at the tag, so the tag's content hash cannot admit it. A case sweep is
admitted only when, for that case:

1. **its record is committed** (``experiment/cases/<label>/case.lock``) and the content supplied to the run
   hashes to it: the dossier, the scenario text and the rubric. Real-case content may never be in the public
   repository (Phase 5 decision 5), so the record holds hashes and the content arrives at run time;
2. **the record was pushed before any model saw the case**, shown by two times nobody here can set: the
   created time of a GitHub Actions run on a commit holding the record, before the S3 ``LastModified`` of the
   case's first recognition-probe object (results objects are write-once, so ``LastModified`` is when it was
   written). A commit's own date is set by its author and proves nothing, so it is never read;
3. **every recognition probe that counts passed**, on every official model, three calls each (``planning/07``
   §10.3). A case that failed is coarsened and re-probed once: the second set counts, the first is kept, and a
   second set exists only after the first failed;
4. checks 2, 5, 6, 7 and 8 of the grid's gate hold (document, instrument, analysis, model, container); the
   content hash, check 3, is replaced by 1 above, and the sealed-template check does not apply.

**A re-probe needs a coarsened dossier.** The probe reads only the dossier, so a second set on a dossier an
earlier set was probed on would be probing until it passes; it is refused.

**The order, for a coarsened case, is checked twice.** The rubric must precede the case's first probe of any
set (no model sees a case before its rubric). The coarsened content must precede the first probe of the set
that counts (the content that passed is the content that was committed first). An uncoarsened case is the same
rule with one set.

**Where each part runs.** Check 2 needs the GitHub API and S3, so it runs on the laptop at launch and its
finding goes into the manifest (``OrderFinding.as_record``); the container re-checks 1, 3 and 4 and refuses a
manifest whose finding is missing or not admitted. The GitHub and S3 readers are interfaces here (``CiRun``,
``ProbeRecord``), tested with fakes; Phase 5 writes the real ones, so this check does not depend on where the
content lives.
"""

from __future__ import annotations

import hashlib
import tomllib
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from horizon_compact.model_config import ModelsFile
from horizon_compact.protocol.gate import (
    GateResult,
    check_analysis,
    check_container,
    check_instrument,
    check_lock_file,
    default_package_dir,
)
from horizon_compact.protocol.lock import (
    LINE_ENDING_NOTE,
    Lock,
    check_document,
    identity_differences,
)
from horizon_compact.sweep.identity import RunnerIdentity
from horizon_compact.sweep.plan import SweepRefusal

CASE_VERSION = 1
CASES_DIR = "experiment/cases"
CASE_FILE = "case.lock"
PROBE_CALLS = 3  # per model per probe set (planning/07 section 10.3)
MAX_PROBE_SETS = 2  # the first, and one re-probe after coarsening
CASE_REFUSED = "case sweep refused"


class CaseError(Exception):
    """The case record cannot be read. The message names the file and the reason."""


# --- the case record ----------------------------------------------------------------------------------------


class CaseRecord(BaseModel):
    """``case.lock``: hashes only, never content.

    ``probe_set`` is the set this content is probed in: 1 as built, 2 after coarsening. Phase 5 writes the
    file; a field it adds needs a ``case_version`` this reader knows.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    case_version: int
    label: str
    probe_set: int = Field(ge=1, le=MAX_PROBE_SETS)
    dossier_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    scenario_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    rubric_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


def case_path(label: str) -> str:
    pure = PurePosixPath(label)
    if len(pure.parts) != 1 or label in {"", ".", ".."} or "\\" in label:
        raise CaseError(f"{label!r} is not a case label")
    return f"{CASES_DIR}/{label}/{CASE_FILE}"


def parse_case(text: str, label: str) -> CaseRecord:
    """A record's text as committed. Its label must be the folder's, so a record cannot vouch for another
    case."""
    try:
        raw = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise CaseError(f"{case_path(label)} is not valid TOML: {exc}") from exc
    if raw.get("case_version") != CASE_VERSION:
        raise CaseError(
            f"{case_path(label)} has case_version {raw.get('case_version')!r}; this reader knows "
            f"{CASE_VERSION}"
        )
    try:
        record = CaseRecord.model_validate(raw)
    except ValidationError as exc:
        fields = "; ".join(
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in exc.errors()
        )
        raise CaseError(f"{case_path(label)} is malformed: {fields}") from exc
    if record.label != label:
        raise CaseError(f"{case_path(label)} names case {record.label!r}")
    return record


def read_case(root: Path, label: str) -> CaseRecord:
    path = root / case_path(label)
    if not path.is_file():
        raise CaseError(f"no case record: {case_path(label)} is not committed")
    return parse_case(path.read_text(encoding="utf-8"), label)


# --- what the checks read -----------------------------------------------------------------------------------


@dataclass(frozen=True)
class CaseContent:
    """The case as supplied to the run, from private storage. Bytes, hashed as they are."""

    dossier: bytes
    scenario: bytes
    rubric: bytes


@dataclass(frozen=True)
class CiRun:
    """One GitHub Actions run: when GitHub created it, and the case record as it stood at the run's head
    commit (None where that commit has no record). Both come from servers whose clocks he cannot set."""

    run_id: str
    created_at: datetime
    record_text: str | None


@dataclass(frozen=True)
class ProbeRecord:
    """One recognition-probe call's object in S3: its model, its set, whether it passed (named neither the
    company nor its brand) and its ``LastModified``."""

    key: str
    model_key: str
    probe_set: int
    passed: bool
    last_modified: datetime


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _naive(moment: datetime) -> bool:
    return moment.tzinfo is None or moment.utcoffset() is None


# --- check 1: the content hashes to the record --------------------------------------------------------------


def check_case_content(record: CaseRecord, content: CaseContent) -> list[str]:
    return [
        f"{part} does not hash to {case_path(record.label)}"
        for part, data, expected in (
            ("the dossier", content.dossier, record.dossier_sha256),
            ("the scenario text", content.scenario, record.scenario_sha256),
            ("the rubric", content.rubric, record.rubric_sha256),
        )
        if _sha256(data) != expected
    ]


# --- check 3: the probes ------------------------------------------------------------------------------------


def counting_set(probes: Sequence[ProbeRecord]) -> int | None:
    return max((p.probe_set for p in probes), default=None)


def check_case_probes(
    record: CaseRecord, probes: Sequence[ProbeRecord], official_models: Sequence[str]
) -> list[str]:
    """Every official model probed three times in the set that counts, every call passed; that set is the
    record's; a second set only after the first failed."""
    label = record.label
    if not probes:
        return [f"case {label} has no recognition probe"]
    counted = counting_set(probes)
    assert counted is not None
    lines: list[str] = []
    if counted > MAX_PROBE_SETS or any(p.probe_set < 1 for p in probes):
        return [f"case {label} has probe sets outside 1-{MAX_PROBE_SETS}: a case is re-probed once"]
    if counted != record.probe_set:
        lines.append(
            f"case {label}'s record is for probe set {record.probe_set}, but set {counted} is the last probed"
        )
    if counted == 2 and all(p.passed for p in probes if p.probe_set == 1):
        lines.append(f"case {label} was re-probed although its first probe set passed")
    for model in sorted(official_models):
        calls = [p for p in probes if p.probe_set == counted and p.model_key == model]
        if len(calls) < PROBE_CALLS:
            lines.append(
                f"case {label}: {model} has {len(calls)} probe calls in set {counted}, not {PROBE_CALLS}"
            )
        failed = [p.key for p in calls if not p.passed]
        if failed:
            lines.append(
                f"case {label}: {model} failed the recognition probe ({', '.join(failed)})"
            )
    return lines


# --- check 2: the order, by server times --------------------------------------------------------------------


@dataclass(frozen=True)
class OrderFinding:
    """Check 2's result, written into the case sweep's manifest on the laptop and re-read by the container."""

    label: str
    admitted: bool
    rubric_run: str | None
    rubric_run_created: str | None
    content_run: str | None
    content_run_created: str | None
    first_probe: str | None
    first_probe_modified: str | None
    first_counting_probe: str | None
    first_counting_probe_modified: str | None
    reasons: tuple[str, ...]

    def as_record(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "admitted": self.admitted,
            "rubric_run": self.rubric_run,
            "rubric_run_created": self.rubric_run_created,
            "content_run": self.content_run,
            "content_run_created": self.content_run_created,
            "first_probe": self.first_probe,
            "first_probe_modified": self.first_probe_modified,
            "first_counting_probe": self.first_counting_probe,
            "first_counting_probe_modified": self.first_counting_probe_modified,
            "reasons": list(self.reasons),
        }


def _earliest_run(
    runs: Sequence[CiRun], label: str, holds: Callable[[CaseRecord], bool]
) -> CiRun | None:
    found: list[CiRun] = []
    for run in runs:
        if run.record_text is None:
            continue
        try:
            at_run = parse_case(run.record_text, label)
        except CaseError:
            continue  # a record this reader cannot read attests to nothing
        if holds(at_run):
            found.append(run)
    return min(found, key=lambda r: r.created_at, default=None)


def _iso(moment: datetime | None) -> str | None:
    return moment.isoformat() if moment is not None else None


def check_case_order(
    record: CaseRecord, runs: Sequence[CiRun], probes: Sequence[ProbeRecord]
) -> OrderFinding:
    """The rubric before the case's first probe; the content that counts before its own set's first probe.
    Each time is the earliest CI run on a commit whose record carries that hash."""
    label = record.label
    naive = [f"CI run {r.run_id}" for r in runs if _naive(r.created_at)] + [
        f"probe {p.key}" for p in probes if _naive(p.last_modified)
    ]
    if naive:
        reason = f"times without a time zone cannot be ordered: {', '.join(naive)}"
        return OrderFinding(label, False, None, None, None, None, None, None, None, None, (reason,))
    rubric_run = _earliest_run(runs, label, lambda r: r.rubric_sha256 == record.rubric_sha256)
    content_run = _earliest_run(
        runs,
        label,
        lambda r: (
            (r.dossier_sha256, r.scenario_sha256, r.probe_set)
            == (record.dossier_sha256, record.scenario_sha256, record.probe_set)
        ),
    )
    first = min(probes, key=lambda p: p.last_modified, default=None)
    counting = [p for p in probes if p.probe_set == record.probe_set]
    first_counting = min(counting, key=lambda p: p.last_modified, default=None)

    reasons: list[str] = []
    if record.probe_set > 1 and _earliest_run(
        runs,
        label,
        lambda r: r.probe_set < record.probe_set and r.dossier_sha256 == record.dossier_sha256,
    ):
        reasons.append(
            f"case {label}'s probe set {record.probe_set} has the dossier an earlier set was probed on: "
            "a re-probe follows coarsening, and the probe reads only the dossier"
        )
    if first is None or first_counting is None:
        reasons.append(
            f"case {label} has no recognition probe in set {record.probe_set} to order against"
        )
    if rubric_run is None:
        reasons.append(f"no GitHub Actions run on a commit holding case {label}'s rubric hash")
    elif first is not None and not rubric_run.created_at < first.last_modified:
        reasons.append(
            f"case {label}'s rubric was first in CI at {rubric_run.created_at.isoformat()}, not before its "
            f"first probe at {first.last_modified.isoformat()}"
        )
    if content_run is None:
        reasons.append(
            f"no GitHub Actions run on a commit holding case {label}'s content for probe set "
            f"{record.probe_set}"
        )
    elif first_counting is not None and not content_run.created_at < first_counting.last_modified:
        reasons.append(
            f"case {label}'s content for probe set {record.probe_set} was first in CI at "
            f"{content_run.created_at.isoformat()}, not before that set's first probe at "
            f"{first_counting.last_modified.isoformat()}"
        )
    return OrderFinding(
        label=label,
        admitted=not reasons,
        rubric_run=rubric_run.run_id if rubric_run else None,
        rubric_run_created=_iso(rubric_run.created_at if rubric_run else None),
        content_run=content_run.run_id if content_run else None,
        content_run_created=_iso(content_run.created_at if content_run else None),
        first_probe=first.key if first else None,
        first_probe_modified=_iso(first.last_modified if first else None),
        first_counting_probe=first_counting.key if first_counting else None,
        first_counting_probe_modified=_iso(
            first_counting.last_modified if first_counting else None
        ),
        reasons=tuple(reasons),
    )


def check_order_finding(label: str, finding: Mapping[str, Any] | None) -> list[str]:
    """The container's view of check 2: the manifest's finding must exist, name this case and admit it."""
    if finding is None:
        return [
            f"the manifest has no order finding for case {label} (check 2 runs on the laptop at launch)"
        ]
    if finding.get("label") != label:
        return [f"the manifest's order finding is for case {finding.get('label')!r}, not {label!r}"]
    if finding.get("admitted") is not True:
        reasons = finding.get("reasons") or ["no reason recorded"]
        return [f"the order check did not admit case {label}: {'; '.join(map(str, reasons))}"]
    return []


# --- the case gate ------------------------------------------------------------------------------------------


def check_case_model(models: ModelsFile, model_key: str, lock: Lock) -> list[str]:
    """Check 7, as for the grid: one of the lock's models, with the same identity in ``models.toml``."""
    locked = lock.models.get(model_key)
    if locked is None:
        return [
            f"model {model_key} is not one of {lock.protocol}'s models ({', '.join(sorted(lock.models))})"
        ]
    config = models.models.get(model_key)
    if config is None:
        return [f"model {model_key} is in {lock.protocol} but not in models.toml"]
    return identity_differences(model_key, locked, config, lock.protocol)


def run_case_gate(
    label: str,
    content: CaseContent,
    probes: Sequence[ProbeRecord],
    order_finding: Mapping[str, Any] | None,
    models: ModelsFile,
    model_key: str,
    identity: RunnerIdentity,
    *,
    require_container: bool = True,
    why: str = "dry run",
    package_dir: Path | None = None,
) -> GateResult:
    """The container's case gate: the record and the content (1), the order finding from the manifest (2), the
    probes (3), and the grid's checks 2, 5, 6, 7 and 8 (4). Every failure, in that order."""
    root = (package_dir or default_package_dir()).parents[1]
    failures: list[str] = []
    lock, problems = check_lock_file(root)
    failures += problems
    record: CaseRecord | None = None
    try:
        record = read_case(root, label)
    except CaseError as exc:
        failures.append(str(exc))
    if record is not None:
        failures += check_case_content(record, content)
        failures += check_order_finding(label, order_finding)
    if lock is not None:
        if record is not None:
            failures += check_case_probes(record, probes, sorted(lock.models))
        failures += check_document(root, lock)
        failures += check_instrument(root, lock)
        failures += check_analysis(root, lock)
        failures += check_case_model(models, model_key, lock)
    container_failures, notes = check_container(identity, required=require_container, why=why)
    failures += container_failures
    if any(line.startswith(("document differs", "instrument", "analysis")) for line in failures):
        notes.append(LINE_ENDING_NOTE)
    return GateResult(tuple(failures), tuple(notes))


def case_refusal_message(result: GateResult) -> str:
    return "\n".join(f"{CASE_REFUSED}: {line}" for line in result.failures)


def check_case_official(
    label: str,
    content: CaseContent,
    probes: Sequence[ProbeRecord],
    order_finding: Mapping[str, Any] | None,
    models: ModelsFile,
    model_key: str,
    identity: RunnerIdentity,
    *,
    package_dir: Path | None = None,
) -> GateResult:
    """The case gate a real case session passes: every check, the container required. Raises on any
    failure."""
    result = run_case_gate(
        label,
        content,
        probes,
        order_finding,
        models,
        model_key,
        identity,
        package_dir=package_dir,
    )
    if not result.ok:
        raise SweepRefusal(case_refusal_message(result))
    return result
