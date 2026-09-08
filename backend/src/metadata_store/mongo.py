from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient

from src.config import get_settings


class MongoMetadataStore:
    name = "mongo"

    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncIOMotorClient(
            settings.mongo_uri,
            uuidRepresentation="standard",
            serverSelectionTimeoutMS=2000,
            connectTimeoutMS=2000,
        )
        self._db = self._client[settings.mongo_db]

    async def ensure_indexes(self) -> None:
        await self._db.sources.create_index([("tenant", 1), ("source_id", 1)], unique=True)
        await self._db.sources.create_index([("tenant", 1), ("created_at", -1)])
        await self._db.outputs.create_index([("tenant", 1), ("created_at", -1)])
        await self._db.audit.create_index([("tenant", 1), ("created_at", -1)])

    async def put_source(self, *, tenant: str, source_id: str, doc: dict[str, Any]) -> None:
        doc = {**doc, "tenant": tenant, "source_id": source_id}
        doc.setdefault("created_at", datetime.utcnow())
        await self._db.sources.replace_one({"tenant": tenant, "source_id": source_id}, doc, upsert=True)

    async def get_source(self, *, tenant: str, source_id: str) -> dict[str, Any] | None:
        return await self._db.sources.find_one({"tenant": tenant, "source_id": source_id})

    async def list_sources(self, *, tenant: str, limit: int = 100) -> list[dict[str, Any]]:
        cursor = self._db.sources.find({"tenant": tenant}).sort("created_at", -1).limit(limit)
        return [d async for d in cursor]

    async def delete_source(self, *, tenant: str, source_id: str) -> bool:
        result = await self._db.sources.delete_one({"tenant": tenant, "source_id": source_id})
        return result.deleted_count > 0

    async def put_output(self, *, tenant: str, doc: dict[str, Any]) -> str:
        doc = {**doc, "tenant": tenant}
        doc.setdefault("created_at", datetime.utcnow())
        doc.setdefault("_id", uuid.uuid4().hex)
        await self._db.outputs.insert_one(doc)
        return doc["_id"]

    async def list_outputs(self, *, tenant: str, limit: int = 50) -> list[dict[str, Any]]:
        cursor = self._db.outputs.find({"tenant": tenant}).sort("created_at", -1).limit(limit)
        return [d async for d in cursor]

    async def audit(self, *, tenant: str, event: dict[str, Any]) -> None:
        doc = {**event, "tenant": tenant, "created_at": datetime.utcnow()}
        await self._db.audit.insert_one(doc)
