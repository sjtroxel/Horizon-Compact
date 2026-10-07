"""A stand-in OpenRouter on the loopback address, for the provider and CLI tests. Standard library only.

It answers ``POST /api/v1/chat/completions``, remembers every body and every Authorization header it
received, and answers with whatever the test hands it. Nothing leaves this machine, and the key in these
tests is a made-up string.
"""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from sweep_helpers import valid_input

MODEL = "openai/gpt-test-1b"
# Made up. It has the shape the harness checks (the prefix and a length) and opens nothing.
KEY = "sk-or-v1-0123456789abcdef0123456789abcdef"

# A reply is (HTTP status, a dict that becomes JSON, or bytes sent as they are).
Reply = tuple[int, dict[str, Any] | bytes]


def completion(
    tool_input: Any = None,
    *,
    finish_reason: str = "tool_calls",
    content: str | None = None,
    reasoning: str | None = None,
    tool_calls: list[dict[str, Any]] | None = None,
    prompt_tokens: int = 2400,
    completion_tokens: int = 500,
) -> dict[str, Any]:
    """A reply shaped like OpenRouter's chat completions: the arguments arrive as a JSON string."""
    if tool_calls is None:
        arguments = valid_input() if tool_input is None else tool_input
        tool_calls = [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "submit_decision",
                    "arguments": arguments if isinstance(arguments, str) else json.dumps(arguments),
                },
            }
        ]
    message: dict[str, Any] = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
    if reasoning is not None:
        message["reasoning"] = reasoning
    return {
        "id": "gen-test-abc",
        "model": MODEL,
        "provider": "Test Host",
        "created": 1_790_000_000,
        "choices": [{"index": 0, "finish_reason": finish_reason, "message": message}],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "cost": 0.000123,
        },
    }


class FakeOpenRouter:
    def __init__(
        self, chat: Callable[[dict[str, Any]], Reply] | None = None, *, delay: float = 0.0
    ) -> None:
        self.chat = chat or (lambda body: (200, completion()))
        self.delay = delay
        self.bodies: list[dict[str, Any]] = []
        self.authorizations: list[str] = []
        self.paths: list[str] = []
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:  # silence the access log
                pass

            def do_POST(self) -> None:
                owner.paths.append(self.path)
                owner.authorizations.append(self.headers.get("Authorization", ""))
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                owner.bodies.append(body)
                if owner.delay:
                    time.sleep(owner.delay)
                status, payload = owner.chat(body)
                data = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(
            target=lambda: self._server.serve_forever(poll_interval=0.01), daemon=True
        )

    @property
    def url(self) -> str:
        host, port = self._server.server_address[:2]
        return f"http://{host!s}:{port}/api/v1/chat/completions"

    def __enter__(self) -> FakeOpenRouter:
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)
