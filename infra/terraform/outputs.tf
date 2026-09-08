output "ingest_bucket" {
  value = aws_s3_bucket.ingest.bucket
}

output "ingest_queue_url" {
  value = aws_sqs_queue.ingest.id
}

output "ingest_dlq_url" {
  value = aws_sqs_queue.ingest_dlq.id
}

output "sfn_state_machine_arn" {
  value = aws_sfn_state_machine.ingest.arn
}

output "metadata_table" {
  value = aws_dynamodb_table.metadata.name
}

output "sessions_table" {
  value = aws_dynamodb_table.sessions.name
}

output "opensearch_endpoint" {
  value = aws_opensearchserverless_collection.vectors.collection_endpoint
}

output "kms_key_arn" {
  value = aws_kms_key.main.arn
}

output "query_api_endpoint" {
  value = aws_apigatewayv2_api.query.api_endpoint
}
