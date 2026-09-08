from __future__ import annotations

from functools import lru_cache

from src.config import get_settings
from src.embeddings.base import EmbeddingProvider


@lru_cache
def get_embedder() -> EmbeddingProvider:
    backend = get_settings().embeddings_backend.lower()
    if backend == "gemini":
        from src.embeddings.gemini import GeminiEmbedder
        return GeminiEmbedder()
    if backend == "titan":
        from src.embeddings.titan import TitanEmbedder
        return TitanEmbedder()
    if backend == "sentence_transformers":
        from src.embeddings.sentence_transformers import SentenceTransformerEmbedder
        return SentenceTransformerEmbedder()
    raise ValueError(f"Unknown embeddings backend: {backend}")
