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
    account_id = re.compile(r"(?<![\w-])\d{12}(?![\w-])")
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


# --- the harness (Phase 1 IMPLEMENTATION doc section 13, "architecture") -----------------------------------

_SAMPLING_KEYS = {"temperature", "topP", "top_p", "top_k"}


def test_no_sampling_parameter_can_be_built_into_a_request() -> None:
    """Sampling parameters are never set, so none can be sent (planning/07 section 2.3)."""
    import dataclasses

    from horizon_compact.providers.base import DecisionRequest

    assert not _SAMPLING_KEYS & {f.name for f in dataclasses.fields(DecisionRequest)}
    offenders: list[str] = []
    for path in sorted((ROOT / "src" / "horizon_compact" / "providers").glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Dict):
                offenders.extend(
                    f"{path.name}:{key.lineno} {key.value}"
                    for key in node.keys
                    if isinstance(key, ast.Constant) and key.value in _SAMPLING_KEYS
                )
    assert not offenders, f"a sampling key in a provider dict: {offenders}"


def test_the_experiment_folder_has_no_account_id_or_email() -> None:
    """experiment/ is built into a public image and committed; nothing private belongs in it."""
    account_id = re.compile(r"(?<![\w-])\d{12}(?![\w-])")
    email = re.compile(r"[\w.+-]+@[\w-]+\.[A-Za-z]{2,}")
    offenders = [
        str(p.relative_to(ROOT))
        for p in _text_files(ROOT / "experiment")
        if account_id.search(p.read_text(encoding="utf-8"))
        or email.search(p.read_text(encoding="utf-8"))
    ]
    assert not offenders, f"account id or email address in: {offenders}"


# --- IAM and storage rules (Phase 1 IMPLEMENTATION doc sections 8 and 10) ----------------------------------

IAM = INFRA / "iam"
BOOTSTRAP = INFRA / "terraform" / "bootstrap"

# Fictional values with the real shape and length, so a rendered policy's size is measured, not guessed.
_FAKE_VARS = {
    "account_id": "000000000000",
    "region": "us-east-1",
    "state_bucket": "horizon-compact-tfstate-000000000000",
    "results_bucket": "horizon-compact-results-000000000000",
    "ecr_repository_arn": "arn:aws:ecr:us-east-1:000000000000:repository/horizon-compact",
    "boundary_arn": "arn:aws:iam::000000000000:policy/horizon-compact-boundary",
    "sonnet_profile_arn": (
        "arn:aws:bedrock:us-east-1:000000000000:application-inference-profile/abcdefghijkl"
    ),
    "nova_pro_profile_arn": (
        "arn:aws:bedrock:us-east-1:000000000000:application-inference-profile/mnopqrstuvwx"
    ),
    # main passes a JSON list here (jsonencode); a plain substitution is enough to parse the template.
    "bedrock_resources": (
        '["arn:aws:bedrock:us-east-1:000000000000:application-inference-profile/abcdefghijkl",'
        '"arn:aws:bedrock:*::foundation-model/anthropic.claude-sonnet-4-6*"]'
    ),
}
_MANAGED_POLICY_LIMIT = 6144


def _rendered(name: str) -> tuple[str, dict[str, object]]:
    import json
    from string import Template

    text = Template((IAM / name).read_text(encoding="utf-8")).substitute(_FAKE_VARS)
    return text, json.loads(text)


def _statements(name: str) -> list[dict[str, object]]:
    statements = _rendered(name)[1]["Statement"]
    assert isinstance(statements, list)
    return statements


def _as_list(value: object) -> list[str]:
    return [value] if isinstance(value, str) else list(value)  # type: ignore[call-overload]


def _actions(statement: dict[str, object]) -> list[str]:
    return _as_list(statement["Action"])


def _allowed_actions(name: str) -> list[str]:
    return [a for s in _statements(name) if s["Effect"] == "Allow" for a in _actions(s)]


def test_iam_templates_render_to_json_and_fit_a_managed_policy() -> None:
    for name in ("boundary.json", "deploy.json"):
        text, _ = _rendered(name)
        size = len("".join(text.split()))
        assert size < _MANAGED_POLICY_LIMIT, f"{name} renders to {size} non-space characters"


def test_boundary_grants_no_iam_and_no_s3_delete() -> None:
    allowed = _allowed_actions("boundary.json")
    assert not [a for a in allowed if a.startswith("iam:") or a == "*"]
    assert not [a for a in allowed if a.startswith("s3:Delete") or a in {"s3:*", "s3:Put*"}]


def test_deploy_policy_has_no_wildcard_allow_of_a_whole_service() -> None:
    allowed = _allowed_actions("deploy.json")
    assert not [a for a in allowed if a == "*" or a.endswith(":*")]


def test_every_deploy_iam_write_on_roles_carries_the_boundary_condition() -> None:
    """The deploy role may create a role only with the boundary on it (planning/04, Phase 1 section 10.4)."""
    found = False
    for s in _statements("deploy.json"):
        if s["Effect"] == "Allow" and "iam:CreateRole" in _actions(s):
            found = True
            condition = s["Condition"]
            assert isinstance(condition, dict)
            assert (
                condition["StringEquals"]["iam:PermissionsBoundary"] == _FAKE_VARS["boundary_arn"]
            )
    assert found


def test_deploy_policy_denies_what_ci_must_never_do() -> None:
    denied: dict[str, list[str]] = {}
    for s in _statements("deploy.json"):
        if s["Effect"] == "Deny":
            denied[str(s["Sid"])] = _actions(s)
    assert {"ecs:RunTask", "bedrock:InvokeModel*", "bedrock:Converse*"} <= set(
        denied["CiNeverLaunchesASweep"]
    )
    assert "s3:GetObject" in denied["CiNeverReadsRawResults"]
    assert denied["NeverChangeOwnPermissions"] == ["iam:*"]
    assert denied["NeverRemoveBoundary"] == ["iam:DeleteRolePermissionsBoundary"]


def test_deploy_policy_can_write_state_only_under_main() -> None:
    for s in _statements("deploy.json"):
        if s["Sid"] == "StateMainKey":
            assert _as_list(s["Resource"]) == [f"arn:aws:s3:::{_FAKE_VARS['state_bucket']}/main/*"]


def test_dev_policy_keeps_its_explicit_denies() -> None:
    import json

    statements = json.loads((IAM / "horizon-compact-dev-policy.json").read_text(encoding="utf-8"))[
        "Statement"
    ]
    sids = {s["Sid"] for s in statements if s["Effect"] == "Deny"}
    assert {
        "NeverChangeOidcProviders",
        "NeverChangeOtherBudgets",
        "NeverInvokeMusicalMyceliumModels",
    } <= sids


def test_results_bucket_is_write_once_and_cannot_be_destroyed() -> None:
    code = _strip_comments((BOOTSTRAP / "results.tf").read_text(encoding="utf-8"))
    assert re.search(r"prevent_destroy\s*=\s*true", code)
    assert "force_destroy" not in code
    assert "aws_s3_bucket_lifecycle_configuration" not in code
    for needle in (
        "s3:if-none-match",
        "s3:if-match",
        "s3:DeleteObjectVersion",
        "aws:SecureTransport",
    ):
        assert needle in code, needle


def test_ecr_tags_are_immutable_and_scanned() -> None:
    code = _strip_comments((BOOTSTRAP / "ecr.tf").read_text(encoding="utf-8"))
    assert re.search(r'image_tag_mutability\s*=\s*"IMMUTABLE"', code)
    assert re.search(r"scan_on_push\s*=\s*true", code)


# --- the `main` root and the workflows (Phase 1 IMPLEMENTATION doc sections 9, 10 and 12) -----------------

MAIN = INFRA / "terraform" / "main"
WORKFLOWS = ROOT / ".github" / "workflows"


def _main_code() -> str:
    return "\n".join(
        _strip_comments(p.read_text(encoding="utf-8")) for p in sorted(MAIN.glob("*.tf"))
    )


def test_task_and_execution_roles_fit_inside_the_boundary() -> None:
    """Both roles' actions are a subset of the boundary's (a role can never hold more than it)."""
    boundary = set(_allowed_actions("boundary.json"))
    for name in ("task.json", "execution.json"):
        assert set(_allowed_actions(name)) <= boundary, name


def test_task_role_cannot_delete_or_touch_iam() -> None:
    allowed = _allowed_actions("task.json")
    assert not [a for a in allowed if a.startswith(("iam:", "s3:Delete")) or a.endswith(":*")]
    assert set(allowed) == {"bedrock:InvokeModel", "s3:GetObject", "s3:PutObject", "s3:ListBucket"}


def test_every_role_in_main_carries_the_boundary() -> None:
    code = _main_code()
    roles = re.split(r'(?=resource\s+"aws_iam_role"\s)', code)[1:]
    assert len(roles) == 2
    for block in roles:
        assert re.search(r"permissions_boundary\s*=\s*local\.boundary_arn", block), block[:80]


def test_roles_trust_ecs_tasks_for_this_account_only() -> None:
    code = _main_code()
    assert "ecs-tasks.amazonaws.com" in code
    assert "aws:SourceAccount" in code


def test_main_creates_no_always_on_resource() -> None:
    """No NAT gateway, load balancer, database or endpoint (planning/02 section 2.4; CLAUDE.md cost rules)."""
    code = _main_code()
    for resource in (
        "aws_nat_gateway",
        "aws_eip",
        "aws_lb",
        "aws_alb",
        "aws_db_instance",
        "aws_rds_cluster",
        "aws_vpc_endpoint",
        "aws_ecs_service",
    ):
        assert not re.search(rf'resource\s+"{resource}"', code), resource


def test_main_log_group_has_explicit_retention_and_cluster_insights_are_off() -> None:
    code = _main_code()
    assert re.search(r"retention_in_days\s*=\s*30", code)
    assert re.search(r'name\s*=\s*"containerInsights"\s*\n\s*value\s*=\s*"disabled"', code)


def test_sweep_security_group_has_no_ingress_and_only_https_egress() -> None:
    code = _main_code()
    assert not re.search(r"\bingress\b\s*\{", code)
    egress = re.findall(r"egress\s*\{(.*?)\n\s*\}", code, flags=re.DOTALL)
    assert len(egress) == 1
    assert re.search(r"from_port\s*=\s*443", egress[0]) and re.search(
        r"to_port\s*=\s*443", egress[0]
    )


def test_task_definition_is_arm64_and_names_the_image_by_digest() -> None:
    code = _main_code()
    assert re.search(r'cpu_architecture\s*=\s*"ARM64"', code)
    assert "@${var.image_digest}" in code
    assert not re.search(r'image\s*=\s*"[^"]*:latest', code)


def test_main_requires_the_route_and_the_digest_with_no_default() -> None:
    code = (MAIN / "variables.tf").read_text(encoding="utf-8")
    for name in ("image_digest", "sonnet_route"):
        block = re.search(rf'variable\s+"{name}"\s*\{{(.*?)\n\}}', code, flags=re.DOTALL)
        assert block is not None, name
        assert not re.search(r"^\s*default\s*=", block.group(1), flags=re.MULTILINE), name


def test_main_backend_names_no_bucket() -> None:
    """The state bucket's name holds the account id; it arrives at init (-backend-config=bucket=...)."""
    code = _strip_comments((MAIN / "versions.tf").read_text(encoding="utf-8"))
    assert re.search(r'backend\s+"s3"', code)
    assert not re.search(r"\bbucket\s*=", code)
    assert re.search(r"use_lockfile\s*=\s*true", code)


def test_tf_check_covers_both_roots() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "terraform -chdir=$(TF_MAIN) validate" in makefile
    assert "terraform -chdir=$(TF_MAIN) fmt -check" in makefile
    assert (MAIN / ".terraform.lock.hcl").is_file()


def test_deploy_workflow_never_cancels_an_apply_and_builds_one_manifest() -> None:
    text = (WORKFLOWS / "deploy.yml").read_text(encoding="utf-8")
    assert re.search(r"cancel-in-progress:\s*false", text)
    assert re.search(r"provenance:\s*false", text)
    assert "ubuntu-24.04-arm" in text
    assert "mask-aws-account-id: true" in text
    assert "-lockfile=readonly" in text
    assert "ecs run-task" not in text and "sweep launch" not in text


def test_permission_check_covers_the_four_refusals() -> None:
    text = (WORKFLOWS / "aws-permission-check.yml").read_text(encoding="utf-8")
    for needle in (
        "create-role",
        "create-bucket",
        "put-role-policy",
        "run-task",
        "workflow_dispatch",
    ):
        assert needle in text, needle
    assert "push:" not in text


def test_workflows_hold_no_account_id() -> None:
    account_id = re.compile(r"(?<![\w-])\d{12}(?![\w-])")
    offenders = [p.name for p in WORKFLOWS.glob("*.yml") if account_id.search(p.read_text())]
    assert not offenders, offenders


# --- the analysis package (Phase 3 IMPLEMENTATION doc sections 4, 5 and 16) --------------------------------

SRC = ROOT / "src" / "horizon_compact"
ANALYSIS = SRC / "analysis"
ANALYSIS_GROUP_LIBRARIES = {"numpy", "scipy", "statsmodels"}
# Phase 3.5 hashes analysis/ alone, so nothing it needs may live outside it except the scenario loader.
ANALYSIS_MAY_IMPORT_FROM_THE_PACKAGE = {"horizon_compact.experiment"}


def _imports(path: Path, root: Path = SRC.parent) -> list[tuple[int, str]]:
    """Every module a file imports, absolute. A relative import is resolved against the file's package, so
    ``from ..simulation import x`` cannot slip past a rule written for ``horizon_compact.simulation``."""
    package = list(path.relative_to(root).with_suffix("").parts)[:-1]
    found: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                module = node.module or ""
            else:
                base = package[: len(package) - (node.level - 1)]
                module = ".".join(base + ([node.module] if node.module else []))
            if module:
                found.append((node.lineno, module))
            # `from horizon_compact import simulation` names the module in the alias, not in `module`.
            found.extend((node.lineno, f"{module}.{alias.name}") for alias in node.names)
    return found


def test_relative_imports_are_resolved_by_the_import_reader(tmp_path: Path) -> None:
    probe = tmp_path / "horizon_compact" / "analysis" / "probe.py"
    probe.parent.mkdir(parents=True)
    probe.write_text("from ..simulation import x\nfrom . import records\n", encoding="utf-8")
    names = {name for _line, name in _imports(probe, root=tmp_path)}
    assert "horizon_compact.simulation" in names
    assert "horizon_compact.simulation.x" in names
    assert "horizon_compact.analysis.records" in names


def test_analysis_never_imports_simulation() -> None:
    offenders = [
        f"{path.name}:{line} {name}"
        for path in sorted(ANALYSIS.rglob("*.py"))
        for line, name in _imports(path)
        if name == "horizon_compact.simulation" or name.startswith("horizon_compact.simulation.")
    ]
    assert not offenders, f"analysis imports simulation: {offenders}"


def test_analysis_imports_only_itself_the_experiment_loader_and_the_allowed_libraries() -> None:
    allowed_top = set(sys.stdlib_module_names) | {"__future__"} | ANALYSIS_GROUP_LIBRARIES
    offenders: list[str] = []
    for path in sorted(ANALYSIS.rglob("*.py")):
        for line, name in _imports(path):
            top = name.split(".")[0]
            if top == "horizon_compact":
                inside = name == "horizon_compact" or name.startswith("horizon_compact.analysis")
                loader = any(
                    name == ok or name.startswith(ok + ".")
                    for ok in ANALYSIS_MAY_IMPORT_FROM_THE_PACKAGE
                )
                if not (inside or loader):
                    offenders.append(f"{path.name}:{line} {name}")
            elif top not in allowed_top:
                offenders.append(f"{path.name}:{line} {name}")
    assert not offenders, f"analysis imports outside its allowance: {offenders}"


def test_nothing_outside_analysis_and_simulation_imports_the_analysis_libraries() -> None:
    """The container image leaves the analysis group out, so a sweep module that imported numpy would crash
    there. Only analysis/ and the simulation package may import them."""
    homes = {SRC / "analysis", SRC / "simulation"}
    offenders = [
        f"{path.relative_to(SRC)}:{line} {name}"
        for path in sorted(SRC.rglob("*.py"))
        if not any(home in path.parents for home in homes)
        for line, name in _imports(path)
        if name.split(".")[0] in ANALYSIS_GROUP_LIBRARIES
    ]
    assert not offenders, f"analysis-group libraries imported outside their home: {offenders}"


def test_the_image_leaves_the_analysis_group_out() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert set(pyproject["tool"]["uv"]["default-groups"]) == {"dev", "analysis"}
    assert {re.split(r"[<>=]", d)[0] for d in pyproject["dependency-groups"]["analysis"]} == (
        ANALYSIS_GROUP_LIBRARIES
    )
    syncs = [
        line
        for line in (ROOT / "infra" / "docker" / "Dockerfile")
        .read_text(encoding="utf-8")
        .splitlines()
        if "uv sync" in line
    ]
    assert len(syncs) == 2
    for line in syncs:
        assert "--no-default-groups" in line and "--no-dev" not in line, line


def test_the_command_line_imports_the_simulations_only_inside_their_command() -> None:
    """``hc`` is the container image's entry point and the image has no numpy: a module-level import of the
    simulation (or the analysis) in cli.py would crash every command there, sweeps included."""
    tree = ast.parse((SRC / "cli.py").read_text(encoding="utf-8"))
    top_level = [
        node.module if isinstance(node, ast.ImportFrom) else alias.name
        for node in tree.body
        if isinstance(node, ast.Import | ast.ImportFrom)
        for alias in node.names
    ]
    offenders = [
        name
        for name in top_level
        if name
        and (
            name.startswith("horizon_compact.simulation")
            or name.startswith("horizon_compact.analysis")
        )
    ]
    assert not offenders, offenders


def test_analysis_imports_nothing_from_model_config() -> None:
    """The frozen analysis set must not depend on run code (Phase 3.5 IMPLEMENTATION doc section 5.1).

    ``model_config.py`` is a run file that may change after the tag; ``analysis/`` reads scenarios
    through ``experiment.py`` only.
    """
    offenders: list[str] = []
    for path in sorted((ROOT / "src" / "horizon_compact" / "analysis").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                base = "." * node.level + (node.module or "")
                names = [base] + [f"{base}.{alias.name}" for alias in node.names]
            else:
                continue
            offenders.extend(
                f"{path.name}:{node.lineno} {name}" for name in names if "model_config" in name
            )
    assert not offenders, f"analysis/ imports model_config: {offenders}"
