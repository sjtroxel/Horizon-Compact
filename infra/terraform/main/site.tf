# The static site (Phase 1.5 IMPLEMENTATION doc section 9): a private bucket, a CloudFront distribution in front
# of it, and the bucket policy that lets only this distribution read it. The page itself is built and synced by
# the deploy workflow's `site` job, never by Terraform, so `terraform apply` alone gives a distribution that serves
# nothing until a deploy syncs a build into it.
#
# The origin access control and the response headers policy live in `bootstrap` (decision 5): neither takes a tag
# condition in IAM, so the deploy role holds no write on them. `main` receives their ids as CI repository variables
# and reads them here, so a wrong id fails the plan, not the page.

locals {
  # Computed, never written: the name holds the account id.
  site_bucket = "${var.project}-site-${local.account_id}"
}

resource "aws_s3_bucket" "site" {
  bucket = local.site_bucket

  # The bucket holds only a build, which the next deploy re-creates, so the teardown (section 10) needs no
  # emptying step. The results bucket, which holds the records, is `bootstrap`'s and keeps `prevent_destroy`.
  force_destroy = true
}

# Private, all four blocks on. The bucket policy below names a service principal and one distribution's ARN, so
# S3 does not judge it public and `block_public_policy` can stay on.
resource "aws_s3_bucket_public_access_block" "site" {
  bucket = aws_s3_bucket.site.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

data "aws_cloudfront_origin_access_control" "site" {
  id = var.site_origin_access_control_id
}

data "aws_cloudfront_response_headers_policy" "site" {
  id = var.site_response_headers_policy_id
}

# Resolved by name, so the id is not a pasted UUID nobody can check by eye.
data "aws_cloudfront_cache_policy" "optimized" {
  name = "Managed-CachingOptimized"
}

# Each page is its own file, <path>/index.html (Phase 6.5 IMPLEMENTATION doc, decision B): the function serves a
# path ending in "/" its own index.html and redirects a page path missing its "/" (functions/site-paths.js). Named
# with the project's prefix and tagged by default_tags, which is what the deploy role's function grants are fenced by.
resource "aws_cloudfront_function" "site_paths" {
  name    = "${var.project}-site-paths"
  runtime = "cloudfront-js-2.0"
  comment = "${var.project}: a page path serves its own index.html"
  publish = true
  code    = file("${path.module}/functions/site-paths.js")
}

resource "aws_cloudfront_distribution" "site" {
  enabled             = true
  comment             = "${var.project} site"
  default_root_object = "index.html"
  price_class         = "PriceClass_100"

  # An apply returns once the distribution exists; the site job's smoke test waits for the edge instead.
  wait_for_deployment = false

  origin {
    domain_name              = aws_s3_bucket.site.bucket_regional_domain_name
    origin_id                = "site"
    origin_access_control_id = data.aws_cloudfront_origin_access_control.site.id
  }

  default_cache_behavior {
    target_origin_id           = "site"
    viewer_protocol_policy     = "redirect-to-https"
    allowed_methods            = ["GET", "HEAD"]
    cached_methods             = ["GET", "HEAD"]
    compress                   = true
    cache_policy_id            = data.aws_cloudfront_cache_policy.optimized.id
    response_headers_policy_id = data.aws_cloudfront_response_headers_policy.site.id

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.site_paths.arn
    }
  }

  # A private bucket answers a missing key with 403, not 404, so both are an address that names nothing: the
  # not-found page, with status 404 (decision B). Until Phase 6.5 both served the root page with 200, which gave
  # every deep link the root's title and card. Every build the site serves has a 404.html (check-dist).
  dynamic "custom_error_response" {
    for_each = [403, 404]

    content {
      error_code            = custom_error_response.value
      response_code         = 404
      response_page_path    = "/404.html"
      error_caching_min_ttl = 0
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # The *.cloudfront.net certificate; the public URL is the Vercel rewrite (C5), so no custom domain here.
  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

# CloudFront signs as the service principal; `AWS:SourceArn` limits the grant to this one distribution, so no
# other distribution, in this account or any other, can read the bucket.
data "aws_iam_policy_document" "site" {
  statement {
    sid       = "CloudFrontReadsThroughTheAccessControl"
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.site.arn}/*"]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.site.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "site" {
  bucket = aws_s3_bucket.site.id
  policy = data.aws_iam_policy_document.site.json

  # Written before the public access block settles, the policy can be refused.
  depends_on = [aws_s3_bucket_public_access_block.site]
}
