from __future__ import annotations

from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from src.agents.state import AgentState
from src.llm import get_llm
from src.tools.registry import build_qa_tools

_SYSTEM = """You are the Reasoning Agent for an enterprise document intelligence platform.

Rules:
1. Answer strictly from retrieved chunks obtained via rag_search.
2. Call rag_search first, then refine queries if useful.
3. For every chunk you use in the final answer, call cite_source(source_id, chunk_index, reason).
4. If information is missing, say so explicitly. Never invent facts.
5. Cite inline in the answer as [source_id#chunk_index].

Additional tools may be available for actions. Do not call them unless the user query implies a side effect.
"""


async def reasoning_node(state: AgentState) -> AgentState:
    citations: list[dict] = []
    tools = build_qa_tools(
        tenant=state["tenant"],
        granted_scopes=state.get("granted_scopes") or ["default"],
        citations_sink=citations,
        metadata_filter=state.get("metadata_filter"),
    )
    llm_provider = get_llm()
    if hasattr(llm_provider, "raw_langchain"):
        model = llm_provider.raw_langchain(temperature=0.2)
    else:
        # Bedrock provider does not yet expose a LangChain-compatible model here.
        # Fallback: run rag_search + direct chat.
        from src.tools.rag_search import make_rag_search_tool

        search_tool = make_rag_search_tool(state["tenant"], state.get("granted_scopes") or ["default"], state.get("metadata_filter"))
        context = await search_tool.arun({"query": state["query"], "top_k": 5})
        answer = await llm_provider.chat(f"{_SYSTEM}\n\nContext:\n{context}\n\nQuestion:\n{state['query']}")
        return {
            "draft_answer": answer,
            "citations": [],
            "reasoning_trace": ["bedrock-direct"],
            "events": state.get("events", []) + [{"type": "generation_complete"}],
        }

    agent = create_react_agent(model=model, tools=tools, prompt=_SYSTEM)
    result = await agent.ainvoke({"messages": [HumanMessage(content=state["query"])]})
    messages = result.get("messages", [])
    final = messages[-1] if messages else None
    answer = getattr(final, "content", "") if final else ""
    trace = [f"{m.__class__.__name__}: {(getattr(m, 'content', '') or '')[:300]}" for m in messages if getattr(m, "content", "")]
    return {
        "draft_answer": answer,
        "citations": citations,
        "reasoning_trace": trace,
        "events": state.get("events", []) + [{"type": "generation_complete", "trace_len": len(trace)}],
    }
