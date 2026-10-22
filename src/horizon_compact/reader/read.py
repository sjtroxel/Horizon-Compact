"""``hc case reader``: one independent read, recorded write-once (protocol §12.9; search-half doc §4.9).

In order, and every refusal before the first byte leaves the machine: the kind; the reader's inputs
committed and pushed; the reader's entry and the kind's brief; (for a rejection) the selection log; the
material; the case's earlier attempts; then, after the caller's confirmation of the spend, the provider, the
request record, the one call and the reply record. **The request record is written before the call**, so a
call that never returns (a crash, an interrupt) leaves a request with no reply, and the next attempt is
refused until he has looked.

**A read is made once.** Every attempt leaves a request record and a reply record, numbered, in the case's
folder. A rejection is read once, whatever its excerpt: a changed excerpt after a reading is how a reading
would be shopped for. A scenario or a rubric is read once **as it stands**: a fix after a reading changes the
material, and the changed material may be read once in its turn (every earlier read stays on record). A later
attempt on the same material is allowed only when every earlier one produced no reading (the call failed,
was cut off at the token limit, or its reply was not in the brief's format), so a reader cannot be asked again
until it says what is wanted. After a usable reply, or after ``MAX_ATTEMPTS`` unusable ones, the command
refuses.

The command never writes the selection log and never decides anything. For a rejection it prints what to
run; ``hc case log ... read`` takes the verdict from the reply file itself (``rejection_reply_on_record``). A
scenario or rubric reading of "concerns" or "disagrees" is resolved by him with ``hc case resolve``, and
``hc case lock`` refuses until the scenario and the rubric it locks have a usable read and any such
resolution (``reads_settled``; search-half doc §11, the step 9 review, decisions 6-8).
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.exploratory import (
    KNOWLEDGE,
    ExploratoryRow,
    exploratory_started,
    row_for,
)
from horizon_compact.casebuild.frozen import Git
from horizon_compact.casebuild.search import LogError, ReaderReply, Row
from horizon_compact.model_config import ModelConfig
from horizon_compact.providers.base import (
    RawDecision,
    TextProvider,
    TextRequest,
    text_prompt_sha256,
)
from horizon_compact.reader import material as materials
from horizon_compact.reader.briefs import KINDS, Brief, frozen_reader_inputs, load_brief
from horizon_compact.reader.entry import entry_sha256, load_reader_model, reader_route

RECORD_VERSION = 1
MAX_ATTEMPTS = 3
# A conservative count of characters per token, for the spend warning only.
CHARS_PER_TOKEN = 3


class ReaderError(Exception):
    """A read cannot be made, or its reply could not be used. The message never holds a name or a figure."""


# --- the replies the briefs ask for ---------------------------------------------------------------------


class _Reply(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)


class RejectionReply(_Reply):
    criterion: str
    reading: Literal["pass", "fail", "cannot_tell"]
    shape: str | None = None
    type: str | None = None
    reason: str
    alternative: str | None = None


class Concern(_Reply):
    kind: Literal["slant", "fictional_company_wording", "unequal_options", "figure_source", "other"]
    where: str
    text: str


class ScenarioReply(_Reply):
    reading: Literal["neutral", "concerns"]
    concerns: list[Concern]
    summary: str

    @model_validator(mode="after")
    def _the_reading_matches_the_list(self) -> ScenarioReply:
        if (self.reading == "neutral") != (not self.concerns):
            raise ValueError("neutral means no concerns, and concerns means at least one")
        return self


class RubricLine(_Reply):
    line: str
    your_reading: str
    agrees: bool
    note: str = ""


class RubricReply(_Reply):
    reading: Literal["agrees", "disagrees"]
    lines: list[RubricLine] = Field(min_length=1)
    reasons_stated: list[str]
    summary: str

    @model_validator(mode="after")
    def _the_reading_matches_the_lines(self) -> RubricReply:
        all_agree = bool(self.lines) and all(line.agrees for line in self.lines)
        if (self.reading == "agrees") != (all_agree and not self.reasons_stated):
            raise ValueError("agrees means every line agrees and no line states a reason")
        return self


_REPLY_MODELS: dict[str, type[_Reply]] = {
    "rejection": RejectionReply,
    "scenario": ScenarioReply,
    "rubric": RubricReply,
}


def json_object(text: str) -> dict[str, Any] | None:
    """The reply's JSON object: the whole text, a fenced block, or the span from the first ``{`` to the last
    ``}``, whichever parses first. Anything else is no object."""
    candidates = [text.strip()]
    candidates += re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    start, end = text.find("{"), text.rfind("}")
    if 0 <= start < end:
        candidates.append(text[start : end + 1])
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except ValueError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def parse_reply(
    kind: str, criterion: str | None, text: str
) -> tuple[dict[str, Any] | None, str | None]:
    """The reply as the brief's model, or the reason it is not one (a kind of failure, never the text)."""
    parsed = json_object(text)
    if parsed is None:
        return None, "the reply holds no JSON object"
    try:
        model = _REPLY_MODELS[kind].model_validate(parsed)
    except ValidationError as exc:
        fields = sorted(
            {".".join(str(p) for p in err["loc"]) or "(object)" for err in exc.errors()}
        )
        return None, "the reply does not fit the brief's format: " + ", ".join(fields)
    if isinstance(model, RejectionReply):
        if model.criterion != criterion:
            return None, "the reply names another criterion than the one asked"
        problem = _shape_problem(model)
        if problem:
            return None, problem
    return model.model_dump(), None


_SHAPES = ("S1", "S2", "S3", "S4")
# The type each shape's decision is, by protocol §12.1 (search-half doc §4.6.4): S3 is closure or retool by
# where the facility's production goes; S4 and "none" carry no type.
_SHAPE_TYPES: dict[str, tuple[str | None, ...]] = {
    "S1": ("ai",),
    "S2": ("closure",),
    "S3": ("closure", "retool"),
    "S4": (None,),
    "none": (None,),
}


def _shape_problem(reply: RejectionReply) -> str | None:
    """The shape fits the criterion and the reading: none on ``real_decision``; on ``maps_to_shape`` one of
    the four on a pass, either on a fail or cannot_tell (a fail on the total alone names the shape that
    matches, his decision 2026-10-18). The type fits the shape (§4.6.4)."""
    if reply.criterion in (
        "real_decision",
        materials.PROBE_CRITERION,
        materials.KNOWLEDGE_CRITERION,
    ):
        if reply.shape is not None:
            return f"the reply names a shape on {reply.criterion}"
        return None if reply.type is None else f"the reply names a type on {reply.criterion}"
    allowed = {
        "pass": _SHAPES,
        "fail": (*_SHAPES, "none"),
        "cannot_tell": (*_SHAPES, "none"),
    }[reply.reading]
    if reply.shape not in allowed:
        return f"the reply's shape does not fit a {reply.reading} on maps_to_shape"
    if reply.type not in _SHAPE_TYPES[reply.shape]:
        return f"the reply's type does not fit its shape {reply.shape}"
    return None


# --- the record -----------------------------------------------------------------------------------------


def stem(kind: str, criterion: str | None, probe_set: int | None = None) -> str:
    """A criterion 5 read is per probe set (``-set2``): a coarsened case is probed again, and that failure
    is read in its own right."""
    return (
        f"reader-{kind}"
        + (f"-{criterion}" if criterion else "")
        + (f"-set{probe_set}" if probe_set is not None else "")
    )


def _request_name(stem_: str, attempt: int) -> str:
    return f"{stem_}-{attempt}-request.json"


def _reply_name(stem_: str, attempt: int) -> str:
    return f"{stem_}-{attempt}-reply.json"


@dataclass(frozen=True)
class Attempt:
    """One numbered attempt on record. ``material`` is the request's part hashes (None when the request
    cannot be read: it then counts as the same material); ``usable`` is True for a reply that cannot be read
    (an unreadable reply is not a reason to ask again)."""

    number: int
    has_request: bool
    has_reply: bool
    usable: bool
    material: dict[str, str] | None
    reading: str | None
    type: str | None = None


def _load(path: Path) -> dict[str, Any] | None:
    try:
        record = json.loads(path.read_text("utf-8"))
    except (OSError, ValueError):
        return None
    return record if isinstance(record, dict) else None


def attempts_on_record(case: CaseAppendix, stem_: str) -> list[Attempt]:
    """Every attempt the folder holds for ``stem_``, by number."""
    pattern = re.compile(rf"{re.escape(stem_)}-(\d+)-(request|reply)\.json")
    numbers: dict[int, set[str]] = {}
    if case.directory.is_dir():
        for path in case.directory.iterdir():
            match = pattern.fullmatch(path.name)
            if match:
                numbers.setdefault(int(match.group(1)), set()).add(match.group(2))
    found: list[Attempt] = []
    for number in sorted(numbers):
        kinds = numbers[number]
        request = (
            _load(case.directory / _request_name(stem_, number)) if "request" in kinds else None
        )
        parts = request.get("material_sha256") if request else None
        reply = _load(case.directory / _reply_name(stem_, number)) if "reply" in kinds else None
        parsed = reply.get("parsed") if reply else None
        found.append(
            Attempt(
                number=number,
                has_request="request" in kinds,
                has_reply="reply" in kinds,
                usable="reply" in kinds and (reply is None or reply.get("usable") is True),
                material=parts if isinstance(parts, dict) else None,
                reading=str(parsed["reading"])
                if isinstance(parsed, dict) and "reading" in parsed
                else None,
                type=str(parsed["type"])
                if isinstance(parsed, dict) and parsed.get("type") is not None
                else None,
            )
        )
    return found


def _same_material(kind: str, attempts: list[Attempt], parts: dict[str, str]) -> list[Attempt]:
    """The attempts the once-only rule counts: every one for a rejection; for a scenario or a rubric, those
    on this material (or on material that cannot be read)."""
    if kind == "rejection":
        return attempts
    return [a for a in attempts if a.material is None or a.material == parts]


def _check_attempts(
    kind: str,
    name: str,
    attempts: list[Attempt],
    parts: dict[str, str],
    earlier: frozenset[str] = frozenset(),
) -> int:
    """The next attempt's number, after the once-only rule's refusals. ``earlier`` names replies of the
    pre-registered record's reads of a carried row: the rule does not count them, but the number follows
    them, so no file of theirs is written again."""
    if any(a.has_request and not a.has_reply for a in attempts):
        raise ReaderError(
            f"{name} has a request record with no reply record (a call that never returned): look in the "
            "case's folder before reading again"
        )
    counted = [a for a in attempts if _reply_name(name, a.number) not in earlier]
    same = _same_material(kind, counted, parts)
    if any(a.usable for a in same):
        what = "" if kind == "rejection" else ", as it stands,"
        raise ReaderError(f"{name}{what} was read already: a read is made once")
    if len(same) >= MAX_ATTEMPTS:
        raise ReaderError(
            f"{name} has had {MAX_ATTEMPTS} attempts with no usable reply: its reading is his to settle"
        )
    return max((a.number for a in attempts), default=0) + 1


def reader_spend_so_far(root: Path) -> tuple[Decimal, int]:
    """The reader's estimated spend across the whole appendix, from every reply record's ``estimated_usd``,
    and the number of reply records whose spend cannot be read (counted as unknown, never as zero)."""
    total, unknown = Decimal(0), 0
    for path in sorted(root.glob("*/reader-*-reply.json")):
        record = _load(path)
        try:
            spent = Decimal(str(record["estimated_usd"])) if record else None
        except (KeyError, ArithmeticError):
            spent = None
        if spent is None or not spent.is_finite() or spent < 0:
            unknown += 1
        else:
            total += spent
    return total, unknown


def _cost(usage_in: int, usage_out: int, config: ModelConfig) -> Decimal:
    return (
        Decimal(usage_in) * Decimal(str(config.prices.input))
        + Decimal(usage_out) * Decimal(str(config.prices.output))
    ) / Decimal(1_000_000)


@dataclass(frozen=True)
class Preview:
    """What the spend warning shows before anything is sent."""

    model_id: str
    kind: str
    criterion: str | None
    attempt: int
    input_tokens_at_most: int
    worst_case_usd: Decimal
    spent_so_far_usd: Decimal
    replies_of_unknown_cost: int


@dataclass(frozen=True)
class ReadOutcome:
    kind: str
    criterion: str | None
    attempt: int
    usable: bool
    problem: str | None
    reading: str | None
    parsed: dict[str, Any] | None
    input_tokens: int
    output_tokens: int
    estimated_usd: Decimal
    request_name: str
    reply_name: str
    candidate_type: str | None
    probe_set: int | None = None


def _row_of_record(search: CaseAppendix, candidate: str) -> Row | None:
    """The candidate's row (§4.6.5 B.4). A row of the pre-registered log is refused once that log is closed
    (§4.6.5 A.1): a read of it could be paid for but never logged."""
    try:
        row = row_for(search, candidate)
        closed = exploratory_started(search)
    except LogError as exc:
        raise ReaderError(f"the selection log cannot be read: {exc}") from exc
    if row is not None and closed and not isinstance(row, ExploratoryRow):
        raise ReaderError(
            f"{candidate} is in the pre-registered log, which is closed (§4.6.5 A.1); carry it with "
            "`hc case xlog carry` first"
        )
    return row


def rejection_ready(search: CaseAppendix, candidate: str, criterion: str) -> str:
    """The candidate's type, after checking the log holds a rejection on ``criterion`` with no read yet."""
    row = _row_of_record(search, candidate)
    if row is None:
        raise ReaderError(f"no candidate {candidate!r} in the log")
    result = row.results.get(criterion)
    if result is None or result.result != "fail":
        raise ReaderError(
            f"{candidate} has no rejection on {criterion} in the log: nothing to read"
        )
    if isinstance(row, ExploratoryRow) and row.empty_fail and criterion == KNOWLEDGE:
        raise ReaderError(
            f"{candidate}'s {criterion} rejection is a call empty three times: it fails by rule and is "
            "never read"
        )
    if criterion in row.reads:
        raise ReaderError(f"{candidate}'s rejection on {criterion} already has a read in the log")
    return row.type


def earlier_record_replies(search: CaseAppendix, candidate: str) -> frozenset[str]:
    """The reply files of the pre-registered record's reads of a carried row (§4.6.5 B.2). They are still in
    the case's folder and are reads of a different rejection: criterion 4 is recorded again under the
    exploratory rules and needs its own read."""
    row = _row_of_record(search, candidate)
    return row.prior_replies if isinstance(row, ExploratoryRow) else frozenset()


def probe_read_ready(search: CaseAppendix, candidate: str) -> str | None:
    """A criterion 5 read comes before the log's result (a first-set failure is not yet a rejection: it is
    coarsened unless the reader disputes it), so the log need not hold a fail. It must not already hold a
    read. Returns the candidate's type when the log has the candidate, else None."""
    row = _row_of_record(search, candidate)
    if row is None:
        return None
    if materials.PROBE_CRITERION in row.reads:
        raise ReaderError(
            f"{candidate}'s rejection on {materials.PROBE_CRITERION} already has a read in the log"
        )
    return row.type


def run_read(
    case: CaseAppendix,
    kind: str,
    criterion: str | None,
    *,
    probe_set: int | None = None,
    repo_root: Path,
    git: Git,
    search: CaseAppendix,
    confirm: Callable[[Preview], bool],
    make_provider: Callable[[], TextProvider],
) -> ReadOutcome:
    if kind not in KINDS:
        raise ReaderError(f"{kind!r} is not a kind of read: {', '.join(KINDS)}")
    if (kind == "rejection") != (criterion is not None):
        raise ReaderError("a rejection read names its criterion, and the other kinds name none")
    if (criterion == materials.PROBE_CRITERION) != (probe_set is not None):
        raise ReaderError("a read of a probe failure names its probe set, and no other read does")
    frozen = frozen_reader_inputs(git)
    key, config = load_reader_model(repo_root / "experiment")
    assert config.max_tokens is not None  # a reader entry always has one (ModelConfig checks)
    brief: Brief = load_brief(repo_root, kind, criterion)
    name = stem(kind, criterion, probe_set)
    candidate_type: str | None = None
    earlier: frozenset[str] = frozenset()
    if kind == "rejection":
        assert criterion is not None
        if criterion == materials.PROBE_CRITERION:
            candidate_type = probe_read_ready(search, case.label)
        else:
            candidate_type = rejection_ready(search, case.label, criterion)
            earlier = earlier_record_replies(search, case.label)
        material = materials.rejection_material(case, criterion, probe_set)
    elif kind == "scenario":
        material = materials.scenario_material(case, repo_root)
    else:
        material = materials.rubric_material(case)
    attempt = _check_attempts(kind, name, attempts_on_record(case, name), material.parts, earlier)
    request = TextRequest(
        route=reader_route(key, config),
        system=brief.text,
        user=material.user,
        max_tokens=config.max_tokens,
    )
    tokens_in = (len(request.system) + len(request.user)) // CHARS_PER_TOKEN + 1
    spent, unknown = reader_spend_so_far(case.root)
    preview = Preview(
        model_id=config.model_id,
        kind=kind,
        criterion=criterion,
        attempt=attempt,
        input_tokens_at_most=tokens_in,
        worst_case_usd=_cost(tokens_in, config.max_tokens, config),
        spent_so_far_usd=spent,
        replies_of_unknown_cost=unknown,
    )
    if not confirm(preview):
        raise ReaderError("not confirmed: nothing was sent")
    provider = make_provider()  # the key, last; a refusal here leaves no record

    request_name, reply_name = _request_name(name, attempt), _reply_name(name, attempt)
    request_record = {
        "record_version": RECORD_VERSION,
        "kind": kind,
        "criterion": criterion,
        "probe_set": probe_set,
        "attempt": attempt,
        "reader_model": key,
        "reader_entry_sha256": entry_sha256(key, config),
        "brief": brief.name,
        "brief_sha256": brief.sha256,
        "material_sha256": material.parts,
        "prompt_sha256": text_prompt_sha256(request),
        "frozen": frozen,
        "max_tokens": config.max_tokens,
        "system": request.system,
        "user": request.user,
    }
    case.write_once(case.directory / request_name, _dump(request_record))
    decision = provider.decide_text(request)

    usable, problem, parsed = _judge(kind, criterion, decision)
    estimated = _cost(decision.usage.input_tokens, decision.usage.output_tokens, config)
    reply_record = {
        "record_version": RECORD_VERSION,
        "kind": kind,
        "criterion": criterion,
        "probe_set": probe_set,
        "attempt": attempt,
        "status": decision.status,
        "stop_reason": decision.stop_reason,
        "usable": usable,
        "problem": problem,
        "parsed": parsed,
        "text": "\n".join(decision.text_blocks),
        "error": decision.error,
        "usage": dataclasses.asdict(decision.usage),
        "estimated_usd": str(estimated),
        "provenance": dataclasses.asdict(decision.provenance),
        "raw_response": decision.raw_response,
    }
    case.write_once(case.directory / reply_name, _dump(reply_record))
    return ReadOutcome(
        kind=kind,
        criterion=criterion,
        attempt=attempt,
        usable=usable,
        problem=problem,
        reading=str(parsed["reading"]) if parsed else None,
        parsed=parsed,
        input_tokens=decision.usage.input_tokens,
        output_tokens=decision.usage.output_tokens,
        estimated_usd=estimated,
        request_name=request_name,
        reply_name=reply_name,
        candidate_type=candidate_type,
        probe_set=probe_set,
    )


def _judge(
    kind: str, criterion: str | None, decision: RawDecision
) -> tuple[bool, str | None, dict[str, Any] | None]:
    """Whether the reply is a reading: the call succeeded, ended normally, and fits the brief's format."""
    if decision.status != "ok":
        code = (decision.error or {}).get("code", "unknown")
        return False, f"the call failed ({code})", None
    if decision.stop_reason != "end_turn":
        return False, f"the reply stopped early ({decision.stop_reason})", None
    parsed, problem = parse_reply(kind, criterion, "\n".join(decision.text_blocks))
    return parsed is not None, problem, parsed


def _dump(record: dict[str, Any]) -> bytes:
    return (json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


# --- what the log and the lock read back ----------------------------------------------------------------


def _usable_reads(case: CaseAppendix, name: str) -> list[tuple[Attempt, Path]]:
    return [
        (a, case.directory / _reply_name(name, a.number))
        for a in attempts_on_record(case, name)
        if a.usable and a.has_reply
    ]


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


PROBE_SETS_NEWEST_FIRST = (2, 1)  # protocol §12.8: the first probe set, and one re-probe


def probe_reply_on_record(case: CaseAppendix, probe_set: int) -> tuple[ReaderReply, Path] | None:
    """The usable reply to the reader's read of probe set ``probe_set``'s flagged answers, or None when the
    set has not been read. Its file name, sha256 and reading are what a probe verdict and the log record."""
    found = _usable_reads(case, stem("rejection", materials.PROBE_CRITERION, probe_set))
    if not found:
        return None
    attempt, path = found[0]
    if attempt.reading not in ("pass", "fail", "cannot_tell"):
        raise ReaderError(f"{path.name} cannot be read back: look at it before using it")
    return ReaderReply(path.name, _file_sha256(path), attempt.reading), path


def reply_material(reply_path: Path) -> dict[str, str] | None:
    """The part hashes of the request the reply answered (the pair's request record), or None."""
    request = _load(reply_path.with_name(reply_path.name.replace("-reply.json", "-request.json")))
    parts = request.get("material_sha256") if request else None
    return parts if isinstance(parts, dict) else None


def rejection_reply_on_record(
    case: CaseAppendix, criterion: str, earlier: frozenset[str] = frozenset()
) -> ReaderReply:
    """The usable reply ``hc case log ... read`` logs a rejection's read from: its file, sha256 and
    reading. Refused when no usable read exists, so a read cannot be logged that was never made. For
    criterion 5 it is the reply for the newest probe set with flagged answers: the log holds the candidate's
    final probe outcome, and an earlier set's reply never stands in for a later set not yet read. A reply
    named in ``earlier`` (``earlier_record_replies``) is never the one returned."""
    if criterion not in materials.READ_CRITERIA:
        raise ReaderError(f"{criterion!r} is not a criterion the reader reads")
    if criterion == materials.PROBE_CRITERION:
        for probe_set in PROBE_SETS_NEWEST_FIRST:
            if not case.probe_flagged_path(probe_set).is_file():
                continue
            found = probe_reply_on_record(case, probe_set)
            if found is None:
                raise ReaderError(
                    f"{case.label}'s probe set {probe_set} has flagged answers and no usable read: run "
                    f"`hc case reader {case.label} rejection --criterion {criterion} --set {probe_set}` first"
                )
            return found[0]
        raise ReaderError(
            f"{case.label} has no usable read of its {criterion} rejection: run `hc case reader` first"
        )
    name = stem("rejection", criterion)
    found_reads = [(a, p) for a, p in _usable_reads(case, name) if p.name not in earlier]
    if not found_reads:
        raise ReaderError(
            f"{case.label} has no usable read of its {criterion} rejection: run `hc case reader` first"
        )
    attempt, path = found_reads[0]
    if attempt.reading not in ("pass", "fail", "cannot_tell"):
        raise ReaderError(f"{path.name} cannot be read back: look at it before logging")
    return ReaderReply(path.name, _file_sha256(path), attempt.reading, attempt.type)


# A scenario or rubric reading that needs his written resolution before the lock.
UNSETTLED = {"scenario": "concerns", "rubric": "disagrees"}
_PART = {"scenario": "Scenario", "rubric": "Rubric"}


def _resolution_name(name: str, attempt: int) -> str:
    return f"{name}-{attempt}-resolution.json"


def _read_of_current(case: CaseAppendix, kind: str) -> tuple[Attempt, Path]:
    """The newest usable read of the scenario or rubric exactly as it now stands in the case's folder. Newest,
    since a re-read of an unchanged scenario (its figure sources fixed, say) supersedes the earlier read."""
    path = case.scenario_path if kind == "scenario" else case.rubric_path
    try:
        current = _file_sha256(path)
    except OSError as exc:
        raise ReaderError(f"the {kind} cannot be read: {path.name}") from exc
    for attempt, reply in reversed(_usable_reads(case, stem(kind, None))):
        if attempt.material and attempt.material.get(_PART[kind]) == current:
            return attempt, reply
    raise ReaderError(
        f"the {kind} as it stands has no usable independent read: run `hc case reader {case.label} {kind}`"
    )


def record_resolution(case: CaseAppendix, kind: str, resolution: str, today: str) -> str:
    """His written resolution of a "concerns" or "disagrees" reading of the current scenario or rubric,
    write-once beside the reply it answers, with that reply's sha256. Returns the file name."""
    if kind not in UNSETTLED:
        raise ReaderError(f"only a scenario or rubric reading is resolved here, not {kind!r}")
    if not resolution.strip():
        raise ReaderError("a resolution says what he decided and why")
    attempt, reply = _read_of_current(case, kind)
    if attempt.reading != UNSETTLED[kind]:
        raise ReaderError(
            f"the {kind}'s reading is {attempt.reading!r}: there is nothing to resolve"
        )
    name = _resolution_name(stem(kind, None), attempt.number)
    record = {
        "record_version": RECORD_VERSION,
        "kind": kind,
        "reply": reply.name,
        "reply_sha256": _file_sha256(reply),
        "reading": attempt.reading,
        "resolution": resolution.strip(),
        "date": today,
    }
    case.write_once(case.directory / name, _dump(record))
    return name


def reads_settled(case: CaseAppendix) -> None:
    """Refuse unless the scenario and the rubric, as they stand, each have a usable independent read, and
    each "concerns" or "disagrees" reading has his resolution naming that reply (search-half doc §11, the
    step 9 review, decision 6). The message names files and readings, never content."""
    for kind in ("scenario", "rubric"):
        attempt, reply = _read_of_current(case, kind)
        if attempt.reading == UNSETTLED[kind]:
            path = case.directory / _resolution_name(stem(kind, None), attempt.number)
            record = _load(path)
            if (
                record is None
                or record.get("reply_sha256") != _file_sha256(reply)
                or not str(record.get("resolution", "")).strip()
            ):
                raise ReaderError(
                    f"the {kind}'s reading is {attempt.reading!r} and has no resolution of his: "
                    f"run `hc case resolve {case.label} {kind}`"
                )
