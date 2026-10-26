"""``hc case freeze``: the exploratory freeze's checks and its name-free evidence (exploratory
IMPLEMENTATION doc §3.1, steps 14a and 14b; search-half doc §4.11).

Reads only, then writes three files into ``docs/phases/evidence/phase-5/`` or none. In order: the two
selections are complete; each selected case, in D.1's order, passes every check the gate makes before a run
that can be made now (the committed, pushed ``case.lock``; the appendix's content and the stored copy hashing
to it; ``check_case_order`` on the CI runs and the probe objects; ``check_case_probes`` on the official models
of ``protocol.lock``; the scenario's and rubric's independent reads settled); no case decision has run;
nothing is there to be overwritten. Every reason is collected and the command refuses with all of them. The
readers (S3, GitHub, git) are injected, so the tests run on fakes and nothing here touches a network.

**The case sweep prefix.** No code fixes one yet: Phase 5.5 wires the case sweeps. The only mechanism is
``sweep_prefix``: ``<role>/<experiment>/<sweep_id>/``, where the experiment is a folder of the repository. So
a case decision is taken to be any object under ``development/``, ``pilot/`` or ``official/`` that is outside
the repository's own experiment folders, or whose key names a case label. That fails closed: an unrelated
object there refuses the freeze and is named by its experiment segment, for him to look at.

Before anything is written, every string that would be is checked against the private term file by the name
guard's own matcher; a hit refuses. The guard runs again on the commit (rule zero).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.exploratory import (
    AT_MOST,
    CARRIED,
    ExploratoryLog,
    ExploratoryRow,
    load_newest_exploratory,
)
from horizon_compact.casebuild.frozen import FrozenInputsError, Git
from horizon_compact.casebuild.search import (
    TYPES,
    K,
    LogError,
    Row,
    SelectionLog,
    load_newest_log,
)
from horizon_compact.caseprobe.github import GithubReadError
from horizon_compact.caseprobe.layout import CONTENT_FILES, content_key
from horizon_compact.caseprobe.upload import lock_pushed
from horizon_compact.experiment import EXPERIMENT_FILES
from horizon_compact.privacy.names import TermFile, find_terms
from horizon_compact.protocol.cases import (
    CaseContent,
    CaseError,
    CiRun,
    ProbeRecord,
    check_case_content,
    check_case_order,
    check_case_probes,
    read_case,
)
from horizon_compact.protocol.gate import check_lock_file
from horizon_compact.reader.read import UNSETTLED, ReaderError, _read_of_current, reads_settled
from horizon_compact.sweep.runner import ROLES
from horizon_compact.sweep.store import Store

EVIDENCE_DIR = "docs/phases/evidence/phase-5"
SELECTION_FILE = "selection-public.json"
EXPLORATORY_FILE = "exploratory-public.json"
FREEZE_FILE = "freeze.json"
OUTPUT_FILES = (SELECTION_FILE, EXPLORATORY_FILE, FREEZE_FILE)
FREEZE_VERSION = 1
SHOWN = 5  # experiment names listed in a refusal about case decisions


class FreezeError(Exception):
    """The freeze is refused, and nothing was written. ``reasons`` has one line for each cause."""

    def __init__(self, reasons: Sequence[str]) -> None:
        self.reasons = tuple(reasons)
        super().__init__("\nrefused: ".join(self.reasons))


@dataclass(frozen=True)
class FreezeReaders:
    """What the freeze reads from outside the appendix: the results bucket, the probe records and the CI runs
    of a case, and git for the pushed check."""

    store: Store
    probes: Callable[[str], Sequence[ProbeRecord]]
    runs: Callable[[str], Sequence[CiRun]]
    git: Git


@dataclass(frozen=True)
class Frozen:
    """The three files' text by name, the cases they cover in D.1's order, and each case's order finding."""

    files: Mapping[str, str]
    cases: tuple[str, ...]
    admitted: Mapping[str, bool]


# --- small readers ------------------------------------------------------------------------------------------


def _newest(directory: Path, stem: str) -> str | None:
    """The highest-numbered ``<stem>-<n>.json`` (numerically: 10 is after 9), as the logs' loaders choose."""
    pattern = re.compile(rf"{re.escape(stem)}-(\d+)\.json")
    numbers = [
        int(m.group(1))
        for path in directory.glob(f"{stem}-*.json")
        if (m := pattern.fullmatch(path.name))
    ]
    return f"{stem}-{max(numbers)}.json" if numbers else None


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _say(label: str, line: str) -> str:
    return line if label in line else f"{label}: {line}"


def _dump(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


# --- 14a item 1: the selections -----------------------------------------------------------------------------


def _selections(
    search: CaseAppendix,
) -> tuple[SelectionLog | None, ExploratoryLog | None, list[str]]:
    reasons: list[str] = []
    pre: SelectionLog | None = None
    xlog: ExploratoryLog | None = None
    try:
        pre = load_newest_log(search)
    except LogError as exc:
        reasons.append(f"the pre-registered selection log: {exc}")
    if _newest(search.directory, "exploratory-log") is None:
        reasons.append("there is no exploratory log")
    else:
        try:
            xlog = load_newest_exploratory(search)
        except LogError as exc:
            reasons.append(f"the exploratory log: {exc}")
    if pre is not None:
        for case_type in TYPES:
            reasons += [
                f"the pre-registered log is not complete ({case_type}): {line}"
                for line in pre.selection(case_type).waiting
            ]
        reasons += [f"the pre-registered log: {line}" for line in pre.problems()]
    if xlog is not None:
        chosen = xlog.selection()
        reasons += [f"the exploratory log is not complete: {line}" for line in chosen.waiting]
        reasons += [f"the exploratory log: {line}" for line in xlog.problems()]
        if not chosen.cases:
            reasons.append("the exploratory log has no case")
    return pre, xlog, reasons


# --- 14a item 3: no case decision has run -------------------------------------------------------------------


def case_decision_objects(
    store: Store, labels: Sequence[str], experiments: Collection[str]
) -> list[str]:
    """One reason for each sweep role that holds an object outside ``experiments`` (the repository's
    experiment folders) or naming a case label. The module note says why that stands for a sweep prefix."""
    names = [re.compile(rf"(?<![A-Za-z0-9]){re.escape(label)}(?![A-Za-z0-9])") for label in labels]
    reasons: list[str] = []
    for role in ROLES:
        stray: list[str] = []
        for key in store.list_keys(f"{role}/"):
            parts = key.split("/")
            experiment = parts[1] if len(parts) > 2 else ""
            if experiment not in experiments or any(name.search(key) for name in names):
                stray.append(experiment or "(none)")
        if stray:
            distinct = sorted(set(stray))
            shown = ", ".join(distinct[:SHOWN]) + (
                f" and {len(distinct) - SHOWN} more" if len(distinct) > SHOWN else ""
            )
            reasons.append(
                f"{len(stray)} object(s) under {role}/ are outside the repository's experiments or name "
                f"a case (experiment segment: {shown}): a case decision may have run (search-half DoD 6)"
            )
    return reasons


def _experiments(root: Path) -> set[str]:
    base = root / "experiment"
    if not base.is_dir():
        return set()
    return {p.name for p in base.iterdir() if all((p / f).is_file() for f in EXPERIMENT_FILES)}


# --- 14a item 2: one case's checks --------------------------------------------------------------------------


def _probe_results(probes: Iterable[ProbeRecord]) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, str], list[ProbeRecord]] = {}
    for probe in probes:
        grouped.setdefault((probe.probe_set, probe.model_key), []).append(probe)
    return [
        {"set": s, "model": m, "calls": len(calls), "passed": sum(1 for c in calls if c.passed)}
        for (s, m), calls in sorted(grouped.items())
    ]


def _case_reads(case: CaseAppendix) -> dict[str, dict[str, Any]]:
    """The scenario's and rubric's reading as they now stand, after the lock's own check that each has a read
    and each "concerns" or "disagrees" has his resolution."""
    reads_settled(case)
    found: dict[str, dict[str, Any]] = {}
    for kind in ("scenario", "rubric"):
        attempt, _ = _read_of_current(case, kind)
        found[kind] = {
            "reading": attempt.reading or "unread",
            "his_resolution": attempt.reading == UNSETTLED[kind],
        }
    return found


def _appendix_content(case: CaseAppendix, probe_set: int) -> CaseContent | list[str]:
    paths = (case.dossier_path_for(probe_set), case.scenario_path, case.rubric_path)
    try:
        dossier, scenario, rubric = (p.read_bytes() for p in paths)
    except OSError as exc:
        return [f"cannot read a content file: {exc.strerror or type(exc).__name__}"]
    return CaseContent(dossier, scenario, rubric)


def _stored_content(store: Store, label: str, probe_set: int) -> CaseContent | list[str]:
    try:
        texts = {name: store.get(content_key(label, probe_set, name)) for name in CONTENT_FILES}
    except (BotoCoreError, ClientError) as exc:
        return [f"cannot read set {probe_set} from storage: {type(exc).__name__}"]
    missing = [name for name, text in texts.items() if text is None]
    if missing:
        return [f"set {probe_set} is not in storage: {', '.join(missing)}"]
    dossier, scenario, rubric = (str(texts[name]).encode("utf-8") for name in CONTENT_FILES)
    return CaseContent(dossier, scenario, rubric)


def _check_case(
    label: str,
    root: Path,
    case: CaseAppendix,
    readers: FreezeReaders,
    official_models: Sequence[str],
    reasons: list[str],
) -> dict[str, Any] | None:
    """Every check for one case. Reasons are appended; the evidence is returned only when none was found."""
    found: list[str] = []
    try:
        record = read_case(root, label)
    except CaseError as exc:
        reasons.append(_say(label, str(exc)))
        return None
    try:
        lock_pushed(readers.git, label)
    except FrozenInputsError as exc:
        found.append(str(exc))
    content = _appendix_content(case, record.probe_set)
    found += content if isinstance(content, list) else check_case_content(record, content)
    stored = _stored_content(readers.store, label, record.probe_set)
    if isinstance(stored, list):
        found += stored
    else:
        found += [f"in storage, {line}" for line in check_case_content(record, stored)]
    probes: Sequence[ProbeRecord] = []
    finding = None
    try:
        probes = readers.probes(label)
        runs = readers.runs(label)
    except (GithubReadError, BotoCoreError, ClientError) as exc:
        found.append(f"cannot read the CI runs or the probe records: {type(exc).__name__}")
    else:
        finding = check_case_order(record, runs, probes)
        found += list(finding.reasons)
        found += check_case_probes(record, probes, official_models)
    reads: dict[str, dict[str, Any]] = {}
    try:
        reads = _case_reads(case)
    except ReaderError as exc:
        found.append(str(exc))
    reasons += [_say(label, line) for line in found]
    if found or finding is None:
        return None
    return {
        "record": record,
        "probes": _probe_results(probes),
        "finding": finding,
        "reads": reads,
    }


# --- 14b: what is written -----------------------------------------------------------------------------------


def _rejection_reads(
    rows: Iterable[Row], copied: Callable[[Row, str], bool]
) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for row in rows:
        for criterion, read in row.reads.items():
            if copied(row, criterion):
                continue
            entry = counts.setdefault(criterion, {"agrees": 0, "disputes": 0})
            entry["agrees" if read.agrees else "disputes"] += 1
    return {criterion: counts[criterion] for criterion in sorted(counts)}


def _carried_copy(row: Row, criterion: str) -> bool:
    """A carried row's reads before criterion 4 are copies of the pre-registered log's, counted there."""
    return isinstance(row, ExploratoryRow) and row.source is not None and criterion in CARRIED


def _sources(search: CaseAppendix) -> list[dict[str, str]]:
    """The logs the public views came from: the exploratory log, the selection logs it carries rows from and
    the newest selection log, each by file name and sha256."""
    xlog_name = _newest(search.directory, "exploratory-log")
    pre_name = _newest(search.directory, "selection-log")
    assert xlog_name is not None and pre_name is not None  # both loaded, so both files exist
    xlog_text = (search.directory / xlog_name).read_text(encoding="utf-8")
    names = [xlog_name, *ExploratoryLog.source_names(xlog_text), pre_name]
    return [
        {"file": name, "sha256": _file_sha256(search.directory / name)}
        for name in dict.fromkeys(names)
    ]


def _freeze_record(
    search: CaseAppendix,
    pre: SelectionLog,
    xlog: ExploratoryLog,
    evidence: Mapping[str, dict[str, Any]],
) -> dict[str, Any]:
    chosen = xlog.selection()
    rows = [xlog.rows[c] for c in chosen.cases]
    cases = []
    for row in rows:
        found = evidence[row.id]
        record = found["record"]
        cases.append(
            {
                "label": row.id,
                "step": row.step,
                "type": row.type,
                "filled": row.id in chosen.filled,
                "carried": row.source is not None,
                "text": row.label,
                "probe_set": record.probe_set,
                "dossier_sha256": record.dossier_sha256,
                "scenario_sha256": record.scenario_sha256,
                "rubric_sha256": record.rubric_sha256,
                "reads": found["reads"],
            }
        )
    tallies: dict[str, dict[str, int]] = {"scenario": {}, "rubric": {}}
    for found in evidence.values():
        for kind, read in found["reads"].items():
            tallies[kind][read["reading"]] = tallies[kind].get(read["reading"], 0) + 1
    by_type = {t: sum(1 for r in rows if r.type == t) for t in TYPES}
    released = next((e for e in xlog.events if e["event"] == "released"), None)
    return {
        "freeze_version": FREEZE_VERSION,
        "sources": _sources(search),
        "cases": cases,
        "probes": {label: found["probes"] for label, found in evidence.items()},
        "order": [found["finding"].as_record() for found in evidence.values()],
        "reads": {
            "rejections": {
                "preregistered": _rejection_reads(pre.rows.values(), lambda r, c: False),
                "exploratory": _rejection_reads(xlog.rows.values(), _carried_copy),
            },
            "scenario": dict(sorted(tallies["scenario"].items())),
            "rubric": dict(sorted(tallies["rubric"].items())),
        },
        "shortfall": {
            "at_most": AT_MOST,
            "cases": len(rows),
            "cases_by_type": by_type,
            "short_by_type": {t: max(0, K[t] - by_type[t]) for t in TYPES},
            "filled": len(chosen.filled),
        },
        "hold": {"released": xlog.fill_released, "on": released["on"] if released else None},
    }


def _name_hits(files: Mapping[str, str], term_file: TermFile) -> list[str]:
    """Where the name guard's matcher finds a term in what would be written: the file and the line, never the
    term."""
    return [
        f"{name} line {match.line}: a term from the name guard's list"
        for name, text in files.items()
        for match in find_terms(text, term_file)
    ]


def _already_frozen(root: Path) -> list[str]:
    folder = root / EVIDENCE_DIR
    return [
        f"{EVIDENCE_DIR}/{name} already exists: the freeze is write-once"
        for name in OUTPUT_FILES
        if (folder / name).exists()
    ]


def build_freeze(
    search: CaseAppendix,
    root: Path,
    readers: FreezeReaders,
    term_file: TermFile,
    *,
    progress: Callable[[str], None] = lambda line: None,
) -> Frozen:
    """Every check of 14a, then the three files' text with the name check of 14b. Raises ``FreezeError`` with
    every reason; writes nothing (see ``write_freeze``)."""
    existing = _already_frozen(root)
    if existing:
        raise FreezeError(existing)
    pre, xlog, reasons = _selections(search)
    lock, problems = check_lock_file(root)
    reasons += problems
    evidence: dict[str, dict[str, Any]] = {}
    if xlog is not None and lock is not None:
        official = sorted(lock.models)
        for label in xlog.selection().cases:
            progress(f"checking {label}")
            found = _check_case(
                label, root, CaseAppendix(search.root, label), readers, official, reasons
            )
            if found is not None:
                evidence[label] = found
    if xlog is not None:
        progress("looking for a case decision under the sweep prefixes")
        try:
            reasons += case_decision_objects(
                readers.store, list(xlog.selection().cases), _experiments(root)
            )
        except (BotoCoreError, ClientError) as exc:
            reasons.append(f"cannot list the results bucket: {type(exc).__name__}")
    if reasons or pre is None or xlog is None:
        raise FreezeError(reasons)
    files = {
        SELECTION_FILE: _dump(pre.public_view()),
        EXPLORATORY_FILE: _dump(xlog.public_view()),
        FREEZE_FILE: _dump(_freeze_record(search, pre, xlog, evidence)),
    }
    hits = _name_hits(files, term_file)
    if hits:
        raise FreezeError(hits)
    return Frozen(
        files=files,
        cases=tuple(evidence),
        admitted={label: found["finding"].admitted for label, found in evidence.items()},
    )


def write_freeze(root: Path, frozen: Frozen) -> list[Path]:
    """The three files, write-once and all or none: each is completed under a temporary name, then all are
    linked into place, and a link that fails removes the ones already made."""
    existing = _already_frozen(root)
    if existing:
        raise FreezeError(existing)
    folder = root / EVIDENCE_DIR
    folder.mkdir(parents=True, exist_ok=True)
    temps: dict[str, Path] = {}
    linked: list[Path] = []
    try:
        for name in OUTPUT_FILES:
            fd, temp_name = tempfile.mkstemp(dir=folder, prefix=".partial-")
            temps[name] = Path(temp_name)
            with os.fdopen(fd, "wb") as handle:
                handle.write(frozen.files[name].encode("utf-8"))
        for name in OUTPUT_FILES:
            os.link(temps[name], folder / name)
            linked.append(folder / name)
    except OSError as exc:
        for path in linked:
            path.unlink(missing_ok=True)
        raise FreezeError(
            [f"cannot write the freeze: {exc.strerror or type(exc).__name__}; nothing was kept"]
        ) from exc
    finally:
        for temp in temps.values():
            temp.unlink(missing_ok=True)
    return linked
