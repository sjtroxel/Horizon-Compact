provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project   = var.project
      ManagedBy = "terraform"
      Root      = "main"
    }
  }
}

data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id

  # Both names are computed, never written: they hold the account id. `bootstrap` owns these resources and
  # `main` only names them, so `terraform destroy` here can never touch the results or the images.
  results_bucket = "${var.project}-results-${local.account_id}"
  boundary_arn   = "arn:aws:iam::${local.account_id}:policy/${var.project}-boundary"
}

# The repository belongs to `bootstrap` (Phase 1 decision 1); `main` reads it.
data "aws_ecr_repository" "sweep" {
  name = var.project
}
