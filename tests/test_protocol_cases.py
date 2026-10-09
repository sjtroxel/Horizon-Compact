"""The gate's case mode (Phase 3.5 IMPLEMENTATION doc section 8, decision 10, build step 6), both ways.

Fake GitHub runs and fake probe objects stand in for the two servers whose times prove the order. Every case
label, every byte of case content and every time here is invented; no real case exists yet (Phase 5).
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from horizon_compact.experiment import load_experiment
from horizon_compact.protocol import lock
from horizon_compact.protocol.cases import (
    CASE_REFUSED,
    CaseContent,
    CaseError,
    CiRun,
    ProbeRecord,
    check_case_content,
    check_case_official,
    check_case_order,
    check_case_probes,
    check_order_finding,
    parse_case,
    read_case,
    run_case_gate,
)
from horizon_compact.protocol.lock import write_lock
from horizon_compact.sweep.plan import SweepRefusal
from sweep_helpers import FARGATE, LAPTOP

ROOT = Path(__file__).resolve().parents[1]
PKG = "src/horizon_compact"
LABEL = "case-a"
MODELS = ("nova-lite", "sonnet-4-6")
MAIN = "sonnet-4-6"
T0 = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)
HOUR = timedelta(hours=1)

CONTENT = CaseContent(
    dossier=b"case-a: the dossier as built\n",
    scenario=b"case-a: the scenario text\n",
    rubric=b"case-a: what was done, mapped onto the table\n",
)
COARSENED = CaseContent(
    dossier=b"case-a: the dossier, coarsened\n",
    scenario=CONTENT.scenario,
    rubric=CONTENT.rubric,
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def record_text(
    content: CaseContent = CONTENT, *, probe_set: int = 1, label: str = LABEL, version: int = 1
) -> str:
    return (
        f"case_version = {version}\n"
        f'label = "{label}"\n'
        f"probe_set = {probe_set}\n"
        f'dossier_sha256 = "{sha(content.dossier)}"\n'
        f'scenario_sha256 = "{sha(content.scenario)}"\n'
        f'rubric_sha256 = "{sha(content.rubric)}"\n'
    )


def run(run_id: str, at: datetime, text: str | None) -> CiRun:
    return CiRun(run_id, at, text)


def probes(
    at: datetime,
    *,
    probe_set: int = 1,
    passed: bool = True,
    models: tuple[str, ...] = MODELS,
    calls: int = 3,
) -> list[ProbeRecord]:
    """``calls`` probe calls per model, a minute apart from ``at``."""
    return [
        ProbeRecord(
            f"probes/{LABEL}/set-{probe_set}/{model}/call-{n}.json",
            model,
            probe_set,
            passed,
            at + timedelta(minutes=n + 10 * i),
        )
        for i, model in enumerate(models)
        for n in range(calls)
    ]


RECORD = parse_case(record_text(), LABEL)
RECORD_2 = parse_case(record_text(COARSENED, probe_set=2), LABEL)


# --- check 1: the record and the content --------------------------------------------------------------------


def test_content_that_hashes_to_the_record_passes() -> None:
    assert check_case_content(RECORD, CONTENT) == []


@pytest.mark.parametrize(
    ("part", "changed"),
    [
        ("the dossier", CaseContent(b"other\n", CONTENT.scenario, CONTENT.rubric)),
        ("the scenario text", CaseContent(CONTENT.dossier, b"other\n", CONTENT.rubric)),
        ("the rubric", CaseContent(CONTENT.dossier, CONTENT.scenario, b"other\n")),
    ],
)
def test_content_that_does_not_hash_to_the_record_is_refused(
    part: str, changed: CaseContent
) -> None:
    assert check_case_content(RECORD, changed) == [
        f"{part} does not hash to experiment/cases/case-a/case.lock"
    ]


def test_a_record_naming_another_case_is_refused() -> None:
    with pytest.raises(CaseError, match="names case 'case-b'"):
        parse_case(record_text(label="case-b"), LABEL)


def test_a_record_of_an_unknown_version_or_shape_is_refused() -> None:
    with pytest.raises(CaseError, match="case_version 2"):
        parse_case(record_text(version=2), LABEL)
    with pytest.raises(CaseError, match="is malformed"):
        parse_case(record_text().replace(sha(CONTENT.rubric), "not-a-hash"), LABEL)
    with pytest.raises(CaseError, match="is malformed"):
        parse_case(record_text() + 'surprise = "x"\n', LABEL)
    with pytest.raises(CaseError, match="is malformed"):
        parse_case(record_text(probe_set=3), LABEL)
    with pytest.raises(CaseError, match="not valid TOML"):
        parse_case("this = = broken\n", LABEL)


@pytest.mark.parametrize("label", ["", ".", "..", "a/b", "../case-a", "a\\b"])
def test_a_label_that_is_not_one_folder_name_is_refused(label: str) -> None:
    with pytest.raises(CaseError, match="is not a case label"):
        parse_case(record_text(), label)


def test_an_uncommitted_record_is_refused(tmp_path: Path) -> None:
    with pytest.raises(CaseError, match="no case record"):
        read_case(tmp_path, LABEL)


# --- check 2: the order -------------------------------------------------------------------------------------


def test_a_record_in_ci_before_the_first_probe_is_admitted() -> None:
    found = check_case_order(RECORD, [run("101", T0, record_text())], probes(T0 + HOUR))
    assert found.admitted and found.reasons == ()
    assert (found.rubric_run, found.content_run) == ("101", "101")
    assert found.first_probe == f"probes/{LABEL}/set-1/nova-lite/call-0.json"


def test_a_ci_run_after_the_first_probe_is_refused() -> None:
    found = check_case_order(RECORD, [run("101", T0 + HOUR, record_text())], probes(T0))
    assert not found.admitted
    assert any("rubric was first in CI at" in reason for reason in found.reasons)
    assert any("content for probe set 1 was first in CI" in reason for reason in found.reasons)


def test_a_ci_run_at_the_same_instant_as_the_first_probe_is_refused() -> None:
    first = min(p.last_modified for p in probes(T0))
    found = check_case_order(RECORD, [run("101", first, record_text())], probes(T0))
    assert not found.admitted
    assert any("rubric was first in CI" in reason for reason in found.reasons)


def test_no_ci_run_is_refused() -> None:
    found = check_case_order(RECORD, [], probes(T0 + HOUR))
    assert not found.admitted
    assert f"no GitHub Actions run on a commit holding case {LABEL}'s rubric hash" in found.reasons


def test_ci_runs_that_do_not_hold_this_record_prove_nothing() -> None:
    runs = [
        run("100", T0, None),
        run("101", T0, record_text(label="case-b")),
        run("102", T0, "this = = broken\n"),
        run("103", T0, record_text(CaseContent(b"x\n", b"y\n", b"z\n"))),
    ]
    assert not check_case_order(RECORD, runs, probes(T0 + HOUR)).admitted


def test_the_earliest_run_holding_the_record_is_the_one_that_counts() -> None:
    runs = [run("102", T0 + 2 * HOUR, record_text()), run("101", T0, record_text())]
    found = check_case_order(RECORD, runs, probes(T0 + HOUR))
    assert found.admitted and found.rubric_run == "101"


def test_no_probe_to_order_against_is_refused() -> None:
    found = check_case_order(RECORD, [run("101", T0, record_text())], [])
    assert not found.admitted
    assert f"case {LABEL} has no recognition probe in set 1 to order against" in found.reasons


def test_a_time_without_a_zone_cannot_be_ordered() -> None:
    naive = [run("101", datetime(2026, 11, 2, 12, 0), record_text())]  # no zone, on purpose
    found = check_case_order(RECORD, naive, probes(T0 + HOUR))
    assert not found.admitted and "without a time zone" in found.reasons[0]


def test_times_in_different_zones_are_compared_as_instants() -> None:
    """A CI time written at UTC-5 that is an hour before the probe in UTC is before it."""
    est = timezone(timedelta(hours=-5))
    at = (T0 + HOUR).astimezone(est) - HOUR
    assert check_case_order(RECORD, [run("101", at, record_text())], probes(T0 + HOUR)).admitted


# --- a coarsened case ---------------------------------------------------------------------------------------


def coarsened_history() -> tuple[list[CiRun], list[ProbeRecord]]:
    """Rubric and first content in CI at T0; set 1 probed at T0+1h and failed on one model; the coarsened
    record in CI at T0+3h; set 2 probed at T0+4h and passed."""
    first = probes(T0 + HOUR)
    first[0] = ProbeRecord(first[0].key, first[0].model_key, 1, False, first[0].last_modified)
    runs = [
        run("101", T0, record_text()),
        run("102", T0 + 3 * HOUR, record_text(COARSENED, probe_set=2)),
    ]
    return runs, first + probes(T0 + 4 * HOUR, probe_set=2)


def test_a_coarsened_case_is_admitted_on_its_second_probe_set() -> None:
    runs, all_probes = coarsened_history()
    found = check_case_order(RECORD_2, runs, all_probes)
    assert found.admitted, found.reasons
    assert (found.rubric_run, found.content_run) == ("101", "102")
    assert check_case_probes(RECORD_2, all_probes, MODELS) == []


def test_a_rubric_first_committed_after_the_first_probe_is_refused_even_when_coarsened() -> None:
    runs, all_probes = coarsened_history()
    rewritten = CaseContent(
        COARSENED.dossier, COARSENED.scenario, b"case-a: a rubric written later\n"
    )
    record = parse_case(record_text(rewritten, probe_set=2), LABEL)
    runs.append(run("103", T0 + 3 * HOUR, record_text(rewritten, probe_set=2)))
    found = check_case_order(record, runs, all_probes)
    assert not found.admitted
    assert any("rubric was first in CI" in reason for reason in found.reasons)


def test_coarsened_content_committed_after_its_set_was_probed_is_refused() -> None:
    runs, all_probes = coarsened_history()
    runs[1] = run("102", T0 + 5 * HOUR, record_text(COARSENED, probe_set=2))
    found = check_case_order(RECORD_2, runs, all_probes)
    assert not found.admitted
    assert any("content for probe set 2 was first in CI" in reason for reason in found.reasons)


def test_the_coarsened_content_needs_its_own_ci_run_not_the_first_records() -> None:
    runs, all_probes = coarsened_history()
    found = check_case_order(RECORD_2, runs[:1], all_probes)
    assert not found.admitted
    assert any("content for probe set 2" in reason for reason in found.reasons)


def test_a_re_probe_on_the_same_dossier_is_refused() -> None:
    """Set 1 failed, then the record was bumped to set 2 without changing the dossier: probing until it
    passes, which the CI history shows."""
    runs, all_probes = coarsened_history()
    same = CaseContent(CONTENT.dossier, b"case-a: a scenario reworded\n", CONTENT.rubric)
    record = parse_case(record_text(same, probe_set=2), LABEL)
    runs[1] = run("102", T0 + 3 * HOUR, record_text(same, probe_set=2))
    found = check_case_order(record, runs, all_probes)
    assert found.reasons == (
        f"case {LABEL}'s probe set 2 has the dossier an earlier set was probed on: a re-probe follows "
        "coarsening, and the probe reads only the dossier",
    )


# --- check 3: the probes ------------------------------------------------------------------------------------


def test_every_official_model_passing_three_calls_passes() -> None:
    assert check_case_probes(RECORD, probes(T0), MODELS) == []


def test_a_failed_probe_is_refused_naming_the_call() -> None:
    calls = probes(T0)
    calls[4] = ProbeRecord(calls[4].key, calls[4].model_key, 1, False, calls[4].last_modified)
    assert check_case_probes(RECORD, calls, MODELS) == [
        f"case {LABEL}: sonnet-4-6 failed the recognition probe ({calls[4].key})"
    ]


def test_too_few_calls_or_a_model_never_probed_is_refused() -> None:
    assert check_case_probes(RECORD, probes(T0, calls=2), MODELS) == [
        f"case {LABEL}: nova-lite has 2 probe calls in set 1, not 3",
        f"case {LABEL}: sonnet-4-6 has 2 probe calls in set 1, not 3",
    ]
    assert check_case_probes(RECORD, probes(T0, models=("nova-lite",)), MODELS) == [
        f"case {LABEL}: sonnet-4-6 has 0 probe calls in set 1, not 3"
    ]


def test_no_probe_at_all_is_refused() -> None:
    assert check_case_probes(RECORD, [], MODELS) == [f"case {LABEL} has no recognition probe"]


def test_the_set_that_counts_must_be_the_records() -> None:
    _runs, all_probes = coarsened_history()
    assert check_case_probes(RECORD, all_probes, MODELS) == [
        f"case {LABEL}'s record is for probe set 1, but set 2 is the last probed"
    ]


def test_a_re_probe_after_a_passed_first_set_is_refused() -> None:
    all_probes = probes(T0) + probes(T0 + HOUR, probe_set=2)
    assert check_case_probes(RECORD_2, all_probes, MODELS) == [
        f"case {LABEL} was re-probed although its first probe set passed"
    ]


def test_a_third_probe_set_is_refused() -> None:
    all_probes = probes(T0, passed=False) + probes(T0 + HOUR, probe_set=3)
    assert check_case_probes(RECORD_2, all_probes, MODELS) == [
        f"case {LABEL} has probe sets outside 1-2: a case is re-probed once"
    ]


def test_a_model_outside_the_official_set_does_not_count() -> None:
    extra = probes(T0, models=("qwen-local",), passed=False)
    assert check_case_probes(RECORD, probes(T0) + extra, MODELS) == []


# --- the order finding in the manifest ----------------------------------------------------------------------


def test_the_finding_round_trips_through_the_manifest() -> None:
    found = check_case_order(RECORD, [run("101", T0, record_text())], probes(T0 + HOUR))
    as_stored = json.loads(json.dumps(found.as_record()))
    assert check_order_finding(LABEL, as_stored) == []


def test_a_missing_foreign_or_refused_finding_is_refused() -> None:
    assert "has no order finding" in check_order_finding(LABEL, None)[0]
    assert (
        "is for case 'case-b'"
        in check_order_finding(LABEL, {"label": "case-b", "admitted": True})[0]
    )
    refused = check_case_order(RECORD, [], probes(T0)).as_record()
    [line] = check_order_finding(LABEL, refused)
    assert line.startswith(f"the order check did not admit case {LABEL}: no GitHub Actions run")
    assert "did not admit" in check_order_finding(LABEL, {"label": LABEL, "admitted": "yes"})[0]


# --- the whole case gate ------------------------------------------------------------------------------------


def write(root: Path, path: str, text: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")


@pytest.fixture
def tagged(tmp_path: Path) -> Path:
    """A tagged tree (a fake package, the placeholder, a lock for both models) with case-a's record."""
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
    shutil.copytree(ROOT / "experiment" / "placeholder", root / "experiment" / "placeholder")
    shutil.copy(ROOT / "experiment" / "models.toml", root / "experiment" / "models.toml")
    write(root, "experiment/protocol/protocol-v1.md", "# the protocol\n")
    write(root, "uv.lock", "# locked\n")
    write(root, lock.SIMULATION_RELATIVE, '{"code_sha256": "abc"}\n')
    write_lock(root, MODELS, experiment="placeholder")
    write(root, f"experiment/cases/{LABEL}/case.lock", record_text())
    return root


def admitted_finding() -> dict[str, object]:
    return check_case_order(RECORD, [run("101", T0, record_text())], probes(T0 + HOUR)).as_record()


def case_gate(root: Path, **overrides: object) -> tuple[str, ...]:
    if "models" not in overrides:
        overrides["models"] = load_experiment("placeholder", root / "experiment").models
    arguments: dict[str, object] = {
        "label": LABEL,
        "content": CONTENT,
        "probes": probes(T0 + HOUR),
        "order_finding": admitted_finding(),
        "model_key": MAIN,
        "identity": FARGATE,
    }
    arguments.update(overrides)
    return run_case_gate(package_dir=root / PKG, **arguments).failures  # type: ignore[arg-type]


def test_a_case_with_its_record_order_and_probes_is_admitted_in_the_container(tagged: Path) -> None:
    assert case_gate(tagged) == ()


def test_the_case_gate_refuses_content_that_does_not_hash_to_the_record(tagged: Path) -> None:
    changed = CaseContent(CONTENT.dossier, CONTENT.scenario, b"another rubric\n")
    assert case_gate(tagged, content=changed) == (
        "the rubric does not hash to experiment/cases/case-a/case.lock",
    )


def test_the_case_gate_refuses_a_failed_probe(tagged: Path) -> None:
    assert case_gate(tagged, probes=probes(T0 + HOUR, passed=False)) == tuple(
        f"case {LABEL}: {model} failed the recognition probe "
        f"({', '.join(p.key for p in probes(T0 + HOUR) if p.model_key == model)})"
        for model in MODELS
    )


def test_the_case_gate_refuses_without_an_admitting_order_finding(tagged: Path) -> None:
    [line] = case_gate(tagged, order_finding=None)
    assert "has no order finding" in line


def test_the_case_gate_refuses_an_uncommitted_case(tagged: Path) -> None:
    assert case_gate(tagged, label="case-b") == (
        "no case record: experiment/cases/case-b/case.lock is not committed",
    )


def test_the_grid_checks_hold_for_a_case(tagged: Path) -> None:
    decision = tagged / f"{PKG}/sweep/decision.py"
    decision.write_text(decision.read_text(encoding="utf-8") + "# changed\n", encoding="utf-8")
    (tagged / "experiment/protocol/protocol-v1.md").write_text("# edited\n", encoding="utf-8")
    assert case_gate(tagged, model_key="qwen-local", identity=LAPTOP) == (
        "document differs from prereg-v1: experiment/protocol/protocol-v1.md",
        f"instrument differs from prereg-v1: {PKG}/sweep/decision.py",
        "model qwen-local is not one of prereg-v1's models (nova-lite, sonnet-4-6)",
        "official sweeps run only in the container, never on a laptop",
    )


def test_the_case_gate_needs_the_lock(tagged: Path) -> None:
    (tagged / lock.LOCK_RELATIVE).unlink()
    assert case_gate(tagged)[0].startswith("no committed protocol")


def test_the_content_hash_and_sealed_template_are_not_case_checks(tagged: Path) -> None:
    """A case brings content the tag never saw: the tagged experiment changing does not touch a case run."""
    models = load_experiment("placeholder", tagged / "experiment").models
    write(tagged, "experiment/placeholder/dossier.toml", "this would not even load = = \n")
    assert case_gate(tagged, models=models) == ()


def test_a_dry_run_notes_the_container(tagged: Path) -> None:
    models = load_experiment("placeholder", tagged / "experiment").models
    result = run_case_gate(
        LABEL,
        CONTENT,
        probes(T0 + HOUR),
        admitted_finding(),
        models,
        MAIN,
        LAPTOP,
        require_container=False,
        package_dir=tagged / PKG,
    )
    assert result.ok and result.notes == ("not in the container (dry run)",)


def test_check_case_official_raises_one_line_per_failure(tagged: Path) -> None:
    models = load_experiment("placeholder", tagged / "experiment").models
    with pytest.raises(SweepRefusal) as caught:
        check_case_official(
            LABEL, CONTENT, [], admitted_finding(), models, MAIN, LAPTOP, package_dir=tagged / PKG
        )
    assert str(caught.value).splitlines() == [
        f"{CASE_REFUSED}: case {LABEL} has no recognition probe",
        f"{CASE_REFUSED}: official sweeps run only in the container, never on a laptop",
    ]


def test_the_case_mode_loads_without_the_analysis_libraries() -> None:
    code = (
        "import sys\n"
        "class Block:\n"
        "    def find_spec(self, name, path=None, target=None):\n"
        "        if name.split('.')[0] in {'numpy', 'scipy', 'statsmodels'}:\n"
        "            raise ImportError('blocked: ' + name)\n"
        "sys.meta_path.insert(0, Block())\n"
        "import horizon_compact.protocol.cases\n"
        "print('loaded')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
