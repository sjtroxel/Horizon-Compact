"""Where a run is executing (Phase 1 IMPLEMENTATION doc section 6.7)."""

from __future__ import annotations

import json

import pytest

from horizon_compact.sweep.identity import IdentityError, identify

DIGEST = "sha256:" + "cd" * 32
URI = "http://169.254.170.2/v4/abc"


def laptop_git() -> tuple[str, bool]:
    return "feedbeef", True


def metadata(**container: object) -> bytes:
    return json.dumps(
        {
            "TaskARN": "arn:aws:ecs:us-east-1:123456789012:task/horizon-compact/t1",
            "Containers": [
                {"Name": "sweep", "Image": "repo:tag", "ImageID": f"repo@{DIGEST}", **container}
            ],
        }
    ).encode()


def test_no_metadata_means_a_laptop_run_with_no_digest() -> None:
    who = identify({}, laptop_git)
    assert (who.runner, who.image_digest, who.task_arn) == ("laptop", None, None)
    assert (who.git_sha, who.git_dirty, who.in_container) == ("feedbeef", True, False)


def test_a_task_reads_its_digest_from_ecs_not_from_an_environment_variable() -> None:
    env = {
        "ECS_CONTAINER_METADATA_URI_V4": URI,
        "HC_GIT_SHA": "cafe123",
        "HC_IMAGE_DIGEST": "sha256:" + "00" * 32,
    }
    seen: list[str] = []

    def fetch(url: str) -> bytes:
        seen.append(url)
        return metadata()

    who = identify(env, laptop_git, fetch)
    assert seen == [f"{URI}/task"]
    assert who.runner == "fargate"
    assert who.image_digest == DIGEST  # the metadata's, never the environment's
    assert (who.git_sha, who.git_dirty, who.in_container) == ("cafe123", False, True)
    assert who.task_arn is not None


def test_a_fargate_task_without_a_digest_is_an_error_not_a_laptop_run() -> None:
    env = {"ECS_CONTAINER_METADATA_URI_V4": URI}
    with pytest.raises(IdentityError, match="no image digest"):
        identify(env, laptop_git, lambda url: metadata(ImageID="repo:tag"))


def test_a_task_with_no_sweep_container_is_an_error() -> None:
    env = {"ECS_CONTAINER_METADATA_URI_V4": URI}
    with pytest.raises(IdentityError, match="no container named 'sweep'"):
        identify(env, laptop_git, lambda url: json.dumps({"Containers": []}).encode())


def test_unreadable_metadata_is_an_error() -> None:
    env = {"ECS_CONTAINER_METADATA_URI_V4": URI}

    def broken(url: str) -> bytes:
        raise OSError("connection refused")

    with pytest.raises(IdentityError, match="cannot read the task metadata"):
        identify(env, laptop_git, broken)
