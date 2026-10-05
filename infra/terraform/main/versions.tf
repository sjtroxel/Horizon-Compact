terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.67"
    }
  }

  # State lives in the bucket `bootstrap` creates. The bucket name holds the account id, so it is not written
  # here: `terraform init -backend-config=bucket=<name>` supplies it (the TF_STATE_BUCKET secret in CI, or
  # `terraform -chdir=infra/terraform/bootstrap output -raw state_bucket` by hand). S3's native lock file
  # replaces a DynamoDB table.
  backend "s3" {
    key          = "main/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true
    encrypt      = true
  }
}
