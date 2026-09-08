from __future__ import annotations

from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from src.agents.state import AgentState
from src.llm import get_llm
from src.tools.registry import build_action_tools

_SYSTEM = """You are the Action Agent. The user query has been classified as requiring a side effect.

Guidance:
- Choose exactly the tools needed (Jira, ServiceNow, Slack, email, http_webhook).
- Always call write_audit_log after any successful side effect.
- Never fabricate ticket IDs or webhook URLs.
- Summarize what you did in one paragraph at the end.
"""


async def action_node(state: AgentState) -> AgentState:
    if not state.get("trigger_actions"):
        return {
            "actions_taken": [],
            "events": state.get("events", []) + [{"type": "action_skipped", "label": "No side effects requested"}],
        }

    tools = build_action_tools(tenant=state["tenant"])
    llm_provider = get_llm()
    if not hasattr(llm_provider, "raw_langchain"):
        return {
            "actions_taken": [],
            "events": state.get("events", []) + [{"type": "action_skipped", "reason": "llm_not_langchain", "label": "Skipping actions (LLM backend does not support tool-use)"}],
        }
    model = llm_provider.raw_langchain(temperature=0.1)
    agent = create_react_agent(model=model, tools=tools, prompt=_SYSTEM)
    combined_query = (
        f"Grounded answer:\n{state.get('draft_answer','')}\n\n"
        f"Original user request:\n{state['query']}\n\n"
        "Take the appropriate action(s) and write an audit log entry."
    )
    result = await agent.ainvoke({"messages": [HumanMessage(content=combined_query)]})
    messages = result.get("messages", [])
    actions: list[dict] = []
    for m in messages:
        tool_calls = getattr(m, "tool_calls", []) or []
        for tc in tool_calls:
            actions.append({"tool": tc.get("name"), "args": tc.get("args")})
    return {
        "actions_taken": actions,
        "events": state.get("events", []) + [
            {"type": "actions_completed", "count": len(actions), "label": f"Actions completed ({len(actions)} tool calls, audit log written)"}
        ],
    }
