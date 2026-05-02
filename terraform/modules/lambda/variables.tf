variable "project_name" {
  type = string
}

variable "s3_bucket" {
  description = "S3 bucket containing Lambda deployment zips"
  type        = string
}

variable "fasting_records_table" {
  type = string
}

variable "health_snapshots_table" {
  type = string
}

variable "fasting_overrides_table" {
  type = string
}

variable "reminder_log_table" {
  type = string
}

variable "notification_recipients_table" {
  type = string
}
