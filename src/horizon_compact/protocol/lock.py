"""The pre-registration lock: write it, read it, and check the tree against it.

Phase 3.5 IMPLEMENTATION doc sections 5 and 6, build step 4.

``experiment/protocol/prereg.lock`` is TOML, written only by ``hc protocol lock --write`` and never by hand.
It records the protocol document's hash, the content hash and each content file's hash, the instrument and
analysis code sets and each file's hash, the identity of each official model, and a few record-only fields
(``tree_sha256``, ``uv_lock_sha256``, the simulation record) that prove where things came from and are never
compared.

``check_lock`` recomputes everything the lock holds and reports every difference, never only the first. With
no lock it passes and says so. A model's prices, quotas and pacing are not in the lock, so a price change
passes; its id, route, profile, role and region are, so a change to one fails. ``errata-v1.md`` is never
read.

The writer needs no TOML library: the lock is a few nested tables of strings and integers, and ``dumps``
writes them in sorted order so the same data is always the same bytes.
"""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from horizon_compact.analysis import RESULTS_VERSION
from horizon_compact.experiment import MODELS_FILE, ExperimentError, load_experiment
from horizon_compact.model_config import ModelConfig
from horizon_compact.protocol import sets
from horizon_compact.protocol.sets import SetError
from horizon_compact.providers.bedrock import REGION

LOCK_VERSION = 1
PROTOCOL = "prereg-v1"
EXPERIMENT = "company"
LOCK_RELATIVE = "experiment/protocol/prereg.lock"
DOCUMENT_RELATIVE = "experiment/protocol/protocol-v1.md"
UV_LOCK_RELATIVE = "uv.lock"
SIMULATION_RELATIVE = "docs/phases/evidence/phase-3/simulation-results.json"
EXPERIMENT_DIR = "experiment"

# What the harness sends when it sets neither (Phase 3.5 IMPLEMENTATION doc section 3, item 4). The sweep has
# no thinking option yet, so the writer records these for every model; a model that needs another value waits
# for the option (build step 9).
NOT_SET = "not set"
BEDROCK_ROUTES = frozenset({"in_region", "geo_profile", "application_profile"})

HEADER = (
    "# The pre-registration lock. Written by `hc protocol lock --write`; never edit it by hand.\n"
    "# Phase 3.5 IMPLEMENTATION doc section 6."
)


class LockError(Exception):
    """The lock cannot be written or read. ``reasons`` has one line for each cause."""

    def __init__(self, reasons: Sequence[str]) -> None:
        self.reasons = tuple(reasons)
        super().__init__("\n".join(self.reasons))


# --- the lock as data ---------------------------------------------------------------------------------------


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ContentRecord(_Strict):
    experiment: str
    content_hash: str
    files: dict[str, str]
    tree_sha256: str
    sealed_template: str | None = None


class InstrumentRecord(_Strict):
    sha256: str
    files: dict[str, str]


class AnalysisRecord(_Strict):
    sha256: str
    files: dict[str, str]
    results_version: int
    uv_lock_sha256: str


class SimulationRecord(_Strict):
    results_sha256: str
    code_sha256: str


class ModelIdentity(_Strict):
    model_id: str
    route: str
    role: str
    thinking: str
    sampling: str
    inference_profile: str | None = None
    geo_profile_id: str | None = None
    region: str | None = None


class Lock(_Strict):
    lock_version: int
    protocol: str
    document: str
    document_sha256: str
    content: ContentRecord
    instrument: InstrumentRecord
    analysis: AnalysisRecord
    simulation: SimulationRecord
    models: dict[str, ModelIdentity]


def lock_path(root: Path) -> Path:
    return root / LOCK_RELATIVE


def read_lock(path: Path) -> Lock:
    """Parse and validate a lock; every problem becomes a ``LockError`` naming the file."""
    name = path.name
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        raise LockError([f"{name} cannot be read: {type(exc).__name__}"]) from exc
    except tomllib.TOMLDecodeError as exc:
        raise LockError([f"{name} is not valid TOML: {exc}"]) from exc
    version = raw.get("lock_version")
    if version != LOCK_VERSION:
        raise LockError([f"{name} has lock_version {version!r}; this reader knows {LOCK_VERSION}"])
    try:
        return Lock.model_validate(raw)
    except ValidationError as exc:
        fields = "; ".join(
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in exc.errors()
        )
        raise LockError([f"{name} is malformed: {fields}"]) from exc


# --- writing ------------------------------------------------------------------------------------------------

_BARE_KEY = re.compile(r"[A-Za-z0-9_-]+")


def _key(key: str) -> str:
    return key if _BARE_KEY.fullmatch(key) else json.dumps(key)


def _value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value)
    raise TypeError(
        f"the lock writer takes strings, integers and booleans, not {type(value).__name__}"
    )


def _table(lines: list[str], path: tuple[str, ...], table: Mapping[str, Any]) -> None:
    scalars = sorted(k for k, v in table.items() if not isinstance(v, Mapping))
    tables = sorted(k for k, v in table.items() if isinstance(v, Mapping))
    if path and (scalars or not tables):
        lines.append("")
        lines.append(f"[{'.'.join(_key(part) for part in path)}]")
    lines.extend(f"{_key(k)} = {_value(table[k])}" for k in scalars)
    for k in tables:
        _table(lines, (*path, k), table[k])


def dumps(data: Mapping[str, Any]) -> str:
    """The lock's TOML: a header, then each table's scalars and sub-tables in sorted order, LF endings."""
    lines = [HEADER]
    first = len(lines)
    _table(lines, (), data)
    if len(lines) > first:
        lines.insert(first, "")
    return "\n".join(lines) + "\n"


def model_identity(config: ModelConfig) -> dict[str, str]:
    """The fields that decide which model answers and how it is asked; never a price, quota or pace."""
    record = {
        "model_id": config.model_id,
        "route": config.route,
        "role": config.role,
        "thinking": NOT_SET,
        "sampling": NOT_SET,
    }
    if config.inference_profile:
        record["inference_profile"] = config.inference_profile
    if config.geo_profile_id:
        record["geo_profile_id"] = config.geo_profile_id
    if config.route in BEDROCK_ROUTES:
        record["region"] = REGION
    return record


def _tree_sha256(root: Path, experiment: str) -> str:
    """The whole experiment folder, for the record. Filtered through git like the code sets, so a stranger
    recomputing it from a clean clone of the tag gets the same value."""
    under = f"{EXPERIMENT_DIR}/{experiment}"
    tracked = sets.tracked_files(root, under)
    on_disk = (
        path.relative_to(root).as_posix() for path in (root / under).rglob("*") if path.is_file()
    )
    paths = sorted(
        p for p in on_disk if not sets.is_bytecode(p) and (tracked is None or p in tracked)
    )
    return sets.set_sha256(root, paths)


def _file_sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_lock(
    root: Path, model_keys: Sequence[str], *, experiment: str = EXPERIMENT
) -> dict[str, Any]:
    """The lock's data for the tree under ``root`` and the named official models.

    Refuses, naming every cause, when a lock already exists, no model is named, the protocol document is
    missing, a model is not in ``models.toml``, a frozen pattern matches no file, or a record-only source
    (``uv.lock``, the simulation results) is missing.
    """
    keys = list(dict.fromkeys(model_keys))
    problems: list[str] = []
    if lock_path(root).exists():
        problems.append(
            f"{LOCK_RELATIVE} already exists: a lock is never overwritten, a new protocol version "
            "writes its own beside it"
        )
    if not keys:
        problems.append("no official model named: pass --model KEY once for each (never inferred)")
    document = root / DOCUMENT_RELATIVE
    if not document.is_file():
        problems.append(f"the protocol document {DOCUMENT_RELATIVE} does not exist")
    uv_lock = root / UV_LOCK_RELATIVE
    if not uv_lock.is_file():
        problems.append(f"{UV_LOCK_RELATIVE} does not exist")
    simulation = root / SIMULATION_RELATIVE
    simulation_code: str | None = None
    if not simulation.is_file():
        problems.append(f"the simulation results {SIMULATION_RELATIVE} do not exist")
    else:
        try:
            simulation_code = json.loads(simulation.read_text(encoding="utf-8"))["code_sha256"]
        except (OSError, ValueError, KeyError, TypeError):
            problems.append(f"{SIMULATION_RELATIVE} has no readable code_sha256")

    loaded = None
    try:
        loaded = load_experiment(experiment, root=root / EXPERIMENT_DIR)
    except ExperimentError as exc:
        problems.append(f"experiment {experiment!r} does not load: {exc}")
    if loaded is not None:
        known = loaded.models.models
        problems.extend(
            f"model {key!r} is not in {MODELS_FILE} (it has: {', '.join(sorted(known))})"
            for key in keys
            if key not in known
        )

    instrument: tuple[str, ...] = ()
    analysis: tuple[str, ...] = ()
    try:
        problems.extend(
            f"frozen pattern {pattern} matches no file" for pattern in sets.unmatched_patterns(root)
        )
        instrument = sets.list_set(root, "instrument")
        analysis = sets.list_set(root, "analysis")
    except SetError as exc:
        problems.append(str(exc))

    if problems or loaded is None or simulation_code is None:
        raise LockError(problems)

    content_files = {k: v for k, v in loaded.file_hashes.items() if k != MODELS_FILE}
    content: dict[str, Any] = {
        "experiment": experiment,
        "content_hash": loaded.content_hash,
        "files": content_files,
        "tree_sha256": _tree_sha256(root, experiment),
    }
    if loaded.sealed_template:
        content["sealed_template"] = loaded.sealed_template
    return {
        "lock_version": LOCK_VERSION,
        "protocol": PROTOCOL,
        "document": DOCUMENT_RELATIVE,
        "document_sha256": _file_sha256_of(document),
        "content": content,
        "instrument": {
            "sha256": sets.set_sha256(root, instrument),
            "files": {p: sets.file_sha256(root, p) for p in instrument},
        },
        "analysis": {
            "sha256": sets.set_sha256(root, analysis),
            "files": {p: sets.file_sha256(root, p) for p in analysis},
            "results_version": RESULTS_VERSION,
            "uv_lock_sha256": _file_sha256_of(uv_lock),
        },
        "simulation": {
            "results_sha256": _file_sha256_of(simulation),
            "code_sha256": simulation_code,
        },
        "models": {key: model_identity(loaded.models.models[key]) for key in keys},
    }


def render_lock(root: Path, model_keys: Sequence[str], *, experiment: str = EXPERIMENT) -> str:
    return dumps(build_lock(root, model_keys, experiment=experiment))


def write_lock(root: Path, model_keys: Sequence[str], *, experiment: str = EXPERIMENT) -> Path:
    """Write ``prereg.lock``; the file is created exclusively, so an existing lock can never be replaced."""
    text = render_lock(root, model_keys, experiment=experiment)
    path = lock_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    except FileExistsError as exc:
        raise LockError([f"{LOCK_RELATIVE} already exists"]) from exc
    return path


# --- checking -----------------------------------------------------------------------------------------------

LINE_ENDING_NOTE = (
    "if no frozen file was edited, check line endings: the lock hashes the bytes in git, which are LF, "
    "and a checkout with core.autocrlf=true hashes differently"
)


@dataclass(frozen=True)
class CheckReport:
    failures: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.failures


def _differences(
    kind: str, protocol: str, locked: Mapping[str, str], current: Mapping[str, str]
) -> list[str]:
    lines: list[str] = []
    for path in sorted(set(locked) | set(current)):
        if path not in current:
            lines.append(f"{kind} differs from {protocol}: {path} (missing)")
        elif path not in locked:
            lines.append(f"{kind} differs from {protocol}: {path} (added)")
        elif locked[path] != current[path]:
            lines.append(f"{kind} differs from {protocol}: {path}")
    return lines


def _unsafe(path: str) -> bool:
    pure = PurePosixPath(path)
    return pure.is_absolute() or ".." in pure.parts or "\\" in path


def _check_document(root: Path, lock: Lock) -> list[str]:
    if _unsafe(lock.document):
        return [f"the lock names an unsafe document path: {lock.document}"]
    document = root / lock.document
    if not document.is_file():
        return [f"document differs from {lock.protocol}: {lock.document} (missing)"]
    if _file_sha256_of(document) != lock.document_sha256:
        return [f"document differs from {lock.protocol}: {lock.document}"]
    return []


def _check_set(
    root: Path, lock: Lock, name: sets.SetName, locked_sha: str, locked_files: Mapping[str, str]
) -> list[str]:
    try:
        files = sets.list_set(root, name)
        current = {p: sets.file_sha256(root, p) for p in files}
        current_sha = sets.set_sha256(root, files)
    except (SetError, OSError) as exc:
        return [f"{name}: cannot be listed or read: {exc}"]
    lines = _differences(name, lock.protocol, locked_files, current)
    if not lines and current_sha != locked_sha:
        lines.append(f"{name} set hash differs from {lock.protocol}")
    return lines


def _check_content(root: Path, lock: Lock) -> list[str]:
    record = lock.content
    try:
        loaded = load_experiment(record.experiment, root=root / EXPERIMENT_DIR)
    except ExperimentError as exc:
        return [f"content: experiment {record.experiment!r} does not load: {exc}"]
    current = {k: v for k, v in loaded.file_hashes.items() if k != MODELS_FILE}
    lines = _differences("content", lock.protocol, record.files, current)
    if not lines and loaded.content_hash != record.content_hash:
        lines.append(f"content hash differs from {lock.protocol}")
    if loaded.sealed_template != record.sealed_template:
        lines.append(
            f"sealed template differs from {lock.protocol}: now {loaded.sealed_template!r}, "
            f"locked {record.sealed_template!r}"
        )
    for key, locked in sorted(lock.models.items()):
        config = loaded.models.models.get(key)
        if config is None:
            lines.append(f"model {key} is in {lock.protocol} but not in {MODELS_FILE}")
            continue
        now = model_identity(config)
        for field in ("model_id", "route", "role", "inference_profile", "geo_profile_id", "region"):
            if getattr(locked, field) != now.get(field):
                lines.append(
                    f"model {key} differs from {lock.protocol}: {field} is {now.get(field)!r}, "
                    f"locked {getattr(locked, field)!r}"
                )
    return lines


def check_lock(root: Path) -> CheckReport:
    """Compare the tree with the lock. Passes, with a note, when there is no lock yet."""
    path = lock_path(root)
    if not path.is_file():
        return CheckReport(notes=(f"no lock exists yet ({LOCK_RELATIVE}); nothing to check",))
    try:
        lock = read_lock(path)
    except LockError as exc:
        return CheckReport(failures=exc.reasons)
    failures = [
        *_check_document(root, lock),
        *_check_content(root, lock),
        *_check_set(root, lock, "instrument", lock.instrument.sha256, lock.instrument.files),
        *_check_set(root, lock, "analysis", lock.analysis.sha256, lock.analysis.files),
    ]
    hashed = any(
        line.startswith(("instrument", "analysis", "content", "document")) for line in failures
    )
    notes = (LINE_ENDING_NOTE,) if hashed else ()
    return CheckReport(failures=tuple(failures), notes=notes)
