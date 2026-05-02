# SNS topic for alarm notifications
resource "aws_sns_topic" "alarms" {
  name = "${var.project_name}-alarms"

  tags = {
    Project = var.project_name
  }
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alarms.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

# API Lambda errors alarm — any 5xx errors across API functions
resource "aws_cloudwatch_metric_alarm" "api_errors" {
  alarm_name          = "${var.project_name}-api-errors"
  alarm_description   = "API Lambda functions are throwing errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = "${var.project_name}-get-health"
  }

  alarm_actions = [aws_sns_topic.alarms.arn]

  tags = {
    Project = var.project_name
  }
}

# DynamoDB throttling alarm
resource "aws_cloudwatch_metric_alarm" "dynamodb_throttles" {
  alarm_name          = "${var.project_name}-dynamodb-throttles"
  alarm_description   = "DynamoDB read/write requests are being throttled"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ThrottledRequests"
  namespace           = "AWS/DynamoDB"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  treat_missing_data  = "notBreaching"

  dimensions = {
    TableName = "fasting-records"
  }

  alarm_actions = [aws_sns_topic.alarms.arn]

  tags = {
    Project = var.project_name
  }
}

# Lambda duration alarm — catches hanging functions
resource "aws_cloudwatch_metric_alarm" "reminder_duration" {
  alarm_name          = "${var.project_name}-reminder-duration"
  alarm_description   = "Reminder Lambda is running unusually long"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 86400
  statistic           = "Maximum"
  threshold           = 50000
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = "${var.project_name}-reminder"
  }

  alarm_actions = [aws_sns_topic.alarms.arn]

  tags = {
    Project = var.project_name
  }
}

# Reminder Lambda error alarm
resource "aws_cloudwatch_metric_alarm" "reminder_errors" {
  alarm_name          = "${var.project_name}-reminder-errors"
  alarm_description   = "Reminder Lambda function is throwing errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 86400
  statistic           = "Sum"
  threshold           = 0
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = "${var.project_name}-reminder"
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
  ok_actions    = [aws_sns_topic.alarms.arn]

  tags = {
    Project = var.project_name
  }
}

# Fasting Error Lambda error alarm
resource "aws_cloudwatch_metric_alarm" "get_fasting_errors" {
  alarm_name          = "${var.project_name}-get-fasting-errors"
  alarm_description   = "get-fasting Lambda is throwing errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  treat_missing_data  = "notBreaching"
  dimensions          = { FunctionName = "${var.project_name}-get-fasting" }
  alarm_actions       = [aws_sns_topic.alarms.arn]
  tags                = { Project = var.project_name }
}

# Manage Overrides Lambda error alarm
resource "aws_cloudwatch_metric_alarm" "manage_overrides_errors" {
  alarm_name          = "${var.project_name}-manage-overrides-errors"
  alarm_description   = "manage-overrides Lambda is throwing errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  treat_missing_data  = "notBreaching"
  dimensions          = { FunctionName = "${var.project_name}-manage-overrides" }
  alarm_actions       = [aws_sns_topic.alarms.arn]
  tags                = { Project = var.project_name }
}

# Get Status Lambda error alarm
resource "aws_cloudwatch_metric_alarm" "get_status_errors" {
  alarm_name          = "${var.project_name}-get-status-errors"
  alarm_description   = "get-status Lambda is throwing errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  treat_missing_data  = "notBreaching"
  dimensions          = { FunctionName = "${var.project_name}-get-status" }
  alarm_actions       = [aws_sns_topic.alarms.arn]
  tags                = { Project = var.project_name }
}
