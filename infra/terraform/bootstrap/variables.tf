variable "project" {
  description = "Name prefix for every resource, and the value of the Project tag."
  type        = string
  default     = "horizon-compact"
}

variable "region" {
  description = "AWS region. Sonnet 4.6 has no in-region endpoint in any US region, so it is reached through a cross-region profile."
  type        = string
  default     = "us-east-1"
}

variable "github_repo" {
  description = <<-EOT
    The repository whose workflows may assume the deploy role, in the exact form GitHub puts in the OIDC
    token's `sub` claim. This repo was created after GitHub's 2026-07-15 change, so the claim is the
    *immutable* form, which carries permanent numeric owner and repository IDs after each name.

    A trust policy written against the old name-only form fails closed with `Not authorized to perform
    sts:AssumeRoleWithWebIdentity` and no hint as to why (Musical Mycelium, 2026-08-05).

    Read the current value rather than assembling it by hand, and use its `sub_claim_prefix` verbatim:

        gh api repos/sjtroxel/Horizon-Compact/actions/oidc/customization/sub

    Read 2026-10-04: use_immutable_subject is true.
  EOT
  type        = string
  default     = "sjtroxel@183318591/Horizon-Compact@1403629566"
}

variable "github_branch" {
  description = <<-EOT
    The only branch whose workflow runs may assume the deploy role. Scoped to a branch, a pull request
    (including one from a fork) cannot obtain credentials, because its token's `sub` names a pull-request
    ref rather than `refs/heads/main`. A run dispatched from a tag is refused for the same reason, by design.
  EOT
  type        = string
  default     = "main"
}

variable "alert_email" {
  description = "Where budget notifications go. Set in an untracked terraform.tfvars or TF_VAR_alert_email; never in a tracked file."
  type        = string
  sensitive   = true
}

variable "sonnet_service_name" {
  description = <<-EOT
    The exact `Service` value the Budgets filter uses for Claude Sonnet 4.6, which is billed through AWS
    Marketplace under the model provider rather than under "Amazon Bedrock".

    The Budgets console's filter list only offers services that have already been billed, so this string
    cannot be read before the first Sonnet 4.6 call has charges (found 2026-10-04: the list held 13 services,
    Haiku's among them as "Claude Haiku 4.5 ( Bedrock Edition)", and no Sonnet). Until it is set, the
    Sonnet-line budget is NOT created. Set it in the untracked terraform.tfvars once it appears in the list,
    then apply. Deliberately no guessed default: a wrong string would make a budget that watches nothing.
  EOT
  type        = string
  default     = ""
}

variable "budget_start" {
  description = "Start of the one CUSTOM budget period covering the whole project (the $80 ceiling is cumulative)."
  type        = string
  default     = "2026-10-01_00:00"
}

variable "budget_end" {
  description = "End of the budget period. Within three years of the start; past the credits' expiry (2027-07-30)."
  type        = string
  default     = "2029-09-30_00:00"
}

variable "budget_limit_usd" {
  description = "The v1 ceiling (planning/03 section 4)."
  type        = string
  default     = "80"
}

variable "budget_alert_thresholds_usd" {
  description = "Actual-spend alert points: 40, the re-plan point 60, and 75."
  type        = list(number)
  default     = [40, 60, 75]
}
