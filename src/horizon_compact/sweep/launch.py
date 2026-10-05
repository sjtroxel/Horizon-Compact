"""Start and stop a sweep's Fargate task from the laptop (Phase 1 IMPLEMENTATION doc sections 9 and 10.5).

One task per model: a second sweep on a model that already has a running task is refused, because tasks
share the model's account-wide request quota. A task's model is read from the ``--model`` in its command
override, so no tagging permission is needed. CI never launches a sweep, and the deploy role is denied
``ecs:RunTask``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from horizon_compact.sweep.plan import SweepRefusal

if TYPE_CHECKING:
    from mypy_boto3_ec2 import EC2Client
    from mypy_boto3_ecs import ECSClient

CLUSTER = "horizon-compact"
FAMILY = "horizon-compact-sweep"
CONTAINER = "sweep"
SECURITY_GROUP = "horizon-compact-sweep"
STARTED_BY = "hc-sweep-launch"


def _model_of(task: dict[str, Any]) -> str | None:
    """The ``--model`` value in the task's container command override, if it has one."""
    for override in (task.get("overrides") or {}).get("containerOverrides", []):
        command = override.get("command") or []
        if "--model" in command and command.index("--model") + 1 < len(command):
            return str(command[command.index("--model") + 1])
    return None


def running_tasks(ecs: ECSClient, model_key: str) -> list[str]:
    """ARNs of this model's pending or running sweep tasks."""
    arns = ecs.list_tasks(cluster=CLUSTER, family=FAMILY, desiredStatus="RUNNING").get(
        "taskArns", []
    )
    if not arns:
        return []
    described = ecs.describe_tasks(cluster=CLUSTER, tasks=arns).get("tasks", [])
    return [str(t["taskArn"]) for t in described if _model_of(dict(t)) == model_key]


def _network(ec2: EC2Client) -> dict[str, Any]:
    subnets = ec2.describe_subnets(
        Filters=[
            {"Name": "tag:Tier", "Values": ["public"]},
            {"Name": "tag:Project", "Values": ["horizon-compact"]},
        ]
    ).get("Subnets", [])
    groups = ec2.describe_security_groups(
        Filters=[{"Name": "group-name", "Values": [SECURITY_GROUP]}]
    ).get("SecurityGroups", [])
    if not subnets or len(groups) != 1:
        raise SweepRefusal(
            f"expected public subnets and one security group named {SECURITY_GROUP!r}; found "
            f"{len(subnets)} subnets and {len(groups)} groups (has `main` been deployed?)"
        )
    return {
        "awsvpcConfiguration": {
            "subnets": [str(s["SubnetId"]) for s in subnets],
            "securityGroups": [str(groups[0]["GroupId"])],
            "assignPublicIp": "ENABLED",
        }
    }


def launch_task(ecs: ECSClient, ec2: EC2Client, *, model_key: str, command: list[str]) -> str:
    """Run one sweep task. Refuses a second task for the same model. Returns the task ARN."""
    already = running_tasks(ecs, model_key)
    if already:
        raise SweepRefusal(
            f"{model_key} already has a running sweep task ({already[0].rsplit('/', 1)[-1]}); "
            "tasks share the model's request quota. Stop it first, or wait."
        )
    # Run the explicit revision, so the IAM resource is the task definition's own ARN.
    definition = ecs.describe_task_definition(taskDefinition=FAMILY)["taskDefinition"]
    response = ecs.run_task(
        cluster=CLUSTER,
        taskDefinition=str(definition["taskDefinitionArn"]),
        launchType="FARGATE",
        count=1,
        startedBy=STARTED_BY,
        networkConfiguration=_network(ec2),  # type: ignore[arg-type]
        overrides={"containerOverrides": [{"name": CONTAINER, "command": command}]},
    )
    failures = response.get("failures", [])
    tasks = response.get("tasks", [])
    if failures or len(tasks) != 1:
        raise SweepRefusal(f"RunTask did not start a task: {failures or 'no task returned'}")
    return str(tasks[0]["taskArn"])


def stop_tasks(ecs: ECSClient, model_key: str, reason: str = "hc sweep stop") -> list[str]:
    """Stop this model's running sweep task(s). The task gets SIGTERM, stops between attempts and writes its
    summary."""
    stopped = running_tasks(ecs, model_key)
    for arn in stopped:
        ecs.stop_task(cluster=CLUSTER, task=arn, reason=reason)
    return stopped
