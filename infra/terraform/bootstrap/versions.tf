terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.67"
    }
  }

  # No backend block: bootstrap uses LOCAL state, deliberately (Phase 0.5 IMPLEMENTATION doc, section 5).
  #
  # This root creates the S3 bucket that holds `main`'s state, so it cannot keep its own state there from
  # the start. The state file is gitignored and lives on one machine. That is an accepted risk, as in
  # Musical Mycelium: this root holds a handful of resources with stable names, so losing the state costs a
  # few `terraform import` commands, not a rebuild. The bucket this root creates can hold its own state
  # later, if that risk stops being acceptable.
}
