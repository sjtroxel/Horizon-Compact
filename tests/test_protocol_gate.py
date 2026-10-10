"""The official-sweep gate and the repeat count (Phase 3.5 IMPLEMENTATION doc section 7, build step 5).

Every refusal both ways, on a synthetic tree: a small fake package, a copy of the company experiment and the
real ``models.toml``, a stand-in protocol document, and a lock written by ``hc protocol lock`` for Sonnet 4.6.
These are the cases the tag-day dry runs repeat against the tagged commit (section 7.2), so they hold in CI
after the tag.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import boto3
import pytest

from analysis_helpers import decision, relocate
from horizon_compact import cli
from horizon_compact.analysis.repeats import ChoiceRepeats, ShareRepeats
from horizon_compact.experiment import Experiment, load_experiment
from horizon_compact.protocol import gate, lock
from horizon_compact.protocol.gate import (
    PILOT_LABEL,
    PilotRefusal,
    RepeatDecision,
    check_official,
    check_repeats,
    describe_decision,
    repeats_key,
    required_repeats,
    run_gate,
    write_repeats,
)
from horizon_compact.protocol.lock import LINE_ENDING_NOTE, read_lock, write_lock
from horizon_compact.sweep import launch as sweep_launch
from horizon_compact.sweep.plan import SweepPlan, SweepRefusal, build_plan
from horizon_compact.sweep.runner import sweep_prefix
from horizon_compact.sweep.store import LocalStore
from sweep_helpers import FARGATE, LAPTOP, SONNET_ROUTE, ScriptedProvider, raw_ok, session

ROOT = Path(__file__).resolve().parents[1]
PKG = "src/horizon_compact"
MODEL = "sonnet-4-6"
DECISION = f"{PKG}/sweep/decision.py"
VERDICT = f"{PKG}/analysis/verdict.py"
DOCUMENT = "experiment/protocol/protocol-v1.md"
MODELS = "experiment/models.toml"
SCENARIO = "experiment/company/scenarios/s1.toml"
REFUSED = "official sweep refused: "

PACKAGE_FILES = (
    f"{PKG}/__init__.py",
    f"{PKG}/experiment.py",
    f"{PKG}/model_config.py",
    f"{PKG}/sweep/prompt.py",
    DECISION,
    f"{PKG}/sweep/classify.py",
    f"{PKG}/sweep/runner.py",
    f"{PKG}/analysis/__init__.py",
    VERDICT,
    f"{PKG}/analysis/matcher_thresholds.toml",
)


def write(root: Path, path: str, text: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")


def append(root: Path, path: str, text: str = "\n# changed\n") -> None:
    target = root / path
    target.write_text(target.read_text(encoding="utf-8") + text, encoding="utf-8", newline="\n")


def replace(root: Path, path: str, old: str, new: str) -> None:
    target = root / path
    text = target.read_text(encoding="utf-8")
    assert old in text
    target.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


@pytest.fixture
def tagged(tmp_path: Path) -> Path:
    """A tree as it would stand at the tag: everything in place and locked for Sonnet 4.6."""
    root = tmp_path / "repo"
    for path in PACKAGE_FILES:
        write(root, path, f"# {path}\n")
    shutil.copytree(ROOT / "experiment" / "company", root / "experiment" / "company")
    shutil.copytree(ROOT / "experiment" / "placeholder", root / "experiment" / "placeholder")
    shutil.copy(ROOT / MODELS, root / MODELS)
    write(root, DOCUMENT, "# the protocol, as tagged\n")
    write(root, "uv.lock", "# the library lock\n")
    write(root, lock.SIMULATION_RELATIVE, '{"code_sha256": "abc123"}\n')
    write_lock(root, (MODEL,))
    return root


def load(root: Path, name: str = "company") -> Experiment:
    return load_experiment(name, root / "experiment")


def plan(
    exp: Experiment,
    *,
    model: str = MODEL,
    label: str = "grid",
    templates: list[str] | None = None,
    scenarios: list[str] | None = None,
    repeats: int = 1,
) -> SweepPlan:
    return build_plan(
        exp,
        model_key=model,
        label=label,
        repeats=repeats,
        seed=1,
        scenarios=scenarios,
        templates=templates,
        official=True,
    )


def failures(root: Path, exp: Experiment | None = None, **kwargs: Any) -> tuple[str, ...]:
    exp = exp or load(root)
    the_plan = kwargs.pop("the_plan", None) or plan(exp)
    identity = kwargs.pop("identity", FARGATE)
    return run_gate(exp, the_plan, identity, package_dir=root / PKG, **kwargs).failures


# --- passes as tagged -------------------------------------------------------------------------------------


def test_the_tagged_tree_passes_every_check_in_the_container(tagged: Path) -> None:
    exp = load(tagged)
    result = run_gate(exp, plan(exp), FARGATE, package_dir=tagged / PKG)
    assert result.ok and result.notes == ()
    assert check_official(exp, plan(exp), FARGATE, package_dir=tagged / PKG).ok


def test_the_grid_with_every_template_and_scenario_passes(tagged: Path) -> None:
    exp = load(tagged)
    full = plan(exp, repeats=2)
    assert set(full.templates) == {"w1", "w2", "w3"} and len(full.scenarios) == 4
    assert failures(tagged, exp, the_plan=full) == ()


def test_prices_quotas_and_pace_may_change(tagged: Path) -> None:
    replace(tagged, MODELS, "input = 3.30", "input = 9.99")
    replace(tagged, MODELS, "requests_per_minute = 10", "requests_per_minute = 2")
    replace(tagged, MODELS, "pace_fraction = 0.8", "pace_fraction = 0.5")
    assert failures(tagged) == ()


def test_run_code_may_change(tagged: Path) -> None:
    append(tagged, f"{PKG}/sweep/runner.py")
    append(tagged, f"{PKG}/model_config.py")
    assert failures(tagged) == ()


def test_the_errata_file_may_change(tagged: Path) -> None:
    write(tagged, "experiment/protocol/errata-v1.md", "# 2026-10-20: a typo in section 3\n")
    assert failures(tagged) == ()


# --- check 1: the lock ------------------------------------------------------------------------------------


def test_no_lock_is_refused_and_the_container_is_still_checked(tagged: Path) -> None:
    (tagged / lock.LOCK_RELATIVE).unlink()
    assert failures(tagged, identity=LAPTOP) == (
        "no committed protocol: experiment/protocol/prereg.lock does not exist (prereg-v1 is not tagged)",
        "official sweeps run only in the container, never on a laptop",
    )


def test_an_unreadable_lock_is_refused(tagged: Path) -> None:
    write(tagged, lock.LOCK_RELATIVE, "this = = broken\n")
    [line] = failures(tagged)
    assert "is not valid TOML" in line


def test_a_lock_of_an_unknown_version_is_refused(tagged: Path) -> None:
    replace(tagged, lock.LOCK_RELATIVE, "lock_version = 1", "lock_version = 9")
    assert failures(tagged) == ("prereg.lock has lock_version 9; this reader knows 1",)


# --- checks 2-7, one change each --------------------------------------------------------------------------


def test_a_changed_protocol_document_is_refused(tagged: Path) -> None:
    append(tagged, DOCUMENT)
    assert failures(tagged) == (f"document differs from prereg-v1: {DOCUMENT}",)


def test_one_byte_in_a_scenario_is_refused_naming_the_file(tagged: Path) -> None:
    append(tagged, SCENARIO, "\n")
    assert failures(tagged) == ("content differs from prereg-v1: company/scenarios/s1.toml",)


def test_the_content_checked_is_the_content_in_hand(tagged: Path) -> None:
    """The gate reads the experiment the sweep will send, not a fresh read of the disk: the scenario is
    changed, loaded, then put back on disk, and the gate still refuses what was loaded."""
    append(tagged, SCENARIO, "\n")
    changed = load(tagged)
    (tagged / SCENARIO).write_text(
        (ROOT / SCENARIO).read_text(encoding="utf-8"), encoding="utf-8", newline="\n"
    )
    assert failures(tagged, changed) == (
        "content differs from prereg-v1: company/scenarios/s1.toml",
    )


def test_another_experiment_is_refused(tagged: Path) -> None:
    exp = load(tagged, "placeholder")
    the_plan = plan(exp)
    assert failures(tagged, exp, the_plan=the_plan)[0] == (
        "experiment is 'placeholder'; prereg-v1 locks 'company'"
    )


def test_one_byte_in_an_instrument_file_is_refused_naming_it(tagged: Path) -> None:
    append(tagged, DECISION)
    assert failures(tagged) == (f"instrument differs from prereg-v1: {DECISION}",)


def test_one_byte_in_an_analysis_file_is_refused_naming_it(tagged: Path) -> None:
    append(tagged, VERDICT)
    assert failures(tagged) == (f"analysis differs from prereg-v1: {VERDICT}",)


def test_a_changed_model_profile_is_refused_naming_the_field(tagged: Path) -> None:
    replace(
        tagged,
        MODELS,
        'inference_profile = "horizon-compact-sonnet-4-6"',
        'inference_profile = "x"',
    )
    assert failures(tagged) == (
        "model sonnet-4-6 differs from prereg-v1: inference_profile is 'x', "
        "locked 'horizon-compact-sonnet-4-6'",
    )


def test_a_changed_model_id_or_route_is_refused(tagged: Path) -> None:
    replace(tagged, MODELS, 'route = "application_profile"', 'route = "geo_profile"')
    assert failures(tagged) == (
        "model sonnet-4-6 differs from prereg-v1: route is 'geo_profile', locked 'application_profile'",
    )


def test_a_model_outside_the_lock_is_refused(tagged: Path) -> None:
    exp = load(tagged)
    assert failures(tagged, exp, the_plan=plan(exp, model="nova-lite")) == (
        "model nova-lite is not one of prereg-v1's models (sonnet-4-6)",
    )


def test_an_experiment_loaded_from_another_tree_is_refused(tagged: Path, tmp_path: Path) -> None:
    elsewhere = tmp_path / "elsewhere"
    shutil.copytree(tagged / "experiment", elsewhere / "experiment")
    exp = load(elsewhere)
    [line] = failures(tagged, exp)
    assert line.startswith("the experiment was loaded from") and "same tree" in line


# --- check 4: the sealed template, grid and pilot ---------------------------------------------------------


def test_a_grid_without_the_sealed_template_is_refused(tagged: Path) -> None:
    exp = load(tagged)
    assert failures(tagged, exp, the_plan=plan(exp, templates=["w1", "w3"])) == (
        "the plan leaves out the sealed template (w2), which the official grid includes",
    )


def test_a_changed_sealed_template_is_refused(tagged: Path) -> None:
    replace(
        tagged,
        "experiment/company/objectives.toml",
        'sealed_template = "w2"',
        'sealed_template = "w3"',
    )
    found = failures(tagged)
    assert "sealed template differs from prereg-v1: now 'w3', locked 'w2'" in found
    assert "content differs from prereg-v1: company/objectives.toml" in found


def test_a_pilot_on_the_development_wordings_passes(tagged: Path) -> None:
    exp = load(tagged)
    pilot = plan(exp, label=PILOT_LABEL, templates=["w1", "w3"], repeats=2)
    assert failures(tagged, exp, the_plan=pilot, pilot=True) == ()


def test_a_pilot_that_includes_the_sealed_template_is_refused(tagged: Path) -> None:
    exp = load(tagged)
    pilot = plan(exp, label=PILOT_LABEL, repeats=2)
    assert failures(tagged, exp, the_plan=pilot, pilot=True) == (
        "a pilot never runs the sealed template (w2): the development wordings only",
    )


def test_a_pilot_with_another_label_is_refused(tagged: Path) -> None:
    exp = load(tagged)
    pilot = plan(exp, label="trial", templates=["w1", "w3"], repeats=2)
    assert failures(tagged, exp, the_plan=pilot, pilot=True) == (
        "a pilot is labeled 'pilot', not 'trial'",
    )


def test_a_pilot_in_any_shape_but_the_protocols_is_refused_naming_each_difference(
    tagged: Path,
) -> None:
    """Protocol 8.1: every scenario, both development wordings, two repeats a cell (OPEN entry 2026-10-10)."""
    exp = load(tagged)
    small = plan(exp, label=PILOT_LABEL, templates=["w1"], scenarios=["s1", "s3"], repeats=3)
    assert failures(tagged, exp, the_plan=small, pilot=True) == (
        "a pilot runs every scenario; this one leaves out ['s2', 's4']",
        "a pilot runs every development wording; this one leaves out ['w3']",
        "a pilot runs 2 repeats a cell; this one has {'s1': 3, 's3': 3}",
    )
    uneven = build_plan(
        exp,
        model_key=MODEL,
        label=PILOT_LABEL,
        repeats={**dict.fromkeys(exp.scenarios, 2), "s4": 20},
        seed=1,
        templates=["w1", "w3"],
        official=True,
    )
    assert failures(tagged, exp, the_plan=uneven, pilot=True) == (
        "a pilot runs 2 repeats a cell; this one has {'s4': 20}",
    )


def test_the_shape_rule_is_for_pilots_only(tagged: Path) -> None:
    exp = load(tagged)
    assert (
        failures(tagged, exp, the_plan=plan(exp, repeats=20)) == ()
    )  # the grid: any count the pilot set


def test_a_grid_labeled_pilot_is_refused(tagged: Path) -> None:
    exp = load(tagged)
    assert failures(tagged, exp, the_plan=plan(exp, label=PILOT_LABEL)) == (
        "the label 'pilot' is the pilot's, and this plan is not run as a pilot",
    )


# --- check 8 and the reporting ----------------------------------------------------------------------------


def test_a_laptop_is_refused_when_the_container_is_required(tagged: Path) -> None:
    assert failures(tagged, identity=LAPTOP) == (
        "official sweeps run only in the container, never on a laptop",
    )


def test_the_dry_run_on_a_laptop_notes_the_container_and_judges_checks_one_to_seven(
    tagged: Path,
) -> None:
    exp = load(tagged)
    result = run_gate(exp, plan(exp), LAPTOP, require_container=False, package_dir=tagged / PKG)
    assert result.ok and result.notes == ("not in the container (dry run)",)
    append(tagged, DECISION)
    result = run_gate(exp, plan(exp), LAPTOP, require_container=False, package_dir=tagged / PKG)
    assert result.failures == (f"instrument differs from prereg-v1: {DECISION}",)


def test_every_failure_is_reported_together_in_check_order(tagged: Path) -> None:
    append(tagged, DOCUMENT)
    append(tagged, SCENARIO, "\n")
    append(tagged, DECISION)
    append(tagged, VERDICT)
    replace(tagged, MODELS, 'model_id = "anthropic.claude-sonnet-4-6"', 'model_id = "anthropic.x"')
    assert failures(tagged, identity=LAPTOP) == (
        f"document differs from prereg-v1: {DOCUMENT}",
        "content differs from prereg-v1: company/scenarios/s1.toml",
        f"instrument differs from prereg-v1: {DECISION}",
        f"analysis differs from prereg-v1: {VERDICT}",
        "model sonnet-4-6 differs from prereg-v1: model_id is 'anthropic.x', "
        "locked 'anthropic.claude-sonnet-4-6'",
        "official sweeps run only in the container, never on a laptop",
    )


def test_a_hash_failure_carries_the_line_ending_note(tagged: Path) -> None:
    append(tagged, DECISION)
    exp = load(tagged)
    assert LINE_ENDING_NOTE in run_gate(exp, plan(exp), FARGATE, package_dir=tagged / PKG).notes


def test_check_official_raises_one_line_per_failure_in_the_refusal_form(tagged: Path) -> None:
    append(tagged, DECISION)
    exp = load(tagged)
    with pytest.raises(SweepRefusal) as caught:
        check_official(exp, plan(exp), LAPTOP, package_dir=tagged / PKG)
    assert str(caught.value).splitlines() == [
        f"{REFUSED}instrument differs from prereg-v1: {DECISION}",
        f"{REFUSED}official sweeps run only in the container, never on a laptop",
    ]


def test_the_real_repository_has_no_lock_so_every_official_sweep_is_refused() -> None:
    exp = load_experiment("company")
    with pytest.raises(SweepRefusal, match="no committed protocol"):
        check_official(exp, plan(exp), FARGATE)


def test_the_gate_hashes_the_package_that_is_running() -> None:
    assert gate.default_package_dir() == (ROOT / PKG).resolve()


def test_the_image_installs_the_project_editable_so_the_gate_hashes_the_code_that_runs() -> None:
    """The gate takes the root from ``horizon_compact.__file__``. A non-editable install would put the running
    code in site-packages, and the gate would refuse (no ``experiment/`` beside it): safe, but every official
    sweep would fail. This pins the install mode the gate relies on."""
    dockerfile = (ROOT / "infra" / "docker" / "Dockerfile").read_text(encoding="utf-8")
    assert "--no-editable" not in dockerfile
    assert "COPY src ./src" in dockerfile and "COPY experiment ./experiment" in dockerfile


def test_the_gate_and_the_command_line_load_without_the_analysis_libraries() -> None:
    """The image has no numpy, scipy or statsmodels: importing the gate (and so ``hc``) must not need them."""
    code = (
        "import sys\n"
        "class Block:\n"
        "    def find_spec(self, name, path=None, target=None):\n"
        "        if name.split('.')[0] in {'numpy', 'scipy', 'statsmodels'}:\n"
        "            raise ImportError('blocked: ' + name)\n"
        "sys.meta_path.insert(0, Block())\n"
        "import horizon_compact.protocol.gate\n"
        "import horizon_compact.cli\n"
        "print('loaded')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "loaded"


# --- the command line -------------------------------------------------------------------------------------


@pytest.fixture
def no_aws(monkeypatch: pytest.MonkeyPatch) -> None:
    def explode(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("a boto3 session was created")

    monkeypatch.setattr(boto3, "Session", explode)


@pytest.fixture
def at(tagged: Path, monkeypatch: pytest.MonkeyPatch, no_aws: None) -> Iterator[Path]:
    """The command line pointed at the synthetic tree: its package and its experiment folder."""
    monkeypatch.setattr(gate, "default_package_dir", lambda: tagged / PKG)
    monkeypatch.delenv("ECS_CONTAINER_METADATA_URI_V4", raising=False)
    yield tagged


def cli_args(root: Path, *extra: str, label: str = "grid", repeats: str = "1") -> list[str]:
    return [
        "--experiment",
        "company",
        "--model",
        MODEL,
        "--repeats",
        repeats,
        "--seed",
        "1",
        "--label",
        label,
        "--experiment-dir",
        str(root / "experiment"),
        *extra,
    ]


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_the_dry_run_passes_writes_nothing_and_calls_nothing(
    at: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    before = snapshot(at)
    assert cli.main(["sweep", "run", *cli_args(at, "--official", "--dry-run")]) == 0
    out = capsys.readouterr().out
    assert "note: not in the container (dry run)" in out
    assert "every check passes" in out
    assert snapshot(at) == before


def test_the_dry_run_refuses_a_change_with_its_message(
    at: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    append(at, DECISION)
    assert cli.main(["sweep", "run", *cli_args(at, "--official", "--dry-run")]) == 2
    assert f"{REFUSED}instrument differs from prereg-v1: {DECISION}" in capsys.readouterr().err


def test_the_dry_run_needs_official(at: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["sweep", "run", *cli_args(at, "--dry-run")]) == 2
    assert "add --official" in capsys.readouterr().err


def test_an_official_run_on_a_laptop_is_refused_before_any_aws_call(
    at: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["sweep", "run", *cli_args(at, "--official", "--profile", "p")]) == 2
    assert f"{REFUSED}official sweeps run only in the container" in capsys.readouterr().err


def test_an_official_launch_a_changed_file_refuses_never_reaches_aws(
    at: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The gate's checks 1-7 run on the laptop before any AWS call (``no_aws`` fails if one is made)."""
    append(at, VERDICT)
    args = cli_args(at, "--official", "--pilot-sweep", "p-1", "--profile", "p")
    assert cli.main(["sweep", "launch", *args]) == 2
    assert f"{REFUSED}analysis differs from prereg-v1: {VERDICT}" in capsys.readouterr().err


# --- the repeat count -------------------------------------------------------------------------------------

S1_SPREAD = [
    decision({"eliminate": 125, "move_plant_pay": 0, "move_keep_pay": 0}),
    decision({"eliminate": 0, "move_plant_pay": 0, "move_keep_pay": 125}),
]


def run_pilot(
    tagged: Path,
    store_root: Path,
    *,
    label: str = PILOT_LABEL,
    model: str = MODEL,
    templates: tuple[str, ...] = ("w1", "w3"),
) -> tuple[Experiment, LocalStore, str]:
    """A small pilot on S1 written by the runner itself, moved under a pilot prefix the reader accepts."""
    exp = load(tagged)
    pilot = plan(
        exp, model=model, label=label, templates=list(templates), scenarios=["s1"], repeats=2
    )
    store = LocalStore(store_root)
    provider = ScriptedProvider(
        lambda n, request: raw_ok(request, tool_input=S1_SPREAD[n % len(S1_SPREAD)])
    )
    session(exp, pilot, provider, store, route=SONNET_ROUTE)
    return exp, store, relocate(store, pilot)


def test_the_repeat_count_comes_from_a_finished_pilot_by_the_frozen_rule(
    tagged: Path, tmp_path: Path
) -> None:
    exp, store, prefix = run_pilot(tagged, tmp_path / "store")
    decided = required_repeats(store, prefix, exp, read_lock(tagged / lock.LOCK_RELATIVE))
    assert list(decided.repeats()) == ["s1"]
    assert 6 <= decided.repeats()["s1"] <= 20
    assert decided.model_key == MODEL and len(decided.run_ids) == 20
    record = decided.as_record()
    assert json.loads(json.dumps(record)) == record
    assert record["scenarios"][0]["kind"] == "ShareRepeats"


def _strings(value: Any) -> Iterator[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, str):
        yield value


def test_the_repeat_record_names_no_objective_and_holds_no_mean(
    tagged: Path, tmp_path: Path
) -> None:
    exp, store, prefix = run_pilot(tagged, tmp_path / "store")
    record = required_repeats(
        store, prefix, exp, read_lock(tagged / lock.LOCK_RELATIVE)
    ).as_record()
    strings = set(_strings(record))
    assert not strings & {o.id for o in exp.objectives}
    assert not [s for s in strings if "mean" in s or "difference" in s]


def _lock(tagged: Path) -> lock.Lock:
    return read_lock(tagged / lock.LOCK_RELATIVE)


def test_a_sweep_not_labeled_pilot_is_refused(tagged: Path, tmp_path: Path) -> None:
    exp, store, prefix = run_pilot(tagged, tmp_path / "store", label="trial")
    with pytest.raises(PilotRefusal, match="label is 'trial'"):
        required_repeats(store, prefix, exp, _lock(tagged))


def test_a_pilot_on_a_model_outside_the_lock_is_refused(tagged: Path, tmp_path: Path) -> None:
    exp, store, prefix = run_pilot(tagged, tmp_path / "store", model="nova-lite")
    with pytest.raises(PilotRefusal, match="'nova-lite' is not one of prereg-v1's"):
        required_repeats(store, prefix, exp, _lock(tagged))


def test_a_pilot_that_ran_the_sealed_template_is_refused(tagged: Path, tmp_path: Path) -> None:
    exp, store, prefix = run_pilot(tagged, tmp_path / "store", templates=("w1", "w2"))
    with pytest.raises(PilotRefusal, match=r"ran the sealed template \(w2\)"):
        required_repeats(store, prefix, exp, _lock(tagged))


def test_a_pilot_on_other_content_is_refused(tagged: Path, tmp_path: Path) -> None:
    exp, store, prefix = run_pilot(tagged, tmp_path / "store")
    manifest = tmp_path / "store" / prefix / "manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["content_hash"] = "0" * 64
    manifest.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(PilotRefusal, match="content hash is not prereg-v1's"):
        required_repeats(store, prefix, exp, _lock(tagged))


def test_content_in_hand_that_is_not_the_lock_s_is_refused(tagged: Path, tmp_path: Path) -> None:
    _exp, store, prefix = run_pilot(tagged, tmp_path / "store")
    append(tagged, SCENARIO, "\n")
    with pytest.raises(PilotRefusal, match="experiment given is not prereg-v1's content"):
        required_repeats(store, prefix, load(tagged), _lock(tagged))


def test_an_unfinished_pilot_is_refused(tagged: Path, tmp_path: Path) -> None:
    exp, store, prefix = run_pilot(tagged, tmp_path / "store")
    final = next((tmp_path / "store" / prefix / "runs").rglob("final.json"))
    final.unlink()
    with pytest.raises(PilotRefusal, match="1 unfinished runs"):
        required_repeats(store, prefix, exp, _lock(tagged))


def test_a_missing_manifest_is_refused(tagged: Path, tmp_path: Path) -> None:
    exp = load(tagged)
    with pytest.raises(PilotRefusal, match=r"no manifest\.json"):
        required_repeats(LocalStore(tmp_path / "empty"), "pilot-test/x/", exp, _lock(tagged))


def test_development_records_on_real_content_stay_unreadable(tagged: Path, tmp_path: Path) -> None:
    """The reader's own rule holds through the gate: a pilot left under development/ is refused."""
    exp = load(tagged)
    pilot = plan(exp, label=PILOT_LABEL, templates=["w1", "w3"], scenarios=["s1"], repeats=2)
    store = LocalStore(tmp_path / "store")
    provider = ScriptedProvider(lambda n, request: raw_ok(request, tool_input=S1_SPREAD[n % 2]))
    session(exp, pilot, provider, store, route=SONNET_ROUTE)
    with pytest.raises(PilotRefusal, match="no allocation by objective was seen"):
        required_repeats(store, f"development/company/{pilot.sweep_id}/", exp, _lock(tagged))


# --- Phase 4 code half, sections 4.3 and 4.4: the pilot path and the official launch ------------------------

PILOT_ID = "pilot-company-0000"


def counts(exp: Experiment, n: int = 1) -> dict[str, int]:
    return dict.fromkeys(exp.scenarios, n)


def fake_decision(
    exp: Experiment,
    by_scenario: dict[str, int],
    *,
    pilot_id: str = PILOT_ID,
    model: str = MODEL,
    content_hash: str | None = None,
) -> RepeatDecision:
    scenarios = tuple(
        ShareRepeats(sid, 0.12, 40, 9, 14, n, False, None)
        if sid in ("s1", "s2")
        else ChoiceRepeats(sid, n, 0.1, 0.05)
        for sid, n in by_scenario.items()
    )
    return RepeatDecision(
        protocol="prereg-v1",
        pilot_sweep_id=pilot_id,
        model_key=model,
        content_hash=content_hash or exp.content_hash,
        run_ids=("r-0",),
        scenarios=scenarios,
    )


def pilot_prefix(exp: Experiment, pilot_id: str = PILOT_ID) -> str:
    return sweep_prefix(exp.name, pilot_id, "pilot")


def test_repeats_json_is_written_once_beside_the_pilot_and_never_replaced(tmp_path: Path) -> None:
    exp = load(ROOT)
    store = LocalStore(tmp_path)
    decided = fake_decision(exp, counts(exp, 7))
    key = write_repeats(store, pilot_prefix(exp), decided)
    assert key == f"pilot/{exp.name}/{PILOT_ID}/repeats.json" == repeats_key(pilot_prefix(exp))
    first = store.get(key)
    assert first is not None and json.loads(first) == decided.as_record()
    with pytest.raises(PilotRefusal, match="already exists"):
        write_repeats(store, pilot_prefix(exp), fake_decision(exp, counts(exp, 9)))
    assert store.get(key) == first


def test_a_second_pilot_on_the_same_model_cannot_write_its_repeats(tmp_path: Path) -> None:
    """Protocol 13.2, one study per protocol version (OPEN entry 2026-10-10). Another model is fine."""
    exp = load(ROOT)
    store = LocalStore(tmp_path)
    write_repeats(store, pilot_prefix(exp), fake_decision(exp, counts(exp, 7)))
    second = fake_decision(exp, counts(exp, 9), pilot_id="pilot-company-1111")
    with pytest.raises(PilotRefusal, match="already has its repeats from another pilot"):
        write_repeats(store, pilot_prefix(exp, "pilot-company-1111"), second)
    assert store.get(repeats_key(pilot_prefix(exp, "pilot-company-1111"))) is None
    other_model = fake_decision(
        exp, counts(exp, 9), pilot_id="pilot-company-2222", model="nova-lite"
    )
    write_repeats(store, pilot_prefix(exp, "pilot-company-2222"), other_model)


def test_an_official_sweep_refuses_when_its_model_has_two_pilots_counts(tmp_path: Path) -> None:
    """Belt and braces: a second file placed by hand still stops the official sweep."""
    exp = load(ROOT)
    store = LocalStore(tmp_path)
    write_repeats(store, pilot_prefix(exp), fake_decision(exp, counts(exp, 7)))
    stray = fake_decision(exp, counts(exp, 9), pilot_id="pilot-company-1111")
    store.put_new(
        repeats_key(pilot_prefix(exp, "pilot-company-1111")), json.dumps(stray.as_record())
    )
    with pytest.raises(SweepRefusal, match="more than one pilot"):
        check_repeats(store, plan(exp, repeats=7), PILOT_ID)


def test_the_plan_must_equal_the_pilots_repeats_scenario_by_scenario(tmp_path: Path) -> None:
    exp = load(ROOT)
    store = LocalStore(tmp_path)
    the_plan = plan(exp, repeats=7)
    write_repeats(store, pilot_prefix(exp), fake_decision(exp, counts(exp, 7)))
    check_repeats(store, the_plan, PILOT_ID)  # equal: nothing raised
    store = LocalStore(tmp_path / "other")
    write_repeats(store, pilot_prefix(exp), fake_decision(exp, {**counts(exp, 7), "s3": 20}))
    with pytest.raises(SweepRefusal) as raised:
        check_repeats(store, the_plan, PILOT_ID)
    message = str(raised.value)
    assert "scenario s3: the pilot sets 20 repeats, the plan has 7" in message
    assert (
        "scenario s1" not in message and "scenario s2" not in message
    )  # only the one that differs


def test_a_missing_or_foreign_repeats_file_is_refused(tmp_path: Path) -> None:
    exp = load(ROOT)
    the_plan = plan(exp, repeats=3)
    with pytest.raises(SweepRefusal, match=r"no pilot/company/pilot-company-0000/repeats\.json"):
        check_repeats(LocalStore(tmp_path / "empty"), the_plan, PILOT_ID)
    for name, decided, needle in (
        (
            "model",
            fake_decision(exp, counts(exp, 3), model="nova-lite"),
            "the pilot ran 'nova-lite'",
        ),
        ("content", fake_decision(exp, counts(exp, 3), content_hash="0" * 64), "different content"),
        (
            "id",
            fake_decision(exp, counts(exp, 3), pilot_id="pilot-other"),
            "is for pilot 'pilot-other'",
        ),
    ):
        store = LocalStore(tmp_path / name)
        write_repeats(store, pilot_prefix(exp), decided)
        with pytest.raises(SweepRefusal, match=needle):
            check_repeats(store, the_plan, PILOT_ID)


def test_a_repeats_file_that_leaves_out_or_adds_a_scenario_is_refused(tmp_path: Path) -> None:
    exp = load(ROOT)
    the_plan = plan(exp, repeats=3)
    short = {sid: n for sid, n in counts(exp, 3).items() if sid != "s2"}
    store = LocalStore(tmp_path / "short")
    write_repeats(store, pilot_prefix(exp), fake_decision(exp, short))
    with pytest.raises(SweepRefusal, match="scenario s2: the pilot sets None repeats"):
        check_repeats(store, the_plan, PILOT_ID)
    store = LocalStore(tmp_path / "extra")
    write_repeats(store, pilot_prefix(exp), fake_decision(exp, {**counts(exp, 3), "s9": 3}))
    with pytest.raises(SweepRefusal, match=r"scenario\(s\) \['s9'\]"):
        check_repeats(store, the_plan, PILOT_ID)


def test_the_printout_names_the_rule_that_set_each_count_and_nothing_directional() -> None:
    def lines_for(*results: ShareRepeats | ChoiceRepeats) -> str:
        decided = RepeatDecision("prereg-v1", "pilot-x", MODEL, "h", ("r-0",), tuple(results))
        return "\n".join(describe_decision(decided))

    assert "set by the cap, 20; half-width at the cap 0.0830" in lines_for(
        ShareRepeats("s1", 0.15, 60, 11, 22, 20, True, 0.083)
    )
    assert "set by the floor, 6" in lines_for(ShareRepeats("s1", 0.02, 60, 3, 4, 6, False, None))
    assert "set by rule (b), both verdicts reachable" in lines_for(
        ShareRepeats("s1", 0.1, 60, 6, 10, 10, False, None)
    )
    assert "set by rule (a), power" in lines_for(
        ShareRepeats("s1", 0.1, 60, 14, 9, 14, False, None)
    )
    text = lines_for(
        ShareRepeats("s1", 0.1, 60, 6, 10, 10, False, None), ChoiceRepeats("s3", 20, 0.1, 0.05)
    )
    assert "pooled spread 0.1000 on 60 degrees of freedom" in text
    assert "s3: repeats 20, the cap (a pilot cannot measure a choice rate)" in text
    assert "mean" not in text and "objective" not in text


class Reached(Exception):
    """Raised by the stand-in for ``run_session``: the command got as far as starting a session."""

    def __init__(self, kwargs: dict[str, Any]) -> None:
        super().__init__("a session was started")
        self.kwargs = kwargs


@pytest.fixture
def in_container(at: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> LocalStore:
    """``hc sweep run`` as the task runs it: in the container, with a local folder for a store."""
    store = LocalStore(tmp_path / "bucket")

    def stop_here(**kwargs: Any) -> None:
        raise Reached(kwargs)

    monkeypatch.setattr(cli, "identify", lambda env, git: FARGATE)
    monkeypatch.setattr(cli, "check_route", lambda *a, **k: None)
    monkeypatch.setattr(cli, "_connect", lambda *a, **k: (object(), object(), store, "0" * 12))
    monkeypatch.setattr(cli, "run_session", stop_here)
    return store


CAPS = ("--cap-usd", "25", "--allow-over-cap")  # sixty runs cost more than the $5 development cap


def official_run(at: Path, *extra: str) -> list[str]:
    return ["sweep", "run", *cli_args(at, "--official", *extra, *CAPS)]


def test_an_official_run_needs_the_pilot_it_must_match(
    at: Path, in_container: LocalStore, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(official_run(at)) == 2
    assert "needs --pilot-sweep" in capsys.readouterr().err
    args = cli_args(
        at, "--pilot", "--pilot-sweep", PILOT_ID, "--template", "w1", *CAPS, label="pilot"
    )
    assert cli.main(["sweep", "run", *args]) == 2
    assert "--pilot-sweep goes with --official" in capsys.readouterr().err


def test_an_official_run_without_the_pilots_repeats_is_refused_before_a_session(
    at: Path, in_container: LocalStore, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(official_run(at, "--pilot-sweep", PILOT_ID)) == 2
    assert f"pilot/company/{PILOT_ID}/repeats.json" in capsys.readouterr().err


def test_an_official_run_whose_repeats_differ_in_one_scenario_is_refused(
    at: Path, in_container: LocalStore, capsys: pytest.CaptureFixture[str]
) -> None:
    exp = load(at)
    write_repeats(in_container, pilot_prefix(exp), fake_decision(exp, {**counts(exp), "s4": 12}))
    assert cli.main(official_run(at, "--pilot-sweep", PILOT_ID)) == 2
    assert "scenario s4: the pilot sets 12 repeats, the plan has 1" in capsys.readouterr().err


def test_an_official_run_that_matches_starts_a_session_under_the_official_role(
    at: Path, in_container: LocalStore
) -> None:
    exp = load(at)
    write_repeats(in_container, pilot_prefix(exp), fake_decision(exp, counts(exp)))
    with pytest.raises(Reached) as reached:
        cli.main(official_run(at, "--pilot-sweep", PILOT_ID))
    assert reached.value.kwargs["role"] == "official"


def test_a_pilot_run_starts_under_the_pilot_role_and_needs_no_repeats_file(
    at: Path, in_container: LocalStore
) -> None:
    args = cli_args(
        at, "--pilot", "--template", "w1", "--template", "w3", *CAPS, label=PILOT_LABEL, repeats="2"
    )
    with pytest.raises(Reached) as reached:
        cli.main(["sweep", "run", *args])
    assert reached.value.kwargs["role"] == "pilot"


def test_a_pilot_not_labeled_pilot_or_with_the_sealed_template_is_refused(
    at: Path, in_container: LocalStore, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["sweep", "run", *cli_args(at, "--pilot", "--template", "w1", *CAPS)]) == 2
    assert f"a pilot is labeled {PILOT_LABEL!r}, not 'grid'" in capsys.readouterr().err
    args = cli_args(at, "--pilot", "--template", "w1", "--template", "w2", *CAPS, label=PILOT_LABEL)
    assert cli.main(["sweep", "run", *args]) == 2
    assert "a pilot never runs the sealed template (w2)" in capsys.readouterr().err


def test_official_and_pilot_together_are_an_argument_error(at: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["sweep", "run", *cli_args(at, "--official", "--pilot")])
    assert exc.value.code == 2


def test_the_dry_run_takes_a_pilot_and_checks_it_the_pilot_way(
    at: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ok = cli_args(
        at,
        "--pilot",
        "--dry-run",
        "--template",
        "w1",
        "--template",
        "w3",
        label="pilot",
        repeats="2",
    )
    assert cli.main(["sweep", "run", *ok]) == 0
    assert "pilot: every check passes" in capsys.readouterr().out
    assert (
        cli.main(["sweep", "run", *cli_args(at, "--pilot", "--dry-run", "--template", "w1")]) == 2
    )
    assert "a pilot is labeled" in capsys.readouterr().err


class Launcher:
    """Stands in for the AWS session and the one call that starts a task; keeps the command it was given."""

    def __init__(self) -> None:
        self.command: list[str] = []

    def client(self, name: str) -> object:
        return object()

    def launch_task(self, ecs: object, ec2: object, *, model_key: str, command: list[str]) -> str:
        self.command = command
        return "arn:aws:ecs:us-east-1:000000000000:task/horizon-compact/abc123"


@pytest.fixture
def launcher(at: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Launcher:
    """``hc sweep launch`` on the laptop with no AWS: the session and the bucket are stand-ins."""
    stand_in = Launcher()
    store = LocalStore(tmp_path / "bucket")
    monkeypatch.setattr(cli, "_session", lambda args, identity: stand_in)
    monkeypatch.setattr(cli, "_store", lambda args, session: store)
    monkeypatch.setattr(sweep_launch, "launch_task", stand_in.launch_task)
    stand_in.store = store  # type: ignore[attr-defined]
    return stand_in


WORST_CASE = (
    "--profile",
    "p",
    "--cap-usd",
    "25",
    "--allow-over-cap",
)  # sixty runs cost more than $5


def launch(at: Path, *extra: str, label: str = "grid", repeats: str = "1") -> int:
    return cli.main(
        ["sweep", "launch", *cli_args(at, *extra, *WORST_CASE, label=label, repeats=repeats)]
    )


def test_an_official_launch_forwards_official_and_the_pilot_to_the_task(
    at: Path, launcher: Launcher
) -> None:
    exp = load(at)
    write_repeats(launcher.store, pilot_prefix(exp), fake_decision(exp, counts(exp)))  # type: ignore[attr-defined]
    assert launch(at, "--official", "--pilot-sweep", PILOT_ID) == 0
    command = launcher.command
    assert "--official" in command  # the test that fails if it is dropped
    assert command[command.index("--pilot-sweep") + 1] == PILOT_ID
    assert "--pilot" not in command
    assert command[command.index("--repeats") + 1] == "1"


def test_an_official_launch_refuses_repeats_that_differ_from_the_pilots(
    at: Path, launcher: Launcher, capsys: pytest.CaptureFixture[str]
) -> None:
    exp = load(at)
    write_repeats(
        launcher.store,  # type: ignore[attr-defined]
        pilot_prefix(exp),
        fake_decision(exp, {**counts(exp), "s2": 15}),
    )
    assert launch(at, "--official", "--pilot-sweep", PILOT_ID) == 2
    assert "scenario s2: the pilot sets 15 repeats, the plan has 1" in capsys.readouterr().err
    assert launcher.command == []  # nothing was started


def test_an_official_launch_with_no_repeats_file_or_no_pilot_named_starts_nothing(
    at: Path, launcher: Launcher, capsys: pytest.CaptureFixture[str]
) -> None:
    assert launch(at, "--official", "--pilot-sweep", PILOT_ID) == 2
    assert "repeats.json" in capsys.readouterr().err
    assert launch(at, "--official") == 2
    assert "needs --pilot-sweep" in capsys.readouterr().err
    assert launcher.command == []


def test_a_pilot_launch_forwards_pilot_and_nothing_official(at: Path, launcher: Launcher) -> None:
    pilot = ("--pilot", "--template", "w1", "--template", "w3")
    assert launch(at, *pilot, label=PILOT_LABEL, repeats="2") == 0
    assert "--pilot" in launcher.command
    assert "--official" not in launcher.command and "--pilot-sweep" not in launcher.command


def test_a_pilot_launch_not_labeled_pilot_is_refused_on_the_laptop(
    at: Path, launcher: Launcher, capsys: pytest.CaptureFixture[str]
) -> None:
    assert launch(at, "--pilot", "--template", "w1", "--template", "w3") == 2
    assert "a pilot is labeled" in capsys.readouterr().err
    assert launcher.command == []


# --- hc protocol repeats ----------------------------------------------------------------------------------


def run_pilot_in_place(tagged: Path, bucket: Path) -> tuple[Experiment, LocalStore, str]:
    """A small pilot on S1 written by the runner itself under ``pilot/``, where the command reads it."""
    exp = load(tagged)
    pilot = plan(exp, label=PILOT_LABEL, templates=["w1", "w3"], scenarios=["s1"], repeats=2)
    store = LocalStore(bucket)
    provider = ScriptedProvider(
        lambda n, request: raw_ok(request, tool_input=S1_SPREAD[n % len(S1_SPREAD)])
    )
    session(exp, pilot, provider, store, route=SONNET_ROUTE, role="pilot")
    return exp, store, pilot.sweep_id


def repeats_command(tagged: Path, sweep_id: str) -> list[str]:
    return ["protocol", "--root", str(tagged), "repeats", "--pilot", sweep_id, "--store", "local"]


@pytest.fixture
def scratch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """The local store's folder, so ``--store local`` never touches this repository's own scratch/."""
    top = tmp_path / "top"
    monkeypatch.setattr(cli, "_git", lambda *a: str(top))
    return top / "scratch" / "runs"


def test_hc_protocol_repeats_writes_the_count_once_and_prints_only_what_the_record_holds(
    tagged: Path, scratch: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exp, _store, sweep_id = run_pilot_in_place(tagged, scratch)
    assert cli.main(repeats_command(tagged, sweep_id)) == 0
    out = capsys.readouterr().out
    key = f"pilot/company/{sweep_id}/repeats.json"
    assert f"written: {key}" in out
    assert "s1: pooled spread" in out and "repeats" in out and "set by" in out
    assert not {o.id for o in exp.objectives} & set(out.replace(":", " ").replace(",", " ").split())
    assert "mean" not in out
    written = (scratch / key).read_text(encoding="utf-8")
    assert json.loads(written)["pilot_sweep_id"] == sweep_id
    assert cli.main(repeats_command(tagged, sweep_id)) == 2  # written once: a second run is refused
    assert "already exists" in capsys.readouterr().err
    assert (scratch / key).read_text(encoding="utf-8") == written


def test_hc_protocol_repeats_refuses_an_unfinished_pilot_and_writes_nothing(
    tagged: Path, scratch: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _exp, _store, sweep_id = run_pilot_in_place(tagged, scratch)
    next((scratch / f"pilot/company/{sweep_id}/runs").rglob("final.json")).unlink()
    assert cli.main(repeats_command(tagged, sweep_id)) == 2
    assert "unfinished runs" in capsys.readouterr().err
    assert not (scratch / f"pilot/company/{sweep_id}/repeats.json").exists()


def test_hc_protocol_repeats_refuses_a_sweep_that_is_not_there_and_a_missing_lock(
    tagged: Path, scratch: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(repeats_command(tagged, "pilot-company-nope")) == 2
    assert "no manifest.json" in capsys.readouterr().err
    (tagged / lock.LOCK_RELATIVE).unlink()
    assert cli.main(repeats_command(tagged, "pilot-company-nope")) == 2
    assert "refused:" in capsys.readouterr().err
