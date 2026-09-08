from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    frontend_origin: str = "http://localhost:3000"
    log_level: str = "INFO"

    # Auth
    jwt_secret: str = "change_me"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 1440

    # Metadata store — production default: DynamoDB
    metadata_backend: str = "dynamodb"       # dynamodb | mongo
    dynamodb_table_metadata: str = "docintel-metadata"
    dynamodb_table_sessions: str = "docintel-sessions"
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "docintel"

    # Vector store — production default: OpenSearch Serverless
    vector_backend: str = "opensearch"       # opensearch | chroma | pgvector
    opensearch_endpoint: str = ""
    opensearch_index: str = "docintel-vectors"
    chroma_path: str = "./chromadb_store"
    pgvector_dsn: str = "postgresql://user:pass@localhost:5432/docintel"

    # LLM — production default: AWS Bedrock LLaMA 3
    llm_backend: str = "bedrock"             # bedrock | gemini
    bedrock_model_id: str = "meta.llama3-70b-instruct-v1:0"
    bedrock_region: str = "us-east-1"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # Embeddings — production default: AWS Titan
    embeddings_backend: str = "titan"        # titan | gemini | sentence_transformers
    titan_model_id: str = "amazon.titan-embed-text-v1"
    gemini_embedding_model: str = "text-embedding-004"
    sentence_transformer_model: str = "all-MiniLM-L6-v2"

    # Ingestion
    s3_bucket_ingest: str = "docintel-ingest"
    sqs_ingest_queue_url: str = ""
    step_functions_arn: str = ""
    chunk_size_tokens: int = 500
    chunk_overlap_tokens: int = 50
    retrieval_top_k: int = 5
    rerank_enabled: bool = True
    keyword_hybrid_enabled: bool = True

    # Quality pipeline
    quality_threshold: int = 90
    max_eval_rounds: int = 3
    max_factuality_rounds: int = 2

    # Session
    session_timeout_seconds: int = 300
    question_timeout_seconds: int = 60

    # Caching — production default: Redis
    cache_backend: str = "redis"             # redis | memory
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_embedding: int = 86400
    cache_ttl_retrieval: int = 300
    cache_ttl_answer: int = 600
    cache_ttl_metadata: int = 3600

    # Tools
    jira_base_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    servicenow_base_url: str = ""
    servicenow_user: str = ""
    servicenow_password: str = ""
    slack_webhook_url: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    github_token: str = ""

    # AWS
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    kms_key_id: str = ""
    secrets_manager_prefix: str = "docintel/"

    # Observability
    cloudwatch_log_group: str = "/docintel/app"
    cloudwatch_namespace: str = "DocIntel"
    enable_structured_logs: bool = True
    enable_metrics: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
