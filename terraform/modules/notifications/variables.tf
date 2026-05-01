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

variable "phone_number_rayyan" {
  type      = string
  sensitive = true
}

variable "phone_number_ma" {
  type      = string
  sensitive = true
}

variable "phone_number_simrah" {
  type      = string
  sensitive = true
}
