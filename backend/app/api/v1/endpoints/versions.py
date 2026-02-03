"""
API Endpoints for Version Comparison
Enables comparing different versions of BOQ files
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.boq_version import BOQVersion
from app.models.boq_file import BOQFile
from app.services.version_comparison_service import (
    VersionComparisonService,
    ChangeStatus
)

router = APIRouter()


# ==============================================
# Pydantic Schemas
# ==============================================

class VersionResponse(BaseModel):
    version_id: int
    version_number: int
    version_name: Optional[str]
    file_id: int
    file_name: str
    created_at: str
    notes: Optional[str]


class CreateVersionRequest(BaseModel):
    file_id: int
    version_name: Optional[str] = None
    notes: Optional[str] = None


class ComparisonItemResponse(BaseModel):
    description: str
    normalized_description: Optional[str]
    sec_code: Optional[str]
    status: str
    v1_quantity: Optional[float]
    v2_quantity: Optional[float]
    v1_unit_price: Optional[float]
    v2_unit_price: Optional[float]
    v1_amount: Optional[float]
    v2_amount: Optional[float]
    price_diff_percent: Optional[float]
    quantity_diff_percent: Optional[float]


class ComparisonSummaryResponse(BaseModel):
    v1_version_number: int
    v2_version_number: int
    v1_total_items: int
    v2_total_items: int
    v1_total_amount: float
    v2_total_amount: float
    amount_diff: float
    amount_diff_percent: float
    unchanged_count: int
    price_changed_count: int
    quantity_changed_count: int
    added_count: int
    removed_count: int


class ComparisonResponse(BaseModel):
    project_id: int
    summary: ComparisonSummaryResponse
    items: List[ComparisonItemResponse]


# ==============================================
# Endpoints
# ==============================================

@router.get("/{project_id}/versions")
def list_versions(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all versions for a project
    """
    versions = db.query(BOQVersion).filter(
        BOQVersion.project_id == project_id
    ).order_by(BOQVersion.version_number.desc()).all()

    result = []
    for v in versions:
        boq_file = db.query(BOQFile).filter(BOQFile.file_id == v.file_id).first()
        result.append({
            "version_id": v.version_id,
            "version_number": v.version_number,
            "version_name": v.version_name,
            "file_id": v.file_id,
            "file_name": boq_file.file_name if boq_file else None,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "notes": v.notes
        })

    return {
        "project_id": project_id,
        "versions": result,
        "total": len(result)
    }


@router.post("/{project_id}/versions")
def create_version(
    project_id: int,
    request: CreateVersionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new version for a project
    """
    # Verify file belongs to project
    boq_file = db.query(BOQFile).filter(
        BOQFile.file_id == request.file_id,
        BOQFile.project_id == project_id
    ).first()

    if not boq_file:
        raise HTTPException(
            status_code=400,
            detail="File not found or does not belong to this project"
        )

    # Get next version number
    max_version = db.query(BOQVersion).filter(
        BOQVersion.project_id == project_id
    ).order_by(BOQVersion.version_number.desc()).first()

    next_version = (max_version.version_number + 1) if max_version else 1

    version = BOQVersion(
        project_id=project_id,
        version_number=next_version,
        version_name=request.version_name or f"Version {next_version}",
        file_id=request.file_id,
        notes=request.notes
    )

    db.add(version)
    db.commit()
    db.refresh(version)

    return {
        "message": "Version created successfully",
        "version_id": version.version_id,
        "version_number": version.version_number,
        "version_name": version.version_name
    }


@router.get("/{project_id}/versions/compare")
def compare_versions(
    project_id: int,
    v1: int = Query(..., description="First version number"),
    v2: int = Query(..., description="Second version number"),
    status_filter: Optional[str] = Query(
        None,
        pattern="^(unchanged|price_changed|quantity_changed|added|removed)$",
        description="Filter by change status"
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Compare two versions of BOQ

    Returns:
    - Summary with counts of changes by type
    - Item-level comparison with price/quantity differences
    - Filter by status to focus on specific changes
    """
    service = VersionComparisonService(db)

    try:
        result = service.compare_versions(project_id, v1, v2)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Filter items if requested
    items = result.items
    if status_filter:
        try:
            status = ChangeStatus(status_filter)
            items = [i for i in items if i.status == status]
        except ValueError:
            pass

    # Paginate
    total_items = len(items)
    items = items[skip:skip + limit]

    # Convert to response format
    items_response = [
        ComparisonItemResponse(
            description=i.description,
            normalized_description=i.normalized_description,
            sec_code=i.sec_code,
            status=i.status.value,
            v1_quantity=i.v1_quantity,
            v2_quantity=i.v2_quantity,
            v1_unit_price=i.v1_unit_price,
            v2_unit_price=i.v2_unit_price,
            v1_amount=i.v1_amount,
            v2_amount=i.v2_amount,
            price_diff_percent=i.price_diff_percent,
            quantity_diff_percent=i.quantity_diff_percent
        )
        for i in items
    ]

    summary_response = ComparisonSummaryResponse(
        v1_version_number=result.summary.v1_version_number,
        v2_version_number=result.summary.v2_version_number,
        v1_total_items=result.summary.v1_total_items,
        v2_total_items=result.summary.v2_total_items,
        v1_total_amount=result.summary.v1_total_amount,
        v2_total_amount=result.summary.v2_total_amount,
        amount_diff=result.summary.amount_diff,
        amount_diff_percent=result.summary.amount_diff_percent,
        unchanged_count=result.summary.unchanged_count,
        price_changed_count=result.summary.price_changed_count,
        quantity_changed_count=result.summary.quantity_changed_count,
        added_count=result.summary.added_count,
        removed_count=result.summary.removed_count
    )

    return {
        "project_id": project_id,
        "summary": summary_response,
        "items": items_response,
        "total_items": total_items,
        "skip": skip,
        "limit": limit
    }


@router.delete("/{project_id}/versions/{version_number}")
def delete_version(
    project_id: int,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a version (does not delete the underlying file)
    """
    version = db.query(BOQVersion).filter(
        BOQVersion.project_id == project_id,
        BOQVersion.version_number == version_number
    ).first()

    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    db.delete(version)
    db.commit()

    return {
        "message": "Version deleted successfully",
        "version_number": version_number
    }
