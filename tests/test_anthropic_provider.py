"""The Anthropic provider (Phase 4 code half section 4.9, K6), under the official SDK with a fake transport.
No test here opens a socket, reaches Anthropic or AWS, or spends anything; the key is a made-up string."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx2
import pytest

from fake_anthropic import KEY, MODEL, REQUEST_ID, FakeAnthropic, failure, message, ok
from horizon_compact.model_config import ModelConfig
from horizon_compact.protocol.lock import NOT_SET, THINKING_OFF, model_identity
from horizon_compact.providers.anthropic import (
    BASE_URL,
    SSM_PARAMETER,
    AnthropicKeyError,
    AnthropicProvider,
    read_key,
    ssm_key_fetcher,
)
from horizon_compact.providers.base import (
    DecisionRequest,
    ModelRoute,
    RawDecision,
    TextRequest,
    ToolSpec,
)
from horizon_compact.smoke.record import RedactionError, serialize_safely
from horizon_compact.sweep.classify import classify
from horizon_compact.sweep.store import LocalStore
from sweep_helpers import experiment, make_plan, session, valid_input

ROUTE = ModelRoute("haiku-5-5", MODEL, "anthropic", invoke_id=MODEL, thinking_off=True)
UNSET_ROUTE = ModelRoute("haiku-5-5", MODEL, "anthropic", invoke_id=MODEL)
TOOL = ToolSpec(
    name="submit_decision",
    description="d",
    input_schema={"type": "object", "properties": {"memo": {"type": "string"}}},
)


def request(route: ModelRoute = ROUTE, max_tokens: int = 2048) -> DecisionRequest:
    return DecisionRequest(route, "the system", "the user", TOOL, max_tokens)


def provider(server: FakeAnthropic, **kwargs: Any) -> AnthropicProvider:
    return AnthropicProvider(KEY, http_client=server.client, **kwargs)


def decide(server: FakeAnthropic, req: DecisionRequest | None = None) -> RawDecision:
    return provider(server).decide(req or request())


# --- a normal reply -------------------------------------------------------------------------------------


def test_a_tool_call_comes_back_in_the_shape_the_bedrock_provider_returns() -> None:
    server = FakeAnthropic()
    result = decide(server)
    assert result.status == "ok"
    assert result.stop_reason == "tool_use"
    assert result.tool_call_count == 1
    assert result.tool_calls[0]["name"] == "submit_decision"
    assert result.tool_input == valid_input()
    assert result.text_blocks == []
    assert result.reasoning_block_count == 0
    assert (result.usage.input_tokens, result.usage.output_tokens) == (2400, 500)
    assert classify(result, experiment().scenario).status in ("valid", "valid_rescaled")


def test_the_request_has_exactly_the_approved_fields_and_none_of_the_never_sent_ones() -> None:
    server = FakeAnthropic()
    decide(server)
    body = server.bodies[0]
    assert set(body) == {
        "model",
        "max_tokens",
        "system",
        "messages",
        "tools",
        "tool_choice",
        "thinking",
    }
    assert body["model"] == MODEL and body["max_tokens"] == 2048
    assert body["system"] == "the system"
    assert body["messages"] == [{"role": "user", "content": "the user"}]
    assert body["tool_choice"] == {"type": "auto"}
    assert body["thinking"] == {"type": "disabled"}
    assert [t["name"] for t in body["tools"]] == ["submit_decision"]
    for never in (
        "temperature", "top_p", "top_k", "effort", "output_config", "cache_control", "inference_geo",
        "betas", "fallback_model", "service_tier", "metadata", "stop_sequences",
    ):  # fmt: skip
        assert never not in body, never
    assert "cache_control" not in json.dumps(body)


def test_a_route_that_does_not_turn_thinking_off_sends_no_thinking_field() -> None:
    server = FakeAnthropic()
    result = decide(server, request(UNSET_ROUTE))
    assert "thinking" not in server.bodies[0]
    assert result.provenance.thinking.startswith("not set")


def test_the_body_the_provider_describes_is_the_body_it_sends() -> None:
    server = FakeAnthropic()
    sender = provider(server)
    sender.decide(request())
    assert sender.request_body(request()) == server.bodies[0]


def test_a_text_request_offers_no_tool_and_no_tool_choice() -> None:
    server = FakeAnthropic(
        lambda body: ok(
            message(content=[{"type": "text", "text": "I notice a test."}], stop_reason="end_turn")
        )
    )
    text = TextRequest(ROUTE, "sys", "usr", 300)
    result = provider(server).decide_text(text)
    body = server.bodies[0]
    assert "tools" not in body and "tool_choice" not in body
    assert body["thinking"] == {"type": "disabled"} and body["max_tokens"] == 300
    assert result.text_blocks == ["I notice a test."] and result.stop_reason == "end_turn"
    assert provider(server).text_request_body(text) == body


def test_the_runners_cache_flag_never_becomes_a_cache_point() -> None:
    """The runner marks every request cache_system=True; this route ignores it (decision F)."""
    server = FakeAnthropic()
    base = request()
    flagged = DecisionRequest(base.route, base.system, base.user, TOOL, 10, cache_system=True)
    result = provider(server).decide(flagged)
    assert "cache_control" not in json.dumps(server.bodies[0])
    assert server.bodies[0] == {**provider(server).request_body(base), "max_tokens": 10}
    assert (result.usage.cache_read_tokens, result.usage.cache_write_tokens) == (0, 0)


def test_extra_request_or_response_fields_are_refused_not_quietly_dropped() -> None:
    server = FakeAnthropic()
    sender = provider(server)
    base = request()
    for changed in (
        DecisionRequest(base.route, base.system, base.user, TOOL, 10, additional_fields={"a": 1}),
        DecisionRequest(
            base.route, base.system, base.user, TOOL, 10, additional_response_fields=["/x"]
        ),
    ):
        with pytest.raises(ValueError, match="no extra request or response fields"):
            sender.decide(changed)
    assert server.bodies == []


# --- the client: no retries, no steering from the environment, the key in one header ----------------------


def test_the_sdk_never_retries_underneath_the_harness() -> None:
    server = FakeAnthropic(lambda body: failure(529, "overloaded_error", "Overloaded"))
    result = decide(server)
    assert len(server.bodies) == 1  # one attempt, however retryable
    assert result.status == "api_error"


def test_the_key_travels_in_one_header_and_the_call_goes_where_it_is_told() -> None:
    server = FakeAnthropic()
    decide(server)
    headers = server.headers[0]
    assert headers["x-api-key"] == KEY
    assert server.urls == [f"{BASE_URL}/v1/messages"]
    assert "authorization" not in headers and "anthropic-beta" not in headers
    assert KEY not in json.dumps(server.bodies[0])


def test_the_environment_cannot_redirect_the_call_or_add_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://elsewhere.example")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "a-token-from-the-shell")
    monkeypatch.setenv("ANTHROPIC_CUSTOM_HEADERS", "X-Extra: 1")
    server = FakeAnthropic()
    decide(server)
    assert server.urls == [f"{BASE_URL}/v1/messages"]
    assert "x-extra" not in server.headers[0] and "authorization" not in server.headers[0]
    assert server.headers[0]["x-api-key"] == KEY
    # and the environment is as it was
    assert os.environ["ANTHROPIC_BASE_URL"] == "https://elsewhere.example"
    assert os.environ["ANTHROPIC_CUSTOM_HEADERS"] == "X-Extra: 1"


def test_the_provider_never_shows_its_key() -> None:
    assert KEY not in repr(provider(FakeAnthropic()))


# --- provenance and the raw response ----------------------------------------------------------------------


def test_provenance_names_the_request_the_served_model_and_sets_no_sampling() -> None:
    prov = decide(FakeAnthropic()).provenance
    assert (prov.provider, prov.api, prov.route_kind) == (
        "anthropic",
        "anthropic-messages",
        "anthropic",
    )
    assert prov.model_id == MODEL and prov.max_tokens == 2048
    assert prov.details == {"served_model": MODEL, "request_id": REQUEST_ID}
    assert prov.thinking == THINKING_OFF
    assert prov.temperature.startswith("not set") and prov.latency_ms >= 0


def test_the_raw_response_is_the_servers_bytes_parsed_with_no_field_dropped() -> None:
    payload = message(stop_details=None)
    payload["a_field_the_sdk_does_not_model"] = {"kept": True}
    payload["content"][0]["extra"] = 7
    result = decide(FakeAnthropic(lambda body: ok(payload)))
    assert result.raw_response == payload


# --- stop reasons ----------------------------------------------------------------------------------------


def test_end_turn_and_max_tokens_pass_through_and_the_classifier_reads_them() -> None:
    said = [{"type": "text", "text": "Here is my reasoning."}]
    ended = decide(FakeAnthropic(lambda b: ok(message(content=said, stop_reason="end_turn"))))
    assert ended.stop_reason == "end_turn" and ended.text_blocks == ["Here is my reasoning."]
    assert classify(ended, experiment().scenario).status == "no_tool_call"
    cut = decide(FakeAnthropic(lambda b: ok(message(stop_reason="max_tokens"))))
    assert cut.stop_reason == "max_tokens"
    assert classify(cut, experiment().scenario).status == "truncated"


def test_a_refusal_becomes_the_refusal_the_classifier_already_reads_and_keeps_its_details() -> None:
    details = {"category": "a_policy"}
    reply = message(content=[], stop_reason="refusal", stop_details=details)
    result = decide(FakeAnthropic(lambda body: ok(reply)))
    assert result.status == "ok" and result.stop_reason == "content_filtered"
    assert result.raw_response is not None and result.raw_response["stop_details"] == details
    assert classify(result, experiment().scenario).status == "refusal"


def test_an_unfamiliar_stop_reason_is_passed_through_for_the_classifier_to_flag() -> None:
    result = decide(FakeAnthropic(lambda body: ok(message(stop_reason="pause_turn"))))
    assert result.stop_reason == "pause_turn"
    assert classify(result, experiment().scenario).status == "unexpected_stop"


def test_two_tool_calls_and_thinking_blocks_are_counted() -> None:
    one = message()["content"][0]
    reply = message(content=[{"type": "thinking", "thinking": "", "signature": "x"}, one, one])
    result = decide(FakeAnthropic(lambda body: ok(reply)))
    assert result.tool_call_count == 2 and result.reasoning_block_count == 1
    assert classify(result, experiment().scenario).status == "multiple_calls"


def test_cache_tokens_are_read_from_the_usage() -> None:
    reply = message()
    reply["usage"].update(cache_read_input_tokens=11, cache_creation_input_tokens=7)
    usage = decide(FakeAnthropic(lambda body: ok(reply))).usage
    assert (usage.cache_read_tokens, usage.cache_write_tokens) == (11, 7)


# --- failures are records, on names the classifier knows -------------------------------------------------


@pytest.mark.parametrize(
    ("http", "kind", "code", "retry", "stops"),
    [
        (401, "authentication_error", "AccessDeniedException", "none", True),
        (402, "billing_error", "AccessDeniedException", "none", True),
        (403, "permission_error", "AccessDeniedException", "none", True),
        (404, "not_found_error", "ResourceNotFoundException", "none", True),
        (400, "invalid_request_error", "ValidationException", "none", True),
        (413, "request_too_large", "ValidationException", "none", True),
        (429, "rate_limit_error", "ThrottlingException", "backoff", False),
        (500, "api_error", "InternalServerException", "backoff", False),
        (504, "timeout_error", "ModelTimeoutException", "backoff", False),
        (529, "overloaded_error", "ServiceUnavailableException", "backoff", False),
    ],
)
def test_an_http_failure_is_an_api_error_the_classifier_handles(
    http: int, kind: str, code: str, retry: str, stops: bool
) -> None:
    result = decide(FakeAnthropic(lambda body: failure(http, kind, "no good")))
    assert result.status == "api_error"
    assert result.error == {"code": code, "message": "no good", "http_status": str(http)}
    assert result.provenance.details["request_id"] == REQUEST_ID
    outcome = classify(result, experiment().scenario)
    assert (outcome.retry, outcome.stop_session) == (retry, stops)


@pytest.mark.parametrize(
    ("http", "text"),
    [
        (
            400,
            "You have reached your specified workspace API usage limits. You will regain access on 2026-11-01",
        ),
        (429, "Your organization has reached its monthly spend cap."),
    ],
)
def test_a_reached_spend_limit_stops_the_session_as_a_configuration_error(
    http: int, text: str
) -> None:
    result = decide(FakeAnthropic(lambda body: failure(http, "invalid_request_error", text)))
    assert result.error is not None and result.error["code"] == "SpendLimitReached"
    outcome = classify(result, experiment().scenario)
    assert outcome.status == "config_error" and outcome.stop_session
    assert outcome.retry == "none" and not outcome.is_model_outcome


def test_an_error_message_that_echoes_a_key_is_scrubbed() -> None:
    other = "sk-ant-api03-zzzzzzzzzzzzzzzzzzzzzzzz"
    text = f"bad credential {KEY} and also {other} rejected"
    result = decide(FakeAnthropic(lambda body: failure(401, "authentication_error", text)))
    assert result.error is not None
    shown = json.dumps(result.error)
    assert KEY not in shown and other not in shown and "[key]" in shown


def test_a_reply_that_is_not_json_is_a_server_fault() -> None:
    result = decide(
        FakeAnthropic(lambda body: httpx2.Response(200, content=b"<html>gateway</html>"))
    )
    assert result.error is not None and result.error["code"] == "InternalServerException"


def test_a_connection_that_fails_is_retried_with_backoff() -> None:
    def refuse(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("no route", request=request)

    sender = AnthropicProvider(
        KEY, http_client=httpx2.Client(transport=httpx2.MockTransport(refuse))
    )
    result = sender.decide(request())
    assert result.error is not None and result.error["code"] == "EndpointConnectionError"
    outcome = classify(result, experiment().scenario)
    assert (outcome.retry, outcome.stop_session) == ("backoff", False)


def test_a_server_that_takes_too_long_is_a_timeout() -> None:
    def hang(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ReadTimeout("slow", request=request)

    sender = AnthropicProvider(KEY, http_client=httpx2.Client(transport=httpx2.MockTransport(hang)))
    result = sender.decide(request())
    assert result.error is not None and result.error["code"] == "ReadTimeoutError"
    assert classify(result, experiment().scenario).retry == "backoff"


# --- the key ----------------------------------------------------------------------------------------------


def test_the_key_comes_from_the_environment_first_and_is_not_asked_for() -> None:
    def never() -> str:
        raise AssertionError("prompted although the environment held the key")

    assert read_key({"ANTHROPIC_API_KEY": f"  {KEY}\n"}, never) == KEY


def test_without_the_environment_the_key_is_asked_for() -> None:
    assert read_key({}, lambda: KEY) == KEY


@pytest.mark.parametrize(
    "given", ["", "   ", "sk-or-v1-0123456789abcdef0123456789abcdef", "sk-ant-short"]
)
def test_a_missing_or_misshapen_key_is_refused_and_the_message_never_holds_it(given: str) -> None:
    with pytest.raises(AnthropicKeyError) as caught:
        read_key({}, lambda: given)
    if given.strip():
        assert given.strip() not in str(caught.value)


def test_the_record_writer_refuses_a_record_that_holds_an_anthropic_key() -> None:
    with pytest.raises(RedactionError, match="API key"):
        serialize_safely({"note": f"the key was {KEY}"}, "000000000000")
    serialize_safely({"note": "the key is typed in, never stored"}, "000000000000")


class FakeSsm:
    def __init__(self, value: str = KEY, error: Exception | None = None) -> None:
        self.value, self.error = value, error
        self.calls: list[dict[str, Any]] = []

    def get_parameter(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return {"Parameter": {"Name": kwargs["Name"], "Type": "SecureString", "Value": self.value}}


def test_the_ssm_key_is_read_with_decryption_from_the_one_parameter() -> None:
    ssm = FakeSsm()
    assert read_key({}, lambda: "", ssm_key_fetcher(ssm)) == KEY
    assert ssm.calls == [{"Name": SSM_PARAMETER, "WithDecryption": True}]
    assert SSM_PARAMETER == "/horizon-compact/anthropic-key"


def test_the_environment_beats_ssm_and_ssm_beats_the_prompt() -> None:
    other = "sk-ant-api03-fedcba9876543210fedcba9876543210"
    ssm = FakeSsm(other)
    assert read_key({"ANTHROPIC_API_KEY": KEY}, lambda: "", ssm_key_fetcher(ssm)) == KEY
    assert ssm.calls == []

    def never() -> str:
        raise AssertionError("prompted although SSM held the key")

    assert read_key({}, never, ssm_key_fetcher(FakeSsm(other))) == other


def test_a_misshapen_or_empty_ssm_value_is_refused_and_never_echoed() -> None:
    for value in ("", "   ", "sk-or-v1-this-is-not-an-anthropic-key-at-all", "placeholder"):
        with pytest.raises(AnthropicKeyError) as caught:
            read_key({}, lambda: "", ssm_key_fetcher(FakeSsm(value)))
        if value.strip():
            assert value.strip() not in str(caught.value)


class _AwsError(Exception):
    def __init__(self, code: str, text: str) -> None:
        super().__init__(text)
        self.response = {"Error": {"Code": code, "Message": text}}


def test_an_ssm_failure_names_its_kind_and_code_and_never_a_value() -> None:
    fetch = ssm_key_fetcher(FakeSsm(error=_AwsError("AccessDeniedException", f"nope {KEY}")))
    with pytest.raises(AnthropicKeyError) as caught:
        read_key({}, lambda: "", fetch)
    shown = str(caught.value)
    assert "AccessDeniedException" in shown and SSM_PARAMETER in shown
    assert KEY not in shown and "nope" not in shown
    assert caught.value.__cause__ is None


# --- a whole session, with nothing in the runner or the classifier changed ----------------------------------


def test_a_placeholder_session_runs_end_to_end_and_no_stored_file_holds_the_key(
    tmp_path: Path,
) -> None:
    exp, plan = make_plan("haiku-5-5", repeats=1, seed=3)
    store = LocalStore(tmp_path)
    server = FakeAnthropic()
    result = session(exp, plan, provider(server), store, route=ROUTE)
    assert len(server.bodies) == 5
    assert result.stopped == "complete" and result.clean
    keys = store.list_keys(f"development/placeholder/{plan.sweep_id}/")
    attempts = []
    for stored_key in keys:
        text = store.get(stored_key) or ""
        assert KEY not in text and "sk-ant-" not in text
        if "/attempt-" in stored_key:
            attempts.append(json.loads(text))
    assert len(attempts) == 5
    for attempt in attempts:
        assert attempt["status"] == "valid"
        assert attempt["provider"] == "anthropic" and attempt["route_kind"] == "anthropic"
        assert attempt["request"]["tool_choice"] == {"type": "auto"}
        assert attempt["request"]["thinking"] == {"type": "disabled"}
        assert attempt["provider_details"]["request_id"] == REQUEST_ID


def test_the_cost_is_counted_from_tokens_and_the_prices_in_models_toml(tmp_path: Path) -> None:
    exp, plan = make_plan("haiku-5-5", repeats=1, seed=3)
    result = session(exp, plan, provider(FakeAnthropic()), LocalStore(tmp_path), route=ROUTE)
    per_attempt = round((2400 * 0.10 + 500 * 0.50) / 1_000_000, 6)
    assert result.cost_usd_now == pytest.approx(5 * per_attempt, abs=1e-9)


def test_a_reached_spend_limit_ends_the_session_at_once_and_is_no_models_failure(
    tmp_path: Path,
) -> None:
    exp, plan = make_plan("haiku-5-5", repeats=1, seed=3)
    server = FakeAnthropic(
        lambda body: failure(
            400, "invalid_request_error", "You have reached your specified API usage limits."
        )
    )
    result = session(exp, plan, provider(server), LocalStore(tmp_path), route=ROUTE)
    assert len(server.bodies) == 1
    assert result.stopped == "config_error" and result.runs_finished_now == 0


def test_a_rejected_key_stops_the_session_at_once(tmp_path: Path) -> None:
    exp, plan = make_plan("haiku-5-5", repeats=1, seed=3)
    server = FakeAnthropic(lambda body: failure(401, "authentication_error", "invalid x-api-key"))
    result = session(exp, plan, provider(server), LocalStore(tmp_path), route=ROUTE)
    assert len(server.bodies) == 1 and result.stopped == "config_error"


# --- the model entry, the config rule and the lock --------------------------------------------------------


def test_the_model_entry_is_haiku_5_5_with_thinking_off_and_the_prices_read_on_2026_10_11() -> None:
    config = experiment().model("haiku-5-5")
    assert (config.route, config.model_id, config.thinking) == (
        "anthropic",
        "claude-haiku-5-5",
        "off",
    )
    assert config.role == "development"  # until the protocol names it the main model (build step 9)
    assert config.requests_per_minute <= 600  # far under the 10K requests his Scale tier showed
    assert (config.prices.input, config.prices.output) == (0.10, 0.50)
    assert (config.prices.cache_read, config.prices.cache_write_5m) == (0.01, 0.125)
    assert config.num_ctx is None and config.openrouter_provider is None


def test_thinking_is_refused_on_any_route_but_anthropic() -> None:
    nova = experiment().model("nova-lite")
    with pytest.raises(ValueError, match="thinking is for an anthropic route"):
        ModelConfig.model_validate({**nova.model_dump(), "thinking": "off"})


def test_the_lock_names_thinking_for_haiku_and_leaves_every_other_model_as_it_was() -> None:
    exp = experiment()
    assert model_identity(exp.model("haiku-5-5"))["thinking"] == THINKING_OFF
    assert model_identity(exp.model("haiku-5-5"))["route"] == "anthropic"
    for key in ("sonnet-4-6", "nova-lite", "qwen-local", "gpt-oss-openrouter"):
        assert model_identity(exp.model(key))["thinking"] == NOT_SET
