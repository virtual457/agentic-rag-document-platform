from __future__ import annotations

from functools import lru_cache

from src.config import get_settings
from src.vector_store.base import VectorStore


@lru_cache
def get_vector_store() -> VectorStore:
    backend = get_settings().vector_backend.lower()
    if backend == "chroma":
        from src.vector_store.chroma import ChromaVectorStore
        return ChromaVectorStore()
    if backend == "opensearch":
        from src.vector_store.opensearch import OpenSearchVectorStore
        return OpenSearchVectorStore()
    if backend == "pgvector":
        from src.vector_store.pgvector import PgVectorStore
        return PgVectorStore()
    raise ValueError(f"Unknown vector backend: {backend}")
