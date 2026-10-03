"""Architecture tests: rules about the code's shape that a convention alone would not keep."""

from __future__ import annotations

import ast
import sys
import tomllib
from pathlib import Path

import horizon_compact

ROOT = Path(__file__).resolve().parents[1]
PRIVACY = ROOT / "src" / "horizon_compact" / "privacy"


def test_package_version_matches_pyproject() -> None:
    declared = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "version"
    ]
    assert horizon_compact.__version__ == declared


def test_privacy_imports_only_the_standard_library() -> None:
    """The guard must run before any third-party dependency is installed or trusted (Phase 0 §5).

    A third-party import here would also mean a dependency update could silently break the one check
    that protects against an irreversible mistake.
    """
    allowed = set(sys.stdlib_module_names) | {"__future__", "horizon_compact"}
    offenders: list[str] = []
    for path in sorted(PRIVACY.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            else:
                continue
            offenders.extend(
                f"{path.name}:{node.lineno} {name}"
                for name in names
                if name.split(".")[0] not in allowed
            )
    assert not offenders, f"non-standard-library imports in privacy/: {offenders}"


def test_privacy_package_exists_and_documents_its_contract() -> None:
    from horizon_compact import privacy
    from horizon_compact.privacy import guard, names

    for module in (privacy, guard, names):
        assert module.__doc__
