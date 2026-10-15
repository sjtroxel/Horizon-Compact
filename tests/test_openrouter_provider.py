"""The OpenRouter provider (Phase 2.5 IMPLEMENTATION doc section 17 step 8, item 10), against a stand-in
server on the loopback address. Nothing here reaches a network, a real OpenRouter or AWS, and the key in these
tests is a made-up string."""

from __future__ import annotations

import http.client
import json
import urllib.request
from pathlib import Path
from typing import Any

import pytest

from fake_ollama import dead_url
from fake_openrouter import KEY, MODEL, FakeOpenRouter, completion
from horizon_compact.providers.base import DecisionRequest, ModelRoute, TextRequest, ToolSpec
from horizon_compact.providers.openrouter import (
    SSM_PARAMETER,
    OpenRouterKeyError,
    OpenRouterProvider,
    read_key,
    ssm_key_fetcher,
)
from horizon_compact.smoke.record import RedactionError, serialize_safely
from horizon_compact.sweep.classify import classify
from horizon_compact.sweep.store import LocalStore
from sweep_helpers import experiment, make_plan, session, valid_input

ROUTE = ModelRoute("gpt-oss-openrouter", MODEL, "openrouter", invoke_id=MODEL)
PIN = "deepinfra/bf16"
PINNED = ModelRoute("gpt-oss-openrouter", MODEL, "openrouter", invoke_id=MODEL, pinned_provider=PIN)
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


def test_a_body_that_stops_short_is_an_api_error_the_classifier_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The fault of 2026-10-14: the connection dropped 231 bytes into the reply, and IncompleteRead (an
    # http.client.HTTPException, not an OSError) escaped and ended the session.
    class Dropped:
        def __enter__(self) -> Dropped:
            return self

        def __exit__(self, *exc: object) -> None:
            return None

        def read(self) -> bytes:
            raise http.client.IncompleteRead(b"x" * 231, 4000)

    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: Dropped())
    result = OpenRouterProvider(KEY, DEAD_URL).decide(request())
    assert result.status == "api_error"
    assert result.error is not None and result.error["code"] == "EndpointConnectionError"
    assert "IncompleteRead" in result.error["message"]
    outcome = classify(result, experiment().scenario)
    assert (outcome.retry, outcome.stop_session) == ("backoff", False)


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


def test_the_model_entry_is_the_second_family_with_the_prices_checked_live() -> None:
    config = experiment().model("gpt-oss-openrouter")
    assert (config.route, config.role, config.model_id) == (
        "openrouter",
        "second_family",
        "openai/gpt-oss-120b",
    )
    assert config.num_ctx is None
    assert (
        config.reasoning_effort == "medium"
    )  # section 25: its reasoning cannot be turned off, so it is pinned
    assert (config.prices.input, config.prices.output) == (0.037, 0.17)


# --- the container's route (Phase 4 code half section 4.8): a pinned provider and the key from SSM ---------


def served_by(name: str) -> dict[str, Any]:
    reply = completion()
    reply["provider"] = name
    return reply


def test_a_pinned_route_sends_the_provider_with_fallbacks_off_and_an_unpinned_one_sends_nothing() -> (
    None
):
    with FakeOpenRouter(lambda body: (200, served_by("DeepInfra"))) as server:
        provider = OpenRouterProvider(KEY, server.url)
        provider.decide(DecisionRequest(PINNED, "s", "u", TOOL, 100))
        provider.decide(DecisionRequest(ROUTE, "s", "u", TOOL, 100))
        provider.decide_text(TextRequest(PINNED, "s", "u", 100))
    pinned, unpinned, text = server.bodies
    assert pinned["provider"] == {"order": [PIN], "allow_fallbacks": False}
    assert "provider" not in unpinned
    assert text["provider"] == {"order": [PIN], "allow_fallbacks": False} and "tools" not in text


REASONING = ModelRoute(
    "gpt-oss-openrouter",
    MODEL,
    "openrouter",
    invoke_id=MODEL,
    pinned_provider=PIN,
    reasoning_effort="medium",
)


def test_a_route_with_a_reasoning_level_sends_it_in_both_bodies_and_one_without_sends_nothing() -> (
    None
):
    """Phase 3.5 section 25: the level is sent on the decision body and on the text body (probes)."""
    with FakeOpenRouter(lambda body: (200, served_by("DeepInfra"))) as server:
        provider = OpenRouterProvider(KEY, server.url)
        provider.decide(DecisionRequest(REASONING, "s", "u", TOOL, 100))
        provider.decide(DecisionRequest(PINNED, "s", "u", TOOL, 100))
        provider.decide_text(TextRequest(REASONING, "s", "u", 100))
        provider.decide_text(TextRequest(PINNED, "s", "u", 100))
    decision, plain_decision, text, plain_text = server.bodies
    assert decision["reasoning"] == {"effort": "medium"}
    assert text["reasoning"] == {"effort": "medium"}
    assert "reasoning" not in plain_decision and "reasoning" not in plain_text
    # the pin is still sent beside it
    assert decision["provider"] == {"order": [PIN], "allow_fallbacks": False}


def test_the_record_says_the_level_it_sent_and_otherwise_what_it_always_said() -> None:
    with FakeOpenRouter(lambda body: (200, served_by("DeepInfra"))) as server:
        provider = OpenRouterProvider(KEY, server.url)
        sent = provider.decide(DecisionRequest(REASONING, "s", "u", TOOL, 100)).provenance
        unset = provider.decide(DecisionRequest(PINNED, "s", "u", TOOL, 100)).provenance
    assert sent.thinking == "reasoning effort medium sent"
    assert sent.effort == "medium"
    assert unset.thinking == "not set (the model's default)"
    assert unset.effort == "not set"


def test_the_pinned_body_is_the_body_the_provider_describes_and_holds_no_key() -> None:
    request_ = DecisionRequest(PINNED, "s", "u", TOOL, 100)
    with FakeOpenRouter(lambda body: (200, served_by("DeepInfra"))) as server:
        provider = OpenRouterProvider(KEY, server.url)
        provider.decide(request_)
        assert provider.request_body(request_) == server.bodies[0]
    assert KEY not in json.dumps(provider.request_body(request_))


@pytest.mark.parametrize("name", ["DeepInfra", "deepinfra", "Deep-Infra", "DeepInfra/turbo"])
def test_a_reply_from_the_pinned_provider_is_a_result_however_it_is_spelled(name: str) -> None:
    with FakeOpenRouter(lambda body: (200, served_by(name))) as server:
        result = OpenRouterProvider(KEY, server.url).decide(
            DecisionRequest(PINNED, "s", "u", TOOL, 100)
        )
    assert result.status == "ok" and result.tool_call_count == 1


@pytest.mark.parametrize("name", ["Together", "Test Host", "DeepInfraX", "", "unknown"])
def test_a_reply_from_any_other_provider_is_a_recorded_api_error_never_a_result(name: str) -> None:
    with FakeOpenRouter(lambda body: (200, served_by(name))) as server:
        result = OpenRouterProvider(KEY, server.url).decide(
            DecisionRequest(PINNED, "s", "u", TOOL, 100)
        )
    assert result.status == "api_error"
    assert result.error is not None and result.error["code"] == "ProviderMismatch"
    assert PIN in result.error["message"]
    # the decision is never carried, only the raw reply, as evidence, and its tokens for the cap
    assert (result.tool_calls, result.text_blocks, result.tool_input) == ([], [], None)
    assert result.reasoning_block_count == 0
    assert result.raw_response is not None and result.usage.input_tokens == 2400
    assert result.raw_response["choices"][0]["message"][
        "tool_calls"
    ]  # still there, in the evidence


def test_a_host_whose_name_and_slug_differ_fails_closed() -> None:
    """A known limit: Google's endpoint has the slug ``google-vertex`` and the name ``Google``. The pin and
    the reply never match, so the call is refused, never counted. Check each host before pinning it."""
    route = ModelRoute(
        "m", MODEL, "openrouter", invoke_id=MODEL, pinned_provider="google-vertex/global"
    )
    with FakeOpenRouter(lambda body: (200, served_by("Google"))) as server:
        result = OpenRouterProvider(KEY, server.url).decide(
            DecisionRequest(route, "s", "u", TOOL, 100)
        )
    assert result.status == "api_error" and result.error is not None
    assert result.error["code"] == "ProviderMismatch"


def test_a_missing_provider_in_the_reply_is_a_mismatch_not_a_pass() -> None:
    reply = completion()
    del reply["provider"]
    with FakeOpenRouter(lambda body: (200, reply)) as server:
        result = OpenRouterProvider(KEY, server.url).decide(
            DecisionRequest(PINNED, "s", "u", TOOL, 100)
        )
    assert result.status == "api_error" and result.error is not None
    assert result.error["code"] == "ProviderMismatch"


def test_a_provider_mismatch_stops_the_session_and_its_cost_still_counts(tmp_path: Path) -> None:
    exp, plan = make_plan("gpt-oss-openrouter", repeats=1, seed=3)
    store = LocalStore(tmp_path)
    with FakeOpenRouter(lambda body: (200, served_by("Together"))) as server:
        result = session(exp, plan, OpenRouterProvider(KEY, server.url), store, route=PINNED)
        assert (
            len(server.bodies) == 1
        )  # one call, then the session stops: no retry onto the wrong backend
    assert result.stopped == "config_error" and result.runs_finished_now == 0
    attempts = [
        json.loads(store.get(k) or "")
        for k in store.list_keys(f"development/placeholder/{plan.sweep_id}/")
        if "/attempt-" in k
    ]
    assert len(attempts) == 1
    assert attempts[0]["status"] == "config_error" and "ProviderMismatch" in attempts[0]["detail"]
    assert attempts[0]["parsed_decision"] is None and attempts[0]["tool_calls"] == []
    assert attempts[0]["text_blocks"] == [] and attempts[0]["validation"] is None
    assert attempts[0]["cost_usd"] > 0 and attempts[0]["raw_response"] is not None
    assert KEY not in json.dumps(attempts[0])


def test_the_pinned_session_runs_end_to_end_and_records_the_pinned_body(tmp_path: Path) -> None:
    exp, plan = make_plan("gpt-oss-openrouter", repeats=1, seed=3)
    store = LocalStore(tmp_path)
    with FakeOpenRouter(lambda body: (200, served_by("DeepInfra"))) as server:
        result = session(exp, plan, OpenRouterProvider(KEY, server.url), store, route=PINNED)
    assert result.stopped == "complete" and result.runs_finished_now == 5
    for stored_key in store.list_keys(f"development/placeholder/{plan.sweep_id}/"):
        text = store.get(stored_key) or ""
        assert KEY not in text
        if "/attempt-" in stored_key:
            attempt = json.loads(text)
            assert attempt["request"]["provider"] == {"order": [PIN], "allow_fallbacks": False}
            assert attempt["provider_details"]["served_by"] == "DeepInfra"


class FakeSsm:
    """An ``ssm`` client that answers ``get_parameter`` with ``value`` or raises ``error``."""

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
    assert SSM_PARAMETER == "/horizon-compact/openrouter-key"


def test_the_environment_beats_ssm_and_ssm_beats_the_prompt() -> None:
    other = "sk-or-v1-fedcba9876543210fedcba9876543210"
    ssm = FakeSsm(other)
    assert read_key({"OPENROUTER_API_KEY": KEY}, lambda: "", ssm_key_fetcher(ssm)) == KEY
    assert ssm.calls == []  # not even asked

    def never() -> str:
        raise AssertionError("prompted although SSM held the key")

    assert read_key({}, never, ssm_key_fetcher(FakeSsm(other))) == other


def test_a_misshapen_or_empty_ssm_value_is_refused_and_never_echoed() -> None:
    for value in ("", "   ", "sk-ant-api03-this-is-not-an-openrouter-key", "placeholder"):
        with pytest.raises(OpenRouterKeyError) as caught:
            read_key({}, lambda: "", ssm_key_fetcher(FakeSsm(value)))
        if value.strip():
            assert value.strip() not in str(caught.value)


class _AwsError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.response = {"Error": {"Code": code, "Message": message}}


def test_an_ssm_failure_names_its_kind_and_code_and_never_a_value() -> None:
    fetch = ssm_key_fetcher(FakeSsm(error=_AwsError("AccessDeniedException", f"nope {KEY}")))
    with pytest.raises(OpenRouterKeyError) as caught:
        read_key({}, lambda: "", fetch)
    message = str(caught.value)
    assert "AccessDeniedException" in message and SSM_PARAMETER in message
    assert KEY not in message and "nope" not in message  # the AWS message could hold anything
    assert caught.value.__cause__ is None  # no chained exception that a traceback would print


def test_a_malformed_ssm_reply_is_refused_without_a_traceback_holding_the_value() -> None:
    class Odd:
        def get_parameter(self, **kwargs: Any) -> dict[str, Any]:
            return {"unexpected": KEY}

    with pytest.raises(OpenRouterKeyError) as caught:
        read_key({}, lambda: "", ssm_key_fetcher(Odd()))
    assert KEY not in str(caught.value) and caught.value.__cause__ is None
