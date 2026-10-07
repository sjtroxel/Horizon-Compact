"""Render one run's prompt and build the one tool (Phase 1 IMPLEMENTATION doc section 5, planning/07 section
4).

The tool's schema is **identical on every run**: keys and the choice's enum in alphabetical order, generated
from the scenario's file. The tool definition is part of the cached prefix, so a schema that changed per run
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
    template_id: str


def menu_order_seed(sweep_seed: int, run_id: str) -> int:
    """The first 8 bytes, as an integer, of SHA-256 over the sweep seed and the run id."""
    digest = hashlib.sha256(f"{sweep_seed}|{run_id}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def build_tool(scenario: Scenario) -> ToolSpec:
    offered = sorted(lever.key for lever in scenario.offered())
    amount_type = "integer" if scenario.unit == "people" else "number"
    # The key order is the cached prefix's: amounts, the choice (if any), then the memo.
    properties: dict[str, Any] = {
        "amounts": {
            "type": "object",
            "description": AMOUNTS_DESCRIPTION,
            "properties": {key: {"type": amount_type} for key in offered},
            "required": offered,
            "additionalProperties": False,
        }
    }
    required = ["amounts", "memo"]
    if scenario.choice is not None:
        properties[scenario.choice.key] = {
            "type": "string",
            "enum": sorted(o.key for o in scenario.choice.options),
        }
        required.append(scenario.choice.key)
    properties["memo"] = {"type": "string", "description": MEMO_DESCRIPTION}
    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "required": sorted(required),
        "additionalProperties": False,
    }
    return ToolSpec(name=TOOL_NAME, description=TOOL_DESCRIPTION, input_schema=schema)


def _dollars(amount: int) -> str:
    return f"${amount:,}"


def _lever_line(lever: Lever, unit: str) -> str:
    if lever.kind == "not_offered":
        return f"- {lever.label} [{lever.key}]: {lever.note or 'not offered'}"
    cap = f"{lever.cap:,} people" if unit == "people" else _dollars(lever.cap)
    return f"- {lever.label} [{lever.key}]: {lever.kind}, up to {cap}"


def _option_line(option: Option) -> str:
    return f"- {option.text} [{option.key}]"


def render_prompt(
    experiment: Experiment,
    scenario: Scenario,
    objective: Objective,
    template_id: str,
    seed: int,
) -> RenderedPrompt:
    """One ``random.Random(seed)`` shuffles the levers, then the options, in that order."""
    rng = random.Random(seed)
    levers = list(scenario.levers)
    rng.shuffle(levers)
    options = list(scenario.choice.options) if scenario.choice else []
    rng.shuffle(options)

    system = "\n\n".join([scenario.role, experiment.dossier.text.strip(), scenario.currency_note])
    parts = [
        scenario.scenario.strip(),
        experiment.wording_sentence(objective, template_id),
        "\n".join(
            [scenario.menu_heading, *(_lever_line(lever, scenario.unit) for lever in levers)]
        ),
    ]
    if scenario.choice is not None:
        parts.append("\n".join([scenario.options_heading, *(_option_line(o) for o in options)]))
    parts.append(scenario.instruction.strip())
    return RenderedPrompt(
        system=system,
        user="\n\n".join(parts),
        lever_order=tuple(lever.key for lever in levers),
        option_order=tuple(o.key for o in options),
        template_id=template_id,
    )
