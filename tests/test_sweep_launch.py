"""Launch and stop (Phase 1 IMPLEMENTATION doc sections 9, 10.5 and 13, "launch")."""

from __future__ import annotations

from typing import Any, cast

import pytest

from horizon_compact.sweep.launch import launch_task, running_tasks, stop_tasks
from horizon_compact.sweep.plan import SweepRefusal

TASK_DEF = "arn:aws:ecs:us-east-1:123456789012:task-definition/horizon-compact-sweep:7"
COMMAND = ["sweep", "run", "--experiment", "placeholder", "--model", "sonnet-4-6", "--repeats", "3"]


def task(model: str, n: int) -> dict[str, Any]:
    return {
        "taskArn": f"arn:aws:ecs:us-east-1:123456789012:task/horizon-compact/t{n}",
        "overrides": {
            "containerOverrides": [{"name": "sweep", "command": ["sweep", "run", "--model", model]}]
        },
    }


class FakeEcs:
    def __init__(
        self, running: list[dict[str, Any]] | None = None, failures: list[Any] | None = None
    ) -> None:
        self.running = running or []
        self.failures = failures or []
        self.run_kwargs: dict[str, Any] | None = None
        self.stopped: list[str] = []

    def list_tasks(self, **kwargs: Any) -> dict[str, Any]:
        assert (kwargs["cluster"], kwargs["family"], kwargs["desiredStatus"]) == (
            "horizon-compact",
            "horizon-compact-sweep",
            "RUNNING",
        )
        return {"taskArns": [t["taskArn"] for t in self.running]}

    def describe_tasks(self, **kwargs: Any) -> dict[str, Any]:
        return {"tasks": [t for t in self.running if t["taskArn"] in kwargs["tasks"]]}

    def describe_task_definition(self, **kwargs: Any) -> dict[str, Any]:
        assert kwargs["taskDefinition"] == "horizon-compact-sweep"
        return {"taskDefinition": {"taskDefinitionArn": TASK_DEF}}

    def run_task(self, **kwargs: Any) -> dict[str, Any]:
        self.run_kwargs = kwargs
        return {
            "tasks": [] if self.failures else [task("sonnet-4-6", 9)],
            "failures": self.failures,
        }

    def stop_task(self, **kwargs: Any) -> dict[str, Any]:
        self.stopped.append(kwargs["task"])
        return {}


class FakeEc2:
    def __init__(self, subnets: int = 2, groups: int = 1) -> None:
        self.subnets, self.groups = subnets, groups

    def describe_subnets(self, **kwargs: Any) -> dict[str, Any]:
        names = {f["Name"] for f in kwargs["Filters"]}
        assert names == {"tag:Tier", "tag:Project"}
        return {"Subnets": [{"SubnetId": f"subnet-{i}"} for i in range(self.subnets)]}

    def describe_security_groups(self, **kwargs: Any) -> dict[str, Any]:
        return {"SecurityGroups": [{"GroupId": f"sg-{i}"} for i in range(self.groups)]}


def launch(ecs: FakeEcs, ec2: FakeEc2 | None = None) -> str:
    return launch_task(
        cast("Any", ecs), cast("Any", ec2 or FakeEc2()), model_key="sonnet-4-6", command=COMMAND
    )


def test_a_second_task_for_a_model_with_one_running_is_refused() -> None:
    ecs = FakeEcs(running=[task("sonnet-4-6", 1)])
    with pytest.raises(SweepRefusal, match=r"already has a running sweep task \(t1\)"):
        launch(ecs)
    assert ecs.run_kwargs is None  # nothing was started


def test_a_task_for_another_model_does_not_block() -> None:
    ecs = FakeEcs(running=[task("nova-pro", 1)])
    assert launch(ecs).endswith("/t9")
    assert ecs.run_kwargs is not None


def test_the_task_runs_the_explicit_revision_on_fargate_with_the_command_override() -> None:
    ecs = FakeEcs()
    launch(ecs)
    kwargs = ecs.run_kwargs
    assert kwargs is not None
    assert (
        kwargs["taskDefinition"] == TASK_DEF
    )  # the revision's own ARN, which the IAM resource names
    assert (kwargs["cluster"], kwargs["launchType"], kwargs["count"]) == (
        "horizon-compact",
        "FARGATE",
        1,
    )
    assert kwargs["overrides"] == {"containerOverrides": [{"name": "sweep", "command": COMMAND}]}
    network = kwargs["networkConfiguration"]["awsvpcConfiguration"]
    assert network == {
        "subnets": ["subnet-0", "subnet-1"],
        "securityGroups": ["sg-0"],
        "assignPublicIp": "ENABLED",
    }


def test_a_run_task_failure_is_reported() -> None:
    with pytest.raises(SweepRefusal, match="did not start a task"):
        launch(FakeEcs(failures=[{"reason": "CAPACITY"}]))


@pytest.mark.parametrize(("subnets", "groups"), [(0, 1), (2, 0), (2, 2)])
def test_a_missing_network_is_refused_before_run_task(subnets: int, groups: int) -> None:
    ecs = FakeEcs()
    with pytest.raises(SweepRefusal, match="has `main` been deployed"):
        launch(ecs, FakeEc2(subnets, groups))
    assert ecs.run_kwargs is None


def test_running_tasks_reads_the_model_from_the_command_override() -> None:
    ecs = FakeEcs(running=[task("sonnet-4-6", 1), task("nova-pro", 2)])
    assert running_tasks(cast("Any", ecs), "nova-pro") == [ecs.running[1]["taskArn"]]
    assert running_tasks(cast("Any", FakeEcs()), "nova-pro") == []


def test_stop_stops_only_that_models_tasks() -> None:
    ecs = FakeEcs(running=[task("sonnet-4-6", 1), task("nova-pro", 2)])
    assert stop_tasks(cast("Any", ecs), "sonnet-4-6") == [ecs.running[0]["taskArn"]]
    assert ecs.stopped == [ecs.running[0]["taskArn"]]
    assert stop_tasks(cast("Any", FakeEcs()), "sonnet-4-6") == []
