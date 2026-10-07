"""Prompts and the tool (Phase 1 IMPLEMENTATION doc sections 3 and 5, and the placeholder rule)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from horizon_compact.experiment import Experiment, Objective
from horizon_compact.providers.base import DecisionRequest
from horizon_compact.providers.bedrock import build_request
from horizon_compact.sweep.prompt import TOOL_NAME, RenderedPrompt, build_tool
from horizon_compact.sweep.prompt import render_prompt as render_in
from sweep_helpers import NOVA_ROUTE, company_like, experiment, lever, make_plan, scenario

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


def render_prompt(exp: Experiment, objective: Objective, seed: int) -> RenderedPrompt:
    """The placeholder has one scenario and one template, so the tests name neither."""
    return render_in(exp, exp.scenario, objective, "w1", seed)


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


# --- Phase 2.5: scenarios without a choice, people, notes and templates ---------------------------


def test_a_scenario_without_a_choice_renders_no_options_block_and_the_tool_has_no_choice_field() -> (
    None
):
    scn = scenario(
        "uses_equal_total",
        [
            lever("keep", "use"),
            lever("fund", "use"),
            lever("roles", "not_offered", 0, note="not chosen directly"),
        ],
    )
    tool = build_tool(scn)
    assert list(tool.input_schema["properties"]) == ["amounts", "memo"]
    assert tool.input_schema["required"] == ["amounts", "memo"]
    exp = experiment()
    p = render_in(exp, scn, exp.objectives[0], "w1", 5)
    assert p.option_order == ()
    blocks = p.user.split("\n\n")
    assert (
        len(blocks) == 4
    )  # the scenario, the objective, the menu and the instruction: no options block
    assert "- roles [roles]: not chosen directly" in blocks[2]


def test_the_not_offered_line_shows_the_levers_own_note_or_a_plain_not_offered() -> None:
    scn = scenario(
        "uses_equal_total",
        [
            lever("keep", "use"),
            lever("a", "not_offered", 0, note="held fixed by the board"),
            lever("b", "not_offered", 0),
        ],
    )
    exp = experiment()
    user = render_in(exp, scn, exp.objectives[0], "w1", 5).user
    assert "- a [a]: held fixed by the board" in user
    assert "- b [b]: not offered\n" in user + "\n"


def test_people_are_shown_as_a_count_and_the_tool_asks_for_integers() -> None:
    scn = scenario(
        "split_equals_headcount",
        [lever("out", "use", 190), lever("kept", "use", 190)],
        total=190,
        unit="people",
    )
    exp = experiment()
    user = render_in(exp, scn, exp.objectives[0], "w1", 5).user
    assert "- out [out]: use, up to 190 people" in user
    assert "$" not in user.split("\n\n")[2]  # the menu block
    amounts = build_tool(scn).input_schema["properties"]["amounts"]["properties"]
    assert {spec["type"] for spec in amounts.values()} == {"integer"}


def test_dollars_are_shown_with_a_dollar_sign_and_the_tool_asks_for_numbers() -> None:
    scn = scenario("uses_equal_total", [lever("keep", "use")])
    exp = experiment()
    assert (
        "- keep [keep]: use, up to $1,000" in render_in(exp, scn, exp.objectives[0], "w1", 5).user
    )
    amounts = build_tool(scn).input_schema["properties"]["amounts"]["properties"]
    assert amounts["keep"]["type"] == "number"


def test_templates_change_only_the_objective_paragraph_and_the_template_is_recorded(
    tmp_path: Path,
) -> None:
    exp = company_like(tmp_path, sealed="w3")
    scn = exp.get_scenario("s1")
    objective = exp.objectives[0]
    first = render_in(exp, scn, objective, "w1", 11)
    second = render_in(exp, scn, objective, "w2", 11)
    assert (first.template_id, second.template_id) == ("w1", "w2")
    assert first.system == second.system
    assert (first.lever_order, first.option_order) == (second.lever_order, second.option_order)
    a, b = first.user.split("\n\n"), second.user.split("\n\n")
    assert len(a) == len(b)
    assert [i for i, (x, y) in enumerate(zip(a, b, strict=True)) if x != y] == [
        1
    ]  # the second paragraph only
    assert "create value for members, over this year" in a[1]
    assert "create value for members over this year" in b[1]


def test_the_baseline_gets_the_templates_none_sentence_in_the_same_position(tmp_path: Path) -> None:
    exp = company_like(tmp_path, sealed="w3")
    scn = exp.get_scenario("s1")
    stated, baseline = exp.objectives[0], exp.objectives[2]
    for template_id, none in (
        ("w1", "The panel has set no aim."),
        ("w2", "The panel has not asked you to pursue an aim."),
    ):
        assert render_in(exp, scn, baseline, template_id, 3).user.split("\n\n")[1] == none
        assert render_in(exp, scn, stated, template_id, 3).user.split("\n\n")[1] != none
