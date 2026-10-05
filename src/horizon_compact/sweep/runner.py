"""One session of a sweep (Phase 1 IMPLEMENTATION doc sections 6 and 7).

A session plans, resumes, runs and writes. Every attempt is its own write-once object; a run gets
``final.json`` once it has a final status; the session ends with a summary object saying why it stopped. A
re-launch recomputes the plan, refuses unless it matches the stored manifest exactly, skips every run that
has a ``final.json`` and continues an unfinished run at its next free attempt number. Nothing is re-run and
nothing is overwritten.
"""

from __future__ import annotations

import dataclasses
import json
import random
import re
import time
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from horizon_compact.experiment import Experiment, ModelConfig, Objective
from horizon_compact.providers.base import DecisionRequest, ModelRoute, Provider, RawDecision
from horizon_compact.providers.bedrock import build_request
from horizon_compact.smoke.record import serialize_safely
from horizon_compact.sweep.classify import (
    MAX_MODEL_ATTEMPTS,
    NON_MODEL_STATUSES,
    RETRYABLE_MODEL_STATUSES,
    Outcome,
    classify,
)
from horizon_compact.sweep.identity import RunnerIdentity
from horizon_compact.sweep.pacing import Pacer, backoff_seconds
from horizon_compact.sweep.plan import RunSpec, SweepPlan, SweepRefusal, check_preflight
from horizon_compact.sweep.prompt import RenderedPrompt, build_tool, render_prompt
from horizon_compact.sweep.spend import (
    SpendCap,
    attempt_cost_usd,
    estimate_input_tokens,
    worst_case_attempt_usd,
)
from horizon_compact.sweep.store import Store

RECORD_VERSION = 1
SONNET_ROUTE_ENV = "HC_SONNET_ROUTE"
PROTOCOL_LOCK = ("protocol", "prereg.lock")
_RUN_KEY = re.compile(
    r"runs/(?P<run>r-[0-9a-f]{12})/(?:attempt-(?P<n>\d+)|(?P<final>final))\.json$"
)

# Why a session stopped. "complete" and the first three are clean: a re-launch resumes. The last two are not.
CLEAN_STOPS = frozenset({"complete", "cap_reached", "max_minutes", "stop_requested"})
# This many api_errors in a row, across runs, means the problem is not transient: stop and say so. (Phase 1
# IMPLEMENTATION doc section 6.4 said unlimited within the wall clock; a daily quota showed that hides a
# stuck sweep.)
MAX_CONSECUTIVE_API_ERRORS = 10


@dataclass(frozen=True)
class SessionResult:
    stopped: str
    runs_total: int
    runs_finished_before: int
    runs_finished_now: int
    attempts_now: int
    cost_usd_now: float
    cost_usd_total: float
    summary_key: str

    @property
    def clean(self) -> bool:
        return self.stopped in CLEAN_STOPS


def check_route(experiment: Experiment, model_key: str, env: Mapping[str, str]) -> None:
    """A session refuses when the task's route and ``models.toml``'s differ, so a mismatch can never surface
    as a run of ``AccessDenied`` errors (section 9.3). Only the main model has a decided route; the variable
    is optional on the laptop, always set in the task definition."""
    config = experiment.model(model_key)
    configured = env.get(SONNET_ROUTE_ENV)
    if config.role == "main" and configured and configured != config.route:
        raise SweepRefusal(
            f"{SONNET_ROUTE_ENV} is {configured!r} but models.toml says route {config.route!r} for "
            f"{model_key}; they must agree"
        )


def check_official(experiment: Experiment, identity: RunnerIdentity) -> None:
    """``--official`` needs (a) a committed protocol whose recorded content hash equals the current one and
    (b) a container with an image digest. Phase 3.5 owns the lock file's format; until then (a) never
    holds."""
    lock = experiment.root.joinpath(*PROTOCOL_LOCK)
    if not lock.is_file() or not _lock_matches(lock.read_text(encoding="utf-8"), experiment):
        raise SweepRefusal(
            "official sweeps are refused: no committed protocol (prereg-v1 does not exist)"
        )
    if not identity.in_container:
        raise SweepRefusal(
            "official sweeps are refused: they run only in the container, never on a laptop"
        )


def _lock_matches(text: str, experiment: Experiment) -> bool:
    import tomllib

    try:
        return tomllib.loads(text).get("content_hash") == experiment.content_hash
    except tomllib.TOMLDecodeError:
        return False


def _now_utc() -> datetime:
    return datetime.now(UTC)


@dataclass
class _Tally:
    attempts: int = 0
    cost: float = 0.0
    finished: int = 0
    consecutive_api_errors: int = 0


class _Existing:
    """What the store already holds for this sweep."""

    def __init__(self, store: Store, prefix: str) -> None:
        self.finals: set[str] = set()
        self.attempts: dict[str, list[dict[str, Any]]] = {}
        for key in store.list_keys(f"{prefix}runs/"):
            match = _RUN_KEY.search(key)
            if match is None:
                continue
            if match.group("final"):
                self.finals.add(match.group("run"))
                continue
            text = store.get(key)
            if text is None:
                raise SweepRefusal(f"{key} was listed but cannot be read")
            self.attempts.setdefault(match.group("run"), []).append(json.loads(text))
        for items in self.attempts.values():
            items.sort(key=lambda a: int(a["attempt"]))

    def cost_usd(self) -> float:
        costs = (float(a.get("cost_usd", 0.0)) for items in self.attempts.values() for a in items)
        return round(sum(costs), 6)


def _check_manifest(store: Store, key: str, plan: SweepPlan) -> None:
    wanted = plan.manifest()
    text = json.dumps(wanted, indent=2, sort_keys=True) + "\n"
    if store.put_new(key, text):
        return
    stored = store.get(key)
    if stored is None or json.loads(stored) != wanted:
        raise SweepRefusal(
            f"the stored manifest for {plan.sweep_id} differs from the plan recomputed from the "
            "current files, seed and repeats; refusing to resume (a changed experiment is a new sweep)"
        )


def _attempt_record(
    *,
    plan: SweepPlan,
    experiment: Experiment,
    spec: RunSpec,
    prompt: RenderedPrompt,
    request: DecisionRequest,
    raw: RawDecision,
    outcome: Outcome,
    attempt: int,
    cost_usd: float,
    identity: RunnerIdentity,
    harness_version: str,
) -> dict[str, Any]:
    prov = raw.provenance
    tool_input = raw.tool_input
    return {
        "record_version": RECORD_VERSION,
        "label": "development",
        "sweep_id": plan.sweep_id,
        "run_id": spec.run_id,
        "attempt": attempt,
        "git_sha": identity.git_sha,
        "git_dirty": identity.git_dirty,
        "image_digest": identity.image_digest,
        "image": identity.image,
        "runner": identity.runner,
        "task_arn": identity.task_arn,
        "harness_version": harness_version,
        "provider": prov.provider,
        "api": prov.api,
        "model_key": plan.model_key,
        "model_id": prov.model_id,
        "route_kind": prov.route_kind,
        "inference_profile": prov.inference_profile,
        "invoke_id": prov.invoke_id,
        "region": prov.region,
        "effort": prov.effort,
        "thinking": prov.thinking,
        "temperature": prov.temperature,
        "max_tokens": prov.max_tokens,
        "prompt_sha256": prov.prompt_sha256,
        "content_hash": experiment.content_hash,
        "file_hashes": experiment.file_hashes,
        "scenario_id": spec.scenario_id,
        "objective_id": spec.objective_id,
        "wording_variant_id": spec.wording_id,
        "dossier_hash": experiment.file_hashes[f"{experiment.name}/dossier.toml"],
        "menu_order_seed": str(spec.menu_order_seed),
        "menu_order": list(prompt.lever_order),
        "option_order": list(prompt.option_order),
        "started_at": prov.started_at,
        "finished_at": prov.finished_at,
        "latency_ms": prov.latency_ms,
        "usage": dataclasses.asdict(raw.usage),
        "cost_usd": cost_usd,
        "request": json.loads(json.dumps(build_request(request), default=str)),
        "raw_response": json.loads(json.dumps(raw.raw_response, default=str)),
        "stop_reason": raw.stop_reason,
        "tool_calls": raw.tool_calls,
        "text_blocks": raw.text_blocks,
        "reasoning_block_count": raw.reasoning_block_count,
        "parsed_decision": tool_input if isinstance(tool_input, dict) else None,
        "validation": outcome.validation.as_dict() if outcome.validation else None,
        "status": outcome.status,
        "possible_decline": outcome.possible_decline,
        "error": raw.error,
        "detail": outcome.detail,
    }


def run_session(
    *,
    experiment: Experiment,
    plan: SweepPlan,
    route: ModelRoute,
    provider: Provider,
    store: Store,
    identity: RunnerIdentity,
    account_id: str,
    cap_usd: float,
    max_minutes: float,
    harness_version: str,
    now: Callable[[], datetime] = _now_utc,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    rng: random.Random | None = None,
    should_stop: Callable[[], bool] = lambda: False,
    pacer: Pacer | None = None,
    progress: Callable[[str], None] = lambda line: None,
) -> SessionResult:
    config: ModelConfig = experiment.model(plan.model_key)
    check_preflight(experiment, plan, cap_usd)
    prefix = f"development/{plan.sweep_id}/"
    _check_manifest(store, f"{prefix}manifest.json", plan)

    existing = _Existing(store, prefix)
    cap = SpendCap(cap_usd, existing.cost_usd())
    pacer = pacer or Pacer(
        config.requests_per_minute, experiment.models.pace_fraction, monotonic, sleep
    )
    rng = rng or random.Random()
    scenario = experiment.scenario
    tool = build_tool(scenario)
    objectives: dict[str, Objective] = {o.id: o for o in experiment.objectives}
    started = now()
    deadline = monotonic() + max_minutes * 60
    finished_before = len(existing.finals & {r.run_id for r in plan.runs})
    counts: Counter[str] = Counter()
    tally = _Tally()

    def write_final(spec: RunSpec, attempts: list[dict[str, Any]]) -> bool:
        model_attempts = [a for a in attempts if a["status"] not in NON_MODEL_STATUSES]
        last = model_attempts[-1]
        record = {
            "record_version": RECORD_VERSION,
            "label": "development",
            "sweep_id": plan.sweep_id,
            "run_id": spec.run_id,
            "objective_id": spec.objective_id,
            "status": last["status"],
            "first_attempt_status": model_attempts[0]["status"],
            "final_attempt": last["attempt"],
            "attempts": len(attempts),
            "model_attempts": len(model_attempts),
            "cost_usd": round(sum(a.get("cost_usd", 0.0) for a in attempts), 6),
        }
        text = serialize_safely(record, account_id)
        return store.put_new(f"{prefix}runs/{spec.run_id}/final.json", text)

    def nap(seconds: float) -> None:
        """Sleep in slices of at most a second, so a stop request is honoured within a second."""
        remaining = seconds
        while remaining > 0 and not should_stop():
            step = min(1.0, remaining)
            sleep(step)
            remaining -= step

    def run_one(position: int, spec: RunSpec) -> str | None:
        prompt = render_prompt(experiment, objectives[spec.objective_id], spec.menu_order_seed)
        request = DecisionRequest(
            route=route,
            system=prompt.system,
            user=prompt.user,
            tool=tool,
            max_tokens=scenario.max_tokens,
            cache_system=True,
        )
        worst = worst_case_attempt_usd(
            estimate_input_tokens(prompt.system, prompt.user, tool),
            scenario.max_tokens,
            config.prices,
        )
        attempts = list(existing.attempts.get(spec.run_id, []))
        next_n = max((int(a["attempt"]) for a in attempts), default=0) + 1
        model_done = [a for a in attempts if a["status"] not in NON_MODEL_STATUSES]
        # An interrupted run may already hold its last attempt without a final.json (a crash between the two
        # writes).
        if model_done and (
            model_done[-1]["status"] not in RETRYABLE_MODEL_STATUSES
            or len(model_done) >= MAX_MODEL_ATTEMPTS
        ):
            return None if write_final(spec, attempts) else "write_conflict"
        api_streak = 0
        while True:
            if should_stop():
                return "stop_requested"
            if monotonic() >= deadline:
                return "max_minutes"
            if not cap.allows(worst):
                return "cap_reached"
            pacer.wait()
            raw = provider.decide(request)
            outcome = classify(raw, scenario)
            cost = attempt_cost_usd(raw.usage, config.prices)
            record = _attempt_record(
                plan=plan,
                experiment=experiment,
                spec=spec,
                prompt=prompt,
                request=request,
                raw=raw,
                outcome=outcome,
                attempt=next_n,
                cost_usd=cost,
                identity=identity,
                harness_version=harness_version,
            )
            text = serialize_safely(record, account_id)
            if not store.put_new(f"{prefix}runs/{spec.run_id}/attempt-{next_n}.json", text):
                return "write_conflict"
            cap.record(cost)
            tally.attempts += 1
            tally.cost = round(tally.cost + cost, 6)
            counts[outcome.status] += 1
            attempts.append(record)
            next_n += 1
            note = f" {outcome.detail}" if outcome.detail else ""
            progress(
                f"run {position}/{len(plan.runs)} {spec.objective_id} attempt {next_n - 1}: "
                f"{outcome.status}{note}  (${tally.cost:.4f} so far)"
            )
            if outcome.stop_session:
                return outcome.stop_as
            if outcome.status == "api_error":
                tally.consecutive_api_errors += 1
                if tally.consecutive_api_errors >= MAX_CONSECUTIVE_API_ERRORS:
                    return "api_errors"
                wait = backoff_seconds(api_streak, rng)
                progress(
                    f"  backing off {wait:.0f}s ({tally.consecutive_api_errors} api errors in a row)"
                )
                nap(wait)
                api_streak += 1
                continue
            tally.consecutive_api_errors = 0
            api_streak = 0
            done = [a for a in attempts if a["status"] not in NON_MODEL_STATUSES]
            if outcome.retry == "model" and len(done) < MAX_MODEL_ATTEMPTS:
                continue
            if not write_final(spec, attempts):
                return "write_conflict"
            tally.finished += 1
            return None

    stopped = "crashed"
    try:
        stopped = "complete"
        for position, spec in enumerate(plan.runs, 1):
            if spec.run_id in existing.finals:
                continue
            reason = run_one(position, spec)
            if reason is not None:
                stopped = reason
                break
    finally:
        summary = {
            "record_version": RECORD_VERSION,
            "label": "development",
            "sweep_id": plan.sweep_id,
            "runner": identity.runner,
            "image_digest": identity.image_digest,
            "git_sha": identity.git_sha,
            "started_at": started.isoformat(),
            "finished_at": now().isoformat(),
            "stopped": stopped,
            "runs_total": len(plan.runs),
            "runs_finished_before": finished_before,
            "runs_finished_this_session": tally.finished,
            "attempts_this_session": tally.attempts,
            "status_counts_this_session": dict(sorted(counts.items())),
            "cost_usd_this_session": tally.cost,
            "cost_usd_sweep_total": cap.spent_usd,
            "cap_usd": cap_usd,
        }
        stamp = started.strftime("%Y%m%dT%H%M%S%fZ")
        summary_key = f"{prefix}sessions/{stamp}-{identity.runner}.json"
        store.put_new(summary_key, serialize_safely(summary, account_id))

    return SessionResult(
        stopped=stopped,
        runs_total=len(plan.runs),
        runs_finished_before=finished_before,
        runs_finished_now=tally.finished,
        attempts_now=tally.attempts,
        cost_usd_now=tally.cost,
        cost_usd_total=cap.spent_usd,
        summary_key=summary_key,
    )
