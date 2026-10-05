# The two roles a sweep task uses (Phase 1 IMPLEMENTATION doc sections 9.3 and 10). Each carries the permissions
# boundary, and the deploy role may create them only with it, so neither can ever hold more than the boundary
# allows. Policies are JSON templates in infra/iam/, so tests parse real JSON.

# The Sonnet 4.6 resources a task may invoke, by route (decision 3, section 9.3). The application profile's ARN
# is looked up by name here, since its id is random.
data "aws_bedrock_inference_profiles" "application" {
  type = "APPLICATION"
}

locals {
  sonnet_profile_arns = [
    for p in data.aws_bedrock_inference_profiles.application.inference_profile_summaries :
    p.inference_profile_arn if p.inference_profile_name == "${var.project}-sonnet-4-6"
  ]

  # Empty on the geo_profile route, which does not use it. On the application_profile route a missing profile
  # is an error at plan time, not an AccessDenied at the first call.
  sonnet_profile_arn = var.sonnet_route == "application_profile" ? one(local.sonnet_profile_arns) : ""

  geo_profile_arn   = "arn:aws:bedrock:${var.region}:${local.account_id}:inference-profile/us.anthropic.claude-sonnet-4-6"
  sonnet_foundation = "arn:aws:bedrock:*::foundation-model/anthropic.claude-sonnet-4-6*"
  bedrock_resources = var.sonnet_route == "application_profile" ? [
    local.sonnet_profile_arn, local.geo_profile_arn, local.sonnet_foundation,
    ] : [
    local.geo_profile_arn, local.sonnet_foundation,
  ]

  policy_vars = {
    account_id         = local.account_id
    region             = var.region
    results_bucket     = local.results_bucket
    ecr_repository_arn = data.aws_ecr_repository.sweep.arn
    bedrock_resources  = jsonencode(local.bedrock_resources)
  }
}

data "aws_iam_policy_document" "ecs_tasks_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }

    # Confused-deputy guard: only ECS acting for this account may assume the role.
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [local.account_id]
    }
  }
}

# The task's own role: invoke the model, write and read its results, nothing else.
resource "aws_iam_role" "task" {
  name                 = "${var.project}-task"
  description          = "The sweep task: invoke Sonnet 4.6, read and write development results."
  assume_role_policy   = data.aws_iam_policy_document.ecs_tasks_assume.json
  permissions_boundary = local.boundary_arn
}

resource "aws_iam_role_policy" "task" {
  name   = "task"
  role   = aws_iam_role.task.id
  policy = templatefile("${path.module}/../../iam/task.json", local.policy_vars)
}

# ECS's own role for the task: pull the image, write the log stream.
resource "aws_iam_role" "execution" {
  name                 = "${var.project}-task-execution"
  description          = "ECS pulls the sweep image and writes its logs with this role."
  assume_role_policy   = data.aws_iam_policy_document.ecs_tasks_assume.json
  permissions_boundary = local.boundary_arn
}

resource "aws_iam_role_policy" "execution" {
  name   = "execution"
  role   = aws_iam_role.execution.id
  policy = templatefile("${path.module}/../../iam/execution.json", local.policy_vars)
}
