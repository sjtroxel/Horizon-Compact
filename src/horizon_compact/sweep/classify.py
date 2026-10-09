"""One attempt's status, from the raw decision and the validation (Phase 1 IMPLEMENTATION doc section 6.4).

Every row of the table is here. ``api_error`` and ``config_error`` are **not model outcomes**: they are not
counted against the retry budget and are not a run's final status. A retry is a fresh identical request (same
prompt, same menu order, no repair message), so nothing here ever edits a request.

An error code the table does not name is treated as ``config_error``, which stops the session: the safe
direction, since a session that stops can be re-launched and resumes, and a session that retries an unknown
error forever cannot.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from horizon_compact.experiment import Scenario
from horizon_compact.providers.base import RawDecision
from horizon_compact.sweep.decision import Validation, validate_decision
from horizon_compact.sweep.prompt import TOOL_NAME

Status = Literal[
    "valid",
    "valid_rescaled",
    "refusal",
    "truncated",
    "malformed_tool_use",
    "no_tool_call",
    "multiple_calls",
    "schema_invalid",
    "sum_mismatch",
    "unexpected_stop",
    "api_error",
    "config_error",
]
Retry = Literal["none", "model", "backoff"]

MAX_MODEL_ATTEMPTS = 3  # the first attempt plus up to two retries
NON_MODEL_STATUSES = frozenset({"api_error", "config_error"})

# Statuses that earn a retry (a fresh identical request) while the run has attempts left.
RETRYABLE_MODEL_STATUSES = frozenset(
    {
        "truncated",
        "malformed_tool_use",
        "no_tool_call",
        "multiple_calls",
        "schema_invalid",
        "sum_mismatch",
    }
)

_NORMAL_STOPS = frozenset({"tool_use", "end_turn"})
_BACKOFF_CODES = frozenset(
    {
        "ThrottlingException",
        "ServiceUnavailableException",
        "InternalServerException",
        "ModelNotReadyException",
        "ModelTimeoutException",
    }
)
_NETWORK_ERRORS = frozenset(
    {
        "EndpointConnectionError",
        "ConnectionClosedError",
        "ConnectTimeoutError",
        "ReadTimeoutError",
        "ProxyConnectionError",
        "SSLError",
        "HTTPClientError",
    }
)
# Carried from Phase 0.5: Bedrock reports a malformed tool call as ModelErrorException.
_MALFORMED_CODES = frozenset({"ModelErrorException"})
# S4's option is named "decline", so the bare word is not a refusal: it counts only as "decline to" or
# "declining to" in a clause that starts with "I" ("I'm going to have to decline to"). "refuse" names no
# option and stays broad (Phase 3.5 IMPLEMENTATION doc section 16 step 2).
_DECLINE = re.compile(
    r"won't|will not|cannot|can't|unable to|refus|\bI\b[^.!?\n]{0,30}?\bdeclin(?:e|ing)\s+to\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Outcome:
    status: Status
    retry: Retry = "none"
    stop_session: bool = False
    possible_decline: bool = False
    validation: Validation | None = None
    detail: str | None = None
    # Why the session stops, when ``stop_session`` is set.
    stop_as: str = "config_error"

    @property
    def is_model_outcome(self) -> bool:
        return self.status not in NON_MODEL_STATUSES


def classify_error(raw: RawDecision) -> Outcome:
    """An API error's outcome: retried with backoff, or the session stops (also used by the probes)."""
    code = (raw.error or {}).get("code", "")
    message = (raw.error or {}).get("message", "")
    # A *daily* limit will not clear in minutes, so retrying inside a 30-minute session only hides it (seen
    # 2026-10-05: Nova Lite answered "Too many tokens per day" to every call). Stop and say so.
    if code == "ThrottlingException" and "per day" in message.lower():
        return Outcome(
            "api_error",
            stop_session=True,
            stop_as="quota_exhausted",
            detail=f"{code}: {message}",
        )
    if code in _BACKOFF_CODES or code in _NETWORK_ERRORS:
        return Outcome("api_error", retry="backoff", detail=code)
    if code in _MALFORMED_CODES:
        return Outcome("malformed_tool_use", retry="model", detail=code)
    # ValidationException, AccessDeniedException, ResourceNotFoundException, and anything not named.
    return Outcome("config_error", stop_session=True, detail=code or "unknown error")


def classify(raw: RawDecision, scenario: Scenario) -> Outcome:
    if raw.status == "api_error":
        return classify_error(raw)

    stop = raw.stop_reason
    if stop == "max_tokens":
        return Outcome("truncated", retry="model")
    if stop == "content_filtered":
        return Outcome("refusal")
    if stop == "malformed_tool_use":
        return Outcome("malformed_tool_use", retry="model")
    if stop not in _NORMAL_STOPS:
        return Outcome("unexpected_stop", detail=str(stop))

    count = raw.tool_call_count
    if count == 0:
        declined = any(_DECLINE.search(text) for text in raw.text_blocks)
        return Outcome("no_tool_call", retry="model", possible_decline=declined)
    if count > 1:
        return Outcome("multiple_calls", retry="model")

    call = raw.tool_calls[0]
    if call.get("name") != TOOL_NAME:
        return Outcome("schema_invalid", retry="model", detail=f"tool name {call.get('name')!r}")
    validation = validate_decision(scenario, call.get("input"))
    if validation.ok:
        return Outcome(validation.status, validation=validation)
    return Outcome(validation.status, retry="model", validation=validation)
