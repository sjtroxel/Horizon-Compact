# ARNs contain the account id, so every output is sensitive (a pasted `terraform output` cannot leak it).

output "task_definition_arn" {
  description = "The registered sweep task definition, which names the image by digest."
  value       = aws_ecs_task_definition.sweep.arn
  sensitive   = true
}

output "cluster_arn" {
  value     = aws_ecs_cluster.main.arn
  sensitive = true
}

output "security_group_id" {
  value     = aws_security_group.sweep.id
  sensitive = true
}
