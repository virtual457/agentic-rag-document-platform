from __future__ import annotations

from functools import lru_cache

from src.config import get_settings
from src.metadata_store.base import MetadataStore


@lru_cache
def get_metadata_store() -> MetadataStore:
    backend = get_settings().metadata_backend.lower()
    if backend == "mongo":
        from src.metadata_store.mongo import MongoMetadataStore
        return MongoMetadataStore()
    if backend == "dynamodb":
        from src.metadata_store.dynamodb import DynamoMetadataStore
        return DynamoMetadataStore()
    raise ValueError(f"Unknown metadata backend: {backend}")
