from __future__ import annotations

import httpx
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.config import get_settings


class SlackInput(BaseModel):
    text: str = Field(..., description="Plain-text message to post")


def make_slack_tool() -> StructuredTool:
    async def _send(text: str) -> str:
        s = get_settings()
        if not s.slack_webhook_url:
            return "error: SLACK_WEBHOOK_URL not set"
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(s.slack_webhook_url, json={"text": text})
        if r.status_code >= 400:
            return f"error: Slack {r.status_code} {r.text[:200]}"
        return "sent"

    return StructuredTool.from_function(
        coroutine=_send,
        func=lambda text: "async only",
        name="send_slack_message",
        description="Post a message to a Slack incoming webhook.",
        args_schema=SlackInput,
    )
