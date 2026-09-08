from __future__ import annotations

import json
import re

from src.agents.state import AgentState
from src.llm import get_llm

_PROMPT = """You are the Query Router in an agentic RAG platform.

Classify the query into exactly one route:
- qa: user wants a factual answer grounded in indexed documents.
- action: user wants an external side effect (open ticket, notify, webhook).
- unclear: ambiguous, off-topic, or unanswerable.

Return JSON only: {{"route": "qa|action|unclear", "rationale": "one sentence"}}

Query: {query}
"""


async def router_node(state: AgentState) -> AgentState:
    llm = get_llm()
    text = await llm.chat(_PROMPT.format(query=state["query"]), temperature=0.0)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    route = "qa"
    rationale = "fallback"
    if m:
        try:
            data = json.loads(m.group(0))
            r = data.get("route", "qa")
            if r in {"qa", "action", "unclear"}:
                route = r
            rationale = data.get("rationale", "")
        except Exception:
            pass
    return {
        "route": route,
        "router_rationale": rationale,
        "events": state.get("events", []) + [{"type": "route_decided", "route": route, "label": f"Routing query as {route}..."}],
    }
