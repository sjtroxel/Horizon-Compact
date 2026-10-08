"""Run records into typed rows, one per run (Phase 3 IMPLEMENTATION doc sections 2 item 1 and 6, decision 8).

The reader takes the objects ``sweep/runner.py`` writes (``manifest.json``, ``runs/<run>/attempt-N.json`` and
``runs/<run>/final.json``) from anything with ``get`` and ``list_keys``. It **refuses** any record under
``development/`` whose experiment is not the placeholder: the Phase 2.5 format runs sit there, and both honor
statements in that phase say no allocation by objective was seen. Running this engine on them would show
exactly that, so the rule is code, not memory. Official, pilot and placeholder records are read; nothing else.

The amounts a row carries are the ones that count as the decision: the scaled amounts when the run is
``valid_rescaled``, otherwise the raw ones (``planning/07`` section 2.4 item 3). A run that is not valid has
none.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from horizon_compact.experiment import PLACEHOLDER_EXPERIMENT

# What the runner writes; test_analysis_records checks these against sweep/classify.py so they cannot drift.
VALID_STATUSES = frozenset({"valid", "valid_rescaled"})
NON_MODEL_STATUSES = frozenset({"api_error", "config_error"})
DEVELOPMENT_PREFIX = "development/"

_RUN_KEY = re.compile(
    r"runs/(?P<run>r-[0-9a-f]{12})/(?:attempt-(?P<n>\d+)|(?P<final>final))\.json$"
)


class RecordRefusal(Exception):
    """The reader will not read these records. The message says why."""


class RecordSource(Protocol):
    """The two calls the reader needs. ``sweep.store.Store`` has both; this package may not import it."""

    def get(self, key: str) -> str | None: ...

    def list_keys(self, prefix: str) -> list[str]: ...


@dataclass(frozen=True)
class RunRow:
    run_id: str
    sweep_id: str
    model_key: str
    scenario_id: str
    objective_id: str
    wording_id: str
    repeat: int
    status: str  # the run's final status
    first_attempt_status: str
    attempts: int  # model attempts, not counting api_error or config_error
    possible_decline: (
        bool  # the final attempt's flag: a candidate for a human call, never a decision
    )
    menu_order: tuple[str, ...]
    option_order: tuple[str, ...]
    # The decision as counted: scaled amounts for valid_rescaled, else the raw amounts. None unless valid.
    amounts: Mapping[str, float] | None
    choice: str | None
    # The first attempt's decision on the same terms; None unless the first attempt was valid.
    first_amounts: Mapping[str, float] | None
    first_choice: str | None

    @property
    def valid(self) -> bool:
        return self.status in VALID_STATUSES


@dataclass(frozen=True)
class RunSet:
    rows: tuple[RunRow, ...]
    # Runs in the manifest with no final.json yet: not analysed, and listed so no one forgets them.
    unfinished: tuple[str, ...]


def check_readable(key: str) -> None:
    """Refuse a key under ``development/`` whose experiment is not the placeholder (decision 8)."""
    cleaned = key.lstrip("/")
    if cleaned.startswith(DEVELOPMENT_PREFIX) or cleaned == DEVELOPMENT_PREFIX.rstrip("/"):
        parts = cleaned.split("/")
        experiment = parts[1] if len(parts) > 1 else ""
        if experiment != PLACEHOLDER_EXPERIMENT:
            raise RecordRefusal(
                f"refusing to read {key!r}: records under development/ are read only for the "
                f"{PLACEHOLDER_EXPERIMENT} experiment. Development runs on real content were seen for "
                "format only, and both Phase 2.5 honor statements say no allocation by objective was "
                "seen; analysing them would show it. Official, pilot and placeholder records only."
            )


def _decision(validation: Mapping[str, Any] | None, status: str) -> dict[str, float] | None:
    if status not in VALID_STATUSES:
        return None
    if validation is None:
        raise RecordRefusal(f"an attempt with status {status} has no validation object")
    scaled = validation.get("scaled_amounts") if status == "valid_rescaled" else None
    chosen = scaled if scaled is not None else validation.get("amounts")
    if not isinstance(chosen, dict) or not chosen:
        raise RecordRefusal(f"an attempt with status {status} has no amounts")
    return {str(key): float(value) for key, value in chosen.items()}


def _load(source: RecordSource, key: str) -> dict[str, Any]:
    text = source.get(key)
    if text is None:
        raise RecordRefusal(f"{key} was listed but cannot be read")
    loaded = json.loads(text)
    if not isinstance(loaded, dict):
        raise RecordRefusal(f"{key} is not a JSON object")
    return loaded


def read_runs(source: RecordSource, prefix: str) -> RunSet:
    """Every finished run under ``prefix`` (one sweep: ``.../<sweep_id>/``) as a ``RunRow``."""
    check_readable(prefix)
    prefix = prefix if prefix.endswith("/") or not prefix else prefix + "/"
    keys = source.list_keys(prefix)
    for key in keys:
        check_readable(key)

    manifest_text = source.get(f"{prefix}manifest.json")
    if manifest_text is None:
        raise RecordRefusal(
            f"no manifest.json under {prefix!r}; the repeat of each run is read from it"
        )
    manifest = json.loads(manifest_text)
    planned = {run["run_id"]: run for run in manifest["runs"]}

    finals: dict[str, dict[str, Any]] = {}
    attempts: dict[str, dict[int, dict[str, Any]]] = {}
    for key in keys:
        match = _RUN_KEY.search(key)
        if match is None:
            continue
        run_id = match.group("run")
        if run_id not in planned:
            raise RecordRefusal(f"{key} belongs to a run that is not in the manifest")
        if match.group("final"):
            finals[run_id] = _load(source, key)
        else:
            attempts.setdefault(run_id, {})[int(match.group("n"))] = _load(source, key)

    rows: list[RunRow] = []
    for run_id in sorted(finals):
        rows.append(_row(manifest, planned[run_id], finals[run_id], attempts.get(run_id, {})))
    unfinished = tuple(sorted(set(planned) - set(finals)))
    return RunSet(tuple(rows), unfinished)


def _row(
    manifest: Mapping[str, Any],
    planned: Mapping[str, Any],
    final: Mapping[str, Any],
    attempts: Mapping[int, Mapping[str, Any]],
) -> RunRow:
    run_id = str(planned["run_id"])
    model_attempts = [
        attempts[n] for n in sorted(attempts) if attempts[n]["status"] not in NON_MODEL_STATUSES
    ]
    if not model_attempts:
        raise RecordRefusal(f"run {run_id} has a final.json and no model attempt")
    first, last = model_attempts[0], model_attempts[-1]
    if int(last["attempt"]) != int(final["final_attempt"]) or last["status"] != final["status"]:
        raise RecordRefusal(
            f"run {run_id}: final.json says {final['status']} at attempt {final['final_attempt']}, "
            f"but its last model attempt is {last['status']} at attempt {last['attempt']}"
        )
    if first["status"] != final["first_attempt_status"]:
        raise RecordRefusal(
            f"run {run_id}: final.json and attempt records disagree on the first attempt"
        )
    for attempt in (first, last):
        if attempt["scenario_id"] != planned["scenario_id"] or (
            attempt["objective_id"] != planned["objective_id"]
        ):
            raise RecordRefusal(
                f"run {run_id}: an attempt disagrees with the manifest on scenario or objective"
            )

    def choice_of(attempt: Mapping[str, Any]) -> str | None:
        validation = attempt.get("validation")
        return (
            validation.get("choice") if attempt["status"] in VALID_STATUSES and validation else None
        )

    return RunRow(
        run_id=run_id,
        sweep_id=str(manifest["sweep_id"]),
        model_key=str(manifest["model_key"]),
        scenario_id=str(planned["scenario_id"]),
        objective_id=str(planned["objective_id"]),
        wording_id=str(planned["wording_id"]),
        repeat=int(planned["repeat"]),
        status=str(final["status"]),
        first_attempt_status=str(final["first_attempt_status"]),
        attempts=len(model_attempts),
        possible_decline=bool(last.get("possible_decline", False)),
        menu_order=tuple(last["menu_order"]),
        option_order=tuple(last["option_order"]),
        amounts=_decision(last.get("validation"), str(last["status"])),
        choice=choice_of(last),
        first_amounts=_decision(first.get("validation"), str(first["status"])),
        first_choice=choice_of(first),
    )
