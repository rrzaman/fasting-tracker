# EventBridge daily schedule
resource "aws_cloudwatch_event_rule" "daily_reminder" {
  name                = "fasting-tracker-daily"
  description         = "Triggers fasting reminder Lambda daily at 8pm Mountain Time (2am UTC)"
  schedule_expression = "cron(0 2 * * ? *)"

  tags = {
    Project = var.project_name
  }
}

resource "aws_cloudwatch_event_target" "reminder_target" {
  rule      = aws_cloudwatch_event_rule.daily_reminder.name
  target_id = "FastingReminderLambda"
  arn       = var.reminder_lambda_arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.reminder_lambda_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_reminder.arn
}
