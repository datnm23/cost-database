"""
Unit Standards API Endpoints

Provides endpoints for managing:
1. Unit standardization mappings (raw unit -> standard unit)
2. SEC code default units
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.unit_standard import (
    UnitStandardCreate, UnitStandardUpdate, UnitStandardResponse, UnitStandardList,
    SecCodeDefaultUnitCreate, SecCodeDefaultUnitUpdate, SecCodeDefaultUnitResponse, SecCodeDefaultUnitList,
    StandardizeUnitRequest, StandardizeUnitResponse, BulkStandardizeRequest, BulkStandardizeResponse
)
from app.services.unit_standard_service import UnitStandardService, get_unit_standard_service

router = APIRouter(prefix="/units", tags=["Unit Standards"])


# =====================================================
# Unit Standardization Endpoints
# =====================================================

@router.get("/standards", response_model=UnitStandardList)
def list_unit_standards(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    category: Optional[str] = Query(None, description="Filter by category"),
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Get list of unit standardization mappings"""
    service = get_unit_standard_service(db)
    items, total = service.get_unit_standards(skip, limit, category, active_only)
    return UnitStandardList(
        items=items,
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


@router.get("/standards/categories", response_model=List[str])
def list_unit_categories(db: Session = Depends(get_db)):
    """Get list of unit categories"""
    service = get_unit_standard_service(db)
    return service.get_all_unit_categories()


@router.get("/standards/{unit_id}", response_model=UnitStandardResponse)
def get_unit_standard(unit_id: int, db: Session = Depends(get_db)):
    """Get a unit standard by ID"""
    service = get_unit_standard_service(db)
    unit = service.get_unit_standard_by_id(unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit standard not found")
    return unit


@router.post("/standards", response_model=UnitStandardResponse, status_code=201)
def create_unit_standard(
    data: UnitStandardCreate,
    db: Session = Depends(get_db)
):
    """Create a new unit standardization mapping"""
    service = get_unit_standard_service(db)

    # Check if already exists
    existing = service.get_unit_standard_by_raw(data.raw_unit)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Unit mapping for '{data.raw_unit}' already exists"
        )

    return service.create_unit_standard(data)


@router.put("/standards/{unit_id}", response_model=UnitStandardResponse)
def update_unit_standard(
    unit_id: int,
    data: UnitStandardUpdate,
    db: Session = Depends(get_db)
):
    """Update a unit standardization mapping"""
    service = get_unit_standard_service(db)
    unit = service.update_unit_standard(unit_id, data)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit standard not found")
    return unit


@router.delete("/standards/{unit_id}")
def delete_unit_standard(unit_id: int, db: Session = Depends(get_db)):
    """Delete a unit standardization mapping (soft delete)"""
    service = get_unit_standard_service(db)
    if not service.delete_unit_standard(unit_id):
        raise HTTPException(status_code=404, detail="Unit standard not found")
    return {"message": "Unit standard deleted successfully"}


# =====================================================
# SEC Code Default Unit Endpoints
# =====================================================

@router.get("/sec-defaults", response_model=SecCodeDefaultUnitList)
def list_sec_code_defaults(
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Get list of SEC code default units"""
    service = get_unit_standard_service(db)
    items, total = service.get_sec_code_defaults(active_only)
    return SecCodeDefaultUnitList(items=items, total=total)


@router.get("/sec-defaults/{default_id}", response_model=SecCodeDefaultUnitResponse)
def get_sec_code_default(default_id: int, db: Session = Depends(get_db)):
    """Get a SEC code default by ID"""
    service = get_unit_standard_service(db)
    default = service.get_sec_code_default_by_id(default_id)
    if not default:
        raise HTTPException(status_code=404, detail="SEC code default not found")
    return default


@router.get("/sec-defaults/code/{sec_code}", response_model=SecCodeDefaultUnitResponse)
def get_sec_code_default_by_code(sec_code: str, db: Session = Depends(get_db)):
    """Get a SEC code default by SEC code"""
    service = get_unit_standard_service(db)
    default = service.get_sec_code_default_by_code(sec_code)
    if not default:
        raise HTTPException(status_code=404, detail=f"No default unit for SEC code '{sec_code}'")
    return default


@router.post("/sec-defaults", response_model=SecCodeDefaultUnitResponse, status_code=201)
def create_sec_code_default(
    data: SecCodeDefaultUnitCreate,
    db: Session = Depends(get_db)
):
    """Create a new SEC code default unit"""
    service = get_unit_standard_service(db)

    # Check if already exists
    existing = service.get_sec_code_default_by_code(data.sec_code)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Default unit for SEC code '{data.sec_code}' already exists"
        )

    return service.create_sec_code_default(data)


@router.put("/sec-defaults/{default_id}", response_model=SecCodeDefaultUnitResponse)
def update_sec_code_default(
    default_id: int,
    data: SecCodeDefaultUnitUpdate,
    db: Session = Depends(get_db)
):
    """Update a SEC code default unit"""
    service = get_unit_standard_service(db)
    default = service.update_sec_code_default(default_id, data)
    if not default:
        raise HTTPException(status_code=404, detail="SEC code default not found")
    return default


@router.delete("/sec-defaults/{default_id}")
def delete_sec_code_default(default_id: int, db: Session = Depends(get_db)):
    """Delete a SEC code default (soft delete)"""
    service = get_unit_standard_service(db)
    if not service.delete_sec_code_default(default_id):
        raise HTTPException(status_code=404, detail="SEC code default not found")
    return {"message": "SEC code default deleted successfully"}


# =====================================================
# Utility Endpoints
# =====================================================

@router.post("/standardize", response_model=StandardizeUnitResponse)
def standardize_unit(
    request: StandardizeUnitRequest,
    db: Session = Depends(get_db)
):
    """Standardize a single unit with optional SEC code fallback"""
    service = get_unit_standard_service(db)

    standardized_unit, is_default = service.get_unit_with_default(
        request.raw_unit,
        request.sec_code or ""
    )

    # Determine source
    if is_default:
        source = "default"
    elif standardized_unit != request.raw_unit:
        source = "mapping"
    else:
        source = "original"

    return StandardizeUnitResponse(
        raw_unit=request.raw_unit,
        standardized_unit=standardized_unit,
        is_default_applied=is_default,
        source=source
    )


@router.post("/standardize/bulk", response_model=BulkStandardizeResponse)
def bulk_standardize_units(
    request: BulkStandardizeRequest,
    db: Session = Depends(get_db)
):
    """Standardize multiple units at once"""
    service = get_unit_standard_service(db)
    results = []

    for item in request.units:
        standardized_unit, is_default = service.get_unit_with_default(
            item.raw_unit,
            item.sec_code or ""
        )

        if is_default:
            source = "default"
        elif standardized_unit != item.raw_unit:
            source = "mapping"
        else:
            source = "original"

        results.append(StandardizeUnitResponse(
            raw_unit=item.raw_unit,
            standardized_unit=standardized_unit,
            is_default_applied=is_default,
            source=source
        ))

    return BulkStandardizeResponse(results=results)


@router.post("/refresh-cache")
def refresh_unit_cache(db: Session = Depends(get_db)):
    """Clear the unit service cache to reload from database"""
    service = get_unit_standard_service(db)
    service.clear_cache()
    return {"message": "Unit cache refreshed successfully"}
