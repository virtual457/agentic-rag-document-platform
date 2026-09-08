"""Placeholder Lambda that Terraform packages before the real app image is built.

The real handler is `backend/src/ingestion/s3_worker.py:handler`. Once the app
image is deployed via container-based Lambda (recommended for the full deps),
swap this stub via `--image-uri` in the Lambda function config.
"""


def handler(event, context):  # noqa: D401
    return {"statusCode": 200, "body": "stub"}
