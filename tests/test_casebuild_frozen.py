"""The extraction inputs must be committed and pushed before a real document is fetched (protocol §12.6),
and the hand-boundaries file (search-half IMPLEMENTATION doc §4.5). A fake git throughout: no repository
is read."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from pathlib import Path

import pytest

from horizon_compact.casebuild.extract import instructions_sha256
from horizon_compact.casebuild.frozen import FROZEN_FILES, FrozenInputsError, frozen_inputs
from horizon_compact.casebuild.handfile import HandFileError, load_hand_boundaries

COMMIT = "a" * 40


def fake_git(
    *, status: str = "", commit: str = COMMIT, remotes: str = "  origin/main\n"
) -> list[list[str]]:
    """Returns the calls so a test can read them; the function itself is ``run``."""
    calls: list[list[str]] = []

    def run(args: Sequence[str]) -> str:
        calls.append(list(args))
        return {"status": status, "log": commit + "\n" if commit else "", "branch": remotes}[
            args[0]
        ]

    run.calls = calls  # type: ignore[attr-defined]
    return run  # type: ignore[return-value]


def test_clean_and_pushed_inputs_return_the_commit_and_the_instructions_hash() -> None:
    git = fake_git()
    got = frozen_inputs(git)  # type: ignore[arg-type]
    assert got["extraction_inputs_commit"] == COMMIT
    assert got["extraction_inputs_files"] == list(FROZEN_FILES)
    assert got["instructions_sha256"] == instructions_sha256()
    assert ["branch", "-r", "--contains", COMMIT] in git.calls  # type: ignore[attr-defined]


def test_the_frozen_files_are_the_instructions_and_the_models_entry() -> None:
    assert FROZEN_FILES == ("src/horizon_compact/casebuild/extract.py", "experiment/models.toml")
    root = Path(__file__).resolve().parents[1]
    assert all((root / name).is_file() for name in FROZEN_FILES)


@pytest.mark.parametrize(
    ("kwargs", "words"),
    [
        ({"status": " M experiment/models.toml\n"}, "uncommitted"),
        ({"status": "?? src/horizon_compact/casebuild/extract.py\n"}, "uncommitted"),
        ({"commit": ""}, "no commit"),
        ({"remotes": ""}, "not on any remote branch"),
    ],
)
def test_it_refuses_uncommitted_unknown_or_unpushed_inputs(
    kwargs: dict[str, str], words: str
) -> None:
    with pytest.raises(FrozenInputsError, match=words):
        frozen_inputs(fake_git(**kwargs))  # type: ignore[arg-type]


# --- the hand-boundaries file ------------------------------------------------------------------------------

ACCESSION = "0009999999-26-000001"


def test_no_file_means_no_hand_boundaries(tmp_path: Path) -> None:
    assert load_hand_boundaries(tmp_path / "hand-boundaries.json") == ({}, None)


def test_a_good_file_loads_with_its_hash(tmp_path: Path) -> None:
    path = tmp_path / "hand-boundaries.json"
    raw = json.dumps({ACCESSION: {"1": [10, 90], "human-capital": [20, 40]}}).encode()
    path.write_bytes(raw)
    bounds, digest = load_hand_boundaries(path)
    assert bounds == {ACCESSION: {"1": (10, 90), "human-capital": (20, 40)}}
    assert digest == hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize(
    "content",
    [
        "not json",
        "[]",
        "{}",
        json.dumps({"not-an-accession": {"1": [1, 2]}}),
        json.dumps({ACCESSION: {}}),
        json.dumps({ACCESSION: {"1": [5, 5]}}),
        json.dumps({ACCESSION: {"1": [9, 5]}}),
        json.dumps({ACCESSION: {"1": [-1, 5]}}),
        json.dumps({ACCESSION: {"1": [1, 2, 3]}}),
        json.dumps({ACCESSION: {"1": ["1", "2"]}}),
        json.dumps({ACCESSION: {"1": [True, 5]}}),
        json.dumps({ACCESSION: {" ": [1, 5]}}),
    ],
)
def test_a_malformed_file_is_refused_whole(tmp_path: Path, content: str) -> None:
    path = tmp_path / "hand-boundaries.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(HandFileError):
        load_hand_boundaries(path)
