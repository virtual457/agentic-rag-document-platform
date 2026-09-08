from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field, HttpUrl

from src.auth.dependencies import get_current_user
from src.auth.models import UserInDB
from src.ingestion.pipeline import ingest_bytes, ingest_url
from src.metadata_store import get_metadata_store

router = APIRouter(prefix="/api/upload", tags=["ingestion"])


class UrlIngestRequest(BaseModel):
    url: HttpUrl
    title: str | None = None
    # Free-form business metadata — e.g. product, version, severity,
    # service, environment, doc_type, access_scope.
    metadata: dict = Field(default_factory=dict)


def _parse_metadata_json(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("metadata must be a JSON object")
        return parsed
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"metadata is not valid JSON: {e}")


@router.post("/file")
async def upload_file(
    file: UploadFile = File(...),
    metadata: str | None = Form(default=None, description='JSON object of business metadata, e.g. {"product":"payments","version":"v2.3.1","severity":"high"}'),
    user: UserInDB = Depends(get_current_user),
):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="empty file")
    extra = _parse_metadata_json(metadata)
    try:
        result = await ingest_bytes(
            tenant=user.username,
            filename=file.filename or "upload",
            data=data,
            content_type=file.content_type,
            extra_metadata=extra or None,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@router.post("/url")
async def upload_url(body: UrlIngestRequest, user: UserInDB = Depends(get_current_user)):
    try:
        return await ingest_url(
            tenant=user.username,
            url=str(body.url),
            title=body.title,
            extra_metadata=body.metadata or None,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/sources")
async def list_sources(user: UserInDB = Depends(get_current_user)):
    ms = get_metadata_store()
    return await ms.list_sources(tenant=user.username, limit=200)


@router.delete("/sources/{source_id}")
async def delete_source(source_id: str, user: UserInDB = Depends(get_current_user)):
    ms = get_metadata_store()
    from src.vector_store import get_vector_store

    vs = get_vector_store()
    ok = await ms.delete_source(tenant=user.username, source_id=source_id)
    if not ok:
        raise HTTPException(status_code=404, detail="source not found")
    await vs.delete_by_metadata(tenant=user.username, metadata_filter={"source_id": source_id})
    return {"ok": True}
