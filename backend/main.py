"""
FastAPI Server - LMARO API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from api.routes import router
from api.auth_routes import router as auth_router
from api.profile_routes import router as profile_router
from api.profile_builder_routes import router as profile_builder_router
from api.rag_routes import router as rag_router

app = FastAPI(
    title="LMARO API",
    description="LLM Multi-Agent Resume Optimizer with RAG",
    version="0.3.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(auth_router)  # Auth routes at /api/auth/*
app.include_router(profile_router)  # Profile routes at /api/profile/*
app.include_router(profile_builder_router)  # Profile builder at /api/profile/builder/*
app.include_router(rag_router)  # RAG routes at /api/rag/*
app.include_router(router)  # Other routes at /api/*


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "LMARO API - Multi-Agent Resume Optimizer",
        "version": "0.3.0",
        "docs": "/docs",
        "features": [
            "User Authentication (MongoDB)",
            "Profile Completion Tracking (LLM-powered)",
            "Multi-Agent Resume Generation",
            "RAG with ChromaDB (User-Isolated)",
            "Real-time SSE Progress Tracking",
            "Autonomous Profile Builder (ReAct Agent)",
            "🆕 GitHub Repository Ingestion & Semantic Search"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        from src.auth.database import mongodb
        # Test MongoDB connection
        mongodb.db.command('ping')
        mongo_status = "connected"
    except:
        mongo_status = "disconnected"
    
    return {
        "status": "healthy",
        "mongodb": mongo_status,
        "version": "0.3.0"
    }


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 Starting LMARO API Server")
    print("="*60)
    print("📍 Server: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("💚 Health Check: http://localhost:8000/health")
    print("="*60 + "\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
