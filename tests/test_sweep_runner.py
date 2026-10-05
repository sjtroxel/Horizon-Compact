"""A whole session against a fake provider and a local store (Phase 1 IMPLEMENTATION doc sections 6, 7 and
13)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from horizon_compact.experiment import load_experiment
from horizon_compact.providers.base import DecisionRequest, RawDecision, Usage
from horizon_compact.sweep.plan import SweepRefusal
from horizon_compact.sweep.runner import check_official, check_route
from horizon_compact.sweep.status import summarize
from horizon_compact.sweep.store import LocalStore
from sweep_helpers import (
    ACCOUNT,
    FARGATE,
    LAPTOP,
    SONNET_ROUTE,
    FakeClock,
    ScriptedProvider,
    make_plan,
    raw_error,
    raw_ok,
    session,
    valid_input,
)


def objects(store: LocalStore, sweep_id: str, pattern: str) -> list[dict[str, Any]]:
    keys = [k for k in store.list_keys(f"development/{sweep_id}/") if pattern in k]
    return [json.loads(store.get(k) or "{}") for k in keys]


def always(status_input: Any = None, **kwargs: Any) -> ScriptedProvider:
    return ScriptedProvider(lambda n, request: raw_ok(request, tool_input=status_input, **kwargs))


def test_a_full_session_writes_a_manifest_attempts_finals_and_a_summary(tmp_path: Path) -> None:
    exp, plan = make_plan()
    store = LocalStore(tmp_path)
    provider = always()
    result = session(exp, plan, provider, store)
    assert result.stopped == "complete" and result.clean
    assert (result.runs_total, result.runs_finished_now, result.attempts_now) == (5, 5, 5)
    assert len(provider.requests) == 5
    keys = store.list_keys(f"development/{plan.sweep_id}/")
    assert sum(k.endswith("manifest.json") for k in keys) == 1
    assert sum("/attempt-1.json" in k for k in keys) == 5
    assert sum(k.endswith("final.json") for k in keys) == 5
    assert sum("/sessions/" in k for k in keys) == 1
    assert len(keys) == len(set(keys)) == 12


def test_an_attempt_object_holds_the_provenance_the_doc_lists(tmp_path: Path) -> None:
    exp, plan = make_plan()
    store = LocalStore(tmp_path)
    session(exp, plan, always(), store)
    attempt = objects(store, plan.sweep_id, "/attempt-1.json")[0]
    for field in [
        "sweep_id",
        "run_id",
        "attempt",
        "git_sha",
        "image_digest",
        "runner",
        "task_arn",
        "provider",
        "model_id",
        "inference_profile",
        "invoke_id",
        "region",
        "effort",
        "thinking",
        "temperature",
        "content_hash",
        "file_hashes",
        "scenario_id",
        "objective_id",
        "wording_variant_id",
        "dossier_hash",
        "menu_order_seed",
        "menu_order",
        "option_order",
        "started_at",
        "finished_at",
        "latency_ms",
        "usage",
        "cost_usd",
        "request",
        "raw_response",
        "tool_calls",
        "text_blocks",
        "reasoning_block_count",
        "parsed_decision",
        "validation",
        "status",
        "error",
        "label",
    ]:
        assert field in attempt, field
    assert attempt["label"] == "development"
    assert (
        attempt["runner"] == "laptop" and attempt["image_digest"] is None
    )  # a laptop run has no digest
    assert attempt["temperature"] == "not set"
    assert attempt["content_hash"] == exp.content_hash
    assert attempt["file_hashes"] == exp.file_hashes
    assert attempt["validation"]["status"] == "valid"
    assert sorted(attempt["menu_order"]) == sorted(lever.key for lever in exp.scenario.levers)
    assert attempt["request"]["system"][1] == {"cachePoint": {"type": "default"}}
    assert "temperature" not in attempt["request"]["inferenceConfig"]


def test_a_container_run_records_the_digest_and_a_laptop_run_does_not(tmp_path: Path) -> None:
    exp, plan = make_plan()
    laptop_store, task_store = LocalStore(tmp_path / "a"), LocalStore(tmp_path / "b")
    session(exp, plan, always(), laptop_store, identity=LAPTOP)
    session(exp, plan, always(), task_store, identity=FARGATE)
    assert {a["image_digest"] for a in objects(laptop_store, plan.sweep_id, "/attempt-")} == {None}
    assert {a["image_digest"] for a in objects(task_store, plan.sweep_id, "/attempt-")} == {
        FARGATE.image_digest
    }
    assert {a["runner"] for a in objects(task_store, plan.sweep_id, "/attempt-")} == {"fargate"}


def test_the_account_id_never_reaches_a_stored_object(tmp_path: Path) -> None:
    exp, plan = make_plan("sonnet-4-6")
    store = LocalStore(tmp_path)
    session(exp, plan, always(), store, route=SONNET_ROUTE, identity=FARGATE)
    text = "".join(store.get(k) or "" for k in store.list_keys(""))
    assert ACCOUNT not in text
    assert "<account-id>" in text  # the profile ARN and the task ARN carried it


def test_resume_skips_finished_runs_and_re_runs_nothing(tmp_path: Path) -> None:
    exp, plan = make_plan()
    store = LocalStore(tmp_path)
    first = always()
    interrupted = session(exp, plan, first, store, should_stop=lambda: len(first.requests) >= 3)
    assert interrupted.stopped == "stop_requested"
    assert (interrupted.runs_finished_now, len(first.requests)) == (3, 3)
    second = always()
    resumed = session(exp, plan, second, store)
    assert resumed.stopped == "complete"
    assert (resumed.runs_finished_before, resumed.runs_finished_now) == (3, 2)
    assert len(second.requests) == 2  # only the two unfinished runs
    finals = objects(store, plan.sweep_id, "final.json")
    assert sorted(f["run_id"] for f in finals) == sorted(r.run_id for r in plan.runs)
    assert len(objects(store, plan.sweep_id, "/sessions/")) == 2


def test_an_interrupted_run_is_finished_on_relaunch_at_the_next_attempt_number(
    tmp_path: Path,
) -> None:
    exp, plan = make_plan()
    store = LocalStore(tmp_path)
    first = ScriptedProvider(lambda n, request: raw_ok(request, stop="max_tokens"))
    session(exp, plan, first, store, should_stop=lambda: len(first.requests) >= 1)
    run = plan.runs[0].run_id
    base = f"development/{plan.sweep_id}/runs/{run}"
    assert store.get(f"{base}/attempt-1.json") and store.get(f"{base}/final.json") is None
    session(exp, plan, always(), store)
    assert json.loads(store.get(f"{base}/attempt-2.json") or "{}")["status"] == "valid"
    final = json.loads(store.get(f"{base}/final.json") or "{}")
    assert (final["status"], final["first_attempt_status"], final["attempts"]) == (
        "valid",
        "truncated",
        2,
    )


def test_a_missing_final_is_written_from_the_stored_attempts_with_no_new_call(
    tmp_path: Path,
) -> None:
    """A crash between the last attempt's write and the run's final.json must not cost a model call."""
    exp, plan = make_plan()
    store = LocalStore(tmp_path)
    session(exp, plan, always(), store)
    victim = plan.runs[0].run_id
    (tmp_path / f"development/{plan.sweep_id}/runs/{victim}/final.json").unlink()
    provider = always()
    result = session(exp, plan, provider, store)
    assert provider.requests == []
    assert result.stopped == "complete"
    assert store.get(f"development/{plan.sweep_id}/runs/{victim}/final.json")


def test_a_changed_manifest_is_refused(tmp_path: Path) -> None:
    exp, plan = make_plan()
    store = LocalStore(tmp_path)
    session(exp, plan, always(), store)
    path = tmp_path / f"development/{plan.sweep_id}/manifest.json"
    manifest = json.loads(path.read_text())
    manifest["content_hash"] = "0" * 64
    path.write_text(json.dumps(manifest))
    provider = always()
    with pytest.raises(SweepRefusal, match="differs from the plan"):
        session(exp, plan, provider, store)
    assert provider.requests == []


def test_a_refusal_is_recorded_and_never_retried(tmp_path: Path) -> None:
    exp, plan = make_plan()
    store = LocalStore(tmp_path)
    provider = ScriptedProvider(
        lambda n, request: raw_ok(request, stop="content_filtered", calls=[])
    )
    result = session(exp, plan, provider, store)
    assert len(provider.requests) == 5  # one attempt per run
    assert {f["status"] for f in objects(store, plan.sweep_id, "final.json")} == {"refusal"}
    assert result.stopped == "complete"


def test_retries_are_fresh_identical_requests_and_the_first_attempt_status_is_kept(
    tmp_path: Path,
) -> None:
    exp, plan = make_plan(repeats=1)
    store = LocalStore(tmp_path)

    def script(n: int, request: DecisionRequest) -> RawDecision:
        return raw_ok(request, stop="max_tokens") if n <= 2 else raw_ok(request)

    provider = ScriptedProvider(script)
    session(exp, plan, provider, store, should_stop=lambda: len(provider.requests) >= 3)
    first_three = provider.requests[:3]
    assert (
        first_three[0] == first_three[1] == first_three[2]
    )  # same prompt, same order, no repair message
    run = plan.runs[0].run_id
    final = json.loads(store.get(f"development/{plan.sweep_id}/runs/{run}/final.json") or "{}")
    assert (final["status"], final["first_attempt_status"], final["attempts"]) == (
        "valid",
        "truncated",
        3,
    )


def test_a_run_gets_at_most_three_model_attempts(tmp_path: Path) -> None:
    exp, plan = make_plan()
    store = LocalStore(tmp_path)
    provider = ScriptedProvider(
        lambda n, request: raw_ok(request, tool_input=valid_input(open_day_season="winter"))
    )
    session(exp, plan, provider, store)
    assert len(provider.requests) == 15  # 5 runs x 3
    assert {f["status"] for f in objects(store, plan.sweep_id, "final.json")} == {"schema_invalid"}


def test_api_errors_back_off_are_stored_and_do_not_count_against_the_retry_budget(
    tmp_path: Path,
) -> None:
    exp, plan = make_plan()
    store = LocalStore(tmp_path)
    clock = FakeClock()

    def script(n: int, request: DecisionRequest) -> RawDecision:
        return raw_error(request, "ThrottlingException") if n <= 4 else raw_ok(request)

    provider = ScriptedProvider(script)
    session(exp, plan, provider, store, clock=clock)
    run = plan.runs[0].run_id
    final = json.loads(store.get(f"development/{plan.sweep_id}/runs/{run}/final.json") or "{}")
    assert (final["status"], final["attempts"], final["model_attempts"]) == ("valid", 5, 1)
    backoffs = [s for s in clock.sleeps if s > 0]
    assert len(backoffs) >= 4  # one backoff per api_error, growing cap 4, 8, 16, 32
    attempts = objects(store, plan.sweep_id, f"{run}/attempt-")
    assert [a["status"] for a in attempts][:4] == ["api_error"] * 4
    assert all(a["cost_usd"] == 0 for a in attempts[:4])


def test_a_request_error_stops_the_session_and_leaves_the_run_unfinished(tmp_path: Path) -> None:
    exp, plan = make_plan()
    store = LocalStore(tmp_path)
    provider = ScriptedProvider(lambda n, request: raw_error(request, "AccessDeniedException"))
    result = session(exp, plan, provider, store)
    assert (result.stopped, result.clean, len(provider.requests)) == ("config_error", False, 1)
    assert objects(store, plan.sweep_id, "final.json") == []
    summary = objects(store, plan.sweep_id, "/sessions/")[0]
    assert summary["stopped"] == "config_error"


def test_the_cap_stops_the_session_before_the_attempt_that_would_pass_it(tmp_path: Path) -> None:
    exp, plan = make_plan()  # Nova Lite: worst case per attempt is a fraction of a cent
    store = LocalStore(tmp_path)
    expensive = Usage(input_tokens=1_000_000, output_tokens=0)  # $0.06 on Nova Lite
    provider = ScriptedProvider(lambda n, request: raw_ok(request, usage=expensive))
    result = session(exp, plan, provider, store, cap_usd=0.10)
    assert result.stopped == "cap_reached"
    assert (
        len(provider.requests) == 2
    )  # $0.06, then $0.12 would pass the cap, so the third never starts
    assert result.cost_usd_total == pytest.approx(0.12)


def test_the_cap_is_per_sweep_across_sessions(tmp_path: Path) -> None:
    exp, plan = make_plan()
    store = LocalStore(tmp_path)
    expensive = Usage(input_tokens=1_000_000, output_tokens=0)
    session(
        exp, plan, ScriptedProvider(lambda n, r: raw_ok(r, usage=expensive)), store, cap_usd=0.10
    )
    again = ScriptedProvider(lambda n, r: raw_ok(r, usage=expensive))
    result = session(exp, plan, again, store, cap_usd=0.10)
    assert result.stopped == "cap_reached"
    assert again.requests == []  # the first session already spent what the cap allows


def test_a_sweep_that_could_pass_its_cap_is_refused_before_any_call(tmp_path: Path) -> None:
    exp, plan = make_plan("sonnet-4-6", repeats=3)
    provider = always()
    with pytest.raises(SweepRefusal, match="above the cap"):
        session(exp, plan, provider, LocalStore(tmp_path), cap_usd=0.50, route=SONNET_ROUTE)
    assert provider.requests == []


def test_the_wall_clock_ends_the_session_cleanly_between_attempts(tmp_path: Path) -> None:
    exp, plan = make_plan(repeats=3)
    store = LocalStore(tmp_path)
    result = session(
        exp, plan, always(), store, max_minutes=0.1
    )  # six seconds; Nova Lite paces at 3.75s
    assert result.stopped == "max_minutes" and result.clean
    assert 0 < result.attempts_now < 15


def test_a_lost_write_race_stops_the_session_rather_than_guessing(tmp_path: Path) -> None:
    class Racing(LocalStore):
        def put_new(self, key: str, text: str) -> bool:
            return False if "/attempt-" in key else super().put_new(key, text)

    exp, plan = make_plan()
    result = session(exp, plan, always(), Racing(tmp_path))
    assert result.stopped == "write_conflict" and not result.clean


def test_every_object_is_written_once(tmp_path: Path) -> None:
    """The local store refuses to overwrite, so a second identical session adds only a summary."""
    exp, plan = make_plan()
    store = LocalStore(tmp_path)
    session(exp, plan, always(), store)
    before = {k: store.get(k) for k in store.list_keys("")}
    session(exp, plan, always(), store)
    after = {k: store.get(k) for k in store.list_keys("")}
    assert {k: v for k, v in after.items() if k in before} == before
    assert len(after) == len(before) + 1  # the second session's summary


def test_status_summarizes_a_sweep(tmp_path: Path) -> None:
    exp, plan = make_plan()
    store = LocalStore(tmp_path)
    assert summarize(store, plan.sweep_id) is None
    session(exp, plan, always(), store)
    summary = summarize(store, plan.sweep_id)
    assert summary is not None
    assert (summary["runs_total"], summary["runs_finished"], summary["attempts"]) == (5, 5, 5)
    assert summary["final_statuses"] == {"valid": 5}
    assert summary["sessions"][0]["stopped"] == "complete"


# --- the official gate and the route check ---------------------------------------------------------------


def test_an_official_sweep_is_refused_because_no_protocol_exists() -> None:
    with pytest.raises(SweepRefusal, match=r"no committed protocol \(prereg-v1 does not exist\)"):
        check_official(load_experiment("placeholder"), FARGATE)


def test_an_official_sweep_is_refused_on_a_laptop_even_if_a_protocol_existed(
    tmp_path: Path,
) -> None:
    from sweep_helpers import copy_experiment

    root = copy_experiment(tmp_path)
    exp = load_experiment("placeholder", root)
    (root / "protocol").mkdir()
    (root / "protocol" / "prereg.lock").write_text(f'content_hash = "{exp.content_hash}"\n')
    check_official(exp, FARGATE)  # a matching lock and a container: allowed
    with pytest.raises(SweepRefusal, match="only in the container"):
        check_official(exp, LAPTOP)


def test_a_stale_protocol_lock_does_not_open_the_gate(tmp_path: Path) -> None:
    from sweep_helpers import copy_experiment

    root = copy_experiment(tmp_path)
    (root / "protocol").mkdir()
    (root / "protocol" / "prereg.lock").write_text('content_hash = "stale"\n')
    with pytest.raises(SweepRefusal, match="no committed protocol"):
        check_official(load_experiment("placeholder", root), FARGATE)


def test_a_route_mismatch_is_refused_naming_both() -> None:
    exp = load_experiment("placeholder")
    with pytest.raises(SweepRefusal, match=r"'geo_profile'.*'application_profile'"):
        check_route(exp, "sonnet-4-6", {"HC_SONNET_ROUTE": "geo_profile"})
    check_route(exp, "sonnet-4-6", {"HC_SONNET_ROUTE": "application_profile"})
    check_route(exp, "sonnet-4-6", {})  # unset on a laptop: nothing to compare
    check_route(
        exp, "nova-lite", {"HC_SONNET_ROUTE": "geo_profile"}
    )  # only the main model has the variable


def test_every_object_a_session_writes_is_labeled_development_and_stored_under_development(
    tmp_path: Path,
) -> None:
    exp, plan = make_plan()
    store = LocalStore(tmp_path)
    session(exp, plan, always(), store)
    assert all(k.startswith("development/") for k in store.list_keys(""))
    for pattern in ("/attempt-", "final.json", "/sessions/"):
        labels = {o["label"] for o in objects(store, plan.sweep_id, pattern)}
        assert labels == {"development"}, pattern


DAILY = "Too many tokens per day, please wait before trying again."


def test_a_daily_quota_stops_at_once_with_a_clear_reason_and_no_waiting(tmp_path: Path) -> None:
    exp, plan = make_plan()
    store = LocalStore(tmp_path)
    clock = FakeClock()
    provider = ScriptedProvider(lambda n, request: raw_error(request, "ThrottlingException", DAILY))
    result = session(exp, plan, provider, store, clock=clock)
    assert (result.stopped, result.clean, len(provider.requests)) == ("quota_exhausted", False, 1)
    assert clock.sleeps == []  # no backoff: it would not have helped
    assert objects(store, plan.sweep_id, "final.json") == []
    assert objects(store, plan.sweep_id, "/sessions/")[0]["stopped"] == "quota_exhausted"


def test_ten_throttles_in_a_row_stop_the_session_instead_of_waiting_out_the_clock(
    tmp_path: Path,
) -> None:
    exp, plan = make_plan()
    provider = ScriptedProvider(
        lambda n, request: raw_error(request, "ThrottlingException", "Too many requests.")
    )
    result = session(exp, plan, provider, LocalStore(tmp_path))
    assert (result.stopped, result.clean, len(provider.requests)) == ("api_errors", False, 10)


def test_the_run_of_errors_resets_on_any_model_outcome(tmp_path: Path) -> None:
    exp, plan = make_plan()

    def script(n: int, request: DecisionRequest) -> RawDecision:
        # nine throttles, one good answer, nine more: never ten in a row
        return raw_error(request, "ThrottlingException", "x") if n % 10 != 0 else raw_ok(request)

    provider = ScriptedProvider(script)
    result = session(
        exp, plan, provider, LocalStore(tmp_path), should_stop=lambda: len(provider.requests) >= 30
    )
    assert result.stopped == "stop_requested"
    assert result.runs_finished_now == 3


def test_every_attempt_reports_its_progress(tmp_path: Path) -> None:
    exp, plan = make_plan()
    lines: list[str] = []
    session(exp, plan, always(), LocalStore(tmp_path), progress=lines.append)
    assert len(lines) == 5
    assert lines[0].startswith("run 1/5 ") and "attempt 1: valid" in lines[0]
    assert lines[-1].startswith("run 5/5 ")


def test_a_stop_request_during_a_backoff_is_honoured_within_a_second(tmp_path: Path) -> None:
    exp, plan = make_plan()
    clock = FakeClock()
    provider = ScriptedProvider(
        lambda n, request: raw_error(request, "ThrottlingException", "Too many requests.")
    )
    result = session(
        exp,
        plan,
        provider,
        LocalStore(tmp_path),
        clock=clock,
        should_stop=lambda: len(clock.sleeps) >= 3,
    )
    assert result.stopped == "stop_requested"
    assert len(provider.requests) < 10
    assert all(s <= 3.75 + 1e-9 for s in clock.sleeps)  # slices, never one long sleep
