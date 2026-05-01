output "event_rule_arn" {
  description = "EventBridge rule ARN"
  value       = aws_cloudwatch_event_rule.daily_reminder.arn
}
