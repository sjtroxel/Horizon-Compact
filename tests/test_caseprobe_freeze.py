"""``hc case freeze`` (exploratory IMPLEMENTATION doc §3.1, steps 14a and 14b) on fakes: a fake bucket,
fake CI runs and probe objects, fake git, a made-up term. Every label, byte of content and time here is
invented; no real case is read, and nothing touches S3, GitHub or AWS."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from botocore.exceptions import ClientError

from horizon_compact import cli
from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.exploratory import (
    ExploratoryLog,
    write_exploratory_version,
)
from horizon_compact.casebuild.search import (
    CRITERIA,
    ReaderReply,
    Row,
    SelectionLog,
    write_log_version,
)
from horizon_compact.caseprobe import freeze as freeze_module
from horizon_compact.caseprobe.freeze import (
    EVIDENCE_DIR,
    FREEZE_FILE,
    OUTPUT_FILES,
    FreezeError,
    FreezeReaders,
    Frozen,
    build_freeze,
    case_decision_objects,
    write_freeze,
)
from horizon_compact.caseprobe.github import GithubReadError
from horizon_compact.caseprobe.layout import CONTENT_FILES, call_key, content_key
from horizon_compact.cli import CLEAN_EXIT, REFUSED_EXIT, main
from horizon_compact.privacy.guard import GuardError
from horizon_compact.privacy.names import TermFile, compile_term
from horizon_compact.protocol.cases import (
    CaseContent,
    CiRun,
    ProbeRecord,
    case_lock_text,
    content_hashes,
)
from test_casebuild_exploratory import day, take
from test_casebuild_frozen import fake_git
from test_caseprobe import FakeBucket

ROOT = Path(__file__).resolve().parents[1]
T0 = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)
HOUR = timedelta(hours=1)
MODELS = ("gpt-oss-openrouter", "haiku-5-5")  # the two models of experiment/protocol/prereg.lock
LABELS = ("closure-01", "closure-02", "closure-03", "closure-04", "pre-05")
COARSENED = "closure-02"  # the one case with a probe set 2
CONCERNS = "closure-03"  # the one case whose scenario reading needed his resolution
RELEASED = date(2026, 10, 26)
CANARY = "Canary Works"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def content_of(label: str, tag: str = "") -> CaseContent:
    return CaseContent(
        f"dossier of {label}{tag}\n".encode(),
        f"scenario of {label}\n".encode(),
        f"rubric of {label}\n".encode(),
    )


def terms(*words: str) -> TermFile:
    return TermFile(
        terms=tuple(compile_term(word, ignore_case=False) for word in words),
        allows=(),
        longlist=Path("none"),
        longlist_sha256="0" * 64,
    )


@dataclass
class World:
    repo: Path
    app: Path
    search: CaseAppendix
    bucket: FakeBucket
    runs: dict[str, list[CiRun]] = field(default_factory=dict)
    probes: dict[str, list[ProbeRecord]] = field(default_factory=dict)
    git: Any = None

    def readers(self) -> FreezeReaders:
        return FreezeReaders(
            store=self.bucket,
            probes=lambda label: self.probes[label],
            runs=lambda label: self.runs[label],
            git=self.git,
        )

    def case(self, label: str) -> CaseAppendix:
        return CaseAppendix(self.app, label)

    def evidence(self) -> Path:
        return self.repo / EVIDENCE_DIR


def _reader_files(case: CaseAppendix, *, concerns: bool) -> None:
    """The scenario's and rubric's reads, as ``hc case reader`` leaves them: a request naming the part hash
    and a usable reply; a "concerns" reading with his resolution beside it."""
    for kind, part, path, reading in (
        ("scenario", "Scenario", case.scenario_path, "concerns" if concerns else "neutral"),
        ("rubric", "Rubric", case.rubric_path, "agrees"),
    ):
        request = {"material_sha256": {part: sha(path.read_bytes())}}
        reply = {"usable": True, "parsed": {"reading": reading}}
        (case.directory / f"reader-{kind}-1-request.json").write_text(json.dumps(request))
        reply_path = case.directory / f"reader-{kind}-1-reply.json"
        reply_path.write_text(json.dumps(reply))
        if concerns and kind == "scenario":
            resolution = {"reply_sha256": sha(reply_path.read_bytes()), "resolution": "his call"}
            (case.directory / "reader-scenario-1-resolution.json").write_text(
                json.dumps(resolution)
            )


def _probe_objects(
    label: str, probe_set: int, at: datetime, *, passed: bool = True
) -> list[ProbeRecord]:
    return [
        ProbeRecord(
            call_key(label, probe_set, model, call),
            model,
            probe_set,
            passed,
            at + n * timedelta(minutes=1),
        )
        for n, (model, call) in enumerate((m, c) for m in MODELS for c in (1, 2, 3))
    ]


def _exploratory(*, released: bool) -> ExploratoryLog:
    log = ExploratoryLog()
    for n, label in enumerate(LABELS[:4]):
        log.add(label, "closure", "2", "window", f"0009999999-26-{n:06d}")
    log.add("pre-05", "closure", "3", "pre", "0009999999-26-000009")
    for n, label in enumerate(LABELS, start=1):
        take(log, label, n)
    if released:
        log.release_fill(RELEASED, "his reason, private")
    return log


def make_world(tmp_path: Path, *, released: bool = True, write_xlog: bool = True) -> World:
    repo, app = tmp_path / "repo", tmp_path / "app"
    (repo / "experiment" / "protocol").mkdir(parents=True)
    shutil.copy(ROOT / "experiment" / "protocol" / "prereg.lock", repo / "experiment" / "protocol")
    company = repo / "experiment" / "company"
    company.mkdir()
    for name in ("dossier.toml", "objectives.toml"):
        (company / name).write_text("")
    world = World(repo, app, CaseAppendix(app, "search"), FakeBucket(), git=fake_git())
    world.search.directory.mkdir(parents=True)
    write_log_version(world.search, SelectionLog({}))
    if write_xlog:
        write_exploratory_version(world.search, _exploratory(released=released))
    for label in LABELS:
        _build_case(world, label)
    return world


def _build_case(world: World, label: str) -> None:
    case = world.case(label)
    case.directory.mkdir(parents=True)
    coarsened = label == COARSENED
    first = content_of(label)
    final = content_of(label, ", coarsened") if coarsened else first
    case.dossier_path.write_bytes(first.dossier)
    case.scenario_path.write_bytes(first.scenario)
    case.rubric_path.write_bytes(first.rubric)
    probe_set = 2 if coarsened else 1
    if coarsened:
        case.dossier_path_for(2).parent.mkdir()
        case.dossier_path_for(2).write_bytes(final.dossier)
    _reader_files(case, concerns=label == CONCERNS)
    lock = case_lock_text(label, probe_set, content_hashes(final))
    path = world.repo / "experiment" / "cases" / label / "case.lock"
    path.parent.mkdir(parents=True)
    path.write_text(lock)
    for name, data in zip(
        CONTENT_FILES, (final.dossier, final.scenario, final.rubric), strict=True
    ):
        world.bucket.put_new(content_key(label, probe_set, name), data.decode())
    if coarsened:
        earlier = case_lock_text(label, 1, content_hashes(first))
        world.runs[label] = [CiRun("10", T0 - 2 * HOUR, earlier), CiRun("11", T0, lock)]
        world.probes[label] = _probe_objects(label, 1, T0 - HOUR, passed=False) + _probe_objects(
            label, 2, T0 + HOUR
        )
    else:
        world.runs[label] = [CiRun("20", T0, lock)]
        world.probes[label] = _probe_objects(label, 1, T0 + HOUR)


def run(world: World, term_file: TermFile | None = None) -> Frozen:
    return build_freeze(world.search, world.repo, world.readers(), term_file or terms(CANARY))


def refusal(world: World, term_file: TermFile | None = None) -> list[str]:
    with pytest.raises(FreezeError) as caught:
        run(world, term_file)
    assert not world.evidence().exists(), "a refusal writes nothing"
    return list(caught.value.reasons)


def has(reasons: Sequence[str], words: str) -> bool:
    return any(words in line for line in reasons)


# --- the happy path -----------------------------------------------------------------------------------------


def test_every_check_passing_gives_three_files_in_d1s_order(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    frozen = run(world)
    assert tuple(frozen.files) == OUTPUT_FILES
    assert frozen.cases == LABELS and all(frozen.admitted.values())
    record = json.loads(frozen.files[FREEZE_FILE])
    assert [c["label"] for c in record["cases"]] == list(LABELS)
    assert [c["filled"] for c in record["cases"]] == [False, False, True, True, True]
    assert [c["step"] for c in record["cases"]] == ["2", "2", "2", "2", "3"]
    assert record["cases"][0]["text"].startswith("exploratory: selected by §4.6.5 step 2")
    assert "knowledge probe" in record["cases"][4]["text"]  # a pool row carries the probe label too
    hashes = content_hashes(content_of("closure-01"))
    assert record["cases"][0]["rubric_sha256"] == hashes["rubric_sha256"]
    assert record["cases"][1]["probe_set"] == 2 and record["cases"][0]["probe_set"] == 1


def test_probe_results_are_counts_by_case_set_and_model_with_no_answer_text(tmp_path: Path) -> None:
    record = json.loads(run(make_world(tmp_path)).files[FREEZE_FILE])
    assert record["probes"]["closure-01"] == [
        {"set": 1, "model": "gpt-oss-openrouter", "calls": 3, "passed": 3},
        {"set": 1, "model": "haiku-5-5", "calls": 3, "passed": 3},
    ]
    assert [(p["set"], p["passed"]) for p in record["probes"][COARSENED]] == [
        (1, 0),
        (1, 0),
        (2, 3),
        (2, 3),
    ]


def test_the_order_findings_are_the_gates_own_records(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    record = json.loads(run(world).files[FREEZE_FILE])
    first = record["order"][0]
    assert first["label"] == "closure-01" and first["admitted"] is True and first["reasons"] == []
    assert first["rubric_run"] == "20" and first["first_probe"].startswith(
        "cases/closure-01/probes/"
    )
    coarsened = next(f for f in record["order"] if f["label"] == COARSENED)
    assert (
        coarsened["rubric_run"] == "10" and coarsened["content_run"] == "11"
    )  # the rubric before set 1


def test_reads_are_counts_by_reading_and_his_resolution_is_a_flag_not_text(tmp_path: Path) -> None:
    record = json.loads(run(make_world(tmp_path)).files[FREEZE_FILE])
    assert record["reads"]["scenario"] == {"concerns": 1, "neutral": 4}
    assert record["reads"]["rubric"] == {"agrees": 5}
    by_label = {c["label"]: c["reads"] for c in record["cases"]}
    assert by_label[CONCERNS]["scenario"] == {"reading": "concerns", "his_resolution": True}
    assert by_label["closure-01"]["scenario"] == {"reading": "neutral", "his_resolution": False}
    assert "his call" not in json.dumps(record)


def test_the_shortfall_by_type_and_the_holds_release_carry_no_reason(tmp_path: Path) -> None:
    record = json.loads(run(make_world(tmp_path)).files[FREEZE_FILE])
    assert record["shortfall"] == {
        "at_most": 5,
        "cases": 5,
        "cases_by_type": {"closure": 5, "retool": 0, "ai": 0},
        "short_by_type": {"closure": 0, "retool": 2, "ai": 1},
        "filled": 3,
    }
    assert record["hold"] == {"released": True, "on": RELEASED.isoformat()}
    assert "his reason" not in json.dumps(record)


def test_the_sources_are_the_logs_by_file_name_and_sha256(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    record = json.loads(run(world).files[FREEZE_FILE])
    assert [s["file"] for s in record["sources"]] == [
        "exploratory-log-1.json",
        "selection-log-1.json",
    ]
    for source in record["sources"]:
        assert source["sha256"] == sha((world.search.directory / source["file"]).read_bytes())


def test_the_public_views_are_the_logs_own_and_a_row_carries_no_date_or_accession(
    tmp_path: Path,
) -> None:
    world = make_world(tmp_path)
    frozen = run(world)
    directory = world.search.directory
    assert (
        frozen.files["exploratory-public.json"]
        == (directory / "exploratory-public-1.json").read_text()
    )
    assert (
        frozen.files["selection-public.json"] == (directory / "selection-public-1.json").read_text()
    )
    assert "0009999999" not in "".join(frozen.files.values())


def test_rejection_reads_are_counted_once_a_carried_copy_only_in_the_pre_registered_log() -> None:
    reply = ReaderReply("reader-x-1-reply.json", "b" * 64, "pass")
    old = SelectionLog(
        {"closure-07": Row("closure-07", "closure", "window", "0001111111-26-000009")}
    )
    old.record("closure-07", "first_disclosure", "pass", "r", disclosed=day(1))
    for criterion in CRITERIA[1:3]:
        old.record("closure-07", criterion, "pass", "r")
    old.record("closure-07", "real_decision", "fail", "a forced wind-down")
    old.record_read("closure-07", "real_decision", reply=reply, resolution="his call")
    log = ExploratoryLog()
    log.carry("closure-07", old.to_text(), "selection-log-1.json")
    log.add("closure-08", "closure", "2", "window", "0009999999-26-000001")
    log.record("closure-08", "first_disclosure", "pass", "r", disclosed=day(2))
    for criterion in CRITERIA[1:4]:
        log.record("closure-08", criterion, "pass", "r")
    log.record("closure-08", "maps_to_shape", "fail", "r")
    log.record_read(
        "closure-08", "maps_to_shape", reply=ReaderReply("reader-y-1-reply.json", "c" * 64, "fail")
    )
    counts = freeze_module._rejection_reads
    assert counts(old.rows.values(), lambda r, c: False) == {
        "real_decision": {"agrees": 0, "disputes": 1}
    }
    assert counts(log.rows.values(), freeze_module._carried_copy) == {
        "maps_to_shape": {"agrees": 1, "disputes": 0}
    }


# --- the written files --------------------------------------------------------------------------------------


def test_the_files_are_written_exactly_as_built_and_never_twice(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    frozen = run(world)
    written = write_freeze(world.repo, frozen)
    assert [p.name for p in written] == list(OUTPUT_FILES)
    for name in OUTPUT_FILES:
        assert (world.evidence() / name).read_text(encoding="utf-8") == frozen.files[name]
    assert sorted(p.name for p in world.evidence().iterdir()) == sorted(
        OUTPUT_FILES
    )  # no temporary left
    assert has(refusal_of_second(world, frozen), "already exists")


def refusal_of_second(world: World, frozen: Frozen) -> list[str]:
    with pytest.raises(FreezeError) as caught:
        write_freeze(world.repo, frozen)
    with pytest.raises(FreezeError) as again:
        run(world)
    assert list(again.value.reasons) == list(caught.value.reasons)
    return list(caught.value.reasons)


def test_a_write_that_fails_part_way_leaves_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    world = make_world(tmp_path)
    frozen = run(world)
    real = os.link
    calls: list[str] = []

    def failing(src: Any, dst: Any, **kwargs: Any) -> None:
        calls.append(str(dst))
        if len(calls) == 3:
            raise OSError(28, "No space left on device")
        real(src, dst, **kwargs)

    monkeypatch.setattr(os, "link", failing)
    with pytest.raises(FreezeError, match="nothing was kept"):
        write_freeze(world.repo, frozen)
    assert list(world.evidence().iterdir()) == []


# --- 14a item 1: the selections -----------------------------------------------------------------------------


def test_no_exploratory_log_refuses(tmp_path: Path) -> None:
    assert has(refusal(make_world(tmp_path, write_xlog=False)), "there is no exploratory log")


def test_a_hold_still_on_the_fill_leaves_the_selection_open_and_refuses(tmp_path: Path) -> None:
    reasons = refusal(make_world(tmp_path, released=False))
    assert has(reasons, "the exploratory log is not complete") and has(reasons, "slots are held")


def test_an_unread_rejection_is_a_problem_and_refuses(tmp_path: Path) -> None:
    world = make_world(tmp_path, write_xlog=False)
    log = _exploratory(released=True)
    log.add("closure-09", "closure", "2", "window", "0009999999-26-000020")
    log.record("closure-09", "first_disclosure", "pass", "r", disclosed=day(20))
    for criterion in CRITERIA[1:3]:
        log.record("closure-09", criterion, "pass", "r")
    log.record("closure-09", "real_decision", "fail", "r")
    write_exploratory_version(world.search, log)
    assert has(refusal(world), "closure-09: its rejection on real_decision has not been read")


def test_an_open_pre_registered_log_refuses(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    write_log_version(
        world.search, SelectionLog({"closure-01": Row("closure-01", "closure", "window", "x")})
    )
    assert has(refusal(world), "the pre-registered log is not complete (closure)")


# --- 14a item 2: each case ----------------------------------------------------------------------------------


def test_a_missing_case_record_is_named_for_its_case(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    (world.repo / "experiment" / "cases" / "closure-04" / "case.lock").unlink()
    assert has(refusal(world), "no case record: experiment/cases/closure-04/case.lock")


def test_a_lock_not_pushed_refuses_every_case(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    world.git = fake_git(status=" M experiment/cases/x/case.lock\n")
    reasons = refusal(world)
    assert sum("has uncommitted changes" in line for line in reasons) == len(LABELS)


def test_content_in_the_appendix_that_does_not_hash_to_the_lock_refuses(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    world.case("closure-01").dossier_path.write_bytes(b"changed\n")
    reasons = refusal(world)
    assert has(reasons, "the dossier does not hash to experiment/cases/closure-01/case.lock")
    assert len(reasons) == 1


def test_a_probe_set_2_case_is_checked_on_the_coarsened_dossier(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    world.case(COARSENED).dossier_path_for(2).write_bytes(b"changed\n")
    assert has(refusal(world), "the dossier does not hash")


def test_stored_content_that_differs_or_is_missing_refuses(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    key = content_key("closure-02", 2, "scenario.toml")
    world.bucket.objects[key] = ("changed\n", T0)
    del world.bucket.objects[content_key("closure-01", 1, "rubric.toml")]
    reasons = refusal(world)
    assert has(
        reasons,
        "in storage, the scenario text does not hash to experiment/cases/closure-02/case.lock",
    )
    assert has(reasons, "closure-01: set 1 is not in storage: rubric.toml")


def test_a_ci_run_after_the_first_probe_is_an_order_failure(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    run_ = world.runs["pre-05"][0]
    world.runs["pre-05"] = [CiRun(run_.run_id, T0 + 2 * HOUR, run_.record_text)]
    reasons = refusal(world)
    assert has(reasons, "pre-05's rubric was first in CI at") and has(
        reasons, "not before its first probe"
    )


def test_a_case_with_no_ci_run_holding_its_record_refuses(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    world.runs["closure-03"] = []
    assert has(
        refusal(world), "no GitHub Actions run on a commit holding case closure-03's rubric hash"
    )


def test_a_failed_probe_call_refuses_and_names_the_call(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    failed = world.probes["closure-01"][4]
    world.probes["closure-01"][4] = ProbeRecord(
        failed.key, failed.model_key, 1, False, failed.last_modified
    )
    assert has(refusal(world), f"haiku-5-5 failed the recognition probe ({failed.key})")


def test_a_model_short_of_three_calls_refuses(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    del world.probes["closure-04"][0]
    assert has(refusal(world), "closure-04: gpt-oss-openrouter has 2 probe calls in set 1, not 3")


def test_a_scenario_or_rubric_with_no_usable_read_refuses(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    (world.case("closure-01").directory / "reader-rubric-1-reply.json").unlink()
    assert has(refusal(world), "the rubric as it stands has no usable independent read")


def test_a_concerns_reading_without_his_resolution_refuses(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    (world.case(CONCERNS).directory / "reader-scenario-1-resolution.json").unlink()
    assert has(refusal(world), "no resolution of his")


@pytest.mark.parametrize(
    "failure",
    [
        GithubReadError("gh api failed"),
        ClientError({"Error": {"Code": "ExpiredToken"}}, "ListObjectsV2"),
    ],
)
def test_a_reader_that_cannot_answer_refuses_instead_of_crashing(
    tmp_path: Path, failure: Exception
) -> None:
    world = make_world(tmp_path)

    def broken(label: str) -> list[CiRun]:
        raise failure

    readers = FreezeReaders(world.bucket, lambda label: world.probes[label], broken, world.git)
    with pytest.raises(FreezeError) as caught:
        build_freeze(world.search, world.repo, readers, terms(CANARY))
    assert has(caught.value.reasons, "cannot read the CI runs or the probe records")
    assert not has(caught.value.reasons, "no GitHub Actions run")  # no check ran on nothing


def test_a_bucket_that_cannot_answer_for_the_stored_content_refuses_instead_of_crashing(
    tmp_path: Path,
) -> None:
    world = make_world(tmp_path)

    class Expired(FakeBucket):
        def get(self, key: str) -> str | None:
            raise ClientError({"Error": {"Code": "ExpiredToken"}}, "GetObject")

    expired = Expired()
    expired.objects = world.bucket.objects
    readers = FreezeReaders(
        expired, lambda label: world.probes[label], lambda label: world.runs[label], world.git
    )
    with pytest.raises(FreezeError) as caught:
        build_freeze(world.search, world.repo, readers, terms(CANARY))
    assert has(caught.value.reasons, "closure-01: cannot read set 1 from storage: ClientError")


def test_no_protocol_lock_refuses(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    (world.repo / "experiment" / "protocol" / "prereg.lock").unlink()
    assert has(refusal(world), "no committed protocol")


# --- 14a item 3: no case decision has run -------------------------------------------------------------------


def objects(*keys: str) -> FakeBucket:
    bucket = FakeBucket()
    for key in keys:
        bucket.put_new(key, "{}")
    return bucket


def test_the_grids_and_the_placeholders_sweeps_are_not_a_case_decision() -> None:
    bucket = objects(
        "official/company/sw-1/manifest.json",
        "official/company/awareness/sw-2/runs/r-0123456789ab/final.json",
        "development/placeholder/sw-3/manifest.json",
        "pilot/company/sw-4/manifest.json",
        "cases/closure-01/set-1/dossier.toml",
        "cases/closure-01/probes/set-1/haiku-5-5/call-1.json",
    )
    assert case_decision_objects(bucket, list(LABELS), {"company", "placeholder"}) == []


@pytest.mark.parametrize(
    ("key", "role"),
    [
        ("official/some-case-experiment/sw-1/manifest.json", "official/"),
        ("development/company/closure-03-run/manifest.json", "development/"),
        ("pilot/company/sw-1/runs/pre-05/final.json", "pilot/"),
        ("official/readme.txt", "official/"),
    ],
)
def test_an_object_outside_the_repositorys_experiments_or_naming_a_case_is_one(
    key: str, role: str
) -> None:
    reasons = case_decision_objects(objects(key), list(LABELS), {"company", "placeholder"})
    assert len(reasons) == 1 and f"1 object(s) under {role}" in reasons[0]
    assert "a case decision may have run" in reasons[0]


def test_a_label_inside_another_word_is_not_a_case_name() -> None:
    bucket = objects("official/company/sw-closure-011/manifest.json", "official/company/pre-050/x")
    assert case_decision_objects(bucket, list(LABELS), {"company"}) == []


def test_a_case_decision_in_the_bucket_refuses_the_freeze(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    world.bucket.put_new("official/closure-01/sw-1/manifest.json", "{}")
    assert has(refusal(world), "1 object(s) under official/")


# --- 14b: names and write-once ------------------------------------------------------------------------------


def test_a_term_in_what_would_be_written_refuses_with_the_file_and_line_never_the_term(
    tmp_path: Path,
) -> None:
    reasons = refusal(make_world(tmp_path), terms("Haiku"))
    assert has(reasons, "freeze.json line") and has(reasons, "exploratory-public.json line")
    assert all("Haiku" not in line for line in reasons)


def test_an_existing_freeze_is_refused_before_anything_is_read(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    world.evidence().mkdir(parents=True)
    (world.evidence() / FREEZE_FILE).write_text("{}")

    def never(label: str) -> list[Any]:
        raise AssertionError("a reader was called")

    readers = FreezeReaders(world.bucket, never, never, world.git)
    with pytest.raises(FreezeError, match=r"freeze\.json already exists: the freeze is write-once"):
        build_freeze(world.search, world.repo, readers, terms(CANARY))


def test_every_reason_is_reported_together_and_nothing_is_written(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    world.case("closure-01").dossier_path.write_bytes(b"changed\n")
    world.runs["closure-03"] = []
    world.probes["pre-05"] = world.probes["pre-05"][:5]
    world.bucket.put_new("pilot/elsewhere/sw-1/manifest.json", "{}")
    reasons = refusal(world)
    assert len(reasons) >= 4
    assert has(reasons, "the dossier does not hash to experiment/cases/closure-01/case.lock")
    assert has(reasons, "closure-03's rubric hash")
    assert has(reasons, "pre-05: haiku-5-5 has 2 probe calls")
    assert has(reasons, "1 object(s) under pilot/")
    message = str(FreezeError(reasons))
    assert message.count("refused: ") == len(reasons) - 1  # cmd_case prefixes the first


# --- the command --------------------------------------------------------------------------------------------


def command(
    monkeypatch: pytest.MonkeyPatch,
    world: World,
    term_file: TermFile | Callable[[], TermFile] | None = None,
) -> int:
    monkeypatch.setenv("HC_APPENDIX_DIR", str(world.app))
    monkeypatch.setattr(cli, "default_repo_root", lambda: world.repo)
    monkeypatch.setattr(cli, "_freeze_world", lambda args, root: world.readers())
    monkeypatch.setattr(
        cli,
        "load_configured_term_file",
        term_file if callable(term_file) else (lambda: term_file or terms(CANARY)),
    )
    return main(["case", "freeze", "--profile", "dev"])


def test_the_command_writes_the_evidence_and_prints_labels_and_file_names_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = make_world(tmp_path)
    assert command(monkeypatch, world) == CLEAN_EXIT
    captured = capsys.readouterr()
    for label in LABELS:
        assert f"{label}: order admitted: True" in captured.out
    for name in OUTPUT_FILES:
        assert f"wrote {EVIDENCE_DIR}/{name}" in captured.out
        assert (world.evidence() / name).is_file()
    assert "checking closure-01" in captured.err and "case decision" in captured.err
    assert CANARY not in captured.out + captured.err


def test_the_command_refuses_with_every_reason_on_its_own_line_and_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = make_world(tmp_path)
    world.runs["closure-03"] = []
    world.bucket.put_new("pilot/elsewhere/sw-1/manifest.json", "{}")
    assert command(monkeypatch, world) == REFUSED_EXIT
    refused = [
        line for line in capsys.readouterr().err.splitlines() if line.startswith("refused: ")
    ]
    assert len(refused) == 3  # the rubric run, the content run, the sweep prefix
    assert not world.evidence().exists()


def test_the_command_needs_the_term_file_and_refuses_without_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def missing() -> TermFile:
        raise GuardError("no term file is configured")

    assert command(monkeypatch, make_world(tmp_path), missing) == REFUSED_EXIT
    assert "the name check before writing needs the term file" in capsys.readouterr().err


def test_the_command_needs_a_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = make_world(tmp_path)
    monkeypatch.setenv("HC_APPENDIX_DIR", str(world.app))
    monkeypatch.setattr(cli, "default_repo_root", lambda: world.repo)
    monkeypatch.setattr(cli, "load_configured_term_file", lambda: terms(CANARY))
    assert main(["case", "freeze"]) == REFUSED_EXIT
    assert "--profile is required" in capsys.readouterr().err
    assert not world.evidence().exists()


def test_the_worlds_gh_listing_is_fetched_once_for_all_cases(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_runner(program: str, cwd: Path | None = None) -> Callable[[Sequence[str]], str]:
        def run_(args: Sequence[str]) -> str:
            calls.append((program, *args))
            if program == "gh":
                return json.dumps(
                    {"id": 1, "created_at": "2026-10-20T12:00:00Z", "head_sha": "a" * 40}
                )
            return "case_version = 1\n"

        return run_

    client = SimpleNamespace()
    monkeypatch.setattr(cli, "command_runner", fake_runner)
    monkeypatch.setattr(cli, "_case_s3", lambda args: (client, "bucket"))
    readers = cli._freeze_world(argparse.Namespace(), tmp_path)
    for label in LABELS:
        assert len(readers.runs(label)) == 1
    assert sum(1 for call in calls if call[0] == "gh") == 1
    assert sum(1 for call in calls if call[0] == "git") == len(LABELS)
