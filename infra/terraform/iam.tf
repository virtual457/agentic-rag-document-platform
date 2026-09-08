data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ingest_worker" {
  name               = "${var.project}-ingest-worker"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = local.tags
}

resource "aws_iam_role_policy_attachment" "ingest_worker_basic" {
  role       = aws_iam_role.ingest_worker.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "ingest_worker" {
  statement {
    actions   = ["s3:GetObject", "s3:GetObjectVersion"]
    resources = ["${aws_s3_bucket.ingest.arn}/*"]
  }
  statement {
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.ingest.arn]
  }
  statement {
    actions   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
    resources = [aws_sqs_queue.ingest.arn]
  }
  statement {
    actions   = ["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:Query", "dynamodb:DeleteItem", "dynamodb:UpdateItem"]
    resources = [aws_dynamodb_table.metadata.arn, aws_dynamodb_table.sessions.arn]
  }
  statement {
    actions   = ["kms:Decrypt", "kms:GenerateDataKey"]
    resources = [aws_kms_key.main.arn]
  }
  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [for s in aws_secretsmanager_secret.app : s.arn]
  }
  statement {
    actions = ["bedrock:InvokeModel"]
    resources = [
      "arn:aws:bedrock:${var.region}::foundation-model/${var.bedrock_model_id}",
      "arn:aws:bedrock:${var.region}::foundation-model/amazon.titan-embed-text-v1",
    ]
  }
  statement {
    actions   = ["aoss:APIAccessAll"]
    resources = [aws_opensearchserverless_collection.vectors.arn]
  }
  statement {
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "ingest_worker" {
  role   = aws_iam_role.ingest_worker.name
  policy = data.aws_iam_policy_document.ingest_worker.json
}
