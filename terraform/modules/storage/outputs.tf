output "fasting_records_table" {
  description = "Fasting records DynamoDB table name"
  value       = "fasting-records"
}

output "health_snapshots_table" {
  description = "Health snapshots DynamoDB table name"
  value       = aws_dynamodb_table.health_snapshots.name
}

output "fasting_overrides_table" {
  description = "Fasting overrides DynamoDB table name"
  value       = "fasting-overrides"
}

output "lambda_bucket" {
  description = "S3 bucket name for Lambda zips"
  value       = aws_s3_bucket.lambda_storage.bucket
}
