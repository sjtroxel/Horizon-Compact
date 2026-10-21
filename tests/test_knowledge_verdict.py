"""Step 3's knowledge verdict (search-half IMPLEMENTATION doc §4.6.5 step 3 item 4 and its dated notes of
2026-10-21; exploratory plan, part 3c): his read of the probe's replies, the failing replies written for the
independent reader, the reader's new brief and material, and the log's read of ``not_known``. A fake provider
throughout: no model is called, no key is read. Fictional canaries only."""

from __future__ import annotations

import dataclasses
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from horizon_compact import cli
from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.exploratory import (
    KNOWLEDGE,
    load_newest_exploratory,
    write_exploratory_version,
)
from horizon_compact.caseprobe.knowledge import KnowledgeError
from horizon_compact.caseprobe.knowledge_read import (
    knowledge_verdict,
    load_replies,
    reasoning_texts,
)
from horizon_compact.cli import CLEAN_EXIT, REFUSED_EXIT, main
from horizon_compact.dossier.check import default_repo_root
from horizon_compact.providers.base import RawDecision
from horizon_compact.reader.briefs import load_brief
from horizon_compact.reader.material import (
    KNOWLEDGE_DEFINITIONS,
    MaterialError,
    flagged_replies_text,
    knowledge_rejection_material,
    rejection_material,
)
from horizon_compact.reader.read import ReaderError, parse_reply, rejection_reply_on_record
from test_casebuild_extract import ok
from test_knowledge_probe import (
    COMPANY,
    LABEL,
    S1_TEXT,
    S3_MESSAGE,
    S3_TEXT,
    Replies,
    api_error,
    pool_log,
    run,
    world,
)
from test_reader import Replies as ReaderReplies
from test_reader import says

ROOT = default_repo_root()
SEARCH = "search"


@pytest.fixture(autouse=True)
def _appendix_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HC_APPENDIX_DIR", str(tmp_path / "appendix"))


def reasoned(text: str = "unknown", *, reasoning: bool = True) -> RawDecision:
    return dataclasses.replace(ok(text), reasoning_block_count=1 if reasoning else 0)


def probed(tmp_path: Path, *script: RawDecision, inputs: str = S3_TEXT) -> CaseAppendix:
    case = world(tmp_path, inputs)
    run(case, Replies(case, *script))
    return case


def answers(*words: str) -> Callable[[str], str]:
    queue = list(words)
    return lambda prompt: queue.pop(0)


def verdict(case: CaseAppendix, *words: str) -> tuple[Any, list[str]]:
    shown: list[str] = []
    done = knowledge_verdict(
        case, CaseAppendix(case.root, SEARCH), ask=answers(*words), show=shown.append
    )
    return done, shown


# --- the reasoning a reply carries ----------------------------------------------------------------------


def test_reasoning_is_taken_from_openrouters_message_and_anthropics_thinking_blocks() -> None:
    assert reasoning_texts({"choices": [{"message": {"reasoning": " I recall it. "}}]}) == (
        "I recall it.",
    )
    blocks = [
        {"type": "thinking", "thinking": "hmm"},
        {"type": "redacted_thinking"},
        {"type": "text", "text": "unknown"},
    ]
    assert reasoning_texts({"content": blocks}) == (
        "hmm",
        "(redacted reasoning: no text to read)",
    )
    assert reasoning_texts({"choices": [{"message": {"content": "unknown"}}]}) == ()
    assert reasoning_texts(None) == () and reasoning_texts({"choices": "x"}) == ()


# --- the replies that stand -----------------------------------------------------------------------------


def test_the_reply_that_stands_for_a_call_is_its_last_replacement(tmp_path: Path) -> None:
    case = probed(tmp_path, ok(), ok("Fernwick closed it"))
    replies = load_replies(case)
    assert [(r.model_key, r.call) for r in replies][:3] == [
        ("gpt-oss-openrouter", 1),
        ("gpt-oss-openrouter", 2),
        ("gpt-oss-openrouter", 3),
    ]
    haiku = {r.call: r for r in replies if r.model_key == "haiku-5-5"}
    assert haiku[1].replacements == 1 and haiku[1].answer == "Fernwick closed it"
    assert haiku[1].file == "knowledge-probe-haiku-5-5-1-replacement-1-reply.json"
    assert haiku[2].replacements == 0 and len(replies) == 9


def test_an_incomplete_or_missing_probe_is_refused(tmp_path: Path) -> None:
    case = world(tmp_path)
    with pytest.raises(KnowledgeError, match="no knowledge-probe replies"):
        load_replies(case)
    probed_case = probed(tmp_path / "other")
    (probed_case.directory / "knowledge-probe-haiku-5-5-3-reply.json").unlink()
    with pytest.raises(KnowledgeError, match="not complete"):
        load_replies(probed_case)


def test_a_run_stopped_in_the_last_calls_replacement_is_refused_not_read_as_empty_three_times(
    tmp_path: Path,
) -> None:
    case = world(tmp_path)
    # eight calls answer, the ninth is empty, and its replacement stops the run on a fatal API error
    script = [ok("unknown")] * 8 + [ok(), api_error("AccessDeniedException")]
    with pytest.raises(KnowledgeError, match="stopped at sonnet-5-5-extraction call 3"):
        run(case, Replies(case, *script))
    with pytest.raises(KnowledgeError, match=r"replacement-1-request\.json has no reply"):
        verdict(case)
    assert not case.knowledge_reads_path.exists() and not case.knowledge_flagged_path.exists()


# --- his read -------------------------------------------------------------------------------------------


def test_nine_unknowns_need_no_read_and_pass(tmp_path: Path) -> None:
    case = probed(tmp_path)
    done, shown = verdict(case)
    assert (done.stage, done.calls, done.read_by_him, done.failing, done.empty) == (
        "passed",
        9,
        0,
        0,
        0,
    )
    assert shown == [] and not case.knowledge_flagged_path.exists()
    assert case.knowledge_reads_path.is_file()


def test_a_reply_that_is_not_unknown_is_shown_with_the_question_and_asked_about(
    tmp_path: Path,
) -> None:
    case = probed(tmp_path, ok("It makes pumps."), ok("Fernwick will close it."))
    done, shown = verdict(case, "n", "y")
    text = "\n".join(shown)
    assert S3_MESSAGE in text and "It makes pumps." in text and "Fernwick will close it." in text
    assert KNOWLEDGE_DEFINITIONS["facility"] in text
    assert (done.stage, done.read_by_him, done.failing) == ("needs_reader", 2, 1)
    flagged = json.loads(case.knowledge_flagged_path.read_text())
    assert flagged["shape"] == "S3" and flagged["question"] == S3_MESSAGE
    assert [r["answer"] for r in flagged["replies"]] == ["Fernwick will close it."]


def test_an_unknown_that_carries_reasoning_is_still_read_and_the_reasoning_is_shown(
    tmp_path: Path,
) -> None:
    raw = {"choices": [{"message": {"reasoning": "I recall the plant was shut."}}]}
    case = probed(tmp_path, dataclasses.replace(reasoned(), raw_response=raw))
    done, shown = verdict(case, "y")
    assert any("I recall the plant was shut." in line for line in shown)
    assert done.stage == "needs_reader" and done.failing == 1
    flagged = json.loads(case.knowledge_flagged_path.read_text())
    assert flagged["replies"][0]["reasoning"] == ["I recall the plant was shut."]


def test_a_call_empty_three_times_fails_by_rule_and_nothing_goes_to_the_reader(
    tmp_path: Path,
) -> None:
    case = probed(tmp_path, ok(), ok(), ok())
    done, shown = verdict(case)  # no answer is needed: there is nothing to read
    assert (done.stage, done.failing, done.empty, done.read_by_him) == ("failed_empty", 1, 1, 0)
    assert shown == [] and not case.knowledge_flagged_path.exists()
    assert case.knowledge_reads_path.is_file()


def test_an_empty_call_beside_a_read_failure_still_fails_by_rule_with_no_reader(
    tmp_path: Path,
) -> None:
    case = probed(tmp_path, ok(), ok(), ok(), ok("Fernwick will close it."))
    done, _ = verdict(case, "y")
    assert (done.stage, done.failing, done.empty, done.read_by_him) == ("failed_empty", 2, 1, 1)
    assert not case.knowledge_flagged_path.exists()


def test_a_cut_off_reply_is_read_as_it_stands(tmp_path: Path) -> None:
    case = probed(tmp_path, ok("It makes pumps and may have", stop="max_tokens"))
    done, shown = verdict(case, "n")
    assert (done.stage, done.read_by_him) == ("passed", 1)
    assert any("status truncated" in line for line in shown)


def test_his_reads_are_saved_once_and_a_rerun_asks_nothing(tmp_path: Path) -> None:
    case = probed(tmp_path, ok("It makes pumps."))
    verdict(case, "n")
    done, shown = verdict(case)  # no answers available: it must not ask
    assert done.stage == "passed" and shown == []


def test_a_rerun_after_the_replies_changed_is_refused(tmp_path: Path) -> None:
    case = probed(tmp_path, ok("It makes pumps."))
    verdict(case, "n")
    reply = case.directory / "knowledge-probe-haiku-5-5-1-reply.json"
    record = json.loads(reply.read_text())
    reply.chmod(0o644)
    reply.write_text(json.dumps({**record, "answer": "changed"}), encoding="utf-8")
    with pytest.raises(KnowledgeError, match="other replies"):
        verdict(case)


def test_a_reply_that_is_neither_y_nor_n_is_asked_again_then_nothing_is_saved(
    tmp_path: Path,
) -> None:
    case = probed(tmp_path, ok("It makes pumps."))
    with pytest.raises(KnowledgeError, match="no y or n"):
        verdict(case, "maybe", "", "x")
    assert not case.knowledge_reads_path.exists()
    done, _ = verdict(case, "maybe", "no")  # a stray word is asked again, never read as n
    assert done.stage == "passed"


def test_the_verdict_is_refused_for_a_row_that_is_not_at_not_known(tmp_path: Path) -> None:
    case = probed(tmp_path)
    search = CaseAppendix(case.root, SEARCH)
    log = pool_log()
    log.record(LABEL, KNOWLEDGE, "pass", "r")
    write_exploratory_version(search, log)
    with pytest.raises(KnowledgeError, match="already has a result"):
        verdict(case)


def test_a_failing_set_writes_the_same_flagged_file_on_a_rerun_and_refuses_a_different_one(
    tmp_path: Path,
) -> None:
    case = probed(tmp_path, ok("Fernwick will close it."))
    verdict(case, "y")
    verdict(case)  # the same record: nothing is written again
    case.knowledge_flagged_path.chmod(0o644)
    case.knowledge_flagged_path.write_text('{"x": 1}', encoding="utf-8")
    with pytest.raises(KnowledgeError, match="differs from the failing replies"):
        verdict(case)


def test_an_s1_probe_is_given_the_reduction_definition(tmp_path: Path) -> None:
    case = probed(tmp_path, ok("It cut jobs."), inputs=S1_TEXT)
    done, shown = verdict(case, "y")
    assert KNOWLEDGE_DEFINITIONS["reduction"] in "\n".join(shown)
    # item 4's dated note (d): the reduction question's own words are not a reply's
    assert "only repeats this, or takes it as given" in KNOWLEDGE_DEFINITIONS["reduction"]
    assert "only repeats" not in KNOWLEDGE_DEFINITIONS["facility"]
    assert json.loads(case.knowledge_flagged_path.read_text())["shape"] == "S1"
    assert done.failing == 1


# --- the reader's brief and material --------------------------------------------------------------------


def test_a_not_known_read_has_its_own_brief_and_the_other_briefs_are_unchanged() -> None:
    knowledge = load_brief(ROOT, "rejection", KNOWLEDGE)
    assert knowledge.name == "knowledge.txt"
    assert load_brief(ROOT, "rejection").name == "rejection.txt"
    assert load_brief(ROOT, "rejection", "real_decision").name == "rejection.txt"
    assert load_brief(ROOT, "scenario", KNOWLEDGE).name == "scenario.txt"
    assert knowledge.sha256 != load_brief(ROOT, "rejection").sha256


def test_the_knowledge_brief_asks_for_one_json_object_and_names_no_result_and_no_company() -> None:
    text = load_brief(ROOT, "rejection", KNOWLEDGE).text
    for word in ('"pass"', '"fail"', '"cannot_tell"', "not_known", "reasoning", "only repeats"):
        assert word in text, word
    assert (
        "EMPTY" not in text and "workforce reduction" not in text
    )  # notes (e) and the closing fix
    assert text.rstrip().endswith("the decision the definition names, or gives a figure of it.")
    for word in ("grid", "sweep", "objective a", "esg", "stakeholder capitalism", "dossier"):
        assert word not in text.lower(), word


def test_the_knowledge_brief_asks_the_reply_format_the_reader_parses() -> None:
    reply = {
        "criterion": KNOWLEDGE,
        "reading": "fail",
        "shape": None,
        "type": None,
        "reason": "Reply 1 states it.",
        "alternative": None,
    }
    parsed, problem = parse_reply("rejection", KNOWLEDGE, json.dumps(reply))
    assert problem is None and parsed is not None and parsed["reading"] == "fail"
    for bad in ({**reply, "shape": "S3"}, {**reply, "type": "closure"}):
        assert parse_reply("rejection", KNOWLEDGE, json.dumps(bad))[0] is None
    assert parse_reply("rejection", "real_decision", json.dumps(reply))[0] is None


def test_the_material_is_the_definition_the_question_and_the_failing_replies_only(
    tmp_path: Path,
) -> None:
    case = probed(tmp_path, ok("Fernwick will close it."), ok("It was sold."))
    verdict(case, "y", "y")
    material = knowledge_rejection_material(case)
    assert material.user.startswith(f"Criterion to read: {KNOWLEDGE}\n\n")
    assert list(material.parts) == ["Definition", "Question asked", "Flagged replies"]
    assert KNOWLEDGE_DEFINITIONS["facility"] in material.user and S3_MESSAGE in material.user
    assert "Reply 1:\nAnswer: Fernwick will close it.\nReasoning: (none shown)" in material.user
    assert "Reply 2:\nAnswer: It was sold." in material.user and "EMPTY" not in material.user
    for key in ("haiku", "gpt-oss", "sonnet", "knowledge-probe"):
        assert key not in material.user
    assert rejection_material(case, KNOWLEDGE).parts == material.parts


def test_the_flagged_text_marks_a_cut_off_reply_and_shows_reasoning() -> None:
    text = flagged_replies_text(
        [
            {"answer": "", "status": "truncated", "reasoning": ["a", "b"], "empty": False},
            {"answer": "x", "status": "replied", "reasoning": [], "empty": False},
        ]
    )
    assert text.startswith("Reply 1: [cut off at the length limit]\nAnswer: (no answer text)")
    assert "Reasoning: a\nb" in text and "Reply 2:\nAnswer: x" in text


def test_the_material_is_refused_without_a_flagged_file_or_with_a_bad_one(tmp_path: Path) -> None:
    case = probed(tmp_path)
    with pytest.raises(MaterialError, match="flagged knowledge-probe replies"):
        knowledge_rejection_material(case)
    case.knowledge_flagged_path.write_text('{"shape": "S9"}', encoding="utf-8")
    with pytest.raises(MaterialError, match="knowledge-verdict"):
        knowledge_rejection_material(case)
    # a call empty three times is never read (note (e)), so a file holding one is not the verdict's
    empty = {"shape": "S3", "question": "q", "replies": [{"answer": "", "empty": True}]}
    case.knowledge_flagged_path.write_text(json.dumps(empty), encoding="utf-8")
    with pytest.raises(MaterialError, match="knowledge-verdict"):
        knowledge_rejection_material(case)
    with pytest.raises(MaterialError, match="only a probe read names a probe set"):
        rejection_material(case, KNOWLEDGE, 1)


# --- the command, the reader, and the log ---------------------------------------------------------------


def run_verdict(monkeypatch: pytest.MonkeyPatch, *words: str) -> int:
    queue = list(words)
    monkeypatch.setattr("builtins.input", lambda prompt="": queue.pop(0))
    return main(["case", "knowledge-verdict", LABEL])


def test_the_command_prints_counts_and_the_next_commands_and_logs_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    case = probed(tmp_path)
    search = CaseAppendix(case.root, SEARCH)
    logs = sorted(p.name for p in search.directory.iterdir())
    assert run_verdict(monkeypatch) == CLEAN_EXIT
    out = capsys.readouterr().out
    assert "9 calls; 0 replies read by him; 0 empty three times; 0 call(s) fail" in out
    assert f'hc case xlog record {LABEL} {KNOWLEDGE} pass --reason "..."' in out
    assert COMPANY not in out
    assert sorted(p.name for p in search.directory.iterdir()) == logs


def test_the_command_shows_the_replies_to_him_and_names_the_reader_command_on_a_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    probed(tmp_path, ok("Fernwick will close it."))
    assert run_verdict(monkeypatch, "y") == CLEAN_EXIT
    out = capsys.readouterr().out
    assert "Fernwick will close it." in out and "1 call(s) fail" in out
    assert f"hc case reader {LABEL} rejection --criterion {KNOWLEDGE}" in out
    assert f"hc case xlog read {LABEL} {KNOWLEDGE}" in out


def test_the_command_refuses_a_candidate_with_no_probe(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    world(tmp_path)
    assert main(["case", "knowledge-verdict", LABEL]) == REFUSED_EXIT
    assert "no knowledge-probe replies" in capsys.readouterr().err


def test_the_command_saves_nothing_when_the_input_ends(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    case = probed(tmp_path, ok("It makes pumps."))

    def eof(prompt: str = "") -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", eof)
    assert main(["case", "knowledge-verdict", LABEL]) == REFUSED_EXIT
    assert "nothing was saved" in capsys.readouterr().err
    assert not case.knowledge_reads_path.exists()


READER_FAIL = {
    "criterion": KNOWLEDGE,
    "reading": "fail",
    "shape": None,
    "type": None,
    "reason": "Reply 1 states the closure.",
    "alternative": None,
}


def failed_row(tmp_path: Path, *script: RawDecision) -> CaseAppendix:
    """A probed candidate with a failing reply, his read made, and the log holding the failure."""
    case = probed(tmp_path, *script)
    verdict(case, "y")
    search = CaseAppendix(case.root, SEARCH)
    log = load_newest_exploratory(search)
    log.record(LABEL, KNOWLEDGE, "fail", "a reply states the closure")
    write_exploratory_version(search, log)
    return case


def read_with_reader(monkeypatch: pytest.MonkeyPatch, provider: ReaderReplies, *words: str) -> int:
    from test_casebuild_frozen import fake_git

    monkeypatch.setattr(cli, "_reader_provider", lambda: provider)
    monkeypatch.setattr(cli, "git_in", lambda repo: fake_git())
    return main(["case", "reader", LABEL, "rejection", "--criterion", KNOWLEDGE, "--yes", *words])


def test_the_reader_reads_the_failing_replies_with_the_knowledge_brief_and_logs_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    case = failed_row(tmp_path, ok("Fernwick will close it."))
    provider = ReaderReplies(says(READER_FAIL))
    assert read_with_reader(monkeypatch, provider) == CLEAN_EXIT
    out = capsys.readouterr().out
    request = json.loads(
        (case.directory / f"reader-rejection-{KNOWLEDGE}-1-request.json").read_text()
    )
    brief = load_brief(ROOT, "rejection", KNOWLEDGE)
    assert request["brief"] == "knowledge.txt" and request["brief_sha256"] == brief.sha256
    assert provider.requests[0].system == brief.text
    assert set(request["material_sha256"]) == {"Definition", "Question asked", "Flagged replies"}
    assert "reader's reading: fail" in out and "agrees: the rejection stands" in out
    assert f"hc case xlog read {LABEL} {KNOWLEDGE}" in out
    assert "Fernwick" not in out and "close" not in out


def test_a_knowledge_failure_is_read_once_and_needs_the_log_to_hold_the_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    case = probed(tmp_path, ok("Fernwick will close it."))
    verdict(case, "y")  # his read made, but the log holds no failure yet
    provider = ReaderReplies(says(READER_FAIL))
    assert read_with_reader(monkeypatch, provider) == REFUSED_EXIT
    assert f"no rejection on {KNOWLEDGE}" in capsys.readouterr().err
    assert provider.requests == []


def test_the_log_takes_a_reader_pass_as_a_dispute_that_needs_his_resolution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    failed_row(tmp_path, ok("Fernwick will close it."))
    provider = ReaderReplies(says({**READER_FAIL, "reading": "pass"}))
    assert read_with_reader(monkeypatch, provider) == CLEAN_EXIT
    assert "DISPUTES" in capsys.readouterr().out
    assert main(["case", "xlog", "read", LABEL, KNOWLEDGE]) == REFUSED_EXIT
    assert "resolved by him" in capsys.readouterr().err
    assert (
        main(["case", "xlog", "read", LABEL, KNOWLEDGE, "--resolution", "he finds it holds"])
        == CLEAN_EXIT
    )
    row = load_newest_exploratory(CaseAppendix(tmp_path / "appendix", SEARCH)).rows[LABEL]
    assert row.reads[KNOWLEDGE].agrees is False and row.met(KNOWLEDGE)


def test_a_reader_fail_stands_and_the_log_records_the_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    case = failed_row(tmp_path, ok("Fernwick will close it."))
    assert read_with_reader(monkeypatch, ReaderReplies(says(READER_FAIL))) == CLEAN_EXIT
    capsys.readouterr()
    assert main(["case", "xlog", "read", LABEL, KNOWLEDGE]) == CLEAN_EXIT
    row = load_newest_exploratory(CaseAppendix(case.root, SEARCH)).rows[LABEL]
    assert row.reads[KNOWLEDGE].agrees is True and row.failed == KNOWLEDGE
    reply = rejection_reply_on_record(case, KNOWLEDGE)
    assert reply.reading == "fail" and reply.reply.startswith("reader-rejection-not_known")
    with pytest.raises(ReaderError, match="not a criterion the reader reads"):
        rejection_reply_on_record(case, "not_a_criterion")


# --- a call empty three times, in the log (item 4's dated note (e)) -------------------------------------


def test_the_command_names_the_empty_record_and_no_reader_when_a_call_was_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    probed(tmp_path, ok(), ok(), ok())
    assert run_verdict(monkeypatch) == CLEAN_EXIT
    out = capsys.readouterr().out
    assert f'hc case xlog record {LABEL} {KNOWLEDGE} fail --empty --reason "..."' in out
    assert "hc case reader" not in out and "1 empty three times" in out


def xrecord(*extra: str) -> int:
    return main(["case", "xlog", "record", LABEL, KNOWLEDGE, *extra, "--reason", "why"])


def test_an_empty_failure_is_logged_with_empty_and_is_never_read_or_disputed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    case = probed(tmp_path, ok(), ok(), ok())
    verdict(case)
    assert xrecord("fail") == REFUSED_EXIT
    assert "record the failure with --empty" in capsys.readouterr().err
    assert xrecord("fail", "--empty") == CLEAN_EXIT
    capsys.readouterr()
    log = load_newest_exploratory(CaseAppendix(case.root, SEARCH))
    row = log.rows[LABEL]
    assert row.failed == KNOWLEDGE and row.empty_fail and row.finished
    assert row.awaiting_read is None and log.problems() == []
    assert main(["case", "xlog", "read", LABEL, KNOWLEDGE]) == REFUSED_EXIT
    capsys.readouterr()
    provider = ReaderReplies(says(READER_FAIL))
    assert read_with_reader(monkeypatch, provider) == REFUSED_EXIT
    assert "fails by rule and is never read" in capsys.readouterr().err
    assert provider.requests == []
    from horizon_compact.casebuild.search import LogError, ReaderReply

    with pytest.raises(LogError, match="is read"):  # nor a dispute logged by hand
        log.record_read(
            LABEL, KNOWLEDGE, reply=ReaderReply("r.json", "0" * 64, "pass"), resolution="x"
        )


def test_empty_is_refused_on_a_failure_that_was_read_and_without_his_saved_reads(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    case = probed(tmp_path, ok("Fernwick will close it."))
    assert xrecord("fail") == REFUSED_EXIT  # his read is not saved yet
    assert "knowledge-verdict" in capsys.readouterr().err
    verdict(case, "y")
    assert xrecord("fail", "--empty") == REFUSED_EXIT
    assert "--empty does not apply" in capsys.readouterr().err
    assert xrecord("fail") == CLEAN_EXIT
    row = load_newest_exploratory(CaseAppendix(case.root, SEARCH)).rows[LABEL]
    assert not row.empty_fail and row.awaiting_read == KNOWLEDGE


def test_the_log_takes_empty_only_on_a_pool_rows_not_known_failure(tmp_path: Path) -> None:
    from horizon_compact.casebuild.search import LogError

    log = pool_log()
    with pytest.raises(LogError, match="empty three times"):
        log.record(LABEL, KNOWLEDGE, "pass", "why", empty=True)
    carried = pool_log(upto="real_decision")
    with pytest.raises(LogError, match="empty three times"):
        carried.record(LABEL, "real_decision", "fail", "why", empty=True)
    log.record(LABEL, KNOWLEDGE, "fail", "why", empty=True)
    replayed = type(log).from_text(log.to_text())
    assert replayed.rows[LABEL].empty_fail and replayed.rows[LABEL].awaiting_read is None
