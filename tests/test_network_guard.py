"""The test guard that keeps tests off the network (``tests/conftest.py``): loopback only."""

from __future__ import annotations

import socket

import pytest


def test_a_connection_to_any_address_but_loopback_is_refused() -> None:
    """203.0.113.0/24 is a documentation range that is never routed; the guard refuses before any packet."""
    with socket.socket() as probe, pytest.raises(AssertionError, match="open a network connection"):
        probe.connect(("203.0.113.5", 80))


def test_a_connection_to_a_named_host_is_refused_too() -> None:
    with socket.socket() as probe, pytest.raises(AssertionError, match="open a network connection"):
        probe.connect(("example.com", 443))


def test_loopback_is_reachable_so_a_test_can_run_its_own_stand_in_server() -> None:
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        with socket.socket() as client:
            client.connect(server.getsockname())
