"""Claude cannot run any command that reads a pilot or official record (Phase 4 runs half section 5.4): the
project's ``.claude/settings.json`` denies each, in both the ``uv run hc`` and ``uv run --no-sync hc`` forms.
Nothing here runs a command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

SETTINGS = Path(__file__).resolve().parents[1] / ".claude" / "settings.json"
READERS = (
    "analyze",
    "sweep report",
    "sweep awareness",
    "sweep refusals",
    "sweep tokens",  # token counts by objective: a view of the results, his to run at the reveal
    "protocol repeats",
    "protocol records",
)
FORMS = ("uv run hc", "uv run --no-sync hc")


def settings() -> dict[str, dict[str, list[str]]]:
    data: dict[str, dict[str, list[str]]] = json.loads(SETTINGS.read_text(encoding="utf-8"))
    return data


@pytest.mark.parametrize("form", FORMS)
@pytest.mark.parametrize("command", READERS)
def test_every_command_that_reads_a_record_is_denied(form: str, command: str) -> None:
    assert f"Bash({form} {command}*)" in settings()["permissions"]["deny"]


def test_a_reader_is_never_also_allowed() -> None:
    allowed = " ".join(settings()["permissions"]["allow"])
    for command in READERS:
        assert f"hc {command}" not in allowed


def test_the_earlier_denials_still_stand() -> None:
    deny = settings()["permissions"]["deny"]
    for needle in (
        "git commit*",
        "git push*",
        "aws *",
        "hc sweep run*",
        "hc sweep launch*",
        "hc sweep status*",
    ):
        assert any(needle in entry for entry in deny), needle
