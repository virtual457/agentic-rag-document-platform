from __future__ import annotations

import json
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from src.agents.orchestrator import run_orchestrator, stream_orchestrator
from src.auth.dependencies import get_current_user
from src.auth.models import UserInDB
from src.auth.security import decode_access_token
from src.auth.manager import user_auth_manager
from src.metadata_store import get_metadata_store

router = APIRouter(prefix="/api/query", tags=["query"])


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    metadata_filter: dict | None = None
    trigger_actions: bool = False


@router.post("")
async def submit_query(body: QueryRequest, user: UserInDB = Depends(get_current_user)):
    state = await run_orchestrator(
        tenant=user.username,
        query=body.query,
        granted_scopes=["default"],
        metadata_filter=body.metadata_filter,
        trigger_actions=body.trigger_actions,
    )
    result = {
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
    # Persist to outputs
    ms = get_metadata_store()
    try:
        await ms.put_output(tenant=user.username, doc={"query": body.query, **result})
    except Exception:
        pass
    return result


@router.get("/stream")
async def stream_query(
    query: str = Query(..., min_length=1, max_length=4000),
    token: str = Query(..., description="JWT (EventSource cannot set headers)"),
    trigger_actions: bool = Query(False),
):
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="invalid token")
    user = user_auth_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="user not found")

    async def gen() -> AsyncIterator[dict]:
        async for event in stream_orchestrator(
            tenant=user.username,
            query=query,
            granted_scopes=["default"],
            trigger_actions=trigger_actions,
        ):
            yield {"event": event.get("type", event.get("node", "message")), "data": json.dumps(event, default=str)}

    return EventSourceResponse(gen())


@router.get("/history")
async def history(user: UserInDB = Depends(get_current_user), limit: int = Query(50, le=200)):
    ms = get_metadata_store()
    return await ms.list_outputs(tenant=user.username, limit=limit)
