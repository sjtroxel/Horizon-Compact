"""Run exactly one smoke call. Every refusal happens before any model call (section 11.1)."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from horizon_compact.providers.base import DecisionRequest, ModelRoute, Provider
from horizon_compact.providers.bedrock import build_request
from horizon_compact.smoke import plan
from horizon_compact.smoke.record import build_record, serialize_safely, write_once

if TYPE_CHECKING:
    from mypy_boto3_bedrock import BedrockClient


class SmokeRefusal(Exception):
    """The call was refused before any model call was made."""


@dataclass(frozen=True)
class GitInfo:
    sha: str
    dirty: bool


@dataclass(frozen=True)
class Versions:
    harness: str
    botocore: str


@dataclass(frozen=True)
class RunResult:
    path: Path
    record: dict[str, Any]


def existing_records(evidence_dir: Path) -> list[Path]:
    return sorted(evidence_dir.glob("*.json")) if evidence_dir.exists() else []


def record_path(call: plan.SmokeCall, evidence_dir: Path, *, again: bool) -> Path:
    base = f"{call.number:02d}-{call.name}"
    first = evidence_dir / f"{base}.json"
    if not again:
        return first
    n = 2
    while (evidence_dir / f"{base}.{n}.json").exists():
        n += 1
    return evidence_dir / f"{base}.{n}.json"


def resolve_profile_arn(control: BedrockClient, name: str) -> str:
    """The profile's ARN, found by name, so the account id it contains lives in no file."""
    matches: list[str] = []
    token: str | None = None
    while True:
        kwargs: dict[str, Any] = {"typeEquals": "APPLICATION"}
        if token:
            kwargs["nextToken"] = token
        page = control.list_inference_profiles(**kwargs)
        matches.extend(
            s["inferenceProfileArn"]
            for s in page.get("inferenceProfileSummaries", [])
            if s.get("inferenceProfileName") == name
        )
        token = page.get("nextToken")
        if not token:
            break
    if len(matches) != 1:
        raise SmokeRefusal(
            f"expected one application inference profile named {name!r}, found {len(matches)}"
        )
    return matches[0]


def check_before_calling(
    name: str, evidence_dir: Path, *, confirm_access: bool, again_reason: str | None
) -> plan.SmokeCall:
    call = plan.find_call(name)
    if call is None:
        raise SmokeRefusal(f"unknown call {name!r}; see 'hc smoke list'")
    if call.conditional and not confirm_access:
        raise SmokeRefusal(f"{name} is conditional on access having arrived; pass --confirm-access")
    if len(existing_records(evidence_dir)) >= plan.MAX_RECORDS:
        raise SmokeRefusal(
            f"{plan.MAX_RECORDS} records already exist; the phase's call cap is reached"
        )
    if record_path(call, evidence_dir, again=False).exists() and not again_reason:
        raise SmokeRefusal(f'{name} already has a record; pass --again "<reason>" to make another')
    return call


def run_call(
    name: str,
    *,
    evidence_dir: Path,
    provider: Provider,
    control: BedrockClient,
    account_id: str,
    git: GitInfo,
    versions: Versions,
    confirm_access: bool = False,
    again_reason: str | None = None,
) -> RunResult:
    call = check_before_calling(
        name, evidence_dir, confirm_access=confirm_access, again_reason=again_reason
    )
    route: ModelRoute = call.route
    if route.route_kind == "application_profile":
        assert route.inference_profile is not None
        route = dataclasses.replace(
            route, invoke_id=resolve_profile_arn(control, route.inference_profile)
        )
    request = DecisionRequest(
        route=route,
        system=plan.SYSTEM,
        user=plan.USER,
        tool=plan.TOOL,
        max_tokens=call.max_tokens,
        additional_fields=call.additional_fields,
    )
    raw = provider.decide(request)
    record = build_record(
        call_name=call.name,
        again_reason=again_reason,
        request=request,
        body=build_request(request),
        raw=raw,
        git_sha=git.sha,
        git_dirty=git.dirty,
        harness_version=versions.harness,
        botocore_version=versions.botocore,
    )
    text = serialize_safely(record, account_id)
    path = record_path(call, evidence_dir, again=bool(again_reason))
    write_once(path, text)
    return RunResult(path=path, record=record)
