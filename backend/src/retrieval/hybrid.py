from __future__ import annotations

from typing import Any

from src.config import get_settings
from src.embeddings import get_embedder
from src.retrieval.cache import get_cache
from src.retrieval.reranker import rerank_hits
from src.vector_store import get_vector_store
from src.vector_store.base import VectorHit


def _dedupe(hits: list[VectorHit]) -> list[VectorHit]:
    seen: set[str] = set()
    out: list[VectorHit] = []
    for h in hits:
        if h.id in seen:
            continue
        seen.add(h.id)
        out.append(h)
    return out


def _rrf(vec: list[VectorHit], kw: list[VectorHit], k: int = 60) -> list[VectorHit]:
    """Reciprocal Rank Fusion combines two ranked lists."""
    scores: dict[str, float] = {}
    keep: dict[str, VectorHit] = {}
    for rank, h in enumerate(vec):
        scores[h.id] = scores.get(h.id, 0.0) + 1.0 / (k + rank + 1)
        keep[h.id] = h
    for rank, h in enumerate(kw):
        scores[h.id] = scores.get(h.id, 0.0) + 1.0 / (k + rank + 1)
        keep.setdefault(h.id, h)
    ranked_ids = sorted(scores, key=lambda i: scores[i], reverse=True)
    fused: list[VectorHit] = []
    for i in ranked_ids:
        h = keep[i]
        fused.append(VectorHit(id=h.id, text=h.text, metadata=h.metadata, score=scores[i]))
    return fused


async def hybrid_retrieve(
    *,
    tenant: str,
    query: str,
    top_k: int | None = None,
    metadata_filter: dict[str, Any] | None = None,
) -> list[VectorHit]:
    settings = get_settings()
    top_k = top_k or settings.retrieval_top_k

    cache = get_cache()
    cache_key = f"retrieval:{tenant}:{query}:{top_k}:{metadata_filter}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    embedder = get_embedder()
    vs = get_vector_store()
    q_emb = await embedder.embed_query(query)

    vec_hits = await vs.similarity_search(
        tenant=tenant, embedding=q_emb, top_k=top_k * 3, metadata_filter=metadata_filter
    )

    if settings.keyword_hybrid_enabled:
        kw_hits = await vs.keyword_search(
            tenant=tenant, query=query, top_k=top_k * 3, metadata_filter=metadata_filter
        )
    else:
        kw_hits = []

    fused = _rrf(_dedupe(vec_hits), _dedupe(kw_hits))

    if settings.rerank_enabled and fused:
        fused = await rerank_hits(query, fused)

    result = fused[:top_k]
    cache.set(cache_key, result, ttl=settings.cache_ttl_retrieval)
    return result
