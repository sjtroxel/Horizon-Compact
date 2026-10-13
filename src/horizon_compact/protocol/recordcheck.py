"""The record checks (Phase 4 runs half section 5.3; scope Delivers 10): one read-only pass over every
pilot and official sweep, made after the last sweep and the last refusal call and before the reveal.

**It is blind.** A record is read through ``_pick_attempt`` or ``_pick_session``, which take named
provenance fields (where it ran, on what image, with what request, when, at what cost, with what status)
and nothing else. Nothing here asks a record for its validation, its tool calls, its text, its parsed
decision or its raw response, so the report holds counts, ids, hashes and dates, and no decision. A test
plants canary values in those fields and looks for them in the report, and another holds that the source
never names them.

**It is read-only.** It calls ``get`` and ``list_keys`` on the store and nothing else.

The checks (a failed one stops the phase before the reveal, section 6.7):

``content`` the lock's experiment and content hash on every sweep; ``model`` every sweep's model is one
of the lock's; ``labels`` pilots are ``pilot``, official sweeps ``grid``, ``thinking`` or ``awareness``,
one per model and label; ``container`` every pilot and official call ran on ``fargate`` with an image
digest and a clean tree; ``image`` the digests used, per sweep (more than one in a sweep is reported,
not failed: it is a finding for the run log); ``request`` the locked thinking value on grid, pilot and
probe calls, the sub-study's on its own, and DeepInfra serving ``gpt-oss-120b``; ``complete`` every
manifest run has its final record; ``sealed first`` no development or pilot manifest lists the sealed
template and its earliest attempt belongs to an official sweep; ``after the tag`` every pilot and
official call and session began after the tag's Software Heritage visit; ``frozen files`` ``hc protocol
check`` passes on the tree that ran this.

**Time.** The store gives no write time, so "after the tag" reads the records' own ``started_at``: an
object cannot have been written before the call it records began."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

from horizon_compact.protocol.lock import NOT_SET, REASONING_SENT, Lock, ModelIdentity
from horizon_compact.protocol.lock import THINKING_OFF as LOCK_THINKING_OFF
from horizon_compact.providers.anthropic import THINKING_DEFAULT as ANTHROPIC_DEFAULT
from horizon_compact.providers.anthropic import THINKING_OFF as ANTHROPIC_THINKING_OFF
from horizon_compact.providers.base import (
    THINKING_LABEL,
    THINKING_STUDY_EFFORT_NOTE,
    THINKING_STUDY_MAX_TOKENS,
    THINKING_STUDY_THINKING_NOTE,
)
from horizon_compact.providers.openrouter import served_by_pin
from horizon_compact.providers.openrouter import thinking_note as openrouter_thinking_note
from horizon_compact.sweep.store import Store

# The tag's outside timestamp (Phase 3.5 tag record: the Software Heritage visit of prereg-v1).
TAG_VISIT = datetime(2026, 10, 13, 6, 24, 52, tzinfo=UTC)
PILOT = "pilot"
OFFICIAL_LABELS = ("grid", THINKING_LABEL, "awareness")
SWEEP_MANIFEST = re.compile(
    r"^(?P<role>development|pilot|official)/[^/]+/(?P<awareness>awareness/)?[^/]+/manifest\.json$"
)

Role = Literal["development", "pilot", "official"]
ROLES: tuple[Role, ...] = ("development", "pilot", "official")


@dataclass(frozen=True)
class Attempt:
    """The provenance of one call, and nothing about what the model answered."""

    run_id: str
    status: str
    scenario_id: str
    wording_id: str
    started_at: str
    runner: str
    image_digest: str | None
    git_dirty: bool | None
    thinking: str
    effort: str
    max_tokens: int
    served_by: str | None
    cost_usd: float
    content_hash: str
    model_key: str
    label: str


@dataclass(frozen=True)
class Session:
    runner: str
    image_digest: str | None
    started_at: str
    stopped: str


@dataclass
class Sweep:
    role: Role
    prefix: str
    sweep_id: str
    label: str
    model_key: str
    experiment: str
    content_hash: str
    templates: list[str]
    run_ids: list[str]
    awareness: bool
    finished_runs: set[str] = field(default_factory=set)
    attempts: list[Attempt] = field(default_factory=list)
    sessions: list[Session] = field(default_factory=list)

    @property
    def name(self) -> str:
        return f"{self.role} {self.sweep_id}"


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    lines: tuple[str, ...] = ()
    info: bool = False  # reported, never failed


@dataclass(frozen=True)
class RecordReport:
    checks: tuple[Check, ...]
    sweeps: tuple[Sweep, ...]

    @property
    def ok(self) -> bool:
        return all(check.ok for check in self.checks)


# --- reading: named fields only -----------------------------------------------------------------------------


def _pick_attempt(record: dict[str, Any], *, shallow: bool = False) -> Attempt:
    """The provenance fields of one attempt (or probe call or probe error). ``shallow`` keeps the cell and the
    time only, for a development sweep, whose other fields are no concern of this check."""
    details = record.get("provider_details") or {}
    return Attempt(
        run_id=str(record.get("run_id")),
        status="" if shallow else str(record.get("status") or record.get("kind") or ""),
        scenario_id=str(record.get("scenario_id")),
        wording_id=str(record.get("wording_variant_id")),
        started_at=str(record.get("started_at") or ""),
        runner="" if shallow else str(record.get("runner")),
        image_digest=None if shallow else record.get("image_digest"),
        git_dirty=None if shallow else record.get("git_dirty"),
        thinking="" if shallow else str(record.get("thinking")),
        effort="" if shallow else str(record.get("effort")),
        max_tokens=0 if shallow else int(record.get("max_tokens") or 0),
        served_by=None if shallow else details.get("served_by"),
        cost_usd=0.0 if shallow else float(record.get("cost_usd") or 0.0),
        content_hash=str(record.get("content_hash")),
        model_key=str(record.get("model_key")),
        label=str(record.get("label")),
    )


def _pick_session(record: dict[str, Any]) -> Session:
    return Session(
        runner=str(record.get("runner")),
        image_digest=record.get("image_digest"),
        started_at=str(record.get("started_at") or ""),
        stopped=str(record.get("stopped")),
    )


def _load(store: Store, key: str) -> dict[str, Any]:
    text = store.get(key)
    if text is None:
        raise ValueError(f"{key} was listed but cannot be read")
    data: dict[str, Any] = json.loads(text)
    return data


def collect(store: Store, experiment: str) -> list[Sweep]:
    """Every sweep of the experiment under the three roles, with its provenance read through the pickers."""
    keys_by_role = {role: store.list_keys(f"{role}/{experiment}/") for role in ROLES}
    sweeps: list[Sweep] = []
    for role in ROLES:
        keys = keys_by_role[role]
        for key in keys:
            found = SWEEP_MANIFEST.match(key)
            if found is None:
                continue
            manifest = _load(store, key)
            prefix = key[: -len("manifest.json")]
            sweep = Sweep(
                role=role,
                prefix=prefix,
                sweep_id=str(manifest.get("sweep_id")),
                label=str(manifest.get("label")),
                model_key=str(manifest.get("model_key")),
                experiment=str(manifest.get("experiment")),
                content_hash=str(manifest.get("content_hash")),
                templates=[str(t) for t in manifest.get("templates") or []],
                run_ids=[str(run["run_id"]) for run in manifest.get("runs") or []],
                awareness=found.group("awareness") is not None,
            )
            _read_sweep(store, sweep, [k for k in keys if k.startswith(prefix)])
            sweeps.append(sweep)
    return sweeps


_FINAL = re.compile(r"/runs/(?P<run>r-[0-9a-f]{12})/final\.json$")
_ATTEMPT = re.compile(r"/runs/r-[0-9a-f]{12}/attempt-\d+\.json$")
_PROBE_CALL = re.compile(r"/runs/(?P<run>r-[0-9a-f]{12})\.json$")


def _read_sweep(store: Store, sweep: Sweep, keys: list[str]) -> None:
    shallow = sweep.role == "development"
    for key in keys:
        final = _FINAL.search(key)
        if final:
            sweep.finished_runs.add(final.group("run"))
        elif _ATTEMPT.search(key) or "/errors/" in key:
            sweep.attempts.append(_pick_attempt(_load(store, key), shallow=shallow))
        elif (probe := _PROBE_CALL.search(key)) is not None:
            sweep.finished_runs.add(probe.group("run"))
            sweep.attempts.append(_pick_attempt(_load(store, key), shallow=shallow))
        elif "/sessions/" in key and not shallow:
            sweep.sessions.append(_pick_session(_load(store, key)))


# --- the checks ---------------------------------------------------------------------------------------------


def _when(text: str) -> datetime | None:
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


def _graded(sweeps: list[Sweep]) -> list[Sweep]:
    return [s for s in sweeps if s.role in ("pilot", "official")]


def check_content(sweeps: list[Sweep], lock: Lock) -> Check:
    lines = []
    for sweep in _graded(sweeps):
        if sweep.experiment != lock.content.experiment:
            lines.append(
                f"{sweep.name}: experiment {sweep.experiment!r}, locked {lock.content.experiment!r}"
            )
        if sweep.content_hash != lock.content.content_hash:
            lines.append(f"{sweep.name}: the manifest's content hash is not {lock.protocol}'s")
        wrong = sum(1 for a in sweep.attempts if a.content_hash != lock.content.content_hash)
        if wrong:
            lines.append(
                f"{sweep.name}: {wrong} call(s) carry a content hash that is not {lock.protocol}'s"
            )
    return Check("content", not lines, tuple(lines))


def check_model(sweeps: list[Sweep], lock: Lock) -> Check:
    lines = []
    for sweep in _graded(sweeps):
        if sweep.model_key not in lock.models:
            lines.append(f"{sweep.name}: model {sweep.model_key!r} is not one of {lock.protocol}'s")
        odd = sorted({a.model_key for a in sweep.attempts if a.model_key != sweep.model_key})
        if odd:
            lines.append(
                f"{sweep.name}: calls name model(s) {odd}, not the manifest's {sweep.model_key!r}"
            )
    return Check("model", not lines, tuple(lines))


def check_labels(sweeps: list[Sweep]) -> Check:
    lines = []
    seen: Counter[tuple[str, str, str]] = Counter()
    for sweep in _graded(sweeps):
        allowed = (PILOT,) if sweep.role == "pilot" else OFFICIAL_LABELS
        if sweep.label not in allowed:
            lines.append(
                f"{sweep.name}: label {sweep.label!r}; a {sweep.role} sweep's is {' or '.join(allowed)}"
            )
        seen[(sweep.role, sweep.model_key, sweep.label)] += 1
        wrong = sorted({a.label for a in sweep.attempts if a.label != sweep.role})
        if wrong:
            lines.append(f"{sweep.name}: calls are labeled {wrong}, not {sweep.role!r}")
    for (role, model, label), count in sorted(seen.items()):
        if count > 1:
            lines.append(f"{count} {role} sweeps labeled {label!r} on {model}; at most one")
    return Check("labels", not lines, tuple(lines))


def check_container(sweeps: list[Sweep]) -> Check:
    lines = []
    for sweep in _graded(sweeps):
        runners = Counter(a.runner for a in sweep.attempts) + Counter(
            s.runner for s in sweep.sessions
        )
        bad = {r: n for r, n in runners.items() if r != "fargate"}
        if bad:
            lines.append(f"{sweep.name}: not run on fargate: {dict(sorted(bad.items()))}")
        no_digest = sum(1 for a in sweep.attempts if not a.image_digest)
        no_digest += sum(1 for s in sweep.sessions if not s.image_digest)
        if no_digest:
            lines.append(f"{sweep.name}: {no_digest} record(s) have no image digest")
        dirty = sum(1 for a in sweep.attempts if a.git_dirty is not False)
        if dirty:
            lines.append(f"{sweep.name}: {dirty} call(s) did not record a clean git tree")
    return Check("container", not lines, tuple(lines))


def digests_by_sweep(sweeps: list[Sweep]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for sweep in _graded(sweeps):
        counts: Counter[str] = Counter(str(a.image_digest) for a in sweep.attempts)
        counts.update(str(s.image_digest) for s in sweep.sessions)
        result[sweep.name] = dict(sorted(counts.items()))
    return result


def check_image(sweeps: list[Sweep]) -> Check:
    lines = []
    for name, digests in digests_by_sweep(sweeps).items():
        lines.append(f"{name}: {len(digests)} image digest(s): {', '.join(digests) or 'none'}")
        if len(digests) > 1:
            sessions = [
                f"{s.started_at} {s.image_digest}"
                for sweep in sweeps
                if sweep.name == name
                for s in sorted(sweep.sessions, key=lambda s: s.started_at)
            ]
            lines.append(f"  MORE THAN ONE DIGEST in {name}; sessions: {'; '.join(sessions)}")
    return Check("image", True, tuple(lines), info=True)


def recorded_thinking(identity: ModelIdentity) -> str | None:
    """What a grid, pilot or probe call's record says about thinking when it was sent as the lock fixes. The
    lock and the providers word it differently (the lock: ``reasoning {effort: medium} sent``; the OpenRouter
    record: ``reasoning effort medium sent``), so this is taken from each provider's own text, never compared
    as the lock's string. ``None`` for a route with no such rule here (no v1 model is on one)."""
    if identity.route == "anthropic":
        return (
            ANTHROPIC_THINKING_OFF if identity.thinking == LOCK_THINKING_OFF else ANTHROPIC_DEFAULT
        )
    if identity.route == "openrouter":
        if identity.thinking == NOT_SET:
            return openrouter_thinking_note(None)
        level = re.fullmatch(r"reasoning \{effort: (\w+)\} sent", identity.thinking)
        if level is None or REASONING_SENT.format(level.group(1)) != identity.thinking:
            return None
        return openrouter_thinking_note(level.group(1))
    return None


# A call that is not a model's result: the API failed, or the session stopped on a configuration error (an
# OpenRouter reply from a host the pin excludes is one, and is kept as evidence; it never counts).
_NOT_A_RESULT = frozenset({"api_error", "config_error"})


def check_request(sweeps: list[Sweep], lock: Lock) -> Check:
    lines = []
    for sweep in _graded(sweeps):
        locked = lock.models.get(sweep.model_key)
        if locked is None:
            continue  # the model check says so
        expected = recorded_thinking(locked)
        if expected is None:
            lines.append(
                f"{sweep.name}: no rule for what route {locked.route!r} records; cannot check"
            )
            continue
        for what, count in _request_misses(sweep, expected, locked.openrouter_provider).items():
            lines.append(f"{sweep.name}: {count} call(s) {what}")
    return Check("request", not lines, tuple(lines))


def _request_misses(sweep: Sweep, expected_thinking: str, pin: str | None) -> dict[str, int]:
    misses: Counter[str] = Counter()
    for a in sweep.attempts:
        if sweep.label == THINKING_LABEL:
            if a.thinking != THINKING_STUDY_THINKING_NOTE:
                misses[
                    f"whose thinking is {a.thinking!r}, not {THINKING_STUDY_THINKING_NOTE!r}"
                ] += 1
            if a.effort != THINKING_STUDY_EFFORT_NOTE:
                misses[f"whose effort is {a.effort!r}, not {THINKING_STUDY_EFFORT_NOTE!r}"] += 1
            if a.max_tokens != THINKING_STUDY_MAX_TOKENS:
                misses[
                    f"whose max_tokens is {a.max_tokens}, not {THINKING_STUDY_MAX_TOKENS:,}"
                ] += 1
        elif a.thinking != expected_thinking:
            misses[f"whose thinking is {a.thinking!r}, not {expected_thinking!r}"] += 1
        # a probe's failed call is recorded with kind "awareness-api-error" and no status
        is_result = a.status not in _NOT_A_RESULT and not a.status.endswith("api-error")
        if pin and is_result and not served_by_pin(a.served_by, pin):
            misses[f"served by {a.served_by!r}, not the pinned {pin!r}"] += 1
    return dict(misses)


def check_complete(sweeps: list[Sweep]) -> Check:
    lines = []
    for sweep in _graded(sweeps):
        missing = [r for r in sweep.run_ids if r not in sweep.finished_runs]
        if missing:
            lines.append(
                f"{sweep.name}: {len(missing)} of {len(sweep.run_ids)} runs have no final record"
            )
    return Check("complete", not lines, tuple(lines))


def check_sealed_first(sweeps: list[Sweep], lock: Lock) -> Check:
    sealed = lock.content.sealed_template
    lines = []
    for sweep in sweeps:
        if sweep.role in ("development", "pilot") and sealed in sweep.templates:
            lines.append(f"{sweep.name}: its manifest lists the sealed template ({sealed})")
    carrying = [
        (moment, sweep)
        for sweep in sweeps
        for a in sweep.attempts
        if a.wording_id == sealed and (moment := _when(a.started_at)) is not None
    ]
    if carrying:
        first_moment, first = min(carrying, key=lambda pair: pair[0])
        if first.role != "official":
            lines.append(
                f"the earliest call with the sealed template ({first_moment.isoformat()}) is in {first.name}, "
                "not an official sweep"
            )
    return Check("sealed first", not lines, tuple(lines))


def check_after_tag(sweeps: list[Sweep]) -> Check:
    lines = []
    for sweep in _graded(sweeps):
        early = 0
        unreadable = 0
        for moment_text in [a.started_at for a in sweep.attempts] + [
            s.started_at for s in sweep.sessions
        ]:
            moment = _when(moment_text)
            if moment is None:
                unreadable += 1
            elif moment < TAG_VISIT:
                early += 1
        if early:
            lines.append(f"{sweep.name}: {early} record(s) began before {TAG_VISIT.isoformat()}")
        if unreadable:
            lines.append(f"{sweep.name}: {unreadable} record(s) have no readable start time")
    return Check("after the tag", not lines, tuple(lines))


def check_frozen(frozen_failures: list[str]) -> Check:
    return Check(
        "frozen files",
        not frozen_failures,
        tuple(f"hc protocol check: {f}" for f in frozen_failures),
    )


def run_checks(store: Store, lock: Lock, frozen_failures: list[str]) -> RecordReport:
    sweeps = collect(store, lock.content.experiment)
    checks = (
        check_content(sweeps, lock),
        check_model(sweeps, lock),
        check_labels(sweeps),
        check_container(sweeps),
        check_image(sweeps),
        check_request(sweeps, lock),
        check_complete(sweeps),
        check_sealed_first(sweeps, lock),
        check_after_tag(sweeps),
        check_frozen(frozen_failures),
    )
    return RecordReport(checks, tuple(sweeps))


# --- the report ---------------------------------------------------------------------------------------------


def format_report(report: RecordReport, *, protocol: str, tree: str, made_at: str) -> str:
    lines = [
        "# Record checks",
        "",
        f"Protocol `{protocol}`; tree `{tree}`; made {made_at}. Written by `hc protocol records`; do not edit by "
        "hand. Counts, ids, hashes and dates only: no decision, choice, memo or reply is read or shown.",
        "",
        f"**Result: {'every check passes' if report.ok else 'AT LEAST ONE CHECK FAILED'}.**",
        "",
        "| check | result |",
        "|---|---|",
    ]
    for check in report.checks:
        result = "reported" if check.info else ("pass" if check.ok else "FAIL")
        lines.append(f"| {check.name} | {result} |")
    for check in report.checks:
        if check.lines:
            lines += ["", f"## {check.name}", "", *(f"- {line}" for line in check.lines)]
    lines += [
        "",
        "## Run counts, per sweep (protocol 13.2)",
        "",
        "| role | sweep | label | model | runs | finished | calls | calls by status | sessions | cost (USD) |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for sweep in report.sweeps:
        if sweep.role == "development":
            continue
        statuses = dict(sorted(Counter(a.status for a in sweep.attempts).items()))
        cost = round(sum(a.cost_usd for a in sweep.attempts), 6)
        lines.append(
            f"| {sweep.role} | `{sweep.sweep_id}` | {sweep.label} | {sweep.model_key} | {len(sweep.run_ids)} "
            f"| {len(sweep.finished_runs & set(sweep.run_ids))} | {len(sweep.attempts)} | {statuses} "
            f"| {len(sweep.sessions)} | {cost:.4f} |"
        )
    lines.append("")
    return "\n".join(lines)


def sweeps_by_role(sweeps: list[Sweep]) -> dict[str, int]:
    counts: defaultdict[str, int] = defaultdict(int)
    for sweep in sweeps:
        counts[sweep.role] += 1
    return dict(counts)
