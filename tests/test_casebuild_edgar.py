"""The EDGAR client on a fake transport: User-Agent, spacing, stop on 403/429, write-once cache."""

from __future__ import annotations

import hashlib
import http.server
import json
import threading
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest

from edgar_helpers import FACTS_URL, SUBMISSIONS_URL, USER_AGENT, FakeTransport
from horizon_compact.casebuild.appendix import AppendixError, CaseAppendix
from horizon_compact.casebuild.edgar import (
    EdgarBlocked,
    EdgarClient,
    EdgarError,
    Response,
    UrllibTransport,
    user_agent,
)

FIXED_NOW = datetime(2026, 10, 12, 9, 0, 0, tzinfo=UTC)


class Stopwatch:
    """A clock the test moves; ``sleep`` advances it and records the wait."""

    def __init__(self) -> None:
        self.now = 100.0
        self.sleeps: list[float] = []

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def _client(
    tmp_path: Path, transport: FakeTransport, watch: Stopwatch | None = None
) -> tuple[EdgarClient, CaseAppendix]:
    watch = watch or Stopwatch()
    case = CaseAppendix(root=tmp_path, label="closure-1")
    client = EdgarClient(
        appendix=case,
        transport=transport,
        user_agent=USER_AGENT,
        clock=watch.clock,
        sleep=watch.sleep,
        now=lambda: FIXED_NOW,
    )
    return client, case


def test_user_agent_comes_from_local_config_and_is_required() -> None:
    assert (
        user_agent(environ={"HC_SEC_USER_AGENT": USER_AGENT}, git_config=lambda k: "") == USER_AGENT
    )
    assert user_agent(environ={}, git_config=lambda k: USER_AGENT) == USER_AGENT
    with pytest.raises(EdgarError, match="no SEC User-Agent"):
        user_agent(environ={}, git_config=lambda k: "")


def test_a_user_agent_without_a_contact_address_is_refused_without_echoing_it() -> None:
    with pytest.raises(EdgarError, match="contact address") as caught:
        user_agent(environ={"HC_SEC_USER_AGENT": "Just A Name"}, git_config=lambda k: "")
    assert "Just A Name" not in str(caught.value)


def test_the_client_refuses_to_run_without_a_user_agent(tmp_path: Path) -> None:
    with pytest.raises(EdgarError):
        EdgarClient(
            appendix=CaseAppendix(root=tmp_path, label="closure-1"),
            transport=FakeTransport({}),
            user_agent="  ",
        )


def test_the_interval_may_not_be_set_under_a_quarter_second(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"0\.25"):
        EdgarClient(
            appendix=CaseAppendix(root=tmp_path, label="closure-1"),
            transport=FakeTransport({}),
            user_agent=USER_AGENT,
            min_interval=0.1,
        )


def test_a_fetch_sends_the_user_agent_and_caches_body_and_record(tmp_path: Path) -> None:
    body = json.dumps({"name": "Fernwick Canary Holdings"}).encode()
    transport = FakeTransport({SUBMISSIONS_URL: body})
    client, case = _client(tmp_path, transport)

    doc = client.get(SUBMISSIONS_URL)

    assert doc.from_cache is False
    assert doc.json() == {"name": "Fernwick Canary Holdings"}
    assert transport.requests[0][1]["User-Agent"] == USER_AGENT
    key = hashlib.sha256(SUBMISSIONS_URL.encode()).hexdigest()
    assert (case.cache_dir / f"{key}.body").read_bytes() == body
    record = json.loads((case.cache_dir / f"{key}.json").read_text())
    assert record == {
        "url": SUBMISSIONS_URL,
        "sha256": hashlib.sha256(body).hexdigest(),
        "fetched_at": FIXED_NOW.isoformat(),
        "bytes": len(body),
    }


def test_a_cached_url_is_never_fetched_again_even_by_a_new_client(tmp_path: Path) -> None:
    transport = FakeTransport({SUBMISSIONS_URL: b"{}"})
    first, _ = _client(tmp_path, transport)
    first.get(SUBMISSIONS_URL)
    second, _ = _client(tmp_path, FakeTransport({}))  # any request would fail the test
    doc = second.get(SUBMISSIONS_URL)
    assert doc.from_cache is True
    assert len(transport.requests) == 1


def test_requests_are_spaced_at_least_a_quarter_second_apart(tmp_path: Path) -> None:
    watch = Stopwatch()
    transport = FakeTransport({SUBMISSIONS_URL: b"{}", FACTS_URL: b"{}"})
    client, _ = _client(tmp_path, transport, watch)
    client.get(SUBMISSIONS_URL)
    assert watch.sleeps == []  # the first request waits for nothing
    client.get(FACTS_URL)
    assert watch.sleeps == [pytest.approx(0.25)]


def test_a_cache_hit_costs_no_wait_and_does_not_reset_the_spacing(tmp_path: Path) -> None:
    watch = Stopwatch()
    client, _ = _client(tmp_path, FakeTransport({SUBMISSIONS_URL: b"{}", FACTS_URL: b"{}"}), watch)
    client.get(SUBMISSIONS_URL)
    watch.now += 1.0
    client.get(SUBMISSIONS_URL)
    client.get(FACTS_URL)
    assert watch.sleeps == []  # a second has already passed since the one request


@pytest.mark.parametrize("status", [403, 429])
def test_a_403_or_429_stops_the_client_and_nothing_is_retried(tmp_path: Path, status: int) -> None:
    transport = FakeTransport(
        {SUBMISSIONS_URL: Response(status=status, body=b"slow down"), FACTS_URL: b"{}"}
    )
    client, case = _client(tmp_path, transport)
    with pytest.raises(EdgarBlocked):
        client.get(SUBMISSIONS_URL)
    with pytest.raises(EdgarBlocked, match="no further request"):
        client.get(FACTS_URL)
    assert len(transport.requests) == 1
    assert not case.cache_dir.exists()  # a refusal is never cached


def test_a_blocked_client_still_serves_what_is_already_cached(tmp_path: Path) -> None:
    transport = FakeTransport({FACTS_URL: b"{}", SUBMISSIONS_URL: Response(status=429, body=b"")})
    client, _ = _client(tmp_path, transport)
    client.get(FACTS_URL)
    with pytest.raises(EdgarBlocked):
        client.get(SUBMISSIONS_URL)
    assert client.get(FACTS_URL).from_cache is True


def test_another_failure_is_an_error_and_is_not_cached(tmp_path: Path) -> None:
    transport = FakeTransport({SUBMISSIONS_URL: Response(status=404, body=b"")})
    client, case = _client(tmp_path, transport)
    with pytest.raises(EdgarError, match="404"):
        client.get(SUBMISSIONS_URL)
    assert not case.cache_dir.exists()


@pytest.mark.parametrize(
    "url",
    [
        "http://data.sec.gov/submissions/CIK0009999999.json",
        "https://example.com/submissions/CIK0009999999.json",
        "https://data.sec.gov.example.com/x",
        "file:///etc/passwd",
    ],
)
def test_only_https_on_the_secs_own_hosts_is_fetched(tmp_path: Path, url: str) -> None:
    transport = FakeTransport({})
    client, _ = _client(tmp_path, transport)
    with pytest.raises(EdgarError, match="SEC's own hosts"):
        client.get(url)
    assert transport.requests == []


def test_a_tampered_cache_entry_is_refused(tmp_path: Path) -> None:
    client, case = _client(tmp_path, FakeTransport({SUBMISSIONS_URL: b"original"}))
    client.get(SUBMISSIONS_URL)
    body_file = next(case.cache_dir.glob("*.body"))
    body_file.write_bytes(b"changed")
    with pytest.raises(EdgarError, match="cannot be trusted"):
        client.get(SUBMISSIONS_URL)


def test_a_body_without_its_record_is_never_overwritten(tmp_path: Path) -> None:
    client, case = _client(tmp_path, FakeTransport({SUBMISSIONS_URL: b"new"}))
    key = hashlib.sha256(SUBMISSIONS_URL.encode()).hexdigest()
    case.cache_dir.mkdir(parents=True)
    (case.cache_dir / f"{key}.body").write_bytes(b"orphan")
    with pytest.raises(EdgarError, match="no record"):
        client.get(SUBMISSIONS_URL)
    assert (case.cache_dir / f"{key}.body").read_bytes() == b"orphan"


def test_the_cache_refuses_a_location_git_would_track(tmp_path: Path) -> None:
    import subprocess

    repo = tmp_path / "clone"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True)
    case = CaseAppendix(root=repo / "appendix", label="closure-1")
    client = EdgarClient(
        appendix=case, transport=FakeTransport({SUBMISSIONS_URL: b"{}"}), user_agent=USER_AGENT
    )
    with pytest.raises(AppendixError, match="git would track"):
        client.get(SUBMISSIONS_URL)


# --- the real transport, against a stand-in server on loopback (never the SEC) -----------------------------


SEEN: dict[str, str] = {}


@pytest.fixture
def loopback_server() -> Iterator[str]:
    seen = SEEN
    seen.clear()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            seen["user-agent"] = self.headers.get("User-Agent", "")
            if self.path == "/moved":
                self.send_response(302)
                self.send_header("Location", "/ok")
                self.end_headers()
                return
            seen["fetched"] = self.path
            status = 429 if self.path == "/limited" else 200
            self.send_response(status)
            self.end_headers()
            self.wfile.write(b"body")

        def log_message(self, format: str, *args: object) -> None:
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_the_urllib_transport_returns_status_and_body_without_raising_on_http_errors(
    loopback_server: str,
) -> None:
    transport = UrllibTransport(timeout=5.0)
    ok = transport.get(f"{loopback_server}/ok", {"User-Agent": USER_AGENT})
    limited = transport.get(f"{loopback_server}/limited", {"User-Agent": USER_AGENT})
    assert (ok.status, ok.body) == (200, b"body")
    assert limited.status == 429


def test_the_urllib_transport_never_follows_a_redirect(loopback_server: str) -> None:
    moved = UrllibTransport(timeout=5.0).get(f"{loopback_server}/moved", {"User-Agent": USER_AGENT})
    assert moved.status == 302
    assert "fetched" not in SEEN  # the redirect's target was never requested


def test_a_redirect_status_is_an_error_to_the_client(tmp_path: Path) -> None:
    client, case = _client(
        tmp_path, FakeTransport({SUBMISSIONS_URL: Response(status=301, body=b"")})
    )
    with pytest.raises(EdgarError, match="301"):
        client.get(SUBMISSIONS_URL)
    assert not case.cache_dir.exists()


def test_the_urllib_transport_turns_a_connection_failure_into_edgar_error() -> None:
    with pytest.raises(EdgarError, match="request failed"):
        UrllibTransport(timeout=1.0).get("http://127.0.0.1:1/never", {})
