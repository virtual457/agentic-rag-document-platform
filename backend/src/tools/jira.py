from __future__ import annotations

from base64 import b64encode

import httpx
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from src.config import get_settings
from src.observability.logger import get_logger

log = get_logger("tool.jira")


class JiraInput(BaseModel):
    project_key: str = Field(..., description="Jira project key, e.g. 'OPS'")
    summary: str
    description: str
    issue_type: str = Field("Task", description="Task | Bug | Incident")
    labels: list[str] = Field(default_factory=list)


def make_jira_tool() -> StructuredTool:
    async def _create(project_key: str, summary: str, description: str, issue_type: str = "Task", labels: list[str] | None = None) -> str:
        s = get_settings()
        if not (s.jira_base_url and s.jira_email and s.jira_api_token):
            return "error: Jira not configured (set JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN)"
        auth = b64encode(f"{s.jira_email}:{s.jira_api_token}".encode()).decode()
        body = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}]},
                "issuetype": {"name": issue_type},
                "labels": labels or [],
            }
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                f"{s.jira_base_url.rstrip('/')}/rest/api/3/issue",
                headers={"Authorization": f"Basic {auth}", "Accept": "application/json", "Content-Type": "application/json"},
                json=body,
            )
        if r.status_code >= 400:
            log.warning("jira.create_failed", status=r.status_code, body=r.text[:300])
            return f"error: Jira {r.status_code} {r.text[:200]}"
        j = r.json()
        return f"created: {s.jira_base_url.rstrip('/')}/browse/{j.get('key')}"

    return StructuredTool.from_function(
        coroutine=_create,
        func=lambda **_: "async only",
        name="create_jira_issue",
        description="Create a Jira issue in a given project. Requires JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN.",
        args_schema=JiraInput,
    )
