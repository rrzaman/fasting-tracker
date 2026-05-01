resource "aws_apigatewayv2_api" "main" {
  name          = "${var.project_name}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["content-type"]
  }

  tags = {
    Project = var.project_name
  }
}

resource "aws_apigatewayv2_stage" "prod" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "prod"
  auto_deploy = true

  tags = {
    Project = var.project_name
  }
}

# Lambda integrations
resource "aws_apigatewayv2_integration" "get_health" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.lambda_arns.get_health
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "get_fasting" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.lambda_arns.get_fasting
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "manage_overrides" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.lambda_arns.manage_overrides
  payload_format_version = "2.0"
}

# Routes
resource "aws_apigatewayv2_route" "get_health" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /health"
  target    = "integrations/${aws_apigatewayv2_integration.get_health.id}"
}

resource "aws_apigatewayv2_route" "get_fasting" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /fasting"
  target    = "integrations/${aws_apigatewayv2_integration.get_fasting.id}"
}

resource "aws_apigatewayv2_route" "get_overrides" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /overrides"
  target    = "integrations/${aws_apigatewayv2_integration.manage_overrides.id}"
}

resource "aws_apigatewayv2_route" "post_overrides" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /overrides"
  target    = "integrations/${aws_apigatewayv2_integration.manage_overrides.id}"
}

resource "aws_apigatewayv2_route" "put_overrides" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "PUT /overrides"
  target    = "integrations/${aws_apigatewayv2_integration.manage_overrides.id}"
}

resource "aws_apigatewayv2_route" "delete_overrides" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "DELETE /overrides"
  target    = "integrations/${aws_apigatewayv2_integration.manage_overrides.id}"
}

# Lambda permissions for API Gateway
resource "aws_lambda_permission" "api_get_health" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_arns.get_health
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_get_fasting" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_arns.get_fasting
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_manage_overrides" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_arns.manage_overrides
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}
