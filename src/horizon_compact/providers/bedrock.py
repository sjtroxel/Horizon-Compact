"""Bedrock through the Converse API: exactly one tool, ``auto`` choice, no sampling parameters.

The same method for every model (planning/07 section 2.2). Nothing is retried here: the client is built with a
single attempt so every call is visible, and an API error is returned as a record with its code and message.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from horizon_compact.providers.base import DecisionRequest, Provenance, RawDecision, Usage

if TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime import BedrockRuntimeClient

REGION = "us-east-1"


def make_runtime_client(profile: str | None, region: str = REGION) -> BedrockRuntimeClient:
    """A bedrock-runtime client that makes one attempt per call and never retries silently.

    No profile means the default credential chain, which is the task role inside the container.
    """
    config = Config(retries={"max_attempts": 1, "mode": "standard"}, read_timeout=300)
    return boto3.Session(profile_name=profile, region_name=region).client(
        "bedrock-runtime", config=config
    )


def prompt_sha256(request: DecisionRequest) -> str:
    """Hash of the canonical system, user and tool JSON. Independent of the route, so one prompt, one hash."""
    canonical = json.dumps(
        {
            "system": request.system,
            "user": request.user,
            "tool": {
                "name": request.tool.name,
                "description": request.tool.description,
                "input_schema": request.tool.input_schema,
            },
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_request(request: DecisionRequest) -> dict[str, Any]:
    system: list[dict[str, Any]] = [{"text": request.system}]
    if request.cache_system:
        system.append({"cachePoint": {"type": "default"}})
    body: dict[str, Any] = {
        "modelId": request.route.invoke_id,
        "system": system,
        "messages": [{"role": "user", "content": [{"text": request.user}]}],
        "toolConfig": {
            "tools": [
                {
                    "toolSpec": {
                        "name": request.tool.name,
                        "description": request.tool.description,
                        "inputSchema": {"json": dict(request.tool.input_schema)},
                    }
                }
            ],
            "toolChoice": {"auto": {}},
        },
        "inferenceConfig": {"maxTokens": request.max_tokens},
    }
    if request.additional_fields:
        body["additionalModelRequestFields"] = dict(request.additional_fields)
    if request.additional_response_fields:
        body["additionalModelResponseFieldPaths"] = list(request.additional_response_fields)
    return body


def _thinking_as_sent(request: DecisionRequest) -> str:
    fields = request.additional_fields or {}
    return json.dumps(fields["thinking"], sort_keys=True) if "thinking" in fields else "not set"


def _effort_as_sent(request: DecisionRequest) -> str:
    fields = request.additional_fields or {}
    effort = (fields.get("output_config") or {}).get("effort")
    return str(effort) if effort else "not set"


def _usage(raw: dict[str, Any]) -> Usage:
    """Absent cache fields read as zero; the raw response keeps whatever the model actually returned."""
    usage = raw.get("usage") or {}
    return Usage(
        input_tokens=int(usage.get("inputTokens", 0)),
        output_tokens=int(usage.get("outputTokens", 0)),
        cache_read_tokens=int(usage.get("cacheReadInputTokens", 0)),
        cache_write_tokens=int(usage.get("cacheWriteInputTokens", 0)),
    )


def _blocks(raw: dict[str, Any]) -> list[dict[str, Any]]:
    content = ((raw.get("output") or {}).get("message") or {}).get("content") or []
    return [block for block in content if isinstance(block, dict)]


class BedrockConverseProvider:
    name = "bedrock"

    def __init__(
        self,
        client: BedrockRuntimeClient,
        region: str = REGION,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._client = client
        self._region = region
        self._now = now
        self._monotonic = monotonic

    def decide(self, request: DecisionRequest) -> RawDecision:
        body = build_request(request)
        started = self._now()
        t0 = self._monotonic()
        raw: dict[str, Any] | None = None
        error: dict[str, str] | None = None
        try:
            raw = dict(self._client.converse(**body))
        except ClientError as exc:
            err = exc.response.get("Error", {})
            meta = exc.response.get("ResponseMetadata", {})
            error = {
                "code": str(err.get("Code", "ClientError")),
                "message": str(err.get("Message", exc)),
            }
            # AWS Support asks for the request id, and the HTTP status helps classify the error.
            if "HTTPStatusCode" in meta:
                error["http_status"] = str(meta["HTTPStatusCode"])
            if "RequestId" in meta:
                error["request_id"] = str(meta["RequestId"])
        except BotoCoreError as exc:
            error = {"code": type(exc).__name__, "message": str(exc)}
        latency_ms = round((self._monotonic() - t0) * 1000)
        provenance = Provenance(
            provider=self.name,
            api="converse",
            model_id=request.route.model_id,
            invoke_id=request.route.invoke_id,
            route_kind=request.route.route_kind,
            inference_profile=request.route.inference_profile,
            region=self._region,
            thinking=_thinking_as_sent(request),
            effort=_effort_as_sent(request),
            temperature="not set",
            max_tokens=request.max_tokens,
            prompt_sha256=prompt_sha256(request),
            started_at=started.isoformat(),
            finished_at=self._now().isoformat(),
            latency_ms=latency_ms,
        )
        if raw is None:
            return RawDecision(status="api_error", provenance=provenance, error=error)

        blocks = _blocks(raw)
        return RawDecision(
            status="ok",
            provenance=provenance,
            raw_response=raw,
            stop_reason=raw.get("stopReason"),
            tool_calls=[
                {"name": b["toolUse"].get("name"), "input": b["toolUse"].get("input")}
                for b in blocks
                if "toolUse" in b
            ],
            text_blocks=[str(b["text"]) for b in blocks if "text" in b],
            reasoning_block_count=sum(1 for b in blocks if "reasoningContent" in b),
            usage=_usage(raw),
        )
