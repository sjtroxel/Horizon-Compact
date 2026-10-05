"""Render one run's prompt and build the one tool (Phase 1 IMPLEMENTATION doc section 5, planning/07 section
4).

The tool's schema is **identical on every run**: keys and the choice's enum in alphabetical order, generated
from ``scenario.toml``. The tool definition is part of the cached prefix, so a schema that changed per run
would defeat caching on every call. The shuffle lives only in the prompt text, which is where planning/07
section 4 puts it.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from typing import Any

from horizon_compact.experiment import Experiment, Lever, Objective, Option, Scenario
from horizon_compact.providers.base import ToolSpec

TOOL_NAME = "submit_decision"
TOOL_DESCRIPTION = "Submits the decision: the amounts, the choice and the memo."
AMOUNTS_DESCRIPTION = "Dollars for every source and use listed, keyed by the key in brackets."
MEMO_DESCRIPTION = "150 to 300 words explaining the decision."


@dataclass(frozen=True)
class RenderedPrompt:
    system: str
    user: str
    lever_order: tuple[str, ...]
    option_order: tuple[str, ...]


def menu_order_seed(sweep_seed: int, run_id: str) -> int:
    """The first 8 bytes, as an integer, of SHA-256 over the sweep seed and the run id."""
    digest = hashlib.sha256(f"{sweep_seed}|{run_id}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def build_tool(scenario: Scenario) -> ToolSpec:
    offered = sorted(lever.key for lever in scenario.offered())
    choice = scenario.choice
    schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "amounts": {
                "type": "object",
                "description": AMOUNTS_DESCRIPTION,
                "properties": {key: {"type": "number"} for key in offered},
                "required": offered,
                "additionalProperties": False,
            },
            choice.key: {"type": "string", "enum": sorted(o.key for o in choice.options)},
            "memo": {"type": "string", "description": MEMO_DESCRIPTION},
        },
        "required": sorted(["amounts", choice.key, "memo"]),
        "additionalProperties": False,
    }
    return ToolSpec(name=TOOL_NAME, description=TOOL_DESCRIPTION, input_schema=schema)


def _dollars(amount: int) -> str:
    return f"${amount:,}"


def _lever_line(lever: Lever) -> str:
    if lever.kind == "not_offered":
        return f"- {lever.label} [{lever.key}]: not offered this season"
    return f"- {lever.label} [{lever.key}]: {lever.kind}, up to {_dollars(lever.cap)}"


def _option_line(option: Option) -> str:
    return f"- {option.text} [{option.key}]"


def _priority_sentence(scenario: Scenario, objective: Objective) -> str:
    if not objective.wording:
        return scenario.no_priority
    return scenario.priority_frame.replace("{wording}", objective.wording)


def render_prompt(experiment: Experiment, objective: Objective, seed: int) -> RenderedPrompt:
    """One ``random.Random(seed)`` shuffles the levers, then the options, in that order."""
    scenario = experiment.scenario
    rng = random.Random(seed)
    levers = list(scenario.levers)
    rng.shuffle(levers)
    options = list(scenario.choice.options)
    rng.shuffle(options)

    system = "\n\n".join([scenario.role, experiment.dossier.text.strip(), scenario.currency_note])
    user = "\n\n".join(
        [
            scenario.scenario.strip(),
            _priority_sentence(scenario, objective),
            "\n".join([scenario.menu_heading, *(_lever_line(lever) for lever in levers)]),
            "\n".join([scenario.options_heading, *(_option_line(o) for o in options)]),
            scenario.instruction.strip(),
        ]
    )
    return RenderedPrompt(
        system=system,
        user=user,
        lever_order=tuple(lever.key for lever in levers),
        option_order=tuple(o.key for o in options),
    )
