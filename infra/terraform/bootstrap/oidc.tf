# GitHub Actions authentication, without a long-lived AWS key.
#
# THE SHARED PROVIDER IS LOOKED UP, NEVER CREATED OR DESTROYED (planning/04 section 3.5).
#
# An AWS account holds one IAM OIDC provider per issuer URL. Musical Mycelium's Terraform
# (infra/terraform/bootstrap/oidc.tf in that repo) owns this one. If this project created it, the apply
# would fail; if this project ever owned it and was torn down, Musical Mycelium's deploys would break.
# Destroying Musical Mycelium's bootstrap stack would, in turn, break THIS project's deploys, so that
# dependency is recorded here and should be recorded in that repo too.
#
# No `resource "aws_iam_openid_connect_provider"` appears anywhere under infra/, in any form, including
# behind a `count` switch. A test enforces that. The dev IAM policy also denies every change to OIDC
# providers, so the mistake is refused as well as tested for.
data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
}

data "aws_iam_policy_document" "github_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [data.aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # The load-bearing condition. Without it ANY GitHub repository in the world can assume this role.
    # Pinned to one repo and one branch ref, so a pull request (including one from a fork) cannot get
    # credentials: its token's `sub` names a pull-request ref, not refs/heads/main. The value is the API's
    # immutable prefix, used verbatim (see variables.tf).
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repo}:ref:refs/heads/${var.github_branch}"]
    }
  }
}

# NO PERMISSION POLICY, inline or attached (Phase 0.5 decision 1). Its trust is proven by one manual
# workflow run that prints its identity, which needs no permission. Phase 1 attaches permissions, with a
# permissions boundary, once there are resources to scope them to.
resource "aws_iam_role" "github_deploy" {
  name               = "${var.project}-github-deploy"
  description        = "Assumed by GitHub Actions via OIDC. Trust only; permissions arrive in Phase 1."
  assume_role_policy = data.aws_iam_policy_document.github_assume.json

  max_session_duration = 3600
}
