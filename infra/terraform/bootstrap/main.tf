provider "aws" {
  region = var.region

  # Every resource is tagged, so a cost report can answer "what is Horizon Compact costing" without
  # guessing from names. `Project` is also the key the tag test in section 7 of the IMPLEMENTATION doc
  # activates as a cost allocation tag.
  default_tags {
    tags = {
      Project   = var.project
      ManagedBy = "terraform"
      Root      = "bootstrap"
    }
  }
}

data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id

  # Bucket names are global across AWS; the account id is the disambiguator. It is computed at plan time and
  # never written in a tracked file. `main`'s backend takes this name at `init` time for the same reason.
  state_bucket = "${var.project}-tfstate-${local.account_id}"
}
