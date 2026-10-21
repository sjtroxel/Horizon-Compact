"""``hc case knowledge-probe``: step 3's knowledge probe (search-half doc §4.6.5 step 3 item 4, built in 3b).

A pool candidate is admitted only if the models do not know its decision. Each of v1's two official models
and the extraction model gets three calls, with no system text and one message, word for word. In order, and
every refusal before the first byte leaves the machine: the candidate's row stands at ``not_known`` in the
exploratory log; the hand-placed inputs file; no record of a probe for the label; the models; then, after his
confirmation of the spend, the keys, and then for each call **the request record, written before the call**,
the call, and the reply record. A request with no reply is a call that never returned.

**A reply is the measurement, so it is never retried** (a retry would raise the pass rate by hiding a
failure); an API error is retried with backoff, each kept as its own record, and too many stop the run. A
second run for the label is refused, so a run that stopped part-way is his to look at, not to repeat.

This module only asks and records. It never writes the log and never decides: whether an answer fails, his
read of every answer that is not "unknown", the reader's read of a failure and the log's ``not_known`` result
are 3c's. The message carries a real company's name to the official models outside the container, which
this command alone does; the name and the answers are written only to the private appendix and are never
printed.

It also holds the build's one check on a pool row (``check_build_shape``): a case is built only as a shape
its probe asked about, read from the request records, never from a reply.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import random
import time
import tomllib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.exploratory import KNOWLEDGE, ExploratoryRow, row_for
from horizon_compact.casebuild.extraction_model import entry_sha256, extraction_route
from horizon_compact.casebuild.frozen import Git
from horizon_compact.caseprobe.layout import PROBE_MAX_TOKENS, PROBE_ROLES
from horizon_compact.caseprobe.run import check_probe_model, probe_route
from horizon_compact.experiment import MODELS_FILE
from horizon_compact.model_config import ModelConfig, ModelsFile
from horizon_compact.providers.base import (
    ModelRoute,
    RawDecision,
    TextProvider,
    TextRequest,
    text_prompt_sha256,
)
from horizon_compact.sweep.classify import classify_error
from horizon_compact.sweep.pacing import backoff_seconds
from horizon_compact.sweep.spend import (
    attempt_cost_usd,
    estimate_input_tokens_text,
    worst_case_attempt_usd,
)

RECORD_VERSION = 1
CALLS = 3  # per model (item 4)
MAX_TOKENS = PROBE_MAX_TOKENS  # room for an answer, a reasoning model's reasoning included
MAX_API_ERRORS = 5  # per call, then the run stops
SHAPES = ("S1", "S2", "S3")
RECORD_PREFIX = "knowledge-probe-"

# Search-half doc §4.6.5 step 3 item 4, word for word. A test compares both with the doc's own text.
MESSAGE_FACILITY = (
    "What do you know about {company}'s {facility} in {place}? "
    "If you know nothing about it, say unknown."
)
MESSAGE_REDUCTION = (
    "What do you know about the workforce reduction {company} announced in {month} {year}? "
    "If you know nothing about it, say unknown."
)
MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
INPUT_KEYS = frozenset({"shape", "company", "facility", "place"})


class KnowledgeError(Exception):
    """The probe cannot be made, or stopped part-way. The message never holds a name or an answer."""


# --- what the message is filled from --------------------------------------------------------------------


@dataclass(frozen=True)
class Inputs:
    shape: str
    company: str
    facility: str | None
    place: str | None
    sha256: str


def _field(table: Mapping[str, Any], key: str, *, required: bool) -> str | None:
    value = table.get(key)
    if value is None:
        if required:
            raise KnowledgeError(f"{key} is missing from the inputs file")
        return None
    if not isinstance(value, str) or not value.strip():
        raise KnowledgeError(f"{key} in the inputs file is not text")
    text = value.strip()
    if "\n" in text or "\r" in text or len(text) > 200:
        raise KnowledgeError(f"{key} in the inputs file is one line of at most 200 characters")
    return text


def load_inputs(case: CaseAppendix) -> Inputs:
    """The inputs file as placed. S3 names the facility and its town; S1 and S2 name neither (their message
    holds the filer and the first-disclosure date only)."""
    path = case.knowledge_inputs_path
    try:
        raw = path.read_bytes()
        table = tomllib.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise KnowledgeError(
            f"{path.name} cannot be read ({type(exc).__name__}): place it in the case's folder"
        ) from exc
    extra = sorted(set(table) - INPUT_KEYS)
    if extra:
        raise KnowledgeError(f"the inputs file has keys that mean nothing here: {', '.join(extra)}")
    shape = _field(table, "shape", required=True)
    if shape not in SHAPES:
        raise KnowledgeError(f"shape in the inputs file is one of {', '.join(SHAPES)}")
    company = _field(table, "company", required=True)
    facility = _field(table, "facility", required=shape == "S3")
    place = _field(table, "place", required=shape == "S3")
    if shape != "S3" and (facility or place):
        raise KnowledgeError("facility and place are for S3; the S1 and S2 message names neither")
    assert company is not None
    return Inputs(shape, company, facility, place, hashlib.sha256(raw).hexdigest())


def build_message(inputs: Inputs, disclosed: date | None) -> str:
    """The probe's one message. S3 asks about the facility; S1 and S2 about the reduction, dated by the first
    disclosure's month and year."""
    if inputs.shape == "S3":
        assert inputs.facility and inputs.place
        return MESSAGE_FACILITY.format(
            company=inputs.company, facility=inputs.facility, place=inputs.place
        )
    if disclosed is None:
        raise KnowledgeError(
            "the row has no first-disclosure date, which the S1 and S2 message needs"
        )
    return MESSAGE_REDUCTION.format(
        company=inputs.company, month=MONTHS[disclosed.month - 1], year=disclosed.year
    )


# --- the candidate and the models -------------------------------------------------------------------------


def probe_row(search: CaseAppendix, label: str) -> ExploratoryRow:
    """The candidate's row, refused unless it stands at ``not_known``: a probed row (a pool row) that met
    every criterion before it and has no result on it yet. The probe is not run for any other row."""
    row = row_for(search, label)
    if not isinstance(row, ExploratoryRow) or not row.probed:
        raise KnowledgeError(
            f"{label} is not a row of step 3's or step 4's pool: it has no knowledge probe"
        )
    if KNOWLEDGE in row.results:
        raise KnowledgeError(f"{label} already has a result on {KNOWLEDGE}")
    before = row.criteria[: row.criteria.index(KNOWLEDGE)]
    unmet = [c for c in before if not row.met(c)]
    if unmet:
        raise KnowledgeError(
            f"{label} stands at {unmet[0]}, not at {KNOWLEDGE}: the probe comes after {before[-1]}"
        )
    return row


@dataclass(frozen=True)
class ProbeModel:
    key: str
    config: ModelConfig
    route: ModelRoute


def probe_models(experiment_dir: Path) -> tuple[ProbeModel, ...]:
    """The experiment's main and second-family models, then the extraction model (item 4): by role, exactly
    one of each, so a models.toml that changed the set is refused rather than probed with another."""
    path = experiment_dir / MODELS_FILE
    try:
        models = ModelsFile.model_validate(tomllib.loads(path.read_text(encoding="utf-8")))
        extraction = models.extraction()
    except (
        OSError,
        UnicodeDecodeError,
        tomllib.TOMLDecodeError,
        ValidationError,
        ValueError,
    ) as exc:
        raise KnowledgeError(f"{MODELS_FILE}: {type(exc).__name__}: {exc}") from exc
    chosen: list[ProbeModel] = []
    for role in PROBE_ROLES:
        found = [(k, c) for k, c in models.models.items() if c.role == role]
        if len(found) != 1:
            raise KnowledgeError(
                f"{MODELS_FILE} has {len(found)} models with role {role!r}; the probe asks exactly one"
            )
        key, config = found[0]
        check_probe_model(key, config)
        chosen.append(ProbeModel(key, config, probe_route(key, config)))
    chosen.append(ProbeModel(extraction[0], extraction[1], extraction_route(*extraction)))
    return tuple(chosen)


# --- the plan, the record and the run ---------------------------------------------------------------------


@dataclass(frozen=True)
class PlannedModel:
    key: str
    model_id: str
    route_kind: str
    calls: int
    worst_case_usd: float


@dataclass(frozen=True)
class Preview:
    """What the spend warning shows before anything is sent. It holds no name and no part of the message."""

    models: tuple[PlannedModel, ...]

    @property
    def worst_case_usd(self) -> float:
        return round(sum(m.worst_case_usd for m in self.models), 6)


@dataclass(frozen=True)
class CallResult:
    model_key: str
    call: int
    status: str
    unknown: bool  # exactly "unknown"
    reasoning: bool  # the reply carries reasoning, which he reads as the answer (item 4, note of 2026-10-21)
    cost_usd: float

    @property
    def to_read(self) -> bool:
        """His to read in 3c: every answer that is not "unknown", and every reply with reasoning."""
        return not self.unknown or self.reasoning


@dataclass(frozen=True)
class KnowledgeOutcome:
    results: tuple[CallResult, ...]
    api_errors: int

    @property
    def cost_usd(self) -> float:
        return round(sum(r.cost_usd for r in self.results), 6)


def is_unknown(answer: str) -> bool:
    """The answer is the one word asked for. Case, quotes and a closing full stop are ignored; anything else
    is an answer he reads."""
    return answer.strip().strip("\"'`*").strip().rstrip(".").strip().lower() == "unknown"


def reply_status(raw: RawDecision) -> str:
    """How the call ended, as the case probe says it: cut off, filtered, stopped oddly, offered a tool it
    was never given, empty, or replied."""
    if raw.stop_reason == "max_tokens":
        return "truncated"
    if raw.stop_reason == "content_filtered":
        return "content_filtered"
    if raw.stop_reason not in ("end_turn", "tool_use"):
        return "unexpected_stop"
    if raw.tool_call_count:
        return "unexpected_tool_call"
    return "replied" if any(t.strip() for t in raw.text_blocks) else "no_text"


def _stem(model_key: str, call: int) -> str:
    return f"{RECORD_PREFIX}{model_key}-{call}"


def _dump(record: dict[str, Any]) -> bytes:
    return (json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def run_knowledge_probe(
    case: CaseAppendix,
    *,
    search: CaseAppendix,
    repo_root: Path,
    git: Git,
    confirm: Callable[[Preview], bool],
    make_provider: Callable[[str], TextProvider],
    sleep: Callable[[float], None] = time.sleep,
    rng: random.Random | None = None,
) -> KnowledgeOutcome:
    row = probe_row(search, case.label)
    inputs = load_inputs(case)
    message = build_message(inputs, row.disclosed)
    if any(case.directory.glob(f"{RECORD_PREFIX}*")):
        raise KnowledgeError(
            f"{case.label} already has probe records: a second run is refused. If a run stopped "
            "part-way, look in the case's folder"
        )
    models = probe_models(repo_root / "experiment")
    tokens = estimate_input_tokens_text("", message)
    plan = Preview(
        tuple(
            PlannedModel(
                m.key,
                m.config.model_id,
                m.route.route_kind,
                CALLS,
                round(CALLS * worst_case_attempt_usd(tokens, MAX_TOKENS, m.config.prices), 6),
            )
            for m in models
        )
    )
    if not confirm(plan):
        raise KnowledgeError("not confirmed: nothing was sent")
    # The keys, last: a refusal here leaves no record. One provider per route, all made before the first call.
    providers = {
        kind: make_provider(kind) for kind in dict.fromkeys(m.route.route_kind for m in models)
    }
    sha = git(["rev-parse", "HEAD"]).strip()
    dirty = bool(git(["status", "--porcelain", "--", "src", "experiment"]).strip())
    rng = rng or random.Random()
    results: list[CallResult] = []
    api_errors = 0

    for model in models:
        provider = providers[model.route.route_kind]
        request = TextRequest(route=model.route, system="", user=message, max_tokens=MAX_TOKENS)
        for call in range(1, CALLS + 1):
            stem = _stem(model.key, call)
            fields: dict[str, Any] = {
                "record_version": RECORD_VERSION,
                "label": case.label,
                "model_key": model.key,
                "entry_sha256": entry_sha256(model.key, model.config),
                "call": call,
                "shape": inputs.shape,
                "inputs_sha256": inputs.sha256,
                "prompt_sha256": text_prompt_sha256(request),
                "max_tokens": MAX_TOKENS,
                "git_sha": sha,
                "git_dirty": dirty,
            }
            case.write_once(
                case.directory / f"{stem}-request.json",
                _dump(
                    {
                        **fields,
                        "kind": "knowledge-probe-request",
                        "system": request.system,
                        "user": request.user,
                        "request": _jsonable(provider.text_request_body(request)),
                    }
                ),
            )
            errors = 0
            while True:
                raw = provider.decide_text(request)
                cost = attempt_cost_usd(raw.usage, model.config.prices)
                if raw.status != "api_error":
                    break
                errors += 1
                api_errors += 1
                code = (raw.error or {}).get("code", "unknown")
                case.write_once(
                    case.directory / f"{stem}-error-{errors}.json",
                    _dump(
                        {
                            **fields,
                            "kind": "knowledge-probe-api-error",
                            "error": raw.error,
                            "usage": dataclasses.asdict(raw.usage),
                            "cost_usd": cost,
                        }
                    ),
                )
                if classify_error(raw).stop_session or errors >= MAX_API_ERRORS:
                    raise KnowledgeError(
                        f"stopped at {model.key} call {call} on an API error ({code}) after "
                        f"{len(results)} finished calls; look in the case's folder, a second run is refused"
                    )
                sleep(backoff_seconds(errors - 1, rng))
            answer = "\n".join(t for t in raw.text_blocks if t.strip()).strip()
            status = reply_status(raw)
            case.write_once(
                case.directory / f"{stem}-reply.json",
                _dump(
                    {
                        **fields,
                        "kind": "knowledge-probe-reply",
                        "status": status,
                        "stop_reason": raw.stop_reason,
                        "answer": answer,
                        "text_blocks": raw.text_blocks,
                        "reasoning_block_count": raw.reasoning_block_count,
                        "usage": dataclasses.asdict(raw.usage),
                        "cost_usd": cost,
                        "provenance": _jsonable(dataclasses.asdict(raw.provenance)),
                        "raw_response": _jsonable(raw.raw_response),
                    }
                ),
            )
            results.append(
                CallResult(
                    model.key,
                    call,
                    status,
                    status == "replied" and is_unknown(answer),
                    raw.reasoning_block_count > 0,
                    cost,
                )
            )
    return KnowledgeOutcome(tuple(results), api_errors)


# --- what the build may be -------------------------------------------------------------------------------


def _question(shape: str) -> str | None:
    """Which of item 4's two messages a shape is asked; S4 has none."""
    return {"S1": "reduction", "S2": "reduction", "S3": "facility"}.get(shape)


def probed_shape(case: CaseAppendix) -> str:
    """The shape the probe's message was chosen for, read from its request records, which hold no answer."""
    shapes: set[str] = set()
    for path in sorted(case.directory.glob(f"{RECORD_PREFIX}*-request.json")):
        try:
            shapes.add(str(json.loads(path.read_text(encoding="utf-8"))["shape"]))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise KnowledgeError(f"{path.name} cannot be read ({type(exc).__name__})") from exc
    if not shapes:
        raise KnowledgeError(f"{case.label} is a pool row with no knowledge-probe records")
    if len(shapes) > 1:
        raise KnowledgeError(f"{case.label}'s probe records name more than one shape")
    return shapes.pop()


def check_build_shape(search: CaseAppendix, case: CaseAppendix, shape: str) -> None:
    """A pool row is built only as a shape its knowledge probe asked about (search-half doc §4.6.5 step 3 item
    4, dated note of 2026-10-21, his): S3 was asked about the facility, S1 and S2 about the reduction, and S4
    was not asked. Any other row is not checked."""
    row = row_for(search, case.label)
    if not isinstance(row, ExploratoryRow) or not row.probed:
        return
    probed = probed_shape(case)
    if _question(shape) is None or _question(shape) != _question(probed):
        raise KnowledgeError(
            f"{case.label} was probed as {probed}; a build as {shape} would ask its probe a different "
            "question"
        )


__all__ = [
    "CALLS",
    "MESSAGE_FACILITY",
    "MESSAGE_REDUCTION",
    "CallResult",
    "Inputs",
    "KnowledgeError",
    "KnowledgeOutcome",
    "PlannedModel",
    "Preview",
    "ProbeModel",
    "build_message",
    "check_build_shape",
    "is_unknown",
    "load_inputs",
    "probe_models",
    "probe_row",
    "probed_shape",
    "reply_status",
    "run_knowledge_probe",
]
