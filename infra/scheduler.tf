resource "aws_scheduler_schedule_group" "main" {
  name = local.name_prefix
}

# ── Poll every 15 min during world-open hours (11:00–23:00 UTC) ───────────────
resource "aws_scheduler_schedule" "poll" {
  name       = "${local.name_prefix}-poll"
  group_name = aws_scheduler_schedule_group.main.name

  flexible_time_window { mode = "OFF" }

  schedule_expression          = "cron(*/15 11-23 * * ? *)"
  schedule_expression_timezone = "UTC"

  target {
    arn      = aws_lambda_function.scraper.arn
    role_arn = aws_iam_role.scheduler.arn
    input    = jsonencode({ type = "poll" })
  }
}

# ── Daily snapshot at world open (11:00 UTC) ──────────────────────────────────
resource "aws_scheduler_schedule" "snapshot_open" {
  name       = "${local.name_prefix}-snapshot-open"
  group_name = aws_scheduler_schedule_group.main.name

  flexible_time_window { mode = "OFF" }

  schedule_expression          = "cron(0 11 * * ? *)"
  schedule_expression_timezone = "UTC"

  target {
    arn      = aws_lambda_function.scraper.arn
    role_arn = aws_iam_role.scheduler.arn
    input    = jsonencode({ type = "snapshot", label = "world_open" })
  }
}

# ── Daily snapshot at world close (05:00 UTC) ─────────────────────────────────
resource "aws_scheduler_schedule" "snapshot_close" {
  name       = "${local.name_prefix}-snapshot-close"
  group_name = aws_scheduler_schedule_group.main.name

  flexible_time_window { mode = "OFF" }

  schedule_expression          = "cron(0 5 * * ? *)"
  schedule_expression_timezone = "UTC"

  target {
    arn      = aws_lambda_function.scraper.arn
    role_arn = aws_iam_role.scheduler.arn
    input    = jsonencode({ type = "snapshot", label = "world_close" })
  }
}
