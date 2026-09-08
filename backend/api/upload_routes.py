from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, HttpUrl

from src.auth.dependencies import get_current_user
from src.auth.models import UserInDB
from src.ingestion.pipeline import ingest_bytes, ingest_url
from src.metadata_store import get_metadata_store

router = APIRouter(prefix="/api/upload", tags=["ingestion"])


class UrlIngestRequest(BaseModel):
    url: HttpUrl
    title: str | None = None


@router.post("/file")
async def upload_file(file: UploadFile = File(...), user: UserInDB = Depends(get_current_user)):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="empty file")
    try:
        result = await ingest_bytes(
            tenant=user.username,
            filename=file.filename or "upload",
            data=data,
            content_type=file.content_type,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@router.post("/url")
async def upload_url(body: UrlIngestRequest, user: UserInDB = Depends(get_current_user)):
    try:
        return await ingest_url(tenant=user.username, url=str(body.url), title=body.title)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/sources")
async def list_sources(user: UserInDB = Depends(get_current_user)):
    ms = get_metadata_store()
    return await ms.list_sources(tenant=user.username, limit=200)


@router.delete("/sources/{source_id}")
async def delete_source(source_id: str, user: UserInDB = Depends(get_current_user)):
    ms = get_metadata_store()
    # Delete metadata + vector rows
    from src.vector_store import get_vector_store

    vs = get_vector_store()
    ok = await ms.delete_source(tenant=user.username, source_id=source_id)
    if not ok:
        raise HTTPException(status_code=404, detail="source not found")
    await vs.delete_by_metadata(tenant=user.username, metadata_filter={"source_id": source_id})
    return {"ok": True}
