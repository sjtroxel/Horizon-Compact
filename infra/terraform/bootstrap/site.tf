# The two CloudFront objects that cannot be fenced by tag (Phase 1.5 IMPLEMENTATION doc sections 9 and 11,
# decision 5). Neither supports a tag condition in IAM, so they live here, applied by hand with the dev key:
# the deploy role gets no create, update or delete on them and so cannot touch Musical Mycelium's. Neither
# object bills, and living in `bootstrap` they survive `main`'s teardown. `main` receives their ids as CI
# repository variables (outputs.tf); nothing in `main` reads this root's state.

resource "aws_cloudfront_origin_access_control" "site" {
  name                              = "${var.project}-site"
  description                       = "Signs requests from the site distribution to its private bucket."
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_response_headers_policy" "site" {
  name    = "${var.project}-site"
  comment = "Security headers for the static site; no third-party request is allowed."

  security_headers_config {
    # Nothing on the page may load from, or send data to, any host but its own.
    content_security_policy {
      content_security_policy = "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
      override                = true
    }

    strict_transport_security {
      access_control_max_age_sec = 63072000
      include_subdomains         = true
      override                   = true
    }

    content_type_options {
      override = true
    }

    referrer_policy {
      referrer_policy = "no-referrer"
      override        = true
    }
  }

  custom_headers_config {
    # Phase 1.5 decision 3: the test page is not to be indexed. This header is removed at Phase 6.5's go-live.
    items {
      header   = "X-Robots-Tag"
      value    = "noindex"
      override = true
    }
  }
}
