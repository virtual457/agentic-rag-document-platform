resource "aws_apigatewayv2_api" "query" {
  name          = "${var.project}-query-api"
  protocol_type = "HTTP"
  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "OPTIONS", "DELETE"]
    allow_headers = ["*"]
  }
  tags = local.tags
}

resource "aws_apigatewayv2_stage" "prod" {
  api_id      = aws_apigatewayv2_api.query.id
  name        = "prod"
  auto_deploy = true
  default_route_settings {
    throttling_burst_limit = 100
    throttling_rate_limit  = 50
  }
}

# NOTE: The FastAPI query handler runs as a separate Lambda (packaged from
# backend/ via `mangum` adapter). Integration + route wiring intentionally
# left to a separate module so `terraform apply` doesn't fail before the app
# ZIP is built. See `deploy/lambda_stub/` for the placeholder.
