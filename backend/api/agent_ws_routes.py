from __future__ import annotations

import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from src.auth.manager import user_auth_manager
from src.auth.security import decode_access_token
from src.llm import get_llm
from src.session import AgentSession, registry
from src.tools.ask_user import make_ask_user_tool
from src.tools.registry import build_qa_tools

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.websocket("/ws")
async def agent_ws(ws: WebSocket, token: str = Query(...)):
    user_id = decode_access_token(token)
    if not user_id:
        await ws.close(code=4401)
        return
    user = user_auth_manager.get_user_by_id(user_id)
    if not user:
        await ws.close(code=4401)
        return

    await ws.accept()
    session = AgentSession(tenant=user.username)

    async def on_question(session_id: str, question: str):
        await ws.send_text(json.dumps({"type": "question_prompt", "session_id": session_id, "question": question}))

    session._on_question = on_question
    registry.register(session)

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except Exception:
                await ws.send_text(json.dumps({"type": "error", "detail": "invalid json"}))
                continue

            mtype = msg.get("type")
            if mtype == "user_answer":
                await session.deliver_answer(str(msg.get("answer", "")))
                continue

            if mtype == "query":
                query = str(msg.get("query", "")).strip()
                if not query:
                    await ws.send_text(json.dumps({"type": "error", "detail": "empty query"}))
                    continue
                await ws.send_text(json.dumps({"type": "reasoning_started", "session_id": session.id}))
                citations: list[dict] = []
                tools = build_qa_tools(
                    tenant=user.username, granted_scopes=["default"], citations_sink=citations
                )
                tools.append(make_ask_user_tool(session))
                llm_provider = get_llm()
                if not hasattr(llm_provider, "raw_langchain"):
                    await ws.send_text(json.dumps({"type": "error", "detail": "current LLM backend does not support tool-use WS"}))
                    continue
                model = llm_provider.raw_langchain(temperature=0.2)
                agent = create_react_agent(model=model, tools=tools, prompt="You are the interactive Reasoning Agent. Use rag_search first, cite everything you use, ask_user if you need clarification.")
                try:
                    result = await agent.ainvoke({"messages": [HumanMessage(content=query)]})
                    messages = result.get("messages", [])
                    final = getattr(messages[-1], "content", "") if messages else ""
                    await ws.send_text(json.dumps({
                        "type": "final",
                        "session_id": session.id,
                        "answer": final,
                        "citations": citations,
                    }))
                except Exception as e:
                    await ws.send_text(json.dumps({"type": "error", "detail": str(e)}))
                continue

            await ws.send_text(json.dumps({"type": "error", "detail": f"unknown message type: {mtype}"}))
    except WebSocketDisconnect:
        pass
    finally:
        registry.drop(session.id)
