"""
RAG API Routes

Endpoints for RAG system management and semantic search.
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag.chromadb_manager import ChromaDBManager
from src.rag.github_ingestor import GitHubIngestor
from src.rag.rag_retriever import RAGRetriever, setup_rag_for_user
from src.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/rag", tags=["RAG"])

# Initialize RAG components
chromadb_manager = ChromaDBManager()
rag_retriever = RAGRetriever(chromadb_manager)


# ============== Request/Response Models ==============

class RAGSetupRequest(BaseModel):
    github_username: Optional[str] = Field(None, description="GitHub username (defaults to system username)")
    max_repos: int = Field(25, description="Maximum repos to ingest")
    reset_existing: bool = Field(False, description="Reset existing data before setup")


class RAGSetupResponse(BaseModel):
    success: bool
    username: str
    documents_added: int
    total_documents: int
    message: str


class RAGSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    n_results: int = Field(5, description="Number of results")
    filters: Optional[Dict[str, Any]] = Field(None, description="Metadata filters")


class RAGSearchResult(BaseModel):
    content: str
    metadata: Dict[str, Any]
    relevance_score: float


class RAGSearchResponse(BaseModel):
    query: str
    results: List[RAGSearchResult]
    total_results: int


class RAGStatsResponse(BaseModel):
    username: str
    total_documents: int
    status: str
    sample_repos: List[str]


class RAGContextRequest(BaseModel):
    jd_text: str = Field(..., description="Job description")
    max_chunks: int = Field(10, description="Maximum content chunks")


class RAGContextResponse(BaseModel):
    context: str
    chunks_used: int
    queries_extracted: List[str]


# ============== Endpoints ==============

@router.post("/setup", response_model=RAGSetupResponse)
async def setup_rag(
    request: RAGSetupRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """
    Setup RAG system for authenticated user by ingesting GitHub repos.

    This process runs in the background and can take 1-5 minutes.
    """
    username = current_user.username

    try:
        # Reset if requested
        if request.reset_existing:
            chromadb_manager.reset_user_data(username)

        # Run setup (this can be slow, but we'll do it synchronously for now)
        # TODO: Move to background task for better UX
        github_username = request.github_username or username

        result = setup_rag_for_user(
            username=username,
            github_username=github_username,
            max_repos=request.max_repos,
            use_gitingest=True
        )

        if result["success"]:
            return RAGSetupResponse(
                success=True,
                username=username,
                documents_added=result["documents_added"],
                total_documents=result["stats"]["document_count"],
                message=f"Successfully ingested {result['documents_added']} repositories"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Setup failed")
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=RAGStatsResponse)
async def get_rag_stats(current_user = Depends(get_current_user)):
    """
    Get RAG system statistics for current user
    """
    username = current_user.username

    try:
        summary = rag_retriever.get_project_summary(username)

        return RAGStatsResponse(
            username=username,
            total_documents=summary.get("total_documents", 0),
            status=summary.get("status", "unknown"),
            sample_repos=summary.get("sample_repos", [])
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=RAGSearchResponse)
async def search_rag(
    request: RAGSearchRequest,
    current_user = Depends(get_current_user)
):
    """
    Search user's RAG database with semantic search
    """
    username = current_user.username

    try:
        results = rag_retriever.search(
            username=username,
            query=request.query,
            n_results=request.n_results,
            filters=request.filters
        )

        return RAGSearchResponse(
            query=request.query,
            results=[
                RAGSearchResult(
                    content=r["content"],
                    metadata=r["metadata"],
                    relevance_score=r["relevance_score"]
                )
                for r in results
            ],
            total_results=len(results)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/context", response_model=RAGContextResponse)
async def get_context_for_jd(
    request: RAGContextRequest,
    current_user = Depends(get_current_user)
):
    """
    Get relevant project context based on job description.

    This endpoint is used internally during resume generation.
    """
    username = current_user.username

    try:
        context = rag_retriever.get_context_for_jd(
            username=username,
            jd_text=request.jd_text,
            max_chunks=request.max_chunks
        )

        # Extract queries for debugging
        queries = rag_retriever._extract_key_terms(request.jd_text)

        return RAGContextResponse(
            context=context,
            chunks_used=len(context.split("[Project")) - 1 if "[Project" in context else 0,
            queries_extracted=queries[:5]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/reset")
async def reset_rag_data(current_user = Depends(get_current_user)):
    """
    Reset all RAG data for current user (DANGEROUS!)
    """
    username = current_user.username

    try:
        chromadb_manager.reset_user_data(username)

        return {
            "success": True,
            "message": f"All RAG data deleted for user {username}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== Public Test Endpoint (No Auth) ==============

@router.get("/health")
async def rag_health_check():
    """Check if RAG system is operational"""
    try:
        # Try to create a test client
        test_manager = ChromaDBManager()
        return {
            "status": "healthy",
            "chromadb": "operational",
            "base_path": str(test_manager.base_path)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
