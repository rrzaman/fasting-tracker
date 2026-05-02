# DynamoDB Tables

resource "aws_dynamodb_table" "fasting_records" {
  name         = "fasting-records"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "date"

  attribute {
    name = "date"
    type = "S"
  }

  tags = {
    Project = var.project_name
  }
}

resource "aws_dynamodb_table" "health_snapshots" {
  name         = "health-snapshots"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "date"
  range_key    = "metric"

  attribute {
    name = "date"
    type = "S"
  }

  attribute {
    name = "metric"
    type = "S"
  }

  tags = {
    Project = var.project_name
  }
}

resource "aws_dynamodb_table" "fasting_overrides" {
  name         = "fasting-overrides"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "date"

  attribute {
    name = "date"
    type = "S"
  }

  tags = {
    Project = var.project_name
  }
}

resource "aws_dynamodb_table" "reminder_log" {
  name         = "reminder-log"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "date"
  range_key    = "fast_type"

  attribute {
    name = "date"
    type = "S"
  }

  attribute {
    name = "fast_type"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = {
    Project = var.project_name
  }
}

resource "aws_dynamodb_table" "notification_recipients" {
  name         = "notification-recipients"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "phone"

  attribute {
    name = "phone"
    type = "S"
  }

  tags = {
    Project = var.project_name
  }
}

# S3 Buckets

resource "aws_s3_bucket" "lambda_storage" {
  bucket = "${var.project_name}-rayyan"

  tags = {
    Project = var.project_name
  }
}
