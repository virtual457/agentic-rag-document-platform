from __future__ import annotations

import httpx
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class HttpInput(BaseModel):
    url: str = Field(..., description="https URL")
    payload: dict = Field(default_factory=dict)


def make_http_webhook_tool() -> StructuredTool:
    async def _post(url: str, payload: dict) -> str:
        if not url.startswith("https://"):
            return "error: only https URLs are allowed"
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(url, json=payload)
        return f"status={r.status_code} body={r.text[:200]}"

    return StructuredTool.from_function(
        coroutine=_post,
        func=lambda url, payload: "async only",
        name="http_webhook",
        description="POST a JSON payload to an https webhook.",
        args_schema=HttpInput,
    )
