# Terraform: AWS infrastructure

Provisions the AWS pieces the platform expects when running production-mode:

- **S3** bucket for raw document uploads (`aws_s3_bucket.ingest`)
- **SQS** queue + DLQ for ingestion events (`aws_sqs_queue.ingest`, `.ingest_dlq`)
- **Step Functions** state machine (`aws_sfn_state_machine.ingest`)
- **Lambda** for the ingestion worker (`aws_lambda_function.ingest_worker`)
- **API Gateway** REST API in front of a query Lambda (`aws_apigatewayv2_api.query`)
- **DynamoDB** metadata + session tables
- **OpenSearch Serverless** collection for the vector store
- **KMS** key encrypting S3 + DynamoDB
- **Secrets Manager** entries (Gemini/Bedrock keys, MongoDB DSN, JWT secret, Jira/Slack tokens)
- **IAM** service-role wiring for Lambda ↔ S3/SQS/DynamoDB/OpenSearch/Secrets/KMS

## Usage

```bash
cd infra/terraform
terraform init
terraform plan -var="project=docintel" -var="region=us-east-1"
terraform apply
```

Costs: everything scale-to-zero except the OpenSearch Serverless collection (~$25/mo minimum) and DynamoDB on-demand (near-$0 idle). Delete via `terraform destroy` when idle.

## Outputs

- `ingest_bucket` — S3 bucket for `aws s3 cp <file> s3://<bucket>/uploads/<tenant>/<file>`
- `query_api_url` — HTTPS endpoint the frontend calls
- `sfn_state_machine_arn` — Step Functions ARN
- `metadata_table` / `sessions_table` — DynamoDB names
- `opensearch_endpoint` — OpenSearch collection endpoint
