"""The OpenRouter provider (Phase 2.5 IMPLEMENTATION doc section 17 step 8, item 10), against a stand-in
server on the loopback address. Nothing here reaches a network, a real OpenRouter or AWS, and the key in these
tests is a made-up string."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from fake_ollama import dead_url
from fake_openrouter import KEY, MODEL, FakeOpenRouter, completion
from horizon_compact.providers.base import DecisionRequest, ModelRoute, ToolSpec
from horizon_compact.providers.openrouter import (
    OpenRouterKeyError,
    OpenRouterProvider,
    read_key,
)
from horizon_compact.smoke.record import RedactionError, serialize_safely
from horizon_compact.sweep.classify import classify
from horizon_compact.sweep.store import LocalStore
from sweep_helpers import experiment, make_plan, session, valid_input

ROUTE = ModelRoute("gpt-oss-openrouter", MODEL, "openrouter", invoke_id=MODEL)
TOOL = ToolSpec(
    name="submit_decision",
    description="d",
    input_schema={"type": "object", "properties": {"memo": {"type": "string"}}},
)
DEAD_URL = dead_url() + "/api/v1/chat/completions"


def request(max_tokens: int = 2048) -> DecisionRequest:
    return DecisionRequest(ROUTE, "the system", "the user", TOOL, max_tokens)


def decide(server: FakeOpenRouter, req: DecisionRequest | None = None) -> Any:
    return OpenRouterProvider(KEY, server.url).decide(req or request())


# --- a normal reply -------------------------------------------------------------------------------


def test_a_tool_call_comes_back_in_the_shape_the_bedrock_provider_returns() -> None:
    with FakeOpenRouter() as server:
        result = decide(server)
    assert result.status == "ok"
    assert result.stop_reason == "tool_use"
    assert result.tool_call_count == 1
    assert result.tool_calls[0]["name"] == "submit_decision"
    assert result.tool_input == valid_input()  # parsed from a JSON string into an object
    assert result.text_blocks == []
    assert result.reasoning_block_count == 0
    assert (result.usage.input_tokens, result.usage.output_tokens) == (2400, 500)
    assert (result.usage.cache_read_tokens, result.usage.cache_write_tokens) == (0, 0)


def test_the_request_is_the_one_tool_with_auto_choice_and_no_sampling_option() -> None:
    with FakeOpenRouter() as server:
        decide(server, request(max_tokens=777))
        body = server.bodies[0]
        assert server.paths == ["/api/v1/chat/completions"]
    assert set(body) == {"model", "messages", "tools", "tool_choice", "max_tokens", "usage"}
    assert body["model"] == MODEL
    assert body["tool_choice"] == "auto"
    assert body["max_tokens"] == 777
    assert body["usage"] == {"include": True}
    for sampling in (
        "temperature",
        "top_p",
        "top_k",
        "seed",
        "presence_penalty",
        "frequency_penalty",
    ):
        assert sampling not in body
    assert body["messages"] == [
        {"role": "system", "content": "the system"},
        {"role": "user", "content": "the user"},
    ]
    assert [t["function"]["name"] for t in body["tools"]] == ["submit_decision"]


def test_the_key_travels_in_the_header_only_and_never_in_the_body_or_the_stored_request() -> None:
    with FakeOpenRouter() as server:
        provider = OpenRouterProvider(KEY, server.url)
        result = provider.decide(request())
        assert server.authorizations == [f"Bearer {KEY}"]
        assert KEY not in json.dumps(server.bodies[0])
    assert KEY not in json.dumps(provider.request_body(request()))
    assert KEY not in repr(provider)
    assert KEY not in json.dumps(result.raw_response)
    assert KEY not in repr(result.provenance)


def test_the_body_the_provider_describes_is_the_body_it_sends() -> None:
    with FakeOpenRouter() as server:
        provider = OpenRouterProvider(KEY, server.url)
        provider.decide(request())
        assert provider.request_body(request()) == server.bodies[0]


def test_provenance_names_the_served_model_and_the_host_and_sets_no_sampling() -> None:
    with FakeOpenRouter() as server:
        prov = decide(server).provenance
    assert (prov.provider, prov.api, prov.route_kind) == (
        "openrouter",
        "openrouter-chat-completions",
        "openrouter",
    )
    assert prov.model_id == MODEL
    assert prov.details == {
        "served_model": MODEL,
        "served_by": "Test Host",
        "generation_id": "gen-test-abc",
    }
    assert prov.temperature.startswith("not set")
    assert prov.max_tokens == 2048
    assert prov.latency_ms >= 0


def test_the_cost_openrouter_reports_is_kept_in_the_stored_response() -> None:
    with FakeOpenRouter() as server:
        result = decide(server)
    assert result.raw_response["usage"]["cost"] == 0.000123


# --- other endings -----------------------------------------------------------------------------------


def test_text_without_a_tool_call_is_end_turn_and_the_classifier_calls_it_no_tool_call() -> None:
    reply = completion(tool_calls=[], finish_reason="stop", content="I would rather not say.")
    with FakeOpenRouter(lambda body: (200, reply)) as server:
        result = decide(server)
    assert (result.stop_reason, result.tool_call_count) == ("end_turn", 0)
    assert result.text_blocks == ["I would rather not say."]
    assert classify(result, experiment().scenario).status == "no_tool_call"


def test_finish_reason_length_is_a_truncation() -> None:
    reply = completion(tool_calls=[], finish_reason="length", content="")
    with FakeOpenRouter(lambda body: (200, reply)) as server:
        result = decide(server)
    assert result.stop_reason == "max_tokens"
    assert classify(result, experiment().scenario).status == "truncated"


def test_a_content_filter_ending_is_the_classifiers_refusal_and_stop_is_a_tool_use() -> None:
    reply = completion(tool_calls=[], finish_reason="content_filter")
    with FakeOpenRouter(lambda body: (200, reply)) as server:
        assert decide(server).stop_reason == "content_filtered"
    with FakeOpenRouter(lambda body: (200, completion(finish_reason="stop"))) as server:
        assert decide(server).stop_reason == "tool_use"  # some hosts say stop after a tool call


def test_an_unfamiliar_finish_reason_is_passed_through_for_the_classifier_to_flag() -> None:
    with FakeOpenRouter(lambda body: (200, completion(finish_reason="error"))) as server:
        result = decide(server)
    assert result.stop_reason == "error"
    assert classify(result, experiment().scenario).status == "unexpected_stop"


def test_two_tool_calls_are_two_calls_and_a_reasoning_block_is_counted() -> None:
    one = completion()["choices"][0]["message"]["tool_calls"][0]
    reply = completion(tool_calls=[one, one], reasoning="thinking about it")
    with FakeOpenRouter(lambda body: (200, reply)) as server:
        result = decide(server)
    assert result.tool_call_count == 2
    assert result.reasoning_block_count == 1
    assert classify(result, experiment().scenario).status == "multiple_calls"


def test_arguments_that_are_not_json_are_kept_as_the_string_for_the_validator() -> None:
    reply = completion("{not json")
    with FakeOpenRouter(lambda body: (200, reply)) as server:
        result = decide(server)
    assert result.tool_input == "{not json"
    assert classify(result, experiment().scenario).status == "schema_invalid"


# --- failures are records, on names the classifier knows ------------------------------------------------


@pytest.mark.parametrize(
    ("http", "code", "retry", "stops"),
    [
        (401, "AccessDeniedException", "none", True),
        (402, "AccessDeniedException", "none", True),
        (403, "AccessDeniedException", "none", True),
        (404, "ResourceNotFoundException", "none", True),
        (400, "ValidationException", "none", True),
        (429, "ThrottlingException", "backoff", False),
        (502, "ServiceUnavailableException", "backoff", False),
        (503, "ServiceUnavailableException", "backoff", False),
        (504, "ModelTimeoutException", "backoff", False),
        (500, "InternalServerException", "backoff", False),
    ],
)
def test_an_http_failure_is_an_api_error_the_classifier_handles(
    http: int, code: str, retry: str, stops: bool
) -> None:
    payload = {"error": {"code": http, "message": "no good"}}
    with FakeOpenRouter(lambda body: (http, payload)) as server:
        result = decide(server)
    assert result.status == "api_error"
    assert result.error == {"code": code, "message": "no good", "http_status": str(http)}
    outcome = classify(result, experiment().scenario)
    assert (outcome.retry, outcome.stop_session) == (retry, stops)


def test_a_daily_limit_stops_the_session_instead_of_retrying() -> None:
    payload = {
        "error": {
            "code": 429,
            "message": "Rate limit exceeded: free-models-per-day. Add credits to unlock more requests per day",
        }
    }
    with FakeOpenRouter(lambda body: (429, payload)) as server:
        outcome = classify(decide(server), experiment().scenario)
    assert outcome.stop_session and outcome.stop_as == "quota_exhausted"


def test_a_failure_in_the_body_of_a_200_is_still_an_api_error() -> None:
    payload = {"error": {"code": 502, "message": "upstream down"}}
    with FakeOpenRouter(lambda body: (200, payload)) as server:
        result = decide(server)
    assert result.status == "api_error"
    assert result.error is not None and result.error["code"] == "ServiceUnavailableException"


def test_an_error_message_that_echoes_the_key_is_scrubbed() -> None:
    payload = {"error": {"code": 401, "message": f"bad credential {KEY} rejected"}}
    with FakeOpenRouter(lambda body: (401, payload)) as server:
        result = decide(server)
    assert result.error is not None
    assert KEY not in json.dumps(result.error)
    assert "[key]" in result.error["message"]


def test_a_reply_that_is_not_json_is_a_server_fault() -> None:
    with FakeOpenRouter(lambda body: (200, b"<html>gateway</html>")) as server:
        result = decide(server)
    assert result.error is not None and result.error["code"] == "InternalServerException"


def test_a_server_that_is_not_there_is_an_api_error_the_classifier_retries_with_backoff() -> None:
    result = OpenRouterProvider(KEY, DEAD_URL).decide(request())
    assert result.status == "api_error"
    outcome = classify(result, experiment().scenario)
    assert (outcome.retry, outcome.stop_session) == ("backoff", False)


def test_a_server_that_takes_too_long_is_a_timeout() -> None:
    with FakeOpenRouter(delay=0.5) as server:
        result = OpenRouterProvider(KEY, server.url, timeout=0.1).decide(request())
    assert result.error is not None and result.error["code"] == "ReadTimeoutError"


# --- the key --------------------------------------------------------------------------------------------


def test_the_key_comes_from_the_environment_first_and_is_not_asked_for() -> None:
    def never() -> str:
        raise AssertionError("asked for a key that the environment already holds")

    assert read_key({"OPENROUTER_API_KEY": f"  {KEY}  "}, never) == KEY


def test_without_the_environment_the_key_is_asked_for() -> None:
    assert read_key({}, lambda: f"{KEY}\n") == KEY


@pytest.mark.parametrize(
    "given", ["", "   ", "sk-ant-api03-notopenrouter0000000", "sk-or-short", "hello"]
)
def test_a_missing_or_misshapen_key_is_refused_and_the_message_never_holds_it(given: str) -> None:
    with pytest.raises(OpenRouterKeyError) as caught:
        read_key({}, lambda: given)
    if given.strip():
        assert given.strip() not in str(caught.value)
    assert "nothing was sent" in str(caught.value) or "no key" in str(caught.value)


def test_the_record_writer_refuses_a_record_that_holds_a_key() -> None:
    with pytest.raises(RedactionError, match="API key"):
        serialize_safely({"note": f"the key was {KEY}"}, "000000000000")
    serialize_safely({"note": "the key is typed in, never stored"}, "000000000000")


# --- a whole session, with nothing in the runner or the classifier changed ----------------------------


def test_a_placeholder_session_runs_end_to_end_and_no_stored_file_holds_the_key(
    tmp_path: Path,
) -> None:
    exp, plan = make_plan("gpt-oss-openrouter", repeats=1, seed=3)
    store = LocalStore(tmp_path)
    with FakeOpenRouter() as server:
        provider = OpenRouterProvider(KEY, server.url)
        result = session(exp, plan, provider, store, route=ROUTE)
        assert len(server.bodies) == 5
    assert result.stopped == "complete" and result.clean
    assert (result.runs_total, result.runs_finished_now) == (5, 5)
    keys = store.list_keys(f"development/placeholder/{plan.sweep_id}/")
    assert keys
    attempts = []
    for stored_key in keys:
        text = store.get(stored_key) or ""
        assert KEY not in text
        assert "sk-or-" not in text
        if "/attempt-" in stored_key:
            attempts.append(json.loads(text))
    assert len(attempts) == 5
    for attempt in attempts:
        assert attempt["status"] == "valid"
        assert attempt["provider"] == "openrouter" and attempt["route_kind"] == "openrouter"
        assert attempt["provider_details"]["served_by"] == "Test Host"
        assert attempt["request"]["tool_choice"] == "auto"
        assert "toolConfig" not in attempt["request"]
        assert attempt["usage"]["input_tokens"] == 2400


def test_the_cost_is_counted_from_tokens_and_the_prices_in_models_toml(tmp_path: Path) -> None:
    exp, plan = make_plan("gpt-oss-openrouter", repeats=1, seed=3)
    with FakeOpenRouter() as server:
        result = session(
            exp, plan, OpenRouterProvider(KEY, server.url), LocalStore(tmp_path), route=ROUTE
        )
    # Each attempt: 2,400 in x $0.037 + 500 out x $0.17 per million tokens, to a millionth of a dollar.
    per_attempt = round((2400 * 0.037 + 500 * 0.17) / 1_000_000, 6)
    assert result.cost_usd_now == pytest.approx(5 * per_attempt, abs=1e-9)


def test_a_dead_server_ends_the_session_as_api_errors_instead_of_crashing(tmp_path: Path) -> None:
    exp, plan = make_plan("gpt-oss-openrouter", repeats=1, seed=3)
    result = session(
        exp, plan, OpenRouterProvider(KEY, DEAD_URL), LocalStore(tmp_path), route=ROUTE
    )
    assert result.stopped == "api_errors"
    assert result.runs_finished_now == 0


def test_a_rejected_key_stops_the_session_at_once(tmp_path: Path) -> None:
    exp, plan = make_plan("gpt-oss-openrouter", repeats=1, seed=3)
    payload = {"error": {"code": 401, "message": "User not found."}}
    with FakeOpenRouter(lambda body: (401, payload)) as server:
        result = session(
            exp, plan, OpenRouterProvider(KEY, server.url), LocalStore(tmp_path), route=ROUTE
        )
        assert len(server.bodies) == 1
    assert result.stopped == "config_error"


def test_the_model_entry_is_the_development_model_with_the_prices_checked_live() -> None:
    config = experiment().model("gpt-oss-openrouter")
    assert (config.route, config.role, config.model_id) == (
        "openrouter",
        "development",
        "openai/gpt-oss-120b",
    )
    assert config.num_ctx is None
    assert (config.prices.input, config.prices.output) == (0.037, 0.17)
