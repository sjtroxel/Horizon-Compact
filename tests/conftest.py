"""Test isolation: the network is unreachable and no real AWS identity can be used.

A test that tries to reach AWS fails instead of quietly using the developer's credentials. The guard tests'
``git`` subprocesses are separate processes and are unaffected.

**One exception, narrow on purpose:** a connection to the loopback address (``127.0.0.1`` or ``::1``) is
allowed, so a test can talk to a stand-in server it started itself (``tests/fake_ollama.py``). Loopback leaves
the machine nowhere, and every other address is still refused.
"""

from __future__ import annotations

import socket
from pathlib import Path
from typing import Any

import pytest

LOOPBACK = frozenset({"127.0.0.1", "::1"})


@pytest.fixture(autouse=True)
def _no_network_no_real_aws(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for name in (
        "AWS_PROFILE",
        "AWS_DEFAULT_PROFILE",
        "AWS_SESSION_TOKEN",
        "AWS_BEARER_TOKEN_BEDROCK",
        "OPENROUTER_API_KEY",  # a real key in the developer's shell must never reach a test
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAFAKEFAKEFAKEFAKE")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "fake-secret-not-real")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_CONFIG_FILE", str(tmp_path / "no-such-aws-config"))
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", str(tmp_path / "no-such-aws-credentials"))

    real_connect = socket.socket.connect

    def guarded(self: socket.socket, address: Any, *args: Any, **kwargs: Any) -> Any:
        host = address[0] if isinstance(address, tuple) and address else None
        if host in LOOPBACK:
            return real_connect(self, address, *args, **kwargs)
        raise AssertionError("a test tried to open a network connection")

    monkeypatch.setattr(socket.socket, "connect", guarded)
