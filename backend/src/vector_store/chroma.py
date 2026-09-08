from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.config import get_settings
from src.vector_store.base import VectorHit, VectorRecord


class ChromaVectorStore:
    name = "chroma"

    def __init__(self) -> None:
        settings = get_settings()
        self._base = Path(settings.chroma_path)
        self._base.mkdir(parents=True, exist_ok=True)
        self._clients: dict[str, chromadb.PersistentClient] = {}

    def _client(self, tenant: str) -> chromadb.PersistentClient:
        if tenant in self._clients:
            return self._clients[tenant]
        p = self._base / tenant
        p.mkdir(parents=True, exist_ok=True)
        c = chromadb.PersistentClient(
            path=str(p),
            settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
        )
        self._clients[tenant] = c
        return c

    def _col(self, tenant: str):
        return self._client(tenant).get_or_create_collection(
            name="documents", metadata={"hnsw:space": "cosine"}
        )

    async def upsert(self, *, tenant: str, records: list[VectorRecord]) -> None:
        if not records:
            return
        col = self._col(tenant)
        col.upsert(
            ids=[r.id for r in records],
            documents=[r.text for r in records],
            metadatas=[r.metadata for r in records],
            embeddings=[r.embedding for r in records],
        )

    async def similarity_search(
        self,
        *,
        tenant: str,
        embedding: list[float],
        top_k: int = 5,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[VectorHit]:
        col = self._col(tenant)
        where = _chroma_where(metadata_filter)
        res = col.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        hits: list[VectorHit] = []
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        ids = (res.get("ids") or [[]])[0]
        for i, doc in enumerate(docs):
            hits.append(
                VectorHit(
                    id=ids[i],
                    text=doc,
                    metadata=metas[i] or {},
                    score=1.0 - float(dists[i]),
                )
            )
        return hits

    async def keyword_search(
        self,
        *,
        tenant: str,
        query: str,
        top_k: int = 5,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[VectorHit]:
        # Chroma supports basic where_document contains. Real hybrid handled elsewhere via BM25 over cached corpus.
        col = self._col(tenant)
        where = _chroma_where(metadata_filter)
        try:
            res = col.get(
                where=where,
                where_document={"$contains": query},
                include=["documents", "metadatas"],
                limit=top_k,
            )
        except Exception:
            return []
        hits: list[VectorHit] = []
        for i, doc in enumerate(res.get("documents", []) or []):
            hits.append(
                VectorHit(
                    id=(res.get("ids") or [])[i] if i < len(res.get("ids") or []) else f"kw_{i}",
                    text=doc,
                    metadata=(res.get("metadatas") or [{}])[i] or {},
                    score=1.0,
                )
            )
        return hits

    async def delete_by_metadata(self, *, tenant: str, metadata_filter: dict[str, Any]) -> int:
        col = self._col(tenant)
        where = _chroma_where(metadata_filter)
        got = col.get(where=where, include=[])
        ids = got.get("ids", []) or []
        if ids:
            col.delete(ids=ids)
        return len(ids)

    async def stats(self, *, tenant: str) -> dict[str, Any]:
        col = self._col(tenant)
        return {"count": col.count(), "path": str(self._base / tenant)}


def _chroma_where(metadata_filter: dict[str, Any] | None) -> dict[str, Any] | None:
    if not metadata_filter:
        return None
    if len(metadata_filter) == 1:
        k, v = next(iter(metadata_filter.items()))
        if isinstance(v, list):
            return {k: {"$in": v}}
        return {k: v}
    clauses = []
    for k, v in metadata_filter.items():
        clauses.append({k: {"$in": v}} if isinstance(v, list) else {k: v})
    return {"$and": clauses}
