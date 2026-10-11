"""Local settings that must never be written into a tracked file.

Same rule as the name guard's term file: the environment variable first, else local git config, no default.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Callable, Mapping


def git_config_value(key: str) -> str:
    """``git config --get <key>``, or an empty string when unset or git cannot run."""
    try:
        result = subprocess.run(["git", "config", "--get", key], capture_output=True, check=False)
    except OSError:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.decode("utf-8", errors="replace").strip()


def setting(
    env_var: str,
    git_key: str,
    *,
    environ: Mapping[str, str] | None = None,
    git_config: Callable[[str], str] = git_config_value,
) -> str:
    """The environment variable if set and non-blank, else the git config value, else an empty string."""
    env = os.environ if environ is None else environ
    from_env = env.get(env_var, "").strip()
    if from_env:
        return from_env
    return git_config(git_key).strip()
