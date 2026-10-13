"""Anthropic's own Messages API, through the official Python SDK: exactly one tool, ``auto`` choice, no
sampling option (Phase 4 code half section 4.9, step K6; Phase 3.5 section 23 decision B).

This is the route Haiku 5.5 takes under the fallback set: the model's own vendor, paid from the prepaid credit
on his Console account, through a key made inside the ``horizon-compact`` workspace (which carries a $10
monthly spend limit). Nothing here touches AWS except the container's read of the key from SSM, which is a
client the caller passes in; this module never imports ``boto3``.

What is sent: ``model``, ``system``, one user message, the one tool, ``tool_choice: {"type": "auto"}``,
``max_tokens``, and ``thinking: {"type": "disabled"}`` when the route says thinking is off (decision C).
**Sent only by a sweep labeled ``thinking``** (protocol 9.5, the sub-study): ``thinking`` as ``{"type":
"adaptive", "display": "summarized"}``, ``output_config`` as ``{"effort": "high"}``, and ``max_tokens``
16,000. **Never sent:** ``temperature``, ``top_p``, ``top_k`` (the model rejects non-default values, and the
design never sets sampling), ``effort`` outside the sub-study, a cache breakpoint (decision F),
``inference_geo``, any beta header, any fallback model. The runner marks every request
``cache_system=True`` (Bedrock honors it); **this route ignores it, as OpenRouter's does**, so no
``cache_control`` is ever sent and no cache write is ever paid (decision F).
Extra fields a request asks for (a smoke call's) are refused here, not quietly dropped.

**The SDK's own retries are off** (``max_retries=0``): the harness counts attempts, and a library retrying
underneath would hide them from the failure accounting. **The environment cannot steer the client**: the SDK
reads ``ANTHROPIC_*`` variables (a base URL, an auth token, extra headers), so they are set aside while the
client is built, and the URL and key are passed explicitly.

**The raw response** is read through the SDK's raw-response accessor and parsed from its bytes, not from the
SDK's typed message, so a field the SDK does not model is still in the stored record. The ``request-id``
header is kept in provenance.

What comes back is mapped onto the shape the Bedrock provider returns, so the classifier and the runner need
no change: ``tool_use``, ``end_turn`` and ``max_tokens`` pass through, and **``refusal`` becomes
``content_filtered``**, which the classifier already reads as a refusal (``stop_details`` stays in the stored
response). A failure is a record, never an exception, on the error names the classifier already knows; **a
spend limit or an exhausted credit, and a rejected key, stop the session** (they are configuration errors,
never a model's failure and never retried). Cost is counted from tokens and the prices in ``models.toml``.

**The key** is his and is never written down. It comes from ``ANTHROPIC_API_KEY`` if that is set, else (in the
container only) from the SSM SecureString ``/horizon-compact/anthropic-key``, else from a hidden prompt; its
shape is checked (``sk-ant-``) before any call. It travels only in the SDK's header: the request the harness
stores is the body, which has no key, every error message is scrubbed of it, and the record writer refuses a
record that still holds one.
"""

from __future__ import annotations

import contextlib
import getpass
import json
import os
import re
import time
from collections.abc import Callable, Iterator, Mapping
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import anthropic

from horizon_compact.providers.base import (
    THINKING_STUDY_EFFORT_NOTE,
    THINKING_STUDY_MAX_TOKENS,
    THINKING_STUDY_OUTPUT_CONFIG,
    THINKING_STUDY_THINKING,
    THINKING_STUDY_THINKING_NOTE,
    DecisionRequest,
    ModelRoute,
    Provenance,
    RawDecision,
    TextRequest,
    Usage,
    prompt_sha256,
    text_prompt_sha256,
)

if TYPE_CHECKING:
    import httpx2

BASE_URL = "https://api.anthropic.com"
KEY_ENV = "ANTHROPIC_API_KEY"
KEY_PREFIX = "sk-ant-"
SSM_PARAMETER = "/horizon-compact/anthropic-key"  # the container's source; a test holds it equal to the IAM JSON
MIN_KEY_LENGTH = 20
HOSTED_REGION = "hosted by Anthropic"
THINKING_OFF = "off: thinking {type: disabled} sent"
THINKING_DEFAULT = "not set (the model's default)"
# The error names the classifier already knows (sweep/classify.py).
_CONNECTION_ERROR = "EndpointConnectionError"
_TIMEOUT_ERROR = "ReadTimeoutError"
_SERVER_ERROR = "InternalServerException"
# Not names the classifier knows, so each is a configuration error that stops the session (the safe
# direction): the credit or the workspace limit is used up, or the SDK itself refused the call.
SPEND_LIMIT = "SpendLimitReached"
_SDK_ERROR = "SdkError"

_KEY_SHAPE = re.compile(r"sk-ant-[A-Za-z0-9_-]{8,}")
_LIMIT_WORDS = ("usage limit", "spend limit", "spend cap", "credit balance")


class AnthropicKeyError(Exception):
    """The key is missing or does not look like one. The message never holds any of the key."""


def read_key(
    env: Mapping[str, str],
    ask: Callable[[], str] = lambda: getpass.getpass(
        "Anthropic key (typing is hidden; press Enter once): "
    ),
    ssm_fetch: Callable[[], str] | None = None,
) -> str:
    """The key from the environment, else from ``ssm_fetch`` (the container's SSM parameter, when given), else
    from ``ask`` (a hidden prompt), checked for shape before use."""
    key = (env.get(KEY_ENV) or "").strip()
    if not key and ssm_fetch is not None:
        key = ssm_fetch().strip()
    if not key:
        key = ask().strip()
    if not key:
        raise AnthropicKeyError(f"no key: set {KEY_ENV} or type it at the prompt")
    if not key.startswith(KEY_PREFIX) or len(key) < MIN_KEY_LENGTH:
        raise AnthropicKeyError(
            f"that does not look like an Anthropic key (it should start {KEY_PREFIX!r}; "
            f"what was given is {len(key)} characters long); nothing was sent"
        )
    return key


def ssm_key_fetcher(client: Any) -> Callable[[], str]:
    """A function that reads the key from the SSM SecureString, for the container. ``client`` is an ``ssm``
    client. A failure names the kind of error and the AWS error code, never a value, so nothing about the key
    can reach a log."""

    def fetch() -> str:
        try:
            response = client.get_parameter(Name=SSM_PARAMETER, WithDecryption=True)
            value = response["Parameter"]["Value"]
        except Exception as exc:  # a boto error, a missing field: say which kind, show nothing else
            code = getattr(exc, "response", {}).get("Error", {}).get("Code", "")
            raise AnthropicKeyError(
                f"could not read the key from SSM parameter {SSM_PARAMETER}: "
                f"{type(exc).__name__}{f' ({code})' if code else ''}"
            ) from None
        return str(value)

    return fetch


def _error_code(status: int, message: str) -> str:
    """Name an HTTP failure with a code the classifier knows, or one it does not (which stops the session).
    A reached spend limit comes back as a 400 (a tier's monthly cap, as a 429), whose message names the limit;
    it must never read as a model's failure or be retried."""
    if status in (400, 429) and any(word in message.lower() for word in _LIMIT_WORDS):
        return SPEND_LIMIT
    if status in (401, 402, 403):
        return "AccessDeniedException"
    if status == 404:
        return "ResourceNotFoundException"
    if status == 408:
        return _TIMEOUT_ERROR
    if status == 429:
        return "ThrottlingException"
    if status in (502, 503, 529):  # 529 is "overloaded"
        return "ServiceUnavailableException"
    if status == 504:
        return "ModelTimeoutException"
    if status >= 500:
        return _SERVER_ERROR
    return "ValidationException"


@contextlib.contextmanager
def _without_anthropic_environment() -> Iterator[None]:
    """Set aside every ``ANTHROPIC_*`` variable while the SDK client is built, so none of them (a base URL,
    an auth token, extra headers) can change where a call goes or what it carries. Put back after."""
    saved = {name: value for name, value in os.environ.items() if name.startswith("ANTHROPIC_")}
    for name in saved:
        del os.environ[name]
    try:
        yield
    finally:
        os.environ.update(saved)


class AnthropicProvider:
    name = "anthropic"

    def __init__(
        self,
        key: str,
        http_client: httpx2.Client | None = None,
        timeout: float = 600.0,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._key = key
        self._timeout = timeout
        self._now = now
        self._monotonic = monotonic
        with _without_anthropic_environment():
            self._client = anthropic.Anthropic(
                api_key=key,
                base_url=BASE_URL,
                max_retries=0,
                timeout=timeout,
                http_client=http_client,
            )

    def __repr__(self) -> str:
        return f"AnthropicProvider(base_url={BASE_URL!r})"  # never the key

    # --- the request ---------------------------------------------------------------------------------------

    @staticmethod
    def _base_body(route: ModelRoute, system: str, user: str, max_tokens: int) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": route.invoke_id,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        if route.thinking_off:
            body["thinking"] = {"type": "disabled"}
        return body

    def request_body(self, request: DecisionRequest) -> dict[str, Any]:
        if request.additional_fields or request.additional_response_fields:
            raise ValueError("the Anthropic route sends no extra request or response fields")
        body = self._base_body(request.route, request.system, request.user, request.max_tokens)
        body["tools"] = [
            {
                "name": request.tool.name,
                "description": request.tool.description,
                "input_schema": dict(request.tool.input_schema),
            }
        ]
        body["tool_choice"] = {"type": "auto"}
        if request.thinking_study:
            self._apply_thinking_study(body, request)
        return body

    @staticmethod
    def _apply_thinking_study(body: dict[str, Any], request: DecisionRequest) -> None:
        """Protocol 9.5's request: the grid's body with ``thinking`` replaced and ``output_config`` added; the
        ``max_tokens`` is the sub-study's own, and the caller must already have set it (the runner does)."""
        if not request.route.thinking_off:
            raise ValueError(
                "the thinking sub-study replaces the grid's thinking {type: disabled}; this route's "
                "configuration does not send it"
            )
        if request.max_tokens != THINKING_STUDY_MAX_TOKENS:
            raise ValueError(
                f"the thinking sub-study sends max_tokens {THINKING_STUDY_MAX_TOKENS:,}, "
                f"not {request.max_tokens:,}"
            )
        body["thinking"] = dict(THINKING_STUDY_THINKING)
        body["output_config"] = dict(THINKING_STUDY_OUTPUT_CONFIG)

    def text_request_body(self, request: TextRequest) -> dict[str, Any]:
        """The same call with no ``tools`` and no ``tool_choice``: the model has nothing to call."""
        return self._base_body(request.route, request.system, request.user, request.max_tokens)

    def decide(self, request: DecisionRequest) -> RawDecision:
        return self._send(
            self.request_body(request),
            request.route,
            request.max_tokens,
            prompt_sha256(request),
            thinking_study=request.thinking_study,
        )

    def decide_text(self, request: TextRequest) -> RawDecision:
        return self._send(
            self.text_request_body(request),
            request.route,
            request.max_tokens,
            text_prompt_sha256(request),
        )

    # --- talking to the server -----------------------------------------------------------------------------

    def _scrub(self, text: str) -> str:
        return _KEY_SHAPE.sub("[key]", text.replace(self._key, "[key]"))

    def _send(
        self,
        body: dict[str, Any],
        route: ModelRoute,
        max_tokens: int,
        sha256: str,
        *,
        thinking_study: bool = False,
    ) -> RawDecision:
        started = self._now()
        t0 = self._monotonic()
        raw: dict[str, Any] | None = None
        error: dict[str, str] | None = None
        request_id = "unknown"
        try:
            response = self._client.messages.with_raw_response.create(**body)
            request_id = str(response.headers.get("request-id", "unknown"))
            parsed = json.loads(response.http_response.content)
            raw = parsed if isinstance(parsed, dict) else {"unexpected": parsed}
        except anthropic.APIStatusError as exc:
            request_id = str(exc.response.headers.get("request-id", "unknown"))
            message = self._scrub(_error_message(exc))
            error = {
                "code": _error_code(exc.status_code, message),
                "message": message,
                "http_status": str(exc.status_code),
            }
        except anthropic.APITimeoutError:  # before APIConnectionError, which it extends
            error = {
                "code": _TIMEOUT_ERROR,
                "message": f"no reply within {self._timeout:g} seconds",
            }
        except anthropic.APIConnectionError as exc:
            error = {
                "code": _CONNECTION_ERROR,
                "message": self._scrub(f"{type(exc).__name__}: {exc}"),
            }
        except ValueError as exc:  # the server answered, but not with JSON
            error = {"code": _SERVER_ERROR, "message": f"the reply is not JSON: {exc}"[:500]}
        except anthropic.AnthropicError as exc:  # the SDK refused the call itself
            error = {
                "code": _SDK_ERROR,
                "message": self._scrub(f"{type(exc).__name__}: {exc}")[:500],
            }
        latency_ms = round((self._monotonic() - t0) * 1000)
        served = raw or {}
        provenance = Provenance(
            provider=self.name,
            api="anthropic-messages",
            model_id=route.model_id,
            invoke_id=route.invoke_id,
            route_kind=route.route_kind,
            inference_profile=None,
            region=HOSTED_REGION,
            thinking=(
                THINKING_STUDY_THINKING_NOTE
                if thinking_study
                else THINKING_OFF
                if route.thinking_off
                else THINKING_DEFAULT
            ),
            effort=THINKING_STUDY_EFFORT_NOTE
            if thinking_study
            else "not set (the model's default)",
            temperature="not set; the API rejects non-default values",
            max_tokens=max_tokens,
            prompt_sha256=sha256,
            started_at=started.isoformat(),
            finished_at=self._now().isoformat(),
            latency_ms=latency_ms,
            details={
                "served_model": str(served.get("model", "unknown")),
                "request_id": request_id,
            },
        )
        if raw is None:
            return RawDecision(status="api_error", provenance=provenance, error=error)
        return _decision(raw, provenance)


def _error_message(exc: anthropic.APIStatusError) -> str:
    body = exc.body
    if isinstance(body, dict):
        inner = body.get("error")
        if isinstance(inner, dict) and inner.get("message"):
            return str(inner["message"])[:500]
    return str(exc.message)[:500]


def _stop_reason(value: Any) -> str | None:
    if value == "refusal":
        return "content_filtered"  # the refusal the classifier already reads
    return None if value is None else str(value)


def _decision(raw: dict[str, Any], provenance: Provenance) -> RawDecision:
    blocks = raw.get("content")
    calls: list[dict[str, Any]] = []
    texts: list[str] = []
    reasoning = 0
    for block in blocks if isinstance(blocks, list) else []:
        if not isinstance(block, dict):
            continue
        kind = block.get("type")
        if kind == "tool_use":
            calls.append({"name": block.get("name"), "input": block.get("input")})
        elif kind == "text":
            text = str(block.get("text") or "")
            if text.strip():
                texts.append(text)
        elif kind in ("thinking", "redacted_thinking"):
            reasoning += 1
    raw_usage = raw.get("usage")
    usage: dict[str, Any] = raw_usage if isinstance(raw_usage, dict) else {}
    return RawDecision(
        status="ok",
        provenance=provenance,
        raw_response=raw,
        stop_reason=_stop_reason(raw.get("stop_reason")),
        tool_calls=calls,
        text_blocks=texts,
        reasoning_block_count=reasoning,
        usage=Usage(
            input_tokens=int(usage.get("input_tokens") or 0),
            output_tokens=int(usage.get("output_tokens") or 0),
            cache_read_tokens=int(usage.get("cache_read_input_tokens") or 0),
            cache_write_tokens=int(usage.get("cache_creation_input_tokens") or 0),
        ),
    )
