"""The matcher's driver for a frozen case (Phase 5.5 IMPLEMENTATION doc §5.2, K2): ``hc case match``.

The computation is the tag's: ``read_runs``, ``match_case`` and the calibrated thresholds, all frozen with
``analysis/``. This module only feeds them. It reads the rubric from the results bucket, refuses unless it
hashes to ``case.lock``, loads the scenario through the same assembly a case sweep uses (``session.py``),
refuses any sweep that is not the case's or is unfinished (as ``results.build_results`` does), and writes one
results file per case and model, once.

**Matched from ``main`` (decision 2).** The tag has no case driver, so the file records HEAD, what ``hc
protocol check`` said about the frozen files on this checkout, and the analysis files' combined sha256 from
the lock. Together they show that the code that computed is the tag's.

**What the file holds** is §5.2's list and nothing else: the exploratory label text, run counts by final
status, per reading the label, the nearest objective, the gap, all five distances with spreads, the basis and
the undistanced counts, ``depends_on_reading``, the observable and excluded dimensions, and the company's
reading as the matcher used it (the choice and the renormalized shares, never an amount). Excerpts, outcome
terms and every sentence of the rubric are dropped by the reader (``casebuild/rubric.py``) before they get
here. **Nothing this module prints names a distance, a nearest objective or an allocation**: he runs it
before the reveal, and a command's output is read by anyone watching.

**An uncertain call's alternative reading** is a sentence in the rubric; its numbers come from the case's
``alternatives.toml`` in the appendix, which must hash to the committed ``alternatives.json`` (written before
any case run). A call with no transcription is reported as not matched, and ``depends_on_reading`` is then
``null`` (not evaluated), never ``false``.

Needs scipy through the analysis, which the container image leaves out: ``cli.py`` imports this inside its
command only.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from horizon_compact.analysis.matcher import (
    PRIMARY_READING,
    CaseMatch,
    CompanyDecision,
    MatcherError,
    check_decision,
    load_thresholds,
    match_case,
    observable_vector,
)
from horizon_compact.analysis.records import RecordRefusal, RunSet, read_runs
from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.rubric import (
    Rubric,
    RubricError,
    check_rubric_against,
    parse_alternatives,
    parse_rubric,
)
from horizon_compact.caseprobe.freeze import EVIDENCE_DIR, FREEZE_FILE
from horizon_compact.caseprobe.layout import runs_prefix
from horizon_compact.caseprobe.run import ProbeRefused, load_content
from horizon_compact.caseprobe.session import (
    CASE_LABEL,
    assemble_experiment,
    case_experiment_name,
    check_frozen,
)
from horizon_compact.experiment import Experiment, ExperimentError, Scenario
from horizon_compact.protocol.cases import (
    CaseContent,
    CaseError,
    CaseRecord,
    check_case_content,
    read_case,
)
from horizon_compact.protocol.gate import check_lock_file
from horizon_compact.protocol.lock import Lock, check_lock
from horizon_compact.sweep.plan import SweepRefusal
from horizon_compact.sweep.store import Store

RESULTS_VERSION = 1
CASE_RESULTS_DIR = Path("experiment") / "results" / "cases"
# Each case's alternatives.toml sha256, committed before any case run.
ALTERNATIVES_FILE = Path("docs") / "phases" / "evidence" / "phase-5.5" / "alternatives.json"
PROTOCOL_OK = "ok"


class MatchRefused(SweepRefusal):
    """The case cannot be matched, and nothing was written. The message holds every reason, never a value.
    A ``SweepRefusal`` so ``cli.py`` catches it without importing this module (it imports scipy)."""


@dataclass(frozen=True)
class CaseMaterial:
    """Everything about a frozen case that the rubric and the scenario fix, before any run is read."""

    label: str
    case_type: str
    exploratory_label: str
    record: CaseRecord
    lock: Lock
    experiment: Experiment
    scenario: Scenario
    rubric: Rubric
    decision: CompanyDecision
    # One per transcribed call, in the transcription's order.
    alternatives: tuple[CompanyDecision, ...]
    alternatives_sha256: str | None

    @property
    def unmatched_calls(self) -> list[str]:
        matched = {alternative.reading for alternative in self.alternatives}
        return [call.id for call in self.rubric.uncertain if call.id not in matched]


@dataclass(frozen=True)
class MatchResult:
    record: dict[str, Any]
    path: Path
    status_counts: dict[str, int]
    unmatched_calls: tuple[str, ...]


def _freeze_entry(root: Path, label: str) -> tuple[str, str] | None:
    """The frozen case's type and exploratory label text; None when the entry has neither as a string."""
    try:
        frozen = json.loads((root / EVIDENCE_DIR / FREEZE_FILE).read_text(encoding="utf-8"))
        entry = next(e for e in frozen["cases"] if str(e["label"]) == label)
        case_type, text = entry["type"], entry["text"]
    except (OSError, ValueError, KeyError, TypeError, StopIteration):
        return None
    if not (isinstance(case_type, str) and isinstance(text, str) and text.strip()):
        return None
    return case_type, text


def _registered(root: Path, label: str) -> tuple[str | None, list[str]]:
    """The committed sha256 of the case's ``alternatives.toml``; None when the case has none."""
    path = root / ALTERNATIVES_FILE
    if not path.exists():
        return None, []
    try:
        cases = json.loads(path.read_text(encoding="utf-8"))["cases"]
        digest = cases.get(label)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None, [
            f"{ALTERNATIVES_FILE.as_posix()} cannot be read as {{cases: {{label: sha256}}}}"
        ]
    if digest is not None and not isinstance(digest, str):
        return None, [f"{ALTERNATIVES_FILE.as_posix()} holds no sha256 string for case {label}"]
    return digest, []


def _alternatives(
    root: Path, appendix: Path, label: str, rubric: Rubric
) -> tuple[tuple[CompanyDecision, ...], str | None, list[str]]:
    """The transcribed alternatives, refused unless the private file hashes to the committed one. A case
    with neither has none; a file with no committed hash, or a hash with no file, is refused."""
    digest, reasons = _registered(root, label)
    if reasons:
        return (), None, reasons
    path = CaseAppendix(appendix, label).alternatives_path
    if digest is None:
        if path.exists():
            return (), None, [f"case {label} has an alternatives.toml whose hash is not committed"]
        return (), None, []
    try:
        data = path.read_bytes()
    except OSError as exc:
        return (), None, [f"cannot read case {label}'s alternatives.toml ({type(exc).__name__})"]
    if hashlib.sha256(data).hexdigest() != digest:
        return (), None, [f"case {label}'s alternatives.toml does not hash to the committed sha256"]
    try:
        found = parse_alternatives(data, rubric)
    except RubricError as exc:
        return (), None, [str(exc)]
    decisions = tuple(
        CompanyDecision(alternative.call, alternative.amounts, rubric.company_choice)
        for alternative in found
    )
    return decisions, digest, []


def load_material(root: Path, store: Store, label: str, appendix: Path) -> CaseMaterial:
    """The case as frozen: refuses, with every reason found, unless the label is in the freeze, the content
    in storage hashes to ``case.lock``, the scenario assembles, the rubric reads and fits it, and any
    transcribed alternatives hash to the committed file and fit it too."""
    try:
        record = read_case(root, label)
    except (CaseError, ValueError) as exc:
        raise MatchRefused(str(exc)) from exc
    reasons = check_frozen(root, label, record)
    entry = None if reasons else _freeze_entry(root, label)
    if not reasons and entry is None:
        reasons.append(f"{EVIDENCE_DIR}/{FREEZE_FILE} has no type and label text for case {label}")
    lock, lock_problems = check_lock_file(root)
    reasons += lock_problems
    content: CaseContent | None = None
    try:
        content = load_content(store, label, record.probe_set)
    except ProbeRefused as exc:
        reasons.append(str(exc))
    if content is not None:
        reasons += check_case_content(record, content)
    if reasons or content is None or lock is None or entry is None:
        raise MatchRefused("\n".join(dict.fromkeys(reasons)))

    try:
        experiment = assemble_experiment(root, label, content, lock)
        scenario = experiment.scenario
        rubric = parse_rubric(content.rubric)
    except (SweepRefusal, ExperimentError, RubricError) as exc:
        raise MatchRefused(str(exc)) from exc
    choice = scenario.choice
    reasons = check_rubric_against(
        rubric,
        label=label,
        scenario_id=scenario.id,
        scenario_total=scenario.total,
        choice_key=choice.key if choice is not None else None,
        options=[option.key for option in choice.options] if choice is not None else [],
        lines=[lever.key for lever in scenario.offered()],
    )
    decision = CompanyDecision(PRIMARY_READING, rubric.amounts, rubric.company_choice)
    alternatives, alternatives_sha256, problems = _alternatives(root, appendix, label, rubric)
    reasons += problems
    for reading in (decision, *alternatives):
        try:
            check_decision(scenario, reading)
        except MatcherError as exc:
            reasons.append(str(exc))
    if reasons:
        raise MatchRefused("\n".join(reasons))
    case_type, text = entry
    return CaseMaterial(
        label,
        case_type,
        text,
        record,
        lock,
        experiment,
        scenario,
        rubric,
        decision,
        alternatives,
        alternatives_sha256,
    )


def describe_rubric(material: CaseMaterial) -> list[str]:
    """``--check-rubric``'s lines: dimension names, reading names and the shape, and whether the primary
    reading, and each alternative, has enough dimensions for the shape's calibration. No choice, amount, run
    or result."""
    rubric, scenario = material.rubric, material.scenario
    thresholds = load_thresholds().get(scenario.id)
    lines = [
        f"{material.label}: shape {scenario.id}",
        f"  observable dimensions: {', '.join(rubric.observable) or 'none'}",
        f"  excluded dimensions:   {', '.join(rubric.excluded) or 'none'}",
        f"  readings:              {PRIMARY_READING}"
        + "".join(f", {alternative.reading}" for alternative in material.alternatives)
        + "".join(
            f", {call} (no transcribed alternative, not matched)"
            for call in material.unmatched_calls
        ),
    ]
    if thresholds is None:
        lines.append(f"  the matcher is not calibrated for shape {scenario.id}")
        return lines
    for reading in (material.decision, *material.alternatives):
        dimensions = reading.dimensions
        enough = "enough" if dimensions >= thresholds.k_star else "NOT enough"
        lines.append(
            f"  {reading.reading} reading: {dimensions} dimension(s) of the {thresholds.k_star} "
            f"needed: {enough}"
        )
    return lines


def read_sweep(store: Store, material: CaseMaterial, model_key: str, sweep_id: str) -> RunSet:
    """The case's sweep for this model, all runs finished. Refuses a manifest that is not the case's."""
    label, scenario = material.label, material.scenario
    try:
        prefix = runs_prefix(label, sweep_id)
    except ValueError as exc:
        raise MatchRefused(str(exc)) from exc
    text = store.get(f"{prefix}manifest.json")
    try:
        manifest = json.loads(text) if text is not None else None
    except ValueError:
        manifest = None
    if not isinstance(manifest, dict):
        raise MatchRefused(f"no readable manifest for sweep {sweep_id} under case {label}")
    reasons = []
    if manifest.get("sweep_id") != sweep_id:
        reasons.append(f"the manifest under {sweep_id} names another sweep")
    if manifest.get("experiment") != case_experiment_name(label):
        reasons.append(f"sweep {sweep_id} is not an experiment of case {label}")
    if manifest.get("label") != CASE_LABEL:
        reasons.append(f"sweep {sweep_id}'s label is not {CASE_LABEL!r}")
    if manifest.get("model_key") != model_key:
        reasons.append(f"sweep {sweep_id} is not a sweep of {model_key}")
    if manifest.get("scenarios") != [scenario.id]:
        reasons.append(f"sweep {sweep_id} does not run the case's one scenario ({scenario.id})")
    if reasons:
        raise MatchRefused("\n".join(reasons))
    try:
        runset = read_runs(store, prefix)
    except (RecordRefusal, ValueError) as exc:
        raise MatchRefused(str(exc)) from exc
    if runset.unfinished:
        raise MatchRefused(
            f"{len(runset.unfinished)} run(s) of sweep {sweep_id} are unfinished: the failure rules "
            "count finished runs only, so the sweep must finish before it is matched"
        )
    if not runset.rows:
        raise MatchRefused(f"sweep {sweep_id} has no finished run")
    return runset


def _company(material: CaseMaterial, decision: CompanyDecision) -> dict[str, Any]:
    """A reading of the company as the matcher used it: the choice and the renormalized shares of the
    observable lines. Never an amount."""
    lines = tuple(
        lever.key for lever in material.scenario.offered() if lever.key in decision.amounts
    )
    shares = observable_vector(decision.amounts, lines) if lines else None
    return {"reading": decision.reading, "choice": decision.choice, "shares": shares or {}}


def _plain(match: CaseMatch) -> dict[str, Any]:
    return dataclasses.asdict(match)


def build_record(
    material: CaseMaterial,
    match: CaseMatch,
    runset: RunSet,
    *,
    head: str,
) -> dict[str, Any]:
    rubric, lock = material.rubric, material.lock
    unmatched = material.unmatched_calls
    whole = _plain(match)
    return {
        "results_version": RESULTS_VERSION,
        "case": material.label,
        "type": material.case_type,
        "exploratory": True,
        "exploratory_label": material.exploratory_label,
        "experiment": material.experiment.name,
        "scenario_id": match.scenario_id,
        "model_key": match.model_key,
        "sweep_id": match.sweep_id,
        "run_counts": {
            "runs": len(runset.rows),
            "by_final_status": dict(sorted(Counter(r.status for r in runset.rows).items())),
        },
        "thresholds": {
            "d_star": match.d_star,
            "k_star": match.k_star,
            "alpha": match.alpha,
            "resamples": match.resamples,
        },
        "dimensions": {"observable": list(rubric.observable), "excluded": list(rubric.excluded)},
        "company": _company(material, material.decision),
        "company_alternatives": [_company(material, a) for a in material.alternatives],
        "readings": whole["readings"],
        "alternative_readings": {"matched": len(match.readings) - 1, "unmatched_calls": unmatched},
        # None = not evaluated: a call with no transcribed alternative cannot be said not to depend.
        "depends_on_reading": None if unmatched else match.depends_on_reading,
        "provenance": {
            "head": head,
            "protocol": lock.protocol,
            "protocol_check": PROTOCOL_OK,
            "analysis_sha256": lock.analysis.sha256,
            "uv_lock_sha256": lock.analysis.uv_lock_sha256,
            "rubric_sha256": material.record.rubric_sha256,
            "alternatives_sha256": material.alternatives_sha256,
            "sweep_id": match.sweep_id,
        },
    }


def results_path(root: Path, label: str, model_key: str) -> Path:
    return root / CASE_RESULTS_DIR / label / f"{model_key}.json"


def match_sweep(
    root: Path,
    store: Store,
    label: str,
    model_key: str,
    sweep_id: str,
    *,
    head: str,
    appendix: Path,
) -> MatchResult:
    """Every check, the frozen matcher and the record; writes nothing. ``path`` is where ``write_match`` will
    put it, and is refused here if it is already there."""
    material = load_material(root, store, label, appendix)
    reasons: list[str] = []
    report = check_lock(root)
    if not report.ok:
        reasons += [f"hc protocol check fails on this checkout: {line}" for line in report.failures]
    path = results_path(root, label, model_key)
    if path.exists():
        reasons.append(
            f"{path.relative_to(root).as_posix()} exists: a case result is never overwritten"
        )
    runset: RunSet | None = None
    try:
        runset = read_sweep(store, material, model_key, sweep_id)
    except MatchRefused as exc:
        reasons.append(str(exc))
    if reasons or runset is None:
        raise MatchRefused("\n".join(reasons))
    try:
        match = match_case(
            material.scenario,
            runset.rows,
            [material.decision, *material.alternatives],
            case_id=label,
            objectives=[objective.id for objective in material.experiment.objectives],
        )
        record = build_record(material, match, runset, head=head)
        results_text(record)  # refuses a value JSON cannot hold, before anything is written
    except (MatcherError, ValueError) as exc:
        raise MatchRefused(f"the matcher refused this sweep: {exc}") from exc
    counts = record["run_counts"]["by_final_status"]
    return MatchResult(
        record, path, counts, tuple(record["alternative_readings"]["unmatched_calls"])
    )


def results_text(record: dict[str, Any]) -> str:
    return json.dumps(record, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def write_match(result: MatchResult) -> Path:
    """The record's file, once: written beside it and linked into place, so an existing file (or a second
    command racing this one) is refused and never replaced."""
    path = result.path
    text = results_text(result.record)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    try:
        os.link(temporary, path)
    except FileExistsError as exc:
        raise MatchRefused(f"{path.name} exists: a case result is never overwritten") from exc
    finally:
        temporary.unlink(missing_ok=True)
    return path
