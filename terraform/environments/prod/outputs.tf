output "cloudfront_url" {
  description = "Live dashboard URL"
  value       = module.frontend.cloudfront_url
}

output "api_gateway_url" {
  description = "API Gateway base URL"
  value       = module.api.api_url
}

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  value       = module.auth.user_pool_id
}
