terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
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
  phone_number_rayyan  = var.phone_number_rayyan
  phone_number_ma      = var.phone_number_ma
  phone_number_simrah  = var.phone_number_simrah
  depends_on           = [module.lambda]
}

module "lambda" {
  source                  = "../../modules/lambda"
  project_name            = var.project_name
  s3_bucket               = module.storage.lambda_bucket
  fasting_records_table   = module.storage.fasting_records_table
  health_snapshots_table  = module.storage.health_snapshots_table
  fasting_overrides_table = module.storage.fasting_overrides_table
  reminder_log_table      = module.storage.reminder_log_table
  phone_number_rayyan     = var.phone_number_rayyan
  phone_number_ma         = var.phone_number_ma
  phone_number_simrah     = var.phone_number_simrah
  depends_on              = [module.storage]
}

module "api" {
  source       = "../../modules/api"
  project_name = var.project_name
  lambda_arns  = module.lambda.api_function_arns
  depends_on   = [module.lambda]
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
