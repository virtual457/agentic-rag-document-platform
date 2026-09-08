from __future__ import annotations

import httpx
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from src.config import get_settings
from src.observability.logger import get_logger

log = get_logger("tool.servicenow")


class ServiceNowInput(BaseModel):
    short_description: str
    description: str
    urgency: int = Field(3, ge=1, le=3, description="1=high, 3=low")
    impact: int = Field(3, ge=1, le=3)
    category: str = Field("inquiry")


def make_servicenow_tool() -> StructuredTool:
    async def _create(short_description: str, description: str, urgency: int = 3, impact: int = 3, category: str = "inquiry") -> str:
        s = get_settings()
        if not (s.servicenow_base_url and s.servicenow_user and s.servicenow_password):
            return "error: ServiceNow not configured"
        body = {
            "short_description": short_description,
            "description": description,
            "urgency": str(urgency),
            "impact": str(impact),
            "category": category,
        }
        async with httpx.AsyncClient(timeout=15.0, auth=(s.servicenow_user, s.servicenow_password)) as client:
            r = await client.post(
                f"{s.servicenow_base_url.rstrip('/')}/api/now/table/incident",
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                json=body,
            )
        if r.status_code >= 400:
            log.warning("servicenow.create_failed", status=r.status_code, body=r.text[:300])
            return f"error: ServiceNow {r.status_code} {r.text[:200]}"
        return f"created: {r.json().get('result', {}).get('number')}"

    return StructuredTool.from_function(
        coroutine=_create,
        func=lambda **_: "async only",
        name="create_servicenow_incident",
        description="Open a ServiceNow incident. Requires SERVICENOW_BASE_URL, SERVICENOW_USER, SERVICENOW_PASSWORD.",
        args_schema=ServiceNowInput,
    )
