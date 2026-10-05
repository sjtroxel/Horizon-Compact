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
