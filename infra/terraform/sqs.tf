resource "aws_sqs_queue" "ingest_dlq" {
  name                      = "${var.project}-ingest-dlq"
  message_retention_seconds = 1209600 # 14 days
  tags                      = local.tags
}

resource "aws_sqs_queue" "ingest" {
  name                       = "${var.project}-ingest"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 345600 # 4 days
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.ingest_dlq.arn
    maxReceiveCount     = 5
  })
  tags = local.tags
}

resource "aws_sqs_queue_policy" "ingest" {
  queue_url = aws_sqs_queue.ingest.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "s3.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.ingest.arn
      Condition = { ArnLike = { "aws:SourceArn" = aws_s3_bucket.ingest.arn } }
    }]
  })
}
