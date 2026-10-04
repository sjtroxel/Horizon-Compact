"""Architecture tests: rules about the code's shape that a convention alone would not keep."""

from __future__ import annotations

import ast
import re
import subprocess
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


# --- Terraform rules (Phase 0.5 IMPLEMENTATION doc section 12) ---------------------------------------------

INFRA = ROOT / "infra"
EVIDENCE = ROOT / "docs" / "phases" / "evidence"

# The lock file holds hex hashes that can contain any 12-digit run by chance; .terraform/ is provider cache.
_SKIP_PARTS = {".terraform", ".terraform.lock.hcl"}


def _text_files(base: Path) -> list[Path]:
    """Files under ``base`` that git would track: tracked, or untracked and not ignored.

    Local Terraform state, plans and terraform.tfvars are gitignored and legitimately hold the account id and
    an email address; the rule is about what can reach the public repo.
    """
    if not base.exists():
        return []
    listed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", str(base)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    paths = (ROOT / name for name in listed.split("\0") if name)
    return sorted(
        p for p in paths if p.is_file() and not (_SKIP_PARTS & set(p.relative_to(base).parts))
    )


def _tf_text() -> dict[Path, str]:
    return {p: p.read_text(encoding="utf-8") for p in sorted(INFRA.rglob("*.tf"))}


def _strip_comments(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def test_no_oidc_provider_resource_anywhere_under_infra() -> None:
    """The shared GitHub OIDC provider is looked up, never created (planning/04 section 3.5)."""
    offenders = [
        str(p.relative_to(ROOT))
        for p, text in _tf_text().items()
        if re.search(r'resource\s+"aws_iam_openid_connect_provider"', _strip_comments(text))
    ]
    assert not offenders, f"declares the shared OIDC provider: {offenders}"


def test_bootstrap_looks_the_oidc_provider_up() -> None:
    text = (INFRA / "terraform" / "bootstrap" / "oidc.tf").read_text(encoding="utf-8")
    assert 'data "aws_iam_openid_connect_provider"' in _strip_comments(text)


def test_no_forecasted_budget_notification() -> None:
    """A forecast alert projected $9.17 against $0.001 of spend on 2026-10-02 (planning/04 section 3.3)."""
    offenders = [
        str(p.relative_to(ROOT))
        for p, text in _tf_text().items()
        if "FORECASTED" in _strip_comments(text)
    ]
    assert not offenders, f"FORECASTED notification in: {offenders}"


def test_every_budget_excludes_credits() -> None:
    """Without include_credit = false a budget reads near zero while credits drain."""
    budgets = 0
    for text in _tf_text().values():
        code = _strip_comments(text)
        for block in re.split(r'(?=resource\s+"aws_budgets_budget")', code)[1:]:
            budgets += 1
            assert re.search(r"include_credit\s*=\s*false", block), (
                "budget without include_credit = false"
            )
    assert budgets >= 1, "no aws_budgets_budget found"


def test_deploy_role_has_no_permission_policy() -> None:
    """Phase 0.5 decision 1: trust only. Phase 1 attaches permissions, with a permissions boundary."""
    code = _strip_comments(
        (INFRA / "terraform" / "bootstrap" / "oidc.tf").read_text(encoding="utf-8")
    )
    for resource in ("aws_iam_role_policy", "aws_iam_role_policy_attachment", "aws_iam_policy"):
        assert f'resource "{resource}"' not in code


def test_no_account_id_or_email_in_infra_or_evidence() -> None:
    """Twelve-digit numbers and email addresses stay out of the public repo."""
    account_id = re.compile(r"(?<!\d)\d{12}(?!\d)")
    email = re.compile(r"[\w.+-]+@[\w-]+\.[A-Za-z]{2,}")
    offenders: list[str] = []
    for base in (INFRA, EVIDENCE):
        for path in _text_files(base):
            text = path.read_text(encoding="utf-8")
            if account_id.search(text) or email.search(text):
                offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, f"account id or email address in: {offenders}"


def test_outputs_with_account_ids_are_sensitive() -> None:
    code = _strip_comments(
        (INFRA / "terraform" / "bootstrap" / "outputs.tf").read_text(encoding="utf-8")
    )
    blocks = re.split(r'(?=output\s+")', code)[1:]
    assert blocks
    for block in blocks:
        assert re.search(r"sensitive\s*=\s*true", block), block.splitlines()[0]
