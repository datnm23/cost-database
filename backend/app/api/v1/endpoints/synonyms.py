"""
API endpoints for Synonym management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.synonym_service import SynonymService
from app.schemas.synonym import SynonymCreate, SynonymResponse

router = APIRouter()


@router.get("/master-items/{master_id}/synonyms", response_model=List[SynonymResponse])
async def get_synonyms_for_master_item(
    master_id: int,
    db: Session = Depends(get_db)
):
    """Get all synonyms for a master item."""
    service = SynonymService(db)
    return service.get_synonyms(master_id)


@router.post("/master-items/{master_id}/synonyms", response_model=SynonymResponse)
async def add_synonym_to_master_item(
    master_id: int,
    data: SynonymCreate,
    db: Session = Depends(get_db)
):
    """Add a synonym for a master item."""
    service = SynonymService(db)
    try:
        return service.add_synonym(
            master_id=master_id,
            synonym_text=data.synonym_text,
            synonym_type=data.synonym_type
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/synonyms", response_model=List[SynonymResponse])
async def list_all_synonyms(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all synonyms with pagination."""
    service = SynonymService(db)
    return service.get_all_synonyms(skip=skip, limit=limit)


@router.get("/synonyms/{synonym_id}", response_model=SynonymResponse)
async def get_synonym(
    synonym_id: int,
    db: Session = Depends(get_db)
):
    """Get a single synonym by ID."""
    service = SynonymService(db)
    synonym = service.get_synonym_by_id(synonym_id)
    if not synonym:
        raise HTTPException(status_code=404, detail="Synonym not found")
    return synonym


@router.delete("/synonyms/{synonym_id}")
async def delete_synonym(
    synonym_id: int,
    db: Session = Depends(get_db)
):
    """Delete a synonym (soft delete)."""
    service = SynonymService(db)
    if service.delete_synonym(synonym_id):
        return {"status": "success", "message": "Synonym deleted"}
    raise HTTPException(status_code=404, detail="Synonym not found")


@router.post("/synonyms/rebuild-cache")
async def rebuild_synonym_cache(db: Session = Depends(get_db)):
    """Rebuild synonym cache (after bulk changes)."""
    service = SynonymService(db)
    count = service.build_synonym_cache()
    return {"status": "success", "cached_count": count}


@router.get("/synonyms/statistics")
async def get_synonym_statistics(db: Session = Depends(get_db)):
    """Get synonym statistics."""
    service = SynonymService(db)
    return service.get_statistics()
