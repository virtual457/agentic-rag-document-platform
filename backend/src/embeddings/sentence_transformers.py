from __future__ import annotations

import asyncio

from src.config import get_settings


class SentenceTransformerEmbedder:
    """Local, free fallback. Loads model on first use."""

    name = "sentence_transformers"

    def __init__(self) -> None:
        from sentence_transformers import SentenceTransformer

        settings = get_settings()
        self._model = SentenceTransformer(settings.sentence_transformer_model)
        self.dim = int(self._model.get_sentence_embedding_dimension() or 384)

    def _encode(self, texts: list[str]) -> list[list[float]]:
        return [v.tolist() for v in self._model.encode(texts, normalize_embeddings=True)]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._encode, texts)

    async def embed_query(self, query: str) -> list[float]:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, self._encode, [query])
        return result[0]
