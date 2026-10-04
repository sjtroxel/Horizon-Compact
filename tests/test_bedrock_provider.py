"""The Bedrock Converse provider against botocore's Stubber: no network, no credentials."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import boto3
import pytest
from botocore.stub import Stubber

from horizon_compact.providers.base import DecisionRequest, ModelRoute, ToolSpec
from horizon_compact.providers.bedrock import BedrockConverseProvider, build_request, prompt_sha256

TOOL = ToolSpec(
    name="record_thing",
    description="Records a thing.",
    input_schema={"type": "object", "properties": {"n": {"type": "number"}}, "required": ["n"]},
)
ROUTE = ModelRoute(
    "m", "anthropic.claude-sonnet-4-6", "geo_profile", invoke_id="us.example-profile"
)


def make_request(**kwargs: Any) -> DecisionRequest:
    defaults: dict[str, Any] = {
        "route": ROUTE,
        "system": "sys",
        "user": "usr",
        "tool": TOOL,
        "max_tokens": 256,
    }
    return DecisionRequest(**{**defaults, **kwargs})


def response(content: list[dict[str, Any]], stop: str = "tool_use", **usage: int) -> dict[str, Any]:
    return {
        "output": {"message": {"role": "assistant", "content": content}},
        "stopReason": stop,
        "usage": {"inputTokens": 10, "outputTokens": 5, "totalTokens": 15, **usage},
        "metrics": {"latencyMs": 100},
    }


def tool_use(tool_id: str = "t1", n: float = 1) -> dict[str, Any]:
    return {"toolUse": {"toolUseId": tool_id, "name": "record_thing", "input": {"n": n}}}


class Ticker:
    """A clock that advances 0.25 s per reading, so latency is deterministic."""

    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        self.t += 0.25
        return self.t


def provider_with(stubber_setup: Any) -> tuple[BedrockConverseProvider, Stubber]:
    client = boto3.client("bedrock-runtime", region_name="us-east-1")
    stubber = Stubber(client)
    stubber_setup(stubber)
    stubber.activate()
    fixed = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)
    return BedrockConverseProvider(client, now=lambda: fixed, monotonic=Ticker()), stubber


def test_request_has_one_tool_auto_choice_and_no_sampling_field() -> None:
    body = build_request(make_request())
    assert body["modelId"] == "us.example-profile"
    assert body["toolConfig"]["toolChoice"] == {"auto": {}}
    assert len(body["toolConfig"]["tools"]) == 1
    assert body["toolConfig"]["tools"][0]["toolSpec"]["name"] == "record_thing"
    assert body["inferenceConfig"] == {"maxTokens": 256}
    assert "additionalModelRequestFields" not in body
    for forbidden in ("temperature", "topP", "topK"):
        assert forbidden not in body["inferenceConfig"]


def test_additional_fields_only_when_given() -> None:
    fields = {"thinking": {"type": "adaptive"}, "output_config": {"effort": "high"}}
    body = build_request(make_request(additional_fields=fields))
    assert body["additionalModelRequestFields"] == fields


def test_the_stubber_accepts_exactly_the_built_request() -> None:
    request = make_request()

    def setup(stubber: Stubber) -> None:
        stubber.add_response("converse", response([tool_use()]), build_request(request))

    provider, stubber = provider_with(setup)
    provider.decide(request)
    stubber.assert_no_pending_responses()


def test_one_tool_call_is_parsed_with_usage_and_provenance() -> None:
    def setup(stubber: Stubber) -> None:
        stubber.add_response("converse", response([tool_use(n=19.31)], cacheReadInputTokens=3))

    provider, _ = provider_with(setup)
    result = provider.decide(make_request())
    assert result.status == "ok"
    assert result.stop_reason == "tool_use"
    assert result.tool_call_count == 1
    assert result.tool_input == {"n": 19.31}
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens == 5
    assert result.usage.cache_read_tokens == 3
    assert result.usage.cache_write_tokens == 0
    assert result.provenance.thinking == "not set"
    assert result.provenance.effort == "not set"
    assert result.provenance.temperature == "not set"
    assert result.provenance.latency_ms == 250
    assert result.provenance.prompt_sha256 == prompt_sha256(make_request())


def test_text_only_answer_is_zero_tool_calls() -> None:
    def setup(stubber: Stubber) -> None:
        stubber.add_response("converse", response([{"text": "It is 19.31."}], stop="end_turn"))

    provider, _ = provider_with(setup)
    result = provider.decide(make_request())
    assert result.tool_call_count == 0
    assert result.tool_input is None
    assert result.text_blocks == ["It is 19.31."]
    assert result.stop_reason == "end_turn"


def test_two_tool_calls_are_both_kept() -> None:
    def setup(stubber: Stubber) -> None:
        stubber.add_response("converse", response([tool_use("a", 1), tool_use("b", 2)]))

    provider, _ = provider_with(setup)
    result = provider.decide(make_request())
    assert result.tool_call_count == 2
    assert result.tool_input == {"n": 1}


def test_a_reasoning_block_before_the_tool_call_is_counted() -> None:
    reasoning = {"reasoningContent": {"reasoningText": {"text": "thinking", "signature": "sig"}}}

    def setup(stubber: Stubber) -> None:
        stubber.add_response("converse", response([reasoning, tool_use()]))

    provider, _ = provider_with(setup)
    result = provider.decide(make_request())
    assert result.reasoning_block_count == 1
    assert result.tool_call_count == 1


def test_max_tokens_stop_is_recorded_as_found() -> None:
    def setup(stubber: Stubber) -> None:
        stubber.add_response("converse", response([{"text": "cut off"}], stop="max_tokens"))

    provider, _ = provider_with(setup)
    assert provider.decide(make_request()).stop_reason == "max_tokens"


@pytest.mark.parametrize(
    ("code", "status"),
    [("ValidationException", 400), ("ThrottlingException", 429), ("AccessDeniedException", 403)],
)
def test_an_api_error_is_a_record_with_its_code_and_message(code: str, status: int) -> None:
    def setup(stubber: Stubber) -> None:
        stubber.add_client_error(
            "converse", service_error_code=code, service_message="boom", http_status_code=status
        )

    provider, _ = provider_with(setup)
    result = provider.decide(make_request())
    assert result.status == "api_error"
    assert result.error is not None
    assert result.error["code"] == code
    assert result.error["message"] == "boom"
    assert result.error["http_status"] == str(status)
    assert result.raw_response is None
    assert result.tool_call_count == 0


def test_thinking_and_effort_are_recorded_as_sent() -> None:
    fields = {"thinking": {"type": "adaptive"}, "output_config": {"effort": "high"}}

    def setup(stubber: Stubber) -> None:
        stubber.add_response("converse", response([tool_use()]))

    provider, _ = provider_with(setup)
    result = provider.decide(make_request(additional_fields=fields))
    assert result.provenance.thinking == '{"type": "adaptive"}'
    assert result.provenance.effort == "high"


def test_the_prompt_hash_ignores_the_route() -> None:
    other = ModelRoute("x", "amazon.nova-pro-v1:0", "in_region", invoke_id="amazon.nova-pro-v1:0")
    assert prompt_sha256(make_request()) == prompt_sha256(make_request(route=other))
    assert prompt_sha256(make_request()) != prompt_sha256(make_request(user="different"))
