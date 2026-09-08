from __future__ import annotations

from functools import lru_cache

from src.config import get_settings
from src.llm.base import LLMProvider


@lru_cache
def get_llm() -> LLMProvider:
    backend = get_settings().llm_backend.lower()
    if backend == "gemini":
        from src.llm.gemini import GeminiProvider
        return GeminiProvider()
    if backend == "bedrock":
        from src.llm.bedrock import BedrockProvider
        return BedrockProvider()
    raise ValueError(f"Unknown LLM backend: {backend}. Use 'gemini' or 'bedrock'.")
