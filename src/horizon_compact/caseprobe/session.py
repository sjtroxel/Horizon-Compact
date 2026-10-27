"""The case session: how a frozen case's sweep is planned, checked and written (Phase 5.5 IMPLEMENTATION doc
§5.1, K1; closes CARRIED 2026-10-09).

``hc sweep launch --case`` and ``hc sweep run --case`` share ``prepare_case_sweep``. On the laptop (launch,
and a dry run) it proves the label is in ``freeze.json``, recomputes check 2 from the CI runs and the probe
objects, and runs the laptop half of the gate; the launch then writes the finding as ``order.json`` beside the
manifest, once, before the task starts. In the container it reads ``order.json`` back and runs the whole case
gate with the container required. Either way every reason is collected and the caller refuses with all of
them, before any call.

**Why ``order.json`` and not a manifest field.** Every session recomputes the manifest from the plan and
refuses unless it matches the stored one exactly, and the container cannot recompute check 2 (it has no
GitHub access). A resume's laptop recomputes the finding and refuses unless it equals the stored one.

**The container cannot read ``freeze.json``** (the image carries ``src/`` and ``experiment/``, not
``docs/``). The label-in-the-freeze check is the laptop's, and the container's guarantee is ``order.json``,
which only a launch that passed it writes.

**The assembled experiment.** A case's content is in the grid's own formats, so a temporary folder holding
``models.toml`` from the image and, under ``case-<label>/``, the case's ``dossier.toml``, the image's
``company/objectives.toml`` (its sha256 checked against the lock's, so the wordings and objectives are the
tag's) and the case's scenario loads through the frozen ``load_experiment`` unchanged. The prompt, the tool
and the classifier are then the grid's, as tagged.

**Where a case sweep writes.** ``cases/<label>/runs/<sweep_id>/`` and nowhere else (``sweep_prefix``), under
the record label ``case``. One sweep per case and model.
"""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
import tomllib
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from horizon_compact.caseprobe.freeze import EVIDENCE_DIR, FREEZE_FILE
from horizon_compact.caseprobe.github import GithubReadError
from horizon_compact.caseprobe.layout import runs_prefix
from horizon_compact.caseprobe.run import ProbeRefused, load_content
from horizon_compact.experiment import (
    EXPERIMENT_FILES,
    MODELS_FILE,
    SCENARIOS_DIR,
    Experiment,
    ExperimentError,
    load_experiment,
)
from horizon_compact.model_config import ModelsFile
from horizon_compact.protocol.cases import (
    CASE_REFUSED,
    CaseContent,
    CaseError,
    CaseRecord,
    CiRun,
    ProbeRecord,
    case_path,
    check_case_content,
    check_case_order,
    read_case,
    run_case_gate,
)
from horizon_compact.protocol.gate import check_lock_file, default_package_dir
from horizon_compact.protocol.lock import Lock
from horizon_compact.providers.base import THINKING_LABEL
from horizon_compact.sweep.identity import RunnerIdentity
from horizon_compact.sweep.plan import (
    SweepPlan,
    SweepRefusal,
    build_plan,
    preflight_bound_usd,
)
from horizon_compact.sweep.runner import CASE_EXPERIMENT_PREFIX
from horizon_compact.sweep.store import Store

CASE_LABEL = "case"  # the plan's label, and the role of every record the sweep writes
CASE_REPEATS = 10  # protocol §12.7
CASE_TEMPLATES = ("w1", "w2", "w3")
CASE_OBJECTIVES = 5
ORDER_FILE = "order.json"
OBJECTIVES_FILE = (
    "company/objectives.toml"  # under experiment/, and the key in the lock's content files
)
_SCENARIO_ID = re.compile(r"[a-z][a-z0-9_-]*")
_MANIFEST_KEY = re.compile(r"cases/[^/]+/runs/(?P<sweep>[^/]+)/manifest\.json")


@dataclass(frozen=True)
class CaseWorld:
    """What a case session reads from outside the repository: the results bucket, the probe records of a
    case, and (the laptop only) the CI runs that hold its record."""

    store: Store
    probes: Callable[[str], Sequence[ProbeRecord]]
    runs: Callable[[str], Sequence[CiRun]] | None = None


@dataclass(frozen=True)
class PreparedSweep:
    """Everything a case session checked. ``reasons`` is empty only when every check passed; the other fields
    are filled as far as the checks got, so a dry run can still show them."""

    label: str
    reasons: tuple[str, ...]
    notes: tuple[str, ...] = ()
    record: CaseRecord | None = None
    experiment: Experiment | None = None
    plan: SweepPlan | None = None
    finding: dict[str, Any] | None = None
    bound_usd: float | None = None

    @property
    def ok(self) -> bool:
        return not self.reasons

    def refusal(self) -> SweepRefusal:
        return SweepRefusal("\n".join(f"{CASE_REFUSED}: {line}" for line in self.reasons))


def case_experiment_name(label: str) -> str:
    return f"{CASE_EXPERIMENT_PREFIX}{label}"


def order_key(label: str, sweep_id: str) -> str:
    return f"{runs_prefix(label, sweep_id)}{ORDER_FILE}"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _dump(finding: dict[str, Any]) -> str:
    return json.dumps(finding, indent=2, sort_keys=True) + "\n"


# --- the laptop's check that the case is frozen -----------------------------------------------------------


def check_frozen(root: Path, label: str, record: CaseRecord) -> list[str]:
    """The label must be one of ``freeze.json``'s cases, and that entry's probe set the record's."""
    path = f"{EVIDENCE_DIR}/{FREEZE_FILE}"
    try:
        frozen = json.loads((root / path).read_text(encoding="utf-8"))
        entries = {str(entry["label"]): entry for entry in frozen["cases"]}
    except (OSError, ValueError, KeyError, TypeError):
        return [f"{path} cannot be read: a case sweep runs only a frozen case"]
    entry = entries.get(label)
    if entry is None:
        return [f"case {label} is not one of {path}'s frozen cases ({', '.join(sorted(entries))})"]
    if entry.get("probe_set") != record.probe_set:
        return [
            f"case {label}'s probe set is {entry.get('probe_set')!r} in {path} but "
            f"{record.probe_set} in {case_path(label)}"
        ]
    return []


# --- the assembled experiment -----------------------------------------------------------------------------


def _scenario_id(scenario: bytes) -> str:
    try:
        found = tomllib.loads(scenario.decode("utf-8")).get("id")
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise SweepRefusal(f"the case's scenario is not valid TOML: {type(exc).__name__}") from exc
    if not isinstance(found, str) or not _SCENARIO_ID.fullmatch(found):
        raise SweepRefusal("the case's scenario has no usable id (a short lower-case name)")
    return found


def assemble_experiment(root: Path, label: str, content: CaseContent, lock: Lock) -> Experiment:
    """The case as an experiment the frozen loader reads, in a folder that is gone once it has been read.
    The objectives file is the image's, refused unless it is the lock's."""
    try:
        objectives = (root / "experiment" / OBJECTIVES_FILE).read_bytes()
        models = (root / "experiment" / MODELS_FILE).read_bytes()
    except OSError as exc:
        raise SweepRefusal(f"cannot read the tagged files: {exc.strerror or exc}") from exc
    locked = lock.content.files.get(OBJECTIVES_FILE)
    if locked is None or _sha256(objectives) != locked:
        raise SweepRefusal(
            f"{OBJECTIVES_FILE} differs from {lock.protocol}'s: the objectives and wordings of a case "
            "sweep are the tag's"
        )
    scenario_id = _scenario_id(content.scenario)
    name = case_experiment_name(label)
    with tempfile.TemporaryDirectory(prefix="hc-case-") as temp:
        base = Path(temp)
        (base / MODELS_FILE).write_bytes(models)
        folder = base / name
        (folder / SCENARIOS_DIR).mkdir(parents=True)
        contents = {EXPERIMENT_FILES[0]: content.dossier, EXPERIMENT_FILES[1]: objectives}
        for filename, data in contents.items():
            (folder / filename).write_bytes(data)
        (folder / SCENARIOS_DIR / f"{scenario_id}.toml").write_bytes(content.scenario)
        return load_experiment(name, base)


def _models(root: Path) -> ModelsFile:
    try:
        raw = tomllib.loads((root / "experiment" / MODELS_FILE).read_text(encoding="utf-8"))
        return ModelsFile.model_validate(raw)
    except (OSError, tomllib.TOMLDecodeError, ValidationError) as exc:
        raise SweepRefusal(f"cannot read {MODELS_FILE}: {type(exc).__name__}") from exc


# --- the plan ---------------------------------------------------------------------------------------------


def build_case_plan(
    experiment: Experiment,
    model_key: str,
    seed: int,
    *,
    label: str = CASE_LABEL,
    repeats: int = CASE_REPEATS,
    scenarios: Sequence[str] | None = None,
    templates: Sequence[str] | None = None,
) -> SweepPlan:
    """The case's plan, official and labeled ``case``. The thinking sub-study's label is refused here, before
    the planner would build it; every other difference is ``check_case_plan``'s."""
    if label != CASE_LABEL:
        raise SweepRefusal(
            f"a case sweep's label is {CASE_LABEL!r}, not {label!r} "
            f"({THINKING_LABEL!r} is the sub-study's and never runs on a case)"
        )
    return build_plan(
        experiment,
        model_key=model_key,
        label=label,
        repeats=repeats,
        seed=seed,
        scenarios=scenarios,
        templates=templates,
        official=True,
    )


def check_case_plan(experiment: Experiment, plan: SweepPlan) -> list[str]:
    """The shape protocol §12.7 fixes: the case's one scenario, every objective, templates ``w1`` to ``w3``,
    exactly 10 repeats. Each difference is named."""
    lines: list[str] = []
    if plan.label != CASE_LABEL:
        lines.append(f"the plan's label is {plan.label!r}, not {CASE_LABEL!r}")
    if plan.experiment != experiment.name or not plan.experiment.startswith(CASE_EXPERIMENT_PREFIX):
        lines.append(f"the plan is for {plan.experiment!r}, not a case's experiment")
    if plan.scenarios != tuple(experiment.scenarios) or len(plan.scenarios) != 1:
        lines.append(
            f"the plan runs scenarios {list(plan.scenarios)}; a case sweep runs its one scenario "
            f"{list(experiment.scenarios)}"
        )
    if plan.templates != CASE_TEMPLATES:
        lines.append(
            f"the plan runs templates {list(plan.templates)}; a case sweep runs {list(CASE_TEMPLATES)}"
        )
    off = {sid: n for sid, n in plan.repeats.items() if n != CASE_REPEATS}
    if off:
        lines.append(f"the plan has repeats {off}; a case sweep has exactly {CASE_REPEATS} a cell")
    if len(experiment.objectives) != CASE_OBJECTIVES:
        lines.append(
            f"the experiment has {len(experiment.objectives)} objectives; a case sweep runs "
            f"{CASE_OBJECTIVES}"
        )
    wanted = CASE_OBJECTIVES * len(CASE_TEMPLATES) * CASE_REPEATS
    if len(plan.runs) != wanted:
        lines.append(f"the plan has {len(plan.runs)} runs, not {wanted}")
    return lines


# --- one sweep per case per model, and the order record ---------------------------------------------------


def check_one_sweep_per_case(store: Store, label: str, model_key: str, sweep_id: str) -> list[str]:
    """No other sweep of this model under the case. A resume of the same sweep id is not another. A manifest
    that cannot be read fails closed: it may be the other sweep."""
    others: list[str] = []
    unreadable: list[str] = []
    for key in store.list_keys(runs_prefix(label)):
        match = _MANIFEST_KEY.fullmatch(key)
        if match is None or match["sweep"] == sweep_id:
            continue
        try:
            manifest = json.loads(store.get(key) or "")
        except ValueError:
            unreadable.append(match["sweep"])
            continue
        if isinstance(manifest, dict) and manifest.get("model_key") == model_key:
            others.append(match["sweep"])
    lines = []
    if others:
        lines.append(
            f"case {label} already has a sweep for {model_key} ({', '.join(others)}): one sweep per case "
            "and model, never a second under another seed"
        )
    if unreadable:
        lines.append(
            f"case {label} has a manifest that cannot be read ({', '.join(unreadable)}), which may be "
            f"another sweep for {model_key}"
        )
    return lines


def write_order(store: Store, label: str, sweep_id: str, finding: dict[str, Any]) -> None:
    """The laptop's record of check 2, write-once before the first task. A resume finds it there and must
    recompute the same finding."""
    key = order_key(label, sweep_id)
    if store.put_new(key, _dump(finding)):
        return
    stored = store.get(key)
    if stored is None or _loads(stored) != finding:
        raise SweepRefusal(
            f"the order finding stored for {sweep_id} differs from the one recomputed now: refusing to resume"
        )


def _loads(text: str) -> Any:
    try:
        return json.loads(text)
    except ValueError:
        return None


# --- the whole preparation --------------------------------------------------------------------------------


def prepare_case_sweep(
    label: str,
    model_key: str,
    seed: int,
    *,
    world: CaseWorld,
    identity: RunnerIdentity,
    container: bool,
    cap_usd: float,
    repeats: int = CASE_REPEATS,
    scenarios: Sequence[str] | None = None,
    templates: Sequence[str] | None = None,
    plan_label: str = CASE_LABEL,
    why: str = "launch",
    package_dir: Path | None = None,
) -> PreparedSweep:
    """Every check of a case session, every reason collected. ``container`` is the container's session
    (check 2 read from ``order.json``, the container required, no freeze file); otherwise the laptop's
    (check 2 recomputed, compared with any stored finding, the container only noted).

    Nothing is written. A reason ends only the checks that need what it found missing.
    """
    package = package_dir or default_package_dir()
    root = package.parents[1]
    try:
        runs_prefix(label)
        record = read_case(root, label)
    except (CaseError, ValueError) as exc:
        return PreparedSweep(label, (str(exc),))
    reasons: list[str] = [] if container else check_frozen(root, label, record)
    try:
        models = _models(root)
    except SweepRefusal as exc:
        return PreparedSweep(label, (*reasons, str(exc)), record=record)

    content: CaseContent | None = None
    try:
        content = load_content(world.store, label, record.probe_set)
    except ProbeRefused as exc:
        reasons.append(str(exc))
    probes = list(world.probes(label))

    experiment: Experiment | None = None
    plan: SweepPlan | None = None
    lock, _ = check_lock_file(root)  # its problems are the gate's to report, once
    if content is not None and lock is not None and not check_case_content(record, content):
        try:
            experiment = assemble_experiment(root, label, content, lock)
            plan = build_case_plan(
                experiment,
                model_key,
                seed,
                label=plan_label,
                repeats=repeats,
                scenarios=scenarios,
                templates=templates,
            )
            reasons += check_case_plan(experiment, plan)
        except (SweepRefusal, ExperimentError) as exc:
            reasons.append(str(exc))
            plan = None

    finding: dict[str, Any] | None = None
    stored = world.store.get(order_key(label, plan.sweep_id)) if plan is not None else None
    if container:
        finding = _loads(stored) if stored is not None else None
        if stored is not None and not isinstance(finding, dict):
            reasons.append(f"{ORDER_FILE} for case {label} is not a record")
            finding = None
    elif world.runs is None:
        reasons.append("the laptop's session has no CI runs to check the order against")
    else:
        try:
            finding = check_case_order(record, world.runs(label), probes).as_record()
        except GithubReadError as exc:
            reasons.append(f"cannot read the CI runs: {exc}")
        if finding is not None and stored is not None and _loads(stored) != finding:
            reasons.append(
                f"the order finding stored for {plan.sweep_id if plan else label} differs from the one "
                "recomputed now: refusing to resume"
            )

    if content is not None:
        result = run_case_gate(
            label,
            content,
            probes,
            finding,
            models,
            model_key,
            identity,
            require_container=container,
            why=why,
            package_dir=package,
        )
        reasons += result.failures
        notes = result.notes
    else:
        notes = ()

    bound: float | None = None
    if experiment is not None and plan is not None:
        bound = preflight_bound_usd(experiment, plan)
        if bound > cap_usd:
            reasons.append(
                f"the worst case for {len(plan.runs)} runs is ${bound:.2f}, above the cap of "
                f"${cap_usd:.2f}; raise the cap with --cap-usd (above $5 also needs --allow-over-cap)"
            )
        reasons += check_one_sweep_per_case(world.store, label, model_key, plan.sweep_id)
    return PreparedSweep(
        label,
        tuple(dict.fromkeys(reasons)),
        tuple(notes),
        record=record,
        experiment=experiment,
        plan=plan,
        finding=finding,
        bound_usd=bound,
    )
