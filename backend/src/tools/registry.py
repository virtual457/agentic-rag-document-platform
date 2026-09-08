from __future__ import annotations

from typing import Any

from src.tools.audit_log import make_audit_tool
from src.tools.calculator import make_calculator_tool
from src.tools.citation import make_citation_tool
from src.tools.email_tool import make_email_tool
from src.tools.http_webhook import make_http_webhook_tool
from src.tools.jira import make_jira_tool
from src.tools.rag_search import make_rag_search_tool
from src.tools.servicenow import make_servicenow_tool
from src.tools.slack import make_slack_tool


def build_qa_tools(
    *,
    tenant: str,
    granted_scopes: list[str],
    citations_sink: list[dict],
    metadata_filter: dict[str, Any] | None = None,
) -> list:
    return [
        make_rag_search_tool(tenant, granted_scopes, metadata_filter=metadata_filter),
        make_citation_tool(citations_sink),
        make_calculator_tool(),
    ]


def build_action_tools(*, tenant: str) -> list:
    return [
        make_jira_tool(),
        make_servicenow_tool(),
        make_slack_tool(),
        make_email_tool(),
        make_http_webhook_tool(),
        make_audit_tool(tenant),
    ]
