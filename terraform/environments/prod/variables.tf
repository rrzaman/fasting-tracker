variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "ca-west-1"
}

variable "project_name" {
  description = "Project name prefix for all resources"
  type        = string
  default     = "fasting-tracker"
}

variable "phone_number_rayyan" {
  description = "Rayyan's phone number for SMS reminders"
  type        = string
  sensitive   = true
}

variable "phone_number_ma" {
  description = "Ma's phone number for SMS reminders"
  type        = string
  sensitive   = true
}

variable "phone_number_simrah" {
  description = "Simrah's phone number for SMS reminders"
  type        = string
  sensitive   = true
}
