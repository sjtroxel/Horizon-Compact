"""The awareness probe's run (Phase 4 code half IMPLEMENTATION doc section 4.5, protocol 9.6).

After the grid, a separate sweep on one model: **S1, every objective under every template, one call each, 15
calls**. Each call is the decision prompt exactly as a grid run shows it (``render_awareness_prompt``), with
no tool offered and the instruction replaced by the protocol's question. It has its own sweep id, manifest and
cap (``build_plan`` with the label ``awareness``), and writes under ``official/<experiment>/awareness/<id>/``.

**A reply is the measurement, so a model reply is never retried**; an API error is retried with backoff, and
too many in a row stop the session. Every API error is kept too, under ``errors/``, since each is a call made
(protocol 13.2). A re-run resumes: a call that has a record is skipped, never repeated.
Every reply is stored write-once and quoted in full by the report, which runs after the grid and filters
nothing: the probe is context, never used to filter or weight a run (protocol 9.6).

It is an official sweep, so the gate's checks (the lock, the content, the instrument, the model, the
container) apply exactly as for the grid; the sealed template is among the 15 because "every template" means
every one, and the gate's check 4 wants it in the plan.
"""

from __future__ import annotations

import dataclasses
import json
import random
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from horizon_compact.experiment import Experiment
from horizon_compact.providers.base import ModelRoute, RawDecision, TextProvider, TextRequest
from horizon_compact.smoke.record import serialize_safely
from horizon_compact.sweep.classify import classify_error
from horizon_compact.sweep.identity import RunnerIdentity
from horizon_compact.sweep.pacing import Pacer, backoff_seconds
from horizon_compact.sweep.plan import RunSpec, SweepPlan, SweepRefusal, build_plan
from horizon_compact.sweep.prompt import RenderedPrompt, render_awareness_prompt
from horizon_compact.sweep.runner import CLEAN_STOPS, MAX_CONSECUTIVE_API_ERRORS, Role, sweep_prefix
from horizon_compact.sweep.spend import (
    SpendCap,
    attempt_cost_usd,
    estimate_input_tokens_text,
    worst_case_attempt_usd,
)
from horizon_compact.sweep.store import Store
from horizon_compact.sweep.warning import SpendEstimate, likely_call_usd

RECORD_VERSION = 1
LABEL = "awareness"
SCENARIO = "s1"
ROLE: Role = "official"
_NORMAL_STOPS = frozenset({"end_turn", "tool_use"})


def build_awareness_plan(experiment: Experiment, model_key: str, seed: int) -> SweepPlan:
    """S1, every objective, every template, one call each. The seed is the probe sweep's own, recorded in its
    manifest; the menu order of each call comes from it and the call's run id, as in the grid."""
    if SCENARIO not in experiment.scenarios:
        raise SweepRefusal(
            f"{experiment.name} has no scenario {SCENARIO!r} for the awareness probe"
        )
    return build_plan(
        experiment,
        model_key=model_key,
        label=LABEL,
        repeats=1,
        seed=seed,
        scenarios=[SCENARIO],
        templates=None,
        official=True,
    )


def awareness_prefix(plan: SweepPlan) -> str:
    return sweep_prefix(plan.experiment, f"{LABEL}/{plan.sweep_id}", ROLE)


def _record_key(prefix: str, run_id: str) -> str:
    return f"{prefix}runs/{run_id}.json"


def _error_key(prefix: str, run_id: str, n: int) -> str:
    """An API error on call ``run_id``: no reply, but a call made, so it is kept too (protocol 13.2: one
    object per attempt, provenance on every call). ``n`` counts that call's errors from 1."""
    return f"{prefix}errors/{run_id}-{n}.json"


def _render(experiment: Experiment, plan: SweepPlan, index: int) -> tuple[RenderedPrompt, int]:
    """Call ``index``'s prompt as the grid would render it, with the awareness question, and its output
    allowance (the scenario's, the same room a grid run has)."""
    spec = plan.runs[index]
    scenario = experiment.get_scenario(spec.scenario_id)
    objective = next(o for o in experiment.objectives if o.id == spec.objective_id)
    prompt = render_awareness_prompt(
        experiment, scenario, objective, spec.wording_id, spec.menu_order_seed
    )
    return prompt, scenario.max_tokens


def awareness_worst_case_usd(experiment: Experiment, plan: SweepPlan) -> float:
    """The most one call can cost: the rendered prompt at full price and the scenario's whole output
    allowance; the largest over the 15."""
    prices = experiment.model(plan.model_key).prices
    worst = 0.0
    for index in range(len(plan.runs)):
        prompt, max_tokens = _render(experiment, plan, index)
        tokens = estimate_input_tokens_text(prompt.system, prompt.user)
        worst = max(worst, worst_case_attempt_usd(tokens, max_tokens, prices))
    return worst


def check_awareness_cap(experiment: Experiment, plan: SweepPlan, cap_usd: float) -> float:
    """Refuse to start above the cap. One call each and no retry of a reply, so the bound is the calls times
    one call's worst case. Returns the bound."""
    bound = round(len(plan.runs) * awareness_worst_case_usd(experiment, plan), 4)
    if bound > cap_usd:
        raise SweepRefusal(
            f"the worst case for {len(plan.runs)} awareness calls is ${bound:.2f}, above the cap of "
            f"${cap_usd:.2f}"
        )
    return bound


def awareness_estimate(experiment: Experiment, plan: SweepPlan, store: Store) -> SpendEstimate:
    prefix = awareness_prefix(plan)
    done = set(store.list_keys(f"{prefix}runs/"))
    prices = experiment.model(plan.model_key).prices
    calls = 0
    likely = 0.0
    worst = 0.0
    for index, spec in enumerate(plan.runs):
        if _record_key(prefix, spec.run_id) in done:
            continue
        prompt, max_tokens = _render(experiment, plan, index)
        tokens = estimate_input_tokens_text(prompt.system, prompt.user)
        calls += 1
        likely += likely_call_usd(tokens, prices.input, prices.output)
        worst += worst_case_attempt_usd(tokens, max_tokens, prices)
    return SpendEstimate(
        what="awareness calls not yet recorded",
        calls=calls,
        likely_usd=likely,
        worst_usd=worst,
        worst_basis="one call each at the full output allowance; a reply is never retried",
    )


def _status(raw: RawDecision) -> str:
    """What kind of reply this was. Every one is kept; the status only labels it."""
    if raw.stop_reason == "max_tokens":
        return "truncated"
    if raw.stop_reason == "content_filtered":
        return "content_filtered"
    if raw.stop_reason not in _NORMAL_STOPS:
        return "unexpected_stop"
    if raw.tool_call_count:
        return "unexpected_tool_call"  # no tool was offered, so this is the provider's fault, not the model's
    return "replied" if any(t.strip() for t in raw.text_blocks) else "no_text"


@dataclass(frozen=True)
class AwarenessResult:
    stopped: str
    calls_total: int
    calls_done_before: int
    calls_done_now: int
    api_calls_now: int
    cost_usd_now: float
    cost_usd_total: float

    @property
    def clean(self) -> bool:
        return self.stopped in CLEAN_STOPS


def _check_manifest(store: Store, key: str, plan: SweepPlan) -> None:
    text = json.dumps(plan.manifest(), indent=2, sort_keys=True) + "\n"
    if store.put_new(key, text):
        return
    stored = store.get(key)
    if stored is None or json.loads(stored) != plan.manifest():
        raise SweepRefusal(
            f"the stored manifest for {plan.sweep_id} differs from the plan recomputed from the current "
            "files and seed; refusing to resume (a changed experiment is a new sweep)"
        )


def _call_fields(
    plan: SweepPlan,
    experiment: Experiment,
    spec: RunSpec,
    prompt: RenderedPrompt,
    raw: RawDecision,
    cost: float,
    identity: RunnerIdentity,
    harness_version: str,
) -> dict[str, Any]:
    """The provenance every call's record carries, a reply's or an API error's."""
    prov = raw.provenance
    return {
        "record_version": RECORD_VERSION,
        "label": ROLE,
        "sweep_id": plan.sweep_id,
        "run_id": spec.run_id,
        "scenario_id": spec.scenario_id,
        "objective_id": spec.objective_id,
        "wording_variant_id": spec.wording_id,
        "menu_order_seed": str(spec.menu_order_seed),
        "menu_order": list(prompt.lever_order),
        "option_order": list(prompt.option_order),
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
        "provider_details": dict(prov.details),
        "effort": prov.effort,
        "thinking": prov.thinking,
        "temperature": prov.temperature,
        "max_tokens": prov.max_tokens,
        "prompt_sha256": prov.prompt_sha256,
        "content_hash": experiment.content_hash,
        "file_hashes": experiment.file_hashes,
        "started_at": prov.started_at,
        "finished_at": prov.finished_at,
        "latency_ms": prov.latency_ms,
        "usage": dataclasses.asdict(raw.usage),
        "cost_usd": cost,
    }


def run_awareness(
    *,
    experiment: Experiment,
    plan: SweepPlan,
    route: ModelRoute,
    provider: TextProvider,
    store: Store,
    identity: RunnerIdentity,
    account_id: str,
    cap_usd: float,
    max_minutes: float,
    harness_version: str,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    rng: random.Random | None = None,
    should_stop: Callable[[], bool] = lambda: False,
    progress: Callable[[str], None] = lambda line: None,
) -> AwarenessResult:
    if plan.label != LABEL:
        raise SweepRefusal(f"an awareness session runs the {LABEL!r} plan, not {plan.label!r}")
    config = experiment.model(plan.model_key)
    check_awareness_cap(experiment, plan, cap_usd)
    prefix = awareness_prefix(plan)
    _check_manifest(store, f"{prefix}manifest.json", plan)

    existing = set(store.list_keys(f"{prefix}runs/"))
    error_keys = store.list_keys(f"{prefix}errors/")
    errors_so_far: Counter[str] = Counter(
        key.rsplit("/", 1)[-1].rsplit("-", 1)[0] for key in error_keys
    )
    spent = 0.0
    for key in [*existing, *error_keys]:
        text = store.get(key)
        if text is not None:
            spent += float(json.loads(text).get("cost_usd", 0.0))
    cap = SpendCap(cap_usd, round(spent, 6))
    pacer = Pacer(config.requests_per_minute, experiment.models.pace_fraction, monotonic, sleep)
    rng = rng or random.Random()
    deadline = monotonic() + max_minutes * 60
    total = len(plan.runs)
    done_before = sum(1 for spec in plan.runs if _record_key(prefix, spec.run_id) in existing)
    calls = 0
    cost_now = 0.0
    done_now = 0
    api_errors = 0

    def finish(stopped: str) -> AwarenessResult:
        return AwarenessResult(
            stopped, total, done_before, done_now, calls, round(cost_now, 6), cap.spent_usd
        )

    for index, spec in enumerate(plan.runs):
        record_key = _record_key(prefix, spec.run_id)
        if record_key in existing:
            continue
        prompt, max_tokens = _render(experiment, plan, index)
        request = TextRequest(
            route=route, system=prompt.system, user=prompt.user, max_tokens=max_tokens
        )
        worst = worst_case_attempt_usd(
            estimate_input_tokens_text(prompt.system, prompt.user), max_tokens, config.prices
        )
        api_streak = 0
        while True:
            if should_stop():
                return finish("stop_requested")
            if monotonic() >= deadline:
                return finish("max_minutes")
            if not cap.allows(worst):
                return finish("cap_reached")
            pacer.wait()
            raw = provider.decide_text(request)
            cost = attempt_cost_usd(raw.usage, config.prices)
            cap.record(cost)
            calls += 1
            cost_now += cost
            if raw.status == "api_error":
                errors_so_far[spec.run_id] += 1
                error_record = {
                    **_call_fields(
                        plan, experiment, spec, prompt, raw, cost, identity, harness_version
                    ),
                    "kind": f"{LABEL}-api-error",
                    "request": json.loads(
                        json.dumps(provider.text_request_body(request), default=str)
                    ),
                    "error": raw.error,
                }
                if not store.put_new(
                    _error_key(prefix, spec.run_id, errors_so_far[spec.run_id]),
                    serialize_safely(error_record, account_id),
                ):
                    return finish("write_conflict")
                outcome = classify_error(raw)
                progress(
                    f"call {index + 1}/{total} {spec.objective_id} {spec.wording_id}: api_error "
                    f"{outcome.detail}  (${cost_now:.4f} so far)"
                )
                if outcome.stop_session:
                    return finish(outcome.stop_as)
                api_errors += 1
                if api_errors >= MAX_CONSECUTIVE_API_ERRORS:
                    return finish("api_errors")
                remaining = backoff_seconds(api_streak, rng)
                while remaining > 0 and not should_stop():
                    step = min(1.0, remaining)
                    sleep(step)
                    remaining -= step
                api_streak += 1
                continue
            api_errors = 0
            break
        status = _status(raw)
        record = {
            **_call_fields(plan, experiment, spec, prompt, raw, cost, identity, harness_version),
            "kind": LABEL,
            "request": json.loads(json.dumps(provider.text_request_body(request), default=str)),
            "raw_response": json.loads(json.dumps(raw.raw_response, default=str)),
            "stop_reason": raw.stop_reason,
            "reasoning_block_count": raw.reasoning_block_count,
            "text_blocks": raw.text_blocks,
            "status": status,
        }
        if not store.put_new(record_key, serialize_safely(record, account_id)):
            return finish("write_conflict")
        done_now += 1
        progress(
            f"call {index + 1}/{total} {spec.objective_id} {spec.wording_id}: {status}  "
            f"(${cost_now:.4f} so far)"
        )
    return finish("complete")


def awareness_report(store: Store, experiment: Experiment, plan: SweepPlan) -> str:
    """Every reply, quoted in full, by objective and template. Nothing is filtered, counted as a score or
    weighted: the probe is context (protocol 9.6)."""
    prefix = awareness_prefix(plan)
    records: dict[str, dict[str, Any]] = {}
    for spec in plan.runs:
        text = store.get(_record_key(prefix, spec.run_id))
        if text is not None:
            records[spec.run_id] = json.loads(text)
    lines = [
        f"# Awareness probe: `{plan.sweep_id}`",
        "",
        f"Experiment `{plan.experiment}`, model `{plan.model_key}`, content hash `{plan.content_hash[:12]}`, "
        f"scenario {SCENARIO}, seed {plan.seed}. Written from the stored records; do not edit by hand. "
        "**Context only:** every reply is quoted in full, none is used to filter or weight any run "
        "(protocol 9.6).",
        "",
        f"**Calls recorded: {len(records)} of {len(plan.runs)}.**",
        "",
    ]
    for objective in experiment.objectives:
        lines += [f"## Objective {objective.id}", ""]
        for template_id in plan.templates:
            found = next(
                (
                    r
                    for r in plan.runs
                    if (r.objective_id, r.wording_id) == (objective.id, template_id)
                ),
                None,
            )
            record = records.get(found.run_id) if found else None
            lines.append(f"### Template {template_id}")
            lines.append("")
            if record is None:
                lines += ["_not recorded_", ""]
                continue
            reply = "\n".join(t for t in record["text_blocks"] if t.strip()) or "(no text)"
            lines += [
                f"status `{record['status']}`, stop reason `{record['stop_reason']}`, "
                f"{record['usage']['output_tokens']} output tokens",
                "",
                *(f"> {row}" if row else ">" for row in reply.splitlines()),
                "",
            ]
    # No trailing newline: the command prints this, and print adds the one a file should end with (two failed
    # the end-of-file hook at the reveal's commit; KNOWN-GAPS OPEN 2026-10-15).
    return "\n".join(lines).rstrip("\n")
