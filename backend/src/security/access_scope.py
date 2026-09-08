from __future__ import annotations

"""Per-chunk access scope enforcement.

Every ingested chunk carries an `access_scope` metadata field. A retrieval call
merges the caller's granted scopes into the metadata_filter so hits outside
their scope are never returned by the vector store.
"""

from typing import Any


def scoped_filter(base_filter: dict[str, Any] | None, granted_scopes: list[str]) -> dict[str, Any]:
    if not granted_scopes:
        granted_scopes = ["default"]
    scope_clause = {"access_scope": granted_scopes} if len(granted_scopes) > 1 else {"access_scope": granted_scopes[0]}
    if not base_filter:
        return scope_clause
    merged = {**base_filter, **scope_clause}
    return merged


def user_scopes(user: dict[str, Any] | None) -> list[str]:
    if not user:
        return ["default"]
    scopes = list(user.get("scopes") or ["default"])
    if "admin" in scopes:
        return ["default", "engineering", "operations", "security", "admin"]
    return scopes
