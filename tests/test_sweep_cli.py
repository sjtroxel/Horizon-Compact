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
        "official sweep refused: no committed protocol: experiment/protocol/prereg.lock does not exist"
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


# --- Phase 2.5 step 8: an OpenRouter model needs no AWS either, and its key is typed here -----------------

OPENROUTER_ARGS = [
    "--experiment", "placeholder",
    "--model", "gpt-oss-openrouter",
    "--repeats", "1",
    "--seed", "5",
    "--label", "or",
]  # fmt: skip
MADE_UP_KEY = "sk-or-v1-0123456789abcdef0123456789abcdef"


def test_an_openrouter_run_builds_its_provider_with_the_key_from_the_environment(
    laptop_repo: Path,
    fake_clock: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    built: list[str] = []

    def fake_provider(key: str) -> ScriptedProvider:
        built.append(key)
        return ScriptedProvider()

    monkeypatch.setattr(cli, "OpenRouterProvider", fake_provider)
    monkeypatch.setenv("OPENROUTER_API_KEY", MADE_UP_KEY)
    monkeypatch.setattr("builtins.input", lambda prompt="": "y")
    assert cli.main(["sweep", "run", *OPENROUTER_ARGS, "--store", "local"]) == 0  # no --profile
    captured = capsys.readouterr()
    assert built == [MADE_UP_KEY]
    assert "runs finished:   5 of 5" in captured.out
    assert MADE_UP_KEY not in captured.out + captured.err
    for path in (laptop_repo / "scratch" / "runs").rglob("*"):
        if path.is_file():
            assert MADE_UP_KEY not in path.read_text(encoding="utf-8")


def test_a_misshapen_key_is_refused_before_any_call_and_never_echoed(
    laptop_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("builtins.input", lambda prompt="": "y")
    monkeypatch.setattr(cli, "OpenRouterProvider", lambda key: pytest.fail("a provider was built"))
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-ant-api03-this-is-not-an-openrouter-key")
    assert cli.main(["sweep", "run", *OPENROUTER_ARGS, "--store", "local"]) == 2
    err = capsys.readouterr().err
    assert "does not look like an OpenRouter key" in err
    assert "this-is-not" not in err


def test_an_openrouter_model_refuses_the_s3_store_before_asking_for_a_key(
    laptop_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def no_prompt(*args: Any, **kwargs: Any) -> str:
        raise AssertionError("a refused run asked for the key")

    monkeypatch.setattr("getpass.getpass", no_prompt)
    assert cli.main(["sweep", "run", *OPENROUTER_ARGS, "--store", "s3", "--bucket", "b"]) == 2
    assert "an OpenRouter model's runs stay on this laptop" in capsys.readouterr().err


def test_an_openrouter_model_refuses_the_container() -> None:
    args = cli.build_parser().parse_args(["sweep", "run", *OPENROUTER_ARGS, "--store", "local"])
    with pytest.raises(SweepRefusal, match="runs on the laptop only"):
        cli._check_openrouter(args, FARGATE)
    cli._check_openrouter(args, LAPTOP)


def test_an_openrouter_model_cannot_be_launched_as_a_fargate_task(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli.main(["sweep", "launch", *OPENROUTER_ARGS, "--profile", "p"]) == 2
    assert "is an OpenRouter model" in capsys.readouterr().err


def test_the_plan_for_an_openrouter_model_prints_with_a_small_cost_bound(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli.main(["sweep", "plan", *OPENROUTER_ARGS]) == 0
    out = capsys.readouterr().out
    assert "runs:            5 (1 scenarios x 5 objectives x 1 templates x 1 repeats)" in out
    assert "one call start every 3.8s" in out


def test_after_the_draw_real_content_runs_on_the_development_templates_only(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The company's sealed template is drawn (w2): the development model may plan on w1 and w3, never on w2,
    and an official model is refused on real content on its own account."""
    args = [*OPENROUTER_ARGS]
    args[args.index("placeholder")] = "company"
    assert cli.main(["sweep", "plan", *args, "--template", "w1", "--template", "w3"]) == 0
    capsys.readouterr()
    assert cli.main(["sweep", "plan", *args, "--template", "w2"]) == 2
    assert "the sealed template (w2) is never part of a decision prompt" in capsys.readouterr().err
    official = [*args]
    official[official.index("gpt-oss-openrouter")] = "sonnet-4-6"
    assert cli.main(["sweep", "plan", *official, "--template", "w1"]) == 2
    assert "is not the development model" in capsys.readouterr().err


# --- the spend warning, before the OpenRouter key -----------------------------------------------------------


def _no_key_and_no_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_prompt(*args: Any, **kwargs: Any) -> str:
        raise AssertionError("a refused run asked for the key")

    monkeypatch.setattr("getpass.getpass", no_prompt)
    monkeypatch.setattr(cli, "OpenRouterProvider", lambda key: pytest.fail("a provider was built"))


def test_the_spend_warning_states_calls_costs_cap_and_assumption_then_asks(
    laptop_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    asked: list[str] = []

    def answer_no(prompt: str = "") -> str:
        asked.append(prompt)
        return "n"

    monkeypatch.setattr("builtins.input", answer_no)
    _no_key_and_no_provider(monkeypatch)
    monkeypatch.setenv("OPENROUTER_API_KEY", MADE_UP_KEY)  # set, and still it is asked first
    assert cli.main(["sweep", "run", *OPENROUTER_ARGS, "--store", "local"]) == 2
    captured = capsys.readouterr()
    assert asked == ["Continue? [y/N] "]
    assert "calls planned:  5 (runs not yet finished)" in captured.out
    assert "likely cost:    $" in captured.out
    assert "1,000 output tokens" in captured.out
    assert "worst case:     $" in captured.out
    assert "cap:            $5.00" in captured.out
    assert "about $0.0003 a call" in captured.out
    assert "not confirmed: nothing was sent" in captured.err
    assert MADE_UP_KEY not in captured.out + captured.err
    assert not (laptop_repo / "scratch" / "runs").exists() or not any(
        p.is_file() for p in (laptop_repo / "scratch" / "runs").rglob("*")
    )


@pytest.mark.parametrize("answer", ["", "n", "yes please", "no", " "])
def test_anything_but_y_sends_nothing_and_asks_for_no_key(
    answer: str,
    laptop_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("builtins.input", lambda prompt="": answer)
    _no_key_and_no_provider(monkeypatch)
    assert cli.main(["sweep", "run", *OPENROUTER_ARGS, "--store", "local"]) == 2
    assert "not confirmed" in capsys.readouterr().err


def test_no_answer_at_all_is_a_refusal(
    laptop_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def closed(prompt: str = "") -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", closed)
    _no_key_and_no_provider(monkeypatch)
    assert cli.main(["sweep", "run", *OPENROUTER_ARGS, "--store", "local"]) == 2
    assert "not confirmed" in capsys.readouterr().err


def test_a_run_refused_for_another_reason_is_not_asked_to_confirm(
    laptop_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def no_question(prompt: str = "") -> str:
        raise AssertionError("a refused run was asked to confirm")

    monkeypatch.setattr("builtins.input", no_question)
    _no_key_and_no_provider(monkeypatch)
    assert cli.main(["sweep", "run", *OPENROUTER_ARGS, "--store", "s3", "--bucket", "b"]) == 2
    assert "an OpenRouter model's runs stay on this laptop" in capsys.readouterr().err


def test_only_the_openrouter_route_is_asked(
    laptop_repo: Path,
    fake_clock: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def no_question(prompt: str = "") -> str:
        raise AssertionError("a local run was asked to confirm")

    monkeypatch.setattr("builtins.input", no_question)
    monkeypatch.setattr(cli, "OllamaProvider", lambda url, num_ctx: ScriptedProvider())
    assert cli.main(["sweep", "run", *LOCAL_ARGS, "--store", "local"]) == 0
    assert "calls planned" not in capsys.readouterr().out


def test_a_resumed_sweep_counts_only_the_runs_not_yet_finished(
    laptop_repo: Path,
    fake_clock: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "OpenRouterProvider", lambda key: ScriptedProvider())
    monkeypatch.setenv("OPENROUTER_API_KEY", MADE_UP_KEY)
    monkeypatch.setattr("builtins.input", lambda prompt="": "y")
    assert cli.main(["sweep", "run", *OPENROUTER_ARGS, "--store", "local"]) == 0
    capsys.readouterr()
    monkeypatch.setattr("builtins.input", lambda prompt="": "n")
    assert cli.main(["sweep", "run", *OPENROUTER_ARGS, "--store", "local"]) == 2
    assert "calls planned:  0 (runs not yet finished)" in capsys.readouterr().out
