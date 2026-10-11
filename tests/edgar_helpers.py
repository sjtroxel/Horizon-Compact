"""Synthetic EDGAR data for the case builder's tests, shaped like the real fields read on 2026-10-11
(Phase 5 code-half IMPLEMENTATION doc §11). Every name is a fictional canary; nothing here is a real filing.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from horizon_compact.casebuild.edgar import Response

CANARY_CIK = "0009999999"
SUBMISSIONS_URL = f"https://data.sec.gov/submissions/CIK{CANARY_CIK}.json"
FACTS_URL = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{CANARY_CIK}.json"
USER_AGENT = "Canary Test Harness canary@example.invalid"


class FakeTransport:
    """Serves synthetic bodies; any URL not given is an unexpected request and fails the test."""

    def __init__(self, responses: Mapping[str, Response | bytes]) -> None:
        self._responses = dict(responses)
        self.requests: list[tuple[str, dict[str, str]]] = []

    def get(self, url: str, headers: Mapping[str, str]) -> Response:
        self.requests.append((url, dict(headers)))
        if url not in self._responses:
            raise AssertionError(f"unexpected request: {url}")
        reply = self._responses[url]
        return reply if isinstance(reply, Response) else Response(status=200, body=reply)


def submissions_recent() -> dict[str, list[Any]]:
    """A ``filings.recent`` table: parallel lists, ``items`` one comma-separated string, acceptance in UTC."""
    return {
        "accessionNumber": [
            "0009999999-26-000003",
            "0009999999-26-000002",
            "0009999999-26-000001",
        ],
        "filingDate": ["2026-08-20", "2026-05-08", "2026-03-02"],
        "reportDate": ["2026-08-19", "2026-03-31", "2026-01-31"],
        "acceptanceDateTime": [
            "2026-08-21T02:00:00.000Z",  # 22:00 US Eastern on 2026-08-20: after the close, dated the 20th
            "2026-05-08T20:15:30.000Z",
            "2026-03-02T21:05:00.000Z",
        ],
        "form": ["8-K", "10-Q", "10-K"],
        "items": ["2.05,9.01", "", ""],
        "primaryDocument": ["canary-8k.htm", "canary-10q.htm", "canary-10k.htm"],
        "size": [1200, 52000, 90000],
        "isXBRL": [0, 1, 1],
    }


def submissions_row(index: int) -> dict[str, Any]:
    table = submissions_recent()
    return {name: values[index] for name, values in table.items()}


def company_fact(**overrides: Any) -> dict[str, Any]:
    """One tagged figure: ``fy`` and ``fp`` describe the filing, ``frame`` is added after the fact."""
    fact: dict[str, Any] = {
        "start": "2025-02-01",
        "end": "2026-01-31",
        "val": 1_234_000_000,
        "accn": "0009999999-26-000001",
        "fy": 2025,
        "fp": "FY",
        "form": "10-K",
        "filed": "2026-03-02",
    }
    fact.update(overrides)
    return fact
