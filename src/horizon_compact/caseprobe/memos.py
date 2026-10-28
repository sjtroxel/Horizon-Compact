"""``hc case memos``: the company-name scan of every model-written text of a case sweep (Phase 5.5
IMPLEMENTATION doc §5.4, K4; protocol §12.11).

**It runs after the reveal**, on a sweep ``hc case match`` has already read (its results file is there), from
a checkout whose code is committed. Every text the models wrote in a run's final attempt is read by two
nets: the **lists** (the private term file, found through the name guard's own configuration, and SEC's
list of filer names and tickers, fetched through the one EDGAR client and its hash recorded) and the
**model net** (Haiku 5.5, in shuffled batches of at most 25 under opaque ids). Anything either net flags
goes to the independent reader, one memo at a time, which says per flagged word whether it names a real
company, brand or ticker. **A memo with a confirmed name is held back and counted, never edited**; one
the reader clears is published. He may overrule the reader toward holding
(``memo-overrules-<model>.toml`` in the case's folder); the file has no verb that publishes.

**What is scanned:** the tool call's ``memo``, and the text blocks of a reply with no tool call (also of a
failed attempt that is the run's final). Never reasoning. ``read_runs`` (frozen) gives the rows but not the
texts, so the final attempt's record is read here, by named fields only.

**What stays private, and what is printed.** Flags, flagged words, the SEC list's hash, every Haiku and reader
request and reply are written once in the case's folder of the appendix. The command prints counts, and
nothing it prints, and no refusal message, holds a flagged word or a memo's text. The public files are
``<model>-memos.jsonl`` (one line per run, the text or ``"held"``) and ``<model>-memos-summary.json`` (the
counts, by reason, and the provenance), each written once by a link. **The results file ``hc case match``
wrote is never amended** (it is write-once): the held counts go to the summary file beside it.

**Resumable, and why.** Every paid call is recorded, request before call and reply after, and a rerun reads
the records instead of calling again. That is what lets him read the flags, write his overrules and apply
them: he deletes the two uncommitted public files, adds ``memo-overrules-<model>.toml`` and runs the command
again, at no cost. A request with no reply (a call that never returned) is refused until he has looked. A
rerun whose lists or flags differ from the first run's is refused.

**Spend is confirmed before it is spent**, once for each of the two paid passes, and only when the pass has a
call left to make. The keys are asked for last.

Needs scipy through the matcher's material (``match.py``), which the container image leaves out: ``cli.py``
imports this inside its command only.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import tomllib
from collections import Counter
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.edgar import EdgarClient
from horizon_compact.casebuild.extraction_model import entry_sha256
from horizon_compact.casebuild.frozen import Git
from horizon_compact.caseprobe.layout import runs_prefix
from horizon_compact.caseprobe.match import (
    load_material,
    read_sweep,
    results_path,
)
from horizon_compact.caseprobe.run import ProbeRefused, check_probe_model, probe_route
from horizon_compact.experiment import MODELS_FILE
from horizon_compact.model_config import ModelConfig, ModelsFile
from horizon_compact.privacy.guard import GuardError, term_file_path
from horizon_compact.privacy.names import TermFile, TermFileError, find_terms, load_term_file
from horizon_compact.protocol.lock import check_lock
from horizon_compact.providers.base import (
    RawDecision,
    TextProvider,
    TextRequest,
    text_prompt_sha256,
)
from horizon_compact.reader import memo as memo_reader
from horizon_compact.reader.briefs import Brief, frozen_reader_inputs, load_brief
from horizon_compact.reader.entry import load_reader_model, reader_route
from horizon_compact.reader.read import CHARS_PER_TOKEN, MAX_ATTEMPTS
from horizon_compact.sweep.plan import SweepRefusal
from horizon_compact.sweep.spend import (
    attempt_cost_usd,
    estimate_input_tokens_text,
    worst_case_attempt_usd,
)
from horizon_compact.sweep.store import Store

RECORD_VERSION = 1
SUMMARY_VERSION = 1
SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
# The model net's model is the experiment's main model: its models.toml entry gives the id, route and prices.
NAMES_KEY = "haiku-5-5"
# A batch of at most 25 memos answered with a short list of names each; only the tokens used are paid for.
NAMES_MAX_TOKENS = 4096
MAX_NAMES_ATTEMPTS = 2  # the reply, and one re-ask for a batch that did not account for every memo
MAX_READ_ATTEMPTS = MAX_ATTEMPTS
MEMO_SOURCE_MEMO, MEMO_SOURCE_REPLY = "memo", "reply_text"
HELD = "held"
HELD_REASONS = ("name_confirmed", "reader_unclear", "reader_no_reply", "overruled")


class MemosRefused(SweepRefusal):
    """The memo scan cannot run, or stopped. The message holds a kind of failure and a file name, never a
    flagged word or a memo's text. A ``SweepRefusal`` so ``cli.py`` catches it without this import."""


# --- the texts ---------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class MemoText:
    run_id: str
    objective: str
    wording: str
    status: str
    source: (
        str | None
    )  # MEMO_SOURCE_MEMO, MEMO_SOURCE_REPLY, or None when the final attempt wrote no text
    text: str | None


def _json(store: Store, key: str) -> dict[str, Any]:
    text = store.get(key)
    try:
        loaded = json.loads(text) if text is not None else None
    except ValueError:
        loaded = None
    if not isinstance(loaded, dict):
        raise MemosRefused(f"{key} cannot be read as a record")
    return loaded


def final_text(attempt: dict[str, Any]) -> tuple[str | None, str | None]:
    """The text a final attempt published its voice in: the first tool call's memo, or, when it made no tool
    call, its text blocks. Named fields only; reasoning is never read."""
    calls = attempt.get("tool_calls")
    if isinstance(calls, list) and calls:
        first = calls[0]
        given = first.get("input") if isinstance(first, dict) else None
        memo = given.get("memo") if isinstance(given, dict) else None
        if isinstance(memo, str) and memo.strip():
            return MEMO_SOURCE_MEMO, memo
        return None, None
    blocks = attempt.get("text_blocks")
    if isinstance(blocks, list):
        text = "\n\n".join(b for b in blocks if isinstance(b, str) and b.strip())
        if text.strip():
            return MEMO_SOURCE_REPLY, text
    return None, None


def collect_texts(store: Store, prefix: str, rows: Sequence[Any]) -> list[MemoText]:
    """One entry per run of the sweep, in run-id order, from its final attempt's record."""
    found: list[MemoText] = []
    for row in sorted(rows, key=lambda r: r.run_id):
        base = f"{prefix}runs/{row.run_id}/"
        final = _json(store, f"{base}final.json")
        number = final.get("final_attempt")
        if not isinstance(number, int):
            raise MemosRefused(f"{base}final.json names no final attempt")
        source, text = final_text(_json(store, f"{base}attempt-{number}.json"))
        found.append(
            MemoText(row.run_id, row.objective_id, row.wording_id, row.status, source, text)
        )
    return found


# --- the lists net -----------------------------------------------------------------------------------------

_TOKEN = re.compile(
    r"[^\W_]+"
)  # a run of letters and digits, as the name guard's whole-word rule sees one
# The ends of an SEC title that are not part of the name: a state or class tag ("/DE/") and a legal form.
_TITLE_TAIL = re.compile(r"\s*/[^/]{1,12}/?\s*$")
_SUFFIXES = frozenset(
    {
        "inc", "incorporated", "corp", "corporation", "co", "company", "ltd", "limited", "llc",
        "lp", "llp", "plc", "nv", "sa", "ag", "se",
    }
)  # fmt: skip
MIN_NAME_CHARS = 4
MAX_NAME_WORDS = 10
# A ticker counts only where the text marks it as one: after an exchange ("NYSE: X", "Nasdaq X"), a dollar
# sign ("$X") or the word ticker ("ticker symbol X"). Bare, a one- or two-letter ticker is an ordinary
# capitalized word ("A", "AI"); a bare ticker is the model net's to find (§5.4's dated note of 2026-10-28).
_MARKED_TICKER = re.compile(
    r"(?:\b(?:NYSE American|NYSE Arca|NYSE|NASDAQ|Nasdaq|AMEX|OTCQX|OTCQB|OTC)\s*[:\-]?\s*"
    r"|\$|\b[Tt]icker(?:\s+symbol)?\s*[:\-]?\s*)"
    r"([A-Z][A-Z0-9]*(?:[.\-][A-Z0-9]+)?)(?![A-Za-z0-9])"
)


def load_term_file_with_hash() -> tuple[TermFile, str]:
    """The private term file, found as the name guard finds it, and its sha256. Fails closed."""
    try:
        path = term_file_path()
        term_file = load_term_file(path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except (GuardError, TermFileError, OSError) as exc:
        raise MemosRefused(f"the private term file cannot be used ({type(exc).__name__})") from exc
    return term_file, digest


def _name_words(title: str) -> tuple[str, ...]:
    words = _TOKEN.findall(_TITLE_TAIL.sub("", title))
    while len(words) > 1 and words[-1].lower() in _SUFFIXES:
        words.pop()
    return tuple(words)


@dataclass(frozen=True)
class ListNet:
    """The private term file and SEC's names and tickers. A name matches as whole words, case-sensitively; a
    ticker only in capitals and only where the text marks it as a ticker (``_MARKED_TICKER``)."""

    term_file: TermFile
    names: frozenset[tuple[str, ...]]
    tickers: frozenset[tuple[str, ...]]

    def words_in(self, text: str) -> list[str]:
        """Every flagged word of ``text``, once, in order of first appearance: the term file's, then SEC's
        names, then SEC's marked tickers."""
        found = list(dict.fromkeys(m.term for m in find_terms(text, self.term_file)))
        tokens = _TOKEN.findall(text)
        for start in range(len(tokens)):
            for width in range(1, min(MAX_NAME_WORDS, len(tokens) - start) + 1):
                gram = tuple(tokens[start : start + width])
                if gram in self.names:
                    found.append(" ".join(gram))
        for hit in _MARKED_TICKER.finditer(text):
            if tuple(_TOKEN.findall(hit.group(1))) in self.tickers:
                found.append(hit.group(1))
        return list(dict.fromkeys(found))


def build_list_net(term_file: TermFile, sec_body: bytes) -> ListNet:
    """SEC's ``company_tickers.json`` (an object of ``{cik_str, ticker, title}``) into the two sets. A name
    shorter than four characters once its legal form is stripped is dropped; a ticker is kept whatever its
    length, in capitals only, and matched only where marked. An all-capitals title is also matched in its
    capitalized form, since the SEC's casing is not a writer's."""
    try:
        listing = json.loads(sec_body)
        entries = list(listing.values())
        pairs = [(str(e["ticker"]), str(e["title"])) for e in entries]
    except (ValueError, AttributeError, KeyError, TypeError) as exc:
        raise MemosRefused("SEC's list of filers is not the shape expected") from exc
    if not pairs:
        raise MemosRefused("SEC's list of filers is empty")
    names: set[tuple[str, ...]] = set()
    tickers: set[tuple[str, ...]] = set()
    for ticker, title in pairs:
        words = _name_words(title)
        if words and len(" ".join(words)) >= MIN_NAME_CHARS and len(words) <= MAX_NAME_WORDS:
            names.add(words)
            if all(w.isupper() for w in words if not w.isdigit()):
                names.add(tuple(w.capitalize() for w in words))
        symbol = tuple(_TOKEN.findall(ticker))
        if symbol and ticker == ticker.upper():
            tickers.add(symbol)
    return ListNet(term_file, frozenset(names), frozenset(tickers))


# --- the records -------------------------------------------------------------------------------------------


def _dump(record: dict[str, Any]) -> bytes:
    return (json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


@dataclass(frozen=True)
class _Attempt:
    number: int
    request: dict[str, Any] | None
    reply: dict[str, Any] | None


def _load(path: Path) -> dict[str, Any]:
    try:
        loaded = json.loads(path.read_text("utf-8"))
    except (OSError, ValueError) as exc:
        raise MemosRefused(f"{path.name} cannot be read") from exc
    if not isinstance(loaded, dict):
        raise MemosRefused(f"{path.name} is not a record")
    return loaded


def _attempts(case: CaseAppendix, stem: str) -> list[_Attempt]:
    pattern = re.compile(rf"{re.escape(stem)}-(\d+)-(request|reply)\.json")
    numbers: dict[int, set[str]] = {}
    if case.directory.is_dir():
        for path in case.directory.iterdir():
            hit = pattern.fullmatch(path.name)
            if hit:
                numbers.setdefault(int(hit.group(1)), set()).add(hit.group(2))
    found = []
    for number in sorted(numbers):
        kinds = numbers[number]
        request = (
            _load(case.directory / f"{stem}-{number}-request.json") if "request" in kinds else None
        )
        reply = _load(case.directory / f"{stem}-{number}-reply.json") if "reply" in kinds else None
        if request is not None and reply is None:
            raise MemosRefused(
                f"{stem}-{number}-request.json has no reply (a call that never returned): look in the "
                "case's folder before running again"
            )
        found.append(_Attempt(number, request, reply))
    return found


@dataclass(frozen=True)
class _State:
    """Where one call stands: ``done`` (a usable reply is on record), ``failed`` (the attempts are used up),
    or ``todo`` (``remaining`` more may be made). A call that failed at the API is not an attempt."""

    kind: str
    reply: dict[str, Any] | None
    next_number: int
    remaining: int


def _state(attempts: list[_Attempt], limit: int) -> _State:
    counted = [a for a in attempts if a.reply is not None and a.reply.get("status") == "ok"]
    for attempt in counted:
        assert attempt.reply is not None
        if attempt.reply.get("usable") is True:
            return _State("done", attempt.reply, 0, 0)
    following = max((a.number for a in attempts), default=0) + 1
    if len(counted) >= limit:
        return _State("failed", None, following, 0)
    return _State("todo", None, following, limit - len(counted))


def _check_request(attempts: list[_Attempt], user: str) -> None:
    """A stored request must be the one this run would send now: the records belong to this scan."""
    for attempt in attempts:
        if attempt.request is not None and attempt.request.get("user") != user:
            raise MemosRefused(
                f"a stored request of this scan is not the one this run would send: {attempt.number}"
            )


def _call(
    case: CaseAppendix,
    stem: str,
    number: int,
    fields: dict[str, Any],
    request: TextRequest,
    provider: TextProvider,
    config: ModelConfig,
    judge: Callable[[RawDecision], tuple[bool, str | None, Any]],
) -> dict[str, Any]:
    """The request record, the call, then the reply record. The request is written before the call."""
    body = _jsonable(provider.text_request_body(request))
    case.write_once(
        case.directory / f"{stem}-{number}-request.json",
        _dump(
            {
                **fields,
                "record_version": RECORD_VERSION,
                "attempt": number,
                "prompt_sha256": text_prompt_sha256(request),
                "max_tokens": request.max_tokens,
                "system": request.system,
                "user": request.user,
                "request": body,
            }
        ),
    )
    raw = provider.decide_text(request)
    usable, problem, parsed = judge(raw)
    reply = {
        "record_version": RECORD_VERSION,
        "attempt": number,
        "status": raw.status,
        "stop_reason": raw.stop_reason,
        "usable": usable,
        "problem": problem,
        "parsed": parsed,
        "text": "\n".join(raw.text_blocks),
        "error": raw.error,
        "usage": {
            "input_tokens": raw.usage.input_tokens,
            "output_tokens": raw.usage.output_tokens,
        },
        "estimated_usd": attempt_cost_usd(raw.usage, config.prices),
        "provenance": _jsonable(raw.provenance),
        "raw_response": _jsonable(raw.raw_response),
    }
    case.write_once(case.directory / f"{stem}-{number}-reply.json", _dump(reply))
    if raw.status != "ok":
        code = (raw.error or {}).get("code", "unknown")
        raise MemosRefused(
            f"a call failed ({code}) and nothing further was sent: run the command again to go on "
            "from the records"
        )
    return reply


# --- the model net -----------------------------------------------------------------------------------------


@dataclass(frozen=True)
class NamesPreview:
    """What the first spend question shows. No memo, no word."""

    model_id: str
    memos: int
    batches: int
    calls_at_most: int
    input_tokens_at_most: int
    worst_case_usd: float
    flagged_by_lists: int


@dataclass(frozen=True)
class ReaderPreview:
    """What the second spend question shows. No memo, no word."""

    model_id: str
    memos: int
    input_tokens_at_most: int
    worst_case_usd: float
    retries_worst_case_usd: float


def names_model(repo_root: Path) -> tuple[str, ModelConfig]:
    path = repo_root / "experiment" / MODELS_FILE
    try:
        models = ModelsFile.model_validate(tomllib.loads(path.read_text(encoding="utf-8")))
        config = models.models[NAMES_KEY]
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError, ValueError, KeyError) as exc:
        raise MemosRefused(
            f"{MODELS_FILE} has no usable {NAMES_KEY} entry ({type(exc).__name__})"
        ) from exc
    try:
        check_probe_model(NAMES_KEY, config)
    except ProbeRefused as exc:
        raise MemosRefused(str(exc)) from exc
    return NAMES_KEY, config


def batches_of(texts: Sequence[MemoText], seed: str) -> list[list[MemoText]]:
    """The memos with text, shuffled with a seed fixed by the scan (so a rerun asks the same questions), in
    batches of at most ``NAMES_BATCH``."""
    pool = [t for t in texts if t.text is not None]
    random.Random(int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16], 16)).shuffle(pool)
    size = memo_reader.NAMES_BATCH
    return [pool[i : i + size] for i in range(0, len(pool), size)]


def _names_judge(ids: Sequence[str]) -> Callable[[RawDecision], tuple[bool, str | None, Any]]:
    def judge(raw: RawDecision) -> tuple[bool, str | None, Any]:
        if raw.status != "ok":
            return False, f"the call failed ({(raw.error or {}).get('code', 'unknown')})", None
        if raw.stop_reason != "end_turn":
            return False, f"the reply stopped early ({raw.stop_reason})", None
        parsed, problem = memo_reader.parse_names_reply("\n".join(raw.text_blocks), ids)
        return parsed is not None, problem, parsed

    return judge


@dataclass(frozen=True)
class NamesOutcome:
    flagged: dict[
        str, list[str]
    ]  # run id -> the names Haiku listed (only memos with a non-empty list)
    unaccounted: frozenset[str]  # run ids of a batch Haiku did not account for twice
    calls: int
    cost_usd: float


def names_pass(
    case: CaseAppendix,
    batches: Sequence[Sequence[MemoText]],
    *,
    model: str,
    names: tuple[str, ModelConfig],
    brief: Brief,
    frozen: dict[str, Any],
    flagged_by_lists: int,
    confirm: Callable[[NamesPreview], bool],
    make_provider: Callable[[], TextProvider],
) -> NamesOutcome:
    key, config = names
    route = probe_route(key, config)
    plan: list[tuple[str, memo_reader.MemoMaterial, tuple[str, ...], list[_Attempt], _State]] = []
    for index, batch in enumerate(batches, start=1):
        stem = f"memos-{model}-names-{index:03d}"
        ids = memo_reader.batch_ids(len(batch))
        material = memo_reader.names_material([t.text or "" for t in batch])
        attempts = _attempts(case, stem)
        _check_request(attempts, material.user)
        plan.append((stem, material, ids, attempts, _state(attempts, MAX_NAMES_ATTEMPTS)))

    todo = [p for p in plan if p[4].kind == "todo"]
    tokens = sum(estimate_input_tokens_text(brief.text, p[1].user) for p in todo)
    worst = sum(
        p[4].remaining
        * worst_case_attempt_usd(
            estimate_input_tokens_text(brief.text, p[1].user), NAMES_MAX_TOKENS, config.prices
        )
        for p in todo
    )
    calls_at_most = sum(p[4].remaining for p in todo)
    if todo:
        preview = NamesPreview(
            config.model_id,
            sum(len(b) for b in batches),
            len(todo),
            calls_at_most,
            tokens,
            round(worst, 6),
            flagged_by_lists,
        )
        if not confirm(preview):
            raise MemosRefused("not confirmed: nothing was sent")
        provider = make_provider()  # the key, last; a refusal here leaves no record
    calls, cost = 0, 0.0
    flagged: dict[str, list[str]] = {}
    unaccounted: set[str] = set()
    for (stem, material, ids, attempts, state), batch in zip(plan, batches, strict=True):
        while state.kind == "todo":
            request = TextRequest(route, brief.text, material.user, NAMES_MAX_TOKENS)
            fields = {
                "kind": "memo-names-request",
                "label": case.label,
                "model_key": key,
                "entry_sha256": entry_sha256(key, config),
                "brief": brief.name,
                "brief_sha256": brief.sha256,
                "material_sha256": material.parts,
                "frozen": frozen,
                "batch": int(stem.rsplit("-", 1)[1]),
            }
            reply = _call(
                case, stem, state.next_number, fields, request, provider, config, _names_judge(ids)
            )
            calls += 1
            cost += float(reply["estimated_usd"])
            attempts = _attempts(case, stem)
            state = _state(attempts, MAX_NAMES_ATTEMPTS)
        if state.kind == "failed":
            unaccounted.update(t.run_id for t in batch)
            continue
        assert state.reply is not None
        parsed = state.reply["parsed"]
        for memo_id, text in zip(ids, batch, strict=True):
            if parsed[memo_id]:
                flagged[text.run_id] = list(parsed[memo_id])
    return NamesOutcome(flagged, frozenset(unaccounted), calls, round(cost, 6))


# --- the flags, and the independent reader -----------------------------------------------------------------


@dataclass(frozen=True)
class MemoFlags:
    run_id: str
    lists: tuple[str, ...]
    model: tuple[str, ...]
    unaccounted: bool

    @property
    def flagged(self) -> bool:
        return bool(self.lists or self.model or self.unaccounted)

    @property
    def words(self) -> list[str]:
        return list(dict.fromkeys([*self.lists, *self.model]))


@dataclass(frozen=True)
class ReadOutcome:
    verdicts: dict[
        str, str | None
    ]  # run id -> confirmed / unclear / cleared, None when no usable reply
    calls: int
    cost_usd: float


def _reader_judge(flag_count: int) -> Callable[[RawDecision], tuple[bool, str | None, Any]]:
    def judge(raw: RawDecision) -> tuple[bool, str | None, Any]:
        if raw.status != "ok":
            return False, f"the call failed ({(raw.error or {}).get('code', 'unknown')})", None
        if raw.stop_reason != "end_turn":
            return False, f"the reply stopped early ({raw.stop_reason})", None
        parsed, problem = memo_reader.parse_memo_reply("\n".join(raw.text_blocks), flag_count)
        if parsed is None:
            return False, problem, None
        return True, None, {"verdict": parsed.verdict, "answers": parsed.answers}

    return judge


def reader_pass(
    case: CaseAppendix,
    flagged: Sequence[tuple[MemoText, MemoFlags]],
    *,
    model: str,
    repo_root: Path,
    brief: Brief,
    frozen: dict[str, Any],
    confirm: Callable[[ReaderPreview], bool],
    make_provider: Callable[[], TextProvider],
) -> ReadOutcome:
    key, config = load_reader_model(repo_root / "experiment")
    assert config.max_tokens is not None  # a reader entry always has one (ModelConfig checks)
    route = reader_route(key, config)
    plan = []
    for text, flags in flagged:
        assert text.text is not None
        material = memo_reader.memo_material(text.text, flags.words)
        stem = f"memos-{model}-read-{text.run_id}"
        attempts = _attempts(case, stem)
        _check_request(attempts, material.user)
        plan.append((text, flags, stem, material, _state(attempts, MAX_READ_ATTEMPTS)))

    todo = [p for p in plan if p[4].kind == "todo"]
    each = [
        worst_case_attempt_usd(
            (len(brief.text) + len(p[3].user)) // CHARS_PER_TOKEN + 1,
            config.max_tokens,
            config.prices,
        )
        for p in todo
    ]
    if todo:
        preview = ReaderPreview(
            config.model_id,
            len(todo),
            sum((len(brief.text) + len(p[3].user)) // CHARS_PER_TOKEN + 1 for p in todo),
            round(sum(each), 6),
            round(sum(c * p[4].remaining for c, p in zip(each, todo, strict=True)), 6),
        )
        if not confirm(preview):
            raise MemosRefused("not confirmed: nothing was sent")
        provider = make_provider()
    calls, cost = 0, 0.0
    verdicts: dict[str, str | None] = {}
    for text, flags, stem, material, state in plan:
        while state.kind == "todo":
            request = TextRequest(route, brief.text, material.user, config.max_tokens)
            fields = {
                "kind": "memo-read-request",
                "label": case.label,
                "run_id": text.run_id,
                "reader_model": key,
                "reader_entry_sha256": entry_sha256(key, config),
                "brief": brief.name,
                "brief_sha256": brief.sha256,
                "material_sha256": material.parts,
                "flagged_words": flags.words,
                "unaccounted_by_the_model_net": flags.unaccounted,
                "frozen": frozen,
            }
            reply = _call(
                case,
                stem,
                state.next_number,
                fields,
                request,
                provider,
                config,
                _reader_judge(len(flags.words)),
            )
            calls += 1
            cost += float(reply["estimated_usd"])
            state = _state(_attempts(case, stem), MAX_READ_ATTEMPTS)
        verdicts[text.run_id] = state.reply["parsed"]["verdict"] if state.reply else None
    return ReadOutcome(verdicts, calls, round(cost, 6))


# --- his overrules -----------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Overrule:
    run_id: str
    reason: str


def load_overrules(
    case: CaseAppendix, model: str, texts: dict[str, MemoText]
) -> tuple[list[Overrule], str | None]:
    """His overrules and the file's sha256 (None when there is no file). The only verb is hold: an entry that
    would publish, one for a run with no text or no run at all, a repeat and one without a reason are
    refused, and nothing is spent. Messages name a run id and a rule, never the reason he wrote."""
    path = case.memo_overrules_path(model)
    if not path.exists():
        return [], None
    try:
        data = path.read_bytes()
        table = tomllib.loads(data.decode("utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise MemosRefused(f"{path.name} cannot be read ({type(exc).__name__})") from exc
    if set(table) - {"overrule"} or not isinstance(table.get("overrule"), list):
        raise MemosRefused(f"{path.name} holds [[overrule]] entries and nothing else")
    found: list[Overrule] = []
    for entry in table["overrule"]:
        if not isinstance(entry, dict) or set(entry) - {"run_id", "reason", "action"}:
            raise MemosRefused(
                f"an entry in {path.name} has keys other than run_id, reason, action"
            )
        run_id, reason = entry.get("run_id"), entry.get("reason")
        if not isinstance(run_id, str) or not isinstance(reason, str) or not reason.strip():
            raise MemosRefused(f"an entry in {path.name} needs a run_id and a reason")
        if entry.get("action", "hold") != "hold":
            raise MemosRefused(
                f"the entry for {run_id} would publish a memo: an overrule can only hold one"
            )
        if run_id not in texts or texts[run_id].text is None:
            raise MemosRefused(f"the entry for {run_id} names no memo of this sweep to hold")
        if any(o.run_id == run_id for o in found):
            raise MemosRefused(f"{path.name} holds two entries for {run_id}")
        found.append(Overrule(run_id, reason.strip()))
    return found, hashlib.sha256(data).hexdigest()


# --- the scan ----------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ScanResult:
    memos_path: Path
    summary_path: Path
    counts: dict[str, Any]
    cost_usd: float


def _write_once(path: Path, text: str) -> None:
    """Written beside itself and linked into place: an existing file (or a second command racing this one)
    is refused and never replaced."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    try:
        os.link(temporary, path)
    except FileExistsError as exc:
        raise MemosRefused(f"{path.name} exists: it is never overwritten") from exc
    finally:
        temporary.unlink(missing_ok=True)


def memos_paths(root: Path, label: str, model_key: str) -> tuple[Path, Path]:
    base = results_path(root, label, model_key).parent
    return base / f"{model_key}-memos.jsonl", base / f"{model_key}-memos-summary.json"


def _lines(held: dict[str, str], texts: Sequence[MemoText]) -> Iterator[dict[str, Any]]:
    for text in texts:
        if text.text is None:
            memo: str | None = None
        else:
            memo = HELD if text.run_id in held else text.text
        yield {
            "run_id": text.run_id,
            "objective": text.objective,
            "wording": text.wording,
            "status": text.status,
            "source": text.source,
            "memo": memo,
        }


def run_memo_scan(
    root: Path,
    store: Store,
    label: str,
    model_key: str,
    sweep_id: str,
    *,
    appendix: Path,
    head: str,
    git: Git,
    sec: EdgarClient,
    confirm_names: Callable[[NamesPreview], bool],
    confirm_reader: Callable[[ReaderPreview], bool],
    make_names_provider: Callable[[], TextProvider],
    make_reader_provider: Callable[[], TextProvider],
) -> ScanResult:
    # --- every refusal that needs no byte to leave the machine
    memos_path, summary_path = memos_paths(root, label, model_key)
    reasons = [
        f"{path.relative_to(root).as_posix()} exists: it is never overwritten (delete it, uncommitted, to "
        "go on from the records)"
        for path in (memos_path, summary_path)
        if path.exists()
    ]
    if not results_path(root, label, model_key).exists():
        reasons.append(
            "the case's results file for this model is not there: the memo scan runs after the reveal "
            "(`hc case match`)"
        )
    report = check_lock(root)
    reasons += [f"hc protocol check fails on this checkout: {line}" for line in report.failures]
    if reasons:
        raise MemosRefused("\n".join(reasons))
    frozen = frozen_reader_inputs(git)
    names = names_model(root)
    names_brief, memo_brief = load_brief(root, "memo-names"), load_brief(root, "memo")
    material = load_material(root, store, label, appendix)
    runset = read_sweep(store, material, model_key, sweep_id)
    case = CaseAppendix(appendix, label)
    texts = collect_texts(store, runs_prefix(label, sweep_id), runset.rows)
    by_run = {t.run_id: t for t in texts}
    overrules, overrules_sha = load_overrules(case, model_key, by_run)
    term_file, term_file_sha = load_term_file_with_hash()

    # --- the lists net (SEC's list is the one fetch; a free one, cached in the case's folder)
    try:
        listing = sec.get(SEC_TICKERS_URL)
    except Exception as exc:
        raise MemosRefused(
            f"SEC's list of filers could not be fetched ({type(exc).__name__})"
        ) from exc
    net = build_list_net(term_file, listing.body)
    on_lists = {t.run_id: tuple(net.words_in(t.text)) for t in texts if t.text is not None}

    # --- the model net
    seed = f"{label}|{model_key}|{sweep_id}"
    batches = batches_of(texts, seed)
    flagged_by_lists = sum(1 for words in on_lists.values() if words)
    named = names_pass(
        case,
        batches,
        model=model_key,
        names=names,
        brief=names_brief,
        frozen=frozen,
        flagged_by_lists=flagged_by_lists,
        confirm=confirm_names,
        make_provider=make_names_provider,
    )
    flags = {
        t.run_id: MemoFlags(
            t.run_id,
            on_lists[t.run_id],
            tuple(named.flagged.get(t.run_id, ())),
            t.run_id in named.unaccounted,
        )
        for t in texts
        if t.text is not None
    }
    _record_flags(
        case,
        model_key,
        sweep_id,
        flags,
        {
            "sec_sha256": listing.sha256,
            "sec_fetched_at": listing.fetched_at,
            "term_file_sha256": term_file_sha,
            "sec_names": len(net.names),
            "sec_tickers": len(net.tickers),
        },
    )

    # --- the independent reader, on every flagged memo
    to_read = [(by_run[run_id], f) for run_id, f in sorted(flags.items()) if f.flagged]
    read = reader_pass(
        case,
        to_read,
        model=model_key,
        repo_root=root,
        brief=memo_brief,
        frozen=frozen,
        confirm=confirm_reader,
        make_provider=make_reader_provider,
    )

    # --- the decisions, his overrules, and the two public files
    held: dict[str, str] = {}
    for text, _ in to_read:
        verdict = read.verdicts[text.run_id]
        if verdict == memo_reader.CONFIRMED:
            held[text.run_id] = "name_confirmed"
        elif verdict == memo_reader.UNCLEAR:
            held[text.run_id] = "reader_unclear"
        elif verdict is None:
            held[text.run_id] = "reader_no_reply"
    applied = [o for o in overrules if o.run_id not in held]
    for overrule in applied:
        held[overrule.run_id] = "overruled"
    if overrules_sha is not None:
        _record_overrules(case, model_key, overrules_sha, overrules, applied)

    with_text = [t for t in texts if t.text is not None]
    verdicts = Counter(v for v in read.verdicts.values() if v is not None)
    counts: dict[str, Any] = {
        "runs": len(texts),
        "with_text": len(with_text),
        "without_text": len(texts) - len(with_text),
        "flagged_by_lists": flagged_by_lists,
        "flagged_by_model": sum(1 for f in flags.values() if f.model),
        "model_net_unaccounted": sum(1 for f in flags.values() if f.unaccounted),
        "flagged_by_both": sum(1 for f in flags.values() if f.lists and f.model),
        "flagged": len(to_read),
        "reader_confirmed": verdicts[memo_reader.CONFIRMED],
        "reader_unclear": verdicts[memo_reader.UNCLEAR],
        "reader_cleared": verdicts[memo_reader.CLEARED],
        "reader_no_reply": sum(1 for v in read.verdicts.values() if v is None),
        "held": len(held),
        "held_by_reason": {r: sum(1 for v in held.values() if v == r) for r in HELD_REASONS},
        "overruled": len(applied),
        "published": len(with_text) - len(held),
    }
    lock = material.lock
    summary = {
        "summary_version": SUMMARY_VERSION,
        "case": label,
        "exploratory": True,
        "exploratory_label": material.exploratory_label,
        "model_key": model_key,
        "sweep_id": sweep_id,
        "counts": counts,
        "provenance": {
            "head": head,
            "protocol": lock.protocol,
            "protocol_check": "ok",
            "analysis_sha256": lock.analysis.sha256,
            "uv_lock_sha256": lock.analysis.uv_lock_sha256,
            "names_brief_sha256": names_brief.sha256,
            "memo_brief_sha256": memo_brief.sha256,
            "names_entry_sha256": entry_sha256(*names),
            "reader_inputs_commit": frozen["reader_inputs_commit"],
            "sec_list_sha256": listing.sha256,
            "overrules_sha256": overrules_sha,
        },
    }
    lines = "".join(
        json.dumps(line, ensure_ascii=False, sort_keys=True) + "\n" for line in _lines(held, texts)
    )
    summary_text = json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    _write_once(memos_path, lines)
    _write_once(summary_path, summary_text)
    return ScanResult(memos_path, summary_path, counts, round(named.cost_usd + read.cost_usd, 6))


def _record_flags(
    case: CaseAppendix,
    model: str,
    sweep_id: str,
    flags: dict[str, MemoFlags],
    lists: dict[str, Any],
) -> None:
    """The flags of the scan, written once in the appendix (they hold the flagged words). A rerun recomputes
    them and refuses unless every memo's flags are the same. The lists' hashes are recorded but not compared:
    an edit to the term file that flags nothing new (a term for another case) must not block his overrules."""
    record = {
        "record_version": RECORD_VERSION,
        "label": case.label,
        "model_key": model,
        "sweep_id": sweep_id,
        "lists": lists,
        "memos": {
            run_id: {
                "lists": list(f.lists),
                "model": list(f.model),
                "model_net_unaccounted": f.unaccounted,
            }
            for run_id, f in sorted(flags.items())
        },
    }
    path = case.directory / f"memos-{model}-flags.json"
    if path.exists():
        stored, found = _load(path), json.loads(json.dumps(record))
        stored.pop("lists", None)
        found.pop("lists")
        if stored != found:
            raise MemosRefused(
                f"{path.name} differs from what this run found: the lists, the replies or the texts "
                "changed since the first run; look before going on"
            )
        return
    case.write_once(path, _dump(record))


def _record_overrules(
    case: CaseAppendix,
    model: str,
    sha256: str,
    overrules: Sequence[Overrule],
    applied: Sequence[Overrule],
) -> None:
    """Each overrule with his reason, and whether it changed a decision, once per version of his file."""
    path = case.directory / f"memos-{model}-overrules-{sha256[:12]}.json"
    if path.exists():
        return
    applied_ids = {o.run_id for o in applied}
    case.write_once(
        path,
        _dump(
            {
                "record_version": RECORD_VERSION,
                "file_sha256": sha256,
                "overrules": [
                    {
                        "run_id": o.run_id,
                        "reason": o.reason,
                        "held_a_published_memo": o.run_id in applied_ids,
                    }
                    for o in overrules
                ],
            }
        ),
    )
