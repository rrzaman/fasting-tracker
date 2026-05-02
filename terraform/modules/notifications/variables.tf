variable "project_name" {
  type = string
}

variable "reminder_lambda_arn" {
  description = "ARN of the reminder Lambda function"
  type        = string
}

variable "reminder_lambda_name" {
  description = "Name of the reminder Lambda function"
  type        = string
}

