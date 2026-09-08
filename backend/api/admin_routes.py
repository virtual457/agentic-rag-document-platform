from __future__ import annotations

from fastapi import APIRouter, Depends

from src.auth.dependencies import get_current_user
from src.auth.models import UserInDB
from src.config import get_settings
from src.metadata_store import get_metadata_store
from src.vector_store import get_vector_store

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats")
async def stats(user: UserInDB = Depends(get_current_user)):
    ms = get_metadata_store()
    vs = get_vector_store()
    sources = await ms.list_sources(tenant=user.username, limit=1000)
    vec_stats = await vs.stats(tenant=user.username)
    return {
        "user": user.username,
        "source_count": len(sources),
        "chunk_count": vec_stats.get("count", 0),
        "vector_backend": vs.name,
        "metadata_backend": ms.name,
    }


@router.get("/health/deep")
async def deep_health():
    settings = get_settings()
    checks: dict = {"llm": "unknown", "embeddings": "unknown", "vector_store": "unknown", "metadata_store": "unknown"}
    try:
        from src.llm import get_llm

        llm = get_llm()
        checks["llm"] = f"ok ({llm.name})"
    except Exception as e:
        checks["llm"] = f"error: {e}"
    try:
        from src.embeddings import get_embedder

        emb = get_embedder()
        checks["embeddings"] = f"ok ({emb.name}, dim={emb.dim})"
    except Exception as e:
        checks["embeddings"] = f"error: {e}"
    try:
        vs = get_vector_store()
        checks["vector_store"] = f"ok ({vs.name})"
    except Exception as e:
        checks["vector_store"] = f"error: {e}"
    try:
        ms = get_metadata_store()
        checks["metadata_store"] = f"ok ({ms.name})"
    except Exception as e:
        checks["metadata_store"] = f"error: {e}"

    return {
        "status": "ok",
        "checks": checks,
        "backends": {
            "llm": settings.llm_backend,
            "embeddings": settings.embeddings_backend,
            "vector": settings.vector_backend,
            "metadata": settings.metadata_backend,
            "cache": settings.cache_backend,
        },
    }
