"""Test isolation: the network is unreachable and no real AWS identity can be used.

A test that tries to reach AWS fails instead of quietly using the developer's credentials. The guard tests'
``git`` subprocesses are separate processes and are unaffected.
"""

from __future__ import annotations

import socket
from pathlib import Path
from typing import Any, NoReturn

import pytest


@pytest.fixture(autouse=True)
def _no_network_no_real_aws(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for name in (
        "AWS_PROFILE",
        "AWS_DEFAULT_PROFILE",
        "AWS_SESSION_TOKEN",
        "AWS_BEARER_TOKEN_BEDROCK",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAFAKEFAKEFAKEFAKE")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "fake-secret-not-real")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_CONFIG_FILE", str(tmp_path / "no-such-aws-config"))
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", str(tmp_path / "no-such-aws-credentials"))

    def refuse(self: socket.socket, *args: Any, **kwargs: Any) -> NoReturn:
        raise AssertionError("a test tried to open a network connection")

    monkeypatch.setattr(socket.socket, "connect", refuse)
