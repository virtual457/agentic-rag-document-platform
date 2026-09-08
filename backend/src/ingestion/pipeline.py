from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import httpx

from src.embeddings import get_embedder
from src.ingestion.chunker import chunk_document
from src.ingestion.parser import ParsedDocument, parse
from src.metadata_store import get_metadata_store
from src.observability.logger import get_logger
from src.vector_store import get_vector_store
from src.vector_store.base import VectorRecord

log = get_logger(__name__)


async def ingest_bytes(
    *,
    tenant: str,
    filename: str,
    data: bytes,
    content_type: str | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_id = uuid.uuid4().hex
    now = datetime.utcnow()

    doc: ParsedDocument = parse(data, filename, content_type)
    base_meta = {"access_scope": "default", **(extra_metadata or {})}
    chunks = chunk_document(doc, source_id=source_id, base_metadata=base_meta)
    if not chunks:
        raise ValueError(f"No chunks produced for {filename}")

    embedder = get_embedder()
    embeddings = await embedder.embed_texts([c.text for c in chunks])

    records = [
        VectorRecord(id=c.chunk_id, text=c.text, embedding=embeddings[i], metadata=c.metadata)
        for i, c in enumerate(chunks)
    ]
    vs = get_vector_store()
    await vs.upsert(tenant=tenant, records=records)

    ms = get_metadata_store()
    await ms.put_source(
        tenant=tenant,
        source_id=source_id,
        doc={
            "filename": filename,
            "source_type": doc.source_type,
            "byte_count": len(data),
            "chunk_count": len(chunks),
            "created_at": now,
            "extra_metadata": extra_metadata or {},
        },
    )
    log.info("ingest.completed", source_id=source_id, chunks=len(chunks), source_type=doc.source_type)
    return {
        "source_id": source_id,
        "filename": filename,
        "source_type": doc.source_type,
        "chunk_count": len(chunks),
    }


async def ingest_url(*, tenant: str, url: str, title: str | None = None) -> dict[str, Any]:
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    return await ingest_bytes(
        tenant=tenant,
        filename=title or url.rsplit("/", 1)[-1] or "url-import",
        data=resp.content,
        content_type=resp.headers.get("content-type"),
    )
