"""The frozen code sets (Phase 3.5 IMPLEMENTATION doc sections 5.1-5.2, build step 3).

The real repository's sets are pinned file by file, so a pattern edit or a renamed file shows up here as a
test change, not as a quietly smaller frozen set. The listing rules (bytecode never, untracked never in a
checkout, the pattern alone in the container) are proven on synthetic trees.
"""

from __future__ import annotations

import ast
import hashlib
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from horizon_compact.protocol import sets
from horizon_compact.protocol.sets import (
    FROZEN_SETS,
    SET_NAMES,
    SetError,
    file_sha256,
    list_set,
    package_files,
    set_of,
    set_sha256,
    tracked_files,
    unmatched_patterns,
)

ROOT = Path(__file__).resolve().parents[1]
PKG = "src/horizon_compact"


def git(*args: str, cwd: Path) -> None:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True, env=env)


def write(root: Path, path: str, text: str = "x = 1\n") -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def garden_tree(root: Path) -> None:
    """A package with one file in each set, bytecode beside them, and nothing else."""
    for path in (
        f"{PKG}/__init__.py",
        f"{PKG}/experiment.py",
        f"{PKG}/model_config.py",
        f"{PKG}/sweep/prompt.py",
        f"{PKG}/sweep/decision.py",
        f"{PKG}/sweep/classify.py",
        f"{PKG}/sweep/runner.py",
        f"{PKG}/analysis/__init__.py",
        f"{PKG}/analysis/verdict.py",
        f"{PKG}/analysis/matcher_thresholds.toml",
    ):
        write(root, path)
    (root / f"{PKG}/analysis/__pycache__").mkdir()
    (root / f"{PKG}/analysis/__pycache__/verdict.cpython-313.pyc").write_bytes(b"\0bytecode")
    (root / f"{PKG}/sweep/stray.pyc").write_bytes(b"\0bytecode")


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    root = tmp_path / "checkout"
    garden_tree(root)
    git("init", "-q", "-b", "main", cwd=root)
    git("add", "--", PKG, cwd=root)
    # Created after `git add`: on disk, never tracked.
    write(root, f"{PKG}/analysis/scratch.py")
    write(root, f"{PKG}/sweep/notes.py")
    return root


# --- the real repository ------------------------------------------------------------------------------------


def test_the_instrument_set_is_exactly_the_prompt_the_validation_and_the_classification() -> None:
    assert list_set(ROOT, "instrument") == (
        f"{PKG}/sweep/classify.py",
        f"{PKG}/sweep/decision.py",
        f"{PKG}/sweep/prompt.py",
    )


def test_the_analysis_set_is_every_tracked_file_in_analysis_and_the_loader() -> None:
    in_analysis = sorted(
        p.relative_to(ROOT).as_posix()
        for p in (ROOT / PKG / "analysis").rglob("*")
        if p.is_file() and not sets.is_bytecode(p.relative_to(ROOT).as_posix())
    )
    tracked = tracked_files(ROOT)
    assert tracked is not None
    expected = sorted([*(p for p in in_analysis if p in tracked), f"{PKG}/experiment.py"])
    assert list(list_set(ROOT, "analysis")) == expected
    assert f"{PKG}/analysis/matcher_thresholds.toml" in expected
    assert f"{PKG}/analysis/__init__.py" in expected


def test_the_run_files_named_in_the_doc_are_run_code() -> None:
    for path in (
        "model_config.py",
        "cli.py",
        "sweep/runner.py",
        "sweep/plan.py",
        "sweep/launch.py",
        "sweep/pacing.py",
        "sweep/spend.py",
        "sweep/store.py",
        "providers/base.py",
        "providers/bedrock.py",
        "protocol/sets.py",
        "simulation/runner.py",
    ):
        assert set_of(f"{PKG}/{path}") == "run", path


def test_every_package_file_is_in_exactly_one_set() -> None:
    files = package_files(ROOT)
    listed = {name: set(list_set(ROOT, name)) for name in SET_NAMES}
    for a in SET_NAMES:
        for b in SET_NAMES:
            if a < b:
                assert not listed[a] & listed[b], (a, b)
    assert set().union(*listed.values()) == set(files)


def test_every_frozen_pattern_matches_a_file() -> None:
    assert unmatched_patterns(ROOT) == ()


def test_no_bytecode_is_listed_even_where_it_sits_on_disk() -> None:
    files = package_files(ROOT)
    assert files
    assert not [p for p in files if "__pycache__" in p or p.endswith(".pyc")]


def _module_path(module: str) -> str | None:
    """The repo-relative file a ``horizon_compact`` module lives in, or None for anything else."""
    if module != "horizon_compact" and not module.startswith("horizon_compact."):
        return None
    base = "src/" + module.replace(".", "/")
    for candidate in (f"{base}.py", f"{base}/__init__.py"):
        if (ROOT / candidate).is_file():
            return candidate
    raise AssertionError(f"cannot find module {module}")


def test_frozen_code_reaches_run_code_only_through_the_known_seams() -> None:
    """A frozen file that imports run code can have its behavior changed by a run fix after the tag.

    The two allowed are deliberate: ``providers/base.py`` holds the seam's data types (``ToolSpec``,
    ``RawDecision``), and ``model_config.py`` is what ``experiment.py`` loads ``models.toml`` with
    (section 5.1).
    Any new one fails here and is decided, not slipped in.
    """
    allowed = {f"{PKG}/providers/base.py", f"{PKG}/model_config.py"}
    offenders: list[str] = []
    for name in FROZEN_SETS:
        for path in list_set(ROOT, name):
            if not path.endswith(".py"):
                continue
            tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.level:
                    offenders.append(f"{path}:{node.lineno} relative import")
                    continue
                if isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    modules = [node.module]
                else:
                    continue
                for module in modules:
                    target = _module_path(module)
                    if target and set_of(target) == "run" and target not in allowed:
                        offenders.append(f"{path}:{node.lineno} {module}")
    assert not offenders, offenders


# --- set_of -------------------------------------------------------------------------------------------------


def test_set_of_refuses_what_is_not_a_package_source_file() -> None:
    for path in (
        "tests/test_protocol_sets.py",
        "src/horizon_compact_extra/sweep/prompt.py",
        f"{PKG}/analysis/__pycache__/verdict.cpython-313.pyc",
        f"{PKG}/sweep/prompt.pyc",
    ):
        with pytest.raises(ValueError):
            set_of(path)


def test_set_of_puts_a_new_analysis_subpackage_in_the_analysis_set() -> None:
    assert set_of(f"{PKG}/analysis/extra/new.py") == "analysis"
    assert set_of(f"{PKG}/sweep/prompt_helpers.py") == "run"
    assert set_of(f"{PKG}/analysis_notes.py") == "run"


# --- listing on synthetic trees -----------------------------------------------------------------------------


def test_a_checkout_lists_tracked_files_only_and_never_bytecode(checkout: Path) -> None:
    assert list_set(checkout, "instrument") == (
        f"{PKG}/sweep/classify.py",
        f"{PKG}/sweep/decision.py",
        f"{PKG}/sweep/prompt.py",
    )
    assert list_set(checkout, "analysis") == (
        f"{PKG}/analysis/__init__.py",
        f"{PKG}/analysis/matcher_thresholds.toml",
        f"{PKG}/analysis/verdict.py",
        f"{PKG}/experiment.py",
    )
    assert list_set(checkout, "run") == (
        f"{PKG}/__init__.py",
        f"{PKG}/model_config.py",
        f"{PKG}/sweep/runner.py",
    )


def test_without_git_the_pattern_alone_lists_the_tree_as_the_container_does(
    checkout: Path, tmp_path: Path
) -> None:
    copied = tmp_path / "app"
    shutil.copytree(checkout / "src", copied / "src")
    assert not (copied / ".git").exists()
    assert tracked_files(copied) is None
    assert f"{PKG}/analysis/scratch.py" in list_set(copied, "analysis")
    assert f"{PKG}/sweep/notes.py" in list_set(copied, "run")
    assert not [p for p in package_files(copied) if sets.is_bytecode(p)]


def test_a_clean_copy_hashes_the_same_as_the_checkout_it_came_from(
    checkout: Path, tmp_path: Path
) -> None:
    (checkout / f"{PKG}/analysis/scratch.py").unlink()
    (checkout / f"{PKG}/sweep/notes.py").unlink()
    copied = tmp_path / "app"
    shutil.copytree(checkout / "src", copied / "src")
    for name in FROZEN_SETS:
        assert list_set(copied, name) == list_set(checkout, name)
        assert set_sha256(copied, list_set(copied, name)) == set_sha256(
            checkout, list_set(checkout, name)
        )


def test_a_tracked_file_missing_on_disk_drops_out_of_its_set(checkout: Path) -> None:
    (checkout / f"{PKG}/sweep/classify.py").unlink()
    assert f"{PKG}/sweep/classify.py" not in list_set(checkout, "instrument")
    assert unmatched_patterns(checkout) == (f"{PKG}/sweep/classify.py",)


def test_a_redirecting_git_variable_does_not_change_the_listing(
    checkout: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    other = tmp_path / "other"
    other.mkdir()
    git("init", "-q", "-b", "main", cwd=other)
    before = package_files(checkout)
    monkeypatch.setenv("GIT_DIR", str(other / ".git"))
    assert package_files(checkout) == before


def test_a_checkout_whose_git_cannot_answer_is_an_error_not_an_unfiltered_list(
    checkout: Path,
) -> None:
    shutil.rmtree(checkout / ".git")
    (checkout / ".git").write_text("gitdir: /nowhere/at/all\n", encoding="utf-8")
    with pytest.raises(SetError, match="git ls-files failed"):
        package_files(checkout)


def test_an_empty_frozen_set_is_an_error(tmp_path: Path) -> None:
    write(tmp_path, f"{PKG}/sweep/runner.py")
    with pytest.raises(SetError, match="instrument set is empty"):
        list_set(tmp_path, "instrument")
    assert list_set(tmp_path, "run") == (f"{PKG}/sweep/runner.py",)


def test_a_root_without_the_package_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(SetError, match="no src/horizon_compact/"):
        package_files(tmp_path)


# --- hashing ------------------------------------------------------------------------------------------------


def test_the_hash_is_path_zero_bytes_zero_in_sorted_path_order(tmp_path: Path) -> None:
    write(tmp_path, "b/z.py", "zed\n")
    write(tmp_path, "a/y.py", "why\n")
    expected = hashlib.sha256(b"a/y.py\0why\n\0b/z.py\0zed\n\0").hexdigest()
    assert set_sha256(tmp_path, ["b/z.py", "a/y.py"]) == expected
    assert set_sha256(tmp_path, ["a/y.py", "b/z.py"]) == expected
    assert file_sha256(tmp_path, "a/y.py") == hashlib.sha256(b"why\n").hexdigest()


def test_the_hash_changes_with_one_byte_and_with_a_rename(checkout: Path) -> None:
    files = list_set(checkout, "instrument")
    before = set_sha256(checkout, files)
    write(checkout, f"{PKG}/sweep/decision.py", "x = 2\n")
    assert set_sha256(checkout, files) != before
    write(checkout, f"{PKG}/sweep/decision.py")
    assert set_sha256(checkout, files) == before
    renamed = [p.replace("decision.py", "decisions.py") for p in files]
    (checkout / f"{PKG}/sweep/decision.py").rename(checkout / f"{PKG}/sweep/decisions.py")
    assert set_sha256(checkout, renamed) != before


def test_swapping_two_files_contents_changes_the_hash(tmp_path: Path) -> None:
    """Each file's bytes are bound to its path, so the same bytes under other names are a different set."""
    write(tmp_path, "a.py", "one\n")
    write(tmp_path, "b.py", "two\n")
    first = set_sha256(tmp_path, ["a.py", "b.py"])
    write(tmp_path, "a.py", "two\n")
    write(tmp_path, "b.py", "one\n")
    assert set_sha256(tmp_path, ["a.py", "b.py"]) != first
