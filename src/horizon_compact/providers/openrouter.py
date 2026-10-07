"""OpenRouter's chat-completions API: exactly one tool, ``auto`` choice, no sampling option, standard
library only (Phase 2.5 IMPLEMENTATION doc section 17 step 8 item 10, and his decision 9 of 2026-10-07).

OpenRouter is the development model's route while Bedrock is blocked: it reaches ``openai/gpt-oss-120b``,
which balanced the scenarios' shapes where the local models could not (step 6a). It is a development route
only (``role = "development"`` in ``models.toml``), so every refusal that keeps official models off real
content covers it, and the $5 sweep cap does too. Nothing here touches AWS, and nothing here imports
``boto3``.

What is sent: the system and user text, the one tool, ``tool_choice: "auto"``, ``max_tokens`` and
``usage: {"include": true}`` (so the reply states the cost). **No sampling option is ever sent**
(planning/07 section 2.3): the provider runs at the defaults it chooses for the model, and the stored
response says which provider served the call.

**The key** is his and is never written down. It comes from ``OPENROUTER_API_KEY`` if that is set, else from
a hidden prompt; its shape is checked (``sk-or-``) before any call. It travels in one header, never in a
body, an argument list, a record or a log: the request the harness stores is the body, which has no key,
any error message is scrubbed of it, and the record writer refuses a record that still holds a key.

What comes back is mapped onto the shape the Bedrock provider returns, so the classifier and the runner
need no change: a reply that ends normally with a tool call has stop reason ``tool_use``, without one
``end_turn``, and ``length`` is ``max_tokens``. A failure is a record, never an exception, on the error
names the classifier already knows. Cost is counted from tokens and the prices in ``models.toml``, as for
every model; the cost the reply reports is kept in the stored response, and a cached prompt is counted at
full price (an overestimate, the safe direction for a cap).
"""

from __future__ import annotations

import contextlib
import getpass
import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any

from horizon_compact.providers.base import (
    DecisionRequest,
    Provenance,
    RawDecision,
    Usage,
    prompt_sha256,
)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
KEY_ENV = "OPENROUTER_API_KEY"
KEY_PREFIX = "sk-or-"
MIN_KEY_LENGTH = 20
HOSTED_REGION = "hosted by OpenRouter"
# The error names the classifier already knows (sweep/classify.py).
_CONNECTION_ERROR = "EndpointConnectionError"
_TIMEOUT_ERROR = "ReadTimeoutError"
_SERVER_ERROR = "InternalServerException"


class OpenRouterKeyError(Exception):
    """The key is missing or does not look like one. The message never holds any of the key."""


def read_key(
    env: Mapping[str, str],
    ask: Callable[[], str] = lambda: getpass.getpass(
        "OpenRouter key (typing is hidden; press Enter once): "
    ),
) -> str:
    """The key from the environment, else from ``ask`` (a hidden prompt), checked for shape before use."""
    key = (env.get(KEY_ENV) or "").strip() or ask().strip()
    if not key:
        raise OpenRouterKeyError(f"no key: set {KEY_ENV} or type it at the prompt")
    if not key.startswith(KEY_PREFIX) or len(key) < MIN_KEY_LENGTH:
        raise OpenRouterKeyError(
            f"that does not look like an OpenRouter key (it should start {KEY_PREFIX!r}; "
            f"what was given is {len(key)} characters long); nothing was sent"
        )
    return key


def _error_code(status: int) -> str:
    """Name an HTTP failure with a code the classifier knows. Credentials, credit and permission problems stop
    the session; a rate limit and a server fault are retried with backoff."""
    if status in (401, 402, 403):
        return "AccessDeniedException"
    if status == 404:
        return "ResourceNotFoundException"
    if status == 408:
        return _TIMEOUT_ERROR
    if status == 429:
        return "ThrottlingException"
    if status in (502, 503):
        return "ServiceUnavailableException"
    if status == 504:
        return "ModelTimeoutException"
    if status >= 500:
        return _SERVER_ERROR
    return "ValidationException"


class OpenRouterProvider:
    name = "openrouter"

    def __init__(
        self,
        key: str,
        url: str = OPENROUTER_URL,
        timeout: float = 600.0,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._key = key
        self._url = url
        self._timeout = timeout
        self._now = now
        self._monotonic = monotonic

    def __repr__(self) -> str:
        return f"OpenRouterProvider(url={self._url!r})"  # never the key

    # --- the request ---------------------------------------------------------------------------------------

    def request_body(self, request: DecisionRequest) -> dict[str, Any]:
        return {
            "model": request.route.invoke_id,
            "messages": [
                {"role": "system", "content": request.system},
                {"role": "user", "content": request.user},
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": request.tool.name,
                        "description": request.tool.description,
                        "parameters": dict(request.tool.input_schema),
                    },
                }
            ],
            "tool_choice": "auto",
            "max_tokens": request.max_tokens,
            "usage": {"include": True},
        }

    # --- talking to the server -----------------------------------------------------------------------------

    def _scrub(self, text: str) -> str:
        return text.replace(self._key, "[key]")

    def _post(self, body: dict[str, Any]) -> dict[str, Any]:
        """One request. Raises ``urllib.error`` and ``OSError`` for the caller to turn into a record."""
        http_request = urllib.request.Request(
            self._url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self._key}"},
            method="POST",
        )
        with urllib.request.urlopen(http_request, timeout=self._timeout) as response:
            parsed = json.loads(response.read().decode("utf-8"))
        return parsed if isinstance(parsed, dict) else {"unexpected": parsed}

    def decide(self, request: DecisionRequest) -> RawDecision:
        body = self.request_body(request)
        started = self._now()
        t0 = self._monotonic()
        raw: dict[str, Any] | None = None
        error: dict[str, str] | None = None
        try:
            raw = self._post(body)
        except urllib.error.HTTPError as exc:
            message = self._scrub(_error_message(exc))
            error = {
                "code": _error_code(exc.code),
                "message": message,
                "http_status": str(exc.code),
            }
        except TimeoutError:
            error = {
                "code": _TIMEOUT_ERROR,
                "message": f"no reply within {self._timeout:g} seconds",
            }
        except urllib.error.URLError as exc:
            reason = exc.reason
            code = _TIMEOUT_ERROR if isinstance(reason, TimeoutError) else _CONNECTION_ERROR
            error = {"code": code, "message": self._scrub(str(reason))}
        except ValueError as exc:  # the server answered, but not with JSON
            error = {"code": _SERVER_ERROR, "message": f"the reply is not JSON: {exc}"}
        except OSError as exc:  # a connection that dropped part way
            error = {
                "code": _CONNECTION_ERROR,
                "message": self._scrub(f"{type(exc).__name__}: {exc}"),
            }
        if raw is not None and "error" in raw and "choices" not in raw:
            # OpenRouter can answer 200 with the provider's failure in the body.
            error = _body_error(raw["error"], self._scrub)
            raw = None
        latency_ms = round((self._monotonic() - t0) * 1000)
        served = raw or {}
        provenance = Provenance(
            provider=self.name,
            api="openrouter-chat-completions",
            model_id=request.route.model_id,
            invoke_id=request.route.invoke_id,
            route_kind=request.route.route_kind,
            inference_profile=None,
            region=HOSTED_REGION,
            thinking="not set (the model's default)",
            effort="not set",
            temperature="not set; the serving provider's defaults",
            max_tokens=request.max_tokens,
            prompt_sha256=prompt_sha256(request),
            started_at=started.isoformat(),
            finished_at=self._now().isoformat(),
            latency_ms=latency_ms,
            details={
                "served_model": str(served.get("model", "unknown")),
                "served_by": str(served.get("provider", "unknown")),
                "generation_id": str(served.get("id", "unknown")),
            },
        )
        if raw is None:
            return RawDecision(status="api_error", provenance=provenance, error=error)
        return _decision(raw, provenance)


def _error_message(exc: urllib.error.HTTPError) -> str:
    try:
        text = exc.read().decode("utf-8", "replace")
        parsed = json.loads(text)
        if isinstance(parsed, dict) and isinstance(parsed.get("error"), dict):
            return str(parsed["error"].get("message", text[:500]))
        return text[:500]
    except (OSError, ValueError):
        return str(exc.reason)


def _body_error(value: Any, scrub: Callable[[str], str]) -> dict[str, str]:
    if not isinstance(value, dict):
        return {"code": _SERVER_ERROR, "message": scrub(str(value))[:500]}
    status = value.get("code")
    code = _error_code(status) if isinstance(status, int) else _SERVER_ERROR
    return {
        "code": code,
        "message": scrub(str(value.get("message", "")))[:500],
        "http_status": str(status),
    }


def _tool_calls(message: dict[str, Any]) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for call in message.get("tool_calls") or []:
        function = call.get("function") if isinstance(call, dict) else None
        if not isinstance(function, dict):
            continue
        arguments = function.get("arguments")
        if isinstance(arguments, str):  # OpenRouter sends the arguments as a JSON string
            # On failure it stays the string: the validator calls that schema_invalid.
            with contextlib.suppress(ValueError):
                arguments = json.loads(arguments)
        calls.append({"name": function.get("name"), "input": arguments})
    return calls


def _stop_reason(finish: Any, has_tool_call: bool) -> str | None:
    if finish == "length":
        return "max_tokens"
    if finish == "content_filter":
        return "content_filtered"
    if finish in ("stop", "tool_calls"):
        return "tool_use" if has_tool_call else "end_turn"
    return None if finish is None else str(finish)


def _decision(raw: dict[str, Any], provenance: Provenance) -> RawDecision:
    choices = raw.get("choices")
    choice: dict[str, Any] = choices[0] if isinstance(choices, list) and choices else {}
    raw_message = choice.get("message")
    message: dict[str, Any] = raw_message if isinstance(raw_message, dict) else {}
    calls = _tool_calls(message)
    content = str(message.get("content") or "")
    raw_usage = raw.get("usage")
    usage: dict[str, Any] = raw_usage if isinstance(raw_usage, dict) else {}
    return RawDecision(
        status="ok",
        provenance=provenance,
        raw_response=raw,
        stop_reason=_stop_reason(choice.get("finish_reason"), bool(calls)),
        tool_calls=calls,
        text_blocks=[content] if content.strip() else [],
        reasoning_block_count=1 if str(message.get("reasoning") or "").strip() else 0,
        usage=Usage(
            input_tokens=int(usage.get("prompt_tokens") or 0),
            output_tokens=int(usage.get("completion_tokens") or 0),
        ),
    )
