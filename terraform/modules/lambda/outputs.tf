output "api_function_arns" {
  description = "ARNs of API Lambda functions for API Gateway integration"
  value = {
    get_health       = aws_lambda_function.get_health.arn
    get_fasting      = aws_lambda_function.get_fasting.arn
    manage_overrides = aws_lambda_function.manage_overrides.arn
  }
}

output "lambda_role_arn" {
  description = "IAM role ARN used by Lambda functions"
  value       = aws_iam_role.lambda_role.arn
}

output "reminder_lambda_arn" {
  description = "ARN of the reminder Lambda function"
  value       = aws_lambda_function.reminder.arn
}

output "reminder_lambda_name" {
  description = "Name of the reminder Lambda function"
  value       = aws_lambda_function.reminder.function_name
}

output "get_status_arn" {
  value = aws_lambda_function.get_status.arn
}
