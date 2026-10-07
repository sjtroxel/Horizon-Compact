"""The placeholder's prompts and tool stay byte for byte what they were before the Phase 2.5 layout change
(Phase 2.5 IMPLEMENTATION doc section 8.1).

``golden/placeholder_prompts.json`` holds SHA-256 digests taken from the code as it was at ``4250ea3``, before
the loader, the objectives file and the scenario folder changed shape. If a digest differs, the migration
changed what the placeholder says, which it must not: its sweeps and records stay comparable.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from horizon_compact.sweep.prompt import build_tool, render_prompt
from sweep_helpers import experiment

GOLDEN = json.loads(
    (Path(__file__).parent / "golden" / "placeholder_prompts.json").read_text(encoding="utf-8")
)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_every_golden_prompt_is_byte_identical() -> None:
    exp = experiment()
    scenario = exp.scenario
    objectives = {o.id: o for o in exp.objectives}
    assert len(GOLDEN["prompts"]) == 15
    for key, expected in GOLDEN["prompts"].items():
        objective_id, seed = key.split("|")
        p = render_prompt(exp, scenario, objectives[objective_id], "w1", int(seed))
        assert _sha(p.system) == expected["system_sha256"], key
        assert _sha(p.user) == expected["user_sha256"], key
        assert list(p.lever_order) == expected["lever_order"], key
        assert list(p.option_order) == expected["option_order"], key


def test_the_tool_is_byte_identical() -> None:
    tool = build_tool(experiment().scenario)
    assert tool.name == GOLDEN["tool"]["name"]
    assert tool.description == GOLDEN["tool"]["description"]
    assert _sha(json.dumps(tool.input_schema)) == GOLDEN["tool"]["schema_sha256"]
