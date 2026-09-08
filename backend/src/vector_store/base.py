from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class VectorHit:
    id: str
    text: str
    metadata: dict[str, Any]
    score: float


@dataclass
class VectorRecord:
    id: str
    text: str
    embedding: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class VectorStore(Protocol):
    name: str

    async def upsert(self, *, tenant: str, records: list[VectorRecord]) -> None:
        ...

    async def similarity_search(
        self,
        *,
        tenant: str,
        embedding: list[float],
        top_k: int = 5,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[VectorHit]:
        ...

    async def keyword_search(
        self,
        *,
        tenant: str,
        query: str,
        top_k: int = 5,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[VectorHit]:
        ...

    async def delete_by_metadata(self, *, tenant: str, metadata_filter: dict[str, Any]) -> int:
        ...

    async def stats(self, *, tenant: str) -> dict[str, Any]:
        ...
