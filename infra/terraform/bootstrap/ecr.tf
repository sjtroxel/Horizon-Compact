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

# Before Phase 4, official images get a protected tag prefix excluded from expiry (Phase 4's IMPLEMENTATION doc).
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
      {
        rulePriority = 2
        description  = "Keep at most ten images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = { type = "expire" }
      },
    ]
  })
}
