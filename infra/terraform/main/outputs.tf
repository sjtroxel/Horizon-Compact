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

# The site (Phase 1.5). The bucket's name holds the account id, so it is sensitive; the distribution's id and its
# *.cloudfront.net domain do not, so the site job can print them.

output "site_bucket" {
  description = "Where the deploy workflow's site job syncs the build."
  value       = aws_s3_bucket.site.id
  sensitive   = true
}

output "site_distribution_id" {
  description = "The distribution the site job invalidates after a sync."
  value       = aws_cloudfront_distribution.site.id
}

output "site_domain" {
  description = "The distribution's *.cloudfront.net domain: the smoke test's target and the Vercel rewrite's destination."
  value       = aws_cloudfront_distribution.site.domain_name
}
