data "aws_iam_policy_document" "sfn_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "sfn" {
  name               = "${var.project}-sfn"
  assume_role_policy = data.aws_iam_policy_document.sfn_assume.json
}

resource "aws_iam_role_policy" "sfn" {
  role = aws_iam_role.sfn.name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["lambda:InvokeFunction"]
      Resource = aws_lambda_function.ingest_worker.arn
    }]
  })
}

resource "aws_sfn_state_machine" "ingest" {
  name     = "${var.project}-ingest"
  role_arn = aws_iam_role.sfn.arn
  definition = jsonencode({
    Comment = "Document ingestion: parse -> chunk -> embed -> index"
    StartAt = "Ingest"
    States = {
      Ingest = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = aws_lambda_function.ingest_worker.arn
          "Payload.$"  = "$"
        }
        Retry = [{
          ErrorEquals     = ["States.ALL"]
          IntervalSeconds = 2
          MaxAttempts     = 3
          BackoffRate     = 2
        }]
        Catch = [{
          ErrorEquals = ["States.ALL"]
          Next        = "Fail"
        }]
        End = true
      }
      Fail = { Type = "Fail" }
    }
  })
  tags = local.tags
}
