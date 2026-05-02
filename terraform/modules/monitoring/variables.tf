variable "project_name" {
  type = string
}

variable "alarm_email" {
  description = "Email address to receive CloudWatch alarm notifications"
  type        = string
  sensitive   = true
}
