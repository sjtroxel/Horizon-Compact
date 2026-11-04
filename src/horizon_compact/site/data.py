"""The site-data builder: one placeholder sweep to one versioned JSON file (Phase 1.5 IMPLEMENTATION doc
section 6, decided points of section 18).

The page reads this file and nothing else. The builder is a pure function from the records to the file's exact
text, so the same records give the same bytes, and a second build can be compared with ``cmp``.

It is not the scorer. The frozen analysis engine refuses the placeholder (it has no sealed template and no
outcomes), so this module computes only counts, per-run values, means and ranges. It reuses the frozen record
reader, ``analysis.records.read_runs``, and changes nothing frozen.

**What it can read is fixed in code.** The prefix is ``development/placeholder/<sweep_id>/`` and nothing else:
the experiment must be the placeholder, and the sweep id must be a plain name, so no argument can move the
prefix. It takes a ``RecordSource`` (``get`` and ``list_keys``), never a ``Store``, so it cannot write to the
bucket by construction. Standard library only.

**What it never copies:** the two fields that hold an account id (``image``, ``task_arn``), the request id,
and anything the model wrote or returned (the parsed decision, the tool calls, the raw response, the request,
the text blocks, the memo and its word count). No memo text appears in any form.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

from horizon_compact.analysis.records import RecordRefusal, RecordSource, RunRow, read_runs
from horizon_compact.experiment import PLACEHOLDER_EXPERIMENT, Experiment, ExperimentError

SCHEMA = "horizon-compact/site-placeholder"
SCHEMA_VERSION = 1
ROLE = "development"

_SWEEP_ID = re.compile(r"[a-z0-9][a-z0-9-]*")
_RUN_KEY = re.compile(
    r"runs/(?P<run>r-[0-9a-f]{12})/(?:attempt-(?P<n>\d+)|(?P<final>final))\.json$"
)
# A bare twelve-digit run would match inside a 64-character hex digest about one time in five, so the number
# must stand alone: no letter or digit on either side.
_ACCOUNT_ID = re.compile(r"(?<![0-9A-Za-z])\d{12}(?![0-9A-Za-z])")

# Fields a run's final attempt must carry for the page to trace a number back to its image and commit.
_PROVENANCE = (
    "image_digest",
    "git_sha",
    "content_hash",
    "provider_details.served_model",
    "runner",
    "started_at",
    "finished_at",
)


class SiteDataRefusal(Exception):
    """The builder or the writer will not produce this file. The message says why."""


def _prefix(sweep_id: str) -> str:
    return f"{ROLE}/{PLACEHOLDER_EXPERIMENT}/{sweep_id}/"


def _fetch(source: RecordSource, key: str) -> dict[str, Any]:
    text = source.get(key)
    if text is None:
        raise SiteDataRefusal(f"{key} was listed but cannot be read")
    loaded = json.loads(text)
    if not isinstance(loaded, dict):
        raise SiteDataRefusal(f"{key} is not a JSON object")
    return loaded


def _field(attempt: Mapping[str, Any], dotted: str) -> Any:
    value: Any = attempt
    for part in dotted.split("."):
        if not isinstance(value, Mapping):
            return None
        value = value.get(part)
    return value


def _missing(attempt: Mapping[str, Any]) -> list[str]:
    return [
        name
        for name in _PROVENANCE
        if not isinstance(_field(attempt, name), str) or not _field(attempt, name)
    ]


def _counts(values: list[str]) -> dict[str, int]:
    return {key: values.count(key) for key in sorted(set(values))}


def _instant(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise SiteDataRefusal(f"{value!r} is not a timestamp") from exc


def _read_attempts(
    source: RecordSource, prefix: str
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[int, dict[str, Any]]]]:
    finals: dict[str, dict[str, Any]] = {}
    attempts: dict[str, dict[int, dict[str, Any]]] = {}
    for key in source.list_keys(prefix):
        match = _RUN_KEY.search(key)
        if match is None:
            continue
        run_id = match.group("run")
        if match.group("final"):
            finals[run_id] = _fetch(source, key)
        else:
            attempts.setdefault(run_id, {})[int(match.group("n"))] = _fetch(source, key)
    return finals, attempts


def _session_cost(source: RecordSource, prefix: str, sweep_id: str) -> float:
    keys = [k for k in source.list_keys(f"{prefix}sessions/") if k.endswith(".json")]
    if not keys:
        raise SiteDataRefusal(f"no session summary under {prefix}sessions/, so the cost is unknown")
    costs: list[float] = []
    for key in sorted(keys):
        session = _fetch(source, key)
        if session.get("sweep_id") != sweep_id:
            raise SiteDataRefusal(
                f"{key} belongs to sweep {session.get('sweep_id')!r}, not {sweep_id!r}"
            )
        cost = session.get("cost_usd_this_session")
        if isinstance(cost, bool) or not isinstance(cost, int | float):
            raise SiteDataRefusal(f"{key} has no cost_usd_this_session")
        costs.append(float(cost))
    return round(math.fsum(costs), 6)


def build_site_data(source: RecordSource, sweep_id: str, experiment: Experiment) -> str:
    """The exact text of the site's data file for one finished placeholder sweep."""
    if experiment.name != PLACEHOLDER_EXPERIMENT:
        raise SiteDataRefusal(
            f"the site shows the {PLACEHOLDER_EXPERIMENT} experiment only; this is {experiment.name!r}"
        )
    if not _SWEEP_ID.fullmatch(sweep_id):
        raise SiteDataRefusal(f"sweep id {sweep_id!r} is not a plain lower-case name")
    prefix = _prefix(sweep_id)
    try:
        runset = read_runs(source, prefix)
    except RecordRefusal as exc:
        raise SiteDataRefusal(str(exc)) from exc

    manifest = _fetch(source, f"{prefix}manifest.json")
    if manifest.get("experiment") != PLACEHOLDER_EXPERIMENT:
        raise SiteDataRefusal(f"the manifest's experiment is {manifest.get('experiment')!r}")
    if manifest.get("sweep_id") != sweep_id:
        raise SiteDataRefusal(
            f"the manifest's sweep id is {manifest.get('sweep_id')!r}, not {sweep_id!r}"
        )
    if runset.unfinished:
        raise SiteDataRefusal(
            f"{len(runset.unfinished)} run(s) are unfinished (first: {runset.unfinished[0]}); "
            "the sweep must finish before it is shown"
        )
    rows = list(runset.rows)
    if not rows:
        raise SiteDataRefusal("the sweep has no runs")

    scenario = experiment.scenario
    if scenario.choice is None:
        raise SiteDataRefusal("the page shows one choice, and the scenario has none")
    line_keys = [lever.key for lever in scenario.offered()]
    option_keys = [option.key for option in scenario.choice.options]
    objective_ids = [objective.id for objective in experiment.objectives]
    for row in rows:
        if row.scenario_id != scenario.id:
            raise SiteDataRefusal(
                f"run {row.run_id} is on scenario {row.scenario_id!r}, not {scenario.id!r}"
            )
        if row.objective_id not in objective_ids:
            raise SiteDataRefusal(
                f"run {row.run_id} has objective {row.objective_id!r}, not in the experiment"
            )
        if row.valid:
            if row.amounts is None or set(row.amounts) != set(line_keys):
                raise SiteDataRefusal(
                    f"run {row.run_id}'s amounts do not match the scenario's lines"
                )
            if row.choice not in option_keys:
                raise SiteDataRefusal(f"run {row.run_id}'s choice {row.choice!r} is not an option")

    finals, attempts = _read_attempts(source, prefix)
    final_attempt: dict[str, dict[str, Any]] = {}
    for row in rows:
        number = int(finals[row.run_id]["final_attempt"])
        record = attempts.get(row.run_id, {}).get(number)
        if record is None:
            raise SiteDataRefusal(f"run {row.run_id} has no attempt-{number}.json")
        missing = _missing(record)
        if missing:
            raise SiteDataRefusal(f"run {row.run_id}'s final attempt lacks {', '.join(missing)}")
        final_attempt[row.run_id] = record

    # Content drift: the page shows the scenario and the sentences as the experiment folder holds them now,
    # so the records must have been made from the same files.
    wanted = {
        k: v
        for k, v in experiment.file_hashes.items()
        if k.startswith(f"{PLACEHOLDER_EXPERIMENT}/")
    }
    for row in rows:
        record = final_attempt[row.run_id]
        if record["content_hash"] != experiment.content_hash:
            raise SiteDataRefusal(
                f"run {row.run_id} was made from content {record['content_hash'][:12]}..., and "
                f"experiment/{PLACEHOLDER_EXPERIMENT}/ now hashes to {experiment.content_hash[:12]}...; "
                "the page would show text the model was not given"
            )
        held = record.get("file_hashes")
        held = held if isinstance(held, Mapping) else {}
        drifted = sorted(k for k, v in wanted.items() if held.get(k) != v)
        if drifted:
            raise SiteDataRefusal(f"run {row.run_id}: file hash differs for {', '.join(drifted)}")

    cost = _session_cost(source, prefix, sweep_id)

    template_ids: dict[str, str] = {}
    for objective_id in objective_ids:
        ids = sorted({r.wording_id for r in rows if r.objective_id == objective_id})
        if not ids:
            raise SiteDataRefusal(f"objective {objective_id!r} has no runs in this sweep")
        if len(ids) > 1:
            raise SiteDataRefusal(
                f"objective {objective_id!r} used more than one wording: {', '.join(ids)}"
            )
        template_ids[objective_id] = ids[0]

    objectives: list[dict[str, Any]] = []
    for objective in experiment.objectives:
        try:
            sentence = experiment.wording_sentence(objective, template_ids[objective.id])
        except ExperimentError as exc:
            raise SiteDataRefusal(str(exc)) from exc
        objectives.append(
            {"id": objective.id, "template_id": template_ids[objective.id], "sentence": sentence}
        )

    every_attempt = [a for per_run in attempts.values() for a in per_run.values()]
    started = [str(a["started_at"]) for a in every_attempt if a.get("started_at")]
    finished = [str(a["finished_at"]) for a in every_attempt if a.get("finished_at")]
    finals_in_order = [final_attempt[r.run_id] for r in sorted(rows, key=lambda r: r.run_id)]

    def distinct(name: str) -> list[str]:
        return sorted({str(_field(a, name)) for a in finals_in_order})

    sweep = {
        "sweep_id": sweep_id,
        "experiment": PLACEHOLDER_EXPERIMENT,
        "role": ROLE,
        "model_key": str(manifest["model_key"]),
        "served_models": distinct("provider_details.served_model"),
        "runs_planned": len(manifest["runs"]),
        "runs_finished": len(rows),
        "status_counts": _counts([r.status for r in rows]),
        "first_attempt_status_counts": _counts([r.first_attempt_status for r in rows]),
        "cost_usd": cost,
        "image_digests": distinct("image_digest"),
        "git_shas": distinct("git_sha"),
        "content_hashes": distinct("content_hash"),
        "runners": distinct("runner"),
        "started_at": min(started, key=_instant),
        "finished_at": max(finished, key=_instant),
    }

    scenario_block = {
        "id": scenario.id,
        "total": scenario.total,
        "lines": [
            {"key": lever.key, "label": lever.label, "kind": lever.kind, "cap": lever.cap}
            for lever in scenario.offered()
        ],
        "not_offered": [
            {"key": lever.key, "label": lever.label, "note": lever.note}
            for lever in scenario.levers
            if lever.kind == "not_offered"
        ],
        "choice": {
            "key": scenario.choice.key,
            "label": scenario.choice.label,
            "options": [{"key": o.key, "text": o.text} for o in scenario.choice.options],
        },
    }

    cells = [_cell(objective_id, rows, line_keys, option_keys) for objective_id in objective_ids]
    runs = [
        _run(row, final_attempt[row.run_id], line_keys)
        for row in sorted(rows, key=lambda r: r.run_id)
    ]

    document = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "kind": "test-run",
        "content": PLACEHOLDER_EXPERIMENT,
        "sweep": sweep,
        "scenario": scenario_block,
        "objectives": objectives,
        "cells": cells,
        "runs": runs,
    }
    text = json.dumps(document, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if "arn:" in text or _ACCOUNT_ID.search(text):
        raise SiteDataRefusal(
            "the output looks like it holds an account id or an ARN; it was not produced"
        )
    return text


def _cell(
    objective_id: str, rows: list[RunRow], line_keys: list[str], option_keys: list[str]
) -> dict[str, Any]:
    mine = [r for r in rows if r.objective_id == objective_id]
    valid = [r for r in mine if r.valid]
    lines: dict[str, dict[str, float | None]] = {}
    for key in line_keys:
        values = [r.amounts[key] for r in valid if r.amounts is not None]
        lines[key] = (
            {"mean": math.fsum(values) / len(values), "min": min(values), "max": max(values)}
            if values
            else {"mean": None, "min": None, "max": None}
        )
    return {
        "objective_id": objective_id,
        "runs": len(mine),
        "valid": len(valid),
        "status_counts": _counts([r.status for r in mine]),
        "first_attempt_status_counts": _counts([r.first_attempt_status for r in mine]),
        "lines": lines,
        "choice_counts": {key: sum(1 for r in valid if r.choice == key) for key in option_keys},
    }


def _run(row: RunRow, final: Mapping[str, Any], line_keys: list[str]) -> dict[str, Any]:
    return {
        "run_id": row.run_id,
        "objective_id": row.objective_id,
        "wording_id": row.wording_id,
        "repeat": row.repeat,
        "status": row.status,
        "first_attempt_status": row.first_attempt_status,
        "attempts": row.attempts,
        "amounts": None if row.amounts is None else {key: row.amounts[key] for key in line_keys},
        "choice": row.choice,
        "image_digest": final["image_digest"],
        "git_sha": final["git_sha"],
        "content_hash": final["content_hash"],
        "served_model": _field(final, "provider_details.served_model"),
        "runner": final["runner"],
        "finished_at": final["finished_at"],
    }


def write_site_data(text: str, path: Path) -> Path:
    """Write the file once. The same bytes again is a no-op; different bytes are refused, never overwritten
    (replacing the file means deleting it on purpose first). Returns the path; committing is the author's."""
    data = text.encode("utf-8")
    if path.exists():
        if path.read_bytes() == data:
            return path
        raise SiteDataRefusal(
            f"{path} already holds different data; delete it on purpose to replace it"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")  # the same bytes on every platform
    temporary.replace(path)
    return path
