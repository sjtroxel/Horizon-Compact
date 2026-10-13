"""The record checks (Phase 4 runs half section 5.3), on a fake store: each check passes on a well-formed
world and fails, naming the sweep, on a fixture built to break it. Canary values sit in every field the pass
must not read, and the test looks for them in the report. No model call, no AWS call. Every id is made up."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from fake_anthropic import KEY as ANTHROPIC_KEY
from fake_anthropic import FakeAnthropic
from fake_openrouter import KEY as OPENROUTER_KEY
from fake_openrouter import FakeOpenRouter, completion
from horizon_compact import cli
from horizon_compact.experiment import load_experiment
from horizon_compact.protocol import recordcheck
from horizon_compact.protocol.lock import CheckReport, Lock, lock_path, read_lock
from horizon_compact.protocol.recordcheck import format_report, recorded_thinking, run_checks
from horizon_compact.providers.anthropic import AnthropicProvider
from horizon_compact.providers.base import (
    THINKING_STUDY_EFFORT_NOTE,
    THINKING_STUDY_MAX_TOKENS,
    THINKING_STUDY_THINKING_NOTE,
    DecisionRequest,
    ModelRoute,
    ToolSpec,
)
from horizon_compact.providers.openrouter import OpenRouterProvider
from horizon_compact.sweep.store import LocalStore

ROOT = Path(__file__).resolve().parents[1]
LOCK = read_lock(lock_path(ROOT))
CANARY = "CANARY-DO-NOT-READ-4417"
UNREAD = ("validation", "tool_calls", "text_blocks", "raw_response", "parsed_decision")
AFTER = "2026-10-14T09:00:00+00:00"
DIGEST = "sha256:" + "ab" * 32
OTHER_DIGEST = "sha256:" + "cd" * 32
HAIKU, GPT = "haiku-5-5", "gpt-oss-openrouter"
SEALED = LOCK.content.sealed_template
# What each provider writes in a call's record, word for word, for the lock's setting. Deliberately literal
# (not computed from the lock), so the fixture holds what the real records will hold.
RECORDED = {HAIKU: "off: thinking {type: disabled} sent", GPT: "reasoning effort medium sent"}


def rid(n: int) -> str:
    return f"r-{n:012x}"


class World:
    """A small bucket: for each model a pilot and a grid, for Haiku also the sub-study and the probe."""

    def __init__(self, tmp_path: Path) -> None:
        self.store = LocalStore(tmp_path)
        self.counter = 0

    def sweep(
        self,
        role: str,
        sweep_id: str,
        label: str,
        model: str,
        *,
        runs: int = 2,
        templates: tuple[str, ...] = ("w1", "w3"),
        finished: int | None = None,
        awareness: bool = False,
        **attempt: Any,
    ) -> list[str]:
        folder = "awareness/" if awareness else ""
        prefix = f"{role}/company/{folder}{sweep_id}/"
        ids = [rid(self.counter + i) for i in range(runs)]
        self.counter += runs
        manifest = {
            "sweep_id": sweep_id, "label": label, "model_key": model, "experiment": "company",
            "content_hash": attempt.pop("manifest_content_hash", LOCK.content.content_hash),
            "templates": list(templates), "scenarios": ["s1"], "runs": [{"run_id": r} for r in ids],
        }  # fmt: skip
        self.store.put_new(f"{prefix}manifest.json", json.dumps(manifest))
        locked = LOCK.models[model]
        base: dict[str, Any] = {
            "label": role, "sweep_id": sweep_id, "scenario_id": "s1", "wording_variant_id": templates[0],
            "started_at": AFTER, "runner": "fargate", "image_digest": DIGEST, "git_dirty": False,
            "thinking": RECORDED[model], "effort": "not set", "max_tokens": 3072, "cost_usd": 0.001,
            "content_hash": LOCK.content.content_hash, "model_key": model, "status": "valid",
            "provider_details": {"served_by": "DeepInfra" if locked.openrouter_provider else "x"},
            "objective_id": CANARY, "usage": {"output_tokens": 9}, **dict.fromkeys(UNREAD, CANARY),
        }  # fmt: skip
        base.update(attempt)
        done = runs if finished is None else finished
        for i, run in enumerate(ids):
            if awareness:
                self.store.put_new(f"{prefix}runs/{run}.json", json.dumps({**base, "run_id": run}))
                continue
            self.store.put_new(
                f"{prefix}runs/{run}/attempt-1.json",
                json.dumps({**base, "run_id": run, "attempt": 1}),
            )
            if i < done:
                self.store.put_new(f"{prefix}runs/{run}/final.json", json.dumps({"status": CANARY}))
        self.store.put_new(
            f"{prefix}sessions/20261014T090000Z-fargate.json",
            json.dumps(
                {
                    "runner": "fargate",
                    "image_digest": DIGEST,
                    "started_at": AFTER,
                    "stopped": "complete",
                }
            ),
        )
        return ids


def good_world(tmp_path: Path) -> World:
    world = World(tmp_path)
    for model in (HAIKU, GPT):
        world.sweep("pilot", f"pilot-{model}-1", "pilot", model)
        world.sweep(
            "official", f"grid-{model}-1", "grid", model, templates=("w1", SEALED or "w2", "w3")
        )
    study: dict[str, Any] = {
        "thinking": THINKING_STUDY_THINKING_NOTE, "effort": THINKING_STUDY_EFFORT_NOTE,
        "max_tokens": THINKING_STUDY_MAX_TOKENS, "wording_variant_id": SEALED,
    }  # fmt: skip
    world.sweep(
        "official", "thinking-haiku-5-5-1", "thinking", HAIKU, templates=(SEALED or "w2",), **study
    )
    world.sweep("official", "pr-haiku", "awareness", HAIKU, awareness=True)
    return world


def report(world: World, frozen: list[str] | None = None) -> recordcheck.RecordReport:
    return run_checks(world.store, LOCK, frozen or [])


def verdicts(result: recordcheck.RecordReport) -> dict[str, bool]:
    return {check.name: check.ok for check in result.checks}


def lines_of(result: recordcheck.RecordReport, name: str) -> str:
    return "\n".join(next(c for c in result.checks if c.name == name).lines)


def text_of(result: recordcheck.RecordReport) -> str:
    return format_report(
        result, protocol=LOCK.protocol, tree="abc123", made_at="2026-10-15T00:00:00Z"
    )


def test_a_well_formed_world_passes_every_check_and_the_report_holds_no_decision_field(
    tmp_path: Path,
) -> None:
    result = report(good_world(tmp_path))
    assert all(verdicts(result).values()), [c for c in result.checks if not c.ok]
    assert [c.name for c in result.checks] == [
        "content", "model", "labels", "container", "image", "request", "complete", "sealed first",
        "after the tag", "frozen files",
    ]  # fmt: skip
    text = text_of(result)
    assert CANARY not in text
    assert "every check passes" in text
    assert "`grid-haiku-5-5-1`" in text and "`pr-haiku`" in text
    assert len(result.sweeps) == 6


def break_content(w: World) -> None:
    w.sweep("official", "grid-bad-1", "grid", "haiku-5-5", manifest_content_hash="0" * 64)


@pytest.mark.parametrize(
    ("check", "needle", "mutate"),
    [
        ("content", "grid-bad-1", break_content),
        ("labels", "grid2", lambda w: w.sweep("official", "grid2-x", "grid2", HAIKU)),
        ("labels", "labeled 'grid' on haiku-5-5", lambda w: w.sweep("official", "grid-two", "grid", HAIKU)),
        ("labels", "pilot-bad", lambda w: w.sweep("pilot", "pilot-bad", "grid", GPT)),
        ("container", "not run on fargate", lambda w: w.sweep("official", "thinking-x", "thinking", GPT, runner="laptop")),
        ("container", "no image digest", lambda w: w.sweep("official", "grid-nd", "thinking", GPT, image_digest=None)),
        ("container", "clean git tree", lambda w: w.sweep("pilot", "pilot-dirty", "pilot", GPT, git_dirty=True)),
        ("request", "whose thinking is", lambda w: w.sweep("official", "grid-t", "grid", HAIKU, thinking="not set")),
        ("request", "whose effort is", lambda w: w.sweep("official", "thinking-e", "thinking", HAIKU, thinking=THINKING_STUDY_THINKING_NOTE, effort="medium", max_tokens=THINKING_STUDY_MAX_TOKENS)),
        ("request", "max_tokens is 3072", lambda w: w.sweep("official", "thinking-m", "thinking", HAIKU, thinking=THINKING_STUDY_THINKING_NOTE, effort=THINKING_STUDY_EFFORT_NOTE)),
        ("request", "served by 'Other Host'", lambda w: w.sweep("official", "grid-s", "grid", GPT, provider_details={"served_by": "Other Host"})),
        ("complete", "1 of 3 runs have no final", lambda w: w.sweep("official", "grid-c", "grid", GPT, runs=3, finished=2)),
        ("sealed first", "pilot-s", lambda w: w.sweep("pilot", "pilot-s", "pilot", GPT, templates=("w1", SEALED or "w2"))),
        ("after the tag", "began before", lambda w: w.sweep("official", "grid-early", "grid", GPT, started_at="2026-10-13T06:00:00+00:00")),
    ],
)  # fmt: skip
def test_each_check_fails_on_a_fixture_built_to_break_it_and_names_the_sweep(
    tmp_path: Path, check: str, needle: str, mutate: Callable[[World], None]
) -> None:
    world = good_world(tmp_path)
    mutate(world)
    result = report(world)
    assert verdicts(result)[check] is False, lines_of(result, check)
    assert needle in lines_of(result, check)
    assert "FAIL" in text_of(result) and CANARY not in text_of(result)


def test_a_model_outside_the_lock_fails_the_model_check(tmp_path: Path) -> None:
    world = good_world(tmp_path)
    world.sweep("official", "grid-z", "grid", HAIKU)  # build a sweep, then say it ran another model
    key = "official/company/grid-z/manifest.json"
    manifest = json.loads(world.store.get(key) or "{}")
    (tmp_path / key).write_text(json.dumps({**manifest, "model_key": "nova-lite"}))
    result = report(world)
    assert verdicts(result)["model"] is False and "nova-lite" in lines_of(result, "model")


def test_the_earliest_sealed_call_in_a_development_sweep_fails_sealed_first(tmp_path: Path) -> None:
    world = good_world(tmp_path)
    world.sweep(
        "development",
        "dev-1",
        "t",
        HAIKU,
        templates=("w1",),
        wording_variant_id=SEALED,
        started_at="2026-10-01T00:00:00+00:00",
    )
    result = report(world)
    assert verdicts(result)["sealed first"] is False
    assert "development dev-1" in lines_of(result, "sealed first")


def test_a_development_sweeps_status_and_other_fields_are_not_even_kept(tmp_path: Path) -> None:
    world = good_world(tmp_path)
    world.sweep(
        "development", "dev-2", "t", HAIKU, templates=("w1",), status=CANARY, runner="elsewhere"
    )
    result = report(world)
    assert all(
        verdicts(result).values()
    )  # a development sweep is held to nothing but the sealed template
    dev = next(s for s in result.sweeps if s.sweep_id == "dev-2")
    assert {a.status for a in dev.attempts} == {""} and not dev.sessions


def test_more_than_one_image_digest_in_a_sweep_is_reported_with_its_sessions_and_does_not_fail(
    tmp_path: Path,
) -> None:
    world = good_world(tmp_path)
    prefix = "official/company/grid-gpt-oss-openrouter-1/"
    world.store.put_new(
        f"{prefix}sessions/20261015T090000Z-fargate.json",
        json.dumps(
            {
                "runner": "fargate",
                "image_digest": OTHER_DIGEST,
                "started_at": "2026-10-15T09:00:00+00:00",
                "stopped": "complete",
            }
        ),
    )
    result = report(world)
    assert all(verdicts(result).values())
    image = lines_of(result, "image")
    assert (
        "MORE THAN ONE DIGEST in official grid-gpt-oss-openrouter-1" in image
        and OTHER_DIGEST in image
    )
    assert "| image | reported |" in text_of(result)


def test_a_frozen_file_failure_from_hc_protocol_check_fails_the_last_check(tmp_path: Path) -> None:
    result = report(good_world(tmp_path), frozen=["instrument differs: sweep/prompt.py"])
    assert verdicts(result)["frozen files"] is False
    assert "sweep/prompt.py" in lines_of(result, "frozen files")


def test_the_run_counts_are_per_sweep_and_cover_status_sessions_and_cost(tmp_path: Path) -> None:
    text = text_of(report(good_world(tmp_path)))
    row = next(line for line in text.splitlines() if "`grid-haiku-5-5-1`" in line)
    assert (
        row
        == "| official | `grid-haiku-5-5-1` | grid | haiku-5-5 | 2 | 2 | 2 | {'valid': 2} | 1 | 0.0020 |"
    )
    assert "development" not in text.split("## Run counts")[1]


class ReadOnly(LocalStore):
    def put_new(self, key: str, text: str) -> bool:
        raise AssertionError("the record checks wrote to the store")


def test_the_checks_only_read(tmp_path: Path) -> None:
    world = good_world(tmp_path)
    result = run_checks(ReadOnly(tmp_path), LOCK, [])
    assert all(c.ok for c in result.checks)
    assert world.counter > 0


def test_the_module_never_looks_up_a_decision_field_by_name() -> None:
    source = Path(recordcheck.__file__).read_text(encoding="utf-8")
    code = re.sub(r'""".*?"""', "", source, flags=re.S)
    for field in (*UNREAD, "objective_id", "amounts", "choice", "memo", "usage", "stop_reason"):
        assert f'"{field}"' not in code and f"'{field}'" not in code, field


def test_the_command_writes_the_evidence_file_and_exits_by_the_verdict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = good_world(tmp_path / "bucket")
    root = tmp_path / "repo"
    lock_file = lock_path(root)
    lock_file.parent.mkdir(parents=True)
    lock_file.write_bytes(lock_path(ROOT).read_bytes())
    monkeypatch.setattr(cli, "_session", lambda args, identity: None)
    monkeypatch.setattr(cli, "_store", lambda args, session: world.store)
    monkeypatch.setattr(cli, "check_lock", lambda r: CheckReport())
    assert cli.main(["protocol", "--root", str(root), "records", "--store", "local"]) == 0
    written = (root / cli.RECORD_CHECKS_FILE).read_text(encoding="utf-8")
    assert "every check passes" in written and CANARY not in written
    assert "pass     content" in capsys.readouterr().out
    monkeypatch.setattr(cli, "check_lock", lambda r: CheckReport(failures=("analysis differs",)))
    assert cli.main(["protocol", "--root", str(root), "records", "--store", "local"]) == 1
    assert "AT LEAST ONE CHECK FAILED" in (root / cli.RECORD_CHECKS_FILE).read_text(
        encoding="utf-8"
    )


def test_the_lock_is_the_real_one() -> None:
    assert isinstance(LOCK, Lock) and set(LOCK.models) == {HAIKU, GPT}


def test_what_the_check_expects_is_what_each_real_provider_records_for_the_lock() -> None:
    """The lock words a setting one way and each provider's record another; the check must expect the
    record's words. Each provider is run on a fake server with its route as ``models.toml`` sets it."""
    config = load_experiment("company").models.models
    tool = ToolSpec("submit_decision", "d", {"type": "object"})
    haiku = config[HAIKU]
    server = FakeAnthropic()
    route = ModelRoute(
        HAIKU, haiku.model_id, "anthropic", haiku.model_id, thinking_off=haiku.thinking == "off"
    )
    sent = AnthropicProvider(ANTHROPIC_KEY, http_client=server.client).decide(
        DecisionRequest(route, "s", "u", tool, 100)
    )
    assert sent.provenance.thinking == recorded_thinking(LOCK.models[HAIKU]) == RECORDED[HAIKU]
    gpt = config[GPT]
    reply = completion()
    reply["provider"] = "DeepInfra"
    with FakeOpenRouter(lambda body: (200, reply)) as fake:
        route = ModelRoute(
            GPT, gpt.model_id, "openrouter", gpt.model_id,
            pinned_provider=gpt.openrouter_provider, reasoning_effort=gpt.reasoning_effort,
        )  # fmt: skip
        sent = OpenRouterProvider(OPENROUTER_KEY, fake.url).decide(
            DecisionRequest(route, "s", "u", tool, 100)
        )
    assert sent.provenance.thinking == recorded_thinking(LOCK.models[GPT]) == RECORDED[GPT]
    assert sent.provenance.details["served_by"] == "DeepInfra"


def test_a_reply_the_pin_refused_is_evidence_not_a_failed_request_check(tmp_path: Path) -> None:
    """An OpenRouter reply from another host is stored as a configuration error and never counts; the
    record check does not hold it against the sweep. A result from another host would fail it."""
    world = good_world(tmp_path)
    world.sweep("official", "pr-gpt", "awareness", GPT, awareness=True)
    world.sweep(
        "official", "grid-gpt-mismatch", "thinking", GPT, status="config_error",
        provider_details={"served_by": "Other Host"},
    )  # fmt: skip
    result = report(world)
    assert "served by" not in lines_of(result, "request")
