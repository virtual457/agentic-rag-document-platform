from __future__ import annotations

from src.agents.state import AgentState
from src.config import get_settings
from src.retrieval.hybrid import hybrid_retrieve
from src.security.access_scope import scoped_filter


async def retrieval_node(state: AgentState) -> AgentState:
    settings = get_settings()
    f = scoped_filter(state.get("metadata_filter"), state.get("granted_scopes") or ["default"])
    hits = await hybrid_retrieve(
        tenant=state["tenant"],
        query=state["query"],
        top_k=settings.retrieval_top_k,
        metadata_filter=f,
    )
    retrieved = [
        {
            "id": h.id,
            "text": h.text,
            "score": h.score,
            "source_id": h.metadata.get("source_id"),
            "source_filename": h.metadata.get("source_filename"),
            "chunk_index": h.metadata.get("chunk_index"),
            "section": h.metadata.get("section"),
            "metadata": h.metadata,
        }
        for h in hits
    ]
    context = "\n\n".join(
        f"[{r['source_id']}#{r['chunk_index']} ({r['source_filename']} — {r.get('section','')})]\n{r['text']}"
        for r in retrieved
    )
    return {
        "retrieved": retrieved,
        "context": context,
        "events": state.get("events", []) + [
            {"type": "retrieval_complete", "hits": len(retrieved), "label": f"Searching documents... found {len(retrieved)} relevant chunks"}
        ],
    }
