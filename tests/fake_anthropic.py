"""A stand-in for Anthropic's API, as a transport under the official SDK. Nothing here opens a socket: the
SDK's HTTP client is handed an ``httpx2.MockTransport``, which answers from memory, so the provider runs
through the SDK's real request building, header setting and error handling with no network at all. The key in
these tests is a made-up string."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx2

from sweep_helpers import valid_input

MODEL = "claude-haiku-5-5"
# Made up. It has the shape the harness checks (the prefix and a length) and opens nothing.
KEY = "sk-ant-api03-0123456789abcdef0123456789abcdef"
REQUEST_ID = "req_test_0123456789"

Reply = httpx2.Response


def message(
    tool_input: Any = None,
    *,
    stop_reason: str = "tool_use",
    content: list[dict[str, Any]] | None = None,
    input_tokens: int = 2400,
    output_tokens: int = 500,
    stop_details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """A reply shaped like the Messages API's: a list of content blocks, one a ``tool_use``."""
    if content is None:
        content = [
            {
                "type": "tool_use",
                "id": "toolu_1",
                "name": "submit_decision",
                "input": valid_input() if tool_input is None else tool_input,
            }
        ]
    return {
        "id": "msg_test_1",
        "type": "message",
        "role": "assistant",
        "model": MODEL,
        "content": content,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "stop_details": stop_details,
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
        },
    }


def ok(payload: dict[str, Any] | None = None) -> Reply:
    return httpx2.Response(
        200,
        json=message() if payload is None else payload,
        headers={"request-id": REQUEST_ID, "anthropic-workspace-id": "wrkspc_test"},
    )


def failure(status: int, error_type: str, text: str) -> Reply:
    body = {
        "type": "error",
        "error": {"type": error_type, "message": text},
        "request_id": REQUEST_ID,
    }
    return httpx2.Response(status, json=body, headers={"request-id": REQUEST_ID})


class FakeAnthropic:
    """Remembers every request (URL, headers, JSON body) and answers with whatever the test hands it."""

    def __init__(self, reply: Callable[[dict[str, Any]], Reply] | None = None) -> None:
        self.reply = reply or (lambda body: ok())
        self.bodies: list[dict[str, Any]] = []
        self.headers: list[dict[str, str]] = []
        self.urls: list[str] = []
        self.transport = httpx2.MockTransport(self._handle)

    def _handle(self, request: httpx2.Request) -> Reply:
        body = json.loads(request.content)
        self.bodies.append(body)
        self.headers.append(dict(request.headers))
        self.urls.append(str(request.url))
        return self.reply(body)

    @property
    def client(self) -> httpx2.Client:
        return httpx2.Client(transport=self.transport)
