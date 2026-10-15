"""The awareness probe's run (Phase 4 code half IMPLEMENTATION doc section 4.5, protocol 9.6): the plan, the
text request on both providers, the session, resume, no retry of a reply, the report and the command. Nothing
here calls a model: the provider is scripted, Bedrock is botocore's Stubber and OpenRouter is a loopback
stand-in."""

from __future__ import annotations

import json
import random
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import boto3
import pytest
from botocore.stub import Stubber

from fake_openrouter import KEY, MODEL, FakeOpenRouter, completion
from horizon_compact import cli
from horizon_compact.experiment import Experiment, load_experiment
from horizon_compact.providers.base import (
    ModelRoute,
    Provenance,
    RawDecision,
    TextRequest,
    Usage,
)
from horizon_compact.providers.bedrock import BedrockConverseProvider, build_text_request
from horizon_compact.providers.openrouter import OpenRouterProvider
from horizon_compact.sweep.awareness import (
    AwarenessResult,
    awareness_prefix,
    awareness_report,
    awareness_worst_case_usd,
    build_awareness_plan,
    run_awareness,
)
from horizon_compact.sweep.plan import SweepPlan, SweepRefusal, build_plan
from horizon_compact.sweep.prompt import AWARENESS_INSTRUCTION, render_prompt
from horizon_compact.sweep.store import LocalStore
from sweep_helpers import ACCOUNT, FARGATE, SONNET_ROUTE, FakeClock

MODEL_KEY = "sonnet-4-6"
REPLY = "I think this tests whether the model weighs people against profit."


@pytest.fixture(scope="module")
def company() -> Experiment:
    return load_experiment("company")


@pytest.fixture(scope="module")
def plan(company: Experiment) -> SweepPlan:
    return build_awareness_plan(company, MODEL_KEY, 11)


def provenance(request: TextRequest) -> Provenance:
    return Provenance(
        provider="fake",
        api="converse",
        model_id=request.route.model_id,
        invoke_id=request.route.invoke_id,
        route_kind=request.route.route_kind,
        inference_profile=request.route.inference_profile,
        region="us-east-1",
        thinking="not set",
        effort="not set",
        temperature="not set",
        max_tokens=request.max_tokens,
        prompt_sha256="0" * 64,
        started_at="2026-10-11T12:00:00+00:00",
        finished_at="2026-10-11T12:00:01+00:00",
        latency_ms=1000,
    )


def reply(request: TextRequest, text: str = REPLY, stop: str = "end_turn") -> RawDecision:
    return RawDecision(
        status="ok",
        provenance=provenance(request),
        raw_response={"stopReason": stop, "usage": {}},
        stop_reason=stop,
        text_blocks=[text],
        usage=Usage(input_tokens=2000, output_tokens=60),
    )


def error(request: TextRequest, code: str) -> RawDecision:
    return RawDecision(
        status="api_error",
        provenance=provenance(request),
        error={"code": code, "message": f"{code} for {ACCOUNT}"},
    )


class TextScript:
    """``script(n, request)`` returns the n-th response (from 1). Every request is kept."""

    name = "fake"

    def __init__(self, script: Callable[[int, TextRequest], RawDecision] | None = None) -> None:
        self._script = script or (lambda n, request: reply(request))
        self.requests: list[TextRequest] = []

    def text_request_body(self, request: TextRequest) -> dict[str, Any]:
        return build_text_request(request)

    def decide_text(self, request: TextRequest) -> RawDecision:
        self.requests.append(request)
        return self._script(len(self.requests), request)


def run(
    company: Experiment,
    plan: SweepPlan,
    provider: TextScript,
    store: LocalStore,
    **overrides: Any,
) -> AwarenessResult:
    clock = FakeClock()
    arguments: dict[str, Any] = {
        "experiment": company,
        "plan": plan,
        "route": SONNET_ROUTE,
        "provider": provider,
        "store": store,
        "identity": FARGATE,
        "account_id": ACCOUNT,
        "cap_usd": 5.0,
        "max_minutes": 30.0,
        "harness_version": "0.test",
        "monotonic": clock.monotonic,
        "sleep": clock.sleep,
        "rng": random.Random(1),
    }
    arguments.update(overrides)
    return run_awareness(**arguments)


def records(store: LocalStore, plan: SweepPlan) -> list[dict[str, Any]]:
    keys = store.list_keys(f"{awareness_prefix(plan)}runs/")
    return [json.loads(store.get(key) or "") for key in keys]


# --- the plan ---------------------------------------------------------------------------------------


def test_the_plan_is_s1_every_objective_every_template_one_call_each(
    company: Experiment, plan: SweepPlan
) -> None:
    assert len(plan.runs) == 15
    assert len(company.objectives) * len(company.templates) == 15
    assert {r.scenario_id for r in plan.runs} == {"s1"}
    assert {(r.objective_id, r.wording_id) for r in plan.runs} == {
        (o.id, t) for o in company.objectives for t in company.templates
    }
    assert plan.label == "awareness" and dict(plan.repeats) == {"s1": 1}
    assert company.sealed_template in plan.templates  # "every template" includes the sealed one


def test_the_plan_is_its_own_sweep_with_its_own_prefix(
    company: Experiment, plan: SweepPlan
) -> None:
    assert plan.sweep_id.startswith("awareness-")
    grid = build_plan(company, model_key=MODEL_KEY, label="grid", repeats=1, seed=11, official=True)
    assert plan.sweep_id != grid.sweep_id
    assert awareness_prefix(plan) == f"official/company/awareness/{plan.sweep_id}/"
    assert not awareness_prefix(plan).startswith(f"official/company/{grid.sweep_id}/")


def test_the_seed_changes_the_sweep_and_the_same_seed_gives_the_same_one(
    company: Experiment, plan: SweepPlan
) -> None:
    assert build_awareness_plan(company, MODEL_KEY, 11).sweep_id == plan.sweep_id
    assert build_awareness_plan(company, MODEL_KEY, 12).sweep_id != plan.sweep_id


def test_an_experiment_without_s1_is_refused(company: Experiment) -> None:
    class NoS1:
        name = "x"
        scenarios: tuple[str, ...] = ("s2",)

    with pytest.raises(SweepRefusal, match="no scenario 's1'"):
        build_awareness_plan(NoS1(), MODEL_KEY, 1)  # type: ignore[arg-type]


# --- the prompt and the request ----------------------------------------------------------------------


def test_the_prompt_is_the_grid_prompt_with_only_the_instruction_replaced(
    company: Experiment, plan: SweepPlan, tmp_path: Path
) -> None:
    provider = TextScript()
    run(company, plan, provider, LocalStore(tmp_path))
    by_user = {r.user: r for r in provider.requests}
    assert len(by_user) == 15
    objectives = {o.id: o for o in company.objectives}
    scenario = company.get_scenario("s1")
    for spec in plan.runs:
        grid = render_prompt(
            company, scenario, objectives[spec.objective_id], spec.wording_id, spec.menu_order_seed
        )
        sent = next(
            r
            for r in provider.requests
            if r.user.startswith(grid.user[: -len(scenario.instruction.strip())])
        )
        assert sent.system == grid.system
        assert sent.user == grid.user[: -len(scenario.instruction.strip())] + AWARENESS_INSTRUCTION
        assert sent.max_tokens == scenario.max_tokens


def test_bedrock_sends_no_tool_config() -> None:
    request = TextRequest(SONNET_ROUTE, "sys", "usr", 300)
    body = build_text_request(request)
    assert "toolConfig" not in body
    assert body["inferenceConfig"] == {"maxTokens": 300}
    assert body["messages"] == [{"role": "user", "content": [{"text": "usr"}]}]
    for forbidden in ("temperature", "topP", "topK"):
        assert forbidden not in body["inferenceConfig"]


def test_bedrock_decide_text_reads_the_text_and_sends_the_body_it_describes() -> None:
    client = boto3.client("bedrock-runtime", region_name="us-east-1")
    request = TextRequest(SONNET_ROUTE, "sys", "usr", 300)
    expected = build_text_request(request)
    stubber = Stubber(client)
    stubber.add_response(
        "converse",
        {
            "output": {"message": {"role": "assistant", "content": [{"text": REPLY}]}},
            "stopReason": "end_turn",
            "usage": {"inputTokens": 10, "outputTokens": 5, "totalTokens": 15},
            "metrics": {"latencyMs": 100},
        },
        expected,
    )
    stubber.activate()
    provider = BedrockConverseProvider(client, now=lambda: datetime(2026, 10, 11, tzinfo=UTC))
    result = provider.decide_text(request)
    stubber.assert_no_pending_responses()
    assert result.status == "ok" and result.text_blocks == [REPLY]
    assert result.tool_call_count == 0 and result.stop_reason == "end_turn"
    assert provider.text_request_body(request) == expected
    assert result.provenance.thinking == "not set" and len(result.provenance.prompt_sha256) == 64


def test_openrouter_sends_no_tools_and_no_tool_choice() -> None:
    route = ModelRoute("gpt-test", MODEL, "openrouter", invoke_id=MODEL)
    request = TextRequest(route, "sys", "usr", 300)
    with FakeOpenRouter(
        lambda body: (200, completion(finish_reason="stop", tool_calls=[], content=REPLY))
    ) as server:
        provider = OpenRouterProvider(KEY, server.url)
        result = provider.decide_text(request)
    (body,) = server.bodies
    assert "tools" not in body and "tool_choice" not in body
    assert body == provider.text_request_body(request)
    assert body["max_tokens"] == 300 and KEY not in json.dumps(body)
    assert result.status == "ok" and result.text_blocks == [REPLY]
    assert result.tool_call_count == 0 and result.stop_reason == "end_turn"


# --- the session ------------------------------------------------------------------------------------


def test_fifteen_calls_are_written_under_the_official_awareness_prefix(
    company: Experiment, plan: SweepPlan, tmp_path: Path
) -> None:
    store = LocalStore(tmp_path)
    result = run(company, plan, TextScript(), store)
    assert result.stopped == "complete" and result.clean
    assert (result.calls_total, result.calls_done_now, result.api_calls_now) == (15, 15, 15)
    prefix = awareness_prefix(plan)
    assert store.get(f"{prefix}manifest.json") is not None
    keys = store.list_keys("")
    assert len(keys) == 16 and all(k.startswith(prefix) for k in keys)
    stored = records(store, plan)
    assert {r["label"] for r in stored} == {"official"}
    assert {r["kind"] for r in stored} == {"awareness"}
    assert {r["status"] for r in stored} == {"replied"}
    assert all(r["text_blocks"] == [REPLY] for r in stored)


def test_a_record_holds_the_request_without_a_tool_and_its_provenance(
    company: Experiment, plan: SweepPlan, tmp_path: Path
) -> None:
    store = LocalStore(tmp_path)
    run(company, plan, TextScript(), store)
    for record in records(store, plan):
        assert "toolConfig" not in record["request"] and "tools" not in record["request"]
        assert record["model_key"] == MODEL_KEY and record["image_digest"] == FARGATE.image_digest
        assert record["content_hash"] == company.content_hash
        assert record["scenario_id"] == "s1" and record["usage"]["output_tokens"] == 60
        assert ACCOUNT not in json.dumps(record)


def test_resume_skips_finished_calls_and_never_repeats_one(
    company: Experiment, plan: SweepPlan, tmp_path: Path
) -> None:
    store = LocalStore(tmp_path)
    first = TextScript()
    stopped = run(company, plan, first, store, should_stop=lambda: len(first.requests) >= 6)
    assert stopped.stopped == "stop_requested" and len(records(store, plan)) == 6
    second = TextScript()
    done = run(company, plan, second, store)
    assert done.stopped == "complete"
    assert (done.calls_done_before, done.calls_done_now) == (6, 9) and len(second.requests) == 9
    assert len(records(store, plan)) == 15
    third = TextScript()
    again = run(company, plan, third, store)
    assert again.stopped == "complete" and third.requests == []


def test_a_changed_experiment_or_seed_is_refused_not_resumed(
    company: Experiment, plan: SweepPlan, tmp_path: Path
) -> None:
    store = LocalStore(tmp_path)
    run(company, plan, TextScript(), store, should_stop=lambda: True)
    key = f"{awareness_prefix(plan)}manifest.json"
    manifest = json.loads(store.get(key) or "")
    manifest["content_hash"] = "0" * 64
    (tmp_path / key).write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(SweepRefusal, match="differs from the plan"):
        run(company, plan, TextScript(), store)


@pytest.mark.parametrize(
    ("stop", "text", "status"),
    [
        ("max_tokens", "the model started to say", "truncated"),
        ("end_turn", "", "no_text"),
        ("content_filtered", "", "content_filtered"),
        ("odd_stop", "x", "unexpected_stop"),
    ],
)
def test_a_reply_is_the_measurement_so_it_is_recorded_whatever_it_is_and_never_retried(
    company: Experiment, plan: SweepPlan, tmp_path: Path, stop: str, text: str, status: str
) -> None:
    provider = TextScript(lambda n, request: reply(request, text, stop))
    store = LocalStore(tmp_path)
    result = run(company, plan, provider, store)
    assert result.stopped == "complete" and len(provider.requests) == 15  # one call each, no retry
    assert {r["status"] for r in records(store, plan)} == {status}


def errors(store: LocalStore, plan: SweepPlan) -> list[tuple[str, dict[str, Any]]]:
    keys = store.list_keys(f"{awareness_prefix(plan)}errors/")
    return [(key, json.loads(store.get(key) or "")) for key in keys]


def test_an_api_error_is_retried_with_backoff_and_kept_as_its_own_record(
    company: Experiment, plan: SweepPlan, tmp_path: Path
) -> None:
    clock = FakeClock()
    provider = TextScript(
        lambda n, request: error(request, "ThrottlingException") if n <= 2 else reply(request)
    )
    store = LocalStore(tmp_path)
    result = run(company, plan, provider, store, monotonic=clock.monotonic, sleep=clock.sleep)
    assert result.stopped == "complete" and len(provider.requests) == 17
    assert len(records(store, plan)) == 15
    assert all(r["status"] == "replied" for r in records(store, plan))
    assert provider.requests[0] == provider.requests[1] == provider.requests[2]  # the same request
    # protocol 13.2: every call leaves an object, an API error included
    kept = errors(store, plan)
    first_run = plan.runs[0].run_id
    assert [key.rsplit("/", 1)[-1] for key, _ in kept] == [
        f"{first_run}-1.json",
        f"{first_run}-2.json",
    ]
    for _, record in kept:
        assert record["kind"] == "awareness-api-error" and record["label"] == "official"
        assert record["error"]["code"] == "ThrottlingException"
        assert record["run_id"] == first_run and record["image_digest"] == FARGATE.image_digest
        assert "toolConfig" not in record["request"]
        assert ACCOUNT not in json.dumps(record)  # the error message named it; the writer scrubs it


def test_a_resumed_session_numbers_errors_on_and_counts_their_cost(
    company: Experiment, plan: SweepPlan, tmp_path: Path
) -> None:
    store = LocalStore(tmp_path)

    def costly_error(n: int, request: TextRequest) -> RawDecision:
        failed = error(request, "ThrottlingException")
        return RawDecision(
            status="api_error",
            provenance=failed.provenance,
            error=failed.error,
            usage=Usage(input_tokens=1000),
        )

    first = TextScript(costly_error)
    run(company, plan, first, store, should_stop=lambda: len(first.requests) >= 1)
    spent = sum(r["cost_usd"] for _, r in errors(store, plan))
    assert spent > 0
    second = TextScript(lambda n, request: costly_error(n, request) if n == 1 else reply(request))
    result = run(company, plan, second, store)
    assert [key.rsplit("-", 1)[-1] for key, _ in errors(store, plan)] == ["1.json", "2.json"]
    assert result.cost_usd_total > result.cost_usd_now  # the first session's error cost is counted


def test_ten_api_errors_in_a_row_stop_the_session(
    company: Experiment, plan: SweepPlan, tmp_path: Path
) -> None:
    provider = TextScript(lambda n, request: error(request, "ThrottlingException"))
    store = LocalStore(tmp_path)
    result = run(company, plan, provider, store)
    assert result.stopped == "api_errors" and not result.clean
    assert records(store, plan) == [] and len(errors(store, plan)) == 10


def test_a_config_error_stops_the_session(
    company: Experiment, plan: SweepPlan, tmp_path: Path
) -> None:
    provider = TextScript(lambda n, request: error(request, "AccessDeniedException"))
    store = LocalStore(tmp_path)
    result = run(company, plan, provider, store)
    assert result.stopped == "config_error" and len(provider.requests) == 1
    assert [r["error"]["code"] for _, r in errors(store, plan)] == ["AccessDeniedException"]


def test_the_cap_stops_the_session_before_a_call_that_could_pass_it(
    company: Experiment, plan: SweepPlan, tmp_path: Path
) -> None:
    worst = awareness_worst_case_usd(company, plan)
    max_tokens = company.get_scenario("s1").max_tokens

    def dear(n: int, request: TextRequest) -> RawDecision:
        return RawDecision(
            status="ok",
            provenance=provenance(request),
            raw_response={},
            stop_reason="end_turn",
            text_blocks=[REPLY],
            usage=Usage(input_tokens=0, output_tokens=2 * max_tokens),
        )

    provider = TextScript(dear)
    cap = worst * 15 + 0.001  # just above the preflight bound, so the session starts
    result = run(company, plan, provider, LocalStore(tmp_path), cap_usd=cap)
    assert result.stopped == "cap_reached" and result.clean
    assert 0 < len(provider.requests) < 15
    assert result.cost_usd_total + worst > cap  # the next call could have passed it


def test_a_cap_below_the_worst_case_is_refused_before_any_call(
    company: Experiment, plan: SweepPlan, tmp_path: Path
) -> None:
    provider = TextScript()
    with pytest.raises(SweepRefusal, match="above the cap"):
        run(company, plan, provider, LocalStore(tmp_path), cap_usd=0.01)
    assert provider.requests == []


def test_a_non_awareness_plan_is_refused(company: Experiment, tmp_path: Path) -> None:
    grid = build_plan(company, model_key=MODEL_KEY, label="grid", repeats=1, seed=1, official=True)
    with pytest.raises(SweepRefusal, match="awareness"):
        run(company, grid, TextScript(), LocalStore(tmp_path))


# --- the report -------------------------------------------------------------------------------------


def test_the_report_quotes_every_reply_in_full_by_objective_and_template(
    company: Experiment, plan: SweepPlan, tmp_path: Path
) -> None:
    long = (
        "A first sentence.\n\nA second paragraph that is quite a bit longer than the first one is."
    )
    provider = TextScript(lambda n, request: reply(request, f"{long} #{n}"))
    store = LocalStore(tmp_path)
    run(company, plan, provider, store)
    text = awareness_report(store, company, plan)
    assert "Calls recorded: 15 of 15" in text
    for objective in company.objectives:
        assert f"## Objective {objective.id}" in text
    for n in range(1, 16):
        assert (
            f"> A second paragraph that is quite a bit longer than the first one is. #{n}" in text
        )
    assert text.count("### Template") == 15
    assert "none is used to filter or weight any run" in text


def test_the_report_says_which_calls_are_not_recorded(
    company: Experiment, plan: SweepPlan, tmp_path: Path
) -> None:
    provider = TextScript()
    store = LocalStore(tmp_path)
    run(company, plan, provider, store, should_stop=lambda: len(provider.requests) >= 4)
    text = awareness_report(store, company, plan)
    assert "Calls recorded: 4 of 15" in text and text.count("_not recorded_") == 11


def test_the_printed_report_ends_in_exactly_one_newline(
    company: Experiment, plan: SweepPlan, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # The command prints the report into a file; a second trailing newline made the end-of-file hook edit it.
    store = LocalStore(tmp_path)
    run(company, plan, TextScript(), store)
    print(awareness_report(store, company, plan))
    out = capsys.readouterr().out
    assert out.endswith("\n") and not out.endswith("\n\n")


# --- the command ------------------------------------------------------------------------------------


def test_the_command_refuses_a_laptop_run_and_a_dry_run_without_a_tagged_protocol(
    capsys: pytest.CaptureFixture[str],
) -> None:
    common = ["sweep", "awareness", "--experiment", "company", "--model", MODEL_KEY, "--seed", "1"]
    # No prereg.lock exists before the tag, so the gate refuses, which is what the command must say.
    assert cli.main([*common, "--dry-run"]) != 0
    assert "official sweep refused" in capsys.readouterr().err
    assert cli.main([*common, "--store", "local"]) != 0
    assert "refused" in capsys.readouterr().err
