from __future__ import annotations

from typing import Any, Literal, TypedDict

Route = Literal["qa", "action", "unclear"]


class AgentState(TypedDict, total=False):
    tenant: str
    query: str
    granted_scopes: list[str]
    metadata_filter: dict[str, Any] | None
    trigger_actions: bool
    route: Route
    router_rationale: str
    retrieved: list[dict]
    context: str
    draft_answer: str
    citations: list[dict]
    reasoning_trace: list[str]
    validation: dict
    validation_passes: int
    eval_rounds: list[dict]
    final_score: float
    actions_taken: list[dict]
    events: list[dict]
