"""The run reader: runner-written records into rows, and decision 8's refusal (Phase 3 doc 6, 17.8)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from analysis_helpers import PILOT_PREFIX, decision, relocate, run_company
from horizon_compact.analysis import records
from horizon_compact.analysis.records import RecordRefusal, read_runs
from horizon_compact.sweep import classify
from horizon_compact.sweep.runner import sweep_prefix
from horizon_compact.sweep.store import LocalStore
from sweep_helpers import (
    VALID_AMOUNTS,
    ScriptedProvider,
    make_plan,
    raw_error,
    raw_ok,
    session,
    valid_input,
)

BALANCED = valid_input()
OFF_BY_SIX_PERCENT = valid_input(
    amounts={
        **VALID_AMOUNTS,
        "yearly_fund": 900,
    }  # sources 1,400 against 1,500: over the 1% tolerance
)
WITHIN_TOLERANCE = valid_input(amounts={**VALID_AMOUNTS, "raffle": 210})  # sources 1,510


def _placeholder_sweep(tmp_path: Path) -> tuple[LocalStore, str]:
    """Five runs, nine calls: valid; rescaled; mismatch then valid; three mismatches; api_error then valid."""
    script: dict[int, Any] = {
        1: BALANCED,
        2: WITHIN_TOLERANCE,
        3: OFF_BY_SIX_PERCENT,
        4: BALANCED,
        5: OFF_BY_SIX_PERCENT,
        6: OFF_BY_SIX_PERCENT,
        7: OFF_BY_SIX_PERCENT,
        8: "api_error",
        9: BALANCED,
    }

    def respond(n: int, request: Any) -> Any:
        item = script[n]
        return (
            raw_error(request, "ThrottlingException")
            if item == "api_error"
            else raw_ok(request, tool_input=item)
        )

    exp, plan = make_plan()
    store = LocalStore(tmp_path)
    session(exp, plan, ScriptedProvider(respond), store)
    return store, sweep_prefix(plan.experiment, plan.sweep_id)


def test_the_status_sets_agree_with_the_runner() -> None:
    assert records.NON_MODEL_STATUSES == classify.NON_MODEL_STATUSES
    assert {"valid", "valid_rescaled"} == records.VALID_STATUSES


def test_rows_carry_what_the_runner_wrote(tmp_path: Path) -> None:
    store, prefix = _placeholder_sweep(tmp_path)
    found = read_runs(store, prefix)
    assert len(found.rows) == 5 and found.unfinished == ()
    by_status = sorted(row.status for row in found.rows)
    assert by_status == ["sum_mismatch", "valid", "valid", "valid", "valid_rescaled"]

    rescaled = next(r for r in found.rows if r.status == "valid_rescaled")
    assert rescaled.amounts is not None and rescaled.first_amounts is not None
    # The counted decision is the scaled one: the raw 210 became about 208.61, and sources sum to 1,500.
    assert rescaled.amounts["raffle"] == pytest.approx(208.61, abs=0.01)
    assert rescaled.first_amounts == rescaled.amounts
    assert sum(
        rescaled.amounts[k] for k in ("yearly_fund", "plant_sale", "raffle")
    ) == pytest.approx(1500, abs=0.05)
    assert rescaled.choice == "spring"

    retried = next(r for r in found.rows if r.first_attempt_status == "sum_mismatch" and r.valid)
    assert retried.attempts == 2
    assert retried.first_amounts is None and retried.first_choice is None
    assert retried.amounts is not None and retried.choice == "spring"

    failed = next(r for r in found.rows if r.status == "sum_mismatch")
    assert failed.attempts == 3 and failed.first_attempt_status == "sum_mismatch"
    assert failed.amounts is None and failed.choice is None and failed.first_amounts is None

    # The api_error attempt is not a model attempt: that run has one, and it was valid first time.
    after_error = [
        r for r in found.rows if r.status == "valid" and r.first_attempt_status == "valid"
    ]
    assert len(after_error) == 2 and all(r.attempts == 1 for r in after_error)


def test_rows_take_scenario_objective_wording_and_repeat_from_the_manifest(tmp_path: Path) -> None:
    store, prefix = _placeholder_sweep(tmp_path)
    manifest = json.loads(store.get(f"{prefix}manifest.json") or "{}")
    planned = {run["run_id"]: run for run in manifest["runs"]}
    for row in read_runs(store, prefix).rows:
        spec = planned[row.run_id]
        assert (row.scenario_id, row.objective_id, row.wording_id, row.repeat) == (
            spec["scenario_id"],
            spec["objective_id"],
            spec["wording_id"],
            spec["repeat"],
        )
        assert row.sweep_id == manifest["sweep_id"] and row.model_key == manifest["model_key"]
        assert set(VALID_AMOUNTS) <= set(row.menu_order)
        assert set(row.option_order) == {"spring", "autumn"}


def test_a_run_without_a_final_is_listed_not_analysed(tmp_path: Path) -> None:
    exp, plan = make_plan()
    store = LocalStore(tmp_path)
    session(exp, plan, ScriptedProvider(), store, cap_usd=5.0, should_stop=_stop_after(2))
    found = read_runs(store, sweep_prefix(plan.experiment, plan.sweep_id))
    assert len(found.rows) + len(found.unfinished) == 5 and found.unfinished


def _stop_after(calls: int) -> Any:
    state = {"n": 0}

    def should_stop() -> bool:
        state["n"] += 1
        return state["n"] > calls

    return should_stop


def test_a_final_that_disagrees_with_its_attempts_is_refused(tmp_path: Path) -> None:
    store, prefix = _placeholder_sweep(tmp_path)
    final_key = next(k for k in store.list_keys(prefix) if k.endswith("final.json"))
    path = tmp_path / final_key
    data = json.loads(path.read_text())
    data["status"] = "refusal" if data["status"] != "refusal" else "valid"
    path.write_text(json.dumps(data))
    with pytest.raises(RecordRefusal, match=r"final\.json says"):
        read_runs(store, prefix)


# --- decision 8: development records on real content are refused ---------------------------------------


def test_the_placeholder_development_records_are_read(tmp_path: Path) -> None:
    store, prefix = _placeholder_sweep(tmp_path)
    assert prefix.startswith("development/placeholder/")
    assert len(read_runs(store, prefix).rows) == 5


def test_development_records_on_real_content_are_refused_with_the_reason(tmp_path: Path) -> None:
    _exp, plan, store = run_company(
        tmp_path,
        "s1",
        [decision({"eliminate": 125, "move_plant_pay": 0, "move_keep_pay": 0})] * 5,
    )
    prefix = sweep_prefix(plan.experiment, plan.sweep_id)
    assert prefix.startswith("development/company/") and store.list_keys(prefix)
    with pytest.raises(RecordRefusal, match="no allocation by objective was seen"):
        read_runs(store, prefix)


@pytest.mark.parametrize(
    "prefix", ["development/", "development", "development/company/", "/development/company/x/"]
)
def test_a_parent_or_odd_spelling_of_the_prefix_is_refused_too(tmp_path: Path, prefix: str) -> None:
    run_company(
        tmp_path, "s1", [decision({"eliminate": 125, "move_plant_pay": 0, "move_keep_pay": 0})] * 5
    )
    with pytest.raises(RecordRefusal):
        read_runs(LocalStore(tmp_path), prefix)


def test_a_listing_that_reaches_real_content_is_refused_key_by_key(tmp_path: Path) -> None:
    """Placeholder and company sweeps side by side: a prefix wide enough to include both is refused, because
    the check runs on every key listed, not only on the prefix asked for."""
    store, _prefix = _placeholder_sweep(tmp_path)
    run_company(
        tmp_path, "s1", [decision({"eliminate": 125, "move_plant_pay": 0, "move_keep_pay": 0})] * 5
    )
    with pytest.raises(RecordRefusal):
        read_runs(store, "")


def test_the_same_records_under_a_pilot_prefix_are_read(tmp_path: Path) -> None:
    _exp, plan, store = run_company(
        tmp_path,
        "s1",
        [decision({"eliminate": 125, "move_plant_pay": 0, "move_keep_pay": 0})] * 5,
    )
    found = read_runs(store, relocate(store, plan))
    assert len(found.rows) == 5 and {r.scenario_id for r in found.rows} == {"s1"}
    assert PILOT_PREFIX  # the prefix is only a place; the rule is about development/


def test_the_reader_takes_a_version_two_and_a_version_three_manifest_alike(tmp_path: Path) -> None:
    """The reader never uses the manifest's repeats (each run carries its own repeat), so a sweep stored
    before counts could differ reads exactly as one stored after."""
    store, prefix = _placeholder_sweep(tmp_path)
    key = f"{prefix}manifest.json"
    manifest = json.loads(store.get(key) or "{}")
    assert manifest["manifest_version"] == 3 and isinstance(manifest["repeats"], dict)
    now = read_runs(store, prefix)
    manifest["manifest_version"] = 2
    manifest["repeats"] = 1
    (tmp_path / key).write_text(json.dumps(manifest))
    assert read_runs(LocalStore(tmp_path), prefix) == now
