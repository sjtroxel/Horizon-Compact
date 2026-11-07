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
        # The two CloudFront ids hold no account id (checked in test_site_objects_outputs...), so CI
        # reads them as plain repository variables.
        if re.match(
            r'output\s+"(site_origin_access_control_id|site_response_headers_policy_id)"', block
        ):
            continue
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
    # The two bootstrap CloudFront objects' ARNs, which only the site policy reads (iam.tf).
    "origin_access_control_arn": "arn:aws:cloudfront::000000000000:origin-access-control/E1ABCDEFGHIJKL",
    "response_headers_policy_arn": (
        "arn:aws:cloudfront::000000000000:response-headers-policy/abcdef01-2345-6789-abcd-ef0123456789"
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
    # deploy-site.json is an inline role policy, not a managed one, but it is held to the same limit.
    for name in ("boundary.json", "deploy.json", "deploy-site.json"):
        text, _ = _rendered(name)
        size = len("".join(text.split()))
        assert size < _MANAGED_POLICY_LIMIT, f"{name} renders to {size} non-space characters"


def test_dev_policy_fits_a_managed_policy() -> None:
    """He pastes this one into the console; IAM refuses a managed policy over 6,144 non-space characters."""
    text = (IAM / "horizon-compact-dev-policy.json").read_text(encoding="utf-8")
    size = len("".join(text.split()))
    assert size < _MANAGED_POLICY_LIMIT, f"the dev policy is {size} non-space characters"


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


def test_ecr_lifecycle_expires_only_untagged_images() -> None:
    """The records carry image digests, so a tagged image never expires (Phase 1.5 decision 7, KNOWN-GAPS
    OPEN 2026-11-04: the old ten-image rule expired Phase 4's official image)."""
    code = _strip_comments((BOOTSTRAP / "ecr.tf").read_text(encoding="utf-8"))
    assert "imageCountMoreThan" not in code
    assert re.search(r"rulePriority\s*=\s*1\b", code)
    assert not re.search(r"rulePriority\s*=\s*[2-9]", code)
    assert re.search(r'tagStatus\s*=\s*"untagged"', code)
    assert re.search(r'countType\s*=\s*"sinceImagePushed"', code)
    assert re.search(r"countNumber\s*=\s*1\b", code)
    assert 'tagStatus   = "any"' not in code


# --- the site's CloudFront objects and the deploy role's site grants (Phase 1.5 sections 9 and 11) ---------

_ACCESS_CONTROL_AND_HEADERS_POLICY_WRITES = re.compile(
    r"^cloudfront:(Create|Update|Delete|Associate|Disassociate|Copy|Publish)"
    r"(OriginAccessControl|ResponseHeadersPolic)"
)


def test_site_origin_access_control_signs_every_request_to_s3() -> None:
    code = _strip_comments((BOOTSTRAP / "site.tf").read_text(encoding="utf-8"))
    assert 'resource "aws_cloudfront_origin_access_control" "site"' in code
    assert 'name                              = "${var.project}-site"' in code
    assert re.search(r'origin_access_control_origin_type\s*=\s*"s3"', code)
    assert re.search(r'signing_behavior\s*=\s*"always"', code)
    assert re.search(r'signing_protocol\s*=\s*"sigv4"', code)


def test_site_headers_policy_forbids_third_party_requests_and_noindexes_until_go_live() -> None:
    raw = (BOOTSTRAP / "site.tf").read_text(encoding="utf-8")
    code = _strip_comments(raw)
    assert 'resource "aws_cloudfront_response_headers_policy" "site"' in code
    match = re.search(r'content_security_policy\s*=\s*"([^"]+)"', code)
    assert match
    assert match.group(1) == (
        "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
        "font-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'; "
        "frame-ancestors 'none'"
    )
    assert re.search(r"access_control_max_age_sec\s*=\s*63072000", code)
    assert re.search(r"include_subdomains\s*=\s*true", code)
    assert re.search(r'referrer_policy\s*=\s*"no-referrer"', code)
    assert re.search(r'header\s*=\s*"X-Robots-Tag"', code)
    assert re.search(r'value\s*=\s*"noindex"', code)
    # Every header overrides whatever the origin sends, so the policy is the one source of truth.
    assert "override" in code and not re.search(r"override\s*=\s*false", code)
    # The comment says when the noindex header goes (decision 3).
    assert "Phase 6.5" in raw


def test_site_objects_outputs_are_the_two_ids_and_hold_no_account_id() -> None:
    code = _strip_comments((BOOTSTRAP / "outputs.tf").read_text(encoding="utf-8"))
    blocks = {
        re.match(r'output\s+"([^"]+)"', b).group(1): b  # type: ignore[union-attr]
        for b in re.split(r'(?=output\s+")', code)[1:]
    }
    for name, resource in (
        ("site_origin_access_control_id", "aws_cloudfront_origin_access_control.site.id"),
        ("site_response_headers_policy_id", "aws_cloudfront_response_headers_policy.site.id"),
    ):
        assert resource in blocks[name]
        assert "sensitive" not in blocks[name]


def test_site_policy_variables_stay_out_of_the_boundary_and_the_deploy_policy() -> None:
    """The new ARNs are unknown until the objects exist; if the two older policies read them, the plan would
    show both as changed."""
    code = _strip_comments((BOOTSTRAP / "iam.tf").read_text(encoding="utf-8"))
    base = code[code.index("policy_vars = {") : code.index("}", code.index("policy_vars = {"))]
    assert "cloudfront" not in base
    assert (
        'templatefile("${path.module}/../../iam/deploy-site.json", local.site_policy_vars)' in code
    )
    for name in ("boundary.json", "deploy.json"):
        assert f'iam/{name}", local.policy_vars)' in code


def test_deploy_policies_name_the_site_grants_exactly() -> None:
    by_sid = {str(s["Sid"]): s for s in _statements("deploy-site.json")}
    assert list(by_sid) == [
        "SiteBucket",
        "SiteDistributionCreate",
        "SiteDistributionManage",
        "SiteDistributionReadAfterDelete",
        "SiteRead",
        "SiteReadOriginAccessControl",
        "SiteReadResponseHeadersPolicy",
        "NeverRetagAnotherProjectsDistribution",
    ]
    assert [sid for sid, s in by_sid.items() if s["Effect"] != "Allow"] == [
        "NeverRetagAnotherProjectsDistribution"
    ]

    bucket = by_sid["SiteBucket"]
    assert _actions(bucket) == ["s3:*"]
    assert _as_list(bucket["Resource"]) == [
        "arn:aws:s3:::horizon-compact-site-*",
        "arn:aws:s3:::horizon-compact-site-*/*",
    ]

    create = by_sid["SiteDistributionCreate"]
    assert _actions(create) == ["cloudfront:CreateDistribution", "cloudfront:TagResource"]
    assert create["Resource"] == "*"
    assert create["Condition"] == {"StringEquals": {"aws:RequestTag/Project": "horizon-compact"}}

    manage = by_sid["SiteDistributionManage"]
    assert sorted(_actions(manage)) == sorted(
        f"cloudfront:{a}"
        for a in (
            "GetDistributionConfig",
            "UpdateDistribution",
            "DeleteDistribution",
            "CreateInvalidation",
            "GetInvalidation",
            "ListTagsForResource",
            "TagResource",
            "UntagResource",
        )
    )
    assert manage["Resource"] == "arn:aws:cloudfront::000000000000:distribution/*"
    assert manage["Condition"] == {"StringEquals": {"aws:ResourceTag/Project": "horizon-compact"}}

    # A deleted distribution has no tags, so a tag-conditioned GetDistribution is denied rather than
    # answered "no such distribution", and Terraform's delete waiter and refresh stop on it (the teardown
    # test, 2026-11-07). The read alone is unconditioned; every write stays fenced by tag above.
    after_delete = by_sid["SiteDistributionReadAfterDelete"]
    assert _actions(after_delete) == ["cloudfront:GetDistribution"]
    assert after_delete["Resource"] == "arn:aws:cloudfront::000000000000:distribution/*"
    assert "Condition" not in after_delete

    read = by_sid["SiteRead"]
    assert sorted(_actions(read)) == [
        "cloudfront:GetCachePolicy",
        "cloudfront:ListCachePolicies",
        "cloudfront:ListDistributions",
        "tag:GetResources",
    ]
    assert read["Resource"] == "*" and "Condition" not in read
    assert _actions(by_sid["SiteReadOriginAccessControl"]) == ["cloudfront:GetOriginAccessControl"]
    assert (
        by_sid["SiteReadOriginAccessControl"]["Resource"] == _FAKE_VARS["origin_access_control_arn"]
    )
    assert _actions(by_sid["SiteReadResponseHeadersPolicy"]) == [
        "cloudfront:GetResponseHeadersPolicy"
    ]
    assert (
        by_sid["SiteReadResponseHeadersPolicy"]["Resource"]
        == _FAKE_VARS["response_headers_policy_arn"]
    )


def test_the_deploy_role_cannot_claim_another_projects_distribution_by_tag() -> None:
    """SiteDistributionCreate allows TagResource on any resource when the request sets
    Project=horizon-compact, which create-with-tags needs. Without this deny, the role could tag Musical
    Mycelium's distribution as this project's and then update or delete it (found writing C4, 2026-11-06).
    The Null guard leaves a resource with no Project tag alone, since a distribution being created may be
    evaluated with none."""
    deny = _statement("deploy-site.json", "NeverRetagAnotherProjectsDistribution")
    assert deny["Effect"] == "Deny"
    assert _actions(deny) == ["cloudfront:TagResource", "cloudfront:UntagResource"]
    assert deny["Resource"] == "*"
    assert deny["Condition"] == {
        "StringNotEquals": {"aws:ResourceTag/Project": "horizon-compact"},
        "Null": {"aws:ResourceTag/Project": "false"},
    }
    # Every Allow that can tag a distribution is covered by it.
    taggers = [
        str(s["Sid"])
        for s in _statements("deploy-site.json")
        if s["Effect"] == "Allow" and "cloudfront:TagResource" in _actions(s)
    ]
    assert taggers == ["SiteDistributionCreate", "SiteDistributionManage"]


def test_deploy_role_never_gets_cloudfront_star_or_a_write_on_the_two_bootstrap_objects() -> None:
    """The origin access control and the response headers policy take no tag condition, so the deploy role
    holds no write on them at all (decision 5): it could otherwise change Musical Mycelium's."""
    for name in ("deploy.json", "deploy-site.json"):
        allowed = _allowed_actions(name)
        assert "cloudfront:*" not in allowed, name
        assert not [a for a in allowed if _ACCESS_CONTROL_AND_HEADERS_POLICY_WRITES.match(a)], name
        assert not [a for a in allowed if a.startswith("cloudfront:") and "*" in a], name


def test_the_only_whole_service_wildcard_in_the_deploy_role_is_the_site_bucket() -> None:
    """deploy.json allows none (above). deploy-site.json allows s3:* on the site bucket pattern alone,
    for the reason Musical Mycelium's role does: the provider's bucket read path calls a dozen Get*."""
    wide = [
        (str(s["Sid"]), _as_list(s["Resource"]))
        for s in _statements("deploy-site.json")
        if s["Effect"] == "Allow" and any(a == "*" or a.endswith(":*") for a in _actions(s))
    ]
    assert wide == [
        (
            "SiteBucket",
            ["arn:aws:s3:::horizon-compact-site-*", "arn:aws:s3:::horizon-compact-site-*/*"],
        )
    ]


def test_no_deploy_deny_reaches_the_site_grants() -> None:
    """The results-bucket deny names that bucket only; every other deny is on ec2, iam, ecs or bedrock."""
    for s in _statements("deploy.json"):
        if s["Effect"] != "Deny":
            continue
        for action in _actions(s):
            if action.split(":")[0] in {"s3", "cloudfront", "tag"}:
                assert s["Sid"] == "CiNeverReadsRawResults", (s["Sid"], action)
                assert all("horizon-compact-results-" in r for r in _as_list(s["Resource"]))


def test_dev_policy_can_apply_the_two_bootstrap_objects_and_nothing_wider() -> None:
    import json

    statements = json.loads((IAM / "horizon-compact-dev-policy.json").read_text(encoding="utf-8"))[
        "Statement"
    ]
    [grant] = [s for s in statements if s["Sid"] == "CloudFrontBootstrapObjects"]
    assert grant["Effect"] == "Allow" and grant["Resource"] == "*"
    # Wildcards instead of the twelve named actions, which would put the policy over IAM's size limit.
    # Against AWS's service reference (read 2026-11-04), the first matches the six access-control actions
    # and the second Create, Get, Update and Delete of a headers policy; a wider "*ResponseHeadersPolic*"
    # would also match ListDistributionsByResponseHeadersPolicyId, so the other two are named.
    assert _as_list(grant["Action"]) == [
        "cloudfront:*OriginAccessControl*",
        "cloudfront:*ResponseHeadersPolicy",
        "cloudfront:GetResponseHeadersPolicyConfig",
        "cloudfront:ListResponseHeadersPolicies",
    ]
    assert not [
        a
        for s in statements
        if s["Effect"] == "Allow"
        for a in _as_list(s["Action"])
        if a == "cloudfront:*"
    ]


def test_deploy_paths_leave_out_results_commits_and_take_the_site() -> None:
    text = (WORKFLOWS / "deploy.yml").read_text(encoding="utf-8")
    paths = re.search(
        r"on:\n  push:\n    branches: \[main\]\n    paths:\n((?:      - .*\n)+)", text
    )
    assert paths
    listed = [line.strip()[2:].strip('"') for line in paths.group(1).splitlines()]
    assert listed.index("!experiment/results/**") == listed.index("experiment/**") + 1
    assert "web/**" in listed  # Phase 1.5 C4
    # The Vercel rewrite is deployed by hand and touches nothing in AWS (Phase 1.5 C5); later patterns win.
    assert listed.index("!infra/vercel/**") == listed.index("infra/**") + 1


def test_the_image_leaves_experiment_results_out() -> None:
    """Nothing the container runs reads experiment/results/ (Phase 1.5 C1 search), and a results-only
    commit must not change the image. Later lines win, so the exclusion follows `!experiment/`."""
    lines = [
        line.strip()
        for line in (INFRA / "docker" / "Dockerfile.dockerignore")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip() and not line.startswith("#")
    ]
    assert lines.index("experiment/results/") > lines.index("!experiment/")


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


def _results_prefixes(name: str) -> tuple[list[str], list[str]]:
    """The key prefixes a policy's results-object statement names, and its list statement's ``s3:prefix``."""
    bucket = f"arn:aws:s3:::{_FAKE_VARS['results_bucket']}/"
    objects: list[str] = []
    listed: list[str] = []
    for s in _statements(name):
        if s["Sid"] == "ResultsObjects":
            objects = [r.removeprefix(bucket) for r in _as_list(s["Resource"])]
        if s["Sid"] == "ResultsList":
            condition = s["Condition"]
            assert isinstance(condition, dict)
            listed = _as_list(condition["StringLike"]["s3:prefix"])
    return objects, listed


def test_task_role_and_boundary_grant_exactly_the_four_results_prefixes() -> None:
    """Phase 4 code half section 4.2: development, pilot and official, and nothing else in the bucket (the
    pilot is its own top-level prefix so it can never sit beside the grid). Phase 5 search-half doc §4.8 adds
    ``cases/``, a real case's private content and probe records, which the publish path never reads."""
    wanted = ["development/*", "pilot/*", "official/*", "cases/*"]
    for name in ("task.json", "boundary.json"):
        objects, listed = _results_prefixes(name)
        assert sorted(objects) == sorted(wanted), name
        assert sorted(listed) == sorted(wanted), name


def test_the_task_role_never_holds_a_results_prefix_the_boundary_lacks() -> None:
    task_objects, task_listed = _results_prefixes("task.json")
    boundary_objects, boundary_listed = _results_prefixes("boundary.json")
    assert set(task_objects) <= set(boundary_objects)
    assert set(task_listed) <= set(boundary_listed)


def test_task_role_cannot_delete_or_touch_iam() -> None:
    allowed = _allowed_actions("task.json")
    assert not [a for a in allowed if a.startswith(("iam:", "s3:Delete")) or a.endswith(":*")]
    assert set(allowed) == {
        "bedrock:InvokeModel",
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket",
        "ssm:GetParameter",  # the two key parameters (OpenRouter, Anthropic), below
        "kms:Decrypt",  # only for that parameter, via SSM, below
    }


def _statement(name: str, sid: str) -> dict[str, object]:
    return next(s for s in _statements(name) if s["Sid"] == sid)


def test_task_role_and_boundary_read_exactly_two_ssm_parameters_and_decrypt_only_them() -> None:
    """Phase 4 code half sections 4.8 and 4.9: read each key's one parameter (OpenRouter's, Anthropic's),
    nothing else in SSM, and decrypt only through SSM and only that parameter's value (the encryption
    context names its ARN). One statement pair per key, so a wildcard can never join them."""
    from horizon_compact.providers import anthropic, openrouter

    for read_sid, decrypt_sid, ssm_parameter in (
        ("ReadOpenRouterKey", "DecryptOpenRouterKey", openrouter.SSM_PARAMETER),
        ("ReadAnthropicKey", "DecryptAnthropicKey", anthropic.SSM_PARAMETER),
    ):
        parameter = f"arn:aws:ssm:{_FAKE_VARS['region']}:{_FAKE_VARS['account_id']}:parameter{ssm_parameter}"
        for name in ("task.json", "boundary.json"):
            read = _statement(name, read_sid)
            assert read["Effect"] == "Allow" and _actions(read) == ["ssm:GetParameter"], name
            assert _as_list(read["Resource"]) == [parameter], name  # one parameter, no wildcard
            decrypt = _statement(name, decrypt_sid)
            assert _actions(decrypt) == ["kms:Decrypt"], name
            condition = decrypt["Condition"]
            assert isinstance(condition, dict)
            assert condition["StringEquals"] == {
                "kms:ViaService": f"ssm.{_FAKE_VARS['region']}.amazonaws.com",
                "kms:EncryptionContext:PARAMETER_ARN": parameter,
            }, name
    for name in ("task.json", "boundary.json"):
        ssm_statements = [s for s in _statements(name) if "ssm:GetParameter" in _actions(s)]
        assert len(ssm_statements) == 2, name  # exactly the two keys' reads
    allowed = _allowed_actions("task.json")
    assert not [a for a in allowed if a.startswith("ssm:") and a != "ssm:GetParameter"]
    assert not [a for a in allowed if a.startswith("kms:") and a != "kms:Decrypt"]


def test_the_key_parameter_is_never_created_by_terraform() -> None:
    """He creates its value by hand in the console, so the key never passes through a file, a command line or
    Terraform state (section 4.8)."""
    assert "aws_ssm_parameter" not in _tf_text_all()


def _tf_text_all() -> str:
    return "\n".join(_strip_comments(text) for text in _tf_text().values())


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


def test_permission_check_covers_the_six_refusals() -> None:
    text = (WORKFLOWS / "aws-permission-check.yml").read_text(encoding="utf-8")
    for needle in (
        "create-role",
        "create-bucket",
        "put-role-policy",
        "run-task",
        "delete-distribution",
        "tag-resource",
        "workflow_dispatch",
    ):
        assert needle in text, needle
    assert "push:" not in text
    assert text.count('expect_refused "') == 6


def test_the_distribution_attempts_could_never_change_it() -> None:
    """If the fence were missing, the delete still fails on a stale ETag and the tag on a value over 256
    characters, so the check can never alter another project's distribution."""
    text = (WORKFLOWS / "aws-permission-check.yml").read_text(encoding="utf-8")
    assert "--if-match E0000000000000" in text
    assert "seq 1 300" in text and "Value=${too_long}" in text
    assert "update-distribution" not in text and "untag-resource" not in text


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


# --- the case builder never sees the outcome (Phase 5 code-half IMPLEMENTATION doc, finding 7) ---

CASEBUILD = ROOT / "src" / "horizon_compact" / "casebuild"
# The rubric, the matcher that reads it and the case record that hashes it. If the builder cannot import them,
# no code path can carry the company's outcome to the extraction model.
OUTCOME_MODULES = (
    "horizon_compact.analysis",
    "horizon_compact.protocol.cases",
    "horizon_compact.simulation",
)


def _imported_modules(tree: ast.AST) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = ("." * node.level) + (node.module or "")
            found.append((node.lineno, base))
            found.extend((node.lineno, f"{base}.{alias.name}") for alias in node.names)
    return found


def _outcome_imports(tree: ast.AST) -> list[str]:
    offenders = []
    for lineno, module in _imported_modules(tree):
        relative = module.startswith(".")
        named = any(word in module.lower() for word in ("rubric", "outcome"))
        listed = any(module == m or module.startswith(f"{m}.") for m in OUTCOME_MODULES)
        if relative or named or listed:
            offenders.append(f"line {lineno}: {module}")
    return offenders


def test_casebuild_cannot_import_the_rubric_or_any_case_outcome_type() -> None:
    offenders: list[str] = []
    for path in sorted(CASEBUILD.rglob("*.py")):
        offenders.extend(
            f"{path.name} {where}"
            for where in _outcome_imports(ast.parse(path.read_text(encoding="utf-8")))
        )
    assert not offenders, f"casebuild/ imports something that could carry an outcome: {offenders}"


def test_the_outcome_import_scan_catches_what_it_is_meant_to() -> None:
    for source in (
        "from horizon_compact.analysis import matcher",
        "import horizon_compact.analysis.outcomes",
        "from horizon_compact.protocol.cases import CaseRecord",
        "from horizon_compact import simulation",
        "from horizon_compact.casebuild.rubric_reader import x",
        "from . import sibling",
    ):
        assert _outcome_imports(ast.parse(source)), source
    for source in (
        "from horizon_compact.casebuild.sections import SectionInputs",
        "from horizon_compact.privacy.names import compile_term",
        "from horizon_compact.providers.base import TextRequest",
    ):
        assert not _outcome_imports(ast.parse(source)), source


# --- the independent reader never sees the grid's results (search-half doc §4.9; protocol §12.9) ---

READER = ROOT / "src" / "horizon_compact" / "reader"
# Whatever holds a result, a run record, a probe answer or the analysis of them. The reader reads named files
# of one case's folder and the shape's template; if it cannot import these, no result can reach it.
RESULT_MODULES = (
    "horizon_compact.analysis",
    "horizon_compact.simulation",
    "horizon_compact.sweep",
    "horizon_compact.probes",
    "horizon_compact.caseprobe",
    "horizon_compact.smoke",
    "horizon_compact.protocol.gate",
)


def test_the_reader_cannot_import_anything_that_holds_a_result() -> None:
    offenders: list[str] = []
    for path in sorted(READER.rglob("*.py")):
        for lineno, module in _imported_modules(ast.parse(path.read_text(encoding="utf-8"))):
            if any(module == m or module.startswith(f"{m}.") for m in RESULT_MODULES):
                offenders.append(f"{path.name}:{lineno} {module}")
    assert not offenders, f"reader/ imports something that holds a result: {offenders}"


def test_the_reader_import_scan_catches_what_it_is_meant_to() -> None:
    def hits(source: str) -> bool:
        return any(
            m == r or m.startswith(f"{r}.")
            for _, m in _imported_modules(ast.parse(source))
            for r in RESULT_MODULES
        )

    assert hits("from horizon_compact.analysis import matcher")
    assert hits("from horizon_compact.sweep.plan import build_plan")
    assert hits("import horizon_compact.probes.run")
    assert hits("from horizon_compact.caseprobe.verdict import probe_verdict")
    assert not hits("from horizon_compact.providers.base import TextRequest")


def test_the_case_builder_cannot_import_the_reader() -> None:
    offenders = [
        f"{path.name}:{lineno} {module}"
        for path in sorted(CASEBUILD.rglob("*.py"))
        for lineno, module in _imported_modules(ast.parse(path.read_text(encoding="utf-8")))
        if "horizon_compact.reader" in module
    ]
    assert not offenders, f"casebuild/ imports the reader: {offenders}"


def test_the_case_builder_cannot_import_the_case_probe_which_holds_probe_answers() -> None:
    offenders = [
        f"{path.name}:{lineno} {module}"
        for path in sorted(CASEBUILD.rglob("*.py"))
        for lineno, module in _imported_modules(ast.parse(path.read_text(encoding="utf-8")))
        if "horizon_compact.caseprobe" in module
    ]
    assert not offenders, f"casebuild/ imports the case probe: {offenders}"


def test_the_reader_reads_the_flagged_answers_from_a_file_not_from_the_case_probe() -> None:
    # The flagged-answers file is the one channel from the probe to the reader; no import carries it.
    imported = [
        module
        for path in sorted(READER.rglob("*.py"))
        for _, module in _imported_modules(ast.parse(path.read_text(encoding="utf-8")))
    ]
    assert not [m for m in imported if "caseprobe" in m]


# --- the site (Phase 1.5 IMPLEMENTATION doc sections 9 and 10, C4) ----------------------------------------


def _site_code() -> str:
    return _strip_comments((MAIN / "site.tf").read_text(encoding="utf-8"))


def test_the_site_bucket_is_private_computed_and_needs_no_emptying() -> None:
    code = _site_code()
    assert 'site_bucket = "${var.project}-site-${local.account_id}"' in code
    assert re.search(r"force_destroy\s*=\s*true", code)
    for setting in (
        "block_public_acls",
        "block_public_policy",
        "ignore_public_acls",
        "restrict_public_buckets",
    ):
        assert re.search(rf"{setting}\s*=\s*true", code), setting
    assert "prevent_destroy" not in code  # the results bucket keeps it, in bootstrap


def test_only_this_distribution_can_read_the_site_bucket() -> None:
    code = _site_code()
    assert re.search(r'actions\s*=\s*\["s3:GetObject"\]', code)
    assert '"cloudfront.amazonaws.com"' in code
    assert re.search(r'variable\s*=\s*"AWS:SourceArn"', code)
    assert "aws_cloudfront_distribution.site.arn" in code


def test_the_distribution_uses_the_bootstrap_objects_and_never_creates_them() -> None:
    """Decision 5: the two objects take no tag condition, so main reads them by id and the deploy role
    holds no write on them."""
    main = _main_code()
    for resource in (
        "aws_cloudfront_origin_access_control",
        "aws_cloudfront_response_headers_policy",
    ):
        assert not re.search(rf'resource\s+"{resource}"', main), resource
    code = _site_code()
    assert "id = var.site_origin_access_control_id" in code
    assert "id = var.site_response_headers_policy_id" in code
    assert "origin_access_control_id = data.aws_cloudfront_origin_access_control.site.id" in code
    assert (
        "response_headers_policy_id = data.aws_cloudfront_response_headers_policy.site.id" in code
    )
    assert '"Managed-CachingOptimized"' in code


def test_the_distribution_is_https_get_only_and_the_cheapest_class() -> None:
    code = re.sub(r"[ \t]+", " ", _site_code())
    assert 'viewer_protocol_policy = "redirect-to-https"' in code
    assert 'allowed_methods = ["GET", "HEAD"]' in code
    assert 'price_class = "PriceClass_100"' in code
    assert "cloudfront_default_certificate = true" in code
    assert "wait_for_deployment = false" in code
    assert "for_each = [403, 404]" in code
    assert not re.search(r"\baliases\b", code)  # the public URL is the Vercel rewrite (C5)


def test_main_outputs_hide_the_site_bucket_and_show_the_distribution() -> None:
    code = _strip_comments((MAIN / "outputs.tf").read_text(encoding="utf-8"))
    blocks = {
        re.match(r'output\s+"([^"]+)"', b).group(1): b  # type: ignore[union-attr]
        for b in re.split(r'(?=output\s+")', code)[1:]
    }
    plain = {"site_distribution_id", "site_domain"}  # neither holds the account id
    for name, block in blocks.items():
        if name in plain:
            assert "sensitive" not in block, name
        else:
            assert re.search(r"sensitive\s*=\s*true", block), name
    assert plain <= set(blocks) and "site_bucket" in blocks


def test_main_requires_the_two_site_ids_with_no_default() -> None:
    code = (MAIN / "variables.tf").read_text(encoding="utf-8")
    for name in ("site_origin_access_control_id", "site_response_headers_policy_id"):
        block = re.search(rf'variable\s+"{name}"\s*\{{(.*?)\n\}}', code, flags=re.DOTALL)
        assert block is not None, name
        assert not re.search(r"^\s*default\s*=", block.group(1), flags=re.MULTILINE), name
        assert "validation" in block.group(1), name


def _deploy() -> str:
    return (WORKFLOWS / "deploy.yml").read_text(encoding="utf-8")


def _job(text: str, name: str) -> str:
    match = re.search(
        rf"^  {name}:\n(.*?)(?=^  [a-z]+:\n|\Z)", text, flags=re.DOTALL | re.MULTILINE
    )
    assert match, name
    return match.group(1)


def test_deploy_splits_the_image_from_the_site_by_changed_paths() -> None:
    text = _deploy()
    changes = _job(text, "changes")
    assert "git diff --name-only" in changes and "fetch-depth: 0" in changes
    assert "uses: dorny" not in text and "paths-filter" not in text  # no third-party action
    # A results-only path is matched first, so it can never set either half.
    case = changes[changes.index('case "$path" in') :]
    assert case.index("experiment/results/*) ;;") < case.index("experiment/*")
    # The Vercel rewrite is matched before infra/, so it never builds an image or applies (Phase 1.5 C5).
    assert case.index("infra/vercel/*) ;;") < case.index("infra/* |")
    assert "web/*) site=true" in changes
    image = _job(text, "image")
    assert "needs: [changes, check]" in image
    assert "if: needs.changes.outputs.code == 'true'" in image


def test_deploy_check_job_installs_node_for_the_page_checks() -> None:
    check = _job(_deploy(), "check")
    assert "actions/setup-node@v7.1.0" in check
    assert "npm --prefix web ci" in check
    assert check.index("npm --prefix web ci") < check.index("run: make check")


def test_the_apply_passes_the_two_site_ids() -> None:
    infra = _job(_deploy(), "infra")
    assert "site_origin_access_control_id=${{ vars.SITE_ORIGIN_ACCESS_CONTROL_ID }}" in infra
    assert "site_response_headers_policy_id=${{ vars.SITE_RESPONSE_HEADERS_POLICY_ID }}" in infra


def test_the_site_job_runs_after_a_good_apply_or_alone_and_never_after_a_failure() -> None:
    site = _job(_deploy(), "site")
    assert "needs: [changes, check, image, infra]" in site
    for clause in (
        "!cancelled()",
        "needs.changes.outputs.site == 'true'",
        "needs.check.result == 'success'",
        "(needs.image.result == 'success' || needs.image.result == 'skipped')",
        "(needs.infra.result == 'success' || needs.infra.result == 'skipped')",
    ):
        assert clause in site, clause
    assert "npm --prefix web run check" in site
    assert "mask-aws-account-id: true" in site
    assert "::add-mask::$bucket" in site


def test_the_site_sync_caches_hashed_assets_only() -> None:
    site = _job(_deploy(), "site")
    assets = site.index('aws s3 sync web/dist/assets "s3://${bucket}/assets/"')
    rest = site.index('aws s3 sync web/dist "s3://${bucket}/"')
    assert assets < rest
    assert "immutable" in site[assets:rest]
    assert '--exclude "assets/*"' in site[rest:] and '--cache-control "no-cache"' in site[rest:]
    assert "--paths '/*'" in site


def test_the_smoke_test_checks_the_build_the_headers_and_the_sweep_on_cloudfront_only() -> None:
    site = _job(_deploy(), "site")
    smoke = site[site.index("Smoke test the site") :]
    assert "output -raw site_domain" in smoke
    assert "vercel.app" not in smoke  # the rewrite is his step; a teardown day cannot turn this red
    for needle in (
        "content-security-policy: default-src 'none'",
        "x-robots-tag: noindex",
        "x-content-type-options: nosniff",
        "strict-transport-security",
        ".sweep.sweep_id",
        "text/css",
        "javascript",
    ):
        assert needle in smoke, needle


def test_the_teardown_runs_only_on_the_typed_phrase_and_never_beside_a_deploy() -> None:
    text = (WORKFLOWS / "teardown.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text and "push:" not in text and "schedule:" not in text
    assert "if: inputs.confirm == 'destroy main'" in text
    assert re.search(r"group:\s*deploy-main", text)
    assert re.search(r"cancel-in-progress:\s*false", text)
    assert "terraform -chdir=infra/terraform/main destroy" in text
    assert "infra/terraform/bootstrap" not in text.split("\n# ", 1)[-1].split("jobs:", 1)[1]
    assert "Key=Root,Values=main" in text
    assert "mask-aws-account-id: true" in text


def test_the_teardown_check_lets_only_inactive_leftovers_through() -> None:
    """A deleted ECS cluster stays discoverable as INACTIVE for a while, as task definitions do (the teardown
    test, 2026-11-07). The check may pass over those two, and only by type and status: an ACTIVE cluster, or
    one the describe call cannot answer for, still fails it."""
    text = (WORKFLOWS / "teardown.yml").read_text(encoding="utf-8")
    assert "grep -v ':task-definition/'" in text
    assert 'if [[ "$arn" == *":cluster/"* ]]; then' in text
    assert "--query 'clusters[0].status'" in text and "|| echo UNKNOWN" in text
    assert 'if [ "$status" = "INACTIVE" ]; then' in text
    # The direct checks by name stay, whatever the listing says.
    assert "length(clusters[?status==`ACTIVE`])" in text
    assert "Comment=='horizon-compact site'" in text
