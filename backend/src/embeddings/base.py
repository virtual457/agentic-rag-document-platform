from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingProvider(Protocol):
    name: str
    dim: int

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...

    async def embed_query(self, query: str) -> list[float]:
        ...
