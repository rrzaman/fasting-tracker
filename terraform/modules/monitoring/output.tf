output "alarm_topic_arn" {
  description = "SNS topic ARN for CloudWatch alarms"
  value       = aws_sns_topic.alarms.arn
}
