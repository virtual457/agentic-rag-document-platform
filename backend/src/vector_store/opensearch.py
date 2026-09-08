from __future__ import annotations

import asyncio
from typing import Any

from opensearchpy import OpenSearch, RequestsHttpConnection

from src.config import get_settings
from src.vector_store.base import VectorHit, VectorRecord


class OpenSearchVectorStore:
    """OpenSearch Serverless / OSS as hybrid vector + BM25 store."""

    name = "opensearch"

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.opensearch_endpoint:
            raise RuntimeError("OPENSEARCH_ENDPOINT not set")
        self._client = OpenSearch(
            hosts=[settings.opensearch_endpoint],
            http_auth=(settings.aws_access_key_id, settings.aws_secret_access_key) if settings.aws_access_key_id else None,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=30,
        )
        self._index = settings.opensearch_index

    def _tenant_index(self, tenant: str) -> str:
        return f"{self._index}-{tenant}"

    def _ensure_index(self, tenant: str, dim: int) -> None:
        idx = self._tenant_index(tenant)
        if self._client.indices.exists(idx):
            return
        self._client.indices.create(
            idx,
            body={
                "settings": {"index": {"knn": True}},
                "mappings": {
                    "properties": {
                        "text": {"type": "text"},
                        "embedding": {"type": "knn_vector", "dimension": dim},
                        "metadata": {"type": "object", "enabled": True},
                    }
                },
            },
        )

    async def upsert(self, *, tenant: str, records: list[VectorRecord]) -> None:
        if not records:
            return
        dim = len(records[0].embedding)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._ensure_index, tenant, dim)
        idx = self._tenant_index(tenant)

        def _bulk() -> None:
            actions = []
            for r in records:
                actions.append({"index": {"_index": idx, "_id": r.id}})
                actions.append({"text": r.text, "embedding": r.embedding, "metadata": r.metadata})
            self._client.bulk(body=actions, refresh=True)

        await loop.run_in_executor(None, _bulk)

    async def similarity_search(
        self,
        *,
        tenant: str,
        embedding: list[float],
        top_k: int = 5,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[VectorHit]:
        idx = self._tenant_index(tenant)

        def _run() -> list[VectorHit]:
            query: dict[str, Any] = {"size": top_k, "query": {"knn": {"embedding": {"vector": embedding, "k": top_k}}}}
            if metadata_filter:
                query = {
                    "size": top_k,
                    "query": {
                        "bool": {
                            "must": [{"knn": {"embedding": {"vector": embedding, "k": top_k}}}],
                            "filter": [{"term": {f"metadata.{k}": v}} for k, v in metadata_filter.items() if not isinstance(v, list)],
                        }
                    },
                }
            resp = self._client.search(index=idx, body=query)
            hits: list[VectorHit] = []
            for h in resp["hits"]["hits"]:
                hits.append(
                    VectorHit(
                        id=h["_id"],
                        text=h["_source"].get("text", ""),
                        metadata=h["_source"].get("metadata", {}),
                        score=float(h.get("_score", 0.0)),
                    )
                )
            return hits

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _run)

    async def keyword_search(
        self,
        *,
        tenant: str,
        query: str,
        top_k: int = 5,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[VectorHit]:
        idx = self._tenant_index(tenant)

        def _run() -> list[VectorHit]:
            body: dict[str, Any] = {"size": top_k, "query": {"match": {"text": query}}}
            if metadata_filter:
                body = {
                    "size": top_k,
                    "query": {
                        "bool": {
                            "must": [{"match": {"text": query}}],
                            "filter": [{"term": {f"metadata.{k}": v}} for k, v in metadata_filter.items() if not isinstance(v, list)],
                        }
                    },
                }
            resp = self._client.search(index=idx, body=body)
            hits: list[VectorHit] = []
            for h in resp["hits"]["hits"]:
                hits.append(
                    VectorHit(
                        id=h["_id"],
                        text=h["_source"].get("text", ""),
                        metadata=h["_source"].get("metadata", {}),
                        score=float(h.get("_score", 0.0)),
                    )
                )
            return hits

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _run)

    async def delete_by_metadata(self, *, tenant: str, metadata_filter: dict[str, Any]) -> int:
        idx = self._tenant_index(tenant)

        def _run() -> int:
            body = {
                "query": {
                    "bool": {"filter": [{"term": {f"metadata.{k}": v}} for k, v in metadata_filter.items() if not isinstance(v, list)]}
                }
            }
            resp = self._client.delete_by_query(index=idx, body=body, refresh=True)
            return int(resp.get("deleted", 0))

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _run)

    async def stats(self, *, tenant: str) -> dict[str, Any]:
        idx = self._tenant_index(tenant)

        def _run() -> dict[str, Any]:
            try:
                c = self._client.count(index=idx)
                return {"count": c.get("count", 0), "index": idx}
            except Exception:
                return {"count": 0, "index": idx, "status": "not_created"}

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _run)
