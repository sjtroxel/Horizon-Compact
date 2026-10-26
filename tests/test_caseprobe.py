"""A real case's recognition probe, on fake S3, fake GitHub and fake providers (search-half doc §4.8, §4.10;
Stage C step 10a): upload, the container's probe run, the verdict (and a reader's dispute of a criterion 5
failure), the S3 probe reader and the GitHub reader. No model is called, no key is read, no AWS call is made.
Fictional canaries only."""

from __future__ import annotations

import argparse
import io
import json
import random
import tomllib
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from horizon_compact import cli
from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.frozen import FrozenInputsError
from horizon_compact.casebuild.search import Row, SelectionLog, write_log_version
from horizon_compact.caseprobe.github import (
    RUNS_ARGS,
    GithubReadError,
    command_runner,
    read_ci_runs,
)
from horizon_compact.caseprobe.layout import (
    PROBE_MAX_TOKENS,
    PROBE_MESSAGE,
    call_key,
    content_key,
    error_key,
    parse_call_key,
    verdict_key,
)
from horizon_compact.caseprobe.run import ProbeRefused, run_case_probe
from horizon_compact.caseprobe.s3reader import read_probe_records
from horizon_compact.caseprobe.upload import UploadError, upload_case
from horizon_compact.caseprobe.verdict import (
    VerdictError,
    is_unknown,
    probe_verdict,
)
from horizon_compact.cli import CLEAN_EXIT, REFUSED_EXIT, main
from horizon_compact.dossier.check import default_repo_root
from horizon_compact.model_config import ModelConfig, ModelsFile
from horizon_compact.protocol.cases import (
    CaseContent,
    case_lock_text,
    case_path,
    check_case_order,
    check_case_probes,
    content_hashes,
    parse_case,
)
from horizon_compact.providers.base import RawDecision
from horizon_compact.reader.read import probe_reply_on_record, rejection_reply_on_record
from horizon_compact.sweep.identity import RunnerIdentity
from test_casebuild_extract import PROVENANCE, ok
from test_casebuild_frozen import fake_git
from test_reader import Replies, run_reader, says

ROOT = default_repo_root()
LABEL = "closure-1"
CANARY = "Fernwick Canary Holdings"
TICKER = "FCNH"
ACCOUNT = "123456789012"
DOSSIER = 'text = "A maker of cages in the Midwest region."\n'
SCENARIO = 'text = "The Company decides about a plant."\n'
RUBRIC = "choice = 'close'\n"
MODELS = ModelsFile.model_validate(
    tomllib.loads((ROOT / "experiment" / "models.toml").read_text(encoding="utf-8"))
)
HAIKU = MODELS.models["haiku-5-5"]
GPT = MODELS.models["gpt-oss-openrouter"]
CONTAINER = RunnerIdentity("fargate", "sha256:" + "b" * 64, "img", "task-1", "deadbeef", False)
LAPTOP = RunnerIdentity("laptop", None, None, None, "deadbeef", False)
PROBE_FAIL = {
    "criterion": "not_recognizable",
    "reading": "fail",
    "shape": None,
    "reason": "Answer 1 names it.",
    "alternative": None,
}
PROBE_PASS = {**PROBE_FAIL, "reading": "pass", "reason": "Answer 1 does not name it."}
PROBE_UNSURE = {**PROBE_FAIL, "reading": "cannot_tell"}


@pytest.fixture(autouse=True)
def _appendix_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HC_APPENDIX_DIR", str(tmp_path / "appendix"))


# --- a fake bucket: the Store protocol and the little of boto3's S3 client the readers use --------


class _NoSuchKey(Exception):
    pass


class _Pages:
    def __init__(self, bucket: FakeBucket) -> None:
        self.bucket = bucket

    def paginate(self, *, Bucket: str, Prefix: str) -> list[dict[str, Any]]:
        keys = sorted(k for k in self.bucket.objects if k.startswith(Prefix))
        return [{"Contents": [{"Key": k, "LastModified": self.bucket.objects[k][1]} for k in keys]}]


class FakeBucket:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[str, datetime]] = {}
        self.exceptions = SimpleNamespace(NoSuchKey=_NoSuchKey)
        self.puts: list[str] = []
        self._clock = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)

    def put_new(self, key: str, text: str) -> bool:
        if key in self.objects:
            return False
        self._clock += timedelta(minutes=1)
        self.objects[key] = (text, self._clock)
        self.puts.append(key)
        return True

    def get(self, key: str) -> str | None:
        return self.objects[key][0] if key in self.objects else None

    def list_keys(self, prefix: str) -> list[str]:
        return sorted(k for k in self.objects if k.startswith(prefix))

    def get_paginator(self, name: str) -> _Pages:
        assert name == "list_objects_v2"
        return _Pages(self)

    def get_object(self, *, Bucket: str, Key: str) -> dict[str, Any]:
        if Key not in self.objects:
            raise _NoSuchKey(Key)
        return {"Body": io.BytesIO(self.objects[Key][0].encode("utf-8"))}


# --- a repository with a pushed lock, an appendix with the three files ----------------------------


def locked(
    tmp_path: Path, *, probe_set: int = 1, dossier: str = DOSSIER
) -> tuple[Path, CaseAppendix]:
    repo = tmp_path / "repo"
    case = CaseAppendix(tmp_path / "appendix", LABEL)
    case.dossier_path_for(probe_set).parent.mkdir(parents=True, exist_ok=True)
    for path, text in (
        (case.dossier_path_for(probe_set), dossier),
        (case.scenario_path, SCENARIO),
        (case.rubric_path, RUBRIC),
    ):
        path.write_text(text, encoding="utf-8")
    case.terms_path.write_text(
        f"term: {CANARY} => the Company\nterm: {TICKER} => the ticker\n", encoding="utf-8"
    )
    lock = repo / case_path(LABEL)
    lock.parent.mkdir(parents=True, exist_ok=True)
    content = CaseContent(dossier.encode(), SCENARIO.encode(), RUBRIC.encode())
    lock.write_text(case_lock_text(LABEL, probe_set, content_hashes(content)), encoding="utf-8")
    return repo, case


def uploaded(tmp_path: Path, bucket: FakeBucket, **kwargs: Any) -> tuple[Path, CaseAppendix]:
    repo, case = locked(tmp_path, **kwargs)
    upload_case(case, repo, probe_set=kwargs.get("probe_set", 1), git=fake_git(), store=bucket)  # type: ignore[arg-type]
    return repo, case


# --- the layout -----------------------------------------------------------------------------------


def test_the_probe_message_is_the_protocols_word_for_word() -> None:
    protocol = (ROOT / "experiment" / "protocol" / "protocol-v1.md").read_text(encoding="utf-8")
    section = protocol.split("### 12.8")[1].split("### 12.9")[0]
    assert f"> {PROBE_MESSAGE}\n" in section
    assert PROBE_MESSAGE == "Which company is this? If you are not sure, say unknown."


def test_keys_round_trip_and_only_a_call_object_parses_as_one() -> None:
    key = call_key(LABEL, 2, "haiku-5-5", 3)
    assert key == "cases/closure-1/probes/set-2/haiku-5-5/call-3.json"
    parsed = parse_call_key(key)
    assert parsed is not None and (
        parsed.label,
        parsed.probe_set,
        parsed.model_key,
        parsed.call,
    ) == (
        LABEL,
        2,
        "haiku-5-5",
        3,
    )
    for other in (
        verdict_key(LABEL, 2, "haiku-5-5", 3),
        error_key(LABEL, 2, "haiku-5-5", 3, 1),
        content_key(LABEL, 2, "dossier.toml"),
    ):
        assert parse_call_key(other) is None, other


@pytest.mark.parametrize("bad", ["../x", "Closure", "a/b", ""])
def test_a_label_that_is_not_one_folder_name_is_refused(bad: str) -> None:
    with pytest.raises(ValueError, match="not a case label"):
        call_key(bad, 1, "haiku-5-5", 1)


@pytest.mark.parametrize("bad", ["../x", "a/b", "", "-x"])
def test_a_model_key_that_is_not_one_path_part_is_refused(bad: str) -> None:
    with pytest.raises(ValueError, match="not a model key"):
        call_key(LABEL, 1, bad, 1)


# --- upload ---------------------------------------------------------------------------------------


def test_upload_puts_the_three_files_write_once_after_checking_the_pushed_lock(
    tmp_path: Path,
) -> None:
    repo, case = locked(tmp_path)
    bucket = FakeBucket()
    git = fake_git()
    done = upload_case(case, repo, probe_set=1, git=git, store=bucket)  # type: ignore[arg-type]
    assert (
        done.written == ("dossier.toml", "scenario.toml", "rubric.toml") and not done.already_there
    )
    assert bucket.get(content_key(LABEL, 1, "dossier.toml")) == DOSSIER
    assert bucket.get(content_key(LABEL, 1, "rubric.toml")) == RUBRIC
    assert ["branch", "-r", "--contains", "a" * 40] in git.calls  # type: ignore[attr-defined]
    again = upload_case(case, repo, probe_set=1, git=fake_git(), store=bucket)  # type: ignore[arg-type]
    assert not again.written and len(again.already_there) == 3 and len(bucket.puts) == 3


@pytest.mark.parametrize(
    ("git_kwargs", "words"),
    [
        ({"status": " M experiment/cases/closure-1/case.lock\n"}, "uncommitted"),
        ({"commit": ""}, "is not committed"),
        ({"remotes": ""}, "not on any remote branch"),
    ],
)
def test_upload_refuses_a_lock_that_is_not_committed_and_pushed(
    tmp_path: Path, git_kwargs: dict[str, str], words: str
) -> None:
    repo, case = locked(tmp_path)
    bucket = FakeBucket()
    with pytest.raises(FrozenInputsError, match=words):
        upload_case(case, repo, probe_set=1, git=fake_git(**git_kwargs), store=bucket)  # type: ignore[arg-type]
    assert bucket.puts == []


def test_upload_refuses_content_that_does_not_hash_to_the_lock_a_wrong_set_and_no_lock(
    tmp_path: Path,
) -> None:
    repo, case = locked(tmp_path)
    bucket = FakeBucket()
    case.dossier_path.write_text(DOSSIER + "# edited\n", encoding="utf-8")
    with pytest.raises(UploadError, match="the dossier does not hash to"):
        upload_case(case, repo, probe_set=1, git=fake_git(), store=bucket)  # type: ignore[arg-type]
    with pytest.raises(UploadError, match="is for probe set 1, not 2"):
        upload_case(case, repo, probe_set=2, git=fake_git(), store=bucket)  # type: ignore[arg-type]
    (repo / case_path(LABEL)).unlink()
    with pytest.raises(UploadError, match="no case record"):
        upload_case(case, repo, probe_set=1, git=fake_git(), store=bucket)  # type: ignore[arg-type]
    assert bucket.puts == []


def test_upload_never_replaces_a_stored_object_and_writes_nothing_when_one_differs(
    tmp_path: Path,
) -> None:
    repo, case = locked(tmp_path)
    bucket = FakeBucket()
    bucket.put_new(content_key(LABEL, 1, "scenario.toml"), "something else\n")
    bucket.puts.clear()
    with pytest.raises(UploadError, match=r"scenario\.toml is already stored"):
        upload_case(case, repo, probe_set=1, git=fake_git(), store=bucket)  # type: ignore[arg-type]
    assert (
        bucket.puts == []
        and bucket.get(content_key(LABEL, 1, "scenario.toml")) == "something else\n"
    )


# --- the container's probe run --------------------------------------------------------------------


def probe(
    bucket: FakeBucket,
    provider: Replies,
    repo: Path,
    *,
    model_key: str = "haiku-5-5",
    config: ModelConfig = HAIKU,
    identity: RunnerIdentity = CONTAINER,
    cap_usd: float = 2.0,
    probe_set: int = 1,
    sleep: Callable[[float], None] = lambda s: None,
    **kwargs: Any,
) -> Any:
    return run_case_probe(
        label=LABEL,
        probe_set=probe_set,
        model_key=model_key,
        config=config,
        pace_fraction=1.0,
        repo_root=repo,
        provider=provider,
        store=bucket,
        identity=identity,
        account_id=ACCOUNT,
        cap_usd=cap_usd,
        harness_version="test",
        sleep=sleep,
        rng=random.Random(1),
        **kwargs,
    )


def api_error(code: str = "ThrottlingException") -> RawDecision:
    return RawDecision(
        status="api_error", provenance=PROVENANCE, error={"code": code, "message": "m"}
    )


def test_a_probe_makes_three_calls_with_the_dossier_as_system_and_the_message_as_user(
    tmp_path: Path,
) -> None:
    bucket = FakeBucket()
    repo, _ = uploaded(tmp_path, bucket)
    provider = Replies(ok("unknown"), ok("Unknown."), ok("Possibly a cage maker."))
    result = probe(bucket, provider, repo)
    assert result.stopped == "complete" and result.clean and result.calls_done_now == 3
    assert len(provider.requests) == 3
    for request in provider.requests:
        assert (request.system, request.user, request.max_tokens) == (
            DOSSIER,
            PROBE_MESSAGE,
            PROBE_MAX_TOKENS,
        )
        assert list(vars(request)) == ["route", "system", "user", "max_tokens"]
    stored = [json.loads(bucket.objects[call_key(LABEL, 1, "haiku-5-5", n)][0]) for n in (1, 2, 3)]
    assert [r["answer"] for r in stored] == ["unknown", "Unknown.", "Possibly a cage maker."]
    first = stored[0]
    assert first["image_digest"] == CONTAINER.image_digest and first["runner"] == "fargate"
    assert (
        first["kind"] == "case-probe" and first["status"] == "replied" and first["probe_set"] == 1
    )
    assert first["model_key"] == "haiku-5-5" and first["usage"]["input_tokens"] == 10
    assert len(first["case_lock_sha256"]) == 64 and len(first["prompt_sha256"]) == 64


def test_a_re_run_resumes_and_never_repeats_a_call(tmp_path: Path) -> None:
    bucket = FakeBucket()
    repo, _ = uploaded(tmp_path, bucket)
    probe(
        bucket,
        Replies(ok("unknown"), ok("unknown")),
        repo,
        should_stop=iter([False, False, True]).__next__,
    )
    assert sorted(parse_call_key(k).call for k in bucket.objects if parse_call_key(k)) == [1, 2]  # type: ignore[union-attr]
    provider = Replies(ok("unknown"))
    result = probe(bucket, provider, repo)
    assert (
        result.calls_done_before == 2 and result.calls_done_now == 1 and len(provider.requests) == 1
    )
    assert probe(bucket, Replies(), repo).api_calls_now == 0  # all three exist: nothing is called


def test_a_reply_is_never_retried_whatever_it_says(tmp_path: Path) -> None:
    bucket = FakeBucket()
    repo, _ = uploaded(tmp_path, bucket)
    provider = Replies(ok("Fern", stop="max_tokens"), ok(""), ok("unknown"))
    probe(bucket, provider, repo)
    statuses = [
        json.loads(bucket.objects[call_key(LABEL, 1, "haiku-5-5", n)][0])["status"]
        for n in (1, 2, 3)
    ]
    assert statuses == ["truncated", "no_text", "replied"] and len(provider.requests) == 3


def test_an_api_error_is_retried_with_backoff_and_kept_but_not_counted_as_an_answer(
    tmp_path: Path,
) -> None:
    bucket = FakeBucket()
    repo, _ = uploaded(tmp_path, bucket)
    slept: list[float] = []
    provider = Replies(api_error(), api_error(), ok("unknown"), ok("unknown"), ok("unknown"))
    result = probe(bucket, provider, repo, sleep=slept.append)
    assert result.stopped == "complete" and result.api_calls_now == 5
    kept = [k for k in bucket.objects if "/errors/" in k]
    assert kept == [error_key(LABEL, 1, "haiku-5-5", 1, 1), error_key(LABEL, 1, "haiku-5-5", 1, 2)]
    assert json.loads(bucket.objects[kept[0]][0])["kind"] == "case-probe-api-error"
    assert any(s > 0 for s in slept)
    assert [r for r in bucket.objects if parse_call_key(r)].__len__() == 3


def test_an_error_that_will_not_clear_stops_the_run_and_too_many_in_a_row_stop_it(
    tmp_path: Path,
) -> None:
    bucket = FakeBucket()
    repo, _ = uploaded(tmp_path, bucket)
    assert (
        probe(bucket, Replies(api_error("AccessDeniedException")), repo).stopped == "config_error"
    )
    many = Replies(*[api_error() for _ in range(10)])
    result = probe(bucket, many, repo)
    assert result.stopped == "api_errors" and not result.clean


@pytest.mark.parametrize(
    ("kwargs", "words"),
    [
        ({"identity": LAPTOP}, "in the container only"),
        ({"model_key": "nova-lite", "config": MODELS.models["nova-lite"]}, "role 'development'"),
        ({"model_key": "sonnet-4-6", "config": MODELS.models["sonnet-4-6"]}, "role 'reserve'"),
        ({"cap_usd": 0.0001}, "above the cap"),
        ({"probe_set": 2}, "is for probe set 1, not 2"),
    ],
)
def test_a_probe_refuses_before_any_call(
    tmp_path: Path, kwargs: dict[str, Any], words: str
) -> None:
    bucket = FakeBucket()
    repo, _ = uploaded(tmp_path, bucket)
    provider = Replies()
    with pytest.raises(ProbeRefused, match=words):
        probe(bucket, provider, repo, **kwargs)
    assert provider.requests == []


def test_a_probe_refuses_a_missing_or_changed_content_a_missing_lock_and_an_unpinned_router(
    tmp_path: Path,
) -> None:
    bucket = FakeBucket()
    repo, _ = locked(tmp_path)
    with pytest.raises(ProbeRefused, match="run `hc case upload` first"):
        probe(bucket, Replies(), repo)
    bucket.put_new(content_key(LABEL, 1, "dossier.toml"), DOSSIER + "# changed\n")
    bucket.put_new(content_key(LABEL, 1, "scenario.toml"), SCENARIO)
    bucket.put_new(content_key(LABEL, 1, "rubric.toml"), RUBRIC)
    with pytest.raises(ProbeRefused, match="the dossier does not hash to"):
        probe(bucket, Replies(), repo)
    (repo / case_path(LABEL)).unlink()
    with pytest.raises(ProbeRefused, match="the image must carry the case record"):
        probe(bucket, Replies(), repo)
    unpinned = GPT.model_copy(update={"openrouter_provider": None})
    with pytest.raises(ProbeRefused, match="no pinned provider"):
        probe(bucket, Replies(), repo, model_key="gpt-oss-openrouter", config=unpinned)


def test_an_openrouter_model_is_asked_on_its_pinned_route(tmp_path: Path) -> None:
    bucket = FakeBucket()
    repo, _ = uploaded(tmp_path, bucket)
    provider = Replies(ok("unknown"), ok("unknown"), ok("unknown"))
    probe(bucket, provider, repo, model_key="gpt-oss-openrouter", config=GPT)
    route = provider.requests[0].route
    assert route.route_kind == "openrouter" and route.pinned_provider == GPT.openrouter_provider
    assert bucket.get(call_key(LABEL, 1, "gpt-oss-openrouter", 3)) is not None


# --- the verdict ----------------------------------------------------------------------------------


def put_calls(
    bucket: FakeBucket, answers: list[str], *, model: str = "haiku-5-5", probe_set: int = 1
) -> None:
    for n, answer in enumerate(answers, start=1):
        record = {"answer": answer, "status": "replied", "call": n}
        bucket.put_new(call_key(LABEL, probe_set, model, n), json.dumps(record))


def verdict(
    case: CaseAppendix,
    bucket: FakeBucket,
    replies: list[str],
    *,
    probe_set: int = 1,
    resolution: str | None = None,
) -> tuple[Any, list[str], list[str]]:
    asked: list[str] = []
    shown: list[str] = []
    queue = list(replies)

    def ask(prompt: str) -> str:
        asked.append(prompt)
        return queue.pop(0)

    done = probe_verdict(
        case,
        bucket,
        probe_set=probe_set,
        resolution=resolution,
        today=date(2026, 10, 21),
        ask=ask,
        show=shown.append,
    )
    return done, asked, shown


def verdicts(
    bucket: FakeBucket, model: str = "haiku-5-5", probe_set: int = 1
) -> list[dict[str, Any]]:
    return [
        json.loads(bucket.objects[verdict_key(LABEL, probe_set, model, n)][0]) for n in (1, 2, 3)
    ]


@pytest.mark.parametrize(
    ("answer", "expected"),
    [("unknown", True), ("Unknown.", True), ("  **UNKNOWN**\n", True), ("unknown company", False),
     ("I don't know", False), ("", False), (f"{CANARY}", False)],
)  # fmt: skip
def test_only_the_word_unknown_skips_the_human_read(answer: str, expected: bool) -> None:
    assert is_unknown(answer) is expected


def test_when_no_answer_names_the_company_every_call_passes_and_he_is_asked_only_about_the_rest(
    tmp_path: Path,
) -> None:
    bucket = FakeBucket()
    _, case = locked(tmp_path)
    put_calls(bucket, ["unknown", "Perhaps a cage maker.", f"Not {TICKER}-like at all"])
    done, asked, shown = verdict(case, bucket, ["n", "n"])
    assert (done.stage, done.flagged, done.written) == ("written", 0, 3)
    assert len(asked) == 2 and any("FINDS a term" in line for line in shown)
    got = verdicts(bucket)
    assert [v["passed"] for v in got] == [True, True, True]
    assert [v["unknown"] for v in got] == [True, False, False]
    assert (
        got[2]["term_hit"] is True and got[2]["original_verdict"] == "pass"
    )  # overruled by his read
    assert all(v["reader"] is None and v["resolution"] is None for v in got)
    assert all(v["call_key"] == call_key(LABEL, 1, "haiku-5-5", i) for i, v in enumerate(got, 1))


def test_an_answer_that_names_the_company_waits_for_the_reader_and_is_not_asked_again(
    tmp_path: Path,
) -> None:
    bucket = FakeBucket()
    _, case = locked(tmp_path)
    put_calls(bucket, ["unknown", f"That is {CANARY}.", "Maybe a cage maker"])
    done, asked, _ = verdict(case, bucket, ["y", "n"])
    assert (done.stage, done.flagged, done.written) == ("needs_reader", 1, 0)
    assert len(asked) == 2 and not any("verdict" in k for k in bucket.objects)
    flagged = json.loads(case.probe_flagged_path(1).read_text(encoding="utf-8"))
    assert flagged == {"probe_set": 1, "answers": [f"That is {CANARY}."]}  # only the flagged one
    again, asked_again, _ = verdict(case, bucket, [])
    assert again.stage == "needs_reader" and asked_again == []  # his read is saved, not repeated
    reads = json.loads(case.probe_reads_path(1).read_text(encoding="utf-8"))["reads"]
    assert [r["names"] for r in reads] == [False, True, False]


def reader_reads(monkeypatch: pytest.MonkeyPatch, reply: dict[str, Any], probe_set: int = 1) -> int:
    code, _ = run_reader(
        monkeypatch,
        Replies(says(reply)),
        LABEL,
        "rejection",
        "--criterion",
        "not_recognizable",
        "--set",
        str(probe_set),
    )
    return code


def search_log(case: CaseAppendix) -> None:
    search = CaseAppendix(case.root, "search")
    log = SelectionLog({LABEL: Row(LABEL, "closure", "window", "acc")})
    log.record(LABEL, "first_disclosure", "pass", "r", disclosed=date(2026, 8, 18))
    for criterion in ("public_and_filing", "inside_window", "real_decision", "maps_to_shape"):
        log.record(LABEL, criterion, "pass", "r")
    search.directory.mkdir(parents=True, exist_ok=True)
    write_log_version(search, log)


@pytest.mark.parametrize(
    ("reply", "passed", "resolution"),
    [
        (PROBE_FAIL, False, None),
        (PROBE_UNSURE, False, None),
        (PROBE_PASS, True, "his reason, and why"),
    ],
)
def test_the_readers_reading_decides_the_final_passed_and_the_log_always_agrees(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    reply: dict[str, Any],
    passed: bool,
    resolution: str | None,
) -> None:
    bucket = FakeBucket()
    _, case = locked(tmp_path)
    search_log(case)
    put_calls(bucket, ["unknown", f"That is {CANARY}.", "unknown"])
    assert verdict(case, bucket, ["y"])[0].stage == "needs_reader"
    assert reader_reads(monkeypatch, reply) == CLEAN_EXIT
    done, _, _ = verdict(case, bucket, [], resolution=resolution)
    assert (done.stage, done.written, done.disputed) == ("written", 3, reply["reading"] == "pass")
    got = verdicts(bucket)
    assert [v["passed"] for v in got] == [True, passed, True]
    flagged = got[1]
    assert flagged["original_verdict"] == "fail" and flagged["term_hit"] is True
    assert flagged["reader"]["reading"] == reply["reading"]
    assert flagged["reader"]["reply"] == "reader-rejection-not_recognizable-set1-1-reply.json"
    assert len(flagged["reader"]["reply_sha256"]) == 64 and flagged["resolution"] == resolution
    assert got[0]["reader"] is None and got[2]["reader"] is None
    # The selection log, written from the same reply, agrees with the gate's verdict.
    log = SelectionLog({LABEL: Row(LABEL, "closure", "window", "acc")})
    log.record(LABEL, "first_disclosure", "pass", "r", disclosed=date(2026, 8, 18))
    for criterion in ("public_and_filing", "inside_window", "real_decision", "maps_to_shape"):
        log.record(LABEL, criterion, "pass", "r")
    log.record(LABEL, "not_recognizable", "fail", "the probe named it")
    logged = rejection_reply_on_record(case, "not_recognizable")
    assert (logged.reply, logged.reply_sha256) == (
        flagged["reader"]["reply"],
        flagged["reader"]["reply_sha256"],
    )
    log.record_read(LABEL, "not_recognizable", reply=logged, resolution=resolution)
    assert log.rows[LABEL].met("not_recognizable") is passed
    assert log.rows[LABEL].passed is passed


def test_a_dispute_needs_his_resolution_and_a_resolution_needs_a_dispute(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bucket = FakeBucket()
    _, case = locked(tmp_path)
    search_log(case)
    put_calls(bucket, [f"That is {CANARY}.", "unknown", "unknown"])
    verdict(case, bucket, ["y"])
    reader_reads(monkeypatch, PROBE_PASS)
    with pytest.raises(VerdictError, match="needs his written resolution"):
        verdict(case, bucket, [])
    assert not any("verdict" in k for k in bucket.objects)
    # the same set, read as an agreement elsewhere, takes no resolution
    other = FakeBucket()
    _, case2 = locked(tmp_path / "two")
    put_calls(other, ["unknown", "unknown", "unknown"])
    with pytest.raises(VerdictError, match="nothing to resolve"):
        verdict(case2, other, [], resolution="why")


def test_a_resolution_with_an_agreeing_reader_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bucket = FakeBucket()
    _, case = locked(tmp_path)
    search_log(case)
    put_calls(bucket, [f"That is {CANARY}.", "unknown", "unknown"])
    verdict(case, bucket, ["y"])
    reader_reads(monkeypatch, PROBE_FAIL)
    with pytest.raises(VerdictError, match="a resolution is for a reader's dispute"):
        verdict(case, bucket, [], resolution="why")


def test_a_reply_made_on_other_answers_than_the_flagged_ones_is_refused(tmp_path: Path) -> None:
    bucket = FakeBucket()
    _, case = locked(tmp_path)
    put_calls(bucket, [f"That is {CANARY}.", "unknown", "unknown"])
    verdict(case, bucket, ["y"])
    stem = case.directory / "reader-rejection-not_recognizable-set1-1"
    Path(f"{stem}-request.json").write_text(
        json.dumps({"material_sha256": {"Flagged answers": "0" * 64}}), encoding="utf-8"
    )
    reply = {"usable": True, "parsed": PROBE_FAIL, "estimated_usd": "0.01"}
    Path(f"{stem}-reply.json").write_text(json.dumps(reply), encoding="utf-8")
    with pytest.raises(VerdictError, match="other answers than the flagged ones"):
        verdict(case, bucket, [])


def test_a_set_is_settled_once_a_half_written_one_is_finished_and_a_differing_verdict_is_never_replaced(
    tmp_path: Path,
) -> None:
    bucket = FakeBucket()
    _, case = locked(tmp_path)
    put_calls(bucket, ["unknown", "unknown", "unknown"])
    verdict(case, bucket, [])
    assert len(bucket.puts) == 6
    again, _, _ = verdict(case, bucket, [])
    assert again.written == 0  # the same verdicts are not written twice
    stored = verdict_key(LABEL, 1, "haiku-5-5", 2)
    first = verdict_key(LABEL, 1, "haiku-5-5", 1)
    del bucket.objects[stored]  # a run that stopped part-way
    finished, _, _ = verdict(case, bucket, [])
    assert finished.written == 1 and stored in bucket.objects
    changed = json.loads(bucket.objects[first][0]) | {"passed": False}
    bucket.objects[first] = (json.dumps(changed), bucket.objects[first][1])
    with pytest.raises(VerdictError, match="differs from this verdict"):
        verdict(case, bucket, [])


def test_an_incomplete_model_no_calls_and_a_missing_term_list_are_refused(tmp_path: Path) -> None:
    bucket = FakeBucket()
    _, case = locked(tmp_path)
    with pytest.raises(VerdictError, match="no probe calls are stored"):
        verdict(case, bucket, [])
    put_calls(bucket, ["unknown", "unknown"])
    with pytest.raises(VerdictError, match="not 1-3"):
        verdict(case, bucket, [])
    complete = FakeBucket()
    put_calls(complete, ["x", "unknown", "unknown"])
    case.terms_path.unlink()
    with pytest.raises(VerdictError, match="term list cannot be read"):
        verdict(case, complete, ["n"])


# --- the criterion 5 read: what the reader is shown -----------------------------------------------


def test_the_reader_of_a_probe_failure_is_shown_the_definition_the_flagged_answers_and_the_terms_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from horizon_compact.reader import material

    bucket = FakeBucket()
    _, case = locked(tmp_path)
    search_log(case)
    case.reader_excerpt_path.write_text("EXCERPT-CANARY", encoding="utf-8")
    put_calls(bucket, ["unknown", f"That is {CANARY}.", "Something about SECRET-ANSWER"])
    verdict(case, bucket, ["y", "n"])
    sent = material.rejection_material(case, "not_recognizable", 1)
    protocol = (ROOT / "experiment" / "protocol" / "protocol-v1.md").read_text(encoding="utf-8")
    assert sent.parts.keys() == {"Definition", "Term list", "Flagged answers"}
    assert material.NAMES_THE_COMPANY.rstrip(".") in " ".join(protocol.replace("**", "").split())
    assert f"Answer 1:\nThat is {CANARY}." in sent.user
    for absent in ("unknown", "SECRET-ANSWER", "EXCERPT-CANARY", "A maker of cages", "Criterion: "):
        assert absent not in sent.user.replace("[end of Definition]", ""), absent
    assert sent.user.startswith("Criterion to read: not_recognizable\n\n[Definition]")
    assert f"term: {CANARY} => the Company" in sent.user
    with pytest.raises(material.MaterialError, match="names its probe set"):
        material.rejection_material(case, "not_recognizable")
    with pytest.raises(material.MaterialError, match="only a probe read names a probe set"):
        material.rejection_material(case, "real_decision", 1)


def test_a_probe_read_needs_the_flagged_file_and_is_made_once_per_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    bucket = FakeBucket()
    _, case = locked(tmp_path)
    search_log(case)
    assert reader_reads(monkeypatch, PROBE_FAIL) == REFUSED_EXIT  # no flagged answers yet
    assert "flagged probe answers" in capsys.readouterr().err
    put_calls(bucket, [f"That is {CANARY}.", "unknown", "unknown"])
    verdict(case, bucket, ["y"])
    assert reader_reads(monkeypatch, PROBE_FAIL) == CLEAN_EXIT
    out = capsys.readouterr().out
    assert "hc case log closure read closure-1 not_recognizable" in out
    assert "hc case probe-verdict closure-1 --set 1" in out
    assert reader_reads(monkeypatch, PROBE_FAIL) == REFUSED_EXIT
    assert "was read already" in capsys.readouterr().err
    request = json.loads(
        (case.directory / "reader-rejection-not_recognizable-set1-1-request.json").read_text(
            "utf-8"
        )
    )
    assert request["probe_set"] == 1 and request["criterion"] == "not_recognizable"
    assert (
        "Flagged answers" in request["material_sha256"]
        and "A maker of cages" not in request["user"]
    )


def test_a_probe_read_names_no_shape_and_a_read_of_set_2_is_its_own(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bucket = FakeBucket()
    _, case = locked(tmp_path)
    search_log(case)
    put_calls(bucket, [f"That is {CANARY}.", "unknown", "unknown"])
    verdict(case, bucket, ["y"])
    assert reader_reads(monkeypatch, {**PROBE_FAIL, "shape": "S1"}) == CHECK_FAILED_EXIT
    assert probe_reply_on_record(case, 1) is None  # an unusable attempt is not a reading
    assert reader_reads(monkeypatch, PROBE_FAIL) == CLEAN_EXIT
    found = probe_reply_on_record(case, 1)
    assert found is not None and found[0].reading == "fail"
    assert probe_reply_on_record(case, 2) is None
    put_calls(bucket, [f"Again {CANARY}.", "unknown", "unknown"], probe_set=2)
    verdict(case, bucket, ["y"], probe_set=2)
    assert reader_reads(monkeypatch, PROBE_PASS, probe_set=2) == CLEAN_EXIT
    newest = rejection_reply_on_record(case, "not_recognizable")
    assert (
        newest.reply == "reader-rejection-not_recognizable-set2-1-reply.json"
    )  # the log holds the last set


CHECK_FAILED_EXIT = cli.CHECK_FAILED_EXIT


def test_the_log_takes_a_criterion_5_read_from_the_reply_through_the_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    bucket = FakeBucket()
    _, case = locked(tmp_path)
    search_log(case)
    put_calls(bucket, [f"That is {CANARY}.", "unknown", "unknown"])
    verdict(case, bucket, ["y"])
    assert main(["case", "log", "closure", "read", LABEL, "not_recognizable"]) == REFUSED_EXIT
    assert (
        "did not fail not_recognizable" not in capsys.readouterr().err
    )  # refused for a missing read
    assert reader_reads(monkeypatch, PROBE_PASS) == CLEAN_EXIT
    words = [
        "case",
        "log",
        "closure",
        "record",
        LABEL,
        "not_recognizable",
        "fail",
        "--reason",
        "named",
    ]
    assert main(words) == CLEAN_EXIT
    capsys.readouterr()
    assert main(["case", "log", "closure", "read", LABEL, "not_recognizable"]) == REFUSED_EXIT
    assert "resolved by him" in capsys.readouterr().err
    done = main(
        ["case", "log", "closure", "read", LABEL, "not_recognizable", "--resolution", "why"]
    )
    assert done == CLEAN_EXIT
    assert "read of not_recognizable: pass" in capsys.readouterr().out
    # a second read of the same rejection is refused by the reader before anything is sent
    assert reader_reads(monkeypatch, PROBE_PASS, probe_set=1) == REFUSED_EXIT


# --- the S3 probe reader and the gate's checks on its records -------------------------------------


def record_for(probe_set: int = 1) -> Any:
    content = CaseContent(DOSSIER.encode(), SCENARIO.encode(), RUBRIC.encode())
    text = case_lock_text(LABEL, probe_set, content_hashes(content))
    return parse_case(text, LABEL)


def settled_bucket(
    tmp_path: Path,
    *,
    models: tuple[str, ...] = ("haiku-5-5", "gpt-oss-openrouter"),
    fail: bool = False,
) -> FakeBucket:
    bucket = FakeBucket()
    locked(tmp_path)
    for model in models:
        put_calls(
            bucket, ["unknown", f"That is {CANARY}." if fail else "unknown", "unknown"], model=model
        )
    return bucket


def test_the_s3_reader_builds_probe_records_from_last_modified_and_the_final_passed(
    tmp_path: Path,
) -> None:
    bucket = FakeBucket()
    _, case = locked(tmp_path)
    for model in ("haiku-5-5", "gpt-oss-openrouter"):
        put_calls(bucket, ["unknown", "unknown", "unknown"], model=model)
    verdict(
        case, bucket, []
    )  # one verdict step settles both models' calls, as it does over a whole set
    records = read_probe_records(bucket, "bucket", LABEL)  # type: ignore[arg-type]
    assert len(records) == 6 and [r.probe_set for r in records] == [1] * 6
    assert {r.model_key for r in records} == {"haiku-5-5", "gpt-oss-openrouter"}
    assert all(r.passed for r in records)
    stamp = bucket.objects[call_key(LABEL, 1, "haiku-5-5", 1)][1]
    assert (
        next(r for r in records if r.key == call_key(LABEL, 1, "haiku-5-5", 1)).last_modified
        == stamp
    )
    assert stamp.tzinfo is not None
    assert check_case_probes(record_for(), records, ["haiku-5-5", "gpt-oss-openrouter"]) == []


def test_the_s3_reader_fails_closed_on_a_missing_a_foreign_or_a_non_true_verdict(
    tmp_path: Path,
) -> None:
    bucket = FakeBucket()
    _, case = locked(tmp_path)
    put_calls(bucket, ["unknown", "unknown", "unknown"])
    unjudged = {r.key: r.passed for r in read_probe_records(bucket, "b", LABEL)}  # type: ignore[arg-type]
    assert unjudged and not any(unjudged.values())  # no verdict: not passed
    verdict(case, bucket, [])
    assert all(r.passed for r in read_probe_records(bucket, "b", LABEL))  # type: ignore[arg-type]
    first = verdict_key(LABEL, 1, "haiku-5-5", 1)
    good = json.loads(bucket.objects[first][0])
    for tampered in (
        {**good, "call_key": call_key(LABEL, 1, "haiku-5-5", 2)},  # a verdict for another call
        {**good, "passed": "true"},  # not literally true
        {**good, "passed": 1},
    ):
        bucket.objects[first] = (json.dumps(tampered), bucket.objects[first][1])
        got = {r.key: r.passed for r in read_probe_records(bucket, "b", LABEL)}  # type: ignore[arg-type]
        assert got[call_key(LABEL, 1, "haiku-5-5", 1)] is False
    bucket.objects[first] = ("not json", bucket.objects[first][1])
    assert not next(
        r
        for r in read_probe_records(bucket, "b", LABEL)  # type: ignore[arg-type]
        if r.key.endswith("call-1.json")
    ).passed


def test_the_s3_reader_ignores_other_cases_verdicts_errors_and_content(tmp_path: Path) -> None:
    bucket = FakeBucket()
    _, case = locked(tmp_path)
    put_calls(bucket, ["unknown", "unknown", "unknown"])
    bucket.put_new("cases/closure-2/probes/set-1/haiku-5-5/call-1.json", "{}")
    bucket.put_new(error_key(LABEL, 1, "haiku-5-5", 1, 1), "{}")
    bucket.put_new(content_key(LABEL, 1, "dossier.toml"), DOSSIER)
    verdict(case, bucket, [])
    assert [r.key for r in read_probe_records(bucket, "b", LABEL)] == [  # type: ignore[arg-type]
        call_key(LABEL, 1, "haiku-5-5", n) for n in (1, 2, 3)
    ]


def test_a_failure_the_reader_agreed_with_fails_the_gate_and_a_disputed_one_passes_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for reply, resolution, gate_ok in ((PROBE_FAIL, None, False), (PROBE_PASS, "why", True)):
        sub = tmp_path / str(gate_ok)
        bucket = FakeBucket()
        _, case = locked(sub)
        monkeypatch.setenv("HC_APPENDIX_DIR", str(sub / "appendix"))
        search_log(case)
        put_calls(bucket, [f"That is {CANARY}.", "unknown", "unknown"])
        verdict(case, bucket, ["y"])
        reader_reads(monkeypatch, reply)
        verdict(case, bucket, [], resolution=resolution)
        records = read_probe_records(bucket, "b", LABEL)  # type: ignore[arg-type]
        lines = check_case_probes(record_for(), records, ["haiku-5-5"])
        assert (lines == []) is gate_ok, lines
        if not gate_ok:
            assert "failed the recognition probe" in lines[0]


def test_the_order_check_reads_the_probe_records_the_reader_built(tmp_path: Path) -> None:
    bucket = FakeBucket()
    _, case = locked(tmp_path)
    put_calls(bucket, ["unknown", "unknown", "unknown"])
    verdict(case, bucket, [])
    probes = read_probe_records(bucket, "b", LABEL)  # type: ignore[arg-type]
    first = min(p.last_modified for p in probes)
    from horizon_compact.protocol.cases import CiRun

    lock_text = (tmp_path / "repo" / case_path(LABEL)).read_text(encoding="utf-8")
    early = CiRun("1", first - timedelta(hours=1), lock_text)
    late = CiRun("2", first + timedelta(hours=1), lock_text)
    assert check_case_order(record_for(), [early], probes).admitted
    assert not check_case_order(record_for(), [late], probes).admitted


# --- the GitHub reader ----------------------------------------------------------------------------


def runs_output(*runs: tuple[int, str, str]) -> str:
    return (
        "\n".join(
            json.dumps({"id": i, "created_at": created, "head_sha": sha})
            for i, created, sha in runs
        )
        + "\n"
    )


def test_the_github_reader_builds_a_run_per_listing_line_with_the_record_at_its_head(
    tmp_path: Path,
) -> None:
    repo, _ = locked(tmp_path)
    lock_text = (repo / case_path(LABEL)).read_text(encoding="utf-8")
    calls: list[tuple[str, ...]] = []

    def gh(args: Any) -> str:
        calls.append(tuple(args))
        return runs_output(
            (11, "2026-10-20T09:30:00Z", "a" * 40),
            (10, "2026-10-19T08:00:00Z", "b" * 40),
            (11, "2026-10-20T09:30:00Z", "a" * 40),  # a page boundary can repeat a run
        )

    def git(args: Any) -> str:
        assert args[0] == "show"
        if args[1].startswith("b" * 40):
            raise GithubReadError("no such path in that commit")
        assert args[1] == f"{'a' * 40}:{case_path(LABEL)}"
        return lock_text

    runs = read_ci_runs(LABEL, gh=gh, git=git)
    assert calls == [tuple(RUNS_ARGS)] and "{owner}/{repo}" in RUNS_ARGS[2]
    assert [r.run_id for r in runs] == ["11", "10"]
    assert (
        runs[0].created_at == datetime(2026, 10, 20, 9, 30, tzinfo=UTC)
        and runs[0].record_text == lock_text
    )
    assert runs[1].record_text is None  # a commit with no record attests to nothing
    probes = read_probe_records(_probes_after(tmp_path), "b", LABEL)  # type: ignore[arg-type]
    assert check_case_order(record_for(), runs, probes).admitted


def _probes_after(tmp_path: Path) -> FakeBucket:
    """Probe objects written after the runs above (the fake clock starts on 2026-10-20 at noon)."""
    bucket = FakeBucket()
    locked(tmp_path / "p")
    put_calls(bucket, ["unknown", "unknown", "unknown"])
    return bucket


@pytest.mark.parametrize(
    ("output", "words"),
    [
        ("not json\n", "not a run"),
        (
            json.dumps({"id": 1, "created_at": "2026-10-20T09:30:00", "head_sha": "a" * 40}) + "\n",
            "no time zone",
        ),
        (
            json.dumps({"id": 1, "created_at": "yesterday", "head_sha": "a" * 40}) + "\n",
            "not a time",
        ),
        (json.dumps({"id": 1}) + "\n", "not a run"),
    ],
)
def test_the_github_reader_refuses_a_listing_it_does_not_know(output: str, words: str) -> None:
    with pytest.raises(GithubReadError, match=words):
        read_ci_runs(LABEL, gh=lambda args: output, git=lambda args: "x")


def test_a_run_the_listing_no_longer_holds_is_simply_absent_so_the_check_refuses() -> None:
    record = record_for()
    assert not check_case_order(record, [], [_probe_stub()]).admitted


def _probe_stub() -> Any:
    from horizon_compact.protocol.cases import ProbeRecord

    return ProbeRecord(
        call_key(LABEL, 1, "haiku-5-5", 1), "haiku-5-5", 1, True, datetime(2026, 10, 21, tzinfo=UTC)
    )


def test_the_command_runner_reports_a_failed_or_missing_program_without_its_output() -> None:
    with pytest.raises(GithubReadError, match="cannot run"):
        command_runner("no-such-program-for-hc-tests")(["x"])
    with pytest.raises(GithubReadError, match="failed"):
        command_runner("false")([])
    assert command_runner("echo")(["hi"]).strip() == "hi"


def test_the_command_runner_runs_in_the_directory_it_is_given(tmp_path: Path) -> None:
    assert command_runner("pwd", cwd=tmp_path)([]).strip() == str(tmp_path)


# --- the commands ---------------------------------------------------------------------------------


def test_hc_case_upload_through_the_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo, _ = locked(tmp_path)
    bucket = FakeBucket()
    monkeypatch.setattr(cli, "default_repo_root", lambda: repo)
    monkeypatch.setattr(cli, "git_in", lambda root: fake_git())
    monkeypatch.setattr(cli, "_case_bucket_store", lambda args: bucket)
    assert main(["case", "upload", LABEL]) == CLEAN_EXIT  # --set defaults to the lock's
    assert "set 1: wrote dossier.toml, scenario.toml, rubric.toml" in capsys.readouterr().out
    assert main(["case", "upload", LABEL, "--set", "2"]) == REFUSED_EXIT
    assert "is for probe set 1, not 2" in capsys.readouterr().err


def test_the_laptop_store_needs_a_profile_and_a_bucket_and_has_no_default() -> None:
    from horizon_compact.sweep.plan import SweepRefusal

    with pytest.raises(SweepRefusal, match="--profile is required"):
        cli._case_bucket_store(argparse.Namespace(profile=None, bucket="b"))
    with pytest.raises(SweepRefusal, match="--bucket or HC_RESULTS_BUCKET"):
        cli._case_bucket_store(argparse.Namespace(profile="p", bucket=None))


def test_hc_case_probe_refuses_outside_the_container_before_any_key_or_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo, _ = locked(tmp_path)
    monkeypatch.setattr(cli, "default_repo_root", lambda: repo)
    monkeypatch.delenv("ECS_CONTAINER_METADATA_URI_V4", raising=False)
    monkeypatch.setattr(cli, "_laptop_git", lambda: ("deadbeef", False))
    assert main(["case", "probe", LABEL, "--model", "haiku-5-5"]) == REFUSED_EXIT
    assert "in the container only" in capsys.readouterr().err
    assert main(["case", "probe", LABEL, "--model", "no-such-model"]) == REFUSED_EXIT
    assert "not a model in models.toml" in capsys.readouterr().err


def test_hc_case_probe_runs_in_the_container_with_a_fake_world(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    bucket = FakeBucket()
    repo, _ = uploaded(tmp_path, bucket)
    provider = Replies(ok("unknown"), ok("unknown"), ok("unknown"))
    monkeypatch.setattr(cli, "default_repo_root", lambda: repo)
    monkeypatch.setattr(cli, "identify", lambda env, git: CONTAINER)
    monkeypatch.setattr(
        cli, "_case_probe_world", lambda args, key, config, identity: (provider, bucket, ACCOUNT)
    )
    assert main(["case", "probe", LABEL, "--model", "haiku-5-5"]) == CLEAN_EXIT
    out = capsys.readouterr().out
    assert "stopped:         complete" in out and "calls recorded:  3 of 3" in out
    assert bucket.get(call_key(LABEL, 1, "haiku-5-5", 3)) is not None
    only_cap = main(
        ["case", "probe", LABEL, "--model", "gpt-oss-openrouter", "--cap-usd", "0.0000001"]
    )
    assert only_cap == REFUSED_EXIT and "above the cap" in capsys.readouterr().err


def test_the_probe_world_refuses_a_laptop_before_it_makes_a_session() -> None:
    with pytest.raises(ProbeRefused, match="in the container only"):
        cli._case_probe_world(argparse.Namespace(bucket="b"), "haiku-5-5", HAIKU, LAPTOP)


def test_hc_case_probe_verdict_through_the_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    bucket = FakeBucket()
    repo, case = locked(tmp_path)
    put_calls(bucket, ["unknown", f"That is {CANARY}.", "unknown"])
    answers = iter(["y"])
    monkeypatch.setattr(cli, "default_repo_root", lambda: repo)
    monkeypatch.setattr(cli, "_case_bucket_store", lambda args: bucket)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    assert main(["case", "probe-verdict", LABEL]) == CLEAN_EXIT
    out = capsys.readouterr().out
    assert "1 of 3 answers name the company" in out
    assert "hc case reader closure-1 rejection --criterion not_recognizable --set 1" in out
    assert not any("verdict" in k for k in bucket.objects) and case.probe_flagged_path(1).is_file()
    assert main(["case", "probe-verdict", LABEL, "--resolution", "why"]) == REFUSED_EXIT
    assert "no dispute to resolve" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("reply", "extra", "words"),
    [
        (PROBE_FAIL, [], "the failure stands: coarsen the dossier once and lock it as set 2"),
        (PROBE_PASS, ["--resolution", "why"], "the reader DISPUTES it"),
    ],
)
def test_the_verdict_command_says_what_comes_next_for_an_agreed_and_a_disputed_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    reply: dict[str, Any],
    extra: list[str],
    words: str,
) -> None:
    bucket = FakeBucket()
    _, case = locked(tmp_path)
    search_log(case)
    put_calls(bucket, [f"That is {CANARY}.", "unknown", "unknown"])
    monkeypatch.setattr(cli, "_case_bucket_store", lambda args: bucket)
    monkeypatch.setattr("builtins.input", lambda prompt="": "y")
    assert main(["case", "probe-verdict", LABEL, "--set", "1"]) == CLEAN_EXIT
    assert reader_reads(monkeypatch, reply) == CLEAN_EXIT
    capsys.readouterr()
    assert main(["case", "probe-verdict", LABEL, "--set", "1", *extra]) == CLEAN_EXIT
    out = capsys.readouterr().out
    assert words in out and "wrote 3 verdict(s) of 3" in out


# --- the Opus review of 10a ---------------------------------------------------------------------------


def test_only_a_plain_yes_or_no_is_taken_and_no_reply_saves_nothing(tmp_path: Path) -> None:
    bucket = FakeBucket()
    _, case = locked(tmp_path)
    put_calls(bucket, [f"That is {CANARY}.", "unknown", "unknown"])
    with pytest.raises(VerdictError, match="no y or n was given"):
        verdict(case, bucket, ["", "sure", "N/A"])
    # A stray Enter is never a saved "does not name it".
    assert not case.probe_reads_path(1).exists()
    done, asked, _ = verdict(case, bucket, ["", "Yes"])
    assert len(asked) == 2 and done.stage == "needs_reader" and done.flagged == 1


def test_the_reader_sees_the_term_directives_and_never_a_comment_or_a_hint_of_the_flag(
    tmp_path: Path,
) -> None:
    from horizon_compact.reader import material

    bucket = FakeBucket()
    _, case = locked(tmp_path)
    case.terms_path.write_text(
        f"# NOTE-CANARY his own note\n\nterm: {CANARY} => the Company\n", encoding="utf-8"
    )
    put_calls(bucket, [f"That is {CANARY}.", "unknown", "unknown"])
    verdict(case, bucket, ["y"])
    sent = material.rejection_material(case, "not_recognizable", 1)
    assert "NOTE-CANARY" not in sent.user
    assert f"[Term list]\nterm: {CANARY} => the Company\n" in sent.user
    brief = (ROOT / "experiment" / "readers" / "rejection.txt").read_text(encoding="utf-8")
    assert "flagged" not in brief and "set aside" not in brief


def test_the_log_never_takes_an_earlier_sets_reply_for_a_later_set_not_yet_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from horizon_compact.reader.read import ReaderError

    bucket = FakeBucket()
    _, case = locked(tmp_path)
    search_log(case)
    put_calls(bucket, [f"That is {CANARY}.", "unknown", "unknown"])
    verdict(case, bucket, ["y"])
    assert reader_reads(monkeypatch, PROBE_FAIL) == CLEAN_EXIT
    put_calls(bucket, [f"Again {CANARY}.", "unknown", "unknown"], probe_set=2)
    verdict(case, bucket, ["y"], probe_set=2)
    with pytest.raises(ReaderError, match="probe set 2 has flagged answers and no usable read"):
        rejection_reply_on_record(case, "not_recognizable")


# --- 10b: the laptop's launch ---------------------------------------------------------------------


def test_hc_case_probe_launch_checks_the_case_on_the_laptop_then_starts_the_task(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    bucket = FakeBucket()
    repo, case = locked(tmp_path)
    launched: list[tuple[str, list[str]]] = []
    git = {"run": fake_git()}

    def launch_task(ecs: object, ec2: object, *, model_key: str, command: list[str]) -> str:
        launched.append((model_key, command))
        return "arn:aws:ecs:us-east-1:123:task/horizon-compact/abc123"

    class Session:
        def __init__(self, **kwargs: object) -> None:
            pass

        def client(self, name: str) -> object:
            return name

    monkeypatch.setattr(cli, "default_repo_root", lambda: repo)
    monkeypatch.setattr(cli, "git_in", lambda root: git["run"])
    monkeypatch.setattr(cli, "_case_bucket_store", lambda args: bucket)
    monkeypatch.setattr("horizon_compact.sweep.launch.launch_task", launch_task)
    monkeypatch.setattr("boto3.Session", Session)
    launch = ["case", "probe", LABEL, "--model", "haiku-5-5", "--launch", "--profile", "p"]

    assert main(launch) == REFUSED_EXIT  # nothing uploaded yet
    assert "run `hc case upload` first" in capsys.readouterr().err
    upload_case(case, repo, probe_set=1, git=fake_git(), store=bucket)  # type: ignore[arg-type]
    git["run"] = fake_git(remotes="")
    assert main(launch) == REFUSED_EXIT
    assert "not on any remote branch" in capsys.readouterr().err
    git["run"] = fake_git()
    assert main(launch) == CLEAN_EXIT
    assert launched == [
        (
            "haiku-5-5",
            ["case", "probe", LABEL, "--model", "haiku-5-5", "--set", "1", "--cap-usd", "2.0"],
        )
    ]
    assert "launched:        abc123" in capsys.readouterr().out
    for n in (1, 2, 3):
        bucket.put_new(call_key(LABEL, 1, "haiku-5-5", n), "{}")
    assert main(launch) == REFUSED_EXIT
    assert "nothing to launch" in capsys.readouterr().err
    assert len(launched) == 1
