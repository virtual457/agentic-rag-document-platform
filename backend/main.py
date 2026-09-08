"""Document Intelligence Platform - FastAPI entrypoint."""
from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_settings
from src.observability.logger import get_logger
from src.session import registry as session_registry

log = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    log.info(
        "app.starting",
        vector=settings.vector_backend,
        llm=settings.llm_backend,
        embeddings=settings.embeddings_backend,
        metadata=settings.metadata_backend,
    )
    try:
        if settings.metadata_backend == "mongo":
            import asyncio

            from src.metadata_store.mongo import MongoMetadataStore

            await asyncio.wait_for(MongoMetadataStore().ensure_indexes(), timeout=3.0)
    except Exception as e:
        log.warning("app.index_init_failed", error=str(e))
    session_registry.start()
    yield
    log.info("app.stopping")


app = FastAPI(
    title="Document Intelligence Platform API",
    description="Agentic RAG platform for enterprise document Q&A with multi-agent orchestration and action tools.",
    version="1.0.0",
    lifespan=lifespan,
)

_settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[_settings.frontend_origin, "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "service": "Document Intelligence Platform",
        "version": app.version,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health():
    return {"status": "ok", "version": app.version}


# Route registration
from api.auth_routes import router as auth_router
from api.upload_routes import router as upload_router
from api.query_routes import router as query_router
from api.agent_ws_routes import router as agent_ws_router
from api.admin_routes import router as admin_router

app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(query_router)
app.include_router(agent_ws_router)
app.include_router(admin_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=_settings.host, port=_settings.port, reload=True)
