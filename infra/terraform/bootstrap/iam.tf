# The permissions boundary and the deploy role's permissions (Phase 1 IMPLEMENTATION doc sections 8 and 10).
#
# Every policy is a JSON template in infra/iam/, so tests parse real JSON. Account ids enter only as template
# variables at plan time; no file holds one.

locals {
  # Built from names, not resource references, so the deploy policy can name itself without a cycle.
  boundary_arn = "arn:aws:iam::${local.account_id}:policy/${var.project}-boundary"

  policy_vars = {
    account_id           = local.account_id
    region               = var.region
    state_bucket         = local.state_bucket
    results_bucket       = local.results_bucket
    ecr_repository_arn   = aws_ecr_repository.sweep.arn
    boundary_arn         = local.boundary_arn
    sonnet_profile_arn   = aws_bedrock_inference_profile.sonnet_4_6.arn
    nova_pro_profile_arn = aws_bedrock_inference_profile.nova_pro.arn
  }
}

# The most any role CI creates can ever do. Nothing in iam:*, nothing in s3:Delete*.
resource "aws_iam_policy" "boundary" {
  name        = "${var.project}-boundary"
  description = "Permissions boundary for every role the deploy role creates."
  policy      = templatefile("${path.module}/../../iam/boundary.json", local.policy_vars)
}

resource "aws_iam_policy" "deploy" {
  name        = "${var.project}-deploy"
  description = "What the GitHub deploy role may do, and what it may never do."
  policy      = templatefile("${path.module}/../../iam/deploy.json", local.policy_vars)
}

# The one attachment: trust was proven in Phase 0.5 (oidc.tf); permissions arrive here.
resource "aws_iam_role_policy_attachment" "github_deploy" {
  role       = aws_iam_role.github_deploy.name
  policy_arn = aws_iam_policy.deploy.arn
}

# The site's grants (Phase 1.5 section 9) are a second, inline policy on the same role. deploy.json already sits at
# 5,674 of IAM's 6,144 non-space characters for one managed policy, and four more statements do not fit in it.
# Inline keeps the grants on this role alone, needs no new attach permission for the dev key (its ProjectRoles
# statement already covers PutRolePolicy), and the deploy policy's NeverChangeOwnPermissions deny already covers
# the role. Its variables are built apart from `policy_vars` so the boundary and the deploy policy do not read
# the two new objects' ARNs, which are unknown until they exist and would show both as changed in the plan.
locals {
  site_policy_vars = merge(local.policy_vars, {
    origin_access_control_arn   = aws_cloudfront_origin_access_control.site.arn
    response_headers_policy_arn = aws_cloudfront_response_headers_policy.site.arn
  })
}

resource "aws_iam_role_policy" "github_deploy_site" {
  name   = "${var.project}-deploy-site"
  role   = aws_iam_role.github_deploy.name
  policy = templatefile("${path.module}/../../iam/deploy-site.json", local.site_policy_vars)
}
