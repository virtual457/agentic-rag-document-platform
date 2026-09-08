from __future__ import annotations

import asyncio
from typing import Any

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from src.retrieval.hybrid import hybrid_retrieve
from src.security.access_scope import scoped_filter


class RagSearchInput(BaseModel):
    query: str = Field(..., description="Natural language search query")
    top_k: int = Field(5, ge=1, le=20)


def make_rag_search_tool(tenant: str, granted_scopes: list[str], metadata_filter: dict[str, Any] | None = None) -> StructuredTool:
    async def _search(query: str, top_k: int = 5) -> str:
        f = scoped_filter(metadata_filter, granted_scopes)
        hits = await hybrid_retrieve(tenant=tenant, query=query, top_k=top_k, metadata_filter=f)
        if not hits:
            return "No relevant passages found."
        out: list[str] = []
        for i, h in enumerate(hits, 1):
            source = h.metadata.get("source_filename", "unknown")
            idx = h.metadata.get("chunk_index", 0)
            section = h.metadata.get("section", "")
            out.append(f"[chunk_{i}] ({source} #{idx} — {section}, score={h.score:.3f})\n{h.text}")
        return "\n\n".join(out)

    def _sync(query: str, top_k: int = 5) -> str:
        return asyncio.run(_search(query, top_k))

    return StructuredTool.from_function(
        coroutine=_search,
        func=_sync,
        name="rag_search",
        description="Hybrid semantic + keyword search over the tenant's indexed document knowledge base. Returns ranked chunks with citations.",
        args_schema=RagSearchInput,
    )
