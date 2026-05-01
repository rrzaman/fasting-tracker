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
