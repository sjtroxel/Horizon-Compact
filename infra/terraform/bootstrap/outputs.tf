# Every value containing the account id is `sensitive`, so a pasted `terraform output` cannot leak it by
# accident. Read one with `terraform output -raw <name>`.

output "state_bucket" {
  description = "Pass to main as `terraform init -backend-config=bucket=<this>`."
  value       = aws_s3_bucket.state.id
  sensitive   = true
}

output "github_deploy_role_arn" {
  description = "Set as the AWS_DEPLOY_ROLE_ARN repository secret in GitHub."
  value       = aws_iam_role.github_deploy.arn
  sensitive   = true
}

output "oidc_provider_arn" {
  description = "The shared provider, as READ. Compared before and after the apply; it must not change."
  value       = data.aws_iam_openid_connect_provider.github.arn
  sensitive   = true
}

output "sonnet_profile_arn" {
  description = "The tagged application profile for Sonnet 4.6."
  value       = aws_bedrock_inference_profile.sonnet_4_6.arn
  sensitive   = true
}

output "nova_pro_profile_arn" {
  description = "The tagged application profile for Nova Pro."
  value       = aws_bedrock_inference_profile.nova_pro.arn
  sensitive   = true
}
