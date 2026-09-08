from __future__ import annotations

import asyncio
import json
from typing import Any

import psycopg
from psycopg.rows import dict_row

from src.config import get_settings
from src.vector_store.base import VectorHit, VectorRecord


class PgVectorStore:
    """PostgreSQL + pgvector backend. Per-tenant table name."""

    name = "pgvector"

    def __init__(self) -> None:
        settings = get_settings()
        self._dsn = settings.pgvector_dsn

    def _tenant_table(self, tenant: str) -> str:
        safe = "".join(ch if ch.isalnum() else "_" for ch in tenant)
        return f"docintel_{safe}"

    def _ensure_table(self, tenant: str, dim: int) -> None:
        table = self._tenant_table(tenant)
        with psycopg.connect(self._dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                cur.execute(
                    f"CREATE TABLE IF NOT EXISTS {table} ("
                    f"id TEXT PRIMARY KEY, text TEXT, metadata JSONB, embedding vector({dim}))"
                )
                cur.execute(
                    f"CREATE INDEX IF NOT EXISTS {table}_emb_idx ON {table} USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
                )
                cur.execute(f"CREATE INDEX IF NOT EXISTS {table}_meta_idx ON {table} USING GIN (metadata)")
                cur.execute(
                    f"CREATE INDEX IF NOT EXISTS {table}_text_idx ON {table} USING GIN (to_tsvector('english', text))"
                )

    async def upsert(self, *, tenant: str, records: list[VectorRecord]) -> None:
        if not records:
            return
        dim = len(records[0].embedding)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._ensure_table, tenant, dim)
        table = self._tenant_table(tenant)

        def _run() -> None:
            with psycopg.connect(self._dsn, autocommit=True) as conn:
                with conn.cursor() as cur:
                    for r in records:
                        cur.execute(
                            f"INSERT INTO {table} (id, text, metadata, embedding) "
                            f"VALUES (%s, %s, %s::jsonb, %s::vector) "
                            f"ON CONFLICT (id) DO UPDATE SET text=EXCLUDED.text, metadata=EXCLUDED.metadata, embedding=EXCLUDED.embedding",
                            (r.id, r.text, json.dumps(r.metadata), r.embedding),
                        )

        await loop.run_in_executor(None, _run)

    def _where_from_filter(self, metadata_filter: dict[str, Any] | None) -> tuple[str, list[Any]]:
        if not metadata_filter:
            return "", []
        clauses: list[str] = []
        params: list[Any] = []
        for k, v in metadata_filter.items():
            if isinstance(v, list):
                clauses.append(f"metadata->>{k!r} = ANY(%s)")
                params.append([str(x) for x in v])
            else:
                clauses.append(f"metadata->>{k!r} = %s")
                params.append(str(v))
        return " WHERE " + " AND ".join(clauses), params

    async def similarity_search(
        self,
        *,
        tenant: str,
        embedding: list[float],
        top_k: int = 5,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[VectorHit]:
        table = self._tenant_table(tenant)
        where, params = self._where_from_filter(metadata_filter)

        def _run() -> list[VectorHit]:
            with psycopg.connect(self._dsn, row_factory=dict_row) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"SELECT id, text, metadata, 1 - (embedding <=> %s::vector) AS score "
                        f"FROM {table}{where} ORDER BY embedding <=> %s::vector LIMIT %s",
                        [embedding, *params, embedding, top_k],
                    )
                    rows = cur.fetchall()
            return [VectorHit(id=r["id"], text=r["text"], metadata=r["metadata"] or {}, score=float(r["score"])) for r in rows]

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _run)

    async def keyword_search(
        self,
        *,
        tenant: str,
        query: str,
        top_k: int = 5,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[VectorHit]:
        table = self._tenant_table(tenant)
        where, params = self._where_from_filter(metadata_filter)
        prefix = " AND " if where else " WHERE "

        def _run() -> list[VectorHit]:
            with psycopg.connect(self._dsn, row_factory=dict_row) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"SELECT id, text, metadata, ts_rank(to_tsvector('english', text), plainto_tsquery('english', %s)) AS score "
                        f"FROM {table}{where}{prefix}to_tsvector('english', text) @@ plainto_tsquery('english', %s) "
                        f"ORDER BY score DESC LIMIT %s",
                        [query, *params, query, top_k],
                    )
                    rows = cur.fetchall()
            return [VectorHit(id=r["id"], text=r["text"], metadata=r["metadata"] or {}, score=float(r["score"])) for r in rows]

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _run)

    async def delete_by_metadata(self, *, tenant: str, metadata_filter: dict[str, Any]) -> int:
        table = self._tenant_table(tenant)
        where, params = self._where_from_filter(metadata_filter)
        if not where:
            return 0

        def _run() -> int:
            with psycopg.connect(self._dsn, autocommit=True) as conn:
                with conn.cursor() as cur:
                    cur.execute(f"DELETE FROM {table}{where}", params)
                    return cur.rowcount or 0

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _run)

    async def stats(self, *, tenant: str) -> dict[str, Any]:
        table = self._tenant_table(tenant)

        def _run() -> dict[str, Any]:
            try:
                with psycopg.connect(self._dsn) as conn:
                    with conn.cursor() as cur:
                        cur.execute(f"SELECT COUNT(*) FROM {table}")
                        (count,) = cur.fetchone()
                return {"count": int(count), "table": table}
            except Exception as e:
                return {"count": 0, "table": table, "status": "not_created", "error": str(e)}

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _run)
