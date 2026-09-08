from __future__ import annotations

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class CitationInput(BaseModel):
    source_id: str = Field(..., description="source_id from rag_search")
    chunk_index: int = Field(..., ge=0)
    reason: str


def make_citation_tool(collected: list[dict]) -> StructuredTool:
    def _cite(source_id: str, chunk_index: int, reason: str) -> str:
        collected.append({"source_id": source_id, "chunk_index": chunk_index, "reason": reason})
        return f"Cited {source_id}#{chunk_index}"

    return StructuredTool.from_function(
        func=_cite,
        name="cite_source",
        description="Record a citation you used in the final answer. Call for every chunk you rely on.",
        args_schema=CitationInput,
    )
