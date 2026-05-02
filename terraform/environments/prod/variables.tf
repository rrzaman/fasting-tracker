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

variable "alarm_email" {
  description = "Email address for CloudWatch alarm notifications"
  type        = string
  sensitive   = true
}
