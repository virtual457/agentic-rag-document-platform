from __future__ import annotations

import asyncio
from typing import Any

from src.observability.logger import get_logger
from src.vector_store.base import VectorHit

log = get_logger(__name__)

_CROSS_ENCODER: Any | None = None


def _get_cross_encoder() -> Any:
    global _CROSS_ENCODER
    if _CROSS_ENCODER is None:
        from sentence_transformers import CrossEncoder

        _CROSS_ENCODER = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _CROSS_ENCODER


async def rerank_hits(query: str, hits: list[VectorHit]) -> list[VectorHit]:
    if not hits:
        return hits
    try:
        model = _get_cross_encoder()
    except Exception as e:
        log.warning("reranker.unavailable", error=str(e))
        return hits
    pairs = [(query, h.text) for h in hits]
    loop = asyncio.get_running_loop()
    scores = await loop.run_in_executor(None, lambda: model.predict(pairs))
    scored = [(float(s), h) for s, h in zip(scores, hits)]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        VectorHit(id=h.id, text=h.text, metadata=h.metadata, score=s) for s, h in scored
    ]
