"""Running probes and reporting them (Phase 2.5 IMPLEMENTATION doc section 10).

A probe run asks each selected scenario's questions ``repeats`` times, one call per repeat, and writes one
write-once record per repeat under ``development/<experiment>/probes/<probe_run_id>/``. **A repeat is a
measurement, so a model failure is not retried** (a retry would raise the pass rate by hiding the failure);
an API error is retried with backoff, and too many in a row stop the run. A re-run with the same arguments
resumes: a repeat that has a record is skipped, never repeated.

Only a development model may run probes on real content (the same rule as a sweep, section 8.4). A probe
carries no objective, so the undrawn sealed template does not apply, and nothing here can show an answer by
objective. An API error is counted against the cap but not stored: it carries no answer, and the run reports
it as it happens.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from horizon_compact.dossier.figures import FigureSet
from horizon_compact.experiment import PLACEHOLDER_EXPERIMENT, Experiment
from horizon_compact.probes.questions import (
    TOOL_NAME,
    Key,
    ProbeFile,
    build_probe_tool,
    load_probe_file,
    probe_path,
    render_probe,
    resolve_keys,
    score,
)
from horizon_compact.providers.base import DecisionRequest, ModelRoute, Provider, RawDecision
from horizon_compact.smoke.record import serialize_safely
from horizon_compact.sweep.classify import classify_error
from horizon_compact.sweep.identity import RunnerIdentity
from horizon_compact.sweep.pacing import Pacer, backoff_seconds
from horizon_compact.sweep.plan import SweepRefusal
from horizon_compact.sweep.spend import (
    SpendCap,
    attempt_cost_usd,
    estimate_input_tokens,
    worst_case_attempt_usd,
)
from horizon_compact.sweep.store import Store
from horizon_compact.sweep.warning import SpendEstimate, likely_call_usd

RECORD_VERSION = 1
MAX_CONSECUTIVE_API_ERRORS = 10
CLEAN_STOPS = frozenset({"complete", "cap_reached", "max_minutes", "stop_requested"})


def check_probe_model(experiment: Experiment, model_key: str) -> None:
    """No official model sees real content, as a decision or as a probe (section 9)."""
    config = experiment.model(model_key)
    if experiment.name != PLACEHOLDER_EXPERIMENT and config.role != "development":
        raise SweepRefusal(
            f"{model_key} is not the development model (role {config.role!r}); only a development model "
            f"may be asked about {experiment.name}'s content"
        )


@dataclass(frozen=True)
class ProbeSet:
    scenario_id: str
    probe: ProbeFile
    keys: list[Key]
    file_sha256: str


def load_probe_sets(
    experiment: Experiment, fs: FigureSet, scenario_ids: list[str] | None
) -> list[ProbeSet]:
    chosen = scenario_ids or list(experiment.scenarios)
    sets: list[ProbeSet] = []
    for scenario_id in chosen:
        scenario = experiment.get_scenario(scenario_id)
        path = probe_path(experiment, scenario_id)
        if not path.is_file():
            raise SweepRefusal(f"{experiment.name} has no probes for {scenario_id} ({path.name})")
        probe = load_probe_file(path)
        sets.append(
            ProbeSet(
                scenario_id=scenario_id,
                probe=probe,
                keys=resolve_keys(probe, scenario, fs),
                file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        )
    return sets


def probe_run_id(
    experiment: Experiment, model_key: str, label: str, repeats: int, sets: list[ProbeSet]
) -> str:
    """Changes when the content, the questions, the model or the repeats change: a changed probe is a new
    run, never a resumed one."""
    basis = json.dumps(
        {
            "content_hash": experiment.content_hash,
            "model": model_key,
            "repeats": repeats,
            "probes": {s.scenario_id: s.file_sha256 for s in sets},
        },
        sort_keys=True,
    )
    return f"{label}-{model_key}-{hashlib.sha256(basis.encode()).hexdigest()[:8]}"


def probe_estimate(
    experiment: Experiment,
    model_key: str,
    label: str,
    repeats: int,
    sets: list[ProbeSet],
    store: Store,
) -> SpendEstimate:
    """What the repeats not yet recorded should cost: one call each, as a model failure is not retried."""
    prices = experiment.model(model_key).prices
    prefix = probe_prefix(
        experiment.name, probe_run_id(experiment, model_key, label, repeats, sets)
    )
    existing = set(store.list_keys(prefix))
    calls = 0
    likely = 0.0
    worst = 0.0
    for probe_set in sets:
        pending = sum(
            1
            for n in range(1, repeats + 1)
            if f"{prefix}{probe_set.scenario_id}/repeat-{n}.json" not in existing
        )
        if not pending:
            continue
        scenario = experiment.get_scenario(probe_set.scenario_id)
        prompt = render_probe(experiment, scenario, probe_set.probe)
        tokens = estimate_input_tokens(
            prompt.system, prompt.user, build_probe_tool(probe_set.probe)
        )
        calls += pending
        likely += pending * likely_call_usd(tokens, prices.input, prices.output)
        worst += pending * worst_case_attempt_usd(tokens, scenario.max_tokens, prices)
    return SpendEstimate(
        what="probe repeats not yet recorded",
        calls=calls,
        likely_usd=likely,
        worst_usd=worst,
        worst_basis="one call each at the full output allowance; a model failure is not retried",
    )


def probe_prefix(experiment_name: str, run_id: str) -> str:
    return f"development/{experiment_name}/probes/{run_id}/"


def _key_value(key: Key) -> Any:
    return list(key.value) if isinstance(key.value, tuple) else key.value


def _repeat_status(raw: RawDecision) -> str:
    """What kind of reply this was. Only ``answered`` is scored question by question; the rest score every
    question wrong and are listed by type in the report."""
    if raw.stop_reason == "max_tokens":
        return "truncated"
    if raw.stop_reason not in ("tool_use", "end_turn"):
        return "unexpected_stop"
    if raw.tool_call_count == 0:
        return "no_tool_call"
    if raw.tool_call_count > 1:
        return "multiple_calls"
    call = raw.tool_calls[0]
    if call.get("name") != TOOL_NAME:
        return "wrong_tool"
    if not isinstance(call.get("input"), dict):
        return "malformed_answers"
    return "answered"


@dataclass(frozen=True)
class ProbeResult:
    run_id: str
    stopped: str
    repeats_total: int
    repeats_done_before: int
    repeats_done_now: int
    calls_now: int
    cost_usd_now: float

    @property
    def clean(self) -> bool:
        return self.stopped in CLEAN_STOPS


def run_probes(
    *,
    experiment: Experiment,
    model_key: str,
    sets: list[ProbeSet],
    repeats: int,
    label: str,
    route: ModelRoute,
    provider: Provider,
    store: Store,
    identity: RunnerIdentity,
    account_id: str,
    cap_usd: float,
    max_minutes: float,
    harness_version: str,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    rng: random.Random | None = None,
    should_stop: Callable[[], bool] = lambda: False,
    progress: Callable[[str], None] = lambda line: None,
) -> ProbeResult:
    if repeats < 1:
        raise SweepRefusal("repeats must be at least 1")
    check_probe_model(experiment, model_key)
    config = experiment.model(model_key)
    run_id = probe_run_id(experiment, model_key, label, repeats, sets)
    prefix = probe_prefix(experiment.name, run_id)
    existing = set(store.list_keys(prefix))
    spent = 0.0
    for key in existing:
        text = store.get(key)
        if text is not None and key.endswith(".json") and "/repeat-" in key:
            spent += float(json.loads(text).get("cost_usd", 0.0))
    cap = SpendCap(cap_usd, round(spent, 6))
    pacer = Pacer(config.requests_per_minute, experiment.models.pace_fraction, monotonic, sleep)
    rng = rng or random.Random()
    deadline = monotonic() + max_minutes * 60
    total = len(sets) * repeats
    done_before = sum(
        1
        for s in sets
        for n in range(1, repeats + 1)
        if f"{prefix}{s.scenario_id}/repeat-{n}.json" in existing
    )
    calls = 0
    cost_now = 0.0
    done_now = 0
    api_errors = 0

    def finish(stopped: str) -> ProbeResult:
        return ProbeResult(run_id, stopped, total, done_before, done_now, calls, round(cost_now, 6))

    for probe_set in sets:
        scenario = experiment.get_scenario(probe_set.scenario_id)
        prompt = render_probe(experiment, scenario, probe_set.probe)
        tool = build_probe_tool(probe_set.probe)
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
        for n in range(1, repeats + 1):
            record_key = f"{prefix}{probe_set.scenario_id}/repeat-{n}.json"
            if record_key in existing:
                continue
            api_streak = 0
            while True:
                if should_stop():
                    return finish("stop_requested")
                if monotonic() >= deadline:
                    return finish("max_minutes")
                if not cap.allows(worst):
                    return finish("cap_reached")
                pacer.wait()
                raw = provider.decide(request)
                cost = attempt_cost_usd(raw.usage, config.prices)
                cap.record(cost)
                calls += 1
                cost_now += cost
                if raw.status == "api_error":
                    outcome = classify_error(raw)
                    progress(
                        f"{probe_set.scenario_id} repeat {n}: api_error {outcome.detail}  "
                        f"(${cost_now:.4f} so far)"
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
            status = _repeat_status(raw)
            answers = raw.tool_input if status == "answered" else None
            marks = score(probe_set.keys, answers)
            prov = raw.provenance
            record = {
                "record_version": RECORD_VERSION,
                "label": "development",
                "kind": "probe",
                "probe_run_id": run_id,
                "scenario_id": probe_set.scenario_id,
                "repeat": n,
                "model_key": model_key,
                "provider": prov.provider,
                "api": prov.api,
                "model_id": prov.model_id,
                "route_kind": prov.route_kind,
                "provider_details": dict(prov.details),
                "thinking": prov.thinking,
                "temperature": prov.temperature,
                "max_tokens": prov.max_tokens,
                "prompt_sha256": prov.prompt_sha256,
                "content_hash": experiment.content_hash,
                "probe_file_sha256": probe_set.file_sha256,
                "menu_order": list(prompt.lever_order),
                "option_order": list(prompt.option_order),
                "git_sha": identity.git_sha,
                "git_dirty": identity.git_dirty,
                "runner": identity.runner,
                "harness_version": harness_version,
                "started_at": prov.started_at,
                "finished_at": prov.finished_at,
                "latency_ms": prov.latency_ms,
                "usage": dataclasses.asdict(raw.usage),
                "cost_usd": cost,
                "request": json.loads(json.dumps(provider.request_body(request), default=str)),
                "raw_response": json.loads(json.dumps(raw.raw_response, default=str)),
                "stop_reason": raw.stop_reason,
                "text_blocks": raw.text_blocks,
                "status": status,
                "answers": answers,
                "keys": {k.question.id: _key_value(k) for k in probe_set.keys},
                "correct": marks,
            }
            if not store.put_new(record_key, serialize_safely(record, account_id)):
                return finish("write_conflict")
            done_now += 1
            right = sum(marks.values())
            progress(
                f"{probe_set.scenario_id} repeat {n}: {status}, {right} of {len(marks)} correct  "
                f"(${cost_now:.4f} so far)"
            )
    return finish("complete")


# --- the report -----------------------------------------------------------------------------------------


def _cell(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, int):
        text = f"{value:,}"
    elif isinstance(value, list):
        text = ", ".join(str(item) for item in value)
    else:
        text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def probe_report(
    store: Store, experiment: Experiment, run_id: str, sets: list[ProbeSet], repeats: int
) -> str:
    """Each question, its key, correct of the repeats made, and every answer given (probe answers carry no
    objective, so they may be read, section 10). A question passes at 4 of 5 (decision 6), scaled to the
    repeats made: at least 80% of them."""
    prefix = probe_prefix(experiment.name, run_id)
    lines = [
        f"# Probe report: `{run_id}`",
        "",
        f"Experiment `{experiment.name}`, content hash `{experiment.content_hash[:12]}`. Generated by "
        "`hc probes report` from the stored records; do not edit by hand. A question passes when it is "
        "answered correctly in at least 80% of the repeats (4 of 5, decision 6). A number is correct within 1% "
        "of its key.",
        "",
    ]
    for probe_set in sets:
        records = []
        for n in range(1, repeats + 1):
            text = store.get(f"{prefix}{probe_set.scenario_id}/repeat-{n}.json")
            if text is not None:
                records.append(json.loads(text))
        model = records[0]["model_key"] if records else "none"
        statuses: dict[str, int] = {}
        for record in records:
            statuses[record["status"]] = statuses.get(record["status"], 0) + 1
        status_text = ", ".join(f"{k} {v}" for k, v in sorted(statuses.items())) or "none"
        lines += [
            f"## {probe_set.scenario_id}",
            "",
            f"{len(records)} of {repeats} repeats recorded, model `{model}`; replies: {status_text}.",
            "",
            "| Question | Text | Key | Correct | Pass | Answers given |",
            "|---|---|---|---|---|---|",
        ]
        for key in probe_set.keys:
            qid = key.question.id
            correct = sum(1 for r in records if r["correct"].get(qid))
            passed = bool(records) and correct >= 0.8 * len(records)
            given = [
                _cell((r.get("answers") or {}).get(qid, "(none)"))
                if r["status"] == "answered"
                else f"({r['status']})"
                for r in records
            ]
            lines.append(
                f"| {qid} | {_cell(key.question.text)} | {_cell(_key_value(key))} | "
                f"{correct} of {len(records)} | {'yes' if passed else 'NO'} | {'; '.join(given)} |"
            )
        lines.append("")
    return "\n".join(lines)
