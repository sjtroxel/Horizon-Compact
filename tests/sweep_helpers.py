"""Shared fakes for the sweep tests: a scripted provider, a fake clock and a valid decision."""

from __future__ import annotations

import random
from collections.abc import Callable
from pathlib import Path
from typing import Any

from horizon_compact.experiment import Experiment, load_experiment
from horizon_compact.providers.base import (
    DecisionRequest,
    ModelRoute,
    Provenance,
    RawDecision,
    Usage,
)
from horizon_compact.sweep.identity import RunnerIdentity
from horizon_compact.sweep.plan import SweepPlan, build_plan
from horizon_compact.sweep.prompt import TOOL_NAME
from horizon_compact.sweep.runner import SessionResult, run_session
from horizon_compact.sweep.store import Store

ACCOUNT = "123456789012"
LAPTOP = RunnerIdentity("laptop", None, None, None, "abc1234", False)
DIGEST = "sha256:" + "ab" * 32
FARGATE = RunnerIdentity(
    "fargate",
    DIGEST,
    "repo@" + DIGEST,
    f"arn:aws:ecs:us-east-1:{ACCOUNT}:task/c/t",
    "abc1234",
    False,
)
NOVA_ROUTE = ModelRoute("nova-lite", "amazon.nova-lite-v1:0", "in_region", "amazon.nova-lite-v1:0")
SONNET_ROUTE = ModelRoute(
    "sonnet-4-6",
    "anthropic.claude-sonnet-4-6",
    "application_profile",
    f"arn:aws:bedrock:us-east-1:{ACCOUNT}:application-inference-profile/xyz",
    "horizon-compact-sonnet-4-6",
)

VALID_AMOUNTS = {
    "yearly_fund": 1000,
    "plant_sale": 300,
    "raffle": 200,
    "bulbs": 700,
    "herbs": 500,
    "irrigation": 200,
    "mulch_compost": 100,
}


def valid_input(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "amounts": dict(VALID_AMOUNTS),
        "open_day_season": "spring",
        "memo": " ".join(["word"] * 160),
    }
    data.update(overrides)
    return data


def experiment() -> Experiment:
    return load_experiment("placeholder")


def make_plan(
    model_key: str = "nova-lite", repeats: int = 1, seed: int = 7
) -> tuple[Experiment, SweepPlan]:
    exp = experiment()
    return exp, build_plan(exp, model_key=model_key, label="t", repeats=repeats, seed=seed)


def provenance(request: DecisionRequest) -> Provenance:
    return Provenance(
        provider="fake",
        api="converse",
        model_id=request.route.model_id,
        invoke_id=request.route.invoke_id,
        route_kind=request.route.route_kind,
        inference_profile=request.route.inference_profile,
        region="us-east-1",
        thinking="not set",
        effort="not set",
        temperature="not set",
        max_tokens=request.max_tokens,
        prompt_sha256="0" * 64,
        started_at="2026-10-05T12:00:00+00:00",
        finished_at="2026-10-05T12:00:01+00:00",
        latency_ms=1000,
    )


def raw_ok(
    request: DecisionRequest,
    *,
    tool_input: Any = None,
    stop: str = "tool_use",
    calls: list[dict[str, Any]] | None = None,
    text: list[str] | None = None,
    usage: Usage | None = None,
) -> RawDecision:
    if calls is None:
        calls = [{"name": TOOL_NAME, "input": valid_input() if tool_input is None else tool_input}]
    return RawDecision(
        status="ok",
        provenance=provenance(request),
        raw_response={"stopReason": stop, "usage": {}},
        stop_reason=stop,
        tool_calls=calls,
        text_blocks=text or [],
        usage=usage or Usage(input_tokens=2000, output_tokens=400),
    )


def raw_error(request: DecisionRequest, code: str) -> RawDecision:
    return RawDecision(
        status="api_error",
        provenance=provenance(request),
        error={"code": code, "message": f"{code} for {ACCOUNT}"},
    )


Script = Callable[[int, DecisionRequest], RawDecision]


class ScriptedProvider:
    """``script(n, request)`` returns the n-th response (from 1). Every request is kept."""

    name = "fake"

    def __init__(self, script: Script | None = None) -> None:
        self._script = script or (lambda n, request: raw_ok(request))
        self.requests: list[DecisionRequest] = []

    def decide(self, request: DecisionRequest) -> RawDecision:
        self.requests.append(request)
        return self._script(len(self.requests), request)


class FakeClock:
    """``sleep`` advances ``monotonic``, so pacing and backoff run without waiting."""

    def __init__(self) -> None:
        self.t = 1000.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.t += seconds


def session(
    exp: Experiment,
    plan: SweepPlan,
    provider: ScriptedProvider,
    store: Store,
    *,
    clock: FakeClock | None = None,
    route: ModelRoute = NOVA_ROUTE,
    identity: RunnerIdentity = LAPTOP,
    cap_usd: float = 5.0,
    max_minutes: float = 30.0,
    should_stop: Callable[[], bool] = lambda: False,
) -> SessionResult:
    clock = clock or FakeClock()
    return run_session(
        experiment=exp,
        plan=plan,
        route=route,
        provider=provider,
        store=store,
        identity=identity,
        account_id=ACCOUNT,
        cap_usd=cap_usd,
        max_minutes=max_minutes,
        harness_version="0.test",
        monotonic=clock.monotonic,
        sleep=clock.sleep,
        rng=random.Random(1),
        should_stop=should_stop,
    )


def copy_experiment(tmp_path: Path) -> Path:
    """A writable copy of the repo's experiment/ folder, for tests that change a file."""
    import shutil

    src = Path(__file__).resolve().parents[1] / "experiment"
    dest = tmp_path / "experiment"
    shutil.copytree(src, dest)
    return dest


def dummy_request() -> DecisionRequest:
    from horizon_compact.sweep.prompt import build_tool

    exp = experiment()
    return DecisionRequest(
        route=NOVA_ROUTE, system="s", user="u", tool=build_tool(exp.scenario), max_tokens=2048
    )
