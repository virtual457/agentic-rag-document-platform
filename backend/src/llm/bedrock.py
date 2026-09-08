from __future__ import annotations

import asyncio
import json
from typing import Any

import boto3
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import get_settings


class BedrockProvider:
    """AWS Bedrock LLaMA 3 provider (production alternative to Gemini).

    Uses the Bedrock Runtime `invoke_model` API. Configure IAM credentials via
    standard AWS envs / SSO / instance profile; do not embed keys in code.
    """

    name = "bedrock"

    def __init__(self) -> None:
        settings = get_settings()
        self._model_id = settings.bedrock_model_id
        self._region = settings.bedrock_region
        self._client = boto3.client("bedrock-runtime", region_name=self._region)

    def _build_llama3_prompt(self, messages: list[dict]) -> str:
        parts: list[str] = ["<|begin_of_text|>"]
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            parts.append(f"<|start_header_id|>{role}<|end_header_id|>\n{content}<|eot_id|>")
        parts.append("<|start_header_id|>assistant<|end_header_id|>\n")
        return "\n".join(parts)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    def _invoke_sync(self, prompt: str, temperature: float, max_tokens: int) -> str:
        body = {
            "prompt": prompt,
            "temperature": float(temperature),
            "max_gen_len": int(max_tokens),
            "top_p": 0.9,
        }
        resp = self._client.invoke_model(
            modelId=self._model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
        data = json.loads(resp["body"].read())
        return data.get("generation", data.get("outputText", ""))

    async def chat(self, prompt: str, *, temperature: float = 0.2, max_tokens: int = 1024, **_: Any) -> str:
        rendered = self._build_llama3_prompt([{"role": "user", "content": prompt}])
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._invoke_sync, rendered, temperature, max_tokens)

    async def chat_messages(self, messages: list[dict], *, temperature: float = 0.2, max_tokens: int = 1024, **_: Any) -> str:
        rendered = self._build_llama3_prompt(messages)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._invoke_sync, rendered, temperature, max_tokens)
