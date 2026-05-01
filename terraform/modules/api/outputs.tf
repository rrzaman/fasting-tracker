output "api_url" {
  description = "API Gateway invoke URL"
  value       = "${aws_apigatewayv2_api.main.api_endpoint}/prod"
}

output "api_id" {
  description = "API Gateway ID"
  value       = aws_apigatewayv2_api.main.id
}
