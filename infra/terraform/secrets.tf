locals {
  secret_names = [
    "gemini-api-key",
    "jwt-secret",
    "mongo-uri",
    "jira-api-token",
    "servicenow-password",
    "slack-webhook-url",
    "smtp-password",
    "github-token",
  ]
}

resource "aws_secretsmanager_secret" "app" {
  for_each   = toset(local.secret_names)
  name       = "${var.project}/${each.key}"
  kms_key_id = aws_kms_key.main.arn
  tags       = local.tags
}
