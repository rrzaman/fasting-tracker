variable "project_name" {
  type = string
}

variable "lambda_arns" {
  description = "Map of Lambda function ARNs for API integrations"
  type = object({
    get_health       = string
    get_fasting      = string
    manage_overrides = string
    get_status       = string
  })
}

variable "cognito_user_pool_id" {
  type = string
}

variable "cognito_client_id" {
  type = string
}
