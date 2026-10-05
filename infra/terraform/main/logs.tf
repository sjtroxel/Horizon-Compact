# Retention is set explicitly: a log group without it keeps logs forever and bills for them.
resource "aws_cloudwatch_log_group" "sweep" {
  name              = "/ecs/${var.project}-sweep"
  retention_in_days = 30
}
