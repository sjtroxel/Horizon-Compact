"""Ollama's chat API: exactly one tool, no sampling option, standard library only (Phase 2.5
IMPLEMENTATION doc section 8.6, and the live checks recorded under its section 17 step 4).

A local model is the development model's first half (Phase 0.5 decision 8): it exists to test format and
plumbing, never to produce results. Nothing here touches AWS, and nothing here imports ``boto3``.

What is sent: the system and user text, the one tool, ``stream: false``, ``think: false`` and two options,
``num_ctx`` (the context window, set explicitly because Ollama's default may be too short for the dossier,
and a silent truncation would drop its start) and ``num_predict`` (the scenario's output limit, the
counterpart of Converse's ``maxTokens``). **No sampling option is ever sent** (planning/07 section 2.3):
the model runs at the defaults its own model file carries, and the provenance names them.

What comes back is mapped onto the shape the Bedrock provider returns, so the classifier and the runner
need no change: a reply that ends normally with a tool call has stop reason ``tool_use``, without one
``end_turn``, and ``length`` is ``max_tokens``. A failure is a record, never an exception, and uses the
error names the classifier already knows (``EndpointConnectionError``, ``ReadTimeoutError``,
``InternalServerException`` and so on).

**One conversion, on purpose:** Ollama reports durations in nanoseconds, and a call over 100 seconds makes
a 12-digit number, which the record writer refuses as a possible account id. The stored response therefore
carries every ``*_duration`` as milliseconds under a ``*_duration_ms`` key; nothing else in it is changed.
"""

from __future__ import annotations

import contextlib
import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from horizon_compact.providers.base import (
    DecisionRequest,
    Provenance,
    RawDecision,
    Usage,
    prompt_sha256,
)

DEFAULT_URL = "http://localhost:11434"
DEFAULT_NUM_CTX = 16384
LOCAL_REGION = "local"
_NS_SUFFIX = "_duration"
# What the error classifier already treats as retryable network trouble or a malformed call.
_CONNECTION_ERROR = "EndpointConnectionError"
_TIMEOUT_ERROR = "ReadTimeoutError"
_MALFORMED_CALL_ERROR = "ModelErrorException"
_SERVER_ERROR = "InternalServerException"


def _milliseconds(raw: dict[str, Any]) -> dict[str, Any]:
    """The reply with each nanosecond ``*_duration`` as a ``*_duration_ms`` float; see the module note."""
    out: dict[str, Any] = {}
    for key, value in raw.items():
        if (
            key.endswith(_NS_SUFFIX)
            and isinstance(value, int | float)
            and not isinstance(value, bool)
        ):
            out[f"{key}_ms"] = round(value / 1e6, 3)
        else:
            out[key] = value
    return out


def _error_code(status: int, message: str) -> str:
    """Name an HTTP failure with a code the classifier knows. An unparseable tool call is a model outcome
    (retried, counted); a server fault is retried with backoff; a missing model stops the session."""
    if "error parsing tool call" in message.lower():
        return _MALFORMED_CALL_ERROR
    if status == 404:
        return "ResourceNotFoundException"
    if status >= 500:
        return _SERVER_ERROR
    return "ValidationException"


class OllamaProvider:
    name = "ollama"

    def __init__(
        self,
        base_url: str = DEFAULT_URL,
        num_ctx: int = DEFAULT_NUM_CTX,
        timeout: float = 600.0,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._url = base_url.rstrip("/")
        self._num_ctx = num_ctx
        self._timeout = timeout
        self._now = now
        self._monotonic = monotonic
        self._about: dict[str, dict[str, str]] = {}

    # --- the request ---------------------------------------------------------------------------------------

    def request_body(self, request: DecisionRequest) -> dict[str, Any]:
        return {
            "model": request.route.invoke_id,
            "stream": False,
            "think": False,
            "options": {"num_ctx": self._num_ctx, "num_predict": request.max_tokens},
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
        }

    # --- talking to the server -----------------------------------------------------------------------------

    def _http(self, path: str, body: dict[str, Any] | None) -> dict[str, Any]:
        """One request. Raises ``urllib.error`` and ``OSError`` for the caller to turn into a record."""
        data = None if body is None else json.dumps(body).encode("utf-8")
        http_request = urllib.request.Request(
            f"{self._url}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="GET" if body is None else "POST",
        )
        with urllib.request.urlopen(http_request, timeout=self._timeout) as response:
            parsed = json.loads(response.read().decode("utf-8"))
        return parsed if isinstance(parsed, dict) else {"unexpected": parsed}

    def _describe(self, model: str) -> dict[str, str]:
        """The runtime's version, the model's digest and its own sampling defaults, read once per model.
        A failure here is recorded as "unknown", not raised: the chat call that follows reports a dead
        server."""
        if model in self._about:
            return self._about[model]
        about = {
            "ollama_version": "unknown",
            "model_digest": "unknown",
            "model_defaults": "unknown",
        }
        try:
            about["ollama_version"] = str(
                self._http("/api/version", None).get("version", "unknown")
            )
            for entry in self._http("/api/tags", None).get("models", []):
                if isinstance(entry, dict) and model in (entry.get("name"), entry.get("model")):
                    about["model_digest"] = str(entry.get("digest", "unknown"))
            shown = self._http("/api/show", {"model": model})
            lines = str(shown.get("parameters", "")).splitlines()
            about["model_defaults"] = (
                "; ".join(" ".join(line.split()) for line in lines if line.strip()) or "none"
            )
        except (urllib.error.URLError, OSError, ValueError):
            return about  # not remembered: if the server comes up later, the next call reads it properly
        self._about[model] = about
        return about

    def decide(self, request: DecisionRequest) -> RawDecision:
        body = self.request_body(request)
        about = self._describe(request.route.invoke_id)
        started = self._now()
        t0 = self._monotonic()
        raw: dict[str, Any] | None = None
        error: dict[str, str] | None = None
        try:
            raw = self._http("/api/chat", body)
        except urllib.error.HTTPError as exc:
            message = _error_message(exc)
            error = {
                "code": _error_code(exc.code, message),
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
            error = {"code": code, "message": str(reason)}
        except ValueError as exc:  # the server answered, but not with JSON
            error = {"code": _SERVER_ERROR, "message": f"the reply is not JSON: {exc}"}
        except OSError as exc:  # a connection that dropped part way
            error = {"code": _CONNECTION_ERROR, "message": f"{type(exc).__name__}: {exc}"}
        latency_ms = round((self._monotonic() - t0) * 1000)
        provenance = Provenance(
            provider=self.name,
            api="ollama-chat",
            model_id=request.route.model_id,
            invoke_id=request.route.invoke_id,
            route_kind=request.route.route_kind,
            inference_profile=None,
            region=LOCAL_REGION,
            thinking="off (think=false)",
            effort="not set",
            temperature=f"not set; the model's own defaults: {about['model_defaults']}",
            max_tokens=request.max_tokens,
            prompt_sha256=prompt_sha256(request),
            started_at=started.isoformat(),
            finished_at=self._now().isoformat(),
            latency_ms=latency_ms,
            details={
                "ollama_version": about["ollama_version"],
                "model_digest": about["model_digest"],
                "num_ctx": str(self._num_ctx),
                "num_predict": str(request.max_tokens),
                "durations": "stored as milliseconds (*_duration_ms); Ollama reports nanoseconds",
            },
        )
        if raw is None:
            return RawDecision(status="api_error", provenance=provenance, error=error)
        return _decision(raw, provenance)


def _error_message(exc: urllib.error.HTTPError) -> str:
    try:
        text = exc.read().decode("utf-8", "replace")
        parsed = json.loads(text)
        if isinstance(parsed, dict) and "error" in parsed:
            return str(parsed["error"])
        return text[:500]
    except (OSError, ValueError):
        return str(exc.reason)


def _tool_calls(message: dict[str, Any]) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for call in message.get("tool_calls") or []:
        function = call.get("function") if isinstance(call, dict) else None
        if not isinstance(function, dict):
            continue
        arguments = function.get("arguments")
        if isinstance(arguments, str):  # some versions send the arguments as a JSON string
            # On failure it stays the string: the validator calls that schema_invalid.
            with contextlib.suppress(ValueError):
                arguments = json.loads(arguments)
        calls.append({"name": function.get("name"), "input": arguments})
    return calls


def _stop_reason(raw: dict[str, Any], has_tool_call: bool) -> str | None:
    reason = raw.get("done_reason")
    if reason == "length":
        return "max_tokens"
    if reason == "stop":
        return "tool_use" if has_tool_call else "end_turn"
    return None if reason is None else str(reason)


def _decision(raw: dict[str, Any], provenance: Provenance) -> RawDecision:
    raw_message = raw.get("message")
    message: dict[str, Any] = raw_message if isinstance(raw_message, dict) else {}
    calls = _tool_calls(message)
    content = str(message.get("content") or "")
    return RawDecision(
        status="ok",
        provenance=provenance,
        raw_response=_milliseconds(raw),
        stop_reason=_stop_reason(raw, bool(calls)),
        tool_calls=calls,
        text_blocks=[content] if content.strip() else [],
        reasoning_block_count=1 if str(message.get("thinking") or "").strip() else 0,
        usage=Usage(
            input_tokens=int(raw.get("prompt_eval_count") or 0),
            output_tokens=int(raw.get("eval_count") or 0),
        ),
    )
