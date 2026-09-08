from __future__ import annotations

"""Conversation memory layer on top of the pluggable MetadataStore.

Persists turn history per (tenant, conversation_id) so the Reasoning Agent
can see prior Q&A pairs. Works with both MongoMetadataStore and
DynamoMetadataStore without any additional dependencies.
"""

import uuid
from datetime import datetime
from typing import Any

from src.metadata_store import get_metadata_store
from src.metadata_store.base import MetadataStore
from src.observability.logger import get_logger

log = get_logger("conversations")


def new_conversation_id() -> str:
    return uuid.uuid4().hex


async def load_recent_turns(
    *,
    tenant: str,
    conversation_id: str,
    max_turns: int = 6,
) -> list[dict[str, Any]]:
    """Return the most recent turns for a conversation, oldest first."""
    if not conversation_id:
        return []
    ms: MetadataStore = get_metadata_store()
    all_outputs = await ms.list_outputs(tenant=tenant, limit=200)
    matches = [o for o in all_outputs if o.get("conversation_id") == conversation_id]
    matches.sort(key=lambda d: str(d.get("created_at", "")))
    return matches[-max_turns:]


def format_prior_turns(turns: list[dict[str, Any]]) -> str:
    """Render prior turns as a compact prompt-prefix string."""
    if not turns:
        return ""
    lines: list[str] = ["Prior conversation turns (most recent last):"]
    for i, t in enumerate(turns, 1):
        q = str(t.get("query", "")).strip()
        a = str(t.get("answer", "")).strip()
        if not q or not a:
            continue
        lines.append(f"\nTurn {i}:")
        lines.append(f"User: {q}")
        lines.append(f"Assistant: {a[:800]}")
    return "\n".join(lines)


async def persist_turn(
    *,
    tenant: str,
    conversation_id: str,
    payload: dict[str, Any],
) -> str:
    """Persist a completed turn under the conversation_id."""
    ms = get_metadata_store()
    doc = {
        **payload,
        "conversation_id": conversation_id,
        "created_at": payload.get("created_at") or datetime.utcnow(),
    }
    return await ms.put_output(tenant=tenant, doc=doc)
