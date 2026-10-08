"""The blind format report and the failures view (Phase 2.5 IMPLEMENTATION doc section 11.3): planted
records carry amounts, a choice, a memo and model text, and none of them may reach either output. Every value
here is a canary; no model is called."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from horizon_compact import cli
from horizon_compact.experiment import load_experiment
from horizon_compact.sweep.blind import failures_view, format_report, mask
from horizon_compact.sweep.plan import RunSpec, SweepPlan, build_plan
from horizon_compact.sweep.runner import sweep_prefix
from horizon_compact.sweep.store import LocalStore

CANARY_AMOUNT = 7654321
CANARY_WORDS = 9876543  # seven digits: unlike 212, too long to turn up by chance in a hex run id
CANARY_MEMO = "CANARYMEMO the memo must never be printed"
PLAN_ARGS = [
    "--experiment", "company",
    "--model", "gpt-oss-openrouter",
    "--repeats", "1",
    "--seed", "5",
    "--label", "blindtest",
    "--template", "w1",
    "--template", "w3",
]  # fmt: skip


def company_plan() -> SweepPlan:
    return build_plan(
        load_experiment("company"),
        model_key="gpt-oss-openrouter",
        label="blindtest",
        repeats=1,
        seed=5,
        templates=["w1", "w3"],
    )


def plant(store: LocalStore, plan: SweepPlan, run: RunSpec, status: str, **attempt: Any) -> None:
    prefix = sweep_prefix(plan.experiment, plan.sweep_id)
    decision = {
        "amounts": {"anything": CANARY_AMOUNT},
        "memo": CANARY_MEMO,
        "plant_decision": "retool",
    }
    record = {
        "status": status,
        "stop_reason": attempt.get("stop_reason", "tool_use"),
        "parsed_decision": decision,
        "tool_calls": [{"name": "submit_decision", "input": decision}],
        "validation": {
            "status": status,
            "problems": attempt.get("problems", []),
            "amounts": {"anything": CANARY_AMOUNT},
            "scaled_amounts": None,
            "choice": "retool",
            "memo_words": CANARY_WORDS,
        },
        "text_blocks": attempt.get("text_blocks", []),
        "detail": None,
    }
    store.put_new(f"{prefix}runs/{run.run_id}/attempt-1.json", json.dumps(record))
    final = {
        "run_id": run.run_id,
        "objective_id": run.objective_id,
        "status": status,
        "first_attempt_status": status,
        "final_attempt": 1,
        "attempts": 1,
        "model_attempts": 1,
        "cost_usd": 0.0003,
    }
    store.put_new(f"{prefix}runs/{run.run_id}/final.json", json.dumps(final))


@pytest.fixture
def planted(tmp_path: Path) -> tuple[LocalStore, SweepPlan]:
    plan = company_plan()
    store = LocalStore(tmp_path)
    s3_runs = [r for r in plan.runs if r.scenario_id == "s3"]
    failing = s3_runs[0]
    plant(
        store,
        plan,
        failing,
        "sum_mismatch",
        problems=[
            f"amounts add up to {CANARY_AMOUNT}, not 190",
            "amounts.kept_at_plant may be non-zero only when the choice is one of ['retool']",
        ],
        text_blocks=[f"I chose to retool, keeping {CANARY_AMOUNT} people. {CANARY_MEMO}"],
    )
    for run in plan.runs:
        if run is not failing:
            plant(store, plan, run, "valid" if run.scenario_id != "s4" else "valid_rescaled")
    return store, plan


def test_the_mask_hides_every_digit_and_every_option_key() -> None:
    assert mask("choice 'retool' gave 1234 and closed", ["close", "retool", "sell"]) == (
        "choice '<option>' gave #### and closed"
    )


def test_neither_output_holds_an_amount_a_choice_or_a_memo(
    planted: tuple[LocalStore, SweepPlan],
) -> None:
    store, plan = planted
    company = load_experiment("company")
    for text in (format_report(store, company, plan), failures_view(store, company, plan)):
        assert str(CANARY_AMOUNT) not in text
        assert f"{CANARY_AMOUNT:,}" not in text
        assert "CANARYMEMO" not in text and "the memo must never be printed" not in text
        assert "retool" not in text
        assert str(CANARY_WORDS) not in text  # the memo's word count
        assert "anything" not in text  # a key that exists only inside the planted amounts


def test_the_failures_view_shows_the_masked_problems_and_text(
    planted: tuple[LocalStore, SweepPlan],
) -> None:
    store, plan = planted
    view = failures_view(store, load_experiment("company"), plan)
    assert "**1 of 40 finished runs are not valid.**" in view
    assert "amounts add up to #######, not ###" in view
    assert "only when the choice is one of ['<option>']" in view
    assert "status: `sum_mismatch`" in view
    assert (
        "text outside the tool call: 14 words; reads as a decline: no; names the tool: no" in view
    )


def test_the_format_report_counts_by_cell_and_objective_only(
    planted: tuple[LocalStore, SweepPlan],
) -> None:
    store, plan = planted
    report = format_report(store, load_experiment("company"), plan)
    assert "| s1 | w1 | 5 | 5 | 5 | 0 | 5 | none |" in report
    assert "| s4 | w3 | 5 | 5 | 5 | 5 | 5 | none |" in report
    assert "sum_mismatch 1" in report
    assert "**Runs finished: 40 of 40.**" in report
    assert "Cells with no valid run:" in report  # the one failing run is its cell's only run


def test_hc_sweep_report_writes_both_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fake_git(*args: str) -> str:
        return str(tmp_path) if "--show-toplevel" in args else "abc1234"

    monkeypatch.setattr(cli, "_git", fake_git)
    plan = company_plan()
    plant(LocalStore(tmp_path / "scratch" / "runs"), plan, plan.runs[0], "valid")
    assert cli.main(["sweep", "report", *PLAN_ARGS]) == 0
    out = capsys.readouterr().out
    folder = tmp_path / cli.FORMAT_REPORT_DIR
    assert f"wrote {cli.FORMAT_REPORT_DIR}/{plan.sweep_id}.md" in out
    assert (folder / f"{plan.sweep_id}.md").is_file()
    assert (folder / f"{plan.sweep_id}-failures.md").is_file()
    assert "**Runs finished: 1 of 40.**" in (folder / f"{plan.sweep_id}.md").read_text()


def test_the_view_also_counts_failed_attempts_that_a_retry_hid(tmp_path: Path) -> None:
    plan = company_plan()
    store = LocalStore(tmp_path)
    run = next(r for r in plan.runs if r.scenario_id == "s2")
    plant(store, plan, run, "valid")
    prefix = sweep_prefix(plan.experiment, plan.sweep_id)
    hidden = {
        "status": "schema_invalid",
        "validation": {
            "problems": [f"amounts.cut_wages_hours is {CANARY_AMOUNT}, above its limit"]
        },
        "parsed_decision": {"memo": CANARY_MEMO},
        "text_blocks": [],
    }
    (tmp_path / f"{prefix}runs/{run.run_id}/attempt-1.json").write_text(json.dumps(hidden))
    store.put_new(f"{prefix}runs/{run.run_id}/attempt-2.json", json.dumps({"status": "valid"}))
    final = json.loads(store.get(f"{prefix}runs/{run.run_id}/final.json") or "{}")
    (tmp_path / f"{prefix}runs/{run.run_id}/final.json").write_text(
        json.dumps({**final, "final_attempt": 2, "model_attempts": 2})
    )
    view = failures_view(store, load_experiment("company"), plan)
    assert "amounts.cut_wages_hours is #######, above its limit" in view
    assert "**1 failed attempts in runs that ended valid.**" in view
    assert str(CANARY_AMOUNT) not in view and "CANARYMEMO" not in view


def test_the_failures_view_names_no_objective_and_no_run_id(
    planted: tuple[LocalStore, SweepPlan],
) -> None:
    """A problem says which lines a run used, so the view must not say whose objective it ran under."""
    store, plan = planted
    view = failures_view(store, load_experiment("company"), plan)
    assert "## s3 w" in view
    assert re.search(r"objective [A-E]\b", view) is None
    assert re.search(r"r-[0-9a-f]{12}", view) is None
