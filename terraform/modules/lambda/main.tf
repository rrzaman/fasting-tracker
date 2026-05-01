# Reminder function — full package with dependencies
resource "aws_lambda_function" "reminder" {
  function_name = "${var.project_name}-reminder"
  role          = aws_iam_role.lambda_role.arn
  handler       = "reminder_function.handler"
  runtime       = "python3.13"
  timeout       = 60
  memory_size   = 128

  s3_bucket = var.s3_bucket
  s3_key    = "lambda/fasting-tracker-reminder.zip"

  environment {
    variables = {
      FASTING_TABLE       = var.fasting_records_table
      HEALTH_TABLE        = var.health_snapshots_table
      OVERRIDES_TABLE     = var.fasting_overrides_table
      REMINDER_LOG_TABLE  = var.reminder_log_table
      PHONE_NUMBER_RAYYAN = var.phone_number_rayyan
      PHONE_NUMBER_MA     = var.phone_number_ma
      PHONE_NUMBER_SIMRAH = var.phone_number_simrah
    }
  }

  tags = {
    Project = var.project_name
  }
}

# API Lambda functions — lightweight, no dependencies
resource "aws_lambda_function" "get_health" {
  function_name = "${var.project_name}-get-health"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.handler"
  runtime       = "python3.13"
  timeout       = 30
  memory_size   = 128

  s3_bucket = var.s3_bucket
  s3_key    = "lambda/fasting-tracker-get-health.zip"

  environment {
    variables = {
      HEALTH_TABLE = var.health_snapshots_table
    }
  }

  tags = {
    Project = var.project_name
  }
}

resource "aws_lambda_function" "get_fasting" {
  function_name = "${var.project_name}-get-fasting"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.handler"
  runtime       = "python3.13"
  timeout       = 30
  memory_size   = 128

  s3_bucket = var.s3_bucket
  s3_key    = "lambda/fasting-tracker-get-fasting.zip"

  environment {
    variables = {
      FASTING_TABLE   = var.fasting_records_table
      OVERRIDES_TABLE = var.fasting_overrides_table
    }
  }

  tags = {
    Project = var.project_name
  }
}

resource "aws_lambda_function" "manage_overrides" {
  function_name = "${var.project_name}-manage-overrides"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.handler"
  runtime       = "python3.13"
  timeout       = 30
  memory_size   = 128

  s3_bucket = var.s3_bucket
  s3_key    = "lambda/fasting-tracker-manage-overrides.zip"

  environment {
    variables = {
      OVERRIDES_TABLE = var.fasting_overrides_table
      FASTING_TABLE   = var.fasting_records_table
    }
  }

  tags = {
    Project = var.project_name
  }
}

resource "aws_lambda_function" "get_status" {
  function_name = "${var.project_name}-get-status"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.handler"
  runtime       = "python3.13"
  timeout       = 30
  memory_size   = 128

  s3_bucket = var.s3_bucket
  s3_key    = "lambda/fasting-tracker-get-status.zip"

  environment {
    variables = {
      FASTING_TABLE      = var.fasting_records_table
      HEALTH_TABLE       = var.health_snapshots_table
      REMINDER_LOG_TABLE = var.reminder_log_table
      REMINDER_LAMBDA    = "fasting-tracker-reminder"
    }
  }

  tags = {
    Project = var.project_name
  }
}
