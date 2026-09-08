from __future__ import annotations

import asyncio

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field


class AskUserInput(BaseModel):
    question: str = Field(..., description="Clarifying question for the user")


def make_ask_user_tool(session) -> StructuredTool:
    async def _ask(question: str) -> str:
        return await session.ask_user(question)

    def _sync(question: str) -> str:
        return asyncio.run(_ask(question))

    return StructuredTool.from_function(
        coroutine=_ask,
        func=_sync,
        name="ask_user",
        description="Pause reasoning and ask the user a clarifying question via the WebSocket session. Returns their reply.",
        args_schema=AskUserInput,
    )
