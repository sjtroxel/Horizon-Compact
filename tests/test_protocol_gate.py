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
from horizon_compact.experiment import Experiment, load_experiment
from horizon_compact.protocol import gate, lock
from horizon_compact.protocol.gate import (
    PILOT_LABEL,
    PilotRefusal,
    check_official,
    required_repeats,
    run_gate,
)
from horizon_compact.protocol.lock import LINE_ENDING_NOTE, read_lock, write_lock
from horizon_compact.sweep.plan import SweepPlan, SweepRefusal, build_plan
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
    pilot = plan(exp, label=PILOT_LABEL)
    assert failures(tagged, exp, the_plan=pilot, pilot=True) == (
        "a pilot never runs the sealed template (w2): the development wordings only",
    )


def test_a_pilot_with_another_label_is_refused(tagged: Path) -> None:
    exp = load(tagged)
    pilot = plan(exp, label="trial", templates=["w1", "w3"])
    assert failures(tagged, exp, the_plan=pilot, pilot=True) == (
        "a pilot is labeled 'pilot', not 'trial'",
    )


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


def cli_args(root: Path, *extra: str, label: str = "grid") -> list[str]:
    return [
        "--experiment",
        "company",
        "--model",
        MODEL,
        "--repeats",
        "1",
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


def test_an_official_launch_runs_the_checks_then_says_it_is_not_wired_yet(
    at: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["sweep", "launch", *cli_args(at, "--official", "--profile", "p")]) == 2
    assert "not wired yet" in capsys.readouterr().err
    append(at, VERDICT)
    assert cli.main(["sweep", "launch", *cli_args(at, "--official", "--profile", "p")]) == 2
    err = capsys.readouterr().err
    assert f"{REFUSED}analysis differs from prereg-v1: {VERDICT}" in err
    assert "not wired yet" not in err


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
