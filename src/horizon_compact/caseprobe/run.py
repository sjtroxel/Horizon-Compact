"""The container's recognition probe for one case, one model, one probe set (protocol §12.8).

``hc case probe`` runs this in the Fargate task. In order, every refusal before the first call: the runner
is a container (an official result carries an image digest); the model is one the experiment names (role
``main`` or ``second_family``) on a route the container can reach; ``case.lock`` for the label is read from
the image and is for this probe set; the content read from storage hashes to it (the image must carry the
record, so the commit is pushed and deployed first); the worst case fits the cap. Then three calls, each the
dossier as the system text and §12.8's message word for word, no tool, no sampling field.

**A reply is the measurement, so a model reply is never retried** (a retry would raise the pass rate by hiding
a failure); an API error is retried with backoff, kept under ``errors/``, and too many stop the run. A call
that has a record is skipped, never repeated, so a re-run resumes. Each answer is one write-once object with
the usual provenance; whether it names the company is judged later, by ``probe-verdict``, not here.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import random
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from horizon_compact.caseprobe.layout import (
    CONTENT_FILES,
    PROBE_CALLS,
    PROBE_MAX_TOKENS,
    PROBE_MESSAGE,
    PROBE_ROLES,
    call_key,
    content_key,
    error_key,
    probes_prefix,
)
from horizon_compact.model_config import ModelConfig
from horizon_compact.protocol.cases import (
    CaseContent,
    CaseError,
    case_path,
    check_case_content,
    read_case,
)
from horizon_compact.providers.base import ModelRoute, TextProvider, TextRequest, text_prompt_sha256
from horizon_compact.smoke.record import serialize_safely
from horizon_compact.sweep.classify import classify_error
from horizon_compact.sweep.identity import RunnerIdentity
from horizon_compact.sweep.pacing import Pacer, backoff_seconds
from horizon_compact.sweep.spend import (
    SpendCap,
    attempt_cost_usd,
    estimate_input_tokens_text,
    worst_case_attempt_usd,
)
from horizon_compact.sweep.store import Store

RECORD_VERSION = 1
MAX_CONSECUTIVE_API_ERRORS = 10
CLEAN_STOPS = frozenset({"complete", "cap_reached", "stop_requested"})
_NORMAL_STOPS = frozenset({"end_turn", "tool_use"})
ROUTES = ("anthropic", "openrouter")


class ProbeRefused(Exception):
    """The probe cannot start, and no call was made. The message names a rule, never a name or a figure."""


def check_probe_model(key: str, config: ModelConfig) -> None:
    """Only an official model, on a route the container reaches, and (OpenRouter) pinned to one provider so
    OpenRouter cannot serve the call from another backend."""
    if config.role not in PROBE_ROLES:
        raise ProbeRefused(
            f"{key} has role {config.role!r}: a case probe asks only the experiment's own models "
            f"({', '.join(PROBE_ROLES)})"
        )
    if config.route not in ROUTES:
        raise ProbeRefused(f"{key} is on route {config.route!r}: the case probe reaches {ROUTES}")
    if config.route == "openrouter" and not config.openrouter_provider:
        raise ProbeRefused(f"{key} is an OpenRouter model with no pinned provider")


def probe_route(key: str, config: ModelConfig) -> ModelRoute:
    if config.route == "openrouter":
        return ModelRoute(
            key,
            config.model_id,
            "openrouter",
            invoke_id=config.model_id,
            pinned_provider=config.openrouter_provider,
            reasoning_effort=config.reasoning_effort,
        )
    return ModelRoute(
        key,
        config.model_id,
        "anthropic",
        invoke_id=config.model_id,
        thinking_off=config.thinking == "off",
    )


@dataclass(frozen=True)
class ProbeResult:
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


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_content(store: Store, label: str, probe_set: int) -> CaseContent:
    """The three files as stored, bytes as written."""
    parts: dict[str, bytes] = {}
    for name in CONTENT_FILES:
        text = store.get(content_key(label, probe_set, name))
        if text is None:
            raise ProbeRefused(
                f"{name} is not stored for set {probe_set}: run `hc case upload` first"
            )
        parts[name] = text.encode("utf-8")
    return CaseContent(parts["dossier.toml"], parts["scenario.toml"], parts["rubric.toml"])


def _status(raw_stop: str | None, tool_calls: int, texts: list[str]) -> str:
    if raw_stop == "max_tokens":
        return "truncated"
    if raw_stop == "content_filtered":
        return "content_filtered"
    if raw_stop not in _NORMAL_STOPS:
        return "unexpected_stop"
    if tool_calls:
        return "unexpected_tool_call"  # no tool was offered: the provider's fault, not the model's
    return "replied" if any(t.strip() for t in texts) else "no_text"


def probe_worst_case_usd(system: str, config: ModelConfig) -> float:
    """The most one call can cost: the dossier at full price and the whole output allowance."""
    tokens = estimate_input_tokens_text(system, PROBE_MESSAGE)
    return worst_case_attempt_usd(tokens, PROBE_MAX_TOKENS, config.prices)


def run_case_probe(
    *,
    label: str,
    probe_set: int,
    model_key: str,
    config: ModelConfig,
    pace_fraction: float,
    repo_root: Path,
    provider: TextProvider,
    store: Store,
    identity: RunnerIdentity,
    account_id: str,
    cap_usd: float,
    harness_version: str,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    rng: random.Random | None = None,
    should_stop: Callable[[], bool] = lambda: False,
    progress: Callable[[str], None] = lambda line: None,
) -> ProbeResult:
    if not identity.in_container:
        raise ProbeRefused(
            "a case probe runs in the container only: an official result carries an image digest"
        )
    check_probe_model(model_key, config)
    try:
        record = read_case(repo_root, label)
    except CaseError as exc:
        raise ProbeRefused(f"{exc} (the image must carry the case record)") from exc
    if record.probe_set != probe_set:
        raise ProbeRefused(
            f"{case_path(label)} in the image is for probe set {record.probe_set}, not {probe_set}"
        )
    content = load_content(store, label, probe_set)
    mismatched = check_case_content(record, content)
    if mismatched:
        raise ProbeRefused("; ".join(mismatched))
    lock_text = (repo_root / case_path(label)).read_bytes()
    system = content.dossier.decode("utf-8")
    worst = probe_worst_case_usd(system, config)
    bound = round(PROBE_CALLS * worst, 4)
    if bound > cap_usd:
        raise ProbeRefused(
            f"the worst case for {PROBE_CALLS} probe calls is ${bound:.2f}, above the cap of ${cap_usd:.2f}"
        )

    prefix = probes_prefix(label, probe_set)
    existing = set(store.list_keys(f"{prefix}{model_key}/"))
    errors_so_far: Counter[int] = Counter()
    spent = 0.0
    for key in sorted(existing):
        text = store.get(key)
        if text is not None:
            spent += float(json.loads(text).get("cost_usd", 0.0))
        if "/errors/" in key:
            errors_so_far[int(key.rsplit("/call-", 1)[1].split("-", 1)[0])] += 1
    cap = SpendCap(cap_usd, round(spent, 6))
    pacer = Pacer(config.requests_per_minute, pace_fraction, monotonic, sleep)
    rng = rng or random.Random()
    request = TextRequest(
        route=probe_route(model_key, config),
        system=system,
        user=PROBE_MESSAGE,
        max_tokens=PROBE_MAX_TOKENS,
    )
    done_before = sum(
        1 for n in range(1, PROBE_CALLS + 1) if call_key(label, probe_set, model_key, n) in existing
    )
    calls = 0
    cost_now = 0.0
    done_now = 0
    api_errors = 0

    def finish(stopped: str) -> ProbeResult:
        return ProbeResult(
            stopped, PROBE_CALLS, done_before, done_now, calls, round(cost_now, 6), cap.spent_usd
        )

    for n in range(1, PROBE_CALLS + 1):
        record_key = call_key(label, probe_set, model_key, n)
        if record_key in existing:
            continue
        api_streak = 0
        while True:
            if should_stop():
                return finish("stop_requested")
            if not cap.allows(worst):
                return finish("cap_reached")
            pacer.wait()
            raw = provider.decide_text(request)
            cost = attempt_cost_usd(raw.usage, config.prices)
            cap.record(cost)
            calls += 1
            cost_now += cost
            prov = raw.provenance
            fields: dict[str, Any] = {
                "record_version": RECORD_VERSION,
                "kind": "case-probe",
                "label": label,
                "probe_set": probe_set,
                "call": n,
                "model_key": model_key,
                "case_lock_sha256": _sha256(lock_text),
                "dossier_sha256": _sha256(content.dossier),
                "git_sha": identity.git_sha,
                "git_dirty": identity.git_dirty,
                "image_digest": identity.image_digest,
                "image": identity.image,
                "runner": identity.runner,
                "task_arn": identity.task_arn,
                "harness_version": harness_version,
                "provider": prov.provider,
                "api": prov.api,
                "model_id": prov.model_id,
                "route_kind": prov.route_kind,
                "invoke_id": prov.invoke_id,
                "region": prov.region,
                "provider_details": dict(prov.details),
                "effort": prov.effort,
                "thinking": prov.thinking,
                "temperature": prov.temperature,
                "max_tokens": prov.max_tokens,
                "prompt_sha256": text_prompt_sha256(request),
                "started_at": prov.started_at,
                "finished_at": prov.finished_at,
                "latency_ms": prov.latency_ms,
                "usage": dataclasses.asdict(raw.usage),
                "cost_usd": cost,
                "request": json.loads(json.dumps(provider.text_request_body(request), default=str)),
            }
            if raw.status == "api_error":
                errors_so_far[n] += 1
                error_record = {**fields, "kind": "case-probe-api-error", "error": raw.error}
                if not store.put_new(
                    error_key(label, probe_set, model_key, n, errors_so_far[n]),
                    serialize_safely(error_record, account_id),
                ):
                    return finish("write_conflict")
                outcome = classify_error(raw)
                progress(f"call {n}/{PROBE_CALLS}: api_error {outcome.detail}  (${cost_now:.4f})")
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
        status = _status(raw.stop_reason, raw.tool_call_count, raw.text_blocks)
        answer = {
            **fields,
            "raw_response": json.loads(json.dumps(raw.raw_response, default=str)),
            "stop_reason": raw.stop_reason,
            "reasoning_block_count": raw.reasoning_block_count,
            "text_blocks": raw.text_blocks,
            "answer": "\n".join(t for t in raw.text_blocks if t.strip()).strip(),
            "status": status,
        }
        if not store.put_new(record_key, serialize_safely(answer, account_id)):
            return finish("write_conflict")
        done_now += 1
        progress(f"call {n}/{PROBE_CALLS}: {status}  (${cost_now:.4f})")
    return finish("complete")
