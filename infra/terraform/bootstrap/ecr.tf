# The image repository (Phase 1 decision 1: it lives here, not in `main`).
#
# In `main` it would be a chicken-and-egg (CI must push an image before `main` can name it by digest) and
# `terraform destroy` on `main` would delete the images whose digests pin every result. Tags are immutable, so
# a tag always names the same bytes.

resource "aws_ecr_repository" "sweep" {
  name                 = var.project
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# Untagged images expire after a day and nothing else expires. The records carry the image digest of the run
# that wrote them, so an image a record names must stay pullable; the earlier rule that kept only the ten
# newest images expired Phase 4's official image and Phase 1's skeleton image (KNOWN-GAPS, OPEN 2026-11-04).
# Phase 1 section 8 item 2's protected tag prefix, "before Phase 4", was never written. Images share most of
# their layers, so keeping them all costs cents a month; the close of Phase 1.5 measures it.
resource "aws_ecr_lifecycle_policy" "sweep" {
  repository = aws_ecr_repository.sweep.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Untagged images expire after one day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = { type = "expire" }
      },
    ]
  })
}
