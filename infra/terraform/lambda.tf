data "archive_file" "ingest_worker" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda_stub"
  output_path = "${path.module}/build/ingest_worker.zip"
}

resource "aws_lambda_function" "ingest_worker" {
  function_name    = "${var.project}-ingest-worker"
  role             = aws_iam_role.ingest_worker.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.ingest_worker.output_path
  source_code_hash = data.archive_file.ingest_worker.output_base64sha256
  timeout          = 300
  memory_size      = 1024
  tags             = local.tags

  environment {
    variables = {
      METADATA_BACKEND      = "dynamodb"
      VECTOR_BACKEND        = "opensearch"
      LLM_BACKEND           = "bedrock"
      EMBEDDINGS_BACKEND    = "titan"
      BEDROCK_MODEL_ID      = var.bedrock_model_id
      BEDROCK_REGION        = var.region
      DYNAMODB_TABLE_METADATA = aws_dynamodb_table.metadata.name
      DYNAMODB_TABLE_SESSIONS = aws_dynamodb_table.sessions.name
      OPENSEARCH_ENDPOINT   = aws_opensearchserverless_collection.vectors.collection_endpoint
      OPENSEARCH_INDEX      = "${var.project}-vectors"
      SECRETS_MANAGER_PREFIX = "${var.project}/"
    }
  }
}

resource "aws_lambda_event_source_mapping" "ingest_worker_sqs" {
  event_source_arn = aws_sqs_queue.ingest.arn
  function_name    = aws_lambda_function.ingest_worker.arn
  batch_size       = 5
}
