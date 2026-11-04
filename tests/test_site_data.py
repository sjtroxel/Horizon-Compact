"""The site-data builder and ``hc site data`` (Phase 1.5 IMPLEMENTATION doc sections 6 and 18).

Every fixture is a placeholder-shaped record written here, five priorities by three repeats, never a copy of a
real record. The experiment is the real placeholder folder, so the content hashes in the fixtures are the ones
the loader computes.
"""

from __future__ import annotations

import copy
import io
import json
import math
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, cast

import pytest
from botocore.exceptions import ClientError

from horizon_compact.cli import CLEAN_EXIT, REFUSED_EXIT, main
from horizon_compact.experiment import Experiment, load_experiment
from horizon_compact.site.data import SiteDataRefusal, build_site_data, write_site_data
from horizon_compact.sweep.store import LocalStore, S3Store

SWEEP = "site-test-haiku-5-5-0a1b2c3d"
PREFIX = f"development/placeholder/{SWEEP}/"
MEMO = "ZEBRA-MEMO-the-distinctive-words-a-model-wrote-about-its-reasons"
REQUEST_ID = "req_011CfxQ13HvKiVPb9UzBW9uX"
ACCOUNT_IMAGE = "123456789012.dkr.ecr.us-east-1.amazonaws.com/horizon-compact"
TASK_ARN = "arn:aws:ecs:us-east-1:123456789012:task/cluster/abc"
DIGEST = "sha256:" + "ab" * 32
GIT_SHA = "8ab367cf6a4178cc863142b70faa470a40cc45ad"

Objects = dict[str, Any]


@pytest.fixture(scope="module")
def experiment() -> Experiment:
    return load_experiment("placeholder")


def _run_id(index: int) -> str:
    return f"r-a{index:011x}"


def _amounts(experiment: Experiment, objective_index: int, repeat: int) -> dict[str, float]:
    keys = [lever.key for lever in experiment.scenario.offered()]
    return {key: float(100 * (i + 1) + 10 * repeat + objective_index) for i, key in enumerate(keys)}


def _attempt(
    experiment: Experiment, run_id: str, objective: str, number: int, **override: Any
) -> dict[str, Any]:
    objective_index = [o.id for o in experiment.objectives].index(objective)
    repeat = int(override.pop("repeat", 0))
    amounts = _amounts(experiment, objective_index, repeat)
    record: dict[str, Any] = {
        "attempt": number,
        "status": "valid",
        "run_id": run_id,
        "sweep_id": SWEEP,
        "scenario_id": "garden",
        "objective_id": objective,
        "menu_order": ["raffle", "herbs", "plant_sale"],
        "option_order": ["spring", "autumn"],
        "possible_decline": False,
        "content_hash": experiment.content_hash,
        "file_hashes": {
            key: value
            for key, value in experiment.file_hashes.items()
            if key.startswith("placeholder/")
        },
        "git_sha": GIT_SHA,
        "image_digest": DIGEST,
        "image": ACCOUNT_IMAGE,
        "task_arn": TASK_ARN,
        "runner": "fargate",
        "started_at": f"2026-10-12T13:09:{10 + number:02d}.500000+00:00",
        "finished_at": f"2026-10-12T13:10:{10 + number:02d}.500000+00:00",
        "provider_details": {"request_id": REQUEST_ID, "served_model": "claude-haiku-5-5"},
        "parsed_decision": {"amounts": amounts, "memo": MEMO, "open_day_season": "autumn"},
        "raw_response": {"content": [{"type": "text", "text": MEMO}]},
        "text_blocks": [MEMO],
        "tool_calls": [{"input": {"memo": MEMO}}],
        "request": {"messages": [{"role": "user", "content": "x"}]},
        "validation": {
            "status": "valid",
            "amounts": amounts,
            "scaled_amounts": None,
            "choice": "autumn",
            "memo_words": 160,
            "problems": [],
        },
    }
    record.update(override)
    return record


def build_objects(experiment: Experiment) -> Objects:
    """Fifteen runs, all valid on the first attempt, one session. Keys are relative to the sweep's prefix."""
    objects: Objects = {}
    runs: list[dict[str, Any]] = []
    index = 0
    for objective in experiment.objectives:
        for repeat in range(3):
            index += 1
            run_id = _run_id(index)
            runs.append(
                {
                    "run_id": run_id,
                    "objective_id": objective.id,
                    "scenario_id": "garden",
                    "wording_id": "w1",
                    "repeat": repeat,
                    "menu_order_seed": 1000 + index,
                }
            )
            objects[f"runs/{run_id}/attempt-1.json"] = _attempt(
                experiment, run_id, objective.id, 1, repeat=repeat
            )
            objects[f"runs/{run_id}/final.json"] = {
                "run_id": run_id,
                "sweep_id": SWEEP,
                "objective_id": objective.id,
                "status": "valid",
                "first_attempt_status": "valid",
                "final_attempt": 1,
                "attempts": 1,
                "model_attempts": 1,
            }
    objects["manifest.json"] = {
        "experiment": "placeholder",
        "sweep_id": SWEEP,
        "model_key": "haiku-5-5",
        "content_hash": experiment.content_hash,
        "runs": runs,
    }
    objects["sessions/20261012T130930899276Z-fargate.json"] = {
        "sweep_id": SWEEP,
        "cost_usd_this_session": 0.013993,
        "runner": "fargate",
    }
    return objects


def put(root: Path, objects: Objects, prefix: str = PREFIX) -> LocalStore:
    store = LocalStore(root)
    for key, value in objects.items():
        assert store.put_new(prefix + key, json.dumps(value))
    return store


def built(
    tmp_path: Path, experiment: Experiment, mutate: Callable[[Objects], None] | None = None
) -> str:
    objects = build_objects(experiment)
    if mutate is not None:
        mutate(objects)
    return build_site_data(put(tmp_path, objects), SWEEP, experiment)


def refused(
    tmp_path: Path, experiment: Experiment, mutate: Callable[[Objects], None], message: str
) -> None:
    with pytest.raises(SiteDataRefusal, match=message):
        built(tmp_path, experiment, mutate)


def run_keys(objects: Objects) -> list[str]:
    return [k for k in objects if k.startswith("runs/") and k.endswith("attempt-1.json")]


# --- determinism and the two stores ---------------------------------------------------------------


def test_a_second_build_is_byte_identical(tmp_path: Path, experiment: Experiment) -> None:
    store = put(tmp_path, build_objects(experiment))
    first = build_site_data(store, SWEEP, experiment)
    second = build_site_data(store, SWEEP, experiment)
    assert first == second
    assert first.endswith("}\n") and not first.endswith("\n\n")
    assert json.loads(first)["schema"] == "horizon-compact/site-placeholder"


def test_the_builder_writes_nothing_to_the_store(tmp_path: Path, experiment: Experiment) -> None:
    store = put(tmp_path, build_objects(experiment))
    before = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))
    build_site_data(store, SWEEP, experiment)
    assert sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*")) == before


class FakeS3:
    """Just enough of a boto3 S3 client for ``S3Store``: paginated listing and get_object."""

    def __init__(self, bucket: str, objects: dict[str, str]) -> None:
        self.bucket, self.objects = bucket, objects

    def get_object(self, *, Bucket: str, Key: str) -> dict[str, Any]:
        if Bucket != self.bucket or Key not in self.objects:
            raise ClientError({"Error": {"Code": "NoSuchKey", "Message": "x"}}, "GetObject")
        return {"Body": io.BytesIO(self.objects[Key].encode("utf-8"))}

    def get_paginator(self, name: str) -> FakeS3:
        assert name == "list_objects_v2"
        return self

    def paginate(self, *, Bucket: str, Prefix: str) -> Iterator[dict[str, Any]]:
        assert Bucket == self.bucket
        keys = sorted(k for k in self.objects if k.startswith(Prefix))
        for start in range(0, len(keys), 4):  # several pages, so pagination is exercised
            yield {"Contents": [{"Key": k} for k in keys[start : start + 4]]}


def test_s3_store_and_local_store_give_identical_text(
    tmp_path: Path, experiment: Experiment
) -> None:
    objects = build_objects(experiment)
    local = put(tmp_path, objects)
    on_s3 = S3Store(
        cast("Any", FakeS3("bucket", {PREFIX + k: json.dumps(v) for k, v in objects.items()})),
        "bucket",
    )
    assert build_site_data(on_s3, SWEEP, experiment) == build_site_data(local, SWEEP, experiment)


# --- the file's shape -----------------------------------------------------------------------------


def test_key_order_is_pinned_at_every_level(tmp_path: Path, experiment: Experiment) -> None:
    data = json.loads(built(tmp_path, experiment))
    assert list(data) == [
        "schema",
        "schema_version",
        "kind",
        "content",
        "sweep",
        "scenario",
        "objectives",
        "cells",
        "runs",
    ]
    assert (data["schema_version"], data["kind"], data["content"]) == (1, "test-run", "placeholder")
    assert list(data["sweep"]) == [
        "sweep_id",
        "experiment",
        "role",
        "model_key",
        "served_models",
        "runs_planned",
        "runs_finished",
        "status_counts",
        "first_attempt_status_counts",
        "cost_usd",
        "image_digests",
        "git_shas",
        "content_hashes",
        "runners",
        "started_at",
        "finished_at",
    ]
    scenario = data["scenario"]
    assert list(scenario) == ["id", "total", "lines", "not_offered", "choice"]
    assert list(scenario["lines"][0]) == ["key", "label", "kind", "cap"]
    assert list(scenario["not_offered"][0]) == ["key", "label", "note"]
    assert list(scenario["choice"]) == ["key", "label", "options"]
    assert list(scenario["choice"]["options"][0]) == ["key", "text"]
    assert list(data["objectives"][0]) == ["id", "template_id", "sentence"]
    cell = data["cells"][0]
    assert list(cell) == [
        "objective_id",
        "runs",
        "valid",
        "status_counts",
        "first_attempt_status_counts",
        "lines",
        "choice_counts",
    ]
    assert list(cell["lines"]) == [lever.key for lever in experiment.scenario.offered()]
    assert list(cell["lines"]["bulbs"]) == ["mean", "min", "max"]
    assert list(data["runs"][0]) == [
        "run_id",
        "objective_id",
        "wording_id",
        "repeat",
        "status",
        "first_attempt_status",
        "attempts",
        "amounts",
        "choice",
        "image_digest",
        "git_sha",
        "content_hash",
        "served_model",
        "runner",
        "finished_at",
    ]
    assert list(data["runs"][0]["amounts"]) == list(cell["lines"])


def test_objectives_cells_and_runs_follow_the_stated_orders(
    tmp_path: Path, experiment: Experiment
) -> None:
    data = json.loads(built(tmp_path, experiment))
    order = [o.id for o in experiment.objectives]
    assert [o["id"] for o in data["objectives"]] == order
    assert [c["objective_id"] for c in data["cells"]] == order
    ids = [r["run_id"] for r in data["runs"]]
    assert ids == sorted(ids) and len(ids) == 15
    first = experiment.objectives[0]
    assert data["objectives"][0]["sentence"] == experiment.wording_sentence(first, "w1")
    assert data["scenario"]["not_offered"] == [
        {"key": "tool_shed", "label": "A tool shed", "note": "not offered this season"}
    ]
    assert list(data["cells"][0]["choice_counts"]) == ["spring", "autumn"]


def test_sweep_block_values(tmp_path: Path, experiment: Experiment) -> None:
    def mutate(objects: Objects) -> None:
        # An earlier api_error attempt on one run: it counts toward the earliest start, not toward `attempts`.
        key = run_keys(objects)[0]
        run_id = key.split("/")[1]
        final = objects[f"runs/{run_id}/final.json"]
        final["final_attempt"] = 2
        second = copy.deepcopy(objects[key])
        second["attempt"] = 2
        objects[f"runs/{run_id}/attempt-2.json"] = second
        objects[key] = {
            "attempt": 1,
            "status": "api_error",
            "started_at": "2026-10-12T13:00:00.000000+00:00",
            "finished_at": "2026-10-12T13:00:05.000000+00:00",
        }
        objects["sessions/20261012T140000000000Z-fargate.json"] = {
            "sweep_id": SWEEP,
            "cost_usd_this_session": 0.2,
        }

    data = json.loads(built(tmp_path, experiment, mutate))
    sweep = data["sweep"]
    assert sweep["started_at"] == "2026-10-12T13:00:00.000000+00:00"
    assert sweep["finished_at"] == "2026-10-12T13:10:11.500000+00:00"
    assert sweep["cost_usd"] == 0.213993
    assert sweep["runs_planned"] == sweep["runs_finished"] == 15
    assert sweep["status_counts"] == {"valid": 15}
    assert sweep["served_models"] == ["claude-haiku-5-5"]
    assert sweep["runners"] == ["fargate"]
    assert (sweep["role"], sweep["experiment"], sweep["model_key"]) == (
        "development",
        "placeholder",
        "haiku-5-5",
    )
    first = next(r for r in data["runs"] if r["run_id"] == _run_id(1))
    assert first["attempts"] == 1


def test_one_cell_by_hand(tmp_path: Path, experiment: Experiment) -> None:
    """The first objective, repeats 0, 1 and 2: each line is 100 * (line index + 1) + 10 * repeat + 0."""
    data = json.loads(built(tmp_path, experiment))
    cell = data["cells"][0]
    assert cell["objective_id"] == "color"
    assert cell["lines"]["yearly_fund"] == {"mean": 110.0, "min": 100.0, "max": 120.0}
    assert cell["lines"]["plant_sale"] == {"mean": 210.0, "min": 200.0, "max": 220.0}
    assert cell["lines"]["mulch_compost"] == {"mean": 710.0, "min": 700.0, "max": 720.0}
    assert (cell["runs"], cell["valid"]) == (3, 3)
    assert cell["choice_counts"] == {"spring": 0, "autumn": 3}


def test_the_mean_is_fsum_over_the_count(tmp_path: Path, experiment: Experiment) -> None:
    values = [0.1, 0.2, 0.4]

    def mutate(objects: Objects) -> None:
        for repeat, key in enumerate(run_keys(objects)[:3]):
            amounts = dict(objects[key]["validation"]["amounts"])
            amounts["yearly_fund"] = values[repeat]
            objects[key]["validation"]["amounts"] = amounts

    data = json.loads(built(tmp_path, experiment, mutate))
    line = data["cells"][0]["lines"]["yearly_fund"]
    assert line["mean"] == math.fsum(values) / 3
    assert (line["min"], line["max"]) == (0.1, 0.4)


def test_a_rescaled_run_is_counted_at_its_scaled_amounts(
    tmp_path: Path, experiment: Experiment
) -> None:
    def mutate(objects: Objects) -> None:
        key = run_keys(objects)[0]
        run_id = key.split("/")[1]
        scaled = dict.fromkeys(objects[key]["validation"]["amounts"], 5.0)
        objects[key]["status"] = "valid_rescaled"
        objects[key]["validation"]["status"] = "valid_rescaled"
        objects[key]["validation"]["scaled_amounts"] = scaled
        objects[f"runs/{run_id}/final.json"]["status"] = "valid_rescaled"
        objects[f"runs/{run_id}/final.json"]["first_attempt_status"] = "valid_rescaled"

    data = json.loads(built(tmp_path, experiment, mutate))
    run = next(r for r in data["runs"] if r["run_id"] == _run_id(1))
    assert run["status"] == "valid_rescaled"
    assert set(run["amounts"].values()) == {5.0}
    cell = data["cells"][0]
    assert cell["valid"] == 3
    assert cell["status_counts"] == {"valid": 2, "valid_rescaled": 1}
    # By hand: repeats 0, 1 and 2 hold 5 (scaled), 110 and 120 on the first line.
    assert cell["lines"]["yearly_fund"] == {"mean": (5 + 110 + 120) / 3, "min": 5.0, "max": 120.0}


def test_a_cell_with_no_valid_run_has_null_ranges(tmp_path: Path, experiment: Experiment) -> None:
    def mutate(objects: Objects) -> None:
        for key in run_keys(objects)[12:15]:  # the last objective, "none"
            run_id = key.split("/")[1]
            objects[key]["status"] = "no_tool_call"
            objects[key]["validation"] = None
            objects[f"runs/{run_id}/final.json"]["status"] = "no_tool_call"
            objects[f"runs/{run_id}/final.json"]["first_attempt_status"] = "no_tool_call"

    data = json.loads(built(tmp_path, experiment, mutate))
    cell = data["cells"][4]
    assert cell["objective_id"] == "none"
    assert (cell["runs"], cell["valid"]) == (3, 0)
    assert cell["status_counts"] == {"no_tool_call": 3}
    assert all(line == {"mean": None, "min": None, "max": None} for line in cell["lines"].values())
    assert cell["choice_counts"] == {"spring": 0, "autumn": 0}
    run = next(r for r in data["runs"] if r["run_id"] == _run_id(13))
    assert run["amounts"] is None and run["choice"] is None
    assert data["sweep"]["status_counts"] == {"no_tool_call": 3, "valid": 12}


# --- what is never copied -------------------------------------------------------------------------


def test_no_memo_text_no_request_id_and_no_account_bearing_field(
    tmp_path: Path, experiment: Experiment
) -> None:
    text = built(tmp_path, experiment)
    for forbidden in (
        "ZEBRA-MEMO",
        "memo",
        REQUEST_ID,
        ACCOUNT_IMAGE,
        "123456789012",
        "arn:",
        "task_arn",
        "raw_response",
        "tool_calls",
        "parsed_decision",
        "memo_words",
    ):
        assert forbidden not in text, forbidden


def test_a_lone_twelve_digit_number_is_caught(tmp_path: Path, experiment: Experiment) -> None:
    def mutate(objects: Objects) -> None:
        for key in run_keys(objects):
            objects[key]["git_sha"] = "123456789012"

    refused(tmp_path, experiment, mutate, "account id or an ARN")


def test_an_arn_is_caught(tmp_path: Path, experiment: Experiment) -> None:
    def mutate(objects: Objects) -> None:
        for key in run_keys(objects):
            objects[key]["provider_details"]["served_model"] = "arn:aws:bedrock:us-east-1:x"

    refused(tmp_path, experiment, mutate, "account id or an ARN")


def test_a_digest_holding_twelve_digits_in_a_row_is_not_caught(
    tmp_path: Path, experiment: Experiment
) -> None:
    digest = "sha256:a123456789012b" + "c" * 50

    def mutate(objects: Objects) -> None:
        for key in run_keys(objects):
            objects[key]["image_digest"] = digest

    data = json.loads(built(tmp_path, experiment, mutate))
    assert data["sweep"]["image_digests"] == [digest]


# --- refusals, one each ---------------------------------------------------------------------------


def test_refuses_an_experiment_other_than_the_placeholder(tmp_path: Path) -> None:
    other = load_experiment("shapes")
    with pytest.raises(SiteDataRefusal, match="placeholder experiment only"):
        build_site_data(LocalStore(tmp_path), SWEEP, other)


@pytest.mark.parametrize("sweep_id", ["../x", "a/b", "A", "-a", "", "a b", "a\n", "x/../../y"])
def test_refuses_a_sweep_id_that_could_move_the_prefix(
    tmp_path: Path, experiment: Experiment, sweep_id: str
) -> None:
    with pytest.raises(SiteDataRefusal, match="plain lower-case name"):
        build_site_data(LocalStore(tmp_path), sweep_id, experiment)


def test_refuses_a_manifest_for_another_experiment(tmp_path: Path, experiment: Experiment) -> None:
    refused(
        tmp_path,
        experiment,
        lambda o: o["manifest.json"].update(experiment="shapes"),
        "manifest's experiment",
    )


def test_refuses_a_manifest_for_another_sweep(tmp_path: Path, experiment: Experiment) -> None:
    refused(
        tmp_path,
        experiment,
        lambda o: o["manifest.json"].update(sweep_id="another-sweep-00000000"),
        "manifest's sweep id",
    )


def test_refuses_an_unfinished_run(tmp_path: Path, experiment: Experiment) -> None:
    refused(
        tmp_path, experiment, lambda o: o.pop(f"runs/{_run_id(3)}/final.json"), "1 run.*unfinished"
    )


@pytest.mark.parametrize(
    "field",
    [
        "image_digest",
        "git_sha",
        "content_hash",
        "provider_details.served_model",
        "runner",
        "started_at",
        "finished_at",
    ],
)
def test_refuses_a_final_attempt_missing_provenance(
    tmp_path: Path, experiment: Experiment, field: str
) -> None:
    def mutate(objects: Objects) -> None:
        record = objects[f"runs/{_run_id(7)}/attempt-1.json"]
        parent, _, leaf = field.rpartition(".")
        target = record[parent] if parent else record
        del target[leaf]

    refused(tmp_path, experiment, mutate, f"{_run_id(7)}.*lacks.*{field}")


def test_provenance_missing_on_a_non_final_attempt_is_not_a_refusal(
    tmp_path: Path, experiment: Experiment
) -> None:
    def mutate(objects: Objects) -> None:
        run_id = _run_id(2)
        final = objects[f"runs/{run_id}/final.json"]
        final["final_attempt"] = 2
        objects[f"runs/{run_id}/attempt-2.json"] = copy.deepcopy(
            objects[f"runs/{run_id}/attempt-1.json"]
        )
        objects[f"runs/{run_id}/attempt-2.json"]["attempt"] = 2
        objects[f"runs/{run_id}/attempt-1.json"] = {
            "attempt": 1,
            "status": "api_error",
        }

    built(tmp_path, experiment, mutate)


def test_refuses_content_that_has_drifted(tmp_path: Path, experiment: Experiment) -> None:
    refused(
        tmp_path,
        experiment,
        lambda o: o[f"runs/{_run_id(4)}/attempt-1.json"].update(content_hash="0" * 64),
        f"{_run_id(4)}.*now hashes",
    )


def test_refuses_a_file_hash_that_has_drifted(tmp_path: Path, experiment: Experiment) -> None:
    def mutate(objects: Objects) -> None:
        hashes = objects[f"runs/{_run_id(5)}/attempt-1.json"]["file_hashes"]
        hashes["placeholder/objectives.toml"] = "0" * 64

    refused(tmp_path, experiment, mutate, "placeholder/objectives.toml")


def test_a_changed_models_toml_hash_is_not_drift(tmp_path: Path, experiment: Experiment) -> None:
    def mutate(objects: Objects) -> None:
        for key in run_keys(objects):
            objects[key]["file_hashes"]["models.toml"] = "0" * 64

    built(tmp_path, experiment, mutate)


def test_refuses_a_sweep_with_no_session_summary(tmp_path: Path, experiment: Experiment) -> None:
    refused(
        tmp_path,
        experiment,
        lambda o: o.pop("sessions/20261012T130930899276Z-fargate.json"),
        "no session summary",
    )


def test_refuses_an_objective_with_two_wordings(tmp_path: Path, experiment: Experiment) -> None:
    def mutate(objects: Objects) -> None:
        objects["manifest.json"]["runs"][0]["wording_id"] = "w2"

    refused(tmp_path, experiment, mutate, "more than one wording")


def test_refuses_an_objective_with_no_runs(tmp_path: Path, experiment: Experiment) -> None:
    def mutate(objects: Objects) -> None:
        gone = {
            r["run_id"] for r in objects["manifest.json"]["runs"] if r["objective_id"] == "water"
        }
        objects["manifest.json"]["runs"] = [
            r for r in objects["manifest.json"]["runs"] if r["run_id"] not in gone
        ]
        for run_id in gone:
            del objects[f"runs/{run_id}/attempt-1.json"]
            del objects[f"runs/{run_id}/final.json"]

    refused(tmp_path, experiment, mutate, "'water' has no runs")


def test_refuses_a_run_whose_objective_is_not_in_the_experiment(
    tmp_path: Path, experiment: Experiment
) -> None:
    def mutate(objects: Objects) -> None:
        run_id = _run_id(1)
        objects["manifest.json"]["runs"][0]["objective_id"] = "invented"
        objects[f"runs/{run_id}/attempt-1.json"]["objective_id"] = "invented"
        objects[f"runs/{run_id}/final.json"]["objective_id"] = "invented"

    refused(tmp_path, experiment, mutate, "'invented'")


def test_reads_only_the_placeholder_prefix(tmp_path: Path, experiment: Experiment) -> None:
    """The same objects under another experiment's prefix are not found: the prefix is built in code."""
    put(tmp_path, build_objects(experiment), prefix=f"development/shapes/{SWEEP}/")
    with pytest.raises(SiteDataRefusal, match="no manifest"):
        build_site_data(LocalStore(tmp_path), SWEEP, experiment)


# --- the writer -----------------------------------------------------------------------------------


def test_the_writer_creates_the_folder_and_the_same_bytes_is_a_no_op(tmp_path: Path) -> None:
    path = tmp_path / "web" / "src" / "data" / "placeholder.json"
    assert write_site_data('{"a": 1}\n', path) == path
    assert path.read_bytes() == b'{"a": 1}\n'
    stamp = path.stat().st_mtime_ns
    assert write_site_data('{"a": 1}\n', path) == path
    assert path.stat().st_mtime_ns == stamp
    assert [p.name for p in path.parent.iterdir()] == ["placeholder.json"]  # no temporary file left


def test_the_writer_refuses_different_bytes_and_leaves_the_file(tmp_path: Path) -> None:
    path = tmp_path / "placeholder.json"
    write_site_data('{"a": 1}\n', path)
    with pytest.raises(SiteDataRefusal, match="different data"):
        write_site_data('{"a": 2}\n', path)
    assert path.read_bytes() == b'{"a": 1}\n'


def test_the_writer_uses_unix_newlines(tmp_path: Path) -> None:
    path = tmp_path / "placeholder.json"
    write_site_data('{\n  "a": 1\n}\n', path)
    assert b"\r" not in path.read_bytes()


# --- the command ----------------------------------------------------------------------------------


def _cli(tmp_path: Path, *extra: str) -> list[str]:
    return [
        "site",
        "data",
        "--experiment",
        "placeholder",
        "--sweep",
        SWEEP,
        "--store",
        "local",
        "--runs-root",
        str(tmp_path / "runs"),
        *extra,
    ]


def test_the_command_end_to_end_on_the_local_store(
    tmp_path: Path, experiment: Experiment, capsys: pytest.CaptureFixture[str]
) -> None:
    put(tmp_path / "runs", build_objects(experiment))
    out = tmp_path / "out" / "placeholder.json"
    assert main(_cli(tmp_path, "--out", str(out))) == CLEAN_EXIT
    lines = capsys.readouterr().out.strip().splitlines()
    assert lines == [f"wrote {out}", f"sweep: {SWEEP}", "runs:  15"]
    expected = build_site_data(LocalStore(tmp_path / "runs"), SWEEP, experiment)
    assert out.read_text(encoding="utf-8") == expected
    # Again: the same bytes, a no-op.
    assert main(_cli(tmp_path, "--out", str(out))) == CLEAN_EXIT
    # A file that holds different bytes is refused, and left alone.
    out.write_text("{}\n", encoding="utf-8")
    assert main(_cli(tmp_path, "--out", str(out))) == REFUSED_EXIT
    assert "different data" in capsys.readouterr().err
    assert out.read_text(encoding="utf-8") == "{}\n"


def test_the_command_refuses_another_experiment(
    tmp_path: Path, experiment: Experiment, capsys: pytest.CaptureFixture[str]
) -> None:
    put(tmp_path / "runs", build_objects(experiment))
    argv = _cli(tmp_path, "--out", str(tmp_path / "x.json"))
    argv[argv.index("placeholder")] = "shapes"
    assert main(argv) == REFUSED_EXIT
    assert capsys.readouterr().err.startswith("refused: ")
    assert not (tmp_path / "x.json").exists()


def test_the_command_refuses_a_bad_sweep_id(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    argv = _cli(tmp_path, "--out", str(tmp_path / "x.json"))
    argv[argv.index(SWEEP)] = "../escape"
    assert main(argv) == REFUSED_EXIT
    assert "plain lower-case name" in capsys.readouterr().err


def test_the_store_is_required(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as raised:
        main(["site", "data", "--experiment", "placeholder", "--sweep", SWEEP])
    assert raised.value.code == 2


def test_s3_needs_a_profile_and_a_bucket(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    config = tmp_path / "aws-config"
    config.write_text("[profile test]\nregion = us-east-1\n", encoding="utf-8")
    monkeypatch.setenv("AWS_CONFIG_FILE", str(config))
    monkeypatch.delenv("HC_RESULTS_BUCKET", raising=False)
    argv = ["site", "data", "--experiment", "placeholder", "--sweep", SWEEP, "--store", "s3"]
    assert main([*argv, "--out", str(tmp_path / "x.json")]) == REFUSED_EXIT
    assert "--profile is required" in capsys.readouterr().err
    assert main([*argv, "--profile", "test", "--out", str(tmp_path / "x.json")]) == REFUSED_EXIT
    assert "needs --bucket" in capsys.readouterr().err
