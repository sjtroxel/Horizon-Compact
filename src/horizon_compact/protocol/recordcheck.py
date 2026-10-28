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
object cannot have been written before the call it records began.

**Case sweeps** (Phase 5.5 IMPLEMENTATION doc section 5.3, ``hc protocol records --cases``). The same pass
over the five frozen cases' sweeps under ``cases/<label>/runs/<sweep_id>/``, never ``development/``,
``pilot/`` or ``official/``. The container, image, request, model, complete and frozen-files checks are the
grid's own, run on case ``Sweep`` objects. The case-only ones are ``cases`` (the labels in the bucket are the
freeze's), ``one sweep`` (one manifest per case and model), ``case plan``, ``seed``, ``case content`` (the
hashes the records carry equal ``case.lock``), ``order`` and ``after the freeze``. Still blind: the manifest
and ``order.json`` are read through named fields, and the rubric is never read (its hash is in no run record;
the gate checks it before every call and ``hc case match`` before every reading)."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from horizon_compact.caseprobe.freeze import EVIDENCE_DIR, FREEZE_FILE
from horizon_compact.caseprobe.layout import runs_prefix
from horizon_compact.caseprobe.session import (
    CASE_LABEL,
    CASE_OBJECTIVES,
    CASE_REPEATS,
    CASE_TEMPLATES,
    OBJECTIVES_FILE,
    ORDER_FILE,
    case_experiment_name,
)
from horizon_compact.caseprobe.session import check_frozen as freeze_lists_case
from horizon_compact.experiment import MODELS_FILE, combine_hashes
from horizon_compact.protocol.cases import CaseError, CaseRecord, read_case
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
# The Phase 5 freeze commit's CI run, completed: CI run 40487345520 on
# 5f794eef380ed05f3e946d79ebbf4254af15c797 ("phase 5: five frozen cases / files"). No case sweep may have a
# record from before it (Phase 5.5 K3).
FREEZE_CI_DONE = datetime(2026, 10, 27, 10, 20, 15, tzinfo=UTC)
# P, the commit tagged ``prereg-v1`` (Phase 3.5 tag record). Phase 5.5 IMPLEMENTATION doc section 4 draws each
# case sweep's seed from it, so it predates every case. The code holds it nowhere else; the docs do.
PREREG_COMMIT = "649e8b9b8f1dde0e3698be0d279b62fef07ad70b"
# Section 4's two models, by key: the lock's, in the order of the run table.
CASE_MODELS = ("haiku-5-5", "gpt-oss-openrouter")
PILOT = "pilot"
OFFICIAL_LABELS = ("grid", THINKING_LABEL, "awareness")
SWEEP_MANIFEST = re.compile(
    r"^(?P<role>development|pilot|official)/[^/]+/(?P<awareness>awareness/)?[^/]+/manifest\.json$"
)

Role = Literal["development", "pilot", "official", "case"]
ROLES: tuple[Role, ...] = (
    "development",
    "pilot",
    "official",
)  # the grid's; a case sweep is read by label


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
    dossier_hash: str = ""
    file_hashes: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class Session:
    runner: str
    image_digest: str | None
    started_at: str
    stopped: str


@dataclass(frozen=True)
class OrderRecord:
    """A case sweep's ``order.json``, read through three named fields."""

    admitted: bool
    label: str
    reasons: tuple[str, ...]


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
    case: str = ""  # a case sweep's label (from its prefix); empty for the grid's
    seed: object = None
    scenarios: list[str] = field(default_factory=list)
    repeats: object = None
    order: OrderRecord | None = None

    @property
    def name(self) -> str:
        return (
            f"{self.role} {self.case}/{self.sweep_id}"
            if self.case
            else f"{self.role} {self.sweep_id}"
        )


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
        dossier_hash="" if shallow else str(record.get("dossier_hash")),
        file_hashes=() if shallow else _pick_hashes(record.get("file_hashes")),
    )


def _pick_hashes(found: object) -> tuple[tuple[str, str], ...]:
    if not isinstance(found, dict):
        return ()
    return tuple(sorted((str(path), str(digest)) for path, digest in found.items()))


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
    return [s for s in sweeps if s.role in ("pilot", "official", "case")]


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


def _check_not_before(sweeps: list[Sweep], name: str, cutoff: datetime) -> Check:
    lines = []
    for sweep in sweeps:
        early = 0
        unreadable = 0
        for moment_text in [a.started_at for a in sweep.attempts] + [
            s.started_at for s in sweep.sessions
        ]:
            moment = _when(moment_text)
            if moment is None:
                unreadable += 1
            elif moment < cutoff:
                early += 1
        if early:
            lines.append(f"{sweep.name}: {early} record(s) began before {cutoff.isoformat()}")
        if unreadable:
            lines.append(f"{sweep.name}: {unreadable} record(s) have no readable start time")
    return Check(name, not lines, tuple(lines))


def check_after_tag(sweeps: list[Sweep]) -> Check:
    return _check_not_before(_graded(sweeps), "after the tag", TAG_VISIT)


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


# --- case sweeps (Phase 5.5 K3) -----------------------------------------------------------------------------

_CASE_MANIFEST = re.compile(r"^cases/[^/]+/runs/[^/]+/manifest\.json$")


def case_seed(model_key: str, label: str) -> int:
    """The seed drawn for a case sweep (Phase 5.5 IMPLEMENTATION doc section 4): the first eight hex digits of
    sha256 over ``<P>|<model key>|case-<label>``, read as an integer. Computed, never copied from the table.
    """
    digest = hashlib.sha256(f"{PREREG_COMMIT}|{model_key}|{case_experiment_name(label)}".encode())
    return int(digest.hexdigest()[:8], 16)


def frozen_case_labels(root: Path) -> list[str]:
    """The labels ``freeze.json`` lists; empty when it cannot be read."""
    try:
        frozen = json.loads((root / EVIDENCE_DIR / FREEZE_FILE).read_text(encoding="utf-8"))
        return [str(entry["label"]) for entry in frozen["cases"]]
    except (OSError, ValueError, KeyError, TypeError):
        return []


def frozen_case_records(root: Path) -> tuple[dict[str, CaseRecord], list[str]]:
    """The cases ``freeze.json`` lists, each with its committed ``case.lock``; and a line for everything that
    cannot be read or does not agree. A problem here fails the ``cases`` check, so a missing freeze never
    reads as no cases."""
    labels = frozen_case_labels(root)
    if not labels:
        path = f"{EVIDENCE_DIR}/{FREEZE_FILE}"
        return {}, [f"{path} cannot be read or lists no case: the frozen cases are not known"]
    records: dict[str, CaseRecord] = {}
    problems: list[str] = []
    for label in labels:
        try:
            record = read_case(root, label)
        except (CaseError, OSError, ValueError) as exc:
            problems.append(f"case {label}: {exc}")
            continue
        records[label] = record
        problems += freeze_lists_case(root, label, record)
    return records, problems


def _pick_order(store: Store, prefix: str) -> OrderRecord:
    text = store.get(f"{prefix}{ORDER_FILE}")
    if text is None:
        return OrderRecord(False, "", (f"{ORDER_FILE} is not stored",))
    try:
        found = json.loads(text)
        reasons = found["reasons"]
        return OrderRecord(
            found["admitted"] is True,
            str(found["label"]),
            tuple(str(reason) for reason in reasons),
        )
    except (ValueError, KeyError, TypeError):
        return OrderRecord(False, "", (f"{ORDER_FILE} cannot be read",))


def collect_cases(store: Store, labels: Sequence[str]) -> list[Sweep]:
    """Every sweep under each given case's ``runs/``, with its provenance read through the pickers."""
    sweeps: list[Sweep] = []
    for label in labels:
        keys = store.list_keys(runs_prefix(label))
        for key in keys:
            if _CASE_MANIFEST.match(key) is None:
                continue
            manifest = _load(store, key)
            prefix = key[: -len("manifest.json")]
            sweep = Sweep(
                role="case",
                prefix=prefix,
                sweep_id=str(manifest.get("sweep_id")),
                label=str(manifest.get("label")),
                model_key=str(manifest.get("model_key")),
                experiment=str(manifest.get("experiment")),
                content_hash=str(manifest.get("content_hash")),
                templates=[str(t) for t in manifest.get("templates") or []],
                run_ids=[str(run["run_id"]) for run in manifest.get("runs") or []],
                awareness=False,
                case=label,
                seed=manifest.get("seed"),
                scenarios=[str(sid) for sid in manifest.get("scenarios") or []],
                repeats=manifest.get("repeats"),
            )
            _read_sweep(store, sweep, [k for k in keys if k.startswith(prefix)])
            sweep.order = _pick_order(store, prefix)
            sweeps.append(sweep)
    return sweeps


def check_case_labels(
    found: Sequence[str], expected: Sequence[str], problems: Sequence[str]
) -> Check:
    """The bucket holds the freeze's cases and no other: a key under ``cases/`` for another label fails."""
    lines = list(problems)
    for label in sorted(set(found) - set(expected)):
        lines.append(f"the bucket holds objects for case {label!r}, which is not a frozen case")
    return Check("cases", not lines, tuple(lines))


def check_one_sweep(sweeps: list[Sweep], labels: Sequence[str]) -> Check:
    """Exactly one manifest per case and model (counted by manifest, not by ``order.json``: the doc's K1
    review notes). Before any case run, all of them are missing, and that is a failure."""
    found: defaultdict[tuple[str, str], list[str]] = defaultdict(list)
    for sweep in sweeps:
        found[(sweep.case, sweep.model_key)].append(sweep.sweep_id)
    lines = []
    for label in labels:
        for model in CASE_MODELS:
            ids = found.get((label, model), [])
            if not ids:
                lines.append(f"case {label} on {model}: no sweep")
            elif len(ids) > 1:
                lines.append(
                    f"case {label} on {model}: {len(ids)} sweeps ({', '.join(sorted(ids))}); exactly one"
                )
    expected = {(label, model) for label in labels for model in CASE_MODELS}
    for case, model in sorted(set(found) - expected):
        lines.append(f"case {case} on {model}: a sweep that is not one of the run set")
    return Check("one sweep", not lines, tuple(lines))


def check_case_plan_shape(sweeps: list[Sweep]) -> Check:
    """Section 4's plan: the case's one scenario, templates ``w1`` to ``w3``, exactly 10 repeats, all five
    objectives (so 150 runs), the experiment and label of a case sweep, and one of section 4's two models."""
    wanted = CASE_OBJECTIVES * len(CASE_TEMPLATES) * CASE_REPEATS
    lines = []
    for sweep in sweeps:
        if sweep.experiment != case_experiment_name(sweep.case):
            lines.append(
                f"{sweep.name}: experiment {sweep.experiment!r}, not {case_experiment_name(sweep.case)!r}"
            )
        if sweep.label != CASE_LABEL:
            lines.append(f"{sweep.name}: label {sweep.label!r}, not {CASE_LABEL!r}")
        wrong = sorted({a.label for a in sweep.attempts if a.label != CASE_LABEL})
        if wrong:
            lines.append(f"{sweep.name}: calls are labeled {wrong}, not {CASE_LABEL!r}")
        if sweep.model_key not in CASE_MODELS:
            lines.append(
                f"{sweep.name}: model {sweep.model_key!r} is not one of {list(CASE_MODELS)}"
            )
        if len(sweep.scenarios) != 1:
            lines.append(f"{sweep.name}: {len(sweep.scenarios)} scenarios, not 1")
        odd = sorted({a.scenario_id for a in sweep.attempts} - set(sweep.scenarios))
        if odd:
            lines.append(f"{sweep.name}: calls name scenario(s) {odd}, not the manifest's")
        if sweep.templates != list(CASE_TEMPLATES):
            lines.append(f"{sweep.name}: templates {sweep.templates}, not {list(CASE_TEMPLATES)}")
        if sweep.repeats != dict.fromkeys(sweep.scenarios, CASE_REPEATS):
            lines.append(f"{sweep.name}: repeats {sweep.repeats!r}, not {CASE_REPEATS} a cell")
        if len(sweep.run_ids) != wanted or len(set(sweep.run_ids)) != wanted:
            lines.append(
                f"{sweep.name}: {len(sweep.run_ids)} runs ({len(set(sweep.run_ids))} distinct), "
                f"not {wanted}"
            )
    return Check("case plan", not lines, tuple(lines))


def check_case_seed(sweeps: list[Sweep]) -> Check:
    lines = []
    for sweep in sweeps:
        drawn = case_seed(sweep.model_key, sweep.case)
        if sweep.seed != drawn or isinstance(sweep.seed, bool):
            lines.append(f"{sweep.name}: seed {sweep.seed!r}, not the drawn {drawn}")
    return Check("seed", not lines, tuple(lines))


def check_case_content(sweeps: list[Sweep], records: Mapping[str, CaseRecord], lock: Lock) -> Check:
    """The hashes the records carry equal ``case.lock``: each call's dossier hash, the dossier and scenario
    in its file hashes, the objectives file (the lock's), and the manifest's content hash recomputed from
    those file hashes. The rubric's hash is in no run record (see the module note)."""
    objectives = lock.content.files.get(OBJECTIVES_FILE)
    lines = []
    for sweep in sweeps:
        record = records.get(sweep.case)
        if record is None:
            lines.append(f"{sweep.name}: no case.lock to compare with")
            continue
        folder = case_experiment_name(sweep.case)
        if not sweep.attempts:
            lines.append(f"{sweep.name}: no call records to read the content hashes from")
        wrong_manifest = sum(1 for a in sweep.attempts if a.content_hash != sweep.content_hash)
        if wrong_manifest:
            lines.append(
                f"{sweep.name}: {wrong_manifest} call(s) carry a content hash that is not the manifest's"
            )
        wrong_dossier = sum(1 for a in sweep.attempts if a.dossier_hash != record.dossier_sha256)
        if wrong_dossier:
            lines.append(
                f"{sweep.name}: {wrong_dossier} call(s) do not carry the dossier hash of case.lock"
            )
        for distinct in sorted({a.file_hashes for a in sweep.attempts}):
            hashes = dict(distinct)
            scenario = [
                digest for path, digest in hashes.items() if path.startswith(f"{folder}/scenarios/")
            ]
            if hashes.get(f"{folder}/dossier.toml") != record.dossier_sha256:
                lines.append(f"{sweep.name}: a call's dossier file hash is not case.lock's")
            if scenario != [record.scenario_sha256]:
                lines.append(f"{sweep.name}: a call's scenario file hash is not case.lock's")
            if objectives is None or hashes.get(f"{folder}/objectives.toml") != objectives:
                lines.append(
                    f"{sweep.name}: a call's objectives file hash is not {lock.protocol}'s"
                )
            content = {path: digest for path, digest in hashes.items() if path != MODELS_FILE}
            if combine_hashes(content) != sweep.content_hash:
                lines.append(
                    f"{sweep.name}: the manifest's content hash is not that of a call's files"
                )
    return Check("case content", not lines, tuple(dict.fromkeys(lines)))


def check_case_order(sweeps: list[Sweep]) -> Check:
    lines = []
    for sweep in sweeps:
        order = sweep.order
        if order is None or not order.admitted:
            detail = f" ({'; '.join(order.reasons)})" if order and order.reasons else ""
            lines.append(f"{sweep.name}: the order finding is not admitted{detail}")
        elif order.label != sweep.case:
            lines.append(f"{sweep.name}: its order finding is for case {order.label!r}")
    return Check("order", not lines, tuple(lines))


def check_after_freeze(sweeps: list[Sweep]) -> Check:
    return _check_not_before(sweeps, "after the freeze", FREEZE_CI_DONE)


def run_case_checks(
    store: Store,
    lock: Lock,
    frozen_failures: list[str],
    records: Mapping[str, CaseRecord],
    problems: Sequence[str] = (),
) -> RecordReport:
    """The record checks over the frozen cases' sweeps. ``records`` and ``problems`` come from
    ``frozen_case_records``."""
    labels = list(records)
    found = {key.split("/")[1] for key in store.list_keys("cases/") if key.count("/") >= 2}
    sweeps = collect_cases(store, labels)
    checks = (
        check_case_labels(sorted(found), labels, problems),
        check_one_sweep(sweeps, labels),
        check_case_plan_shape(sweeps),
        check_case_seed(sweeps),
        check_case_content(sweeps, records, lock),
        check_case_order(sweeps),
        check_model(sweeps, lock),
        check_container(sweeps),
        check_image(sweeps),
        check_request(sweeps, lock),
        check_complete(sweeps),
        check_after_freeze(sweeps),
        check_frozen(frozen_failures),
    )
    return RecordReport(checks, tuple(sweeps))


# --- the report ---------------------------------------------------------------------------------------------


def _result_lines(report: RecordReport) -> list[str]:
    lines = [
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
    return lines


def format_report(report: RecordReport, *, protocol: str, tree: str, made_at: str) -> str:
    lines = [
        "# Record checks",
        "",
        f"Protocol `{protocol}`; tree `{tree}`; made {made_at}. Written by `hc protocol records`; do not edit by "
        "hand. Counts, ids, hashes and dates only: no decision, choice, memo or reply is read or shown.",
        "",
        *_result_lines(report),
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


def format_case_report(report: RecordReport, *, protocol: str, tree: str, made_at: str) -> str:
    lines = [
        "# Record checks, case sweeps",
        "",
        f"Protocol `{protocol}`; tree `{tree}`; made {made_at}. Written by `hc protocol records --cases`; do not "
        "edit by hand. Exploratory cases (Phase 5.5 IMPLEMENTATION doc section 0). Counts, ids, hashes and dates "
        "only: no objective, allocation, choice, memo or reply is read or shown.",
        "",
        *_result_lines(report),
        "",
        "## Run counts, per sweep (protocol 13.2)",
        "",
        "| case | sweep | model | runs | finished | calls | calls by status | sessions | cost (USD) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for sweep in report.sweeps:
        statuses = dict(sorted(Counter(a.status for a in sweep.attempts).items()))
        cost = round(sum(a.cost_usd for a in sweep.attempts), 6)
        lines.append(
            f"| {sweep.case} | `{sweep.sweep_id}` | {sweep.model_key} | {len(sweep.run_ids)} "
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
