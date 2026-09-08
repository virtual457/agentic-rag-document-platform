from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from src.config import get_settings


class GeminiProvider:
    name = "gemini"

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        self._model_id = settings.gemini_model
        self._api_key = settings.gemini_api_key

    def _client(self, temperature: float) -> ChatGoogleGenerativeAI:
        return ChatGoogleGenerativeAI(
            model=self._model_id, google_api_key=self._api_key, temperature=temperature
        )

    async def chat(self, prompt: str, *, temperature: float = 0.2, **_: Any) -> str:
        resp = await self._client(temperature).ainvoke(prompt)
        return resp.content if hasattr(resp, "content") else str(resp)

    async def chat_messages(self, messages: list[dict], *, temperature: float = 0.2, **_: Any) -> str:
        msg_objs = []
        for m in messages:
            role, content = m["role"], m["content"]
            if role == "system":
                msg_objs.append(SystemMessage(content=content))
            elif role == "assistant":
                msg_objs.append(AIMessage(content=content))
            else:
                msg_objs.append(HumanMessage(content=content))
        resp = await self._client(temperature).ainvoke(msg_objs)
        return resp.content if hasattr(resp, "content") else str(resp)

    def raw_langchain(self, temperature: float = 0.2) -> ChatGoogleGenerativeAI:
        return self._client(temperature)
