resource "aws_s3_bucket" "ingest" {
  bucket        = "${var.project}-ingest-${data.aws_caller_identity.current.account_id}"
  force_destroy = true
  tags          = local.tags
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ingest" {
  bucket = aws_s3_bucket.ingest.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.main.arn
    }
  }
}

resource "aws_s3_bucket_versioning" "ingest" {
  bucket = aws_s3_bucket.ingest.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_public_access_block" "ingest" {
  bucket                  = aws_s3_bucket.ingest.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_notification" "ingest" {
  bucket = aws_s3_bucket.ingest.id

  queue {
    queue_arn     = aws_sqs_queue.ingest.arn
    events        = ["s3:ObjectCreated:*"]
    filter_prefix = "uploads/"
  }
  depends_on = [aws_sqs_queue_policy.ingest]
}

data "aws_caller_identity" "current" {}
