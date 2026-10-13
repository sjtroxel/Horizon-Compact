"""``hc sweep tokens`` (Phase 4 runs half section 5.2): token counts and block counts only, never a decision.
A fake store, fictional ids, and canary values planted in every field the command must not read."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from horizon_compact import cli
from horizon_compact.experiment import Experiment, load_experiment
from horizon_compact.sweep import tokens
from horizon_compact.sweep.plan import SweepPlan, SweepRefusal, build_plan
from horizon_compact.sweep.runner import sweep_prefix
from horizon_compact.sweep.store import LocalStore
from horizon_compact.sweep.tokens import tokens_report

HAIKU = "haiku-5-5"
CANARY = "CANARY-DO-NOT-READ-7731"
UNREAD = ("validation", "tool_calls", "text_blocks", "raw_response", "parsed_decision")


def company() -> Experiment:
    return load_experiment("company")


def grid(exp: Experiment) -> SweepPlan:
    return build_plan(exp, model_key=HAIKU, label="grid", repeats=2, seed=541789037, official=True)


def study(exp: Experiment) -> SweepPlan:
    return build_plan(
        exp, model_key=HAIKU, label="thinking", repeats=2, seed=3422206995, scenarios=["s1"],
        templates=[exp.sealed_template or ""], official=True,
    )  # fmt: skip


def plant(store: LocalStore, plan: SweepPlan, out_tokens: dict[str, int], blocks: int = 0) -> None:
    """Write the manifest and, for every run of S1 on the sealed wording, a final attempt whose output tokens
    depend on the objective (so the table has something to show) and whose unread fields hold the canary."""
    prefix = sweep_prefix(plan.experiment, plan.sweep_id, "official")
    store.put_new(f"{prefix}manifest.json", json.dumps(plan.manifest()))
    for run in plan.runs:
        attempt = {
            "scenario_id": run.scenario_id,
            "wording_variant_id": run.wording_id,
            "objective_id": run.objective_id,
            "usage": {"output_tokens": out_tokens[run.objective_id]},
            "reasoning_block_count": blocks,
            **dict.fromkeys(UNREAD, CANARY),
        }
        store.put_new(f"{prefix}runs/{run.run_id}/attempt-1.json", json.dumps(attempt))
        store.put_new(
            f"{prefix}runs/{run.run_id}/final.json",
            json.dumps({"final_attempt": 1, "status": CANARY, "objective_id": run.objective_id}),
        )


def test_the_table_sets_each_objectives_thinking_cost_beside_the_grids(tmp_path: Path) -> None:
    exp = company()
    store = LocalStore(tmp_path)
    base, with_thinking = grid(exp), study(exp)
    plant(store, base, {o.id: 1000 for o in exp.objectives})
    plant(
        store, with_thinking, {o.id: 3000 + 100 * i for i, o in enumerate(exp.objectives)}, blocks=1
    )
    text = tokens_report(store, "company", base.sweep_id, with_thinking.sweep_id)
    rows = {
        line.split("|")[1].strip(): [c.strip() for c in line.split("|")[2:-1]]
        for line in text.splitlines()
        if line.startswith("| ") and "---" not in line
    }
    first, last = exp.objectives[0].id, exp.objectives[-1].id
    # S1 on the sealed wording, twice a cell, in both sweeps; the grid's other cells are not read
    assert rows[first] == ["2", "1000", "2", "3000", "2000", "2 of 2"]
    assert rows[last] == ["2", "1000", "2", "3400", "2400", "2 of 2"]
    assert rows["all"][0] == str(2 * len(exp.objectives))
    assert CANARY not in text


def test_a_sub_study_run_with_no_thinking_block_is_counted_as_one(tmp_path: Path) -> None:
    exp = company()
    store = LocalStore(tmp_path)
    base, with_thinking = grid(exp), study(exp)
    plant(store, base, {o.id: 1000 for o in exp.objectives})
    plant(store, with_thinking, {o.id: 1100 for o in exp.objectives}, blocks=0)
    text = tokens_report(store, "company", base.sweep_id, with_thinking.sweep_id)
    assert "0 of 2" in text and "2 of 2" not in text


def test_a_pair_that_is_not_a_grid_and_its_sub_study_is_refused(tmp_path: Path) -> None:
    exp = company()
    store = LocalStore(tmp_path)
    base, with_thinking = grid(exp), study(exp)
    plant(store, base, {o.id: 1 for o in exp.objectives})
    plant(store, with_thinking, {o.id: 1 for o in exp.objectives})
    with pytest.raises(SweepRefusal, match="--vs is labeled 'grid'"):
        tokens_report(store, "company", with_thinking.sweep_id, base.sweep_id)
    with pytest.raises(SweepRefusal, match="no official manifest"):
        tokens_report(store, "company", base.sweep_id, "thinking-haiku-5-5-00000000")


def test_the_command_reads_no_decision_field_by_name() -> None:
    """The one place a run's counts are picked out is ``_counts``; no unread field is looked up anywhere."""
    source = Path(tokens.__file__).read_text(encoding="utf-8")
    code = re.sub(r'""".*?"""', "", source, flags=re.S)
    for field in (*UNREAD, "status", "memo", "amounts", "choice"):
        assert f'"{field}"' not in code and f"'{field}'" not in code, field
    assert "final['final_attempt']" in code  # the only thing read from a final.json


def test_the_command_line_prints_the_table(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    exp = company()
    store = LocalStore(tmp_path)
    base, with_thinking = grid(exp), study(exp)
    plant(store, base, {o.id: 1000 for o in exp.objectives})
    plant(store, with_thinking, {o.id: 2000 for o in exp.objectives}, blocks=1)
    monkeypatch.setattr(cli, "_session", lambda args, identity: None)
    monkeypatch.setattr(cli, "_store", lambda args, session: store)
    code = cli.main(
        [
            "sweep",
            "tokens",
            "--experiment",
            "company",
            "--sweep",
            base.sweep_id,
            "--vs",
            with_thinking.sweep_id,
        ]
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "thinking against the grid, s1 on w2" in out and "| all |" in out and CANARY not in out
