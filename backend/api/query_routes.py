from __future__ import annotations

import json
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from src.agents.orchestrator import run_orchestrator, stream_orchestrator
from src.auth.dependencies import get_current_user
from src.auth.manager import user_auth_manager
from src.auth.models import UserInDB
from src.auth.security import decode_access_token
from src.metadata_store import get_metadata_store
from src.metadata_store.conversations import new_conversation_id, persist_turn

router = APIRouter(prefix="/api/query", tags=["query"])


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    conversation_id: str | None = Field(
        default=None,
        description="Persistent conversation id. Omit for a fresh one; server returns it in the response.",
    )
    metadata_filter: dict | None = None
    trigger_actions: bool = False


@router.post("")
async def submit_query(body: QueryRequest, user: UserInDB = Depends(get_current_user)):
    conv_id = body.conversation_id or new_conversation_id()
    state = await run_orchestrator(
        tenant=user.username,
        query=body.query,
        conversation_id=conv_id,
        granted_scopes=["default"],
        metadata_filter=body.metadata_filter,
        trigger_actions=body.trigger_actions,
    )
    result = {
        "conversation_id": conv_id,
        "answer": state.get("draft_answer", ""),
        "citations": state.get("citations", []),
        "retrieved": state.get("retrieved", []),
        "eval_rounds": state.get("eval_rounds", []),
        "validation": state.get("validation", {}),
        "actions_taken": state.get("actions_taken", []),
        "final_score": state.get("final_score", 0.0),
        "reasoning_trace": state.get("reasoning_trace", []),
        "route": state.get("route"),
        "router_rationale": state.get("router_rationale"),
    }
    try:
        await persist_turn(
            tenant=user.username,
            conversation_id=conv_id,
            payload={"query": body.query, **result},
        )
    except Exception:
        pass
    return result


@router.get("/stream")
async def stream_query(
    query: str = Query(..., min_length=1, max_length=4000),
    token: str = Query(..., description="JWT (EventSource cannot set headers)"),
    conversation_id: str | None = Query(default=None),
    trigger_actions: bool = Query(False),
):
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="invalid token")
    user = user_auth_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="user not found")

    conv_id = conversation_id or new_conversation_id()

    async def gen() -> AsyncIterator[dict]:
        yield {"event": "conversation_started", "data": json.dumps({"conversation_id": conv_id})}
        final_payload: dict | None = None
        async for event in stream_orchestrator(
            tenant=user.username,
            query=query,
            conversation_id=conv_id,
            granted_scopes=["default"],
            trigger_actions=trigger_actions,
        ):
            if event.get("type") == "done":
                final_payload = {**event, "conversation_id": conv_id}
                yield {"event": "done", "data": json.dumps(final_payload, default=str)}
            else:
                yield {
                    "event": event.get("type", event.get("node", "message")),
                    "data": json.dumps({**event, "conversation_id": conv_id}, default=str),
                }
        if final_payload is not None:
            try:
                await persist_turn(
                    tenant=user.username,
                    conversation_id=conv_id,
                    payload={"query": query, **final_payload},
                )
            except Exception:
                pass

    return EventSourceResponse(gen())


@router.get("/history")
async def history(user: UserInDB = Depends(get_current_user), limit: int = Query(50, le=200)):
    ms = get_metadata_store()
    return await ms.list_outputs(tenant=user.username, limit=limit)


@router.get("/conversations/{conversation_id}")
async def conversation_turns(
    conversation_id: str, user: UserInDB = Depends(get_current_user)
):
    from src.metadata_store.conversations import load_recent_turns

    turns = await load_recent_turns(
        tenant=user.username, conversation_id=conversation_id, max_turns=100
    )
    return {"conversation_id": conversation_id, "turns": turns}
