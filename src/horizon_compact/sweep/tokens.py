"""What thinking cost, in tokens (Phase 4 runs half section 5.2; protocol 9.5).

``hc sweep tokens --sweep <grid> --vs <thinking>`` sets the thinking sub-study beside the grid's matching
cells: S1 on the sealed wording, each objective. Per cell, the mean output tokens of each sweep and their
difference, and the share of sub-study runs that had a thinking block.

**It reads token counts and block counts, never a decision.** Each run is read through ``_counts``, which
picks the cell's three identifying fields, the output token count and the thinking-block count out of the
run's final attempt and touches nothing else in it: not the validation, the tool calls, the text, the parsed
decision or the raw response. A test holds that (no such field is ever looked up by name in this file, and
canary values planted in them never reach the output). It is run at the reveal, not before: a cell is an
objective, and a token count by objective is still a view of the results.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from horizon_compact.providers.base import THINKING_LABEL
from horizon_compact.sweep.plan import SweepRefusal
from horizon_compact.sweep.runner import sweep_prefix
from horizon_compact.sweep.store import Store

GRID_LABEL = "grid"
_FINAL = re.compile(r"runs/(?P<run>r-[0-9a-f]{12})/final\.json$")


@dataclass(frozen=True)
class RunCounts:
    output_tokens: int
    thinking_blocks: int


def _counts(attempt: dict[str, Any]) -> tuple[str, str, str, RunCounts]:
    """The cell and the two counts of one attempt, and nothing else in it."""
    usage = attempt.get("usage") or {}
    return (
        str(attempt.get("scenario_id")),
        str(attempt.get("wording_variant_id")),
        str(attempt.get("objective_id")),
        RunCounts(
            output_tokens=int(usage.get("output_tokens") or 0),
            thinking_blocks=int(attempt.get("reasoning_block_count") or 0),
        ),
    )


def _manifest(store: Store, experiment: str, sweep_id: str, what: str) -> dict[str, Any]:
    text = store.get(f"{sweep_prefix(experiment, sweep_id, 'official')}manifest.json")
    if text is None:
        raise SweepRefusal(f"no official manifest for the {what} sweep {sweep_id!r}")
    manifest: dict[str, Any] = json.loads(text)
    return manifest


def read_cells(
    store: Store, experiment: str, sweep_id: str, scenario: str, template: str
) -> dict[str, list[RunCounts]]:
    """Per objective, the counts of the sweep's runs in one scenario and wording: each run's final attempt."""
    prefix = sweep_prefix(experiment, sweep_id, "official")
    cells: dict[str, list[RunCounts]] = {}
    for key in store.list_keys(f"{prefix}runs/"):
        match = _FINAL.search(key)
        if match is None:
            continue
        final = json.loads(store.get(key) or "{}")
        text = store.get(
            f"{prefix}runs/{match.group('run')}/attempt-{int(final['final_attempt'])}.json"
        )
        if text is None:
            raise SweepRefusal(f"run {match.group('run')} has a final.json but no final attempt")
        found_scenario, found_template, objective, counts = _counts(json.loads(text))
        if (found_scenario, found_template) == (scenario, template):
            cells.setdefault(objective, []).append(counts)
    return cells


def _mean(values: list[int]) -> float | None:
    return sum(values) / len(values) if values else None


def _fmt(value: float | None) -> str:
    return "none" if value is None else f"{value:.0f}"


def tokens_report(store: Store, experiment: str, grid_id: str, thinking_id: str) -> str:
    """The table, as text, for the grid ``grid_id`` and the sub-study ``thinking_id``. Refuses a pair that is
    not a grid and its thinking sub-study on one model, or a sub-study that is not one scenario on one
    wording."""
    grid = _manifest(store, experiment, grid_id, "grid")
    study = _manifest(store, experiment, thinking_id, "thinking")
    problems = []
    if grid.get("label") != GRID_LABEL:
        problems.append(f"--sweep is labeled {grid.get('label')!r}, not {GRID_LABEL!r}")
    if study.get("label") != THINKING_LABEL:
        problems.append(f"--vs is labeled {study.get('label')!r}, not {THINKING_LABEL!r}")
    if grid.get("model_key") != study.get("model_key"):
        problems.append(
            f"the models differ ({grid.get('model_key')!r}, {study.get('model_key')!r})"
        )
    scenarios, templates = study.get("scenarios") or [], study.get("templates") or []
    if len(scenarios) != 1 or len(templates) != 1:
        problems.append("the sub-study is not one scenario on one wording")
    if problems:
        raise SweepRefusal("; ".join(problems))
    scenario, template = scenarios[0], templates[0]
    base = read_cells(store, experiment, grid_id, scenario, template)
    with_thinking = read_cells(store, experiment, thinking_id, scenario, template)
    lines = [
        f"thinking against the grid, {scenario} on {template} ({grid['model_key']}); "
        f"grid {grid_id}, sub-study {thinking_id}",
        "",
        "| objective | grid runs | grid mean output tokens | study runs | study mean output tokens "
        "| difference | study runs with a thinking block |",
        "|---|---|---|---|---|---|---|",
    ]
    all_base: list[int] = []
    all_study: list[int] = []
    all_blocks = 0
    for objective in sorted(set(base) | set(with_thinking)):
        b = [c.output_tokens for c in base.get(objective, [])]
        s_runs = with_thinking.get(objective, [])
        s = [c.output_tokens for c in s_runs]
        blocks = sum(1 for c in s_runs if c.thinking_blocks > 0)
        all_base += b
        all_study += s
        all_blocks += blocks
        lines.append(_row(objective, b, s, blocks))
    lines.append(_row("all", all_base, all_study, all_blocks))
    return "\n".join(lines)


def _row(label: str, base: list[int], study: list[int], blocks: int) -> str:
    mean_base, mean_study = _mean(base), _mean(study)
    difference = None if mean_base is None or mean_study is None else mean_study - mean_base
    share = f"{blocks} of {len(study)}" if study else "none"
    return (
        f"| {label} | {len(base)} | {_fmt(mean_base)} | {len(study)} | {_fmt(mean_study)} "
        f"| {_fmt(difference)} | {share} |"
    )
