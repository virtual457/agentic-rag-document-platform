from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Minimal LLM provider protocol: async chat + streaming chat."""

    name: str

    async def chat(self, prompt: str, *, temperature: float = 0.2, **kwargs: Any) -> str:
        ...

    async def chat_messages(self, messages: list[dict], *, temperature: float = 0.2, **kwargs: Any) -> str:
        ...
