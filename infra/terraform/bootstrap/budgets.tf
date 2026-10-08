# This project's budgets. They live in bootstrap so they exist before the first model call and survive the
# teardown test of `main` (Phase 0.5 decision 2).
#
# One CUSTOM period covering the project, because the $80 ceiling is cumulative: a monthly budget resets
# and would never see it. If `terraform validate` or the apply refuses CUSTOM (the provider documents four
# units without it), the fallback is time_unit = "ANNUALLY" with the same start date, recorded in the
# IMPLEMENTATION doc.
#
# Rules from planning/04 section 3.3, all load-bearing:
#   - ACTUAL notifications only. A forecast alert on bursty spend projected $9.17 against $0.001 of actual
#     spend on 2026-10-02; an alarm that is usually wrong gets ignored. A test fails if FORECASTED appears.
#   - include_credit = false, so the budget reads gross spend while credits drain (Musical Mycelium's
#     2026-09-19 trap). A test fails if any budget omits it.
#   - Musical Mycelium's three budgets are not touched. They are read before and after the apply.
#
# Added budgets cost nothing: notification-only budgets are free (checked 2026-10-04, AWS Budgets pricing).
# Subscriber addresses come from an untracked variable, never a tracked file.

resource "aws_budgets_budget" "sonnet_line" {
  # Not created until the Service string is known (variables.tf, sonnet_service_name).
  count = var.sonnet_service_name == "" ? 0 : 1

  name         = "${var.project}-sonnet-line"
  budget_type  = "COST"
  limit_amount = var.budget_limit_usd
  limit_unit   = "USD"
  time_unit    = "CUSTOM"

  time_period_start = var.budget_start
  time_period_end   = var.budget_end

  # Claude on Bedrock is billed through AWS Marketplace under the model provider, not under "Amazon Bedrock".
  # The exact string is read from the Budgets console's own filter list (variables.tf).
  cost_filter {
    name   = "Service"
    values = [var.sonnet_service_name]
  }

  cost_types {
    include_credit = false
  }

  dynamic "notification" {
    for_each = var.budget_alert_thresholds_usd

    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = notification.value
      threshold_type             = "ABSOLUTE_VALUE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = [var.alert_email]
    }
  }
}

# Decision 3 (c), DECIDED 2026-10-08 (his): the Project tag landed on both billing lines in Cost Explorer for
# 2026-10-04 (the Marketplace-billed Sonnet 4.6 token lines and Nova Pro's), so this budget counts this project's
# spend alone, Nova Pro included, without Musical Mycelium's judge calls. Calls reach it only through the tagged
# application inference profiles (bedrock.tf). Same period, amounts and rules as the Sonnet-line budget, which stays.
resource "aws_budgets_budget" "project_tag" {
  name         = "${var.project}-project-tag"
  budget_type  = "COST"
  limit_amount = var.budget_limit_usd
  limit_unit   = "USD"
  time_unit    = "CUSTOM"

  time_period_start = var.budget_start
  time_period_end   = var.budget_end

  cost_filter {
    name = "TagKeyValue"
    # format(), not "$${...}": in HCL "$${" is the escape for a literal "${", which would match nothing.
    values = [format("user:Project$%s", var.project)]
  }

  cost_types {
    include_credit = false
  }

  dynamic "notification" {
    for_each = var.budget_alert_thresholds_usd

    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = notification.value
      threshold_type             = "ABSOLUTE_VALUE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = [var.alert_email]
    }
  }
}
