from __future__ import annotations

"""Lambda handler that consumes SQS events from the S3 → SQS → Step Functions
ingestion pipeline. Fetches the S3 object referenced in each SQS record, parses,
chunks, embeds, and indexes it. Idempotent by S3 object key + eTag.
"""

import asyncio
import json
from typing import Any

import boto3

from src.config import get_settings
from src.ingestion.pipeline import ingest_bytes
from src.observability.logger import get_logger

log = get_logger(__name__)


def _tenant_from_key(key: str) -> str:
    # convention: uploads/{tenant}/{filename}
    parts = key.split("/")
    if len(parts) >= 2 and parts[0] == "uploads":
        return parts[1]
    return "default"


async def _process_record(bucket: str, key: str, etag: str) -> dict[str, Any]:
    settings = get_settings()
    s3 = boto3.client("s3", region_name=settings.aws_region)
    obj = s3.get_object(Bucket=bucket, Key=key)
    data = obj["Body"].read()
    content_type = obj.get("ContentType")
    tenant = _tenant_from_key(key)
    filename = key.rsplit("/", 1)[-1]
    log.info("s3_worker.processing", bucket=bucket, key=key, etag=etag, tenant=tenant)
    return await ingest_bytes(
        tenant=tenant,
        filename=filename,
        data=data,
        content_type=content_type,
        extra_metadata={"s3_bucket": bucket, "s3_key": key, "etag": etag},
    )


def handler(event: dict[str, Any], _context: Any = None) -> dict[str, Any]:
    """AWS Lambda entrypoint."""
    results: list[dict[str, Any]] = []
    for rec in event.get("Records", []):
        body = rec.get("body")
        if isinstance(body, str):
            body = json.loads(body)
        for s3_rec in (body or {}).get("Records", []):
            bucket = s3_rec["s3"]["bucket"]["name"]
            key = s3_rec["s3"]["object"]["key"]
            etag = s3_rec["s3"]["object"].get("eTag", "")
            try:
                result = asyncio.run(_process_record(bucket, key, etag))
                results.append(result)
            except Exception as e:
                log.error("s3_worker.failed", key=key, error=str(e))
                results.append({"key": key, "error": str(e)})
    return {"processed": len(results), "results": results}
