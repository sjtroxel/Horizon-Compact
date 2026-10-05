# No service and no scheduler: a sweep is a task a person starts by hand (`hc sweep launch`).

resource "aws_ecs_cluster" "main" {
  name = var.project

  # Container Insights bills per metric; it stays off.
  setting {
    name  = "containerInsights"
    value = "disabled"
  }
}

resource "aws_ecs_task_definition" "sweep" {
  family                   = "${var.project}-sweep"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  task_role_arn            = aws_iam_role.task.arn
  execution_role_arn       = aws_iam_role.execution.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "ARM64"
  }

  container_definitions = jsonencode([
    {
      name      = "sweep"
      image     = "${data.aws_ecr_repository.sweep.repository_url}@${var.image_digest}"
      essential = true

      # No command: the image's entrypoint is `hc`, and `hc sweep launch` supplies the arguments per run.
      environment = [
        { name = "HC_RESULTS_BUCKET", value = local.results_bucket },
        { name = "HC_REGION", value = var.region },
        { name = "HC_SONNET_ROUTE", value = var.sonnet_route },
        { name = "HC_SONNET_PROFILE_ARN", value = local.sonnet_profile_arn },
        { name = "PYTHONUNBUFFERED", value = "1" },
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.sweep.name
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "sweep"
        }
      }
    }
  ])
}
