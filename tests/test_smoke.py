"""The smoke command: refusals, records, redaction and the tool-input check. No network, no credentials."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import boto3
import pytest

from horizon_compact import cli
from horizon_compact.providers.bedrock import BedrockConverseProvider
from horizon_compact.smoke import plan
from horizon_compact.smoke.record import (
    RedactionError,
    assert_clean,
    check_tool_input,
    write_once,
)
from horizon_compact.smoke.runner import GitInfo, SmokeRefusal, Versions, run_call

if TYPE_CHECKING:
    from mypy_boto3_bedrock import BedrockClient
    from mypy_boto3_bedrock_runtime import BedrockRuntimeClient

ACCOUNT = "123456789012"
PROFILE_ARN = f"arn:aws:bedrock:us-east-1:{ACCOUNT}:application-inference-profile/abc123"
GIT = GitInfo(sha="deadbeef", dirty=False)
VERSIONS = Versions(harness="0.0.0", botocore="1.0")


def good_response(km: float = 19.31) -> dict[str, Any]:
    return {
        "output": {
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "toolUse": {
                            "toolUseId": "t1",
                            "name": "record_conversion",
                            "input": {
                                "kilometers": km,
                                "unit_system": "metric",
                                "note": "12 x 1.609344.",
                            },
                        }
                    }
                ],
            }
        },
        "stopReason": "tool_use",
        "usage": {"inputTokens": 300, "outputTokens": 60, "totalTokens": 360},
        "metrics": {"latencyMs": 900},
    }


class FakeRuntime:
    def __init__(self, response: dict[str, Any] | Exception) -> None:
        self.response = response
        self.sent: list[dict[str, Any]] = []

    def converse(self, **kwargs: Any) -> dict[str, Any]:
        self.sent.append(kwargs)
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class FakeControl:
    def __init__(
        self, names: tuple[str, ...] = ("horizon-compact-sonnet-4-6", "horizon-compact-nova-pro")
    ):
        self.names = names

    def list_inference_profiles(self, **kwargs: Any) -> dict[str, Any]:
        assert kwargs["typeEquals"] == "APPLICATION"
        return {
            "inferenceProfileSummaries": [
                {"inferenceProfileName": n, "inferenceProfileArn": PROFILE_ARN} for n in self.names
            ]
        }


def run(
    name: str, tmp: Path, response: dict[str, Any] | Exception | None = None, **kwargs: Any
) -> tuple[Any, FakeRuntime]:
    runtime = FakeRuntime(good_response() if response is None else response)
    provider = BedrockConverseProvider(cast("BedrockRuntimeClient", runtime))
    result = run_call(
        name,
        evidence_dir=tmp,
        provider=provider,
        control=cast("BedrockClient", FakeControl()),
        account_id=ACCOUNT,
        git=GIT,
        versions=VERSIONS,
        **kwargs,
    )
    return result, runtime


# --- the plan --------------------------------------------------------------------------------------------


def test_plan_names_and_numbers_are_unique_and_the_cap_leaves_three_spare() -> None:
    assert [c.number for c in plan.PLAN] == list(range(1, 10))
    assert len({c.name for c in plan.PLAN}) == 9
    assert len(plan.PLAN) + 3 == plan.MAX_RECORDS


def test_only_the_two_sonnet_55_calls_are_conditional() -> None:
    assert {c.name for c in plan.PLAN if c.conditional} == {
        "sonnet55-default",
        "sonnet55-between-tools",
    }


def test_the_prompt_and_tool_stay_off_the_experiments_subject() -> None:
    text = (
        plan.SYSTEM + plan.USER + json.dumps(plan.TOOL.input_schema) + plan.TOOL.description
    ).lower()
    hits = [word for word in plan.SUBJECT_VOCABULARY if word in text]
    assert not hits, f"subject vocabulary in the smoke prompt: {hits}"


def test_the_tool_has_the_three_fields_and_forbids_extras() -> None:
    schema = plan.TOOL.input_schema
    assert set(schema["required"]) == {"kilometers", "unit_system", "note"}
    assert schema["additionalProperties"] is False


# --- a successful call -----------------------------------------------------------------------------------


def test_a_good_call_writes_a_redacted_development_record(tmp_path: Path) -> None:
    result, runtime = run("sonnet46-profile-off", tmp_path)
    assert result.path.name == "01-sonnet46-profile-off.json"
    text = result.path.read_text(encoding="utf-8")
    assert ACCOUNT not in text
    assert "<account-id>" in text
    record = json.loads(text)
    assert record["label"] == "development"
    assert record["temperature"] == "not set"
    assert record["thinking"] == "not set"
    assert record["tool_input_check"] == {"valid": True, "problems": [], "answer_correct": True}
    assert record["usage"]["input_tokens"] == 300
    assert record["est_cost_usd"] == pytest.approx((300 * 3.30 + 60 * 16.50) / 1_000_000)
    for absent in ("sweep_id", "run_id", "image_digest"):
        assert absent not in record
    # the call itself used the resolved ARN, unredacted
    assert runtime.sent[0]["modelId"] == PROFILE_ARN
    assert "temperature" not in runtime.sent[0]["inferenceConfig"]


def test_the_adaptive_call_sends_thinking_and_effort_and_records_them(tmp_path: Path) -> None:
    result, runtime = run("sonnet46-profile-adaptive", tmp_path)
    assert runtime.sent[0]["additionalModelRequestFields"] == {
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": "high"},
    }
    assert result.record["thinking"] == '{"type": "adaptive"}'
    assert result.record["effort"] == "high"


def test_a_geo_route_sends_its_profile_id_and_needs_no_lookup(tmp_path: Path) -> None:
    _, runtime = run("sonnet46-geo-off", tmp_path)
    assert runtime.sent[0]["modelId"] == "us.anthropic.claude-sonnet-4-6"


# --- refusals, all before any model call -----------------------------------------------------------------


def test_unknown_call_is_refused(tmp_path: Path) -> None:
    with pytest.raises(SmokeRefusal, match="unknown call"):
        run("nope", tmp_path)


def test_a_call_with_a_record_is_refused_without_again(tmp_path: Path) -> None:
    run("novalite", tmp_path)
    runtime_before = FakeRuntime(good_response())
    with pytest.raises(SmokeRefusal, match="already has a record"):
        run("novalite", tmp_path)
    assert runtime_before.sent == []


def test_again_writes_a_new_record_and_keeps_the_old_one(tmp_path: Path) -> None:
    first, _ = run("novalite", tmp_path)
    before = first.path.read_text(encoding="utf-8")
    second, _ = run("novalite", tmp_path, again_reason="harness bug fixed")
    assert second.path.name == "06-novalite.2.json"
    assert second.record["again_reason"] == "harness bug fixed"
    assert first.path.read_text(encoding="utf-8") == before
    third, _ = run("novalite", tmp_path, again_reason="throttled")
    assert third.path.name == "06-novalite.3.json"


def test_a_conditional_call_needs_confirmation(tmp_path: Path) -> None:
    with pytest.raises(SmokeRefusal, match="--confirm-access"):
        run("sonnet55-default", tmp_path)
    result, _ = run("sonnet55-default", tmp_path, confirm_access=True)
    assert result.record["model_id"] == "anthropic.claude-sonnet-5-5"


def test_the_thirteenth_record_is_refused(tmp_path: Path) -> None:
    for i in range(plan.MAX_RECORDS):
        (tmp_path / f"filler-{i}.json").write_text("{}", encoding="utf-8")
    with pytest.raises(SmokeRefusal, match="cap is reached"):
        run("novalite", tmp_path)


def test_a_missing_profile_is_refused_before_calling(tmp_path: Path) -> None:
    runtime = FakeRuntime(good_response())
    with pytest.raises(SmokeRefusal, match="found 0"):
        run_call(
            "sonnet46-profile-off",
            evidence_dir=tmp_path,
            provider=BedrockConverseProvider(cast("BedrockRuntimeClient", runtime)),
            control=cast("BedrockClient", FakeControl(names=())),
            account_id=ACCOUNT,
            git=GIT,
            versions=VERSIONS,
        )
    assert runtime.sent == []
    assert list(tmp_path.iterdir()) == []


def test_write_once_never_overwrites(tmp_path: Path) -> None:
    target = tmp_path / "r.json"
    write_once(target, "first")
    with pytest.raises(FileExistsError):
        write_once(target, "second")
    assert target.read_text(encoding="utf-8") == "first"


# --- redaction fails closed ------------------------------------------------------------------------------


def text_response(text: str) -> dict[str, Any]:
    resp = good_response()
    resp["output"]["message"]["content"] = [{"text": text}]
    resp["stopReason"] = "end_turn"
    return resp


@pytest.mark.parametrize("leak", ["write to someone@example.com", "id 999988887777 here"])
def test_a_record_that_cannot_be_made_safe_is_not_written(tmp_path: Path, leak: str) -> None:
    with pytest.raises(RedactionError):
        run("novalite", tmp_path, response=text_response(leak))
    assert list(tmp_path.iterdir()) == []


def test_assert_clean_catches_a_surviving_account_id_and_an_email() -> None:
    with pytest.raises(RedactionError):
        assert_clean(f"x {ACCOUNT} y", ACCOUNT)
    with pytest.raises(RedactionError):
        assert_clean("a@b.co", ACCOUNT)
    assert_clean("request id 12345678-1234-1234-1234-999988887777 ok", ACCOUNT)


def test_the_account_id_inside_a_response_is_replaced(tmp_path: Path) -> None:
    result, _ = run("novalite", tmp_path, response=text_response(f"arn:aws:iam::{ACCOUNT}:role/x"))
    assert ACCOUNT not in result.path.read_text(encoding="utf-8")


# --- failures are recorded as found ----------------------------------------------------------------------


def test_a_text_answer_is_recorded_not_retried(tmp_path: Path) -> None:
    result, runtime = run("novapro-direct", tmp_path, response=text_response("It is 19.31 km."))
    assert len(runtime.sent) == 1
    check = result.record["tool_input_check"]
    assert check["valid"] is False
    assert check["problems"] == ["no tool call"]
    assert result.record["tool_call_count"] == 0


def test_an_api_error_is_recorded(tmp_path: Path) -> None:
    from botocore.exceptions import ClientError

    error = ClientError(
        {"Error": {"Code": "ThrottlingException", "Message": "slow down"}}, "Converse"
    )
    result, _ = run("novalite", tmp_path, response=error)
    assert result.record["status"] == "api_error"
    assert result.record["error"] == {"code": "ThrottlingException", "message": "slow down"}


# --- the tool-input check --------------------------------------------------------------------------------


def checked(calls: list[dict[str, Any]]) -> dict[str, Any]:
    from horizon_compact.providers.base import Provenance, RawDecision

    prov = Provenance(
        "p",
        "converse",
        "m",
        "i",
        "in_region",
        None,
        "us-east-1",
        "x",
        "x",
        "x",
        1,
        "h",
        "s",
        "f",
        1,
    )
    return check_tool_input(RawDecision(status="ok", provenance=prov, tool_calls=calls))


def call(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {"kilometers": 19.31, "unit_system": "metric", "note": "ok"}
    data.update(overrides)
    return {"name": "record_conversion", "input": data}


@pytest.mark.parametrize(
    ("calls", "expected_problem"),
    [
        ([], "no tool call"),
        ([call(), call()], "2 tool calls"),
        ([call(kilometers="19.31")], "kilometers is not a number"),
        ([call(kilometers=True)], "kilometers is not a number"),
        ([call(kilometers=-1)], "negative"),
        ([call(unit_system="martian")], "unit_system"),
        ([call(note="  ")], "note"),
        ([{"name": "other_tool", "input": call()["input"]}], "tool name"),
        ([{"name": "record_conversion", "input": {**call()["input"], "extra": 1}}], "keys"),
        ([{"name": "record_conversion", "input": {"kilometers": 1}}], "keys"),
    ],
)
def test_tool_input_problems_are_listed(calls: list[dict[str, Any]], expected_problem: str) -> None:
    result = checked(calls)
    assert result["valid"] is False
    assert any(expected_problem in p for p in result["problems"]), result["problems"]


def test_a_wrong_but_well_formed_answer_is_valid_and_marked_incorrect() -> None:
    result = checked([call(kilometers=20.0)])
    assert result["valid"] is True
    assert result["answer_correct"] is False


# --- the command line ------------------------------------------------------------------------------------


def test_list_needs_no_network_and_shows_the_plan(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["smoke", "--evidence-dir", str(tmp_path), "list"]) == 0
    out = capsys.readouterr().out
    assert "sonnet46-profile-off" in out
    assert "records so far: 0 of 12" in out


def test_run_requires_a_profile_and_has_no_default() -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["smoke", "run", "novalite"])
    assert exc.value.code == 2


def test_run_refuses_an_unknown_call_before_touching_aws(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = cli.main(["smoke", "--evidence-dir", str(tmp_path), "run", "nope", "--profile", "p"])
    assert code == 2
    assert "refused: unknown call" in capsys.readouterr().err


def test_boto3_is_not_asked_for_a_session_when_a_call_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def explode(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("a session was created for a refused call")

    monkeypatch.setattr(boto3, "Session", explode)
    assert (
        cli.main(["smoke", "--evidence-dir", str(tmp_path), "run", "nope", "--profile", "p"]) == 2
    )
