"""The pre-registration lock: write it, read it, check a tree against it (Phase 3.5 IMPLEMENTATION doc
sections 5-6, build step 4).

Every case runs on a synthetic tree: a small fake package (one file in each set), a copy of the placeholder
experiment and the real ``models.toml``, and fake record-only sources. The real repository is touched only to
show that ``check`` passes there today.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tomllib
from pathlib import Path
from typing import Any

import pytest

from horizon_compact import cli
from horizon_compact.protocol import lock
from horizon_compact.protocol.lock import (
    LockError,
    build_lock,
    check_lock,
    dumps,
    lock_path,
    read_lock,
    render_lock,
    write_lock,
)

ROOT = Path(__file__).resolve().parents[1]
PKG = "src/horizon_compact"
EXPERIMENT = "placeholder"
MODEL = "sonnet-4-6"

PACKAGE_FILES = (
    f"{PKG}/__init__.py",
    f"{PKG}/experiment.py",
    f"{PKG}/model_config.py",
    f"{PKG}/sweep/prompt.py",
    f"{PKG}/sweep/decision.py",
    f"{PKG}/sweep/classify.py",
    f"{PKG}/sweep/runner.py",
    f"{PKG}/analysis/__init__.py",
    f"{PKG}/analysis/verdict.py",
    f"{PKG}/analysis/matcher_thresholds.toml",
)
DECISION = f"{PKG}/sweep/decision.py"
VERDICT = f"{PKG}/analysis/verdict.py"
DOCUMENT = "experiment/protocol/protocol-v1.md"
ERRATA = "experiment/protocol/errata-v1.md"
MODELS = "experiment/models.toml"


def write(root: Path, path: str, text: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")


def append(root: Path, path: str, text: str = "\n# changed\n") -> None:
    target = root / path
    target.write_text(target.read_text(encoding="utf-8") + text, encoding="utf-8", newline="\n")


def git(*args: str, cwd: Path) -> None:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True, env=env)


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """A repository-shaped directory that is ready to lock, with no lock written."""
    root = tmp_path / "repo"
    for path in PACKAGE_FILES:
        write(root, path, f"# {path}\n")
    shutil.copytree(ROOT / "experiment" / EXPERIMENT, root / "experiment" / EXPERIMENT)
    shutil.copy(ROOT / MODELS, root / MODELS)
    write(root, f"experiment/{EXPERIMENT}/sources.toml", "# a record file the model never reads\n")
    write(root, DOCUMENT, "# the protocol, as written\n")
    write(root, "uv.lock", "# the library lock\n")
    write(root, lock.SIMULATION_RELATIVE, '{"code_sha256": "abc123", "results_version": 2}\n')
    return root


def make_lock(root: Path, models: tuple[str, ...] = (MODEL,)) -> None:
    write_lock(root, models, experiment=EXPERIMENT)


@pytest.fixture
def locked(tree: Path) -> Path:
    make_lock(tree)
    return tree


def failures(root: Path) -> tuple[str, ...]:
    return check_lock(root).failures


def refusal(root: Path, models: tuple[str, ...] = (MODEL,)) -> str:
    with pytest.raises(LockError) as caught:
        build_lock(root, models, experiment=EXPERIMENT)
    return str(caught.value)


# --- check: no lock, a fresh lock ---------------------------------------------------------------------------


def test_with_no_lock_the_check_passes_and_says_so(tree: Path) -> None:
    report = check_lock(tree)
    assert report.ok
    assert "no lock exists yet" in report.notes[0]


def test_the_real_repository_passes_the_check_today() -> None:
    assert check_lock(ROOT).ok


def test_a_fresh_lock_passes_with_no_notes(locked: Path) -> None:
    report = check_lock(locked)
    assert report.ok
    assert report.notes == ()


# --- check: frozen code -------------------------------------------------------------------------------------


def test_one_byte_in_an_instrument_file_fails_naming_it(locked: Path) -> None:
    append(locked, DECISION)
    assert failures(locked) == (f"instrument differs from prereg-v1: {DECISION}",)


def test_one_byte_in_an_analysis_file_fails_naming_it(locked: Path) -> None:
    append(locked, VERDICT)
    assert failures(locked) == (f"analysis differs from prereg-v1: {VERDICT}",)


def test_the_loader_is_in_the_analysis_set(locked: Path) -> None:
    append(locked, f"{PKG}/experiment.py")
    assert failures(locked) == (f"analysis differs from prereg-v1: {PKG}/experiment.py",)


def test_a_file_added_to_analysis_fails_naming_it(locked: Path) -> None:
    write(locked, f"{PKG}/analysis/extra.py", "x = 1\n")
    assert failures(locked) == (
        f"analysis differs from prereg-v1: {PKG}/analysis/extra.py (added)",
    )


def test_a_deleted_frozen_file_fails_naming_it(locked: Path) -> None:
    (locked / DECISION).unlink()
    assert failures(locked) == (f"instrument differs from prereg-v1: {DECISION} (missing)",)


def test_a_run_file_may_change_freely(locked: Path) -> None:
    append(locked, f"{PKG}/sweep/runner.py")
    append(locked, f"{PKG}/model_config.py")
    write(locked, f"{PKG}/sweep/new_run_module.py", "x = 1\n")
    assert check_lock(locked).ok


def test_every_failure_is_reported_not_only_the_first(locked: Path) -> None:
    append(locked, DECISION)
    append(locked, VERDICT)
    append(locked, DOCUMENT)
    append(locked, f"experiment/{EXPERIMENT}/dossier.toml")
    assert failures(locked) == (
        f"document differs from prereg-v1: {DOCUMENT}",
        f"content differs from prereg-v1: {EXPERIMENT}/dossier.toml",
        f"instrument differs from prereg-v1: {DECISION}",
        f"analysis differs from prereg-v1: {VERDICT}",
    )


def test_a_hash_failure_adds_the_line_ending_note_and_others_do_not(locked: Path) -> None:
    append(locked, DECISION)
    assert "core.autocrlf" in check_lock(locked).notes[0]


def test_a_git_checkout_hashes_tracked_files_only(locked: Path) -> None:
    git("init", "-q", "-b", "main", cwd=locked)
    git("add", "--", PKG, cwd=locked)
    write(locked, f"{PKG}/analysis/scratch.py", "x = 1\n")
    assert check_lock(locked).ok
    git("add", "--", f"{PKG}/analysis/scratch.py", cwd=locked)
    assert failures(locked) == (
        f"analysis differs from prereg-v1: {PKG}/analysis/scratch.py (added)",
    )


# --- check: document, content, sealed template -------------------------------------------------------------


def test_a_changed_document_fails(locked: Path) -> None:
    append(locked, DOCUMENT)
    assert failures(locked) == (f"document differs from prereg-v1: {DOCUMENT}",)


def test_a_missing_document_fails(locked: Path) -> None:
    (locked / DOCUMENT).unlink()
    assert failures(locked) == (f"document differs from prereg-v1: {DOCUMENT} (missing)",)


def test_a_changed_content_file_fails_naming_it(locked: Path) -> None:
    append(locked, f"experiment/{EXPERIMENT}/dossier.toml")
    assert failures(locked) == (f"content differs from prereg-v1: {EXPERIMENT}/dossier.toml",)


def test_a_changed_scenario_fails_naming_it(locked: Path) -> None:
    append(locked, f"experiment/{EXPERIMENT}/scenarios/garden.toml")
    assert failures(locked) == (
        f"content differs from prereg-v1: {EXPERIMENT}/scenarios/garden.toml",
    )


def test_a_content_file_that_no_longer_loads_fails(locked: Path) -> None:
    write(locked, f"experiment/{EXPERIMENT}/dossier.toml", "this is = = not toml\n")
    [line] = failures(locked)
    assert line.startswith(f"content: experiment '{EXPERIMENT}' does not load")


def test_a_changed_sealed_template_is_reported_by_name(locked: Path) -> None:
    path = locked / f"experiment/{EXPERIMENT}/objectives.toml"
    text = path.read_text(encoding="utf-8")
    path.write_text('sealed_template = "w1"\n' + text, encoding="utf-8", newline="\n")
    assert "sealed template differs from prereg-v1: now 'w1', locked None" in failures(locked)


def test_a_sealed_template_is_recorded_when_there_is_one(tree: Path) -> None:
    path = tree / f"experiment/{EXPERIMENT}/objectives.toml"
    path.write_text(
        'sealed_template = "w1"\n' + path.read_text(encoding="utf-8"),
        encoding="utf-8",
        newline="\n",
    )
    make_lock(tree)
    assert read_lock(lock_path(tree)).content.sealed_template == "w1"
    assert check_lock(tree).ok


def test_the_errata_file_is_never_hashed(tree: Path) -> None:
    write(tree, ERRATA, "# first entry\n")
    make_lock(tree)
    append(tree, ERRATA)
    (tree / ERRATA).unlink()
    assert check_lock(tree).ok


def test_record_only_fields_are_never_compared(locked: Path) -> None:
    append(locked, "uv.lock")
    append(locked, lock.SIMULATION_RELATIVE)
    append(locked, f"experiment/{EXPERIMENT}/sources.toml")
    assert check_lock(locked).ok


# --- check: models ------------------------------------------------------------------------------------------


def edit_models(root: Path, old: str, new: str) -> None:
    path = root / MODELS
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


def test_a_changed_model_id_fails(locked: Path) -> None:
    edit_models(locked, 'model_id = "anthropic.claude-sonnet-4-6"', 'model_id = "anthropic.other"')
    assert failures(locked) == (
        "model sonnet-4-6 differs from prereg-v1: model_id is 'anthropic.other', "
        "locked 'anthropic.claude-sonnet-4-6'",
    )


def test_a_changed_inference_profile_fails(locked: Path) -> None:
    edit_models(
        locked, 'inference_profile = "horizon-compact-sonnet-4-6"', 'inference_profile = "x"'
    )
    assert failures(locked) == (
        "model sonnet-4-6 differs from prereg-v1: inference_profile is 'x', "
        "locked 'horizon-compact-sonnet-4-6'",
    )


def test_a_changed_route_fails(locked: Path) -> None:
    edit_models(locked, 'route = "application_profile"', 'route = "geo_profile"')
    assert any("route is 'geo_profile'" in line for line in failures(locked))


def test_a_changed_price_quota_or_pace_passes(locked: Path) -> None:
    edit_models(locked, "input = 3.30", "input = 9.99")
    edit_models(locked, "requests_per_minute = 10", "requests_per_minute = 3")
    edit_models(locked, "pace_fraction = 0.8", "pace_fraction = 0.5")
    assert check_lock(locked).ok


def test_a_locked_model_missing_from_models_toml_fails(locked: Path) -> None:
    edit_models(locked, "[models.sonnet-4-6]", "[models.renamed]")
    edit_models(locked, "[models.sonnet-4-6.prices]", "[models.renamed.prices]")
    assert "model sonnet-4-6 is in prereg-v1 but not in models.toml" in failures(locked)


def test_an_unlocked_model_may_change_freely(locked: Path) -> None:
    edit_models(locked, 'model_id = "amazon.nova-lite-v1:0"', 'model_id = "amazon.other"')
    assert check_lock(locked).ok


# --- the lock's contents ------------------------------------------------------------------------------------


def test_the_lock_holds_identity_only_never_prices_quotas_or_pace(locked: Path) -> None:
    text = lock_path(locked).read_text(encoding="utf-8")
    for word in ("price", "requests_per_minute", "pace", "input =", "cache_read"):
        assert word not in text
    assert read_lock(lock_path(locked)).models[MODEL].model_dump(exclude_none=True) == {
        "model_id": "anthropic.claude-sonnet-4-6",
        "route": "application_profile",
        "role": "main",
        "thinking": "not set",
        "sampling": "not set",
        "inference_profile": "horizon-compact-sonnet-4-6",
        "geo_profile_id": "us.anthropic.claude-sonnet-4-6",
        "region": "us-east-1",
    }


def test_a_route_without_a_region_or_profile_records_neither(tree: Path) -> None:
    make_lock(tree, ("nova-lite", "qwen-local"))
    models = read_lock(lock_path(tree)).models
    assert models["nova-lite"].region == "us-east-1"
    assert models["nova-lite"].inference_profile is None
    assert models["qwen-local"].region is None
    assert models["qwen-local"].geo_profile_id is None
    assert check_lock(tree).ok


def test_the_lock_records_the_sets_and_the_record_only_fields(locked: Path) -> None:
    record = read_lock(lock_path(locked))
    assert (record.lock_version, record.protocol, record.document) == (1, "prereg-v1", DOCUMENT)
    assert sorted(record.instrument.files) == [
        f"{PKG}/sweep/classify.py",
        f"{PKG}/sweep/decision.py",
        f"{PKG}/sweep/prompt.py",
    ]
    assert f"{PKG}/experiment.py" in record.analysis.files
    assert record.analysis.results_version == 2
    assert record.simulation.code_sha256 == "abc123"
    assert record.content.experiment == EXPERIMENT
    assert f"{EXPERIMENT}/dossier.toml" in record.content.files
    assert "models.toml" not in record.content.files
    assert len(record.content.tree_sha256) == 64


def test_the_tree_record_leaves_out_untracked_files_so_a_clean_clone_reproduces_it(
    tree: Path,
) -> None:
    git("init", "-q", "-b", "main", cwd=tree)
    git("add", "-A", cwd=tree)
    clean = build_lock(tree, (MODEL,), experiment=EXPERIMENT)["content"]["tree_sha256"]
    write(tree, f"experiment/{EXPERIMENT}/scratch-notes.md", "untracked\n")
    assert build_lock(tree, (MODEL,), experiment=EXPERIMENT)["content"]["tree_sha256"] == clean
    git("add", "-A", cwd=tree)
    assert build_lock(tree, (MODEL,), experiment=EXPERIMENT)["content"]["tree_sha256"] != clean


def test_the_same_tree_gives_the_same_bytes(tree: Path) -> None:
    first = render_lock(tree, (MODEL,), experiment=EXPERIMENT)
    assert render_lock(tree, (MODEL,), experiment=EXPERIMENT) == first
    assert first.endswith("\n") and "\r" not in first


def test_naming_a_model_twice_records_it_once(tree: Path) -> None:
    assert list(build_lock(tree, (MODEL, MODEL), experiment=EXPERIMENT)["models"]) == [MODEL]


# --- the writer's refusals ----------------------------------------------------------------------------------


def test_the_writer_refuses_without_the_protocol_document(tree: Path) -> None:
    (tree / DOCUMENT).unlink()
    assert f"the protocol document {DOCUMENT} does not exist" in refusal(tree)


def test_the_writer_refuses_when_a_frozen_pattern_matches_nothing(tree: Path) -> None:
    (tree / f"{PKG}/sweep/classify.py").unlink()
    assert f"frozen pattern {PKG}/sweep/classify.py matches no file" in refusal(tree)


def test_the_writer_refuses_a_model_not_in_models_toml(tree: Path) -> None:
    message = refusal(tree, ("no-such-model",))
    assert "model 'no-such-model' is not in models.toml" in message
    assert "sonnet-4-6" in message


def test_the_writer_refuses_when_no_model_is_named(tree: Path) -> None:
    assert "no official model named" in refusal(tree, ())


def test_the_writer_refuses_to_replace_a_lock_and_leaves_it_untouched(locked: Path) -> None:
    before = lock_path(locked).read_bytes()
    with pytest.raises(LockError, match="already exists"):
        write_lock(locked, (MODEL,), experiment=EXPERIMENT)
    assert lock_path(locked).read_bytes() == before


def test_building_the_lock_refuses_too_when_one_exists_so_the_printed_form_cannot_mislead(
    locked: Path,
) -> None:
    assert "prereg.lock already exists" in refusal(locked)


def test_the_writer_never_replaces_a_lock_even_if_one_appears_after_the_build(
    tree: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real = lock.render_lock

    def render_then_race(*args: Any, **kwargs: Any) -> str:
        text = real(*args, **kwargs)
        write(tree, lock.LOCK_RELATIVE, "# someone else's lock\n")
        return text

    monkeypatch.setattr(lock, "render_lock", render_then_race)
    with pytest.raises(LockError, match="already exists"):
        write_lock(tree, (MODEL,), experiment=EXPERIMENT)
    assert lock_path(tree).read_text(encoding="utf-8") == "# someone else's lock\n"


def test_the_writer_names_every_cause_at_once(tree: Path) -> None:
    (tree / DOCUMENT).unlink()
    (tree / "uv.lock").unlink()
    (tree / lock.SIMULATION_RELATIVE).unlink()
    message = refusal(tree, ("nope",))
    for part in ("protocol document", "uv.lock does not exist", "simulation results", "'nope'"):
        assert part in message


def test_a_failed_write_leaves_no_lock_behind(tree: Path) -> None:
    (tree / DOCUMENT).unlink()
    with pytest.raises(LockError):
        write_lock(tree, (MODEL,), experiment=EXPERIMENT)
    assert not lock_path(tree).exists()


# --- reading a bad lock -------------------------------------------------------------------------------------


def test_a_lock_that_is_not_toml_fails_the_check(locked: Path) -> None:
    lock_path(locked).write_text("this = = broken\n", encoding="utf-8")
    [line] = failures(locked)
    assert "is not valid TOML" in line


def test_an_unknown_lock_version_fails_the_check(locked: Path) -> None:
    path = lock_path(locked)
    path.write_text(
        path.read_text(encoding="utf-8").replace("lock_version = 1", "lock_version = 2")
    )
    assert failures(locked) == ("prereg.lock has lock_version 2; this reader knows 1",)


def test_a_set_hash_that_disagrees_with_its_file_hashes_fails_the_check(locked: Path) -> None:
    path = lock_path(locked)
    record = read_lock(path)
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace(record.instrument.sha256, "0" * 64), encoding="utf-8")
    assert failures(locked) == ("instrument set hash differs from prereg-v1",)


def test_a_lock_missing_a_field_or_with_an_extra_one_fails_the_check(locked: Path) -> None:
    path = lock_path(locked)
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace('protocol = "prereg-v1"\n', ""), encoding="utf-8")
    [line] = failures(locked)
    assert "is malformed" in line and "protocol" in line
    path.write_text(
        text.replace("[simulation]", 'surprise = "x"\n\n[simulation]'), encoding="utf-8"
    )
    assert "is malformed" in failures(locked)[0]


def test_an_unsafe_document_path_in_the_lock_fails_the_check(locked: Path) -> None:
    path = lock_path(locked)
    path.write_text(path.read_text(encoding="utf-8").replace(DOCUMENT, "../outside.md"))
    assert failures(locked)[0] == "the lock names an unsafe document path: ../outside.md"


# --- the TOML writer ----------------------------------------------------------------------------------------


def test_the_toml_writer_round_trips_awkward_strings_and_nested_tables() -> None:
    data: dict[str, Any] = {
        "b": 2,
        "a": 'say "hi" \\ back\tslash\nnewline',
        "yes": True,
        "unicode": "café →",
        "t": {"z": "last", "a": {"deep": "x", "path/with.dots and spaces": "v"}, "n": 0},
        "t-2": {"k": "v"},
    }
    assert tomllib.loads(dumps(data)) == data


def test_the_toml_writer_sorts_keys_and_quotes_only_what_needs_it() -> None:
    text = dumps({"z": "1", "a": "2", "m": {"b/c.py": "x", "ok-key_1": "y"}})
    assert text.index('a = "2"') < text.index('z = "1"') < text.index("[m]")
    assert '"b/c.py" = "x"' in text and 'ok-key_1 = "y"' in text


def test_the_toml_writer_leaves_out_the_header_of_a_table_that_only_holds_tables() -> None:
    text = dumps({"m": {"a": {"k": "v"}}, "e": {}})
    assert "[m]" not in text and "[m.a]" in text and "[e]" in text
    assert tomllib.loads(text) == {"m": {"a": {"k": "v"}}, "e": {}}


def test_the_toml_writer_refuses_a_type_it_was_not_built_for() -> None:
    with pytest.raises(TypeError):
        dumps({"x": 1.5})
    with pytest.raises(TypeError):
        dumps({"x": ["a"]})


def test_a_written_lock_reads_back_to_the_data_it_was_built_from(tree: Path) -> None:
    data = build_lock(tree, (MODEL, "nova-lite"), experiment=EXPERIMENT)
    assert tomllib.loads(dumps(data)) == data
    make_lock(tree, (MODEL, "nova-lite"))
    assert read_lock(lock_path(tree)).model_dump(exclude_none=True) == data


# --- the command line and the Makefile ----------------------------------------------------------------------


def run_cli(root: Path, *args: str) -> int:
    return cli.main(["protocol", "--root", str(root), *args])


def test_check_through_the_cli_passes_without_a_lock_and_fails_on_a_change(
    locked: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run_cli(locked, "check") == 0
    assert "protocol check: ok" in capsys.readouterr().out
    append(locked, DECISION)
    assert run_cli(locked, "check") == 1
    err = capsys.readouterr().err
    assert f"FAIL: instrument differs from prereg-v1: {DECISION}" in err
    assert "core.autocrlf" in err


def test_lock_through_the_cli_prints_without_write_and_writes_with_it(
    tree: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    base = ["lock", "--experiment", EXPERIMENT, "--model", MODEL]
    assert run_cli(tree, *base) == 0
    printed = capsys.readouterr().out
    assert printed == render_lock(tree, (MODEL,), experiment=EXPERIMENT)
    assert not lock_path(tree).exists()
    assert run_cli(tree, *base, "--write") == 0
    assert lock_path(tree).read_text(encoding="utf-8") == printed
    assert run_cli(tree, *base, "--write") == 2
    assert "refused:" in capsys.readouterr().err


def test_lock_through_the_cli_refuses_without_a_model(
    tree: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run_cli(tree, "lock", "--experiment", EXPERIMENT, "--write") == 2
    assert "no official model named" in capsys.readouterr().err
    assert not lock_path(tree).exists()


def test_make_check_runs_the_protocol_check() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    [check_line] = [line for line in makefile.splitlines() if line.startswith("check:")]
    assert "protocol-check" in check_line.split("##")[0].split()
    assert "hc protocol check" in makefile
