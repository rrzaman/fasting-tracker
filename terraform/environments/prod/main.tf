terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.45"
    }
  }
  required_version = ">= 1.0"
}

provider "aws" {
  region = var.aws_region
}

module "storage" {
  source       = "../../modules/storage"
  project_name = var.project_name
}

module "notifications" {
  source               = "../../modules/notifications"
  project_name         = var.project_name
  reminder_lambda_arn  = module.lambda.reminder_lambda_arn
  reminder_lambda_name = module.lambda.reminder_lambda_name
  depends_on           = [module.lambda]
}

module "lambda" {
  source                        = "../../modules/lambda"
  project_name                  = var.project_name
  s3_bucket                     = module.storage.lambda_bucket
  fasting_records_table         = module.storage.fasting_records_table
  health_snapshots_table        = module.storage.health_snapshots_table
  fasting_overrides_table       = module.storage.fasting_overrides_table
  reminder_log_table            = module.storage.reminder_log_table
  notification_recipients_table = module.storage.notification_recipients_table
  depends_on                    = [module.storage]
}

module "api" {
  source               = "../../modules/api"
  project_name         = var.project_name
  cognito_user_pool_id = module.auth.user_pool_id
  cognito_client_id    = module.auth.client_id
  lambda_arns = {
    get_health       = module.lambda.api_function_arns.get_health
    get_fasting      = module.lambda.api_function_arns.get_fasting
    manage_overrides = module.lambda.api_function_arns.manage_overrides
    get_status       = module.lambda.get_status_arn
  }
  depends_on = [module.lambda, module.auth]
}

module "auth" {
  source        = "../../modules/auth"
  project_name  = var.project_name
  callback_urls = [module.frontend.cloudfront_url, "http://localhost:5173"]
  depends_on    = [module.frontend]
}

module "frontend" {
  source       = "../../modules/frontend"
  project_name = var.project_name
}
