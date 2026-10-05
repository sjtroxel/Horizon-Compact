"""One write-once JSON record per smoke call, with the account id removed and checked (section 11.7).

Fail closed: if the serialized record still contains the account id, or any email address, nothing is written.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from horizon_compact.providers.base import DecisionRequest, RawDecision
from horizon_compact.smoke.plan import (
    EXPECTED_KILOMETERS,
    EXPECTED_TOLERANCE,
    PRICE_SOURCE,
    PRICES,
    TOOL,
)

RECORD_VERSION = 1
PLACEHOLDER = "<account-id>"
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[A-Za-z]{2,}")
_ACCOUNT_ID_SHAPE = re.compile(r"(?<![\w-])\d{12}(?![\w-])")


class RedactionError(Exception):
    """The record could not be made safe to publish. Nothing was written."""


def check_tool_input(raw: RawDecision) -> dict[str, Any]:
    """Section 11.6: checked by hand, not with pydantic. Problems are listed, never raised."""
    problems: list[str] = []
    count = raw.tool_call_count
    if count == 0:
        problems.append("no tool call")
    elif count > 1:
        problems.append(f"{count} tool calls (expected exactly one)")
    answer_correct: bool | None = None
    if count >= 1:
        call = raw.tool_calls[0]
        if call.get("name") != TOOL.name:
            problems.append(f"tool name {call.get('name')!r}, expected {TOOL.name!r}")
        data = call.get("input")
        expected_keys = {"kilometers", "unit_system", "note"}
        if not isinstance(data, dict):
            problems.append("tool input is not an object")
        else:
            if set(data) != expected_keys:
                problems.append(f"keys {sorted(data)} differ from {sorted(expected_keys)}")
            km = data.get("kilometers")
            if isinstance(km, bool) or not isinstance(km, int | float):
                problems.append("kilometers is not a number")
            elif km < 0 or math.isnan(km):
                problems.append("kilometers is negative or not a number")
            else:
                answer_correct = abs(km - EXPECTED_KILOMETERS) <= EXPECTED_TOLERANCE
            if data.get("unit_system") not in ("metric", "imperial"):
                problems.append("unit_system is not metric or imperial")
            note = data.get("note")
            if not isinstance(note, str) or not note.strip():
                problems.append("note is not a non-empty string")
    return {"valid": not problems, "problems": problems, "answer_correct": answer_correct}


def estimate_cost_usd(model_id: str, input_tokens: int, output_tokens: int) -> float | None:
    prices = PRICES.get(model_id)
    if prices is None:
        return None
    return round((input_tokens * prices[0] + output_tokens * prices[1]) / 1_000_000, 6)


def _json_safe(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def build_record(
    *,
    call_name: str,
    again_reason: str | None,
    request: DecisionRequest,
    body: dict[str, Any],
    raw: RawDecision,
    git_sha: str,
    git_dirty: bool,
    harness_version: str,
    botocore_version: str,
) -> dict[str, Any]:
    prov = raw.provenance
    return {
        "record_version": RECORD_VERSION,
        "label": "development",
        "call_name": call_name,
        "again_reason": again_reason,
        "git_sha": git_sha,
        "git_dirty": git_dirty,
        "harness_version": harness_version,
        "botocore_version": botocore_version,
        "provider": prov.provider,
        "api": prov.api,
        "model_id": prov.model_id,
        "invoke_id": prov.invoke_id,
        "route_kind": prov.route_kind,
        "inference_profile": prov.inference_profile,
        "region": prov.region,
        "thinking": prov.thinking,
        "effort": prov.effort,
        "temperature": prov.temperature,
        "max_tokens": prov.max_tokens,
        "prompt_sha256": prov.prompt_sha256,
        "request": _json_safe(body),
        "started_at": prov.started_at,
        "finished_at": prov.finished_at,
        "latency_ms": prov.latency_ms,
        "status": raw.status,
        "error": raw.error,
        "stop_reason": raw.stop_reason,
        "usage": asdict(raw.usage),
        "tool_call_count": raw.tool_call_count,
        "tool_input": _json_safe(raw.tool_input),
        "tool_input_check": check_tool_input(raw),
        "text_blocks": raw.text_blocks,
        "reasoning_block_count": raw.reasoning_block_count,
        "additional_model_response_fields": _json_safe(
            (raw.raw_response or {}).get("additionalModelResponseFields")
        ),
        "raw_response": _json_safe(raw.raw_response),
        "est_cost_usd": estimate_cost_usd(
            request.route.model_id, raw.usage.input_tokens, raw.usage.output_tokens
        ),
        "price_source": PRICE_SOURCE,
    }


def redact(text: str, account_id: str) -> str:
    return text.replace(account_id, PLACEHOLDER)


def assert_clean(text: str, account_id: str) -> None:
    """Fail closed. Called on the serialized record after redaction."""
    if account_id in text:
        raise RedactionError("the account id is still present after redaction")
    if _EMAIL.search(text):
        raise RedactionError("an email address is present in the record")
    if _ACCOUNT_ID_SHAPE.search(text):
        raise RedactionError("a 12-digit number is present in the record")


def serialize_safely(record: dict[str, Any], account_id: str) -> str:
    text = json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    text = redact(text, account_id)
    assert_clean(text, account_id)
    return text


def write_once(path: Path, text: str) -> None:
    """Exclusive create: an existing record is never overwritten."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(text)
