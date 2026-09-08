from __future__ import annotations

from typing import Any, AsyncIterator

from langgraph.graph import END, StateGraph

from src.agents.action import action_node
from src.agents.evaluator import evaluator_node
from src.agents.reasoning import reasoning_node
from src.agents.retrieval_agent import retrieval_node
from src.agents.router import router_node
from src.agents.state import AgentState
from src.agents.validation import validation_node
from src.config import get_settings


def _route_after_router(state: AgentState) -> str:
    return state.get("route", "qa")


def _route_after_evaluator(state: AgentState) -> str:
    settings = get_settings()
    rounds = state.get("eval_rounds", [])
    if not rounds:
        return "validate"
    last = rounds[-1]
    if last["passed"]:
        return "validate"
    if len(rounds) >= settings.max_eval_rounds:
        return "validate"
    return "reason"


def _route_after_validation(state: AgentState) -> str:
    settings = get_settings()
    v = state.get("validation") or {}
    if v.get("passed"):
        if state.get("route") == "action" or state.get("trigger_actions"):
            return "act"
        return END
    if state.get("validation_passes", 0) >= settings.max_factuality_rounds:
        return "finalize"
    return "reason"


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("router", router_node)
    g.add_node("retrieve", retrieval_node)
    g.add_node("reason", reasoning_node)
    g.add_node("evaluate", evaluator_node)
    g.add_node("validate", validation_node)
    g.add_node("act", action_node)
    g.add_node("finalize", lambda s: {"events": s.get("events", []) + [{"type": "finalize_forced"}]})

    g.set_entry_point("router")
    g.add_conditional_edges("router", _route_after_router, {"qa": "retrieve", "action": "retrieve", "unclear": END})
    g.add_edge("retrieve", "reason")
    g.add_edge("reason", "evaluate")
    g.add_conditional_edges("evaluate", _route_after_evaluator, {"reason": "reason", "validate": "validate"})
    g.add_conditional_edges("validate", _route_after_validation, {"reason": "reason", "act": "act", "finalize": "finalize", END: END})
    g.add_edge("act", END)
    g.add_edge("finalize", END)
    return g.compile()


_GRAPH = None


def get_graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_graph()
    return _GRAPH


async def run_orchestrator(
    *,
    tenant: str,
    query: str,
    granted_scopes: list[str] | None = None,
    metadata_filter: dict[str, Any] | None = None,
    trigger_actions: bool = False,
) -> AgentState:
    graph = get_graph()
    state: AgentState = {
        "tenant": tenant,
        "query": query,
        "granted_scopes": granted_scopes or ["default"],
        "metadata_filter": metadata_filter,
        "trigger_actions": trigger_actions,
        "events": [],
        "eval_rounds": [],
        "reasoning_trace": [],
        "actions_taken": [],
        "citations": [],
    }
    return await graph.ainvoke(state)


async def stream_orchestrator(
    *,
    tenant: str,
    query: str,
    granted_scopes: list[str] | None = None,
    metadata_filter: dict[str, Any] | None = None,
    trigger_actions: bool = False,
) -> AsyncIterator[dict]:
    graph = get_graph()
    state: AgentState = {
        "tenant": tenant,
        "query": query,
        "granted_scopes": granted_scopes or ["default"],
        "metadata_filter": metadata_filter,
        "trigger_actions": trigger_actions,
        "events": [],
        "eval_rounds": [],
        "reasoning_trace": [],
        "actions_taken": [],
        "citations": [],
    }
    final_state: AgentState | None = None
    async for step in graph.astream(state, stream_mode="updates"):
        for node_name, patch in step.items():
            for event in (patch or {}).get("events", []):
                yield {"node": node_name, **event}
            final_state = {**(final_state or state), **(patch or {})}
    yield {
        "node": "done",
        "type": "done",
        "answer": (final_state or {}).get("draft_answer", ""),
        "citations": (final_state or {}).get("citations", []),
        "retrieved": (final_state or {}).get("retrieved", []),
        "eval_rounds": (final_state or {}).get("eval_rounds", []),
        "validation": (final_state or {}).get("validation", {}),
        "actions_taken": (final_state or {}).get("actions_taken", []),
        "final_score": (final_state or {}).get("final_score", 0.0),
        "reasoning_trace": (final_state or {}).get("reasoning_trace", []),
        "route": (final_state or {}).get("route"),
    }
