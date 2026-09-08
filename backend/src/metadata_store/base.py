from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class MetadataStore(Protocol):
    name: str

    async def put_source(self, *, tenant: str, source_id: str, doc: dict[str, Any]) -> None:
        ...

    async def get_source(self, *, tenant: str, source_id: str) -> dict[str, Any] | None:
        ...

    async def list_sources(self, *, tenant: str, limit: int = 100) -> list[dict[str, Any]]:
        ...

    async def delete_source(self, *, tenant: str, source_id: str) -> bool:
        ...

    async def put_output(self, *, tenant: str, doc: dict[str, Any]) -> str:
        ...

    async def list_outputs(self, *, tenant: str, limit: int = 50) -> list[dict[str, Any]]:
        ...

    async def audit(self, *, tenant: str, event: dict[str, Any]) -> None:
        ...
