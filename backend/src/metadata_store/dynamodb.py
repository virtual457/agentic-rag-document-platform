from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

from src.config import get_settings


class DynamoMetadataStore:
    """DynamoDB-backed metadata store.

    Table schema:
      PK = f"{tenant}#{entity}"  (entity in: SOURCE, OUTPUT, AUDIT)
      SK = timestamp or source_id
      attrs: doc payload
    """

    name = "dynamodb"

    def __init__(self) -> None:
        settings = get_settings()
        self._table_name = settings.dynamodb_table_metadata
        self._ddb = boto3.resource("dynamodb", region_name=settings.aws_region)
        self._table = self._ddb.Table(self._table_name)

    async def ensure_indexes(self) -> None:
        # Table creation handled by Terraform; no-op here.
        return None

    def _pk(self, tenant: str, entity: str) -> str:
        return f"{tenant}#{entity}"

    async def put_source(self, *, tenant: str, source_id: str, doc: dict[str, Any]) -> None:
        item = {
            "pk": self._pk(tenant, "SOURCE"),
            "sk": source_id,
            "created_at": (doc.get("created_at") or datetime.utcnow()).isoformat(),
            **{k: v for k, v in doc.items() if k != "created_at"},
        }
        await asyncio.get_running_loop().run_in_executor(None, lambda: self._table.put_item(Item=item))

    async def get_source(self, *, tenant: str, source_id: str) -> dict[str, Any] | None:
        loop = asyncio.get_running_loop()
        r = await loop.run_in_executor(
            None, lambda: self._table.get_item(Key={"pk": self._pk(tenant, "SOURCE"), "sk": source_id})
        )
        return r.get("Item")

    async def list_sources(self, *, tenant: str, limit: int = 100) -> list[dict[str, Any]]:
        loop = asyncio.get_running_loop()
        r = await loop.run_in_executor(
            None,
            lambda: self._table.query(
                KeyConditionExpression=Key("pk").eq(self._pk(tenant, "SOURCE")),
                ScanIndexForward=False,
                Limit=limit,
            ),
        )
        return r.get("Items", [])

    async def delete_source(self, *, tenant: str, source_id: str) -> bool:
        loop = asyncio.get_running_loop()
        r = await loop.run_in_executor(
            None,
            lambda: self._table.delete_item(
                Key={"pk": self._pk(tenant, "SOURCE"), "sk": source_id},
                ReturnValues="ALL_OLD",
            ),
        )
        return "Attributes" in r

    async def put_output(self, *, tenant: str, doc: dict[str, Any]) -> str:
        oid = uuid.uuid4().hex
        item = {
            "pk": self._pk(tenant, "OUTPUT"),
            "sk": f"{datetime.utcnow().isoformat()}#{oid}",
            "output_id": oid,
            **doc,
        }
        await asyncio.get_running_loop().run_in_executor(None, lambda: self._table.put_item(Item=item))
        return oid

    async def list_outputs(self, *, tenant: str, limit: int = 50) -> list[dict[str, Any]]:
        loop = asyncio.get_running_loop()
        r = await loop.run_in_executor(
            None,
            lambda: self._table.query(
                KeyConditionExpression=Key("pk").eq(self._pk(tenant, "OUTPUT")),
                ScanIndexForward=False,
                Limit=limit,
            ),
        )
        return r.get("Items", [])

    async def audit(self, *, tenant: str, event: dict[str, Any]) -> None:
        item = {
            "pk": self._pk(tenant, "AUDIT"),
            "sk": f"{datetime.utcnow().isoformat()}#{uuid.uuid4().hex}",
            **event,
        }
        await asyncio.get_running_loop().run_in_executor(None, lambda: self._table.put_item(Item=item))
