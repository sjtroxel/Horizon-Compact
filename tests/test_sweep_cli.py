"""The ``hc sweep`` command line: what works offline and what is refused before AWS is touched."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import boto3
import pytest

from horizon_compact import cli
from sweep_helpers import company_like

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
