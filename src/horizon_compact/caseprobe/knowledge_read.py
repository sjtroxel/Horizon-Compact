"""``hc case knowledge-verdict``: his read of the knowledge probe's replies (search-half doc §4.6.5 step 3
item 4 and its dated notes of 2026-10-21), built in 3c.

The probe's records are the measurement; this reads them and decides nothing it was not told. For each of the
nine calls the **last** reply stands (a replacement, when the call's first reply held nothing):

* a call whose every reply held no answer text and no reasoning **fails** without a read: there is nothing to
  read, and the patch says it fails (note (c)); the candidate then fails by rule, with no independent read
  and no dispute (note (e));
* a reply that is exactly "unknown" and carries no reasoning passes without a read;
* every other reply is shown to him, its reasoning included (note (a)), and he answers y or n: does it state
  or guess the decision, or give a figure of it? A cut-off or odd-ending reply is read as it stands
  (note (c)).

His reads are saved to ``knowledge-reads.json``, write-once, so a re-run never asks again. If no call fails
the candidate passes ``not_known``; if a call was empty three times it fails by rule
(``hc case xlog record <id> not_known fail --empty``); otherwise the failing replies, with the shape and the
question asked, go to ``knowledge-flagged.json`` for the independent reader, who reads every failure
(``hc case reader <id> rejection --criterion not_known``). The command never writes the log: it prints the
commands to run. Nothing it prints holds a name, an answer or a reasoning, except the replies it shows him to
read, on his own terminal.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.caseprobe.knowledge import (
    CALLS,
    RECORD_PREFIX,
    KnowledgeError,
    is_unknown,
    probe_row,
)
from horizon_compact.reader.material import (
    KNOWLEDGE_DEFINITIONS,
    KNOWLEDGE_QUESTIONS,
)

RECORD_VERSION = 1
ASK_LIMIT = 3
QUESTION = "Does this reply state or guess the decision, or give a figure of it? [y/n] "
_YES = frozenset({"y", "yes"})
_NO = frozenset({"n", "no"})
_REPLY = re.compile(
    rf"{re.escape(RECORD_PREFIX)}(?P<model>.+?)-(?P<call>\d+)(?:-replacement-(?P<k>\d+))?-reply\.json"
)
MODELS = 3  # the two official models and the extraction model (item 4)


@dataclass(frozen=True)
class Reply:
    """The reply that stands for one call."""

    key: str  # "<model>-<call>"
    model_key: str
    call: int
    file: str
    sha256: str
    status: str
    answer: str
    reasoning: tuple[str, ...]
    reasoning_blocks: int
    replacements: int

    @property
    def empty(self) -> bool:
        return not self.answer.strip() and self.reasoning_blocks == 0

    @property
    def clean_unknown(self) -> bool:
        return self.status == "replied" and self.reasoning_blocks == 0 and is_unknown(self.answer)


@dataclass(frozen=True)
class Read:
    """What was decided about one call."""

    key: str
    file: str
    reply_sha256: str
    unknown: bool
    empty: bool
    fails: bool
    reason: str | None  # "empty" | "read" | None


@dataclass(frozen=True)
class VerdictOutcome:
    stage: str  # "passed" | "failed_empty" | "needs_reader"
    calls: int
    read_by_him: int
    failing: int
    empty: int


def reasoning_texts(raw_response: object) -> tuple[str, ...]:
    """The reasoning a reply carries, from the stored response: OpenRouter's ``message.reasoning``, and the
    ``thinking`` blocks of Anthropic's. A block with no text (redacted) is marked, so he knows it was
    there."""
    found: list[str] = []
    if isinstance(raw_response, dict):
        choices = raw_response.get("choices")
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            message = choices[0].get("message")
            reasoning = message.get("reasoning") if isinstance(message, dict) else None
            if isinstance(reasoning, str) and reasoning.strip():
                found.append(reasoning.strip())
        content = raw_response.get("content")
        for block in content if isinstance(content, list) else []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "thinking":
                found.append(str(block.get("thinking") or "").strip() or "(thinking with no text)")
            elif block.get("type") == "redacted_thinking":
                found.append("(redacted reasoning: no text to read)")
    return tuple(found)


def _sha256(data: bytes | str) -> str:
    return hashlib.sha256(data.encode("utf-8") if isinstance(data, str) else data).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise KnowledgeError(f"{path.name} cannot be read ({type(exc).__name__})") from exc
    if not isinstance(record, dict):
        raise KnowledgeError(f"{path.name} is not a JSON object")
    return record


def load_replies(case: CaseAppendix) -> list[Reply]:
    """The reply that stands for each of the probe's calls, in order of model key and call: the last
    replacement, else the first reply. Refused unless three models each have calls 1 to 3, and refused if any
    request has no reply: the run stopped there, and an empty reply before a replacement that never returned
    would otherwise be read as a call empty three times."""
    unanswered = sorted(
        path.name
        for path in case.directory.glob(f"{RECORD_PREFIX}*-request.json")
        if not path.with_name(path.name.removesuffix("-request.json") + "-reply.json").is_file()
    )
    if unanswered:
        raise KnowledgeError(
            f"{case.label}'s probe is not complete: {unanswered[0]} has no reply (the run stopped "
            "part-way): look in the case's folder"
        )
    standing: dict[tuple[str, int], tuple[int, Path]] = {}
    for path in case.directory.glob(f"{RECORD_PREFIX}*-reply.json"):
        match = _REPLY.fullmatch(path.name)
        if match is None:
            continue
        where = (match.group("model"), int(match.group("call")))
        k = int(match.group("k") or 0)
        if where not in standing or k > standing[where][0]:
            standing[where] = (k, path)
    by_model: dict[str, list[int]] = {}
    for model, call in standing:
        by_model.setdefault(model, []).append(call)
    if not standing:
        raise KnowledgeError(f"{case.label} has no knowledge-probe replies: run the probe first")
    if len(by_model) != MODELS or any(
        sorted(calls) != list(range(1, CALLS + 1)) for calls in by_model.values()
    ):
        raise KnowledgeError(
            f"{case.label}'s probe is not complete ({len(by_model)} models; every model needs calls "
            f"1 to {CALLS}): look in the case's folder"
        )
    replies: list[Reply] = []
    for (model, call), (k, path) in sorted(standing.items()):
        record = _load(path)
        try:
            blocks = int(record["reasoning_block_count"])
            reply = Reply(
                key=f"{model}-{call}",
                model_key=model,
                call=call,
                file=path.name,
                sha256=_sha256(path.read_bytes()),
                status=str(record["status"]),
                answer=str(record["answer"]),
                reasoning=reasoning_texts(record.get("raw_response")),
                reasoning_blocks=blocks,
                replacements=k,
            )
        except (KeyError, TypeError, ValueError, OSError) as exc:
            raise KnowledgeError(
                f"{path.name} is not a probe reply ({type(exc).__name__})"
            ) from exc
        replies.append(reply)
    return replies


def _question_asked(case: CaseAppendix, replies: list[Reply]) -> tuple[str, str]:
    """The shape and the message, from the first call's request record (every request holds the same)."""
    first = replies[0]
    record = _load(case.directory / f"{RECORD_PREFIX}{first.key}-request.json")
    shape, user = record.get("shape"), record.get("user")
    if shape not in KNOWLEDGE_QUESTIONS or not isinstance(user, str) or not user.strip():
        raise KnowledgeError(f"{RECORD_PREFIX}{first.key}-request.json holds no shape or question")
    return str(shape), user


def _ask_yes_no(ask: Callable[[str], str]) -> bool:
    """His answer, y or n. Anything else is asked again, up to ``ASK_LIMIT`` times, then refused: nothing is
    saved until every reply is read, so the next run asks again."""
    for _ in range(ASK_LIMIT):
        answer = ask(QUESTION).strip().lower()
        if answer in _YES:
            return True
        if answer in _NO:
            return False
    raise KnowledgeError("no y or n was given: nothing was saved, and the next run asks again")


def _write_once_json(case: CaseAppendix, path: Path, record: dict[str, Any]) -> None:
    case.write_once(
        path, (json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()
    )


def _saved_reads(case: CaseAppendix, replies: list[Reply]) -> list[Read] | None:
    path = case.knowledge_reads_path
    if not path.is_file():
        return None
    record = _load(path)
    try:
        reads = [Read(**r) for r in record["reads"]]
    except (KeyError, TypeError) as exc:
        raise KnowledgeError(f"{path.name} cannot be read ({type(exc).__name__})") from exc
    if [(r.key, r.reply_sha256) for r in reads] != [(r.key, r.sha256) for r in replies]:
        raise KnowledgeError(
            f"{path.name} was made on other replies than the ones now stored: look before going on"
        )
    return reads


def read_replies(
    case: CaseAppendix,
    replies: list[Reply],
    shape: str,
    question: str,
    *,
    ask: Callable[[str], str],
    show: Callable[[str], None],
) -> list[Read]:
    """His read of every reply that needs one; saved once."""
    saved = _saved_reads(case, replies)
    if saved is not None:
        return saved
    to_read = [r for r in replies if not r.empty and not r.clean_unknown]
    if to_read:
        show("The question asked:")
        show("  " + question)
        show("A reply fails if (item 4 and its notes):")
        show("  " + KNOWLEDGE_DEFINITIONS[KNOWLEDGE_QUESTIONS[shape]])
    reads: list[Read] = []
    for reply in replies:
        if reply.empty:
            reads.append(Read(reply.key, reply.file, reply.sha256, False, True, True, "empty"))
        elif reply.clean_unknown:
            reads.append(Read(reply.key, reply.file, reply.sha256, True, False, False, None))
        else:
            show(
                f"{reply.model_key} call {reply.call} (status {reply.status}; "
                f"{reply.replacements} replacements):"
            )
            show(
                "  Answer: " + (reply.answer.replace("\n", "\n  ") if reply.answer else "(no text)")
            )
            for block in reply.reasoning or (
                ("(reasoning present; its text is not in the stored response)",)
                if reply.reasoning_blocks
                else ()
            ):
                show("  Reasoning: " + block.replace("\n", "\n  "))
            fails = _ask_yes_no(ask)
            reads.append(
                Read(
                    reply.key,
                    reply.file,
                    reply.sha256,
                    False,
                    False,
                    fails,
                    "read" if fails else None,
                )
            )
    _write_once_json(
        case,
        case.knowledge_reads_path,
        {
            "record_version": RECORD_VERSION,
            "label": case.label,
            "shape": shape,
            "reads": [dataclasses.asdict(r) for r in reads],
        },
    )
    return reads


def _flagged_record(
    shape: str, question: str, replies: list[Reply], reads: list[Read]
) -> dict[str, Any]:
    return {
        "record_version": RECORD_VERSION,
        "shape": shape,
        "question": question,
        "replies": [
            {
                "answer": r.answer,
                "reasoning": list(r.reasoning),
                "status": r.status,
            }
            for r, read in zip(replies, reads, strict=True)
            if read.fails
        ],
    }


def knowledge_verdict(
    case: CaseAppendix,
    search: CaseAppendix,
    *,
    ask: Callable[[str], str],
    show: Callable[[str], None],
) -> VerdictOutcome:
    probe_row(search, case.label)  # a pool row at not_known with no result yet
    replies = load_replies(case)
    shape, question = _question_asked(case, replies)
    reads = read_replies(case, replies, shape, question, ask=ask, show=show)
    failing = [r for r in reads if r.fails]
    empty = any(r.empty for r in reads)
    outcome = VerdictOutcome(
        "failed_empty" if empty else "needs_reader" if failing else "passed",
        len(reads),
        sum(not r.unknown and not r.empty for r in reads),
        len(failing),
        sum(r.empty for r in reads),
    )
    if failing and not empty:  # a call empty three times fails by rule: nothing goes to the reader
        record = _flagged_record(shape, question, replies, reads)
        path = case.knowledge_flagged_path
        if path.is_file():
            if _load(path) != record:
                raise KnowledgeError(f"{path.name} exists and differs from the failing replies")
        else:
            _write_once_json(case, path, record)
    return outcome


def saved_empty_calls(case: CaseAppendix) -> int:
    """How many calls his saved reads count as empty three times, for the log's ``not_known`` failure:
    refused before his read is saved, or if the stored replies changed since."""
    reads = _saved_reads(case, load_replies(case))
    if reads is None:
        raise KnowledgeError(
            f"{case.label} has no saved read of its knowledge probe: run `hc case knowledge-verdict` first"
        )
    return sum(r.empty for r in reads)


__all__ = [
    "QUESTION",
    "Read",
    "Reply",
    "VerdictOutcome",
    "knowledge_verdict",
    "load_replies",
    "read_replies",
    "reasoning_texts",
    "saved_empty_calls",
]
