variable "project" {
  description = "Name prefix for every resource, and the value of the Project tag."
  type        = string
  default     = "horizon-compact"
}

variable "region" {
  description = "AWS region. The Availability Zones in network.tf are this region's a and b."
  type        = string
  default     = "us-east-1"
}

variable "image_digest" {
  description = "The sweep image's manifest digest, from the deploy workflow's build. The task definition names the image by digest, so a result can say exactly which bytes ran."
  type        = string

  validation {
    condition     = can(regex("^sha256:[0-9a-f]{64}$", var.image_digest))
    error_message = "image_digest must look like sha256:<64 hex characters>."
  }
}

variable "sonnet_route" {
  description = <<-EOT
    How the task reaches Sonnet 4.6 (Phase 0.5 decision 3): `application_profile` (the tagged profile) or
    `geo_profile` (the `us.` cross-region profile). No default, so a deploy cannot pick one by accident. Set in
    CI from the repository variable SONNET_ROUTE, and it must equal `route` in experiment/models.toml: a session
    refuses to start otherwise.
  EOT
  type        = string

  validation {
    condition     = contains(["application_profile", "geo_profile"], var.sonnet_route)
    error_message = "sonnet_route must be application_profile or geo_profile."
  }
}

# The two `bootstrap` objects (Phase 1.5 decision 5). Their ids hold no account id, so CI passes them from plain
# repository variables (SITE_ORIGIN_ACCESS_CONTROL_ID, SITE_RESPONSE_HEADERS_POLICY_ID), set by hand from
# `terraform -chdir=infra/terraform/bootstrap output -raw <name>`. No default, so a deploy cannot run without them.

variable "site_origin_access_control_id" {
  description = "The site distribution's origin access control, from `bootstrap`'s output of the same name."
  type        = string

  validation {
    condition     = can(regex("^E[0-9A-Z]{10,20}$", var.site_origin_access_control_id))
    error_message = "site_origin_access_control_id must look like a CloudFront id (E followed by capitals and digits)."
  }
}

variable "site_response_headers_policy_id" {
  description = "The site distribution's response headers policy, from `bootstrap`'s output of the same name."
  type        = string

  validation {
    condition     = can(regex("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", var.site_response_headers_policy_id))
    error_message = "site_response_headers_policy_id must be a UUID."
  }
}
