"""``hc case probe-verdict``: whether each probe answer names the company (protocol §12.8), and the one
record per call the gate's check (3) reads.

**Two steps, because a reader's dispute can turn a failure into a pass** (KNOWN-GAPS 2026-10-16, criterion 5,
his decision). The verdict record of a call is write-once and carries the *final* ``passed``, so it is written
only when the set is settled:

1. **The read.** Each answer is shown once, with a hint from the case's term list. An answer that is exactly
   "unknown" needs no read; any other he confirms or overrules (§12.8: "one human read of every answer that is
   not 'unknown'"). Everything he decides is saved to ``probe-reads-set-<n>.json`` (write-once), so a
   re-run never asks again. If no answer names the company, every call passes and the verdicts are written.
2. **A failure.** The answers that name the company go to ``probe-flagged-set-<n>.json``, and the independent
   reader reads them (``hc case reader <id> rejection --criterion not_recognizable``): shown only §12.8's
   definition, those answers and the term list. The verdicts are written once that read is on record:
   "fail" agrees and the flagged calls fail; "cannot_tell" is not a dispute, so they fail (decision 8);
   "pass" disputes, and with his written resolution the flagged calls pass. A disputed failure is not
   coarsened.

Each verdict holds the original verdict, the reply's file name and sha256, his resolution on a dispute and the
final ``passed``; the gate reads only ``passed`` (``caseprobe/s3reader.py``), so the selection log (which logs
the reply's reading) and the gate always agree.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any

from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.terms import CaseTerm, parse_case_terms
from horizon_compact.caseprobe.layout import (
    PROBE_CALLS,
    CallKey,
    parse_call_key,
    probes_prefix,
    verdict_key,
)
from horizon_compact.reader.material import PROBE_CRITERION, flagged_answers_text, part_sha256
from horizon_compact.reader.read import ReaderError, probe_reply_on_record, reply_material
from horizon_compact.sweep.store import Store

RECORD_VERSION = 1
_UNKNOWN = re.compile(r"[\s\W_]*unknown[\s\W_]*", re.IGNORECASE)
# His read is saved write-once, so only a plain yes or no is taken: an empty reply or a typo is asked again,
# never read as "does not name it".
_YES = frozenset({"y", "yes"})
_NO = frozenset({"n", "no"})
ASK_LIMIT = 3
QUESTION = "Does this answer name the company, a former name, its ticker or a brand? [y/n] "


class VerdictError(Exception):
    """A verdict cannot be reached or written. The message names a file and a rule, never an answer."""


@dataclass(frozen=True)
class Call:
    key: str
    where: CallKey
    object_sha256: str
    status: str
    answer: str


@dataclass(frozen=True)
class Read:
    """What was decided about one answer, from the term list and from him."""

    key: str
    model_key: str
    call: int
    answer_sha256: str
    unknown: bool
    term_hit: bool
    names: bool  # the answer names the company: the original verdict is "fail"


@dataclass(frozen=True)
class VerdictOutcome:
    probe_set: int
    stage: str  # "needs_reader" | "written"
    flagged: int
    calls: int
    written: int
    disputed: bool = False


def is_unknown(answer: str) -> bool:
    """Exactly "unknown", ignoring case, punctuation and whitespace; anything longer is read."""
    return bool(_UNKNOWN.fullmatch(answer))


def term_hit(answer: str, terms: tuple[CaseTerm, ...]) -> bool:
    return any(t.term.pattern.search(answer) for t in terms)


def names_the_company(ask: Callable[[str], str]) -> bool:
    """His answer, y or n. Anything else is asked again, up to ``ASK_LIMIT`` times, then refused: nothing
    is saved until every answer is read, so the next run asks again."""
    for _ in range(ASK_LIMIT):
        reply = ask(QUESTION).strip().lower()
        if reply in _YES:
            return True
        if reply in _NO:
            return False
    raise VerdictError("no y or n was given: nothing was saved, and the next run asks again")


def _sha256(data: bytes | str) -> str:
    return hashlib.sha256(data.encode("utf-8") if isinstance(data, str) else data).hexdigest()


def load_calls(store: Store, label: str, probe_set: int) -> list[Call]:
    """Every call object of the set, in order of model and call. Refuses an incomplete model (not
    ``PROBE_CALLS`` calls) and a set with no calls: a verdict is made on the whole set."""
    found: list[Call] = []
    for key in store.list_keys(probes_prefix(label, probe_set)):
        where = parse_call_key(key)
        if where is None:
            continue
        text = store.get(key)
        if text is None:
            raise VerdictError(f"{key} vanished while it was read")
        try:
            record = json.loads(text)
            answer = str(record["answer"])
            status = str(record["status"])
        except (ValueError, KeyError, TypeError) as exc:
            raise VerdictError(f"{key} is not a probe record ({type(exc).__name__})") from exc
        found.append(Call(key, where, _sha256(text), status, answer))
    if not found:
        raise VerdictError(f"no probe calls are stored for set {probe_set}")
    found.sort(key=lambda c: (c.where.model_key, c.where.call))
    by_model: dict[str, list[int]] = {}
    for call in found:
        by_model.setdefault(call.where.model_key, []).append(call.where.call)
    for model, numbers in by_model.items():
        if numbers != list(range(1, PROBE_CALLS + 1)):
            raise VerdictError(
                f"{model} has calls {numbers} in set {probe_set}, not 1-{PROBE_CALLS}: "
                "finish the probe first"
            )
    return found


def _write_once_json(case: CaseAppendix, path_name: str, record: dict[str, Any]) -> None:
    case.write_once(
        case.directory / path_name,
        (json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"),
    )


def _saved_reads(case: CaseAppendix, probe_set: int, calls: list[Call]) -> list[Read] | None:
    path = case.probe_reads_path(probe_set)
    if not path.is_file():
        return None
    try:
        record = json.loads(path.read_text("utf-8"))
        reads = [Read(**r) for r in record["reads"]]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise VerdictError(f"{path.name} cannot be read ({type(exc).__name__})") from exc
    if [(r.key, r.answer_sha256) for r in reads] != [(c.key, _sha256(c.answer)) for c in calls]:
        raise VerdictError(
            f"{path.name} was made on other answers than the ones now stored: look before going on"
        )
    return reads


def read_answers(
    case: CaseAppendix,
    probe_set: int,
    calls: list[Call],
    *,
    ask: Callable[[str], str],
    show: Callable[[str], None],
) -> list[Read]:
    """Step 1: the term check and his read of every answer that is not "unknown"; saved once."""
    saved = _saved_reads(case, probe_set, calls)
    if saved is not None:
        return saved
    try:
        terms = parse_case_terms(case.terms_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise VerdictError(
            f"the case's term list cannot be read ({type(exc).__name__}): {case.terms_path.name}"
        ) from exc
    reads: list[Read] = []
    for call in calls:
        answer_sha = _sha256(call.answer)
        hit = term_hit(call.answer, terms)
        unknown = call.status == "replied" and is_unknown(call.answer)
        if unknown:
            reads.append(
                Read(call.key, call.where.model_key, call.where.call, answer_sha, True, hit, False)
            )
            continue
        show(
            f"{call.where.model_key} call {call.where.call} (status {call.status}); the term list "
            f"{'FINDS a term' if hit else 'finds no term'}:"
        )
        show("  " + (call.answer.replace("\n", "\n  ") if call.answer else "(no text)"))
        names = names_the_company(ask)
        reads.append(
            Read(call.key, call.where.model_key, call.where.call, answer_sha, False, hit, names)
        )
    _write_once_json(
        case,
        case.probe_reads_path(probe_set).name,
        {
            "record_version": RECORD_VERSION,
            "probe_set": probe_set,
            "reads": [dataclasses.asdict(r) for r in reads],
            "answers": {c.key: c.answer for c in calls},
        },
    )
    return reads


def _flagged_texts(calls: list[Call], reads: list[Read]) -> list[str]:
    return [c.answer for c, r in zip(calls, reads, strict=True) if r.names]


def _ensure_flagged_file(case: CaseAppendix, probe_set: int, answers: list[str]) -> None:
    path = case.probe_flagged_path(probe_set)
    record = {"probe_set": probe_set, "answers": answers}
    if path.is_file():
        try:
            same = json.loads(path.read_text("utf-8")) == record
        except (OSError, ValueError):
            same = False
        if not same:
            raise VerdictError(
                f"{path.name} exists and differs from the flagged answers: look at it"
            )
        return
    _write_once_json(case, path.name, record)


def probe_verdict(
    case: CaseAppendix,
    store: Store,
    *,
    probe_set: int,
    resolution: str | None,
    today: date,
    ask: Callable[[str], str],
    show: Callable[[str], None],
) -> VerdictOutcome:
    calls = load_calls(store, case.label, probe_set)
    reads = read_answers(case, probe_set, calls, ask=ask, show=show)
    flagged = _flagged_texts(calls, reads)
    reply_info: dict[str, str] | None = None
    final_for_flagged = False
    disputed = False
    if flagged:
        _ensure_flagged_file(case, probe_set, flagged)
        try:
            found = probe_reply_on_record(case, probe_set)
        except ReaderError as exc:
            raise VerdictError(str(exc)) from exc
        if found is None:
            if resolution:
                raise VerdictError(
                    "the reader has not read the flagged answers yet, so there is no dispute to resolve"
                )
            return VerdictOutcome(probe_set, "needs_reader", len(flagged), len(calls), 0)
        reply, path = found
        sent = (reply_material(path) or {}).get("Flagged answers")
        if sent != part_sha256(flagged_answers_text(flagged)):
            raise VerdictError(
                f"the reader's read ({reply.reply}) was made on other answers than the flagged ones now "
                "on record: look before going on"
            )
        reply_info = {
            "reply": reply.reply,
            "reply_sha256": reply.reply_sha256,
            "reading": reply.reading,
        }
        disputed = reply.reading == "pass"
        if disputed:
            if not (resolution and resolution.strip()):
                raise VerdictError(
                    "the reader disputes the failure: the verdict needs his written resolution "
                    '(--resolution "...")'
                )
            final_for_flagged = True
        elif resolution:
            raise VerdictError(
                f"a resolution is for a reader's dispute, and the reading is {reply.reading!r}"
            )
    elif resolution:
        raise VerdictError("no answer names the company, so there is nothing to resolve")

    records: list[tuple[str, dict[str, Any]]] = []
    for call, read in zip(calls, reads, strict=True):
        record: dict[str, Any] = {
            "record_version": RECORD_VERSION,
            "label": case.label,
            "probe_set": probe_set,
            "model_key": call.where.model_key,
            "call": call.where.call,
            "call_key": call.key,
            "call_sha256": call.object_sha256,
            "answer_sha256": read.answer_sha256,
            "unknown": read.unknown,
            "term_hit": read.term_hit,
            "original_verdict": "fail" if read.names else "pass",
            "criterion": PROBE_CRITERION,
            "reader": reply_info if read.names else None,
            "resolution": resolution.strip() if read.names and disputed and resolution else None,
            "passed": (not read.names) or final_for_flagged,
        }
        records.append(
            (verdict_key(case.label, probe_set, call.where.model_key, call.where.call), record)
        )
    # Look before writing: a verdict already stored must be the one this run would write (a run that stopped
    # part-way is finished by the same command); anything else is never replaced.
    todo: list[tuple[str, dict[str, Any]]] = []
    for key, record in records:
        stored = store.get(key)
        if stored is None:
            todo.append((key, record))
            continue
        try:
            same = {k: v for k, v in json.loads(stored).items() if k != "decided"} == record
        except ValueError:
            same = False
        if not same:
            raise VerdictError(
                f"{key} is already stored and differs from this verdict: it is never replaced"
            )
    for key, record in todo:
        text = json.dumps({**record, "decided": today.isoformat()}, indent=2, sort_keys=True) + "\n"
        if not store.put_new(key, text):
            raise VerdictError(f"{key} was written by someone else while this ran")
    return VerdictOutcome(probe_set, "written", len(flagged), len(calls), len(todo), disputed)
