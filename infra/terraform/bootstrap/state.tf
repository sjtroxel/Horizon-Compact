# The bucket that holds `main`'s Terraform state (Phase 1). `main` uses S3's native lock file
# (`use_lockfile = true`), so there is no DynamoDB table.
#
# Cost: fractions of a cent. S3 has no always-on component.

resource "aws_s3_bucket" "state" {
  bucket = local.state_bucket

  # force_destroy is a deliberate choice, with Musical Mycelium's argument: a versioned bucket holding
  # objects refuses to delete without it, and `terraform destroy` must stay a real, complete off-switch.
  #
  # The ordering rule that makes this safe is not optional: destroy `main` FIRST, then `bootstrap`.
  # Reversing it deletes the state that describes main's resources and leaves them running and unmanaged,
  # which is the expensive failure, not this flag.
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "state" {
  bucket = aws_s3_bucket.state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Versioning makes a corrupted state recoverable, and also makes an otherwise free bucket accumulate
# objects forever. Thirty days is long enough to notice and roll back a bad apply.
resource "aws_s3_bucket_lifecycle_configuration" "state" {
  bucket = aws_s3_bucket.state.id

  # The provider requires versioning to be settled before lifecycle rules reference noncurrent versions;
  # without this the first apply can race and fail (recorded by Musical Mycelium).
  depends_on = [aws_s3_bucket_versioning.state]

  rule {
    id     = "expire-noncurrent-state-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 30
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}
