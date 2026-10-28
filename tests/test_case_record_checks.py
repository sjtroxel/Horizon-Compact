"""The record checks for case sweeps (Phase 5.5 IMPLEMENTATION doc §5.3, K3) and ``hc sweep status --case``,
on a fake bucket: each check passes on a well-formed world and fails, naming the sweep, on a fixture built to
break it. Canary values sit in every field the pass must not read, and the tests look for them in the report,
the file and the printed lines. No model call, no AWS call, no GitHub call. Every label, id and hash is made
up; the five real labels appear only where the freeze is read or the seed table is reproduced.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from horizon_compact import cli
from horizon_compact.experiment import combine_hashes
from horizon_compact.protocol import recordcheck
from horizon_compact.protocol.cases import CaseRecord
from horizon_compact.protocol.lock import CheckReport, lock_path, read_lock
from horizon_compact.protocol.recordcheck import (
    CASE_MODELS,
    FREEZE_CI_DONE,
    PREREG_COMMIT,
    case_seed,
    format_case_report,
    frozen_case_labels,
    frozen_case_records,
    run_case_checks,
)
from horizon_compact.providers.base import THINKING_STUDY_THINKING_NOTE
from horizon_compact.sweep.store import LocalStore, Store

ROOT = Path(__file__).resolve().parents[1]
LOCK = read_lock(lock_path(ROOT))
CANARY = "CANARY-DO-NOT-READ-6203"
UNREAD = ("validation", "tool_calls", "text_blocks", "raw_response", "parsed_decision", "request")
AFTER = "2026-10-28T09:00:00+00:00"
DIGEST = "sha256:" + "ab" * 32
HAIKU, GPT = CASE_MODELS
LABELS = ("pre-90", "pre-91")
# What each provider writes in a call's record, word for word (as tests/test_record_checks.py has it).
RECORDED = {HAIKU: "off: thinking {type: disabled} sent", GPT: "reasoning effort medium sent"}
OBJECTIVES_HASH = LOCK.content.files["company/objectives.toml"]
SCENARIO_FILE = "s3"
# Section 4's table, word for word: the ten drawn seeds.
SEEDS = {
    ("closure-07", HAIKU): 4142789090,
    ("closure-19", HAIKU): 916347355,
    ("pre-11", HAIKU): 3510822617,
    ("pre-25", HAIKU): 1933638959,
    ("pre-224", HAIKU): 4141966721,
    ("closure-07", GPT): 2401484987,
    ("closure-19", GPT): 537881194,
    ("pre-11", GPT): 218789764,
    ("pre-25", GPT): 1259122587,
    ("pre-224", GPT): 1744604528,
}


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def record_of(label: str) -> CaseRecord:
    return CaseRecord(
        case_version=1,
        label=label,
        probe_set=1,
        dossier_sha256=sha(f"{label} dossier"),
        scenario_sha256=sha(f"{label} scenario"),
        rubric_sha256=sha(f"{label} rubric"),
    )


RECORDS = {label: record_of(label) for label in LABELS}


def record_for(label: str) -> CaseRecord:
    return RECORDS.get(label) or record_of(label)


def file_hashes(label: str) -> dict[str, str]:
    folder = f"case-{label}"
    return {
        f"{folder}/dossier.toml": record_for(label).dossier_sha256,
        f"{folder}/objectives.toml": OBJECTIVES_HASH,
        f"{folder}/scenarios/{SCENARIO_FILE}.toml": record_for(label).scenario_sha256,
        "models.toml": sha("models"),
    }


def content_hash(hashes: dict[str, str]) -> str:
    return combine_hashes(
        {path: digest for path, digest in hashes.items() if path != "models.toml"}
    )


def rid(n: int) -> str:
    return f"r-{n:012x}"


class GetLog(LocalStore):
    """A local store that remembers every key it was asked for."""

    def __init__(self, root: Path) -> None:
        super().__init__(root)
        self.gets: list[str] = []

    def get(self, key: str) -> str | None:
        self.gets.append(key)
        return super().get(key)


class World:
    """A small bucket: a sweep for each of two cases on each of the two models."""

    def __init__(self, tmp_path: Path, store: Store | None = None) -> None:
        self.store = store or LocalStore(tmp_path)
        self.counter = 0

    def sweep(
        self,
        case: str,
        model: str,
        *,
        sweep_id: str | None = None,
        runs: int = 150,
        finished: int | None = None,
        order: dict[str, Any] | str | None = None,
        manifest: dict[str, Any] | None = None,
        hashes: dict[str, str] | None = None,
        final_status: str = CANARY,
        **attempt: Any,
    ) -> list[str]:
        label = case
        sweep_id = sweep_id or f"sw-{label}-{model}"
        prefix = f"cases/{label}/runs/{sweep_id}/"
        ids = [rid(self.counter + i) for i in range(runs)]
        self.counter += runs
        files = hashes or file_hashes(label)
        header: dict[str, Any] = {
            "sweep_id": sweep_id, "label": "case", "experiment": f"case-{label}", "model_key": model,
            "seed": case_seed(model, label), "content_hash": content_hash(files),
            "scenarios": [SCENARIO_FILE], "templates": ["w1", "w2", "w3"],
            "repeats": {SCENARIO_FILE: 10},
            "runs": [{"run_id": r, "objective_id": CANARY, "menu_order_seed": CANARY} for r in ids],
        }  # fmt: skip
        self.store.put_new(f"{prefix}manifest.json", json.dumps({**header, **(manifest or {})}))
        if order != "missing":
            admitted = order if isinstance(order, dict) else {}
            finding = {
                "label": label, "admitted": True, "reasons": [], "rubric_run": CANARY,
                "first_probe": CANARY, **admitted,
            }  # fmt: skip
            self.store.put_new(f"{prefix}order.json", json.dumps(finding))
        locked = LOCK.models[model]
        base: dict[str, Any] = {
            "label": "case", "sweep_id": sweep_id, "scenario_id": SCENARIO_FILE,
            "wording_variant_id": "w1", "started_at": AFTER, "runner": "fargate",
            "image_digest": DIGEST, "git_dirty": False, "thinking": RECORDED[model],
            "effort": "not set", "max_tokens": 3072, "cost_usd": 0.001,
            "content_hash": content_hash(files), "model_key": model, "status": "valid",
            "provider_details": {"served_by": "DeepInfra" if locked.openrouter_provider else "x"},
            "dossier_hash": record_for(label).dossier_sha256, "file_hashes": files,
            "objective_id": CANARY, "usage": {"output_tokens": 9}, "memo": CANARY,
            **dict.fromkeys(UNREAD, CANARY),
        }  # fmt: skip
        base.update(attempt)
        done = runs if finished is None else finished
        for i, run in enumerate(ids):
            self.store.put_new(
                f"{prefix}runs/{run}/attempt-1.json",
                json.dumps({**base, "run_id": run, "attempt": 1}),
            )
            if i < done:
                self.store.put_new(
                    f"{prefix}runs/{run}/final.json", json.dumps({"status": final_status})
                )
        self.store.put_new(
            f"{prefix}sessions/20261028T090000Z-fargate.json",
            json.dumps(
                {
                    "runner": "fargate",
                    "image_digest": DIGEST,
                    "started_at": AFTER,
                    "stopped": "complete",
                }
            ),
        )
        return ids


def good_world(tmp_path: Path, store: Store | None = None) -> World:
    world = World(tmp_path, store)
    for label in LABELS:
        for model in CASE_MODELS:
            world.sweep(label, model)
    return world


def report(
    world: World, frozen: list[str] | None = None, problems: list[str] | None = None
) -> recordcheck.RecordReport:
    return run_case_checks(world.store, LOCK, frozen or [], RECORDS, problems or [])


def verdicts(result: recordcheck.RecordReport) -> dict[str, bool]:
    return {check.name: check.ok for check in result.checks}


def lines_of(result: recordcheck.RecordReport, name: str) -> str:
    return "\n".join(next(c for c in result.checks if c.name == name).lines)


def text_of(result: recordcheck.RecordReport) -> str:
    return format_case_report(
        result, protocol=LOCK.protocol, tree="abc123", made_at="2026-10-28T00:00:00Z"
    )


# --- the seeds and the constants ----------------------------------------------------------------------------


def test_the_seeds_are_computed_and_reproduce_the_tables_ten_values() -> None:
    assert {key: case_seed(key[1], key[0]) for key in SEEDS} == SEEDS
    assert case_seed(HAIKU, "closure-07") == 4142789090


def test_p_is_the_commit_the_tag_record_names_and_the_cutoff_is_the_freeze_runs_completion() -> (
    None
):
    record = (ROOT / "docs/phases/evidence/phase-3.5/tag-record.md").read_text(encoding="utf-8")
    assert f"`{PREREG_COMMIT}`" in record
    assert FREEZE_CI_DONE.isoformat() == "2026-10-27T10:20:15+00:00"


def test_the_models_are_the_locks_two_and_sections_4s() -> None:
    assert set(CASE_MODELS) == set(LOCK.models) == {"haiku-5-5", "gpt-oss-openrouter"}


# --- the checks ---------------------------------------------------------------------------------------------


def test_a_well_formed_world_passes_every_check_and_the_report_holds_no_unread_field(
    tmp_path: Path,
) -> None:
    result = report(good_world(tmp_path))
    assert all(verdicts(result).values()), [c for c in result.checks if not c.ok]
    assert [c.name for c in result.checks] == [
        "cases", "one sweep", "case plan", "seed", "case content", "order", "model", "container",
        "image", "request", "complete", "after the freeze", "frozen files",
    ]  # fmt: skip
    text = text_of(result)
    assert CANARY not in text and "every check passes" in text
    assert len(result.sweeps) == 4
    row = next(line for line in text.splitlines() if "`sw-pre-90-haiku-5-5`" in line)
    assert row == (
        "| pre-90 | `sw-pre-90-haiku-5-5` | haiku-5-5 | 150 | 150 | 150 | {'valid': 150} | 1 | 0.1500 |"
    )
    assert f"{DIGEST}" in lines_of(result, "image")


def test_before_any_case_run_all_pairs_are_missing_and_the_checks_fail(tmp_path: Path) -> None:
    result = report(World(tmp_path))
    assert verdicts(result)["one sweep"] is False
    lines = lines_of(result, "one sweep").splitlines()
    assert len(lines) == len(LABELS) * len(CASE_MODELS)
    assert "case pre-90 on haiku-5-5: no sweep" in lines
    assert all(ok for name, ok in verdicts(result).items() if name != "one sweep")
    assert "AT LEAST ONE CHECK FAILED" in text_of(result)


def _second_manifest(w: World) -> None:
    w.sweep("pre-90", HAIKU, sweep_id="a-second-sweep", runs=2)


def _stray_label(w: World) -> None:
    w.store.put_new("cases/pre-77/set-1/dossier.toml", "x")


BREAKS: list[tuple[str, str, Callable[[World], object]]] = [
    ("one sweep", "2 sweeps (a-second-sweep, sw-pre-90-haiku-5-5)", _second_manifest),
    ("cases", "'pre-77', which is not a frozen case", _stray_label),
    ("case plan", "pre-90/odd: 149 runs", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", runs=149)),
    ("case plan", "repeats {'s3': 9}", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", runs=150, manifest={"repeats": {"s3": 9}})),
    ("case plan", "repeats 10", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", manifest={"repeats": 10})),
    ("case plan", "templates ['w1', 'w3']", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", manifest={"templates": ["w1", "w3"]})),
    ("case plan", "2 scenarios, not 1", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", manifest={"scenarios": ["s1", "s3"]})),
    ("case plan", "experiment 'company'", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", manifest={"experiment": "company"})),
    ("case plan", "label 'grid', not 'case'", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", manifest={"label": "grid"})),
    ("case plan", "calls are labeled ['official']", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", label="official")),
    ("case plan", "model 'nova-lite' is not one of", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", manifest={"model_key": "nova-lite"})),
    ("seed", "seed 12345, not the drawn", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", manifest={"seed": 12345})),
    ("seed", "seed '4142789090'", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", manifest={"seed": "4142789090"})),
    ("case content", "do not carry the dossier hash", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", dossier_hash="0" * 64)),
    ("case content", "scenario file hash is not case.lock's", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", hashes={**file_hashes("pre-90"), "case-pre-90/scenarios/s3.toml": "0" * 64})),
    ("case content", "objectives file hash is not prereg-v1's", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", hashes={**file_hashes("pre-90"), "case-pre-90/objectives.toml": "0" * 64})),
    ("case content", "manifest's content hash is not that of a call's files", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", manifest={"content_hash": "0" * 64})),
    ("case content", "a content hash that is not the manifest's", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", content_hash="0" * 64)),
    ("case content", "dossier file hash is not case.lock's", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", hashes={k: v for k, v in file_hashes("pre-90").items() if "dossier" not in k})),
    ("order", "the order finding is not admitted (order.json is not stored)", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", order="missing")),
    ("order", "(a reason for refusing)", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", order={"admitted": False, "reasons": ["a reason for refusing"]})),
    ("order", "for case 'pre-91'", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", order={"label": "pre-91"})),
    ("model", "calls name model(s)", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", model_key=HAIKU)),
    ("container", "not run on fargate", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", runner="laptop")),
    ("container", "no image digest", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", image_digest=None)),
    ("container", "clean git tree", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", git_dirty=True)),
    ("request", "whose thinking is", lambda w: w.sweep("pre-90", HAIKU, sweep_id="odd", thinking="not set")),
    ("request", "whose thinking is", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", thinking=THINKING_STUDY_THINKING_NOTE)),
    ("request", "served by 'Other Host'", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", provider_details={"served_by": "Other Host"})),
    ("complete", "1 of 150 runs have no final record", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", finished=149)),
    ("after the freeze", "began before 2026-10-27T10:20:15+00:00", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", started_at="2026-10-27T10:20:14+00:00")),
    ("after the freeze", "no readable start time", lambda w: w.sweep("pre-90", GPT, sweep_id="odd", started_at="not a time")),
]  # fmt: skip


@pytest.mark.parametrize(("check", "needle", "mutate"), BREAKS)
def test_each_check_fails_on_a_fixture_built_to_break_it_and_names_the_sweep(
    tmp_path: Path, check: str, needle: str, mutate: Callable[[World], object]
) -> None:
    world = World(tmp_path)
    for label in LABELS:
        for model in CASE_MODELS:
            if (label, model) != ("pre-90", GPT) or check in ("one sweep", "cases"):
                world.sweep(label, model)
    mutate(world)
    result = report(world)
    assert verdicts(result)[check] is False, lines_of(result, check)
    assert needle in lines_of(result, check), lines_of(result, check)
    assert "pre-90/" in lines_of(result, check) or check in ("one sweep", "cases")
    text = text_of(result)
    assert "FAIL" in text and CANARY not in text


def test_a_sweep_for_a_case_outside_the_run_set_is_a_failure_not_a_skip(tmp_path: Path) -> None:
    world = good_world(tmp_path)
    world.sweep("pre-91", HAIKU, sweep_id="third", runs=1)
    assert "case pre-91 on haiku-5-5: 2 sweeps" in lines_of(report(world), "one sweep")
    extra = World(tmp_path / "other")
    extra.sweep(
        "pre-92", HAIKU, sweep_id="x", runs=1
    )  # not in the freeze: found as a label, not collected
    result = report(extra)
    assert "'pre-92', which is not a frozen case" in lines_of(result, "cases")
    assert verdicts(result)["cases"] is False


def test_problems_reading_the_freeze_fail_the_cases_check(tmp_path: Path) -> None:
    result = report(good_world(tmp_path), problems=["freeze.json cannot be read"])
    assert verdicts(result)["cases"] is False
    assert "freeze.json cannot be read" in lines_of(result, "cases")


def test_a_frozen_file_failure_from_hc_protocol_check_fails_the_last_check(tmp_path: Path) -> None:
    result = report(good_world(tmp_path), frozen=["instrument differs: sweep/prompt.py"])
    assert verdicts(result)["frozen files"] is False
    assert "sweep/prompt.py" in lines_of(result, "frozen files")


def test_the_run_counts_cover_status_sessions_and_cost(tmp_path: Path) -> None:
    world = World(tmp_path)
    world.sweep("pre-90", HAIKU, runs=3, status="no_tool_call", cost_usd=0.5)
    text = text_of(report(world))
    row = next(line for line in text.splitlines() if "`sw-pre-90-haiku-5-5`" in line)
    assert row == (
        "| pre-90 | `sw-pre-90-haiku-5-5` | haiku-5-5 | 3 | 3 | 3 | {'no_tool_call': 3} | 1 | 1.5000 |"
    )


# --- read-only and blind -----------------------------------------------------------------------------------


class ReadOnly(LocalStore):
    def put_new(self, key: str, text: str) -> bool:
        raise AssertionError("the record checks wrote to the store")


def test_the_checks_only_read(tmp_path: Path) -> None:
    world = good_world(tmp_path)
    result = run_case_checks(ReadOnly(tmp_path), LOCK, [], RECORDS)
    assert all(c.ok for c in result.checks) and world.counter > 0


def test_the_pass_reads_only_manifests_attempts_sessions_and_order_files(tmp_path: Path) -> None:
    store = GetLog(tmp_path)
    world = good_world(tmp_path, store)
    store.gets.clear()
    assert all(c.ok for c in report(world).checks)
    assert store.gets
    for key in store.gets:
        assert re.search(
            r"/(manifest|order)\.json$|/attempt-\d+\.json$|/sessions/[^/]+\.json$", key
        ), key  # never final.json's body, a rubric, a dossier or a probe


def test_no_canary_reaches_the_report_whatever_the_fields_hold(tmp_path: Path) -> None:
    world = good_world(tmp_path)
    world.sweep("pre-90", GPT, sweep_id="odd", runs=1, order={"admitted": False, "reasons": ["r"]})
    text = text_of(report(world))
    assert "FAIL" in text and CANARY not in text


def test_the_module_never_names_a_field_it_must_not_read() -> None:
    source = Path(recordcheck.__file__).read_text(encoding="utf-8")
    code = re.sub(r'""".*?"""', "", source, flags=re.S)
    # "request" is also a check's name in the grid's pass, so only the record's other fields are listed
    for field in (
        *UNREAD[:-1],
        "objective_id",
        "amounts",
        "choice",
        "memo",
        "usage",
        "stop_reason",
    ):
        assert f'"{field}"' not in code and f"'{field}'" not in code, field
    assert "rubric.toml" not in code and "set-" not in code and "load_content" not in code


# --- reading the freeze ------------------------------------------------------------------------------------


def test_the_real_freeze_and_case_locks_read_clean() -> None:
    records, problems = frozen_case_records(ROOT)
    assert sorted(records) == sorted(["closure-07", "closure-19", "pre-11", "pre-25", "pre-224"])
    assert problems == []
    assert frozen_case_labels(ROOT) == list(records)


def test_an_unreadable_freeze_is_a_problem_not_an_empty_set(tmp_path: Path) -> None:
    records, problems = frozen_case_records(tmp_path)
    assert records == {} and "cannot be read" in problems[0]
    assert frozen_case_labels(tmp_path) == []


def test_a_label_with_no_case_lock_or_the_wrong_probe_set_is_a_problem(tmp_path: Path) -> None:
    freeze = tmp_path / "docs/phases/evidence/phase-5/freeze.json"
    freeze.parent.mkdir(parents=True)
    freeze.write_text(
        json.dumps(
            {"cases": [{"label": "pre-90", "probe_set": 2}, {"label": "pre-91", "probe_set": 1}]}
        )
    )
    lock_file = tmp_path / "experiment/cases/pre-90/case.lock"
    lock_file.parent.mkdir(parents=True)
    from horizon_compact.protocol.cases import case_lock_text

    lock_file.write_text(
        case_lock_text(
            "pre-90", 1, {k: sha(k) for k in ("dossier_sha256", "scenario_sha256", "rubric_sha256")}
        )
    )
    records, problems = frozen_case_records(tmp_path)
    assert list(records) == ["pre-90"]
    assert any("pre-91" in p and "no case record" in p for p in problems)
    assert any("probe set" in p for p in problems)


# --- the command -------------------------------------------------------------------------------------------


@pytest.fixture
def command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[World, Path]:
    world = good_world(tmp_path / "bucket")
    root = tmp_path / "repo"
    lock_file = lock_path(root)
    lock_file.parent.mkdir(parents=True)
    lock_file.write_bytes(lock_path(ROOT).read_bytes())
    monkeypatch.setattr(cli, "_session", lambda args, identity: None)
    monkeypatch.setattr(cli, "_store", lambda args, session: world.store)
    monkeypatch.setattr(cli, "_laptop_git", lambda: ("abc123def456", False))
    monkeypatch.setattr(cli, "check_lock", lambda r: CheckReport())
    monkeypatch.setattr(cli, "frozen_case_records", lambda r: (RECORDS, []))
    return world, root


def test_the_cases_command_writes_the_case_file_and_exits_by_the_verdict(
    command: tuple[World, Path], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _, root = command
    args = ["protocol", "--root", str(root), "records", "--cases", "--store", "local"]
    assert cli.main(args) == 0
    written = (root / cli.CASE_RECORD_CHECKS_FILE).read_text(encoding="utf-8")
    assert cli.CASE_RECORD_CHECKS_FILE == "docs/phases/evidence/phase-5.5/record-checks.md"
    assert "every check passes" in written and CANARY not in written
    out = capsys.readouterr().out
    assert "pass     one sweep" in out and f"written: {cli.CASE_RECORD_CHECKS_FILE}" in out
    assert not (root / cli.RECORD_CHECKS_FILE).exists()  # the grid's file is not touched
    monkeypatch.setattr(cli, "check_lock", lambda r: CheckReport(failures=("analysis differs",)))
    assert cli.main(args) == 1
    assert "AT LEAST ONE CHECK FAILED" in (root / cli.CASE_RECORD_CHECKS_FILE).read_text(
        encoding="utf-8"
    )


def test_before_any_run_the_command_reports_ten_missing_and_exits_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "repo"
    lock_file = lock_path(root)
    lock_file.parent.mkdir(parents=True)
    lock_file.write_bytes(lock_path(ROOT).read_bytes())
    empty = World(tmp_path / "bucket")
    five = {f"pre-{n}": record_of(f"pre-{n}") for n in range(5)}
    monkeypatch.setattr(cli, "_session", lambda args, identity: None)
    monkeypatch.setattr(cli, "_store", lambda args, session: empty.store)
    monkeypatch.setattr(cli, "_laptop_git", lambda: ("abc123def456", False))
    monkeypatch.setattr(cli, "check_lock", lambda r: CheckReport())
    monkeypatch.setattr(cli, "frozen_case_records", lambda r: (five, []))
    code = cli.main(["protocol", "--root", str(root), "records", "--cases", "--store", "local"])
    assert code == 1
    written = (root / cli.CASE_RECORD_CHECKS_FILE).read_text(encoding="utf-8")
    assert written.count(": no sweep") == 10
    assert re.search(r"^FAIL\s+one sweep$", capsys.readouterr().out, re.M)


def test_without_cases_the_grid_file_is_still_the_one_written(
    command: tuple[World, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    _, root = command
    monkeypatch.setattr(
        cli, "run_record_checks", lambda store, lock, frozen: recordcheck.RecordReport((), ())
    )
    assert cli.main(["protocol", "--root", str(root), "records", "--store", "local"]) == 0
    assert (root / cli.RECORD_CHECKS_FILE).is_file()
    assert not (root / cli.CASE_RECORD_CHECKS_FILE).exists()


# --- hc sweep status --case ---------------------------------------------------------------------------------

FROZEN = "closure-07"  # one of the freeze's labels; the sweep and its records are invented


@pytest.fixture
def status_bucket(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> World:
    world = World(tmp_path / "bucket")
    world.sweep(FROZEN, HAIKU, sweep_id="sw-1", runs=3, finished=2, final_status="valid")
    monkeypatch.setattr(cli, "_session", lambda args, identity: None)
    monkeypatch.setattr(cli, "_store", lambda args, session: world.store)
    monkeypatch.setattr(cli, "_laptop_git", lambda: ("abc123def456", False))
    return world


def test_status_reads_a_case_sweep_and_prints_no_objective_or_unread_field(
    status_bucket: World, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["sweep", "status", "--case", FROZEN, "--sweep-id", "sw-1"]) == 0
    out = capsys.readouterr().out
    assert "sweep:           sw-1" in out
    assert "runs finished:   2 of 3  {'valid': 2}" in out
    assert "attempts:        3  {'valid': 3}" in out
    assert "cost so far:     $0.0030" in out and "stopped: complete" in out
    assert CANARY not in out and "objective" not in out


def test_status_of_a_case_without_a_manifest_says_nothing_has_run(
    status_bucket: World, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["sweep", "status", "--case", "pre-11", "--sweep-id", "sw-9"]) == 0
    assert "no manifest for sw-9: nothing has run yet" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("extra", "needle"),
    [
        (["--case", FROZEN], "--case needs --sweep-id"),
        (["--case", "pre-90", "--sweep-id", "sw-1"], "'pre-90' is not one of the frozen cases"),
        (
            ["--case", FROZEN, "--sweep-id", "sw-1", "--role", "official"],
            "--role is not used with --case",
        ),
        (
            ["--case", FROZEN, "--sweep-id", "sw-1", "--experiment", "company"],
            "--experiment is not used",
        ),
        (
            ["--case", FROZEN, "--sweep-id", "sw-1", "--model", "haiku-5-5"],
            "--model is not used with --case",
        ),
        (
            ["--case", FROZEN, "--sweep-id", "sw-1", "--repeats", "9"],
            "--repeats is not used with --case",
        ),
    ],
)
def test_status_refuses_what_does_not_fit_a_case(
    status_bucket: World, capsys: pytest.CaptureFixture[str], extra: list[str], needle: str
) -> None:
    assert cli.main(["sweep", "status", *extra]) == 2
    captured = capsys.readouterr()
    assert needle in captured.err and "sweep:" not in captured.out


def test_status_without_case_still_needs_the_plan_arguments(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["sweep", "status", "--sweep-id", "sw-1"])
    assert exc.value.code == 2
    assert (
        "--model, --seed, --experiment, --label, --repeats or --repeats-file"
        in capsys.readouterr().err
    )


def test_status_without_case_reads_the_role_it_is_asked_for_as_before(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    store = LocalStore(tmp_path)
    store.put_new(
        "official/placeholder/sw-1/manifest.json",
        json.dumps({"sweep_id": "sw-1", "runs": [{"run_id": "r-000000000001"}]}),
    )
    monkeypatch.setattr(cli, "_session", lambda args, identity: None)
    monkeypatch.setattr(cli, "_store", lambda args, session: store)
    monkeypatch.setattr(cli, "_laptop_git", lambda: ("abc123def456", False))
    plan = [
        "--experiment",
        "placeholder",
        "--model",
        HAIKU,
        "--repeats",
        "1",
        "--seed",
        "5",
        "--label",
        "x",
    ]
    base = ["sweep", "status", *plan, "--sweep-id", "sw-1"]
    assert cli.main(base) == 0
    assert "no manifest for sw-1" in capsys.readouterr().out
    assert cli.main([*base, "--role", "official"]) == 0
    assert "runs finished:   0 of 1" in capsys.readouterr().out
