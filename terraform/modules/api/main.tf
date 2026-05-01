resource "aws_apigatewayv2_api" "main" {
  name          = "${var.project_name}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins  = ["*"]
    allow_methods  = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers  = ["content-type", "authorization"]
    expose_headers = ["*"]
    max_age        = 300
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

# Authorizer
resource "aws_apigatewayv2_authorizer" "cognito" {
  api_id           = aws_apigatewayv2_api.main.id
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  name             = "cognito-authorizer"

  jwt_configuration {
    audience = [var.cognito_client_id]
    issuer   = "https://cognito-idp.ca-west-1.amazonaws.com/${var.cognito_user_pool_id}"
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

resource "aws_apigatewayv2_integration" "get_status" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.lambda_arns.get_status
  payload_format_version = "2.0"
}

# Routes
resource "aws_apigatewayv2_route" "get_health" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "GET /health"
  target             = "integrations/${aws_apigatewayv2_integration.get_health.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito.id
}

resource "aws_apigatewayv2_route" "get_fasting" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "GET /fasting"
  target             = "integrations/${aws_apigatewayv2_integration.get_fasting.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito.id
}

resource "aws_apigatewayv2_route" "get_overrides" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "GET /overrides"
  target             = "integrations/${aws_apigatewayv2_integration.manage_overrides.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito.id
}

resource "aws_apigatewayv2_route" "post_overrides" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "POST /overrides"
  target             = "integrations/${aws_apigatewayv2_integration.manage_overrides.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito.id
}

resource "aws_apigatewayv2_route" "put_overrides" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "PUT /overrides"
  target             = "integrations/${aws_apigatewayv2_integration.manage_overrides.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito.id
}

resource "aws_apigatewayv2_route" "delete_overrides" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "DELETE /overrides"
  target             = "integrations/${aws_apigatewayv2_integration.manage_overrides.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito.id
}

resource "aws_apigatewayv2_route" "get_status" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /status"
  target    = "integrations/${aws_apigatewayv2_integration.get_status.id}"
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

resource "aws_lambda_permission" "api_get_status" {
  statement_id  = "AllowAPIGatewayInvokeStatus"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_arns.get_status
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}
