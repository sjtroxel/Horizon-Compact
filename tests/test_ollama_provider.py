"""The Ollama provider (Phase 2.5 IMPLEMENTATION doc section 8.6), against a stand-in server on the loopback
address. Nothing here reaches a network, a real Ollama or AWS."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from fake_ollama import DIGEST, MODEL, FakeOllama, chat_reply, dead_url
from horizon_compact.providers.base import DecisionRequest, ModelRoute, ToolSpec, prompt_sha256
from horizon_compact.providers.ollama import OllamaProvider
from horizon_compact.smoke.record import serialize_safely
from horizon_compact.sweep.classify import classify
from horizon_compact.sweep.prompt import build_tool
from horizon_compact.sweep.store import LocalStore
from sweep_helpers import ScriptedProvider, experiment, make_plan, session, valid_input

LOCAL_ROUTE = ModelRoute("qwen-local", MODEL, "local", invoke_id=MODEL)
TOOL = ToolSpec(
    name="submit_decision",
    description="d",
    input_schema={"type": "object", "properties": {"memo": {"type": "string"}}},
)
DEAD_URL = dead_url()  # a closed loopback port


def request(max_tokens: int = 2048) -> DecisionRequest:
    return DecisionRequest(LOCAL_ROUTE, "the system", "the user", TOOL, max_tokens)


def decide(server: FakeOllama, *, num_ctx: int = 16384, req: DecisionRequest | None = None) -> Any:
    return OllamaProvider(server.url, num_ctx).decide(req or request())


# --- a normal reply -------------------------------------------------------------------------------


def test_a_tool_call_comes_back_in_the_shape_the_bedrock_provider_returns() -> None:
    with FakeOllama() as server:
        result = decide(server)
    assert result.status == "ok"
    assert result.stop_reason == "tool_use"
    assert result.tool_call_count == 1
    assert result.tool_calls[0]["name"] == "submit_decision"
    assert result.tool_input == valid_input()  # a real object, not a string
    assert result.text_blocks == []
    assert result.reasoning_block_count == 0
    assert (result.usage.input_tokens, result.usage.output_tokens) == (2243, 430)
    assert (result.usage.cache_read_tokens, result.usage.cache_write_tokens) == (0, 0)


def test_the_request_carries_no_sampling_option_and_sets_the_window_and_the_thinking_switch() -> (
    None
):
    with FakeOllama() as server:
        decide(server, num_ctx=12345, req=request(max_tokens=777))
        body = server.chat_bodies[0]
    assert body["model"] == MODEL
    assert body["stream"] is False
    assert body["think"] is False
    assert body["options"] == {"num_ctx": 12345, "num_predict": 777}
    for sampling in ("temperature", "top_p", "top_k", "seed", "presence_penalty", "repeat_penalty"):
        assert sampling not in body
        assert sampling not in body["options"]
    assert body["messages"] == [
        {"role": "system", "content": "the system"},
        {"role": "user", "content": "the user"},
    ]
    assert [t["function"]["name"] for t in body["tools"]] == ["submit_decision"]
    assert (
        "tool_choice" not in body
    )  # Ollama has none: the model may answer in text, which is `auto`


def test_the_body_the_provider_describes_is_the_body_it_sends() -> None:
    with FakeOllama() as server:
        provider = OllamaProvider(server.url, 16384)
        provider.decide(request())
        assert provider.request_body(request()) == server.chat_bodies[0]


def test_provenance_names_the_runtime_the_digest_the_window_and_the_models_own_defaults() -> None:
    with FakeOllama() as server:
        result = decide(server)
    prov = result.provenance
    assert (prov.provider, prov.api, prov.route_kind, prov.region) == (
        "ollama",
        "ollama-chat",
        "local",
        "local",
    )
    assert prov.inference_profile is None
    assert prov.thinking == "off (think=false)"
    assert prov.temperature.startswith("not set; the model's own defaults: ")
    assert "temperature 1" in prov.temperature and "top_k 20" in prov.temperature
    assert prov.details["ollama_version"] == "0.35.1"
    assert prov.details["model_digest"] == DIGEST
    assert (prov.details["num_ctx"], prov.details["num_predict"]) == ("16384", "2048")
    assert prov.prompt_sha256 == prompt_sha256(request())  # one prompt, one hash, on any provider


def test_the_runtime_is_asked_about_the_model_once_not_on_every_call() -> None:
    with FakeOllama() as server:
        provider = OllamaProvider(server.url, 16384)
        provider.decide(request())
        provider.decide(request())
        assert server.paths.count("/api/version") == 1
        assert server.paths.count("/api/chat") == 2


# --- what is not a clean tool call ----------------------------------------------------------------


def test_text_without_a_tool_call_is_end_turn_and_the_classifier_calls_it_no_tool_call() -> None:
    reply = chat_reply(tool_calls=[], content="I would rather not allocate this.")
    with FakeOllama(lambda body: (200, reply)) as server:
        result = decide(server)
    assert result.stop_reason == "end_turn"
    assert result.tool_calls == []
    assert result.text_blocks == ["I would rather not allocate this."]
    outcome = classify(result, experiment().scenario)
    assert outcome.status == "no_tool_call" and outcome.retry == "model"


def test_done_reason_length_is_a_truncation() -> None:
    with FakeOllama(lambda body: (200, chat_reply(done_reason="length", tool_calls=[]))) as server:
        result = decide(server)
    assert result.stop_reason == "max_tokens"
    assert classify(result, experiment().scenario).status == "truncated"


def test_an_unfamiliar_done_reason_is_passed_through_for_the_classifier_to_flag() -> None:
    with FakeOllama(lambda body: (200, chat_reply(done_reason="load"))) as server:
        result = decide(server)
    assert result.stop_reason == "load"
    assert classify(result, experiment().scenario).status == "unexpected_stop"


def test_two_tool_calls_are_two_calls() -> None:
    call = {"function": {"name": "submit_decision", "arguments": valid_input()}}
    with FakeOllama(lambda body: (200, chat_reply(tool_calls=[call, call]))) as server:
        result = decide(server)
    assert result.tool_call_count == 2
    assert classify(result, experiment().scenario).status == "multiple_calls"


def test_arguments_sent_as_a_json_string_are_parsed_and_an_unparseable_string_is_kept() -> None:
    as_string = {"function": {"name": "submit_decision", "arguments": json.dumps(valid_input())}}
    broken = {"function": {"name": "submit_decision", "arguments": "{not json"}}
    with FakeOllama(lambda body: (200, chat_reply(tool_calls=[as_string]))) as server:
        assert decide(server).tool_input == valid_input()
    with FakeOllama(lambda body: (200, chat_reply(tool_calls=[broken]))) as server:
        result = decide(server)
    assert result.tool_input == "{not json"
    assert classify(result, experiment().scenario).status == "schema_invalid"


def test_a_thinking_block_is_counted_even_though_it_is_switched_off() -> None:
    with FakeOllama(lambda body: (200, chat_reply(thinking="let me see"))) as server:
        assert decide(server).reasoning_block_count == 1


# --- durations ------------------------------------------------------------------------------------


def test_nanosecond_durations_are_stored_as_milliseconds_and_nothing_else_changes() -> None:
    with FakeOllama(lambda body: (200, chat_reply(total_duration=150_000_000_000))) as server:
        result = decide(server)
    stored = result.raw_response
    assert stored["total_duration_ms"] == 150_000.0
    assert stored["load_duration_ms"] == 11_000.0
    assert "total_duration" not in stored and "load_duration" not in stored
    assert stored["prompt_eval_count"] == 2243 and stored["done_reason"] == "stop"
    assert stored["model"] == MODEL


def test_a_call_over_a_hundred_seconds_still_makes_a_record_the_writer_accepts() -> None:
    """A raw 150-second duration is a 12-digit number, which the record writer refuses as a possible account
    id. The conversion exists so a slow call cannot crash a sweep."""
    with FakeOllama(lambda body: (200, chat_reply(total_duration=150_000_000_000))) as server:
        result = decide(server)
    text = serialize_safely({"raw_response": result.raw_response}, "000000000000")
    assert "total_duration_ms" in text
    with pytest.raises(Exception, match="12-digit"):
        serialize_safely({"raw": {"total_duration": 150_000_000_000}}, "000000000000")


# --- failures are records, never exceptions -------------------------------------------------------


def test_a_server_that_is_not_there_is_an_api_error_the_classifier_retries_with_backoff() -> None:
    result = OllamaProvider(DEAD_URL, 16384).decide(request())
    assert result.status == "api_error"
    assert result.error is not None and result.error["code"] == "EndpointConnectionError"
    assert result.provenance.details["ollama_version"] == "unknown"
    outcome = classify(result, experiment().scenario)
    assert outcome.status == "api_error" and outcome.retry == "backoff"


def test_the_details_are_read_again_once_the_server_is_there() -> None:
    provider = OllamaProvider(DEAD_URL, 16384)
    assert provider.decide(request()).provenance.details["model_digest"] == "unknown"
    with FakeOllama() as server:
        provider._url = server.url  # the same provider, now pointed at a live server
        assert provider.decide(request()).provenance.details["model_digest"] == DIGEST


def test_an_unparseable_tool_call_is_a_model_outcome_retried_and_counted() -> None:
    reply = (500, {"error": "error parsing tool call: raw='{\"amounts\": '"})
    with FakeOllama(lambda body: reply) as server:
        result = decide(server)
    assert result.error is not None
    assert (result.error["code"], result.error["http_status"]) == ("ModelErrorException", "500")
    outcome = classify(result, experiment().scenario)
    assert outcome.status == "malformed_tool_use" and outcome.retry == "model"


def test_a_missing_model_stops_the_session_and_a_server_fault_is_retried() -> None:
    with FakeOllama(lambda body: (404, {"error": "model 'nope' not found"})) as server:
        missing = decide(server)
    assert missing.error is not None and missing.error["code"] == "ResourceNotFoundException"
    assert classify(missing, experiment().scenario).stop_session is True
    with FakeOllama(lambda body: (503, {"error": "overloaded"})) as server:
        busy = decide(server)
    assert busy.error is not None and busy.error["code"] == "InternalServerException"
    assert classify(busy, experiment().scenario).retry == "backoff"


def test_a_reply_that_is_not_json_is_a_server_fault() -> None:
    with FakeOllama(lambda body: (200, b"<html>not json</html>")) as server:
        result = decide(server)
    assert result.status == "api_error"
    assert result.error is not None and result.error["code"] == "InternalServerException"


def test_a_server_that_takes_too_long_is_a_timeout() -> None:
    with FakeOllama(delay=1.0) as server:
        result = OllamaProvider(server.url, 16384, timeout=0.2).decide(request())
    assert result.status == "api_error"
    assert result.error is not None and result.error["code"] == "ReadTimeoutError"
    assert classify(result, experiment().scenario).retry == "backoff"


# --- a whole session, with nothing in the runner or the classifier changed ------------------------


def test_a_placeholder_session_runs_end_to_end_against_the_stand_in(tmp_path: Path) -> None:
    exp, plan = make_plan("qwen-local", repeats=1, seed=3)
    store = LocalStore(tmp_path)
    with FakeOllama() as server:
        provider = OllamaProvider(server.url, 16384)
        result = session(exp, plan, provider, store, route=LOCAL_ROUTE)
        assert len(server.chat_bodies) == 5
    assert result.stopped == "complete" and result.clean
    assert (result.runs_total, result.runs_finished_now) == (5, 5)
    assert result.cost_usd_now == 0.0  # prices are zero
    keys = store.list_keys(f"development/placeholder/{plan.sweep_id}/")
    attempts = [json.loads(store.get(k) or "{}") for k in keys if "/attempt-" in k]
    assert len(attempts) == 5
    for attempt in attempts:
        assert attempt["status"] == "valid"
        assert attempt["provider"] == "ollama" and attempt["route_kind"] == "local"
        assert attempt["provider_details"]["model_digest"] == DIGEST
        assert (
            attempt["request"]["options"]["num_ctx"] == 16384
        )  # the stored request is the Ollama one
        assert "toolConfig" not in attempt["request"]
        assert attempt["raw_response"]["total_duration_ms"] == 20_600.0
        assert attempt["usage"]["input_tokens"] == 2243


def test_a_dead_server_ends_the_session_as_api_errors_instead_of_crashing(tmp_path: Path) -> None:
    exp, plan = make_plan("qwen-local", repeats=1, seed=3)
    store = LocalStore(tmp_path)
    result = session(exp, plan, OllamaProvider(DEAD_URL, 16384), store, route=LOCAL_ROUTE)
    assert result.stopped == "api_errors"
    assert result.runs_finished_now == 0


def test_a_local_model_is_the_development_model_and_the_tool_is_the_same_one() -> None:
    config = experiment().model("qwen-local")
    assert (config.route, config.role, config.num_ctx) == ("local", "development", 16384)
    assert (config.prices.input, config.prices.output) == (0.0, 0.0)
    assert build_tool(experiment().scenario).name == "submit_decision"
    assert (
        ScriptedProvider().name == "fake"
    )  # the seam is a protocol: any provider with these methods fits
