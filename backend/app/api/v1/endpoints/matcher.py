"""
Matcher Management API Endpoints

Provides endpoints for managing the hybrid 3-tier matcher:
- Health check
- Statistics
- Index rebuild
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.core.database import get_db
from app.core.config import settings

router = APIRouter()


class MatcherHealthResponse(BaseModel):
    """Health check response."""
    status: str
    initialized: bool
    master_items_count: int
    hybrid_matcher_enabled: bool


class MatcherStatsResponse(BaseModel):
    """Matcher statistics response."""
    initialized: bool
    master_items_count: int
    cache: Dict[str, Any]
    embeddings: Dict[str, Any]
    faiss_index: Dict[str, Any]
    thresholds: Dict[str, float]


class RebuildResponse(BaseModel):
    """Rebuild response."""
    status: str
    message: str


@router.get("/health", response_model=MatcherHealthResponse)
async def get_matcher_health(db: Session = Depends(get_db)):
    """
    Health check for hybrid matcher.

    Returns status and basic info about the matcher state.
    """
    if not settings.HYBRID_MATCHER_ENABLED:
        return MatcherHealthResponse(
            status="disabled",
            initialized=False,
            master_items_count=0,
            hybrid_matcher_enabled=False
        )

    try:
        from app.services.hybrid_matcher import get_hybrid_matcher
        matcher = get_hybrid_matcher(db)

        return MatcherHealthResponse(
            status="healthy" if matcher._initialized else "not_initialized",
            initialized=matcher._initialized,
            master_items_count=len(matcher._master_lookup),
            hybrid_matcher_enabled=True
        )
    except Exception as e:
        return MatcherHealthResponse(
            status=f"error: {str(e)}",
            initialized=False,
            master_items_count=0,
            hybrid_matcher_enabled=True
        )


@router.get("/stats")
async def get_matcher_statistics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get detailed matcher statistics.

    Returns information about:
    - Cache hit/miss rates
    - Embedding count
    - FAISS index size
    - Threshold settings
    """
    if not settings.HYBRID_MATCHER_ENABLED:
        raise HTTPException(
            status_code=400,
            detail="Hybrid matcher is disabled. Set HYBRID_MATCHER_ENABLED=True in settings."
        )

    try:
        from app.services.hybrid_matcher import get_hybrid_matcher
        matcher = get_hybrid_matcher(db)

        if not matcher._initialized:
            return {
                "status": "not_initialized",
                "message": "Matcher not initialized. Call /rebuild to initialize."
            }

        return matcher.get_statistics()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get matcher statistics: {str(e)}"
        )


@router.post("/rebuild", response_model=RebuildResponse)
async def rebuild_matcher_index(
    force: bool = True,
    db: Session = Depends(get_db)
):
    """
    Force rebuild of matcher index.

    This should be called after:
    - Master data changes (additions, updates, deletions)
    - Embedding model updates
    - System recovery

    Args:
        force: Force rebuild even if already initialized (default: True)
    """
    if not settings.HYBRID_MATCHER_ENABLED:
        raise HTTPException(
            status_code=400,
            detail="Hybrid matcher is disabled. Set HYBRID_MATCHER_ENABLED=True in settings."
        )

    try:
        from app.services.hybrid_matcher import get_hybrid_matcher
        matcher = get_hybrid_matcher(db)
        matcher.rebuild_index()

        return RebuildResponse(
            status="success",
            message=f"Index rebuilt successfully. {len(matcher._master_lookup)} master items indexed."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to rebuild index: {str(e)}"
        )


@router.post("/clear-cache")
async def clear_matcher_cache(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Clear the exact match cache.

    Use when cache may be stale (e.g., after direct database modifications).
    """
    if not settings.HYBRID_MATCHER_ENABLED:
        raise HTTPException(
            status_code=400,
            detail="Hybrid matcher is disabled."
        )

    try:
        from app.services.hybrid_matcher import get_hybrid_matcher
        matcher = get_hybrid_matcher(db)
        cleared = matcher.clear_cache()

        return {
            "status": "success",
            "message": f"Cache cleared. {cleared} entries removed."
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )
