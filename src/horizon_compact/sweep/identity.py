"""Where a run is executing (Phase 1 IMPLEMENTATION doc section 6.7, section 3 finding 5).

Inside a Fargate task the image digest comes from ECS itself: task metadata v4's ``ImageID`` is the SHA-256
digest of the image manifest. Recording it from inside the task, not from an environment variable CI wrote,
means the record cannot claim a digest the task did not run. **A result without a digest is a laptop run**,
and a test proves it. A Fargate run whose metadata has no digest is an error, never quietly relabeled as a
laptop run.
"""

from __future__ import annotations

import json
import re
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Literal

METADATA_URI_ENV = "ECS_CONTAINER_METADATA_URI_V4"
GIT_SHA_ENV = "HC_GIT_SHA"
CONTAINER_NAME = "sweep"
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")


class IdentityError(Exception):
    """The task metadata did not say what image is running."""


@dataclass(frozen=True)
class RunnerIdentity:
    runner: Literal["fargate", "laptop"]
    image_digest: str | None
    image: str | None
    task_arn: str | None
    git_sha: str
    git_dirty: bool | None

    @property
    def in_container(self) -> bool:
        return self.runner == "fargate" and self.image_digest is not None


def _http_get(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=5) as response:
        return bytes(response.read())


def identify(
    env: Mapping[str, str],
    laptop_git: Callable[[], tuple[str, bool]],
    fetch: Callable[[str], bytes] = _http_get,
) -> RunnerIdentity:
    base = env.get(METADATA_URI_ENV)
    if not base:
        sha, dirty = laptop_git()
        return RunnerIdentity("laptop", None, None, None, sha, dirty)
    try:
        task = json.loads(fetch(f"{base}/task"))
    except (OSError, ValueError) as exc:
        raise IdentityError(f"cannot read the task metadata: {exc}") from exc
    container = next(
        (c for c in task.get("Containers", []) if c.get("Name") == CONTAINER_NAME), None
    )
    if container is None:
        raise IdentityError(f"the task metadata has no container named {CONTAINER_NAME!r}")
    match = _DIGEST.search(str(container.get("ImageID", "")))
    if match is None:
        raise IdentityError("the task metadata has no image digest (ImageID)")
    return RunnerIdentity(
        runner="fargate",
        image_digest=match.group(0),
        image=container.get("Image"),
        task_arn=task.get("TaskARN"),
        git_sha=env.get(GIT_SHA_ENV, "unknown"),
        git_dirty=False,
    )
