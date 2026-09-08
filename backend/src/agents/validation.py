from __future__ import annotations

import json
import re

from src.agents.state import AgentState
from src.llm import get_llm

_PROMPT = """You are the Validation Agent. Judge whether the answer is fully supported by the source passages.

Answer:
{answer}

Source passages:
{context}

For each atomic factual claim in the answer, mark SUPPORTED or UNSUPPORTED. Return JSON only:
{{"claims":[{{"claim":"...","status":"SUPPORTED"|"UNSUPPORTED","why":"..."}}]}}
"""


async def validation_node(state: AgentState) -> AgentState:
    llm = get_llm()
    prompt = _PROMPT.format(answer=state.get("draft_answer", ""), context=state.get("context", "")[:8000])
    text = await llm.chat(prompt, temperature=0.0)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    passed = True
    supported = 0
    unsupported: list[str] = []
    if m:
        try:
            data = json.loads(m.group(0))
            claims = data.get("claims", [])
            supported = sum(1 for c in claims if c.get("status") == "SUPPORTED")
            unsupported = [
                f"{c.get('claim','')} :: {c.get('why','')}"
                for c in claims
                if c.get("status") == "UNSUPPORTED"
            ]
            passed = len(unsupported) == 0
        except Exception:
            pass
    validation = {
        "supported": supported,
        "unsupported": len(unsupported),
        "passed": passed,
        "unsupported_details": unsupported,
    }
    return {
        "validation": validation,
        "validation_passes": state.get("validation_passes", 0) + (1 if passed else 0),
        "events": state.get("events", []) + [{"type": "validation_complete", "passed": passed}],
    }
