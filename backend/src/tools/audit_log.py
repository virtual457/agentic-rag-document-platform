from __future__ import annotations

from datetime import datetime

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from src.metadata_store import get_metadata_store
from src.observability.logger import get_logger

log = get_logger("tool.audit")


class AuditInput(BaseModel):
    action: str = Field(..., description="Short action label, e.g. 'jira_issue_created'")
    subject: str = Field(..., description="Human-readable subject")
    details: dict = Field(default_factory=dict)


def make_audit_tool(tenant: str) -> StructuredTool:
    async def _write(action: str, subject: str, details: dict | None = None) -> str:
        ms = get_metadata_store()
        event = {
            "action": action,
            "subject": subject,
            "details": details or {},
            "logged_at": datetime.utcnow(),
        }
        await ms.audit(tenant=tenant, event=event)
        log.info("audit.recorded", tenant=tenant, action=action, subject=subject)
        return "recorded"

    return StructuredTool.from_function(
        coroutine=_write,
        func=lambda **_: "async only",
        name="write_audit_log",
        description="Write an entry to the tenant's audit log. Call after every Action-Agent side effect.",
        args_schema=AuditInput,
    )
