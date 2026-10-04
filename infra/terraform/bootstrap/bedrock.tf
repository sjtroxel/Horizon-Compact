# Application inference profiles: free (the price is the model's price), taggable, and the vehicle for the
# tag test in section 7 of the IMPLEMENTATION doc. They live here so they exist before the first call and
# survive `main`'s teardown.
#
# The open question (KNOWN-GAPS.md): does a profile's tag land on Marketplace-billed Claude charges in Cost
# Explorer? It closes only by measurement. Nova Pro is measured too, because "documented" is not "observed".

resource "aws_bedrock_inference_profile" "sonnet_4_6" {
  name        = "${var.project}-sonnet-4-6"
  description = "Tag-carrying wrapper around the US geo profile for Claude Sonnet 4.6."

  # Sonnet 4.6 has no in-region endpoint in any US region, so the profile wraps the cross-region profile.
  # The account id is built from the caller identity at plan time, never written in a file.
  model_source {
    copy_from = "arn:aws:bedrock:${var.region}:${local.account_id}:inference-profile/us.anthropic.claude-sonnet-4-6"
  }

  tags = {
    Project = var.project
  }
}

resource "aws_bedrock_inference_profile" "nova_pro" {
  name        = "${var.project}-nova-pro"
  description = "Tag-carrying wrapper around in-region Amazon Nova Pro."

  model_source {
    copy_from = "arn:aws:bedrock:${var.region}::foundation-model/amazon.nova-pro-v1:0"
  }

  tags = {
    Project = var.project
  }
}
