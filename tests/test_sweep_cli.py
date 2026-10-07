"""The ``hc sweep`` command line: what works offline and what is refused before AWS is touched."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import boto3
import pytest

from horizon_compact import cli
from horizon_compact.sweep.plan import SweepRefusal
from horizon_compact.sweep.runner import run_session
from sweep_helpers import FARGATE, LAPTOP, FakeClock, ScriptedProvider, company_like

PLAN_ARGS = [
    "--experiment",
    "placeholder",
    "--model",
    "sonnet-4-6",
    "--repeats",
    "3",
    "--seed",
    "20261005",
    "--label",
    "skeleton",
]


@pytest.fixture(autouse=True)
def _no_boto3_session(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every refusal in this file must happen before a session exists."""

    def explode(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("a boto3 session was created")

    monkeypatch.setattr(boto3, "Session", explode)


def test_plan_is_offline_and_shows_the_runs_the_pacing_and_the_bound(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli.main(["sweep", "plan", *PLAN_ARGS]) == 0
    out = capsys.readouterr().out
    assert "sweep_id:        skeleton-sonnet-4-6-" in out
    assert "runs:            15 (1 scenarios x 5 objectives x 1 templates x 3 repeats)" in out
    assert "one call start every 7.5s" in out
    assert "for the sweep (3 attempts per run)" in out
    assert out.count("repeat ") == 15


def test_plan_can_show_every_rendered_prompt(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["sweep", "plan", *PLAN_ARGS, "--show-prompts"]) == 0
    out = capsys.readouterr().out
    assert out.count("--- system (identical on every run) ---") == 1
    assert out.count("--- user, run ") == 15
    assert out.count("The lines for this season, with each one's maximum:") == 15


def test_plan_names_the_known_models_when_given_an_unknown_one(
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = [
        "--experiment",
        "placeholder",
        "--model",
        "nope",
        "--repeats",
        "1",
        "--seed",
        "1",
        "--label",
        "t",
    ]
    assert cli.main(["sweep", "plan", *args]) == 2
    assert "nova-lite" in capsys.readouterr().err


def test_an_official_run_is_refused_with_the_reason(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["sweep", "run", *PLAN_ARGS, "--profile", "p", "--official"]) == 2
    assert (
        "official sweeps are refused: no committed protocol (prereg-v1 does not exist)"
        in capsys.readouterr().err
    )


def test_an_official_launch_is_refused_before_any_aws_call(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli.main(["sweep", "launch", *PLAN_ARGS, "--profile", "p", "--official"]) == 2
    assert "no committed protocol" in capsys.readouterr().err


def test_a_cap_above_five_dollars_needs_allow_over_cap(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["sweep", "launch", *PLAN_ARGS, "--profile", "p", "--cap-usd", "6"]) == 2
    err = capsys.readouterr().err
    assert "--allow-over-cap" in err


def test_a_launch_whose_worst_case_passes_the_cap_is_refused_before_any_aws_call(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli.main(["sweep", "launch", *PLAN_ARGS, "--profile", "p", "--cap-usd", "0.5"]) == 2
    assert "above the cap of $0.50" in capsys.readouterr().err


def test_a_laptop_run_needs_a_profile_and_has_no_default(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli.main(["sweep", "run", *PLAN_ARGS]) == 2
    assert "--profile is required" in capsys.readouterr().err


def test_a_route_mismatch_is_refused_before_a_session(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("HC_SONNET_ROUTE", "geo_profile")
    assert cli.main(["sweep", "run", *PLAN_ARGS, "--profile", "p"]) == 2
    assert "HC_SONNET_ROUTE" in capsys.readouterr().err


def test_stop_and_status_need_their_arguments() -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["sweep", "stop"])
    assert exc.value.code == 2


# --- Phase 2.5: the selection flags and the refusals reach the command line -----------------------


def _company_args(tmp_path: Path, sealed: str, *extra: str) -> list[str]:
    exp = company_like(tmp_path, sealed=sealed)
    return [
        "--experiment", "company",
        "--experiment-dir", str(exp.root),
        "--model", "nova-lite",
        "--repeats", "1",
        "--seed", "1",
        "--label", "t",
        *extra,
    ]  # fmt: skip


def test_plan_takes_scenario_and_template_flags(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = _company_args(tmp_path, "w3", "--scenario", "s1", "--template", "w1", "--template", "w2")
    assert cli.main(["sweep", "plan", *args]) == 0
    out = capsys.readouterr().out
    assert "runs:            6 (1 scenarios x 3 objectives x 2 templates x 1 repeats)" in out
    assert out.count("repeat ") == 6


def test_the_sealed_template_is_refused_at_the_command_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = _company_args(tmp_path, "w2", "--template", "w2")
    assert cli.main(["sweep", "plan", *args]) == 2
    assert "sealed template (w2) is never part of a decision prompt" in capsys.readouterr().err


def test_an_undrawn_template_blocks_every_decision_plan(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["sweep", "plan", *_company_args(tmp_path, "")]) == 2
    assert "sealed template is not drawn yet" in capsys.readouterr().err


def test_real_content_on_the_main_model_is_refused_at_the_command_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = _company_args(tmp_path, "w3", "--template", "w1")
    args[args.index("nova-lite")] = "sonnet-4-6"
    assert cli.main(["sweep", "plan", *args]) == 2
    assert "sonnet-4-6 is not the development model" in capsys.readouterr().err


# --- Phase 2.5 step 4: a local model needs no AWS at all ------------------------------------------


@pytest.fixture
def laptop_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The repo's git answers, with the records folder moved into tmp: a test never writes to scratch/."""

    def fake_git(*args: str) -> str:
        return str(tmp_path) if "--show-toplevel" in args else ("abc1234" if "HEAD" in args else "")

    monkeypatch.setattr(cli, "_git", fake_git)
    return tmp_path


@pytest.fixture
def fake_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run sessions on a clock that only pretends to wait, so spacing between calls costs no real time."""

    def fast(**kwargs: Any) -> Any:
        clock = FakeClock()
        return run_session(**kwargs, monotonic=clock.monotonic, sleep=clock.sleep)

    monkeypatch.setattr(cli, "run_session", fast)


LOCAL_ARGS = [
    "--experiment", "placeholder",
    "--model", "qwen-local",
    "--repeats", "1",
    "--seed", "5",
    "--label", "local",
]  # fmt: skip


def test_a_local_run_makes_its_records_without_any_aws_session_or_profile(
    laptop_repo: Path,
    fake_clock: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The autouse fixture makes ``boto3.Session`` raise: any AWS path in this run would fail the test."""
    built: list[tuple[str, int]] = []

    def fake_provider(url: str, num_ctx: int) -> ScriptedProvider:
        built.append((url, num_ctx))
        return ScriptedProvider()

    monkeypatch.setattr(cli, "OllamaProvider", fake_provider)
    assert cli.main(["sweep", "run", *LOCAL_ARGS, "--store", "local"]) == 0  # no --profile
    out = capsys.readouterr().out
    assert built == [("http://localhost:11434", 16384)]
    assert "stopped:         complete" in out
    assert "runs finished:   5 of 5" in out
    assert "$0.0000" in out
    assert list(
        (laptop_repo / "scratch" / "runs" / "development" / "placeholder").rglob("final.json")
    )


def test_the_ollama_address_can_be_set_by_the_environment(
    laptop_repo: Path, fake_clock: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    built: list[tuple[str, int]] = []
    monkeypatch.setenv("HC_OLLAMA_URL", "http://127.0.0.1:5555")

    def fake_provider(url: str, num_ctx: int) -> ScriptedProvider:
        built.append((url, num_ctx))
        return ScriptedProvider()

    monkeypatch.setattr(cli, "OllamaProvider", fake_provider)
    assert cli.main(["sweep", "run", *LOCAL_ARGS, "--store", "local"]) == 0
    assert built == [("http://127.0.0.1:5555", 16384)]


def test_a_local_model_refuses_the_s3_store(
    laptop_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["sweep", "run", *LOCAL_ARGS, "--store", "s3", "--bucket", "b"]) == 2
    assert "a local model's runs stay on this laptop: use --store local" in capsys.readouterr().err


def test_a_local_model_refuses_the_container() -> None:
    args = cli.build_parser().parse_args(["sweep", "run", *LOCAL_ARGS, "--store", "local"])
    with pytest.raises(SweepRefusal, match="runs on the laptop only"):
        cli._check_local(args, FARGATE)
    cli._check_local(args, LAPTOP)  # the laptop is fine


def test_a_local_model_cannot_be_launched_as_a_fargate_task(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli.main(["sweep", "launch", *LOCAL_ARGS, "--profile", "p"]) == 2
    assert (
        "is a local model: it runs on this laptop, so use `hc sweep run`" in capsys.readouterr().err
    )


def test_status_of_a_local_store_needs_no_aws_session(
    laptop_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = ["sweep", "status", *LOCAL_ARGS, "--store", "local", "--sweep-id", "nothing-yet"]
    assert cli.main(args) == 0
    assert "no manifest for nothing-yet" in capsys.readouterr().out


def test_the_plan_for_a_local_model_prints_with_zero_cost(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli.main(["sweep", "plan", *LOCAL_ARGS]) == 0
    out = capsys.readouterr().out
    assert "runs:            5 (1 scenarios x 5 objectives x 1 templates x 1 repeats)" in out
    assert "one call start every 2.5s" in out
