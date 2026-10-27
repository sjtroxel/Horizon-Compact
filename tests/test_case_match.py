"""The case matcher's driver (Phase 5.5 IMPLEMENTATION doc §5.2, K2), on fakes. No model, no AWS, no GitHub:
the bucket is a local folder, the runs are written by hand, and the case is invented (every name, sentence and
figure here is a canary, and the real rubrics are private).
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from horizon_compact import cli
from horizon_compact.caseprobe.layout import CONTENT_FILES, content_key, runs_prefix
from horizon_compact.caseprobe.match import (
    MatchRefused,
    describe_rubric,
    load_material,
    match_sweep,
    write_match,
)
from horizon_compact.protocol import lock
from horizon_compact.protocol.cases import CaseContent, case_lock_text, content_hashes
from horizon_compact.protocol.lock import write_lock
from horizon_compact.sweep.plan import SweepRefusal
from horizon_compact.sweep.store import LocalStore
from test_casebuild_rubric import CANARIES, rubric_text

ROOT = Path(__file__).resolve().parents[1]
PKG = "src/horizon_compact"
LABEL = "pre-90"
MODEL = "haiku-5-5"
SWEEP = "sw-test0001"
HEAD = "0123456789abcdef0123456789abcdef01234567"
FREEZE = "docs/phases/evidence/phase-5/freeze.json"
ALTERNATIVES_JSON = "docs/phases/evidence/phase-5.5/alternatives.json"
EXPLORATORY_LABEL = "CANARY exploratory label text"
OBJECTIVES = ("A", "B", "C", "D", "E")
WORDINGS = ("w1", "w2", "w3")
DOSSIER = (
    b'title = "An invented firm"\n'
    b'text = """\nCANARY-DOSSIER-TEXT. The firm makes widgets. Revenue was 100.\n"""\n'
)
SCENARIO = (ROOT / "experiment" / "company" / "scenarios" / "s3.toml").read_bytes()
# Objective A closes the plant every time; the others retool it.
CHOICES = {"A": "close", "B": "retool", "C": "retool", "D": "retool", "E": "retool"}
LINES = ("eliminated", "moved_other_plants", "kept_at_plant", "transferred_to_buyer")


def write(root: Path, path: str, text: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")


def make_tree(tmp_path: Path, rubric: str) -> tuple[Path, LocalStore]:
    """A tagged tree (a fake package, the real ``company`` experiment, a lock), the case's record, a freeze
    that lists it, and a bucket holding its content."""
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
    write_lock(root, (MODEL, "gpt-oss-openrouter"), experiment="company")
    content = CaseContent(DOSSIER, SCENARIO, rubric.encode("utf-8"))
    write(
        root,
        f"experiment/cases/{LABEL}/case.lock",
        case_lock_text(LABEL, 1, content_hashes(content)),
    )
    entry = {"label": LABEL, "probe_set": 1, "type": "closure", "text": EXPLORATORY_LABEL}
    write(root, FREEZE, json.dumps({"cases": [entry]}))
    store = LocalStore(tmp_path / "bucket")
    for name, data in zip(
        CONTENT_FILES, (content.dossier, content.scenario, content.rubric), strict=True
    ):
        store.put_new(content_key(LABEL, 1, name), data.decode("utf-8"))
    return root, store


def write_sweep(
    store: LocalStore,
    *,
    sweep_id: str = SWEEP,
    model: str = MODEL,
    repeats: int = 2,
    unfinished: int = 0,
    experiment: str = f"case-{LABEL}",
    label: str = "case",
    scenarios: tuple[str, ...] = ("s3",),
) -> None:
    prefix = runs_prefix(LABEL, sweep_id)
    planned: list[dict[str, Any]] = []
    n = 0
    for objective in OBJECTIVES:
        for wording in WORDINGS:
            for repeat in range(1, repeats + 1):
                n += 1
                planned.append(
                    {
                        "run_id": f"r-{n:012x}",
                        "scenario_id": "s3",
                        "objective_id": objective,
                        "wording_id": wording,
                        "repeat": repeat,
                    }
                )
    manifest = {
        "sweep_id": sweep_id,
        "label": label,
        "experiment": experiment,
        "model_key": model,
        "scenarios": list(scenarios),
        "runs": planned,
    }
    store.put_new(f"{prefix}manifest.json", json.dumps(manifest))
    for run in planned[: len(planned) - unfinished]:
        choice = CHOICES[run["objective_id"]]
        attempt = {
            "status": "valid",
            "attempt": 1,
            "scenario_id": "s3",
            "objective_id": run["objective_id"],
            "menu_order": list(LINES),
            "option_order": ["close", "retool", "sell"],
            "validation": {
                "amounts": {
                    "eliminated": 190,
                    "moved_other_plants": 0,
                    "kept_at_plant": 0,
                    "transferred_to_buyer": 0,
                },
                "choice": choice,
            },
        }
        final = {"status": "valid", "final_attempt": 1, "first_attempt_status": "valid"}
        base = f"{prefix}runs/{run['run_id']}/"
        store.put_new(f"{base}attempt-1.json", json.dumps(attempt))
        store.put_new(f"{base}final.json", json.dumps(final))


@pytest.fixture
def case(tmp_path: Path) -> tuple[Path, LocalStore]:
    root, store = make_tree(tmp_path, rubric_text())
    write_sweep(store)
    return root, store


def numbers(value: Any) -> list[float]:
    """Every number in a JSON value."""
    if isinstance(value, bool):
        return []
    if isinstance(value, int | float):
        return [value]
    if isinstance(value, dict):
        return [n for item in value.values() for n in numbers(item)]
    if isinstance(value, list):
        return [n for item in value for n in numbers(item)]
    return []


def appendix_of(root: Path) -> Path:
    """The private appendix, beside the fake repository."""
    return root.parent / "appendix"


# Fictional numbers: the alternative makes every line observable, all on eliminated.
ALTERNATIVES = (
    'case = "pre-90"\n\n[[alternative]]\ncall = "u1"\n'
    "lines = { eliminated = 190, moved_other_plants = 0, kept_at_plant = 0, transferred_to_buyer = 0 }\n"
)


def transcribe(root: Path, text: str = ALTERNATIVES, *, digest: str | None = None) -> None:
    """The case's alternatives.toml in the appendix, and its sha256 in the committed file."""
    path = appendix_of(root) / LABEL / "alternatives.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    if digest is None:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    write(root, ALTERNATIVES_JSON, json.dumps({"cases": {LABEL: digest}}))


def run_match(root: Path, store: LocalStore, **changes: Any) -> Any:
    arguments: dict[str, Any] = {
        "model_key": MODEL,
        "sweep_id": SWEEP,
        "head": HEAD,
        "appendix": appendix_of(root),
    }
    arguments.update(changes)
    return match_sweep(
        root, store, LABEL, arguments.pop("model_key"), arguments.pop("sweep_id"), **arguments
    )


def refused(root: Path, store: LocalStore, **changes: Any) -> str:
    with pytest.raises(MatchRefused) as caught:
        run_match(root, store, **changes)
    return str(caught.value)


# --- the case and its rubric ----------------------------------------------------------------------------


def test_a_frozen_case_loads_with_the_rubric_the_lock_names(case: tuple[Path, LocalStore]) -> None:
    root, store = case
    material = load_material(root, store, LABEL, appendix_of(root))
    assert material.case_type == "closure" and material.exploratory_label == EXPLORATORY_LABEL
    assert material.scenario.id == "s3"
    assert material.decision.reading == "primary" and material.decision.choice == "close"
    assert material.decision.amounts == {}


def test_check_rubric_prints_names_and_the_shape_only(case: tuple[Path, LocalStore]) -> None:
    root, store = case
    text = "\n".join(describe_rubric(load_material(root, store, LABEL, appendix_of(root))))
    assert "pre-90: shape s3" in text
    assert "observable dimensions: choice" in text
    assert (
        "excluded dimensions:   eliminated, moved_other_plants, kept_at_plant, transferred_to_buyer"
        in text
    )
    assert "primary, u1 (no transcribed alternative, not matched)" in text
    assert "primary reading: 1 dimension(s) of the 1 needed: enough" in text
    for leak in (*CANARIES, "close", "retool", "190"):
        assert leak not in text


def test_a_rubric_that_does_not_hash_to_the_lock_is_refused(tmp_path: Path) -> None:
    root, store = make_tree(tmp_path, rubric_text())
    shutil.rmtree(tmp_path / "bucket" / "cases" / LABEL / "set-1")
    store.put_new(content_key(LABEL, 1, "dossier.toml"), DOSSIER.decode("utf-8"))
    store.put_new(content_key(LABEL, 1, "scenario.toml"), SCENARIO.decode("utf-8"))
    store.put_new(content_key(LABEL, 1, "rubric.toml"), rubric_text(uncertain=0))
    with pytest.raises(
        MatchRefused, match=r"rubric does not hash to experiment/cases/pre-90/case\.lock"
    ):
        load_material(root, store, LABEL, appendix_of(root))


def test_a_label_that_is_not_in_the_freeze_is_refused(case: tuple[Path, LocalStore]) -> None:
    root, store = case
    write(root, FREEZE, json.dumps({"cases": [{"label": "pre-91", "probe_set": 1}]}))
    assert "is not one of docs/phases/evidence/phase-5/freeze.json's frozen cases" in refused(
        root, store
    )


def test_a_freeze_entry_without_label_text_is_refused(case: tuple[Path, LocalStore]) -> None:
    root, store = case
    write(
        root, FREEZE, json.dumps({"cases": [{"label": LABEL, "probe_set": 1, "type": "closure"}]})
    )
    assert "has no type and label text for case pre-90" in refused(root, store)


def test_a_rubric_that_does_not_fit_its_scenario_is_refused_with_every_reason(
    tmp_path: Path,
) -> None:
    text = (
        rubric_text()
        .replace('shape = "S3"', 'shape = "S2"')
        .replace("scenario_total = 190", "scenario_total = 191")
    )
    root, store = make_tree(tmp_path, text)
    with pytest.raises(MatchRefused) as caught:
        load_material(root, store, LABEL, appendix_of(root))
    message = str(caught.value)
    assert "shape is not the scenario's (s3)" in message
    assert "scenario_total is not the scenario's (190)" in message


def test_a_company_choice_the_scenario_does_not_offer_is_refused(tmp_path: Path) -> None:
    root, store = make_tree(tmp_path, rubric_text(choice="expand"))
    with pytest.raises(MatchRefused, match="not one of the scenario's options"):
        load_material(root, store, LABEL, appendix_of(root))


def test_a_rubric_the_reader_refuses_is_refused_here(tmp_path: Path) -> None:
    root, store = make_tree(tmp_path, rubric_text(extra="surprise = 1\n"))
    with pytest.raises(MatchRefused, match="keys this form does not"):
        load_material(root, store, LABEL, appendix_of(root))


# --- the sweep ---------------------------------------------------------------------------------------------


def test_a_finished_sweep_matches_and_the_record_holds_what_the_plan_lists(
    case: tuple[Path, LocalStore],
) -> None:
    root, store = case
    result = run_match(root, store)
    record = result.record
    assert result.path == root / "experiment/results/cases/pre-90/haiku-5-5.json"
    assert not result.path.exists()  # match_sweep writes nothing
    assert result.status_counts == {"valid": 30} == record["run_counts"]["by_final_status"]
    assert record["run_counts"]["runs"] == 30
    assert record["case"] == LABEL and record["type"] == "closure" and record["exploratory"] is True
    assert record["exploratory_label"] == EXPLORATORY_LABEL
    assert record["experiment"] == "case-pre-90" and record["scenario_id"] == "s3"
    assert record["model_key"] == MODEL and record["sweep_id"] == SWEEP
    assert record["thresholds"]["k_star"] == 1 and record["thresholds"]["d_star"] > 0
    assert record["dimensions"] == {
        "observable": ["choice"],
        "excluded": list(LINES),
    }
    assert record["company"] == {"reading": "primary", "choice": "close", "shares": {}}
    [reading] = record["readings"]
    assert reading["reading"] == "primary" and reading["label"] == "match"
    assert reading["nearest"] == "A" and reading["tied_with"] is None
    assert reading["company_basis"] == "choice" and reading["dimensions"] == 1
    assert [d["objective_id"] for d in reading["distances"]] == list(OBJECTIVES)
    assert all(
        {"distance", "low", "high", "runs", "undistanced_runs"} <= set(d)
        for d in reading["distances"]
    )
    assert reading["distances"][0]["distance"] == 0.0 and reading["distances"][1]["distance"] == 1.0
    assert reading["gap"]["nearest"] == "A"


def test_an_uncertain_call_without_a_transcribed_alternative_is_reported_not_evaluated(
    case: tuple[Path, LocalStore],
) -> None:
    root, store = case
    result = run_match(root, store)
    assert result.unmatched_calls == ("u1",)
    assert result.record["alternative_readings"] == {"matched": 0, "unmatched_calls": ["u1"]}
    assert result.record["depends_on_reading"] is None  # not evaluated, which is not false
    assert result.record["provenance"]["alternatives_sha256"] is None


def test_a_transcribed_alternative_is_matched_as_a_second_reading(
    case: tuple[Path, LocalStore],
) -> None:
    root, store = case
    transcribe(root)
    material = load_material(root, store, LABEL, appendix_of(root))
    [alternative] = material.alternatives
    assert alternative.reading == "u1" and alternative.choice == "close"  # the primary's choice
    assert material.unmatched_calls == []
    text = "\n".join(describe_rubric(material))
    assert "readings:              primary, u1\n" in text + "\n"
    assert "u1 reading: 4 dimension(s) of the 1 needed: enough" in text
    assert "190" not in text
    result = run_match(root, store)
    record = result.record
    assert result.unmatched_calls == ()
    assert record["alternative_readings"] == {"matched": 1, "unmatched_calls": []}
    assert [r["reading"] for r in record["readings"]] == ["primary", "u1"]
    second = record["readings"][1]
    assert list(second["observable_lines"]) == list(LINES) and second["company_basis"] == "both"
    assert isinstance(record["depends_on_reading"], bool)
    assert record["company_alternatives"] == [
        {
            "reading": "u1",
            "choice": "close",
            "shares": {
                "eliminated": 1.0,
                "moved_other_plants": 0.0,
                "kept_at_plant": 0.0,
                "transferred_to_buyer": 0.0,
            },
        }
    ]
    digest = hashlib.sha256(ALTERNATIVES.encode("utf-8")).hexdigest()
    assert record["provenance"]["alternatives_sha256"] == digest
    assert 190 not in numbers(record)


def test_an_alternatives_file_that_does_not_hash_to_the_committed_one_is_refused(
    case: tuple[Path, LocalStore],
) -> None:
    root, store = case
    transcribe(root, digest="0" * 64)
    with pytest.raises(MatchRefused, match="does not hash to the committed sha256"):
        load_material(root, store, LABEL, appendix_of(root))


def test_an_alternatives_file_with_no_committed_hash_is_refused(
    case: tuple[Path, LocalStore],
) -> None:
    root, store = case
    transcribe(root)
    (root / ALTERNATIVES_JSON).unlink()
    with pytest.raises(MatchRefused, match="whose hash is not committed"):
        load_material(root, store, LABEL, appendix_of(root))


def test_a_committed_hash_with_no_alternatives_file_is_refused(
    case: tuple[Path, LocalStore],
) -> None:
    root, store = case
    transcribe(root)
    (appendix_of(root) / LABEL / "alternatives.toml").unlink()
    with pytest.raises(MatchRefused, match="cannot read case pre-90's alternatives"):
        load_material(root, store, LABEL, appendix_of(root))


def test_an_alternative_the_scenario_cannot_take_is_refused(
    case: tuple[Path, LocalStore],
) -> None:
    root, store = case
    transcribe(root, ALTERNATIVES.replace("eliminated = 190", "eliminated = -1"))
    with pytest.raises(MatchRefused, match="negative or not finite"):
        load_material(root, store, LABEL, appendix_of(root))


def test_a_rubric_with_no_uncertain_call_reports_depends_on_reading_from_the_matcher(
    tmp_path: Path,
) -> None:
    root, store = make_tree(tmp_path, rubric_text(uncertain=0))
    write_sweep(store)
    result = run_match(root, store)
    assert result.unmatched_calls == ()
    assert result.record["alternative_readings"] == {"matched": 0, "unmatched_calls": []}
    assert result.record["depends_on_reading"] is False


def test_the_observable_lines_reach_the_matcher_as_shares_never_as_amounts(tmp_path: Path) -> None:
    text = rubric_text(observed={"eliminated": 7700, "kept_at_plant": 3300})
    root, store = make_tree(tmp_path, text)
    write_sweep(store)
    result = run_match(root, store)
    company = result.record["company"]
    assert company["choice"] == "close"
    assert company["shares"] == pytest.approx({"eliminated": 0.7, "kept_at_plant": 0.3})
    [reading] = result.record["readings"]
    assert list(reading["observable_lines"]) == ["eliminated", "kept_at_plant"]
    assert reading["company_basis"] == "both" and reading["dimensions"] == 2
    written = json.loads(write_match(result).read_text(encoding="utf-8"))
    assert not {7700, 3300} & set(
        numbers(written)
    )  # compared as numbers: a digit run can occur in a float


def test_the_results_file_holds_no_excerpt_term_or_sentence(case: tuple[Path, LocalStore]) -> None:
    root, store = case
    path = write_match(run_match(root, store))
    text = path.read_text(encoding="utf-8")
    assert text.endswith("\n") and json.loads(text)["case"] == LABEL
    for canary in (*CANARIES, "CANARY-DOSSIER-TEXT", "kept_at_plant = 12"):
        assert canary not in text
    assert list(json.loads(text)) == [
        "results_version",
        "case",
        "type",
        "exploratory",
        "exploratory_label",
        "experiment",
        "scenario_id",
        "model_key",
        "sweep_id",
        "run_counts",
        "thresholds",
        "dimensions",
        "company",
        "company_alternatives",
        "readings",
        "alternative_readings",
        "depends_on_reading",
        "provenance",
    ]


def test_the_provenance_proves_which_commit_and_which_frozen_code(
    case: tuple[Path, LocalStore],
) -> None:
    root, store = case
    record = run_match(root, store).record
    locked = lock.read_lock(lock.lock_path(root))
    assert record["provenance"] == {
        "head": HEAD,
        "protocol": locked.protocol,
        "protocol_check": "ok",
        "analysis_sha256": locked.analysis.sha256,
        "uv_lock_sha256": locked.analysis.uv_lock_sha256,
        "rubric_sha256": content_hashes(CaseContent(DOSSIER, SCENARIO, rubric_text().encode()))[
            "rubric_sha256"
        ],
        "alternatives_sha256": None,
        "sweep_id": SWEEP,
    }


def test_a_changed_frozen_analysis_file_refuses_the_match(case: tuple[Path, LocalStore]) -> None:
    root, store = case
    write(root, f"{PKG}/analysis/verdict.py", "# changed after the tag\n")
    assert "hc protocol check fails on this checkout" in refused(root, store)


def test_an_unfinished_run_is_refused(tmp_path: Path) -> None:
    root, store = make_tree(tmp_path, rubric_text())
    write_sweep(store, unfinished=3)
    message = refused(root, store)
    assert "3 run(s) of sweep sw-test0001 are unfinished" in message


def test_a_sweep_that_is_not_the_cases_is_refused_with_every_reason(tmp_path: Path) -> None:
    root, store = make_tree(tmp_path, rubric_text())
    write_sweep(
        store, model="gpt-oss-openrouter", experiment="case-pre-91", label="grid", scenarios=("s2",)
    )
    message = refused(root, store)
    assert "is not an experiment of case pre-90" in message
    assert "label is not 'case'" in message
    assert "is not a sweep of haiku-5-5" in message
    assert "does not run the case's one scenario (s3)" in message


def test_a_manifest_that_names_another_sweep_is_refused(tmp_path: Path) -> None:
    root, store = make_tree(tmp_path, rubric_text())
    write_sweep(store)
    prefix = runs_prefix(LABEL, SWEEP)
    manifest = json.loads(store.get(f"{prefix}manifest.json") or "{}")
    manifest["sweep_id"] = "sw-other0001"
    (store.root / f"{prefix}manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert f"the manifest under {SWEEP} names another sweep" in refused(root, store)


def test_a_missing_manifest_is_refused(case: tuple[Path, LocalStore]) -> None:
    root, store = case
    assert "no readable manifest for sweep sw-nothing" in refused(
        root, store, sweep_id="sw-nothing"
    )


def test_a_sweep_id_that_is_not_a_plain_name_is_refused(case: tuple[Path, LocalStore]) -> None:
    root, store = case
    assert "is not a sweep id" in refused(root, store, sweep_id="../x")


def test_an_existing_results_file_is_refused_and_never_overwritten(
    case: tuple[Path, LocalStore],
) -> None:
    root, store = case
    result = run_match(root, store)
    path = write_match(result)
    before = path.read_bytes()
    assert "a case result is never overwritten" in refused(root, store)
    with pytest.raises(MatchRefused, match="never overwritten"):
        write_match(result)  # a second command that passed its checks before the first wrote
    assert path.read_bytes() == before
    assert not list(path.parent.glob(".*.tmp"))


def test_a_refusal_writes_nothing(tmp_path: Path) -> None:
    root, store = make_tree(tmp_path, rubric_text())
    write_sweep(store, unfinished=1)
    refused(root, store)
    assert not (root / "experiment" / "results").exists()


# --- the command ------------------------------------------------------------------------------------


def patch_cli(
    monkeypatch: pytest.MonkeyPatch, root: Path, store: LocalStore, *, dirty: str = ""
) -> None:
    monkeypatch.setattr(cli, "default_repo_root", lambda: root)
    monkeypatch.setattr(cli, "_case_bucket_store", lambda args: store)
    monkeypatch.setattr(cli, "appendix_dir", lambda: appendix_of(root))
    monkeypatch.setattr(cli, "_git", lambda *args: dirty if args[0] == "status" else HEAD)


def test_the_command_writes_one_file_and_prints_the_path_and_counts_only(
    case: tuple[Path, LocalStore],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, store = case
    patch_cli(monkeypatch, root, store)
    argv = ["case", "match", LABEL, "--model", MODEL, "--sweep", SWEEP, "--profile", "p"]
    assert cli.main(argv) == 0
    out = capsys.readouterr().out
    assert "wrote experiment/results/cases/pre-90/haiku-5-5.json" in out
    assert "runs:            30  {'valid': 30}" in out
    assert "not matched:     u1" in out and "not evaluated" in out
    for leak in ("distance", "nearest", "tie", "close", "retool", "0.", "1.0"):
        assert leak not in out  # no figure, no objective, no choice
    assert (root / "experiment/results/cases/pre-90/haiku-5-5.json").is_file()
    assert cli.main(argv) == 2  # the second run is refused
    assert "never overwritten" in capsys.readouterr().err


def test_the_command_refuses_uncommitted_code_and_writes_nothing(
    case: tuple[Path, LocalStore],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, store = case
    patch_cli(monkeypatch, root, store, dirty=" M src/horizon_compact/caseprobe/match.py")
    argv = ["case", "match", LABEL, "--model", MODEL, "--sweep", SWEEP, "--profile", "p"]
    assert cli.main(argv) == 2
    assert "differ from HEAD" in capsys.readouterr().err
    assert not (root / "experiment" / "results").exists()


def test_the_command_refuses_without_a_model_and_sweep(
    case: tuple[Path, LocalStore],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, store = case
    patch_cli(monkeypatch, root, store)
    assert cli.main(["case", "match", LABEL, "--profile", "p"]) == 2
    assert "--model and --sweep are required" in capsys.readouterr().err
    assert not (root / "experiment" / "results").exists()


def test_check_rubric_reads_no_run_and_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root, store = make_tree(tmp_path, rubric_text())  # no sweep exists
    patch_cli(monkeypatch, root, store)
    assert cli.main(["case", "match", LABEL, "--check-rubric", "--profile", "p"]) == 0
    out = capsys.readouterr().out
    assert "shape s3" in out and "observable dimensions: choice" in out
    assert not (root / "experiment" / "results").exists()


def test_the_command_is_a_sweep_refusal_so_the_command_line_needs_no_scipy() -> None:
    assert issubclass(MatchRefused, SweepRefusal)
