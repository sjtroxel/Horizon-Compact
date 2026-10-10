"""The official-sweep gate and the repeat count (Phase 3.5 IMPLEMENTATION doc section 7, build step 5).

**The gate.** An official sweep runs only when every check passes. Each check is a function returning its
failures (an empty list when it passes); ``run_gate`` runs them all and reports them together, never only
the first:

1. the lock exists and parses, with a known ``lock_version``;
2. the protocol document's hash is the lock's;
3. the experiment is the lock's and its content files and content hash are the lock's;
4. the sealed template is the lock's, and the plan uses it (a pilot is the exception: it never does);
5. the instrument set is the lock's, naming each file that differs;
6. the analysis set is the lock's, the same way;
7. the plan's model is one of the lock's, with the same identity in ``models.toml``;
8. the sweep runs in the container, with an image digest.

**What the gate hashes is what runs.** The repository root is taken from the package that is running
(``horizon_compact.__file__``; the project is installed editable, in the image too), and the experiment must
have been loaded from that root's ``experiment/``. A sweep cannot pass the gate on one tree and run another.

**The pilot** (Phase 4 Delivers 1) runs the tagged content on an official model with the two development
wordings only. Check 4 as first written ("the plan uses the sealed template") would refuse it, so a pilot is
checked the other way: labeled ``pilot`` and never including the sealed template. ``--pilot`` on ``hc sweep
run`` and ``launch`` runs it and writes under the ``pilot/`` prefix (Phase 4 code half, section 4.3).

**The repeat count** (section 7.4, decision 9). ``required_repeats`` reads a pilot's records and applies the
frozen rule in ``analysis/repeats.py``. That module needs scipy, which the container image leaves out, so it
is imported inside the function, never at module level: the gate itself must load in the container.

**``repeats.json``** (Phase 4 code half, sections 4.3 and 4.4). ``write_repeats`` puts the decision beside the
pilot's records, once. ``check_repeats`` is what an official launch and an official run both call: the plan's
counts must equal the file's, scenario by scenario, so a hand-typed command cannot skip the pilot.
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import horizon_compact
from horizon_compact.experiment import MODELS_FILE, Experiment, ExperimentError
from horizon_compact.protocol.lock import (
    EXPERIMENT_DIR,
    LINE_ENDING_NOTE,
    LOCK_RELATIVE,
    Lock,
    LockError,
    check_document,
    check_set,
    differences,
    identity_differences,
    lock_path,
    read_lock,
)
from horizon_compact.sweep.identity import RunnerIdentity
from horizon_compact.sweep.plan import SweepPlan, SweepRefusal, repeats_from_json
from horizon_compact.sweep.runner import sweep_prefix
from horizon_compact.sweep.store import Store

if TYPE_CHECKING:
    from horizon_compact.analysis.records import RecordSource
    from horizon_compact.analysis.repeats import ChoiceRepeats, ShareRepeats

PILOT_LABEL = "pilot"
PILOT_REPEATS = 2  # protocol 8.1: two repeats a cell
REFUSED = "official sweep refused"
REPEATS_FILE = "repeats.json"


@dataclass(frozen=True)
class GateResult:
    failures: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.failures


# --- the checks, one function each -------------------------------------------------------------------------


def check_lock_file(root: Path) -> tuple[Lock | None, list[str]]:
    """Check 1. Without a readable lock, checks 2-7 cannot run; the container check still does."""
    path = lock_path(root)
    if not path.is_file():
        return None, [
            f"no committed protocol: {LOCK_RELATIVE} does not exist (prereg-v1 is not tagged)"
        ]
    try:
        return read_lock(path), []
    except LockError as exc:
        return None, list(exc.reasons)


def check_experiment_folder(root: Path, experiment: Experiment) -> list[str]:
    expected = (root / EXPERIMENT_DIR).resolve()
    if experiment.root.resolve() != expected:
        return [
            f"the experiment was loaded from {experiment.root}, not from {expected}: the gate hashes the "
            "code that runs, so the content must come from the same tree"
        ]
    return []


def check_content(experiment: Experiment, lock: Lock) -> list[str]:
    """Check 3, on the experiment the sweep will run, not on a fresh read of the disk."""
    locked = lock.content
    if experiment.name != locked.experiment:
        return [f"experiment is {experiment.name!r}; {lock.protocol} locks {locked.experiment!r}"]
    current = {k: v for k, v in experiment.file_hashes.items() if k != MODELS_FILE}
    lines = differences("content", lock.protocol, locked.files, current)
    if not lines and experiment.content_hash != locked.content_hash:
        lines.append(f"content hash differs from {lock.protocol}")
    return lines


def check_sealed_template(
    experiment: Experiment, plan: SweepPlan, lock: Lock, *, pilot: bool = False
) -> list[str]:
    """Check 4. The grid includes the sealed template; a pilot is labeled pilot and never includes it."""
    locked = lock.content.sealed_template
    if experiment.sealed_template != locked:
        return [
            f"sealed template differs from {lock.protocol}: now {experiment.sealed_template!r}, "
            f"locked {locked!r}"
        ]
    if not locked:
        return [f"{lock.protocol} locks no sealed template, and an official sweep needs one"]
    if pilot:
        lines = []
        if plan.label != PILOT_LABEL:
            lines.append(f"a pilot is labeled {PILOT_LABEL!r}, not {plan.label!r}")
        if locked in plan.templates:
            lines.append(
                f"a pilot never runs the sealed template ({locked}): the development wordings only"
            )
        return lines
    if plan.label == PILOT_LABEL:
        return [f"the label {PILOT_LABEL!r} is the pilot's, and this plan is not run as a pilot"]
    if locked not in plan.templates:
        return [
            f"the plan leaves out the sealed template ({locked}), which the official grid includes"
        ]
    return []


def check_pilot_shape(experiment: Experiment, plan: SweepPlan, lock: Lock) -> list[str]:
    """Check 4, pilot mode, continued: the shape protocol 8.1 fixes. Every scenario, every development wording
    (the sealed one's absence is ``check_sealed_template``'s), two repeats a cell. A pilot in any other shape
    would set the repeats from a different measurement than the one pre-registered."""
    lines: list[str] = []
    missing = [s for s in experiment.scenarios if s not in plan.scenarios]
    if missing:
        lines.append(f"a pilot runs every scenario; this one leaves out {missing}")
    sealed = lock.content.sealed_template
    wordings = [t for t in experiment.templates if t != sealed and t not in plan.templates]
    if wordings:
        lines.append(f"a pilot runs every development wording; this one leaves out {wordings}")
    off = {sid: n for sid, n in plan.repeats.items() if n != PILOT_REPEATS}
    if off:
        lines.append(f"a pilot runs {PILOT_REPEATS} repeats a cell; this one has {off}")
    return lines


def check_instrument(root: Path, lock: Lock) -> list[str]:
    """Check 5."""
    return check_set(root, lock, "instrument", lock.instrument.sha256, lock.instrument.files)


def check_analysis(root: Path, lock: Lock) -> list[str]:
    """Check 6. The sweep does not run the analysis; a changed scoring file is a tripwire (scope DoD 4)."""
    return check_set(root, lock, "analysis", lock.analysis.sha256, lock.analysis.files)


def check_model(experiment: Experiment, plan: SweepPlan, lock: Lock) -> list[str]:
    """Check 7. The model's identity, never its prices, quotas or pace."""
    key = plan.model_key
    locked = lock.models.get(key)
    if locked is None:
        return [
            f"model {key} is not one of {lock.protocol}'s models ({', '.join(sorted(lock.models))})"
        ]
    config = experiment.models.models.get(key)
    if config is None:
        return [f"model {key} is in {lock.protocol} but not in {MODELS_FILE}"]
    return identity_differences(key, locked, config, lock.protocol)


def check_container(
    identity: RunnerIdentity, *, required: bool, why: str
) -> tuple[list[str], list[str]]:
    """Check 8. Returns (failures, notes): where the container is not required yet, a note says so."""
    if identity.in_container:
        return [], []
    if required:
        return ["official sweeps run only in the container, never on a laptop"], []
    return [], [f"not in the container ({why})"]


# --- the gate ----------------------------------------------------------------------------------------------


def default_package_dir() -> Path:
    return Path(horizon_compact.__file__).resolve().parent


def run_gate(
    experiment: Experiment,
    plan: SweepPlan,
    identity: RunnerIdentity,
    *,
    require_container: bool = True,
    why: str = "dry run",
    pilot: bool = False,
    package_dir: Path | None = None,
) -> GateResult:
    """Every check, every failure. ``require_container=False`` is the dry run and the launch preflight:
    check 8 becomes a note, and the verdict is on checks 1-7."""
    root = (package_dir or default_package_dir()).parents[1]
    failures: list[str] = []
    lock, problems = check_lock_file(root)
    failures += problems
    if lock is not None:
        failures += check_experiment_folder(root, experiment)
        failures += check_document(root, lock)
        failures += check_content(experiment, lock)
        failures += check_sealed_template(experiment, plan, lock, pilot=pilot)
        if pilot:
            failures += check_pilot_shape(experiment, plan, lock)
        failures += check_instrument(root, lock)
        failures += check_analysis(root, lock)
        failures += check_model(experiment, plan, lock)
    container_failures, notes = check_container(identity, required=require_container, why=why)
    failures += container_failures
    hashed = ("document differs", "content differs", "content hash", "instrument", "analysis")
    if any(line.startswith(hashed) for line in failures):
        notes.append(LINE_ENDING_NOTE)
    return GateResult(tuple(failures), tuple(notes))


def refusal_message(result: GateResult) -> str:
    return "\n".join(f"{REFUSED}: {line}" for line in result.failures)


def check_official(
    experiment: Experiment,
    plan: SweepPlan,
    identity: RunnerIdentity,
    *,
    pilot: bool = False,
    package_dir: Path | None = None,
) -> GateResult:
    """The gate a real official session passes: every check, the container required. Raises on any failure."""
    result = run_gate(experiment, plan, identity, pilot=pilot, package_dir=package_dir)
    if not result.ok:
        raise SweepRefusal(refusal_message(result))
    return result


# --- the repeat count --------------------------------------------------------------------------------------


class PilotRefusal(Exception):
    """The repeat count cannot be computed from these records. The message says why."""


@dataclass(frozen=True)
class RepeatDecision:
    """What the pilot set: per scenario, the rule's inputs and outputs, and nothing that shows a direction (no
    mean, no difference, no objective)."""

    protocol: str
    pilot_sweep_id: str
    model_key: str
    content_hash: str
    run_ids: tuple[str, ...]
    scenarios: tuple[ShareRepeats | ChoiceRepeats, ...]

    def repeats(self) -> dict[str, int]:
        return {result.scenario_id: result.repeats for result in self.scenarios}

    def as_record(self) -> dict[str, Any]:
        """The body of ``repeats.json``: written once beside the pilot, recomputable by anyone."""
        return {
            "protocol": self.protocol,
            "pilot_sweep_id": self.pilot_sweep_id,
            "model_key": self.model_key,
            "content_hash": self.content_hash,
            "run_ids": list(self.run_ids),
            "scenarios": [
                {"kind": type(result).__name__, **dataclasses.asdict(result)}
                for result in self.scenarios
            ],
        }


def _pilot_problems(manifest: dict[str, Any], experiment: Experiment, lock: Lock) -> list[str]:
    locked = lock.content
    problems: list[str] = []
    if manifest.get("label") != PILOT_LABEL:
        problems.append(f"the manifest's label is {manifest.get('label')!r}, not {PILOT_LABEL!r}")
    if manifest.get("experiment") != locked.experiment:
        problems.append(
            f"the pilot ran experiment {manifest.get('experiment')!r}; {lock.protocol} locks "
            f"{locked.experiment!r}"
        )
    if manifest.get("content_hash") != locked.content_hash:
        problems.append(f"the pilot's content hash is not {lock.protocol}'s")
    if experiment.name != locked.experiment or experiment.content_hash != locked.content_hash:
        problems.append(f"the experiment given is not {lock.protocol}'s content")
    if manifest.get("model_key") not in lock.models:
        problems.append(
            f"the pilot's model {manifest.get('model_key')!r} is not one of {lock.protocol}'s"
        )
    if locked.sealed_template and locked.sealed_template in manifest.get("templates", []):
        problems.append(f"the pilot ran the sealed template ({locked.sealed_template})")
    return problems


def required_repeats(
    source: RecordSource, prefix: str, experiment: Experiment, lock: Lock
) -> RepeatDecision:
    """The repeats per scenario from a finished pilot, by the frozen rule.

    Refuses a manifest that does not say pilot, content that is not the lock's, a model outside the lock,
    the sealed template, and an unfinished run.
    """
    from horizon_compact.analysis.outcomes import OutcomeError, outcomes_for
    from horizon_compact.analysis.records import RecordRefusal, read_runs
    from horizon_compact.analysis.repeats import RepeatRuleError, repeats_for_pilot

    prefix = prefix if prefix.endswith("/") else prefix + "/"
    text = source.get(f"{prefix}manifest.json")
    if text is None:
        raise PilotRefusal(f"no manifest.json under {prefix!r}")
    manifest = json.loads(text)
    problems = _pilot_problems(manifest, experiment, lock)
    if problems:
        raise PilotRefusal("; ".join(problems))
    try:
        runs = read_runs(source, prefix)
    except RecordRefusal as exc:
        raise PilotRefusal(str(exc)) from exc
    if runs.unfinished:
        raise PilotRefusal(
            f"the pilot has {len(runs.unfinished)} unfinished runs; the count is set from a finished pilot"
        )
    if not runs.rows:
        raise PilotRefusal("the pilot has no finished runs")
    try:
        outcomes = [outcomes_for(experiment.get_scenario(sid)) for sid in manifest["scenarios"]]
        results = repeats_for_pilot(outcomes, runs.rows)
    except (OutcomeError, RepeatRuleError, ExperimentError, KeyError) as exc:
        raise PilotRefusal(f"the rule cannot be applied: {exc}") from exc
    return RepeatDecision(
        protocol=lock.protocol,
        pilot_sweep_id=str(manifest["sweep_id"]),
        model_key=str(manifest["model_key"]),
        content_hash=str(manifest["content_hash"]),
        run_ids=tuple(row.run_id for row in runs.rows),
        scenarios=results,
    )


# --- repeats.json: written once beside the pilot, checked at every official launch and run ------------------


def repeats_key(pilot_prefix: str) -> str:
    return (pilot_prefix if pilot_prefix.endswith("/") else pilot_prefix + "/") + REPEATS_FILE


def _experiment_pilots(pilot_prefix: str) -> str:
    """``pilot/<experiment>/`` from ``pilot/<experiment>/<sweep_id>/``."""
    return pilot_prefix.rstrip("/").rsplit("/", 1)[0] + "/"


def repeats_files_for_model(store: Store, pilots_prefix: str, model_key: str) -> list[str]:
    """Every ``repeats.json`` under ``pilot/<experiment>/`` written for ``model_key``, sorted. Protocol 13.2:
    a study runs once per protocol version, so there is at most one."""
    found = []
    for key in store.list_keys(pilots_prefix):
        if not key.endswith("/" + REPEATS_FILE):
            continue
        text = store.get(key)
        try:
            model = json.loads(text).get("model_key") if text else None
        except ValueError:
            model = None
        if model == model_key:
            found.append(key)
    return sorted(found)


def write_repeats(store: Store, pilot_prefix: str, decision: RepeatDecision) -> str:
    """Write ``repeats.json`` beside the pilot's records. Once: a second write is refused, never an overwrite.
    One pilot per model: a ``repeats.json`` from another pilot on the same model is refused too, so an
    official sweep never has two counts to choose between. Returns the key."""
    key = repeats_key(pilot_prefix)
    others = [
        k
        for k in repeats_files_for_model(
            store, _experiment_pilots(pilot_prefix), decision.model_key
        )
        if k != key
    ]
    if others:
        raise PilotRefusal(
            f"{decision.model_key} already has its repeats from another pilot ({others[0]}): one pilot per "
            "model per protocol version (protocol 13.2)"
        )
    text = json.dumps(decision.as_record(), indent=2, sort_keys=True) + "\n"
    if not store.put_new(key, text):
        raise PilotRefusal(
            f"{key} already exists: the repeat count is written once, and an existing one is never replaced"
        )
    return key


def describe_decision(decision: RepeatDecision) -> list[str]:
    """What the record holds, for the person who set it off: per scenario the pooled spread, the count and the
    rule that set it. No mean, no difference, no objective (the record has none to show)."""
    from horizon_compact.analysis.repeats import CAP, FLOOR, ShareRepeats

    lines = [
        f"pilot sweep {decision.pilot_sweep_id} ({decision.model_key}), {len(decision.run_ids)} runs, "
        f"protocol {decision.protocol}"
    ]
    for result in decision.scenarios:
        if isinstance(result, ShareRepeats):
            if result.cap_binds:
                rule = f"the cap, {CAP}"
            elif max(result.n_power, result.n_both_reachable) < FLOOR:
                rule = f"the floor, {FLOOR}"
            elif result.n_both_reachable >= result.n_power:
                rule = "rule (b), both verdicts reachable"
            else:
                rule = "rule (a), power"
            tail = (
                f"; half-width at the cap {result.achieved_half_width:.4f}"
                if result.achieved_half_width is not None
                else ""
            )
            lines.append(
                f"  {result.scenario_id}: pooled spread {result.pooled_sd:.4f} on "
                f"{result.degrees_of_freedom} degrees of freedom; (a) needs {result.n_power}, "
                f"(b) needs {result.n_both_reachable}; repeats {result.repeats}, set by {rule}{tail}"
            )
        else:
            lines.append(
                f"  {result.scenario_id}: repeats {result.repeats}, the cap (a pilot cannot measure a "
                f"choice rate); half-width at a true rate of 50% {result.half_width_at_50:.4f}, "
                f"of 5% {result.half_width_at_5:.4f}"
            )
    return lines


def check_repeats(store: Store, plan: SweepPlan, pilot_sweep_id: str) -> None:
    """Refuse unless the pilot's ``repeats.json`` exists, is for this model and this content, and holds
    exactly the plan's count for every scenario (protocol 8.3). Raises ``SweepRefusal`` naming each
    difference."""
    pilot_prefix = sweep_prefix(plan.experiment, pilot_sweep_id, "pilot")
    key = repeats_key(pilot_prefix)
    text = store.get(key)
    if text is None:
        raise SweepRefusal(
            f"{REFUSED}: no {key}: the pilot sets the repeats (`hc protocol repeats --pilot "
            f"{pilot_sweep_id}`), and an official sweep needs them"
        )
    try:
        record = json.loads(text)
        counts = repeats_from_json(record)
    except (ValueError, SweepRefusal) as exc:
        raise SweepRefusal(f"{REFUSED}: {key} is not a readable repeats record: {exc}") from exc
    problems: list[str] = []
    if record.get("pilot_sweep_id") != pilot_sweep_id:
        problems.append(
            f"the record is for pilot {record.get('pilot_sweep_id')!r}, not {pilot_sweep_id!r}"
        )
    if record.get("model_key") != plan.model_key:
        problems.append(
            f"the pilot ran {record.get('model_key')!r}, and this sweep is {plan.model_key!r}"
        )
    if record.get("content_hash") != plan.content_hash:
        problems.append("the pilot ran different content from this sweep")
    others = [
        k
        for k in repeats_files_for_model(store, _experiment_pilots(pilot_prefix), plan.model_key)
        if k != key
    ]
    if others:
        problems.append(
            f"{plan.model_key} has repeats from more than one pilot ({', '.join(others)} as well): one pilot "
            "per model per protocol version"
        )
    for scenario_id in plan.scenarios:
        want, have = counts.get(scenario_id), plan.repeats[scenario_id]
        if want != have:
            problems.append(
                f"scenario {scenario_id}: the pilot sets {want} repeats, the plan has {have}"
            )
    extra = sorted(set(counts) - set(plan.scenarios))
    if extra:
        problems.append(
            f"the pilot sets repeats for scenario(s) {extra} that this plan does not run"
        )
    if problems:
        raise SweepRefusal("\n".join(f"{REFUSED}: {line}" for line in problems))
