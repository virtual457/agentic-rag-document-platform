from __future__ import annotations

import asyncio

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import get_settings


class GeminiEmbedder:
    name = "gemini"
    dim = 768

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        genai.configure(api_key=settings.gemini_api_key)
        self._model = f"models/{settings.gemini_embedding_model}"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    def _embed_batch(self, texts: list[str], task_type: str) -> list[list[float]]:
        result = genai.embed_content(model=self._model, content=texts, task_type=task_type)
        emb = result["embedding"]
        if isinstance(emb, list) and emb and isinstance(emb[0], float):
            emb = [emb]
        return emb

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        loop = asyncio.get_running_loop()
        out: list[list[float]] = []
        for i in range(0, len(texts), 100):
            batch = texts[i : i + 100]
            emb = await loop.run_in_executor(None, self._embed_batch, batch, "retrieval_document")
            out.extend(emb)
        return out

    async def embed_query(self, query: str) -> list[float]:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, self._embed_batch, [query], "retrieval_query")
        return result[0]
