"""The EDGAR client (IMPLEMENTATION §4.2).

SEC rules checked live 2026-10-11: at most 10 requests a second and a declared User-Agent with a contact
address. This client:

- reads the User-Agent from local config (``HC_SEC_USER_AGENT`` or git config ``hc.secUserAgent``) and refuses
  to run without it;
- spaces network requests at least 0.25 s apart (4 a second, well under the limit); a cache hit costs no wait;
- **stops on a 403 or 429**: raises, and refuses every later uncached request, rather than retrying;
- caches every successful response in the case's appendix, write-once, keyed by URL, with its sha256 and fetch
  time; a cached URL is never fetched again (filings do not change);
- takes a transport object, so tests serve synthetic files from a fake and fail on any unexpected URL.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlsplit

from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.config import git_config_value, setting

ENV_VAR = "HC_SEC_USER_AGENT"
GIT_CONFIG_KEY = "hc.secUserAgent"
MIN_INTERVAL_SECONDS = 0.25
ALLOWED_HOSTS = frozenset(
    {"www.sec.gov", "data.sec.gov", "efts.sec.gov"}
)  # efts: full-text search (step 7)
BLOCKED_STATUSES = frozenset({403, 429})


class EdgarError(Exception):
    """A request failed or the cache cannot be trusted."""


class EdgarBlocked(EdgarError):
    """The SEC answered 403 or 429. Nothing is retried, and no later request is sent."""


@dataclass(frozen=True)
class Response:
    status: int
    body: bytes


class Transport(Protocol):
    def get(self, url: str, headers: Mapping[str, str]) -> Response: ...


class _RefuseRedirects(urllib.request.HTTPRedirectHandler):
    """A redirect is never followed: the client checked the first URL's host, and would not see the next."""

    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        return None


class UrllibTransport:
    """The real transport. Built by hand for the one read-only request; no test uses it against the SEC.

    A redirect comes back as its 3xx status, which the client treats as an error.
    """

    def __init__(self, timeout: float = 30.0) -> None:
        self._timeout = timeout
        self._opener = urllib.request.build_opener(_RefuseRedirects())

    def get(self, url: str, headers: Mapping[str, str]) -> Response:
        request = urllib.request.Request(url, headers=dict(headers))
        try:
            with self._opener.open(request, timeout=self._timeout) as reply:
                return Response(status=reply.status, body=reply.read())
        except urllib.error.HTTPError as exc:
            return Response(status=exc.code, body=exc.read())
        except (urllib.error.URLError, OSError) as exc:
            raise EdgarError(f"the request failed: {type(exc).__name__}") from exc


@dataclass(frozen=True)
class Document:
    url: str
    body: bytes
    sha256: str
    fetched_at: str
    from_cache: bool

    def json(self) -> Any:
        return json.loads(self.body)


def user_agent(
    *,
    environ: Mapping[str, str] | None = None,
    git_config: Callable[[str], str] = git_config_value,
) -> str:
    """The declared User-Agent, from local config only. The message never repeats it."""
    value = setting(ENV_VAR, GIT_CONFIG_KEY, environ=environ, git_config=git_config)
    if not value:
        raise EdgarError(
            f"no SEC User-Agent is configured: set {ENV_VAR} or local git config {GIT_CONFIG_KEY} "
            "(a name and a contact address; the SEC requires one)."
        )
    if "@" not in value:
        raise EdgarError("the SEC User-Agent must include a contact address")
    return value


def _utc_now() -> datetime:
    return datetime.now(UTC)


class EdgarClient:
    def __init__(
        self,
        *,
        appendix: CaseAppendix,
        transport: Transport,
        user_agent: str,
        min_interval: float = MIN_INTERVAL_SECONDS,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        now: Callable[[], datetime] = _utc_now,
    ) -> None:
        if min_interval < MIN_INTERVAL_SECONDS:
            raise ValueError(
                f"the interval between requests may not be under {MIN_INTERVAL_SECONDS} s"
            )
        if not user_agent.strip():
            raise EdgarError("a User-Agent is required")
        self._appendix = appendix
        self._transport = transport
        self._user_agent = user_agent
        self._min_interval = min_interval
        self._clock = clock
        self._sleep = sleep
        self._now = now
        self._last_request: float | None = None
        self._blocked = False

    @staticmethod
    def _check_url(url: str) -> None:
        parts = urlsplit(url)
        if parts.scheme != "https" or parts.hostname not in ALLOWED_HOSTS:
            raise EdgarError("only https URLs on the SEC's own hosts are fetched")

    def _paths(self, url: str) -> tuple[Path, Path]:
        key = hashlib.sha256(url.encode("utf-8")).hexdigest()
        cache = self._appendix.cache_dir
        return cache / f"{key}.body", cache / f"{key}.json"

    def _wait(self) -> None:
        if self._last_request is not None:
            remaining = self._last_request + self._min_interval - self._clock()
            if remaining > 0:
                self._sleep(remaining)
        self._last_request = self._clock()

    def get(self, url: str) -> Document:
        self._check_url(url)
        body_path, meta_path = self._paths(url)
        if meta_path.exists():
            return self._read_cached(url, body_path, meta_path)
        if body_path.exists():
            raise EdgarError(
                "a cache entry has a body but no record; resolve it by hand, nothing is overwritten"
            )
        if self._blocked:
            raise EdgarBlocked("the SEC refused an earlier request; no further request is sent")

        self._wait()
        response = self._transport.get(
            url, {"User-Agent": self._user_agent, "Accept-Encoding": "identity"}
        )
        if response.status in BLOCKED_STATUSES:
            self._blocked = True
            raise EdgarBlocked(f"the SEC answered {response.status}; stopped, nothing retried")
        if response.status != 200:
            raise EdgarError(f"the SEC answered {response.status} for a request")

        digest = hashlib.sha256(response.body).hexdigest()
        fetched_at = self._now().isoformat()
        record = {
            "url": url,
            "sha256": digest,
            "fetched_at": fetched_at,
            "bytes": len(response.body),
        }
        # Body first, record second: the record is what makes an entry count as cached.
        self._appendix.write_once(body_path, response.body)
        self._appendix.write_once(meta_path, json.dumps(record, indent=2).encode("utf-8"))
        return Document(
            url=url, body=response.body, sha256=digest, fetched_at=fetched_at, from_cache=False
        )

    def _read_cached(self, url: str, body_path: Path, meta_path: Path) -> Document:
        try:
            record = json.loads(meta_path.read_bytes())
            body = body_path.read_bytes()
        except (OSError, ValueError) as exc:
            raise EdgarError("a cache entry cannot be read") from exc
        if record.get("url") != url or record.get("sha256") != hashlib.sha256(body).hexdigest():
            raise EdgarError("a cache entry does not match its record; the cache cannot be trusted")
        return Document(
            url=url,
            body=body,
            sha256=record["sha256"],
            fetched_at=record["fetched_at"],
            from_cache=True,
        )
