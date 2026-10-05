"""Every row of the classification table (Phase 1 IMPLEMENTATION doc section 6.4)."""

from __future__ import annotations

from typing import Any

import pytest

from horizon_compact.sweep.classify import NON_MODEL_STATUSES, Outcome, classify
from horizon_compact.sweep.prompt import TOOL_NAME
from sweep_helpers import dummy_request, experiment, raw_error, raw_ok, valid_input

SCENARIO = experiment().scenario


def outcome(raw: Any) -> Outcome:
    return classify(raw, SCENARIO)


def ok(**kwargs: Any) -> Any:
    return raw_ok(dummy_request(), **kwargs)


def test_one_valid_call_is_valid_and_final() -> None:
    result = outcome(ok())
    assert (result.status, result.retry) == ("valid", "none")
    assert result.validation is not None


def test_a_rescaled_call_is_valid_rescaled_and_final() -> None:
    data = valid_input()
    data["amounts"]["raffle"] = 190
    result = outcome(ok(tool_input=data))
    assert (result.status, result.retry) == ("valid_rescaled", "none")


def test_max_tokens_is_truncated_and_retried() -> None:
    assert (outcome(ok(stop="max_tokens")).status, outcome(ok(stop="max_tokens")).retry) == (
        "truncated",
        "model",
    )


def test_content_filtered_is_a_refusal_and_never_retried() -> None:
    result = outcome(ok(stop="content_filtered", calls=[]))
    assert (result.status, result.retry) == ("refusal", "none")


def test_malformed_tool_use_by_stop_reason_or_by_model_error_is_retried() -> None:
    by_stop = outcome(ok(stop="malformed_tool_use", calls=[]))
    by_error = outcome(raw_error(dummy_request(), "ModelErrorException"))
    for result in (by_stop, by_error):
        assert (result.status, result.retry, result.stop_session) == (
            "malformed_tool_use",
            "model",
            False,
        )
    assert by_error.is_model_outcome


def test_no_tool_call_is_retried_and_a_decline_is_flagged_for_a_human() -> None:
    plain = outcome(ok(calls=[], stop="end_turn", text=["Here is my plan in words."]))
    assert (plain.status, plain.retry, plain.possible_decline) == ("no_tool_call", "model", False)
    declined = outcome(ok(calls=[], stop="end_turn", text=["I'm unable to help with this."]))
    assert declined.possible_decline is True
    assert (
        outcome(ok(calls=[], stop="end_turn", text=["I won't do this."])).possible_decline is True
    )


def test_text_beside_one_call_is_not_no_tool_call() -> None:
    result = outcome(ok(text=["Some words beside the call."]))
    assert result.status == "valid"


def test_two_calls_are_multiple_calls_and_retried() -> None:
    call = {"name": TOOL_NAME, "input": valid_input()}
    result = outcome(ok(calls=[call, call]))
    assert (result.status, result.retry) == ("multiple_calls", "model")


def test_a_call_to_another_tool_is_schema_invalid_and_retried() -> None:
    result = outcome(ok(calls=[{"name": "other", "input": valid_input()}]))
    assert (result.status, result.retry) == ("schema_invalid", "model")


def test_validation_failures_are_retried() -> None:
    bad = valid_input(open_day_season="winter")
    assert (outcome(ok(tool_input=bad)).status, outcome(ok(tool_input=bad)).retry) == (
        "schema_invalid",
        "model",
    )
    unbalanced = valid_input()
    unbalanced["amounts"]["raffle"] = 0
    assert (
        outcome(ok(tool_input=unbalanced)).status,
        outcome(ok(tool_input=unbalanced)).retry,
    ) == (
        "sum_mismatch",
        "model",
    )


@pytest.mark.parametrize(
    "stop", ["guardrail_intervened", "model_context_window_exceeded", "something_new", None]
)
def test_any_other_stop_reason_is_unexpected_and_not_retried(stop: str | None) -> None:
    result = outcome(ok(stop=stop or "", calls=[]))
    assert (result.status, result.retry) == ("unexpected_stop", "none")


@pytest.mark.parametrize(
    "code",
    [
        "ThrottlingException",
        "ServiceUnavailableException",
        "InternalServerException",
        "ModelNotReadyException",
        "ModelTimeoutException",
        "EndpointConnectionError",
        "ReadTimeoutError",
    ],
)
def test_transient_errors_are_api_errors_with_backoff_and_are_not_model_outcomes(code: str) -> None:
    result = outcome(raw_error(dummy_request(), code))
    assert (result.status, result.retry, result.stop_session) == ("api_error", "backoff", False)
    assert not result.is_model_outcome


@pytest.mark.parametrize(
    "code", ["ValidationException", "AccessDeniedException", "ResourceNotFoundException"]
)
def test_request_errors_stop_the_session(code: str) -> None:
    result = outcome(raw_error(dummy_request(), code))
    assert (result.status, result.stop_session, result.retry) == ("config_error", True, "none")
    assert result.status in NON_MODEL_STATUSES


def test_an_error_code_the_table_does_not_name_stops_the_session() -> None:
    result = outcome(raw_error(dummy_request(), "SomethingNew"))
    assert (result.status, result.stop_session, result.detail) == (
        "config_error",
        True,
        "SomethingNew",
    )


DAILY = "Too many tokens per day, please wait before trying again."


def test_a_daily_quota_throttle_stops_the_session_as_quota_exhausted() -> None:
    """Seen 2026-10-05: Nova Lite answered this to every call, and retrying only hid it."""
    result = outcome(raw_error(dummy_request(), "ThrottlingException", DAILY))
    assert (result.status, result.stop_session, result.stop_as) == (
        "api_error",
        True,
        "quota_exhausted",
    )
    assert "per day" in (result.detail or "")
    assert not result.is_model_outcome


def test_an_ordinary_throttle_still_backs_off_and_does_not_stop() -> None:
    result = outcome(
        raw_error(dummy_request(), "ThrottlingException", "Too many requests, please wait.")
    )
    assert (result.status, result.retry, result.stop_session) == ("api_error", "backoff", False)
