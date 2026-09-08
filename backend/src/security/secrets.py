from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from src.config import get_settings
from src.observability.logger import get_logger

log = get_logger("secrets")


@lru_cache
def _client() -> Any | None:
    settings = get_settings()
    if not settings.aws_access_key_id:
        return None
    try:
        import boto3

        return boto3.client("secretsmanager", region_name=settings.aws_region)
    except Exception as e:
        log.warning("secrets.client_init_failed", error=str(e))
        return None


def get_secret(name: str, default: str | None = None) -> str | None:
    """Look up a secret. Prefers Secrets Manager, falls back to env, then default."""
    settings = get_settings()
    full_name = f"{settings.secrets_manager_prefix}{name}"
    c = _client()
    if c is not None:
        try:
            resp = c.get_secret_value(SecretId=full_name)
            return resp.get("SecretString") or default
        except Exception as e:
            log.info("secrets.miss", name=full_name, error=str(e))
    env_val = os.getenv(name.upper().replace("/", "_").replace("-", "_"))
    return env_val if env_val is not None else default
