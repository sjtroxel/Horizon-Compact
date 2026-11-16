"""The re-scoring check (Phase 6.5 IMPLEMENTATION doc section 5.2, definition of done row 2).

The frozen analysis, run through ``hc analyze``'s own code path on the published raw records under
``experiment/raw/``, must write each official sweep's results file byte for byte as it is committed under
``experiment/results/prereg-v1/``. The validation each record holds, which is what the analysis reads, must
be the frozen validator's verdict on the tool call the record holds. These tests read the real committed
files, skip nothing, and fail if anything opens an AWS client while they run: a reader with a clone and no
account can repeat every one.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any, NoReturn

import boto3
import botocore.session
import pytest

from horizon_compact import cli
from horizon_compact.experiment import load_experiment
from horizon_compact.sweep.decision import validate_decision

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "experiment" / "results" / "prereg-v1"
RAW = REPO / "experiment" / "raw"

# (model key, sweep id): the three official sweeps that have a results file from ``hc analyze``.
SWEEPS = [
    ("haiku-5-5", "grid-haiku-5-5-0b99fabb"),
    ("gpt-oss-openrouter", "grid-gpt-oss-openrouter-fe599ad2"),
    ("haiku-5-5", "thinking-haiku-5-5-418caa9c"),
]


class AwsClientOpened(Exception):
    """Something asked for an AWS client while the re-scoring test was running."""


def _refuse(*args: object, **kwargs: object) -> NoReturn:
    raise AwsClientOpened(
        "the re-scoring test opened an AWS client: it may read published files only"
    )


@pytest.fixture(autouse=True)
def no_aws_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Every way into AWS that this code base uses ends in botocore's ``create_client``; ``boto3.client``,
    ``boto3.resource`` and the command's own ``_session`` are patched as well, so a failure names the door."""
    monkeypatch.setattr(botocore.session.Session, "create_client", _refuse)
    monkeypatch.setattr(boto3, "client", _refuse)
    monkeypatch.setattr(boto3, "resource", _refuse)
    monkeypatch.setattr(cli, "_session", _refuse)
    yield


def test_the_guard_refuses_every_way_of_opening_an_aws_client() -> None:
    with pytest.raises(AwsClientOpened, match="re-scoring test opened an AWS client"):
        boto3.client("s3", region_name="us-east-1")
    with pytest.raises(AwsClientOpened):
        boto3.resource("s3", region_name="us-east-1")
    with pytest.raises(AwsClientOpened):
        boto3.Session(region_name="us-east-1").client("s3")
    with pytest.raises(AwsClientOpened):
        cli._session(SimpleNamespace(profile=None), None)  # type: ignore[arg-type]


def test_the_list_of_official_results_files_is_complete() -> None:
    """A fourth results file nobody re-scores fails here, rather than passing quietly."""
    on_disk = sorted(p.relative_to(RESULTS).as_posix() for p in RESULTS.rglob("*.json"))
    assert on_disk == sorted(f"{model}/{sweep}.json" for model, sweep in SWEEPS)


# The attempts in each sweep that carry a validation: the ones the analysis reads a decision from.
VALIDATED_ATTEMPTS = {
    "grid-haiku-5-5-0b99fabb": 1128,
    "grid-gpt-oss-openrouter-fe599ad2": 1296,
    "thinking-haiku-5-5-418caa9c": 100,
}


@pytest.mark.parametrize("sweep", list(VALIDATED_ATTEMPTS))
def test_every_recorded_validation_is_the_frozen_validator_on_the_recorded_tool_call(
    sweep: str,
) -> None:
    """The analysis reads each attempt's recorded ``validation``, the harness's verdict written at run
    time, not the model's tool call. This closes that link: the locked validator, run again on the tool call
    each record holds, gives the validation it holds (Opus review of step 3, section 5.2). If it fails, the
    raw text or the validator changed, and neither may."""
    experiment = load_experiment("company")
    checked = 0
    for path in sorted((RAW / "official" / "company" / sweep / "runs").glob("*/attempt-*.json")):
        attempt = json.loads(path.read_bytes())
        recorded = attempt.get("validation")
        if recorded is None:
            continue
        calls = attempt["tool_calls"]
        assert len(calls) == 1, (
            f"{path.relative_to(REPO)}: a validation without exactly one tool call"
        )
        again = validate_decision(
            experiment.get_scenario(attempt["scenario_id"]), calls[0].get("input")
        )
        assert again.as_dict() == recorded, path.relative_to(REPO)
        checked += 1
    assert checked == VALIDATED_ATTEMPTS[sweep]


@pytest.mark.parametrize(("model", "sweep"), SWEEPS, ids=[sweep for _, sweep in SWEEPS])
def test_the_frozen_analysis_rescores_the_published_raw_text_byte_for_byte(
    model: str, sweep: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """If this fails, run it alone and diff the file it wrote (under pytest's tmp folder) against the
    committed one: a difference means the raw text, the analysis or the results file changed, and none of
    those may."""
    root = tmp_path / "repo"
    args: list[Any] = [
        "analyze", "--experiment", "company", "--sweep", sweep,
        "--store", "local", "--runs-root", str(RAW),
        "--protocol", "prereg-v1", "--root", str(root),
    ]  # fmt: skip
    assert cli.main(args) == 0, capsys.readouterr().err
    written = root / "experiment" / "results" / "prereg-v1" / model / f"{sweep}.json"
    assert written.read_bytes() == (RESULTS / model / f"{sweep}.json").read_bytes()
