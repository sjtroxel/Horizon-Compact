# The results bucket (Phase 1 IMPLEMENTATION doc sections 7 and 8; decision 4: it lives in bootstrap).
#
# THIS IS A ONE-WAY DOOR (planning/05 section 3.1): raw model responses are kept write-once, one object per
# attempt. The bucket policy below makes S3 itself refuse an overwrite or a delete from every principal,
# including the account's owner, so a result cannot be changed without first changing the policy, and that
# change is a reviewed Terraform apply.

locals {
  results_bucket = "${var.project}-results-${local.account_id}"
}

resource "aws_s3_bucket" "results" {
  bucket = local.results_bucket

  # Unlike the state bucket, no force_destroy: the contents are the experiment's evidence.
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "results" {
  bucket = aws_s3_bucket.results.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "results" {
  bucket = aws_s3_bucket.results.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "results" {
  bucket = aws_s3_bucket.results.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# No lifecycle configuration on purpose: results never expire.

data "aws_iam_policy_document" "results" {
  # The header's absence is what a plain PutObject looks like. `If-None-Match: *` makes S3 refuse a write to an
  # existing key (a 412), which is how the harness learns another writer got there first.
  statement {
    sid       = "DenyUnconditionalPut"
    effect    = "Deny"
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.results.arn}/*"]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    condition {
      test     = "Null"
      variable = "s3:if-none-match"
      values   = ["true"]
    }
  }

  # No conditional overwrite either: `If-Match` would replace an existing object.
  statement {
    sid       = "DenyConditionalOverwrite"
    effect    = "Deny"
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.results.arn}/*"]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    condition {
      test     = "Null"
      variable = "s3:if-match"
      values   = ["false"]
    }
  }

  statement {
    sid       = "DenyDelete"
    effect    = "Deny"
    actions   = ["s3:DeleteObject", "s3:DeleteObjectVersion"]
    resources = ["${aws_s3_bucket.results.arn}/*"]

    principals {
      type        = "*"
      identifiers = ["*"]
    }
  }

  statement {
    sid       = "DenyInsecureTransport"
    effect    = "Deny"
    actions   = ["s3:*"]
    resources = [aws_s3_bucket.results.arn, "${aws_s3_bucket.results.arn}/*"]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "results" {
  bucket = aws_s3_bucket.results.id
  policy = data.aws_iam_policy_document.results.json

  # The public access block rejects a policy that could grant public access while it is still being applied.
  depends_on = [aws_s3_bucket_public_access_block.results]
}
