"""A stand-in Ollama on the loopback address, for the provider and CLI tests. Standard library only.

It answers ``/api/version``, ``/api/tags``, ``/api/show`` and ``/api/chat``, remembers every chat body it
received, and answers chat with whatever the test hands it. Nothing leaves this machine.
"""

from __future__ import annotations

import json
import socket
import threading
import time
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from sweep_helpers import valid_input

MODEL = "qwen-test:1b"
DIGEST = "d" * 64
DEFAULTS = "temperature                    1\ntop_k                          20\npresence_penalty               1.5"


def dead_url() -> str:
    """A loopback address with nothing listening: a port that was free a moment ago, now closed."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    return f"http://127.0.0.1:{port}"


# A reply is (HTTP status, a dict that becomes JSON, or bytes sent as they are).
Reply = tuple[int, dict[str, Any] | bytes]


def chat_reply(
    tool_input: Any = None,
    *,
    done_reason: str = "stop",
    content: str = "",
    thinking: str | None = None,
    tool_calls: list[dict[str, Any]] | None = None,
    total_duration: int = 20_600_000_000,
) -> dict[str, Any]:
    """A reply shaped like the one measured live on 2026-10-07 (Phase 2.5 IMPLEMENTATION doc §17 step 4)."""
    if tool_calls is None:
        arguments = valid_input() if tool_input is None else tool_input
        tool_calls = [{"function": {"name": "submit_decision", "arguments": arguments}}]
    message: dict[str, Any] = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
    if thinking is not None:
        message["thinking"] = thinking
    return {
        "model": MODEL,
        "created_at": "2026-10-07T15:50:00.123456Z",
        "message": message,
        "done": True,
        "done_reason": done_reason,
        "total_duration": total_duration,
        "load_duration": 11_000_000_000,
        "prompt_eval_count": 2243,
        "prompt_eval_cached_count": 0,
        "prompt_eval_duration": 900_000_000,
        "eval_count": 430,
        "eval_duration": 8_000_000_000,
    }


class FakeOllama:
    def __init__(
        self,
        chat: Callable[[dict[str, Any]], Reply] | None = None,
        *,
        version: str = "0.35.1",
        delay: float = 0.0,
    ) -> None:
        self.chat = chat or (lambda body: (200, chat_reply()))
        self.version = version
        self.delay = delay
        self.chat_bodies: list[dict[str, Any]] = []
        self.paths: list[str] = []
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:  # silence the access log
                pass

            def _send(self, status: int, payload: dict[str, Any] | bytes) -> None:
                data = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self) -> None:
                owner.paths.append(self.path)
                if self.path == "/api/version":
                    self._send(200, {"version": owner.version})
                elif self.path == "/api/tags":
                    self._send(200, {"models": [{"name": MODEL, "model": MODEL, "digest": DIGEST}]})
                else:
                    self._send(404, {"error": "not found"})

            def do_POST(self) -> None:
                owner.paths.append(self.path)
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                if self.path == "/api/show":
                    self._send(200, {"parameters": DEFAULTS, "capabilities": ["tools", "thinking"]})
                elif self.path == "/api/chat":
                    owner.chat_bodies.append(body)
                    if owner.delay:
                        time.sleep(owner.delay)
                    status, payload = owner.chat(body)
                    self._send(status, payload)
                else:
                    self._send(404, {"error": "not found"})

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(
            target=lambda: self._server.serve_forever(poll_interval=0.01), daemon=True
        )

    @property
    def url(self) -> str:
        host, port = self._server.server_address[:2]
        return f"http://{host!s}:{port}"

    def __enter__(self) -> FakeOllama:
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)
