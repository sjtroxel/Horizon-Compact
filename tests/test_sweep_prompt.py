"""Prompts and the tool (Phase 1 IMPLEMENTATION doc sections 3 and 5, and the placeholder rule)."""

from __future__ import annotations

import json
import re

from horizon_compact.providers.base import DecisionRequest
from horizon_compact.providers.bedrock import build_request
from horizon_compact.sweep.prompt import TOOL_NAME, build_tool, render_prompt
from sweep_helpers import NOVA_ROUTE, experiment, make_plan

# The Phase 0.5 smoke list plus the words the placeholder must never lean on (Phase 1 IMPLEMENTATION doc,
# section 13).
SUBJECT_WORDS = (
    "company",
    "shareholder",
    "stakeholder",
    "employee",
    "worker",
    "invest",
    "capital",
    "objective",
    "profit",
    "budget",
    "allocate",
    "quarter",
    "horizon",
    "board",
    "business",
    "firm",
    "owner",
    "staff",
    "wage",
    "dividend",
    "market",
    "stock",
    "future",
    "decade",
    "long-term",
    "short-term",
    "chief executive",
)


def _runs() -> list[tuple[str, str, tuple[str, ...], tuple[str, ...]]]:
    exp, plan = make_plan(repeats=3)
    objectives = {o.id: o for o in exp.objectives}
    out = []
    for run in plan.runs:
        p = render_prompt(exp, objectives[run.objective_id], run.menu_order_seed)
        out.append((p.system, p.user, p.lever_order, p.option_order))
    return out


def test_the_tool_schema_is_byte_identical_on_every_run() -> None:
    """A per-run schema would change the cached prefix and defeat caching on every call (finding 1)."""
    exp, plan = make_plan(repeats=3)
    objectives = {o.id: o for o in exp.objectives}
    tools = set()
    for run in plan.runs:
        p = render_prompt(exp, objectives[run.objective_id], run.menu_order_seed)
        request = DecisionRequest(NOVA_ROUTE, p.system, p.user, build_tool(exp.scenario), 2048)
        tools.add(json.dumps(build_request(request)["toolConfig"], sort_keys=False))
    assert len(tools) == 1


def test_the_tool_is_generated_with_sorted_keys_and_no_not_offered_lever() -> None:
    tool = build_tool(experiment().scenario)
    assert tool.name == TOOL_NAME
    amounts = tool.input_schema["properties"]["amounts"]
    keys = list(amounts["properties"])
    assert keys == sorted(keys)
    assert "tool_shed" not in keys
    assert amounts["required"] == keys
    assert tool.input_schema["properties"]["open_day_season"]["enum"] == ["autumn", "spring"]
    assert tool.input_schema["required"] == ["amounts", "memo", "open_day_season"]
    assert amounts["additionalProperties"] is False
    assert "minimum" not in json.dumps(
        tool.input_schema
    )  # validation is the harness's, not the schema's


def test_levers_and_options_appear_in_the_runs_order() -> None:
    for _system, user, lever_order, option_order in _runs():
        assert tuple(re.findall(r"\[(\w+)\]: (?:source|use|not offered)", user)) == lever_order
        assert tuple(re.findall(r"\[(autumn|spring)\]", user)) == option_order


def test_the_canonical_order_is_not_what_most_runs_show() -> None:
    exp = experiment()
    canonical = tuple(lever.key for lever in exp.scenario.levers)
    orders = {lever_order for _s, _u, lever_order, _o in _runs()}
    assert canonical not in orders or len(orders) > 1
    assert len(orders) > 10  # fifteen runs, fifteen different shuffles (almost surely)
    assert all(sorted(o) == sorted(canonical) for o in orders)  # all eight, every time


def test_the_same_seed_gives_the_same_prompt() -> None:
    exp = experiment()
    objective = exp.objectives[0]
    assert render_prompt(exp, objective, 99) == render_prompt(exp, objective, 99)
    assert render_prompt(exp, objective, 99).user != render_prompt(exp, objective, 100).user


def test_the_priority_sentence_follows_the_objective_and_the_baseline_states_none() -> None:
    exp = experiment()
    by_id = {o.id: o for o in exp.objectives}
    assert (
        "has set your priority: make the garden as colorful as possible."
        in render_prompt(exp, by_id["color"], 1).user
    )
    assert "The club committee has not set a priority." in render_prompt(exp, by_id["none"], 1).user
    assert "{wording}" not in render_prompt(exp, by_id["none"], 1).user


def test_the_cache_point_sits_after_the_dossier_and_only_when_asked() -> None:
    exp = experiment()
    p = render_prompt(exp, exp.objectives[0], 1)
    asked = build_request(
        DecisionRequest(
            NOVA_ROUTE, p.system, p.user, build_tool(exp.scenario), 2048, cache_system=True
        )
    )
    assert asked["system"][1] == {"cachePoint": {"type": "default"}}
    assert "HOLLIN STREET COMMUNITY GARDEN" in asked["system"][0]["text"]
    plain = build_request(
        DecisionRequest(NOVA_ROUTE, p.system, p.user, build_tool(exp.scenario), 2048)
    )
    assert plain["system"] == [{"text": p.system}]


def test_every_rendered_prompt_stays_off_the_experiments_subject() -> None:
    """The placeholder rule: no word from the subject's vocabulary in any system, user or tool text."""
    exp = experiment()
    tool = json.dumps(build_tool(exp.scenario).input_schema) + build_tool(exp.scenario).description
    hits = set()
    for system, user, _l, _o in _runs():
        text = (system + "\n" + user + "\n" + tool).lower()
        hits |= {w for w in SUBJECT_WORDS if re.search(rf"\b{re.escape(w)}\b", text)}
    assert not hits, f"subject vocabulary in a rendered placeholder prompt: {sorted(hits)}"


def test_no_sampling_parameter_is_ever_sent() -> None:
    exp = experiment()
    p = render_prompt(exp, exp.objectives[0], 1)
    body = build_request(
        DecisionRequest(
            NOVA_ROUTE, p.system, p.user, build_tool(exp.scenario), 2048, cache_system=True
        )
    )
    assert set(body["inferenceConfig"]) == {"maxTokens"}
    assert "additionalModelRequestFields" not in body


def test_no_string_in_any_placeholder_file_uses_the_subjects_vocabulary() -> None:
    """The file headers name the forbidden words in comments; the values and TOML keys are what a prompt can
    carry."""
    import tomllib

    def strings(node: object) -> list[str]:
        if isinstance(node, str):
            return [node]
        if isinstance(node, dict):
            return [s for value in node.values() for s in strings(value)]
        if isinstance(node, list):
            return [s for value in node for s in strings(value)]
        return []

    folder = experiment().root / "placeholder"
    hits: dict[str, list[str]] = {}
    for path in sorted(folder.glob("*.toml")):
        text = "\n".join(strings(tomllib.loads(path.read_text(encoding="utf-8")))).lower()
        found = [w for w in SUBJECT_WORDS if re.search(rf"\b{re.escape(w)}\b", text)]
        if found:
            hits[path.name] = found
    assert not hits, f"subject vocabulary in placeholder values: {hits}"
