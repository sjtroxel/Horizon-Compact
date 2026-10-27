"""The case session (Phase 5.5 IMPLEMENTATION doc §5.1, K1): planning, checking and writing a frozen case's
sweep, on fakes. No model, no AWS, no GitHub: the bucket is a local folder, the CI runs and probe objects are
canned, and the case is invented (every name and figure here is a canary).
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import boto3
import pytest

from horizon_compact import cli
from horizon_compact.caseprobe.layout import CONTENT_FILES, content_key, runs_prefix
from horizon_compact.caseprobe.session import (
    CASE_LABEL,
    CaseWorld,
    PreparedSweep,
    assemble_experiment,
    build_case_plan,
    case_experiment_name,
    check_case_plan,
    check_frozen,
    check_one_sweep_per_case,
    order_key,
    prepare_case_sweep,
    write_order,
)
from horizon_compact.experiment import load_experiment
from horizon_compact.protocol import lock
from horizon_compact.protocol.cases import (
    CaseContent,
    CiRun,
    ProbeRecord,
    case_lock_text,
    check_case_order,
    content_hashes,
    read_case,
)
from horizon_compact.protocol.gate import check_lock_file
from horizon_compact.protocol.lock import write_lock
from horizon_compact.sweep import launch as sweep_launch
from horizon_compact.sweep.plan import SweepRefusal, build_plan
from horizon_compact.sweep.prompt import render_prompt
from horizon_compact.sweep.runner import CASE_ROLE, sweep_prefix
from horizon_compact.sweep.store import LocalStore
from sweep_helpers import FARGATE, LAPTOP, ScriptedProvider, raw_error, session
from sweep_helpers import FakeClock as Clock

ROOT = Path(__file__).resolve().parents[1]
PKG = "src/horizon_compact"
LABEL = "pre-90"
MAIN, SECOND = "haiku-5-5", "gpt-oss-openrouter"
MODELS = (MAIN, SECOND)
T0 = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)
HOUR = timedelta(hours=1)
FREEZE = "docs/phases/evidence/phase-5/freeze.json"

CONTENT = CaseContent(
    dossier=(
        b'title = "An invented firm"\n'
        b'text = """\nCANARY-DOSSIER-TEXT. The firm makes widgets. Revenue was 100.\n"""\n'
    ),
    scenario=(ROOT / "experiment" / "company" / "scenarios" / "s3.toml").read_bytes(),
    rubric=b'choice = "CANARY-RUBRIC"\n',
)


@pytest.fixture(autouse=True)
def _no_boto3_session(monkeypatch: pytest.MonkeyPatch) -> None:
    def explode(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("a boto3 session was created")

    monkeypatch.setattr(boto3, "Session", explode)


def write(root: Path, path: str, text: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")


def record_text(content: CaseContent = CONTENT, probe_set: int = 1) -> str:
    return case_lock_text(LABEL, probe_set, content_hashes(content))


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """A tagged tree: a fake package, the real ``company`` experiment and models, a lock for both models, the
    case's record and a freeze that lists it."""
    root = tmp_path / "repo"
    for path in (
        f"{PKG}/__init__.py",
        f"{PKG}/experiment.py",
        f"{PKG}/sweep/prompt.py",
        f"{PKG}/sweep/decision.py",
        f"{PKG}/sweep/classify.py",
        f"{PKG}/analysis/__init__.py",
        f"{PKG}/analysis/verdict.py",
    ):
        write(root, path, f"# {path}\n")
    shutil.copytree(ROOT / "experiment" / "company", root / "experiment" / "company")
    shutil.copy(ROOT / "experiment" / "models.toml", root / "experiment" / "models.toml")
    write(root, "experiment/protocol/protocol-v1.md", "# the protocol\n")
    write(root, "uv.lock", "# locked\n")
    write(root, lock.SIMULATION_RELATIVE, '{"code_sha256": "abc"}\n')
    write_lock(root, MODELS, experiment="company")
    write(root, f"experiment/cases/{LABEL}/case.lock", record_text())
    write(root, FREEZE, json.dumps({"cases": [{"label": LABEL, "probe_set": 1}]}))
    return root


def probes(at: datetime = T0 + HOUR, *, passed: bool = True) -> list[ProbeRecord]:
    return [
        ProbeRecord(
            f"cases/{LABEL}/probes/set-1/{model}/call-{n}.json",
            model,
            1,
            passed,
            at + timedelta(minutes=n + 10 * i),
        )
        for i, model in enumerate(MODELS)
        for n in range(1, 4)
    ]


def world(
    tmp_path: Path, content: CaseContent = CONTENT, *, ci_at: datetime = T0, laptop: bool = True
) -> CaseWorld:
    store = LocalStore(tmp_path / "bucket")
    for name, data in zip(
        CONTENT_FILES, (content.dossier, content.scenario, content.rubric), strict=True
    ):
        store.put_new(content_key(LABEL, 1, name), data.decode("utf-8"))
    runs = [CiRun("101", ci_at, record_text())]
    return CaseWorld(store, lambda label: probes(), (lambda label: runs) if laptop else None)


def prepare(
    tree: Path, w: CaseWorld, *, container: bool = False, model: str = MAIN, **kwargs: Any
) -> PreparedSweep:
    arguments: dict[str, Any] = {
        "world": w,
        "identity": FARGATE if container else LAPTOP,
        "container": container,
        "cap_usd": 5.0,
        "package_dir": tree / PKG,
    }
    arguments.update(kwargs)
    return prepare_case_sweep(LABEL, model, 4142789090, **arguments)


# --- the laptop's checks ----------------------------------------------------------------------------------


def test_a_frozen_case_with_its_content_probes_and_order_is_admitted_on_the_laptop(
    tree: Path, tmp_path: Path
) -> None:
    prepared = prepare(tree, world(tmp_path))
    assert prepared.reasons == ()
    assert prepared.ok and prepared.finding is not None and prepared.finding["admitted"] is True
    assert prepared.notes == ("not in the container (launch)",)
    plan = prepared.plan
    assert plan is not None and len(plan.runs) == 150
    assert plan.label == CASE_LABEL and plan.experiment == case_experiment_name(LABEL)
    assert plan.scenarios == ("s3",) and plan.templates == ("w1", "w2", "w3")
    assert plan.repeats == {"s3": 10}
    assert prepared.bound_usd is not None and prepared.bound_usd < 5.0


def test_a_label_that_is_not_in_the_freeze_is_refused(tree: Path, tmp_path: Path) -> None:
    write(tree, FREEZE, json.dumps({"cases": [{"label": "pre-91", "probe_set": 1}]}))
    prepared = prepare(tree, world(tmp_path))
    [line] = prepared.reasons
    assert f"case {LABEL} is not one of {FREEZE}'s frozen cases (pre-91)" in line


def test_an_unreadable_or_missing_freeze_is_refused(tree: Path, tmp_path: Path) -> None:
    (tree / FREEZE).unlink()
    [line] = prepare(tree, world(tmp_path)).reasons
    assert f"{FREEZE} cannot be read" in line
    write(tree, FREEZE, "{not json")
    assert "cannot be read" in prepare(tree, world(tmp_path)).reasons[0]


def test_a_probe_set_that_differs_from_the_record_is_refused(tree: Path, tmp_path: Path) -> None:
    write(tree, FREEZE, json.dumps({"cases": [{"label": LABEL, "probe_set": 2}]}))
    [line] = prepare(tree, world(tmp_path)).reasons
    assert "probe set is 2" in line and "but 1 in experiment/cases/pre-90/case.lock" in line


def test_the_container_does_not_read_the_freeze(tree: Path, tmp_path: Path) -> None:
    (tree / FREEZE).unlink()  # the image holds no docs/: its guarantee is order.json
    w = world(tmp_path, laptop=False)
    plan = prepare(tree, world(tmp_path)).plan
    assert plan is not None
    finding = prepare(tree, world(tmp_path)).finding
    assert finding is not None
    write_order(w.store, LABEL, plan.sweep_id, finding)
    assert prepare(tree, w, container=True).reasons == ()


def test_content_that_does_not_hash_to_the_record_is_refused(tree: Path, tmp_path: Path) -> None:
    changed = CaseContent(CONTENT.dossier + b"# edited\n", CONTENT.scenario, CONTENT.rubric)
    prepared = prepare(tree, world(tmp_path, changed))
    assert prepared.reasons == ("the dossier does not hash to experiment/cases/pre-90/case.lock",)
    assert prepared.plan is None  # nothing was assembled from content that is not the record's


def test_content_that_is_not_in_storage_is_refused(tree: Path, tmp_path: Path) -> None:
    w = world(tmp_path)
    shutil.rmtree(tmp_path / "bucket" / "cases" / LABEL / "set-1")
    [line] = prepare(tree, w).reasons
    assert "dossier.toml is not stored for set 1" in line


def test_a_changed_objectives_file_is_refused(tree: Path, tmp_path: Path) -> None:
    objectives = tree / "experiment" / "company" / "objectives.toml"
    objectives.write_text(objectives.read_text(encoding="utf-8") + "\n# edited\n", encoding="utf-8")
    prepared = prepare(tree, world(tmp_path))
    assert any(
        "company/objectives.toml differs from prereg-v1's" in line for line in prepared.reasons
    )
    assert prepared.plan is None


def test_a_stored_order_finding_that_differs_from_the_recomputed_one_is_refused(
    tree: Path, tmp_path: Path
) -> None:
    w = world(tmp_path)
    first = prepare(tree, w)
    assert first.plan is not None and first.finding is not None
    write_order(w.store, LABEL, first.plan.sweep_id, first.finding)
    assert prepare(tree, w).reasons == ()  # a resume recomputes the same finding
    moved = world(tmp_path, ci_at=T0 - HOUR)  # CI earlier: another run id and time
    [line] = prepare(tree, CaseWorld(w.store, w.probes, moved.runs)).reasons
    assert "differs from the one recomputed now" in line


def test_an_order_the_check_does_not_admit_is_refused_on_the_laptop(
    tree: Path, tmp_path: Path
) -> None:
    prepared = prepare(tree, world(tmp_path, ci_at=T0 + 2 * HOUR))  # CI after the first probe
    assert prepared.finding is not None and prepared.finding["admitted"] is False
    assert any("was first in CI at" in line for line in prepared.reasons)
    assert any(line.startswith("the order check did not admit case") for line in prepared.reasons)


def test_a_failed_probe_is_refused_naming_the_call(tree: Path, tmp_path: Path) -> None:
    w = world(tmp_path)
    failing = CaseWorld(w.store, lambda label: probes(passed=False), w.runs)
    lines = prepare(tree, failing).reasons
    assert len(lines) == 2 and all("failed the recognition probe" in line for line in lines)


def test_a_cost_above_the_cap_is_refused_with_the_bound(tree: Path, tmp_path: Path) -> None:
    prepared = prepare(tree, world(tmp_path), cap_usd=0.01)
    [line] = prepared.reasons
    assert "the worst case for 150 runs is $" in line and "above the cap of $0.01" in line


def test_every_reason_is_collected_at_once(tree: Path, tmp_path: Path) -> None:
    write(tree, FREEZE, json.dumps({"cases": []}))
    w = world(tmp_path, ci_at=T0 + 2 * HOUR)
    failing = CaseWorld(w.store, lambda label: probes(passed=False), w.runs)
    assert len(prepare(tree, failing, cap_usd=0.01).reasons) >= 5


def test_a_model_outside_the_lock_is_refused(tree: Path, tmp_path: Path) -> None:
    prepared = prepare(tree, world(tmp_path), model="qwen-local")
    assert any("model qwen-local is not one of prereg-v1's models" in r for r in prepared.reasons)


# --- the container's checks -------------------------------------------------------------------------------


def test_the_container_reads_the_order_back_and_admits_the_case(tree: Path, tmp_path: Path) -> None:
    laptop = world(tmp_path)
    first = prepare(tree, laptop)
    assert first.plan is not None and first.finding is not None
    write_order(laptop.store, LABEL, first.plan.sweep_id, first.finding)
    in_container = CaseWorld(laptop.store, laptop.probes)
    prepared = prepare(tree, in_container, container=True)
    assert prepared.reasons == () and prepared.notes == ()
    assert prepared.finding == first.finding


def test_the_container_refuses_a_case_with_no_order_finding(tree: Path, tmp_path: Path) -> None:
    w = world(tmp_path, laptop=False)
    [line] = prepare(tree, w, container=True).reasons
    assert f"case {LABEL} has no order finding" in line


def test_the_container_refuses_an_order_finding_that_did_not_admit(
    tree: Path, tmp_path: Path
) -> None:
    w = world(tmp_path, laptop=False)
    plan = prepare(tree, world(tmp_path)).plan
    assert plan is not None
    refused = check_case_order(read_case(tree, LABEL), [], probes()).as_record()
    write_order(w.store, LABEL, plan.sweep_id, refused)
    [line] = prepare(tree, w, container=True).reasons
    assert line.startswith(f"the order check did not admit case {LABEL}: no GitHub Actions run")


def test_the_container_refuses_a_finding_for_another_case_or_not_a_record(
    tree: Path, tmp_path: Path
) -> None:
    w = world(tmp_path, laptop=False)
    plan = prepare(tree, world(tmp_path)).plan
    assert plan is not None
    w.store.put_new(
        order_key(LABEL, plan.sweep_id), json.dumps({"label": "pre-91", "admitted": True})
    )
    [line] = prepare(tree, w, container=True).reasons
    assert "the order finding is for case 'pre-91'" in line
    other = world(tmp_path / "other", laptop=False)
    other.store.put_new(order_key(LABEL, plan.sweep_id), "[1, 2]")
    assert (
        f"order.json for case {LABEL} is not a record"
        in prepare(tree, other, container=True).reasons
    )


def test_the_container_is_required_in_the_container_session(tree: Path, tmp_path: Path) -> None:
    w = world(tmp_path, laptop=False)
    plan = prepare(tree, world(tmp_path)).plan
    finding = prepare(tree, world(tmp_path)).finding
    assert plan is not None and finding is not None
    write_order(w.store, LABEL, plan.sweep_id, finding)
    prepared = prepare(tree, w, container=True, identity=LAPTOP)
    assert prepared.reasons == ("official sweeps run only in the container, never on a laptop",)


# --- the assembled experiment -----------------------------------------------------------------------------


def test_the_assembled_experiment_prompts_exactly_as_one_built_by_hand(
    tree: Path, tmp_path: Path
) -> None:
    lock_, problems = check_lock_file(tree)
    assert lock_ is not None and not problems
    assembled = assemble_experiment(tree, LABEL, CONTENT, lock_)
    by_hand = tmp_path / "hand"
    folder = by_hand / "case-by-hand"
    (folder / "scenarios").mkdir(parents=True)
    (folder / "dossier.toml").write_bytes(CONTENT.dossier)
    shutil.copy(ROOT / "experiment" / "company" / "objectives.toml", folder / "objectives.toml")
    (folder / "scenarios" / "s3.toml").write_bytes(CONTENT.scenario)
    shutil.copy(ROOT / "experiment" / "models.toml", by_hand / "models.toml")
    expected = load_experiment("case-by-hand", by_hand)
    assert assembled.name == case_experiment_name(LABEL)
    for objective in assembled.objectives:
        for template in ("w1", "w2", "w3"):
            ours = render_prompt(
                assembled, assembled.get_scenario("s3"), objective, template, 12345
            )
            theirs = render_prompt(
                expected,
                expected.get_scenario("s3"),
                next(o for o in expected.objectives if o.id == objective.id),
                template,
                12345,
            )
            assert (ours.system, ours.user) == (theirs.system, theirs.user)
    assert (
        "CANARY-DOSSIER-TEXT"
        in render_prompt(
            assembled, assembled.get_scenario("s3"), assembled.objectives[0], "w1", 1
        ).system
    )


def test_a_scenario_without_a_usable_id_is_refused(tree: Path) -> None:
    lock_, _ = check_lock_file(tree)
    assert lock_ is not None
    for scenario in (b"total = 1\n", b'id = "../x"\n', b"= not toml"):
        with pytest.raises(SweepRefusal):
            assemble_experiment(tree, LABEL, CaseContent(CONTENT.dossier, scenario, b""), lock_)


# --- the plan's shape -------------------------------------------------------------------------------------


def assembled(tree: Path) -> Any:
    lock_, _ = check_lock_file(tree)
    assert lock_ is not None
    return assemble_experiment(tree, LABEL, CONTENT, lock_)


def test_nine_repeats_are_refused_naming_what_differs(tree: Path, tmp_path: Path) -> None:
    prepared = prepare(tree, world(tmp_path), repeats=9)
    assert "the plan has repeats {'s3': 9}; a case sweep has exactly 10 a cell" in prepared.reasons
    assert any("the plan has 135 runs, not 150" in line for line in prepared.reasons)


def test_two_templates_are_refused_naming_what_differs(tree: Path, tmp_path: Path) -> None:
    prepared = prepare(tree, world(tmp_path), templates=["w1", "w3"])
    assert (
        "the plan runs templates ['w1', 'w3']; a case sweep runs ['w1', 'w2', 'w3']"
        in prepared.reasons
    )


def test_two_scenarios_are_refused_naming_what_differs() -> None:
    company = load_experiment("company")  # four scenarios
    plan = build_plan(
        company,
        model_key=MAIN,
        label=CASE_LABEL,
        repeats=10,
        seed=1,
        scenarios=["s1", "s3"],
        official=True,
    )
    lines = check_case_plan(company, plan)
    assert any("the plan runs scenarios ['s1', 's3']" in line for line in lines)
    assert any("not a case's experiment" in line for line in lines)


def test_another_label_is_refused_and_the_thinking_label_by_name(
    tree: Path, tmp_path: Path
) -> None:
    prepared = prepare(tree, world(tmp_path), plan_label="thinking")
    [line] = prepared.reasons
    assert "a case sweep's label is 'case', not 'thinking'" in line
    assert "the sub-study's and never runs on a case" in line
    with pytest.raises(SweepRefusal):
        build_case_plan(assembled(tree), MAIN, 1, label="grid")


def test_an_unknown_scenario_is_refused_by_the_planner(tree: Path, tmp_path: Path) -> None:
    prepared = prepare(tree, world(tmp_path), scenarios=["s9"])
    assert prepared.reasons[0].startswith("unknown scenario ['s9']")


# --- where a case sweep writes, and one sweep per case and model ------------------------------------------


def test_a_case_sweep_lives_under_the_case_prefix_and_nowhere_else(tree: Path) -> None:
    name = case_experiment_name(LABEL)
    assert sweep_prefix(name, "sw-1", CASE_ROLE) == f"cases/{LABEL}/runs/sw-1/"
    assert runs_prefix(LABEL, "sw-1") == f"cases/{LABEL}/runs/sw-1/"
    with pytest.raises(ValueError, match="not a case's experiment"):
        sweep_prefix("company", "sw-1", CASE_ROLE)
    with pytest.raises(ValueError):
        runs_prefix("Bad Label", "sw-1")
    with pytest.raises(ValueError):
        runs_prefix(LABEL, "../escape")
    assert sweep_prefix("company", "sw-1", "official") == "official/company/sw-1/"


def test_records_land_under_the_case_prefix_only_and_no_progress_line_names_an_objective(
    tree: Path, tmp_path: Path
) -> None:
    prepared = prepare(tree, world(tmp_path))
    assert prepared.experiment is not None and prepared.plan is not None
    store = LocalStore(tmp_path / "records")
    lines: list[str] = []
    provider = ScriptedProvider(lambda n, request: raw_error(request, "AccessDeniedException"))
    from horizon_compact.providers.base import ModelRoute

    route = ModelRoute(MAIN, "claude-haiku-5-5", "anthropic", "claude-haiku-5-5", thinking_off=True)
    result = session(
        prepared.experiment,
        prepared.plan,
        provider,
        store,
        route=route,
        identity=FARGATE,
        role=CASE_ROLE,
        progress=lines.append,
        clock=Clock(),
    )
    assert result.stopped == "config_error"
    prefix = runs_prefix(LABEL, prepared.plan.sweep_id)
    keys = store.list_keys("")
    assert keys and all(key.startswith(prefix) for key in keys)
    manifest = json.loads(store.get(f"{prefix}manifest.json") or "")
    assert manifest["label"] == CASE_LABEL and manifest["experiment"] == case_experiment_name(LABEL)
    attempt = json.loads(store.get(next(key for key in keys if "/attempt-" in key)) or "")
    assert attempt["label"] == CASE_ROLE
    named = [
        o.id
        for o in prepared.experiment.objectives
        for line in lines
        if re.search(rf"\b{re.escape(o.id)}\b", line)  # the ids are single letters
    ]
    assert lines and named == []


def test_a_second_sweep_for_the_same_case_and_model_is_refused_and_its_resume_is_not(
    tmp_path: Path,
) -> None:
    store = LocalStore(tmp_path / "bucket")
    store.put_new(f"{runs_prefix(LABEL, 'sw-1')}manifest.json", json.dumps({"model_key": MAIN}))
    assert check_one_sweep_per_case(store, LABEL, MAIN, "sw-1") == []  # the same sweep: a resume
    [line] = check_one_sweep_per_case(store, LABEL, MAIN, "sw-2")
    assert f"case {LABEL} already has a sweep for {MAIN} (sw-1)" in line
    assert check_one_sweep_per_case(store, LABEL, SECOND, "sw-2") == []  # another model: allowed
    assert check_one_sweep_per_case(store, "pre-91", MAIN, "sw-2") == []  # another case: allowed


def test_a_manifest_that_cannot_be_read_fails_closed(tmp_path: Path) -> None:
    store = LocalStore(tmp_path / "bucket")
    store.put_new(f"{runs_prefix(LABEL, 'sw-1')}manifest.json", "{broken")
    [line] = check_one_sweep_per_case(store, LABEL, MAIN, "sw-2")
    assert "a manifest that cannot be read (sw-1)" in line


def test_prepare_refuses_a_second_sweep_under_another_seed(tree: Path, tmp_path: Path) -> None:
    w = world(tmp_path)
    w.store.put_new(
        f"{runs_prefix(LABEL, 'older-sweep')}manifest.json", json.dumps({"model_key": MAIN})
    )
    [line] = prepare(tree, w).reasons
    assert "already has a sweep for haiku-5-5 (older-sweep)" in line


def test_the_order_record_is_write_once_and_a_resume_must_match(tmp_path: Path) -> None:
    store = LocalStore(tmp_path / "bucket")
    finding = {"label": LABEL, "admitted": True, "reasons": []}
    write_order(store, LABEL, "sw-1", finding)
    write_order(store, LABEL, "sw-1", finding)  # the same finding again: a resume
    with pytest.raises(SweepRefusal, match="differs from the one recomputed now"):
        write_order(store, LABEL, "sw-1", {**finding, "reasons": ["changed"]})
    assert json.loads(store.get(order_key(LABEL, "sw-1")) or "") == finding


def test_check_frozen_reads_only_the_freeze_it_is_given(tree: Path) -> None:
    record = read_case(tree, LABEL)
    assert check_frozen(tree, LABEL, record) == []
    assert "not one of" in check_frozen(tree, "pre-91", record)[0]


# --- the command line -------------------------------------------------------------------------------------

CASE_ARGS = ["--case", LABEL, "--model", MAIN, "--seed", "4142789090"]


class _Recorder:
    """Stands in for the AWS session and the one call that starts a task; keeps the command it was given."""

    def __init__(self) -> None:
        self.command: list[str] = []

    def client(self, name: str) -> object:
        return object()

    def launch_task(self, ecs: object, ec2: object, *, model_key: str, command: list[str]) -> str:
        self.command = command
        return "arn:aws:ecs:us-east-1:000000000000:task/horizon-compact/abc123"


@pytest.fixture
def cli_tree(tree: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> CaseWorld:
    """The CLI pointed at the invented tree and the fake bucket."""
    laptop = world(tmp_path)
    monkeypatch.setattr("horizon_compact.caseprobe.session.default_package_dir", lambda: tree / PKG)
    monkeypatch.setattr(cli, "_case_world", lambda args, identity: laptop)
    monkeypatch.setattr(cli, "_laptop_git", lambda: ("abc1234", False))
    return laptop


def test_without_case_the_plan_arguments_are_still_required(
    capsys: pytest.CaptureFixture[str],
) -> None:
    for command in ("run", "launch"):
        with pytest.raises(SystemExit) as exc:
            cli.main(["sweep", command, "--model", MAIN, "--seed", "1"])
        assert exc.value.code == 2
        assert "--experiment, --label, --repeats or --repeats-file" in capsys.readouterr().err


def test_a_dry_run_prints_the_shape_the_order_and_the_bound(
    cli_tree: CaseWorld, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["sweep", "run", *CASE_ARGS, "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "(150 runs, model haiku-5-5)" in out
    assert "shape:   scenario s3 x 5 objectives x 3 templates (w1, w2, w3) x 10 repeats" in out
    assert "order:   admitted" in out and "worst case: $" in out
    assert "case sweep: every check passes (dry run; nothing written, nothing called)" in out
    assert cli_tree.store.list_keys("cases/pre-90/runs/") == []  # a dry run writes nothing


def test_a_dry_run_that_fails_prints_every_failure(
    cli_tree: CaseWorld, tree: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write(tree, FREEZE, json.dumps({"cases": []}))
    assert cli.main(["sweep", "run", *CASE_ARGS, "--dry-run", "--repeats", "9"]) == 2
    captured = capsys.readouterr()
    assert "every check passes" not in captured.out
    assert "case sweep refused: " in captured.err
    assert "is not one of" in captured.err and "repeats {'s3': 9}" in captured.err


def test_flags_that_do_not_fit_a_case_are_refused_by_name(
    cli_tree: CaseWorld, capsys: pytest.CaptureFixture[str]
) -> None:
    assert (
        cli.main(["sweep", "run", *CASE_ARGS, "--dry-run", "--official", "--pilot-sweep", "x"]) == 2
    )
    err = capsys.readouterr().err
    assert "--official is not used with --case" in err and "--pilot-sweep is not used" in err
    assert cli.main(["sweep", "run", *CASE_ARGS, "--dry-run", "--experiment", "company"]) == 2
    assert "a case sweep's experiment is 'case-pre-90'" in capsys.readouterr().err
    assert cli.main(["sweep", "run", *CASE_ARGS, "--dry-run", "--label", "thinking"]) == 2
    assert "the sub-study's and never runs on a case" in capsys.readouterr().err


def test_a_launch_writes_the_order_once_then_starts_the_task_with_a_case_command(
    cli_tree: CaseWorld, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    recorder = _Recorder()
    monkeypatch.setattr(cli, "_session", lambda args, identity: recorder)
    monkeypatch.setattr(sweep_launch, "launch_task", recorder.launch_task)
    assert cli.main(["sweep", "launch", *CASE_ARGS, "--profile", "p", "--max-minutes", "600"]) == 0
    out = capsys.readouterr().out
    assert recorder.command == [
        "sweep", "run", "--case", LABEL, "--model", MAIN, "--seed", "4142789090",
        "--store", "s3", "--cap-usd", "5.0", "--max-minutes", "600.0",
    ]  # fmt: skip
    [sweep_line] = [line for line in out.splitlines() if line.startswith("sweep:")]
    sweep_id = sweep_line.split()[1]
    stored = json.loads(cli_tree.store.get(order_key(LABEL, sweep_id)) or "")
    assert stored["admitted"] is True and stored["label"] == LABEL
    assert (
        cli.main(["sweep", "launch", *CASE_ARGS, "--profile", "p"]) == 0
    )  # a resume: same finding


def test_a_refused_launch_writes_nothing_and_starts_nothing(
    cli_tree: CaseWorld,
    tree: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    recorder = _Recorder()
    monkeypatch.setattr(cli, "_session", lambda args, identity: recorder)
    monkeypatch.setattr(sweep_launch, "launch_task", recorder.launch_task)
    write(tree, FREEZE, json.dumps({"cases": []}))
    assert cli.main(["sweep", "launch", *CASE_ARGS, "--profile", "p"]) == 2
    assert recorder.command == []
    assert cli_tree.store.list_keys("cases/pre-90/runs/") == []
    assert "case sweep refused" in capsys.readouterr().err


def test_a_run_on_a_laptop_is_refused_before_anything_is_read(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "_laptop_git", lambda: ("abc1234", False))
    monkeypatch.setattr(
        cli, "_case_world", lambda args, identity: pytest.fail("a laptop run read the bucket")
    )
    assert cli.main(["sweep", "run", *CASE_ARGS, "--store", "s3"]) == 2
    assert "official sweeps run only in the container" in capsys.readouterr().err


def test_a_container_run_needs_the_results_bucket_store(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "identify", lambda env, git: FARGATE)
    assert cli.main(["sweep", "run", *CASE_ARGS]) == 2  # --store defaults to local
    assert "use --store s3" in capsys.readouterr().err


def test_a_container_run_refuses_without_an_order_and_runs_the_session_with_one(
    cli_tree: CaseWorld,
    tree: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from horizon_compact.providers.base import ModelRoute

    in_container = CaseWorld(cli_tree.store, cli_tree.probes)
    monkeypatch.setattr(cli, "identify", lambda env, git: FARGATE)
    monkeypatch.setattr(cli, "_case_world", lambda args, identity: in_container)
    provider = ScriptedProvider(lambda n, request: raw_error(request, "AccessDeniedException"))
    route = ModelRoute(MAIN, "claude-haiku-5-5", "anthropic", "claude-haiku-5-5", thinking_off=True)
    connected: list[str] = []

    def connect(
        args: Any, experiment: Any, model_key: str, identity: Any, estimate: Any, cap: float
    ) -> Any:
        connected.append(experiment.name)
        return provider, route, cli_tree.store, "123456789012"

    monkeypatch.setattr(cli, "_connect", connect)
    run = ["sweep", "run", *CASE_ARGS, "--store", "s3"]
    assert cli.main(run) == 2
    assert "has no order finding" in capsys.readouterr().err
    assert connected == [] and provider.requests == []  # no provider was built, no call was made

    first = prepare(tree, cli_tree)  # the laptop's finding, as a launch would have written it
    assert first.plan is not None and first.finding is not None
    write_order(cli_tree.store, LABEL, first.plan.sweep_id, first.finding)
    assert cli.main(run) == 3  # the scripted provider stops the session on its first call
    out = capsys.readouterr().out
    assert connected == [case_experiment_name(LABEL)] and len(provider.requests) == 1
    assert (
        f"sweep:           {first.plan.sweep_id}" in out and "stopped:         config_error" in out
    )
    prefix = runs_prefix(LABEL, first.plan.sweep_id)
    assert all(key.startswith(prefix) for key in cli_tree.store.list_keys("cases/pre-90/runs/"))
    assert not any(
        key.startswith(("development/", "official/", "pilot/"))
        for key in cli_tree.store.list_keys("")
    )
