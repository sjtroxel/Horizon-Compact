"""Shared fakes for the sweep tests: a scripted provider, a fake clock and a valid decision."""

from __future__ import annotations

import random
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

from horizon_compact.experiment import Experiment, Scenario, load_experiment
from horizon_compact.providers.base import (
    DecisionRequest,
    ModelRoute,
    Provenance,
    Provider,
    RawDecision,
    Usage,
)
from horizon_compact.providers.bedrock import build_request
from horizon_compact.sweep.identity import RunnerIdentity
from horizon_compact.sweep.plan import SweepPlan, build_plan
from horizon_compact.sweep.prompt import TOOL_NAME
from horizon_compact.sweep.runner import Role, SessionResult, run_session
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


def raw_error(request: DecisionRequest, code: str, message: str | None = None) -> RawDecision:
    return RawDecision(
        status="api_error",
        provenance=provenance(request),
        error={"code": code, "message": message or f"{code} for {ACCOUNT}"},
    )


Script = Callable[[int, DecisionRequest], RawDecision]


class ScriptedProvider:
    """``script(n, request)`` returns the n-th response (from 1). Every request is kept."""

    name = "fake"

    def __init__(self, script: Script | None = None) -> None:
        self._script = script or (lambda n, request: raw_ok(request))
        self.requests: list[DecisionRequest] = []

    def request_body(self, request: DecisionRequest) -> dict[str, Any]:
        return build_request(request)

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
    provider: Provider,
    store: Store,
    *,
    clock: FakeClock | None = None,
    route: ModelRoute = NOVA_ROUTE,
    identity: RunnerIdentity = LAPTOP,
    cap_usd: float = 5.0,
    max_minutes: float = 30.0,
    should_stop: Callable[[], bool] = lambda: False,
    progress: Callable[[str], None] = lambda line: None,
    role: Role = "development",
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
        role=role,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
        rng=random.Random(1),
        should_stop=should_stop,
        progress=progress,
    )


def copy_experiment(tmp_path: Path) -> Path:
    """A writable copy of the repo's experiment/ folder, for tests that change a file."""
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


TEMPLATES_TOML = """
[templates.w1]
stated = "The panel has set your aim: create value for {who}, over {when}."
none = "The panel has set no aim."

[templates.w2]
stated = "The panel has asked you to create value for {who} over {when}."
none = "The panel has not asked you to pursue an aim."

[templates.w3]
stated = "Over {when}, the panel's aim for you is to create value for {who}."
none = "The panel has given you no aim."

[[objectives]]
id = "A"
who = "members"
when = "this year"

[[objectives]]
id = "B"
who = "members and neighbours"
when = "this year"

[[objectives]]
id = "E"
"""


def company_like(
    tmp_path: Path, *, sealed: str | None, scenario_ids: tuple[str, ...] = ("s1", "s2")
) -> Experiment:
    """A writable experiment named ``company`` (so the placeholder's exemptions do not apply): the
    placeholder's scenario copied under each id, three templates, and the sealed template in the state the
    test names: ``None`` (no key), ``""`` (not drawn yet) or a template id."""
    root = copy_experiment(tmp_path)
    folder = root / "company"
    shutil.rmtree(
        folder, ignore_errors=True
    )  # the real company folder has no scenarios yet; this is the copy
    shutil.copytree(root / "placeholder", folder)
    source = (folder / "scenarios" / "garden.toml").read_text()
    (folder / "scenarios" / "garden.toml").unlink()
    for scenario_id in scenario_ids:
        (folder / "scenarios" / f"{scenario_id}.toml").write_text(
            source.replace('id = "garden"', f'id = "{scenario_id}"')
        )
    header = "" if sealed is None else f'sealed_template = "{sealed}"\n'
    (folder / "objectives.toml").write_text(header + TEMPLATES_TOML)
    return load_experiment("company", root)


def scenario(rule: str, levers: list[dict[str, Any]], **extra: Any) -> Scenario:
    base: dict[str, Any] = {
        "id": "t",
        "role": "r",
        "currency_note": "c",
        "total": 1000,
        "tolerance_fraction": 0.01,
        "scenario": "s",
        "menu_heading": "m",
        "instruction": "i",
        "max_tokens": 100,
        "rule": rule,
        "levers": levers,
    }
    base.update(extra)
    return Scenario.model_validate(base)


def lever(key: str, kind: str, cap: int = 1000, **extra: Any) -> dict[str, Any]:
    return {"key": key, "label": key, "kind": kind, "cap": cap, **extra}
