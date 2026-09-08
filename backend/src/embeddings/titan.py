from __future__ import annotations

import asyncio
import json

import boto3
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import get_settings


class TitanEmbedder:
    """AWS Titan Embeddings (production alternative to Gemini embeddings)."""

    name = "titan"
    dim = 1536  # amazon.titan-embed-text-v1

    def __init__(self) -> None:
        settings = get_settings()
        self._model_id = settings.titan_model_id
        self._client = boto3.client("bedrock-runtime", region_name=settings.bedrock_region)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    def _embed_one(self, text: str) -> list[float]:
        body = {"inputText": text}
        resp = self._client.invoke_model(
            modelId=self._model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
        return json.loads(resp["body"].read())["embedding"]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        loop = asyncio.get_running_loop()
        # Titan v1 does not support batch embedding - call in parallel with bounded concurrency
        sem = asyncio.Semaphore(8)

        async def _one(t: str) -> list[float]:
            async with sem:
                return await loop.run_in_executor(None, self._embed_one, t)

        return await asyncio.gather(*[_one(t) for t in texts])

    async def embed_query(self, query: str) -> list[float]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._embed_one, query)
