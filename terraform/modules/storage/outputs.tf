output "fasting_records_table" {
  description = "Fasting records DynamoDB table name"
  value       = aws_dynamodb_table.fasting_records.name
}

output "health_snapshots_table" {
  description = "Health snapshots DynamoDB table name"
  value       = aws_dynamodb_table.health_snapshots.name
}

output "fasting_overrides_table" {
  description = "Fasting overrides DynamoDB table name"
  value       = aws_dynamodb_table.fasting_overrides.name
}

output "reminder_log_table" {
  description = "Reminder deduplication log DynamoDB table name"
  value       = aws_dynamodb_table.reminder_log.name
}

output "notification_recipients_table" {
  description = "SMS notification recipients DynamoDB table name"
  value       = aws_dynamodb_table.notification_recipients.name
}

output "lambda_bucket" {
  description = "S3 bucket name for Lambda deployment zips"
  value       = aws_s3_bucket.lambda_storage.bucket
}
