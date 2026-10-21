"""Step 3's knowledge probe (search-half IMPLEMENTATION doc §4.6.5 step 3 item 4; exploratory plan, part 3b):
the message, the inputs file, who is probed and with what, the order of the records, the refusals before any
call and the once-only rule. A fake provider throughout: no model is called, no key is read. Fictional
canaries only."""

from __future__ import annotations

import dataclasses
import json
import random
from collections.abc import Callable, Sequence
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from horizon_compact import cli
from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.exploratory import (
    KNOWLEDGE,
    ExploratoryLog,
    write_exploratory_version,
)
from horizon_compact.casebuild.search import Row, SelectionLog, write_log_version
from horizon_compact.caseprobe.knowledge import (
    CALLS,
    MAX_API_ERRORS,
    MESSAGE_FACILITY,
    MESSAGE_REDUCTION,
    Inputs,
    KnowledgeError,
    build_message,
    check_build_shape,
    is_unknown,
    load_inputs,
    probe_models,
    probed_shape,
    run_knowledge_probe,
)
from horizon_compact.cli import CLEAN_EXIT, REFUSED_EXIT, main
from horizon_compact.dossier.check import default_repo_root
from horizon_compact.providers.base import RawDecision, TextRequest, text_prompt_sha256
from test_casebuild_extract import PROVENANCE, ok

ROOT = default_repo_root()
LABEL = "pre-01"
COMPANY = "Fernwick Canary Holdings"
FACILITY = "Larkspur Works"
PLACE = "Quillmouth"
DISCLOSED = date(2026, 3, 12)
KEYS = ["haiku-5-5", "gpt-oss-openrouter", "sonnet-5-5-extraction"]
S3_TEXT = f'shape = "S3"\ncompany = "{COMPANY}"\nfacility = "{FACILITY}"\nplace = "{PLACE}"\n'
S1_TEXT = f'shape = "S1"\ncompany = "{COMPANY}"\n'
S3_MESSAGE = (
    f"What do you know about {COMPANY}'s {FACILITY} in {PLACE}? "
    "If you know nothing about it, say unknown."
)
S1_MESSAGE = (
    f"What do you know about the workforce reduction {COMPANY} announced in March 2026? "
    "If you know nothing about it, say unknown."
)


@pytest.fixture(autouse=True)
def _appendix_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HC_APPENDIX_DIR", str(tmp_path / "appendix"))


# --- a pool row at not_known, and the inputs file -------------------------------------------------------


def pool_log(
    *, upto: str = KNOWLEDGE, step: str = "3", pool: str = "pre", label: str = LABEL
) -> ExploratoryLog:
    """A row that met every criterion before ``upto`` (the criterion it stands at)."""
    log = ExploratoryLog()
    log.add(label, "closure", step, pool, "0000000000-26-000001")
    for criterion in ("first_disclosure", "public_and_filing", "inside_window", "real_decision"):
        if criterion == upto:
            return log
        log.record(
            label,
            criterion,
            "pass",
            "r",
            disclosed=DISCLOSED if criterion == "first_disclosure" else None,
        )
    if upto == "maps_to_shape":
        return log
    log.record(label, "maps_to_shape", "pass", "r", case_type="closure")
    return log


def world(
    tmp_path: Path, inputs: str | None = S3_TEXT, log: ExploratoryLog | None = None
) -> CaseAppendix:
    root = tmp_path / "appendix"
    search = CaseAppendix(root, "search")
    search.directory.mkdir(parents=True, exist_ok=True)
    # the pre-registered log is always there once the search has run; it holds only its own rows
    write_log_version(
        search, SelectionLog({"closure-01": Row("closure-01", "closure", "window", "a")})
    )
    write_exploratory_version(search, log or pool_log())
    case = CaseAppendix(root, LABEL)
    case.directory.mkdir(parents=True, exist_ok=True)
    if inputs is not None:
        case.knowledge_inputs_path.write_text(inputs, encoding="utf-8")
    return case


def probe_files(case: CaseAppendix) -> list[str]:
    return sorted(p.name for p in case.directory.glob("knowledge-probe-*"))


# --- a fake provider, and a fake git --------------------------------------------------------------------


def api_error(code: str = "ThrottlingException") -> RawDecision:
    return RawDecision(
        status="api_error", provenance=PROVENANCE, error={"code": code, "message": "try later"}
    )


class Replies:
    """Serves scripted decisions in order (``unknown`` once the script runs out), records every request, and
    proves the request record is on disk before each call and the reply record is not."""

    name = "fake"

    def __init__(self, case: CaseAppendix, *script: RawDecision) -> None:
        self.case = case
        self.script = list(script)
        self.requests: list[TextRequest] = []
        self.seen: dict[str, int] = {}

    def text_request_body(self, request: TextRequest) -> dict[str, Any]:
        return {"messages": [request.user]}

    def decide_text(self, request: TextRequest) -> RawDecision:
        key = request.route.key
        if not self.requests or self.requests[-1].route.key != key:
            self.seen[key] = 0
        self.requests.append(request)
        call = self.seen[key] + 1
        stem = f"knowledge-probe-{key}-{call}"
        assert (self.case.directory / f"{stem}-request.json").exists()
        assert not (self.case.directory / f"{stem}-reply.json").exists()
        reply = self.script.pop(0) if self.script else ok("unknown")
        if reply.status != "api_error":
            self.seen[key] = call
        return reply


def git(args: Sequence[str]) -> str:
    return {"rev-parse": "abc123def456\n", "status": " M src/x.py\n"}[args[0]]


def run(
    case: CaseAppendix,
    provider: Replies,
    *,
    confirm: Callable[[Any], bool] = lambda preview: True,
    made: list[str] | None = None,
) -> Any:
    def factory(kind: str) -> Replies:
        if made is not None:
            made.append(kind)
        return provider

    return run_knowledge_probe(
        case,
        search=CaseAppendix(case.root, "search"),
        repo_root=ROOT,
        git=git,
        confirm=confirm,
        make_provider=factory,
        sleep=lambda seconds: None,
        rng=random.Random(0),
    )


def load(case: CaseAppendix, name: str) -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads((case.directory / name).read_text(encoding="utf-8"))
    return loaded


# --- the message ----------------------------------------------------------------------------------------


def test_the_two_messages_are_the_docs_words() -> None:
    text = (ROOT / "docs/phases/phase-5-case-building-search-IMPLEMENTATION.md").read_text("utf-8")
    doc = " ".join(text.split())  # the doc wraps its lines
    assert f'"{MESSAGE_FACILITY}"' in doc and f'"{MESSAGE_REDUCTION}"' in doc


def test_an_s3_message_names_the_facility_and_its_town_and_an_s1_or_s2_message_the_month() -> None:
    s3 = Inputs("S3", COMPANY, FACILITY, PLACE, "x")
    assert build_message(s3, None) == S3_MESSAGE  # no date needed for a facility
    for shape in ("S1", "S2"):
        assert build_message(Inputs(shape, COMPANY, None, None, "x"), DISCLOSED) == S1_MESSAGE
    with pytest.raises(KnowledgeError, match="first-disclosure date"):
        build_message(Inputs("S1", COMPANY, None, None, "x"), None)


@pytest.mark.parametrize(
    ("text", "kept"),
    [
        ("unknown", True),
        ("Unknown.", True),
        ('"unknown"', True),
        (" UNKNOWN \n", True),
        ("I don't know", False),
        ("unknown company", False),
        ("", False),
        ("Unknown. But", False),
    ],
)
def test_only_the_one_word_asked_for_counts_as_unknown(text: str, kept: bool) -> None:
    assert is_unknown(text) is kept


# --- the inputs file ------------------------------------------------------------------------------------


def test_the_inputs_are_read_as_placed_and_hashed(tmp_path: Path) -> None:
    case = world(tmp_path)
    got = load_inputs(case)
    assert (got.shape, got.company, got.facility, got.place) == ("S3", COMPANY, FACILITY, PLACE)
    assert len(got.sha256) == 64
    assert load_inputs(world_with(tmp_path, S1_TEXT)).facility is None


def world_with(tmp_path: Path, text: str) -> CaseAppendix:
    case = CaseAppendix(tmp_path / "appendix", LABEL)
    case.directory.mkdir(parents=True, exist_ok=True)
    case.knowledge_inputs_path.write_text(text, encoding="utf-8")
    return case


@pytest.mark.parametrize(
    ("text", "why"),
    [
        ('shape = "S4"\ncompany = "A"\n', "shape in the inputs file is one of"),
        ('company = "A"\n', "shape is missing"),
        ('shape = "S1"\n', "company is missing"),
        ('shape = "S3"\ncompany = "A"\nfacility = "B"\n', "place is missing"),
        ('shape = "S3"\ncompany = "A"\nplace = "B"\n', "facility is missing"),
        ('shape = "S1"\ncompany = "A"\nfacility = "B"\n', "facility and place are for S3"),
        ('shape = "S2"\ncompany = "A"\nplace = "B"\n', "facility and place are for S3"),
        ('shape = "S1"\ncompany = "   "\n', "company in the inputs file is not text"),
        ('shape = "S1"\ncompany = 4\n', "company in the inputs file is not text"),
        ('shape = "S1"\ncompany = """A\nB"""\n', "one line"),
        ('shape = "S1"\ncompany = "A"\nnote = "B"\n', "keys that mean nothing here: note"),
        ("shape = ", "cannot be read"),
    ],
)
def test_an_inputs_file_that_cannot_fill_the_message_is_refused(
    tmp_path: Path, text: str, why: str
) -> None:
    with pytest.raises(KnowledgeError, match=why):
        load_inputs(world_with(tmp_path, text))


def test_a_missing_inputs_file_is_refused_and_nothing_is_sent(tmp_path: Path) -> None:
    case = world(tmp_path, inputs=None)
    provider, made = Replies(case), list[str]()
    with pytest.raises(KnowledgeError, match=r"knowledge-inputs\.toml cannot be read"):
        run(case, provider, made=made)
    assert provider.requests == [] and made == [] and probe_files(case) == []


# --- who is probed --------------------------------------------------------------------------------------


def test_the_probed_models_are_the_two_official_ones_then_the_extraction_model() -> None:
    models = probe_models(ROOT / "experiment")
    assert [m.key for m in models] == KEYS
    haiku, gpt_oss, extraction = (m.route for m in models)
    assert haiku.route_kind == "anthropic" and haiku.thinking_off
    assert gpt_oss.route_kind == "openrouter" and gpt_oss.pinned_provider == "deepinfra/bf16"
    assert gpt_oss.reasoning_effort == "medium"
    assert extraction.route_kind == "anthropic" and extraction.thinking_between_tools


def test_a_models_file_with_two_main_models_is_refused(tmp_path: Path) -> None:
    text = (ROOT / "experiment" / "models.toml").read_text("utf-8")
    start = text.index("[models.haiku-5-5]")
    end = text.index("\n\n", text.index("[models.haiku-5-5.prices]"))
    twin = text[start:end].replace("haiku-5-5", "haiku-twin")
    (tmp_path / "models.toml").write_text(text + "\n" + twin, encoding="utf-8")
    with pytest.raises(KnowledgeError, match="2 models with role 'main'"):
        probe_models(tmp_path)


# --- the run --------------------------------------------------------------------------------------------


def test_three_calls_to_each_model_with_no_system_text_and_the_one_message(tmp_path: Path) -> None:
    case = world(tmp_path)
    provider, made = Replies(case), list[str]()
    outcome = run(case, provider, made=made)
    assert [r.route.key for r in provider.requests] == [k for k in KEYS for _ in range(CALLS)]
    assert {(r.system, r.user, r.max_tokens) for r in provider.requests} == {("", S3_MESSAGE, 4000)}
    assert made == ["anthropic", "openrouter"]  # one provider per route, made once
    assert len(outcome.results) == 9 and all(r.unknown for r in outcome.results)
    assert outcome.api_errors == 0 and outcome.cost_usd > 0
    assert len(probe_files(case)) == 18


def test_each_call_leaves_a_request_record_and_a_reply_record_with_provenance(
    tmp_path: Path,
) -> None:
    case = world(tmp_path)
    provider = Replies(case, ok("Larkspur Works is a plant that Fernwick closed."))
    run(case, provider)  # the fake proves the request record preceded each call
    request = load(case, "knowledge-probe-haiku-5-5-1-request.json")
    reply = load(case, "knowledge-probe-haiku-5-5-1-reply.json")
    assert request["system"] == "" and request["user"] == S3_MESSAGE
    assert request["git_sha"] == "abc123def456" and request["git_dirty"] is True
    assert request["prompt_sha256"] == text_prompt_sha256(provider.requests[0])
    assert (
        request["inputs_sha256"] == load_inputs(case).sha256 and len(request["entry_sha256"]) == 64
    )
    assert reply["answer"] == "Larkspur Works is a plant that Fernwick closed."
    assert reply["status"] == "replied" and reply["usage"]["input_tokens"] == 10
    assert reply["provenance"]["model_id"] == "fake-model" and reply["cost_usd"] > 0
    assert reply["label"] == LABEL and reply["call"] == 1 and reply["shape"] == "S3"


def test_an_s1_probe_asks_about_the_reduction_in_the_first_disclosures_month(
    tmp_path: Path,
) -> None:
    case = world(tmp_path, S1_TEXT)
    provider = Replies(case)
    run(case, provider)
    assert {r.user for r in provider.requests} == {S1_MESSAGE}


def test_a_reply_is_never_retried_whatever_it_says(tmp_path: Path) -> None:
    case = world(tmp_path)
    cut_off = ok("Fernwick closed it", stop="max_tokens")
    provider = Replies(case, cut_off, ok(""), ok("unknown", stop="content_filtered"))
    outcome = run(case, provider)
    assert len(provider.requests) == 9  # no call repeated
    assert [r.status for r in outcome.results[:3]] == ["truncated", "no_text", "content_filtered"]
    assert [r.unknown for r in outcome.results[:3]] == [False, False, False]
    assert load(case, "knowledge-probe-haiku-5-5-1-reply.json")["status"] == "truncated"


def test_an_api_error_is_kept_and_retried_and_the_reply_is_then_the_measurement(
    tmp_path: Path,
) -> None:
    case = world(tmp_path)
    provider = Replies(case, api_error(), api_error("ServiceUnavailableException"), ok("unknown"))
    outcome = run(case, provider)
    assert outcome.api_errors == 2 and len(provider.requests) == 11
    names = probe_files(case)
    assert "knowledge-probe-haiku-5-5-1-error-1.json" in names
    assert "knowledge-probe-haiku-5-5-1-error-2.json" in names
    assert load(case, "knowledge-probe-haiku-5-5-1-error-1.json")["error"]["code"] == (
        "ThrottlingException"
    )
    assert len([n for n in names if n.endswith("-reply.json")]) == 9


def test_a_fatal_api_error_stops_the_run_and_a_second_run_is_refused(tmp_path: Path) -> None:
    case = world(tmp_path)
    provider = Replies(case, ok("unknown"), api_error("AccessDeniedException"))
    with pytest.raises(KnowledgeError, match="stopped at haiku-5-5 call 2 on an API error"):
        run(case, provider)
    names = probe_files(case)
    assert "knowledge-probe-haiku-5-5-2-request.json" in names  # written before the call
    assert "knowledge-probe-haiku-5-5-2-error-1.json" in names
    assert "knowledge-probe-haiku-5-5-2-reply.json" not in names
    again = Replies(case)
    with pytest.raises(KnowledgeError, match="a second run is refused"):
        run(case, again)
    assert again.requests == []


def test_too_many_api_errors_on_one_call_stop_the_run(tmp_path: Path) -> None:
    case = world(tmp_path)
    provider = Replies(case, *[api_error() for _ in range(MAX_API_ERRORS)])
    with pytest.raises(KnowledgeError, match="stopped at haiku-5-5 call 1"):
        run(case, provider)
    assert len(provider.requests) == MAX_API_ERRORS


def test_a_second_run_for_the_label_is_refused_before_any_call(tmp_path: Path) -> None:
    case = world(tmp_path)
    run(case, Replies(case))
    again = Replies(case)
    with pytest.raises(KnowledgeError, match="a second run is refused"):
        run(case, again)
    assert again.requests == [] and len(probe_files(case)) == 18


# --- the refusals, every one before the first byte leaves -----------------------------------------------


@pytest.mark.parametrize(
    ("log", "why"),
    [
        (pool_log(upto="maps_to_shape"), "stands at maps_to_shape, not at not_known"),
        (pool_log(upto="real_decision"), "stands at real_decision, not at not_known"),
        (pool_log(upto="first_disclosure"), "stands at first_disclosure"),
        (pool_log(step="2", pool="window", upto="maps_to_shape"), "no knowledge probe"),
        (pool_log(step="5", pool="late", upto="maps_to_shape"), "no knowledge probe"),
        (pool_log(label="pre-02"), "not a row of step 3's or step 4's pool"),
    ],
)
def test_a_row_not_at_not_known_is_refused_and_nothing_is_sent(
    tmp_path: Path, log: ExploratoryLog, why: str
) -> None:
    case = world(tmp_path, log=log)
    provider, made = Replies(case), list[str]()
    with pytest.raises(KnowledgeError, match=why):
        run(case, provider, made=made)
    assert provider.requests == [] and made == [] and probe_files(case) == []


def test_a_pre_registered_row_is_refused(tmp_path: Path) -> None:
    other = CaseAppendix(world(tmp_path).root, "closure-01")
    other.directory.mkdir(parents=True, exist_ok=True)
    other.knowledge_inputs_path.write_text(S3_TEXT, encoding="utf-8")
    provider = Replies(other)
    with pytest.raises(KnowledgeError, match="no knowledge probe"):
        run(other, provider)
    assert provider.requests == [] and probe_files(other) == []


def test_a_row_that_already_has_its_result_is_refused(tmp_path: Path) -> None:
    log = pool_log()
    log.record(LABEL, KNOWLEDGE, "pass", "r")
    case = world(tmp_path, log=log)
    with pytest.raises(KnowledgeError, match="already has a result on not_known"):
        run(case, Replies(case))


def test_a_failed_row_is_refused(tmp_path: Path) -> None:
    log = ExploratoryLog()
    log.add(LABEL, "closure", "3", "pre", "0000000000-26-000001")
    log.record(LABEL, "first_disclosure", "fail", "an earlier mention")
    case = world(tmp_path, log=log)
    with pytest.raises(KnowledgeError, match="stands at first_disclosure"):
        run(case, Replies(case))


def test_a_declined_spend_sends_nothing_and_asks_for_no_key(tmp_path: Path) -> None:
    case = world(tmp_path)
    provider, made = Replies(case), list[str]()
    previews: list[Any] = []

    def decline(preview: Any) -> bool:
        previews.append(preview)
        return False

    with pytest.raises(KnowledgeError, match="not confirmed: nothing was sent"):
        run(case, provider, confirm=decline, made=made)
    assert provider.requests == [] and made == [] and probe_files(case) == []
    assert [m.key for m in previews[0].models] == KEYS
    assert all(m.calls == CALLS and m.worst_case_usd > 0 for m in previews[0].models)
    assert COMPANY not in repr(previews[0])


# --- the command ----------------------------------------------------------------------------------------


def run_cli(
    monkeypatch: pytest.MonkeyPatch, provider: Replies, *words: str, made: list[str] | None = None
) -> int:
    def factory(kind: str) -> Replies:
        if made is not None:
            made.append(kind)
        return provider

    monkeypatch.setattr(cli, "_knowledge_provider", factory)
    monkeypatch.setattr(cli, "git_in", lambda repo: git)
    return main(["case", "knowledge-probe", LABEL, *words])


def test_the_command_prints_counts_only_and_logs_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    case = world(tmp_path)
    search = CaseAppendix(case.root, "search")
    logs_before = sorted(p.name for p in search.directory.iterdir())
    answers = [ok("unknown"), ok("Fernwick closed Larkspur Works"), ok("unknown")]
    provider = Replies(case, *answers)
    assert run_cli(monkeypatch, provider, "--yes") == CLEAN_EXIT
    out = capsys.readouterr()
    for text in (out.out, out.err):
        assert COMPANY not in text and FACILITY not in text and PLACE not in text
        assert "Fernwick" not in text and "closed" not in text
    assert (
        "haiku-5-5: 3 calls, 2 answered exactly 'unknown', 0 with reasoning, 1 for him to read"
        in out.out
    )
    assert "9 calls recorded, 0 API errors retried" in out.out
    assert "the most the nine calls can cost" in out.out
    assert sorted(p.name for p in search.directory.iterdir()) == logs_before  # no log was written


def test_the_command_asks_before_spending_and_a_no_sends_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    case = world(tmp_path)
    provider, made = Replies(case), list[str]()
    monkeypatch.setattr("builtins.input", lambda prompt="": "n")
    assert run_cli(monkeypatch, provider, made=made) == REFUSED_EXIT
    err = capsys.readouterr().err
    assert "not confirmed: nothing was sent" in err and COMPANY not in err
    assert provider.requests == [] and made == [] and probe_files(case) == []


def test_the_command_refuses_a_row_not_at_not_known_with_a_rule_and_no_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    case = world(tmp_path, log=pool_log(upto="maps_to_shape"))
    provider = Replies(case)
    assert run_cli(monkeypatch, provider, "--yes") == REFUSED_EXIT
    err = capsys.readouterr().err
    assert "refused:" in err and "maps_to_shape" in err and COMPANY not in err
    assert provider.requests == []


# --- reasoning is read as the answer (item 4, dated note of 2026-10-21) ---------------------------------


def test_an_unknown_with_reasoning_is_his_to_read_and_says_so(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    case = world(tmp_path)
    reasoned = dataclasses.replace(ok("unknown"), reasoning_block_count=1)
    outcome = run(case, Replies(case, reasoned))
    first, rest = outcome.results[0], outcome.results[1:]
    assert first.unknown and first.reasoning and first.to_read
    assert all(r.unknown and not r.reasoning and not r.to_read for r in rest)
    assert load(case, "knowledge-probe-haiku-5-5-1-reply.json")["reasoning_block_count"] == 1


def test_the_command_counts_a_reasoned_unknown_among_those_to_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    case = world(tmp_path)
    reasoned = dataclasses.replace(ok("unknown"), reasoning_block_count=1)
    assert run_cli(monkeypatch, Replies(case, reasoned), "--yes") == CLEAN_EXIT
    assert (
        "haiku-5-5: 3 calls, 3 answered exactly 'unknown', 1 with reasoning, 1 for him to read"
        in capsys.readouterr().out
    )


# --- the build is only a shape the probe asked about (item 4, dated note of 2026-10-21) -----------------


def probed(tmp_path: Path, inputs: str = S3_TEXT) -> CaseAppendix:
    case = world(tmp_path, inputs)
    run(case, Replies(case))
    return case


@pytest.mark.parametrize(
    ("inputs", "allowed", "refused"),
    [(S3_TEXT, ["S3"], ["S1", "S2", "S4"]), (S1_TEXT, ["S1", "S2"], ["S3", "S4"])],
)
def test_a_pool_row_is_built_only_as_a_shape_its_probe_asked_about(
    tmp_path: Path, inputs: str, allowed: list[str], refused: list[str]
) -> None:
    case = probed(tmp_path, inputs)
    search = CaseAppendix(case.root, "search")
    assert probed_shape(case) == load_inputs(case).shape
    for shape in allowed:
        check_build_shape(search, case, shape)
    for shape in refused:
        with pytest.raises(KnowledgeError, match=f"a build as {shape} would ask"):
            check_build_shape(search, case, shape)


def test_a_pool_row_with_no_probe_records_or_two_shapes_is_refused(tmp_path: Path) -> None:
    case = world(tmp_path)
    search = CaseAppendix(case.root, "search")
    with pytest.raises(KnowledgeError, match="no knowledge-probe records"):
        check_build_shape(search, case, "S3")
    run(case, Replies(case))
    path = case.directory / "knowledge-probe-haiku-5-5-2-request.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    path.chmod(0o644)
    path.write_text(json.dumps({**record, "shape": "S1"}), encoding="utf-8")
    with pytest.raises(KnowledgeError, match="more than one shape"):
        probed_shape(case)


def test_a_row_that_is_not_a_pool_row_is_not_checked(tmp_path: Path) -> None:
    root = tmp_path / "appendix"
    world(tmp_path)  # writes the pre-registered log with closure-01
    check_build_shape(CaseAppendix(root, "search"), CaseAppendix(root, "closure-01"), "S4")


def test_the_build_refuses_another_question_before_any_fetch_or_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    case = probed(tmp_path)
    search = CaseAppendix(case.root, "search")
    log = pool_log()
    log.record(LABEL, KNOWLEDGE, "pass", "r")  # 3c's result, after the probe
    write_exploratory_version(search, log)
    record = {"list": [{"id": LABEL, "ciks": ["0009999999"]}]}
    search.write_once(search.directory / "pre-candidates.json", json.dumps(record).encode())
    monkeypatch.setattr(cli, "UrllibTransport", lambda: pytest.fail("fetched"))
    monkeypatch.setattr(cli, "_extraction_provider", lambda: pytest.fail("asked for a key"))
    cutoff = (DISCLOSED - timedelta(days=1)).isoformat()

    def build(shape: str) -> int:
        return main(["case", "build", LABEL, "--cutoff", cutoff, "--shape", shape])

    assert build("S1") == REFUSED_EXIT
    err = capsys.readouterr().err
    assert "probed as S3; a build as S1" in err and COMPANY not in err
    assert build("S3") == REFUSED_EXIT  # past the shape check, stopped by the missing term list
    assert "term list" in capsys.readouterr().err
