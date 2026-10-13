"""The thinking sub-study (Phase 4 runs half section 5.2; protocol 9.5): the request it sends, the plan it may
be, the repeats it checks, the bound it is capped by, and the one-sweep-per-study rule. Fakes only: no model
call, no AWS call, no socket. The company here is the fictional one."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from fake_anthropic import KEY, FakeAnthropic, message, ok
from horizon_compact.analysis.repeats import ChoiceRepeats, ShareRepeats
from horizon_compact.experiment import Experiment, load_experiment
from horizon_compact.protocol.gate import (
    PILOT_LABEL,
    RepeatDecision,
    check_one_sweep_per_study,
    check_repeats,
    write_repeats,
)
from horizon_compact.providers.anthropic import AnthropicProvider
from horizon_compact.providers.base import (
    THINKING_LABEL,
    THINKING_STUDY_EFFORT_NOTE,
    THINKING_STUDY_MAX_TOKENS,
    THINKING_STUDY_OUTPUT_CONFIG,
    THINKING_STUDY_THINKING,
    THINKING_STUDY_THINKING_NOTE,
    DecisionRequest,
    ModelRoute,
    ToolSpec,
)
from horizon_compact.providers.bedrock import build_request
from horizon_compact.providers.ollama import OllamaProvider
from horizon_compact.providers.openrouter import OpenRouterProvider
from horizon_compact.sweep.plan import (
    SweepPlan,
    SweepRefusal,
    build_plan,
    check_preflight,
    preflight_bound_usd,
    request_max_tokens,
    worst_case_per_attempt_usd,
)
from horizon_compact.sweep.runner import sweep_prefix
from horizon_compact.sweep.store import LocalStore
from sweep_helpers import experiment as placeholder_experiment
from sweep_helpers import session, valid_input

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "experiment" / "protocol" / "protocol-v1.md"
HAIKU = "haiku-5-5"
ROUTE = ModelRoute(
    HAIKU, "claude-haiku-5-5", "anthropic", invoke_id="claude-haiku-5-5", thinking_off=True
)
TOOL = ToolSpec(
    "submit_decision", "d", {"type": "object", "properties": {"memo": {"type": "string"}}}
)
NEVER_SENT = (
    "temperature", "top_p", "top_k", "cache_control", "inference_geo", "betas", "fallback_model",
    "service_tier", "metadata", "stop_sequences",
)  # fmt: skip


def company() -> Experiment:
    return load_experiment("company")


def study_plan(exp: Experiment, **overrides: Any) -> SweepPlan:
    args: dict[str, Any] = {
        "model_key": HAIKU,
        "label": THINKING_LABEL,
        "repeats": 7,
        "seed": 3422206995,
        "scenarios": ["s1"],
        "templates": [exp.sealed_template],
        "official": True,
    }
    args.update(overrides)
    return build_plan(exp, **args)


def study_request(
    max_tokens: int = THINKING_STUDY_MAX_TOKENS, route: ModelRoute = ROUTE
) -> DecisionRequest:
    return DecisionRequest(route, "sys", "usr", TOOL, max_tokens, thinking_study=True)


# --- the request is the protocol's, word for word ---------------------------------------------------------


def test_the_constants_appear_word_for_word_in_the_protocol() -> None:
    text = re.sub(r"\s+", " ", PROTOCOL.read_text(encoding="utf-8"))
    assert f"thinking: {json.dumps(dict(THINKING_STUDY_THINKING))}" in text
    assert f"output_config: {json.dumps(dict(THINKING_STUDY_OUTPUT_CONFIG))}" in text
    assert f"`max_tokens` {THINKING_STUDY_MAX_TOKENS:,}" in text
    assert THINKING_STUDY_OUTPUT_CONFIG["effort"] == THINKING_STUDY_EFFORT_NOTE
    assert THINKING_STUDY_THINKING_NOTE == "adaptive, display summarized: sent"


def test_the_sub_study_body_is_the_grids_with_exactly_the_three_changes() -> None:
    server = FakeAnthropic()
    AnthropicProvider(KEY, http_client=server.client).decide(study_request())
    sent = server.bodies[0]
    grid_server = FakeAnthropic()
    grid = DecisionRequest(ROUTE, "sys", "usr", TOOL, 3072)
    AnthropicProvider(KEY, http_client=grid_server.client).decide(grid)
    baseline = grid_server.bodies[0]
    assert baseline["thinking"] == {"type": "disabled"} and "output_config" not in baseline
    assert sent["thinking"] == {"type": "adaptive", "display": "summarized"}
    assert sent["output_config"] == {"effort": "high"}
    assert sent["max_tokens"] == 16_000
    same = {k: v for k, v in sent.items() if k not in ("thinking", "output_config", "max_tokens")}
    assert same == {k: v for k, v in baseline.items() if k not in ("thinking", "max_tokens")}
    assert set(sent) == set(baseline) | {"output_config"}
    for never in NEVER_SENT:
        assert never not in sent, never
    assert sent["tool_choice"] == {"type": "auto"}


def test_the_body_the_provider_describes_is_the_body_it_sends_in_the_sub_study() -> None:
    server = FakeAnthropic()
    sender = AnthropicProvider(KEY, http_client=server.client)
    sender.decide(study_request())
    assert sender.request_body(study_request()) == server.bodies[0]


def test_the_sub_study_records_thinking_effort_and_max_tokens_on_every_attempt() -> None:
    server = FakeAnthropic(
        lambda body: ok(
            message(
                content=[
                    {"type": "thinking", "thinking": "a summary", "signature": "sig"},
                    {
                        "type": "tool_use",
                        "id": "t",
                        "name": "submit_decision",
                        "input": valid_input(),
                    },
                ],
                output_tokens=4100,
            )
        )
    )
    result = AnthropicProvider(KEY, http_client=server.client).decide(study_request())
    assert result.provenance.thinking == "adaptive, display summarized: sent"
    assert result.provenance.effort == "high"
    assert result.provenance.max_tokens == 16_000
    assert result.reasoning_block_count == 1 and result.usage.output_tokens == 4100


def test_a_request_that_is_not_the_sub_study_sends_none_of_it() -> None:
    server = FakeAnthropic()
    result = AnthropicProvider(KEY, http_client=server.client).decide(
        DecisionRequest(ROUTE, "sys", "usr", TOOL, 3072)
    )
    assert "output_config" not in server.bodies[0]
    assert result.provenance.thinking.startswith("off") and result.provenance.effort.startswith(
        "not set"
    )


def test_the_sub_study_refuses_another_max_tokens_or_a_route_with_no_thinking_off() -> None:
    sender = AnthropicProvider(KEY, http_client=FakeAnthropic().client)
    with pytest.raises(ValueError, match="max_tokens 16,000"):
        sender.request_body(study_request(max_tokens=3072))
    unset = ModelRoute(HAIKU, "claude-haiku-5-5", "anthropic", invoke_id="claude-haiku-5-5")
    with pytest.raises(ValueError, match="replaces the grid's thinking"):
        sender.request_body(study_request(route=unset))


def test_every_other_route_refuses_the_sub_study_request() -> None:
    request = study_request()
    with pytest.raises(ValueError, match="Anthropic's only"):
        build_request(request)
    with pytest.raises(ValueError, match="Anthropic's only"):
        OpenRouterProvider(KEY).request_body(request)
    with pytest.raises(ValueError, match="Anthropic's only"):
        OllamaProvider().request_body(request)


# --- the plan: the label is the switch, and nothing else is allowed -------------------------------------


def test_the_official_sub_study_is_s1_on_the_sealed_wording_on_the_main_model() -> None:
    exp = company()
    plan = study_plan(exp)
    assert plan.scenarios == ("s1",) and plan.templates == (exp.sealed_template,)
    assert len(plan.runs) == 5 * 7
    assert plan.sweep_id.startswith("thinking-haiku-5-5-")


@pytest.mark.parametrize(
    ("overrides", "needle"),
    [
        ({"model_key": "gpt-oss-openrouter"}, "only the Anthropic route carries"),
        ({"model_key": "sonnet-4-6"}, "only the Anthropic route carries"),
        ({"scenarios": ["s2"]}, "the scenario is ['s2']"),
        ({"scenarios": ["s1", "s2"]}, "the scenario is ['s1', 's2']"),
        ({"scenarios": None}, "the scenario is"),
        ({"templates": ["w1"]}, "the template is ['w1']"),
        ({"templates": None}, "the template is"),
        ({"official": False}, "official sub-study"),
    ],
)
def test_a_thinking_plan_on_another_model_scenario_or_template_is_refused(
    overrides: dict[str, Any], needle: str
) -> None:
    with pytest.raises(SweepRefusal, match=re.escape(needle)):
        study_plan(company(), **overrides)


def test_a_thinking_plan_may_run_off_the_subject_for_the_final_image_check() -> None:
    exp = placeholder_experiment()
    plan = build_plan(exp, model_key=HAIKU, label=THINKING_LABEL, repeats=1, seed=1)
    assert plan.scenarios == ("garden",) and len(plan.runs) == 5
    with pytest.raises(SweepRefusal, match="only the Anthropic route carries"):
        build_plan(exp, model_key="nova-lite", label=THINKING_LABEL, repeats=1, seed=1)


def test_a_session_on_a_thinking_plan_sends_the_sub_study_request_and_a_resume_keeps_it(
    tmp_path: Path,
) -> None:
    exp = placeholder_experiment()
    plan = build_plan(exp, model_key=HAIKU, label=THINKING_LABEL, repeats=1, seed=1)
    server = FakeAnthropic()
    store = LocalStore(tmp_path)
    provider = AnthropicProvider(KEY, http_client=server.client)
    stopped = {"n": 0}

    def stop_after_two() -> bool:
        stopped["n"] += 1
        return len(server.bodies) >= 2

    first = session(exp, plan, provider, store, route=ROUTE, should_stop=stop_after_two)
    assert first.stopped == "stop_requested" and len(server.bodies) == 2
    second = session(exp, plan, provider, store, route=ROUTE)
    assert second.stopped == "complete" and len(server.bodies) == 5  # three more; nothing re-run
    for body in server.bodies:
        assert body["thinking"] == {"type": "adaptive", "display": "summarized"}
        assert body["output_config"] == {"effort": "high"} and body["max_tokens"] == 16_000
    prefix = sweep_prefix("placeholder", plan.sweep_id, "development")
    attempts = [
        json.loads(store.get(k) or "{}") for k in store.list_keys(prefix) if "/attempt-" in k
    ]
    assert len(attempts) == 5
    for attempt in attempts:
        assert attempt["thinking"] == "adaptive, display summarized: sent"
        assert attempt["effort"] == "high" and attempt["max_tokens"] == 16_000
        assert attempt["request"]["output_config"] == {"effort": "high"}
    assert json.loads(store.get(f"{prefix}manifest.json") or "{}")["label"] == THINKING_LABEL


def test_a_grid_labeled_session_never_sends_the_sub_study_request(tmp_path: Path) -> None:
    exp = placeholder_experiment()
    plan = build_plan(exp, model_key=HAIKU, label="final", repeats=1, seed=1)
    server = FakeAnthropic()
    session(
        exp,
        plan,
        AnthropicProvider(KEY, http_client=server.client),
        LocalStore(tmp_path),
        route=ROUTE,
    )
    assert len(server.bodies) == 5
    for body in server.bodies:
        assert body["thinking"] == {"type": "disabled"}
        assert "output_config" not in body and body["max_tokens"] == 2048


# --- the repeats: S1's count, and nothing about the other scenarios ---------------------------------------


def repeats_record(exp: Experiment, by_scenario: dict[str, int], pilot_id: str) -> RepeatDecision:
    results = tuple(
        ShareRepeats(sid, 0.12, 40, 9, 14, n, False, None)
        if sid in ("s1", "s2")
        else ChoiceRepeats(sid, n, 0.1, 0.05)
        for sid, n in by_scenario.items()
    )
    return RepeatDecision("prereg-v1", pilot_id, HAIKU, exp.content_hash, ("r-0",), results)


def test_the_sub_study_checks_only_s1s_count_against_the_pilots(tmp_path: Path) -> None:
    exp = company()
    pilot_id = "pilot-company-0000"
    store = LocalStore(tmp_path)
    write_repeats(
        store,
        sweep_prefix("company", pilot_id, "pilot"),
        repeats_record(exp, {"s1": 7, "s2": 11, "s3": 20, "s4": 20}, pilot_id),
    )
    check_repeats(
        store, study_plan(exp, repeats=7), pilot_id
    )  # S1's count is equal: nothing raised
    with pytest.raises(SweepRefusal, match="scenario s1: the pilot sets 7 repeats, the plan has 8"):
        check_repeats(store, study_plan(exp, repeats=8), pilot_id)
    # every other check stands: another model's pilot is still refused
    other = LocalStore(tmp_path / "other")
    write_repeats(
        other,
        sweep_prefix("company", pilot_id, "pilot"),
        RepeatDecision("prereg-v1", pilot_id, "gpt-oss-openrouter", exp.content_hash, ("r-0",),
                       repeats_record(exp, {"s1": 7, "s2": 7, "s3": 20, "s4": 20}, pilot_id).scenarios),
    )  # fmt: skip
    with pytest.raises(SweepRefusal, match="the pilot ran 'gpt-oss-openrouter'"):
        check_repeats(other, study_plan(exp, repeats=7), pilot_id)


def test_a_grid_that_runs_fewer_scenarios_than_the_pilot_is_still_refused(tmp_path: Path) -> None:
    exp = company()
    pilot_id = "pilot-company-0000"
    store = LocalStore(tmp_path)
    write_repeats(
        store,
        sweep_prefix("company", pilot_id, "pilot"),
        repeats_record(exp, {"s1": 7, "s2": 7, "s3": 20, "s4": 20}, pilot_id),
    )
    s1_only_grid = study_plan(exp, label="grid", repeats=7)
    with pytest.raises(SweepRefusal, match=r"that this plan does not run"):
        check_repeats(store, s1_only_grid, pilot_id)


# --- the cap: 16,000 output tokens, not the scenario's ---------------------------------------------------


def test_the_allowance_is_16000_for_the_sub_study_and_the_scenarios_for_everything_else() -> None:
    assert request_max_tokens(THINKING_LABEL, 3072) == 16_000
    assert (
        request_max_tokens("grid", 3072) == 3072 and request_max_tokens(PILOT_LABEL, 3072) == 3072
    )


def test_the_preflight_bound_uses_16000_output_tokens() -> None:
    exp = company()
    study = study_plan(exp)
    grid_shaped = study_plan(exp, label="grid")
    extra = (
        (16_000 - exp.get_scenario("s1").max_tokens) * exp.model(HAIKU).prices.output / 1_000_000
    )
    assert worst_case_per_attempt_usd(exp, study) - worst_case_per_attempt_usd(
        exp, grid_shaped
    ) == pytest.approx(extra, abs=2e-6)
    low, high = preflight_bound_usd(exp, grid_shaped), preflight_bound_usd(exp, study)
    assert high > low
    cap = (low + high) / 2
    check_preflight(exp, grid_shaped, cap)
    with pytest.raises(SweepRefusal, match="above the cap"):
        check_preflight(exp, study, cap)


# --- one sweep per study per model -----------------------------------------------------------------------


def put_manifest(store: LocalStore, plan: SweepPlan) -> None:
    key = f"{sweep_prefix(plan.experiment, plan.sweep_id, 'official')}manifest.json"
    assert store.put_new(key, json.dumps(plan.manifest()))


def grid_plan(exp: Experiment, seed: int = 541789037, model: str = HAIKU) -> SweepPlan:
    return build_plan(exp, model_key=model, label="grid", repeats=1, seed=seed, official=True)


def test_a_second_official_sweep_of_one_study_on_one_model_is_refused_but_its_resume_is_not(
    tmp_path: Path,
) -> None:
    exp = company()
    store = LocalStore(tmp_path)
    first = grid_plan(exp)
    check_one_sweep_per_study(store, first)  # nothing there yet
    put_manifest(store, first)
    check_one_sweep_per_study(store, first)  # the resume of the same sweep id
    with pytest.raises(SweepRefusal, match=r"already has an official 'grid' sweep"):
        check_one_sweep_per_study(store, grid_plan(exp, seed=1))
    check_one_sweep_per_study(store, grid_plan(exp, model="gpt-oss-openrouter"))  # another model
    check_one_sweep_per_study(store, study_plan(exp))  # another study


def test_a_pilot_or_development_manifest_does_not_count_and_an_odd_label_is_refused(
    tmp_path: Path,
) -> None:
    exp = company()
    store = LocalStore(tmp_path)
    pilot = build_plan(exp, model_key=HAIKU, label="grid", repeats=1, seed=5, official=True)
    assert store.put_new(
        f"{sweep_prefix('company', pilot.sweep_id, 'pilot')}manifest.json",
        json.dumps(pilot.manifest()),
    )
    check_one_sweep_per_study(store, grid_plan(exp))
    with pytest.raises(SweepRefusal, match="not an official study's"):
        check_one_sweep_per_study(
            store, build_plan(exp, model_key=HAIKU, label="grid2", repeats=1, seed=1, official=True)
        )
    with pytest.raises(SweepRefusal, match="not an official study's"):
        check_one_sweep_per_study(
            store,
            build_plan(exp, model_key=HAIKU, label=PILOT_LABEL, repeats=2, seed=1, official=True),
        )
