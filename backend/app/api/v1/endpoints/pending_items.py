"""
API endpoints for Pending Items management

Handles reviewing and approving/rejecting items before they enter Master DB.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Optional

from app.core.database import get_db
from app.models.pending_master_item import PendingMasterItem
from app.models.master_work_item import MasterWorkItem
from app.services.work_code_generator import WorkCodeGenerator
from app.services.learning_flywheel import get_learning_flywheel
from app.schemas.pending_item import (
    PendingItemResponse,
    PendingItemUpdate,
    ApprovalRequest,
    BulkApprovalRequest,
    PendingItemStats,
    ApprovalResponse,
    BulkApprovalResponse,
)

router = APIRouter()


@router.get("/", response_model=List[PendingItemResponse])
async def list_pending_items(
    status: Optional[str] = Query('PENDING', description="Filter by status: PENDING, APPROVED, REJECTED"),
    min_score: Optional[float] = Query(None, description="Minimum quality score"),
    max_score: Optional[float] = Query(None, description="Maximum quality score"),
    sec_code: Optional[str] = Query(None, description="Filter by SEC code"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """List pending items with filters."""
    query = db.query(PendingMasterItem)

    if status:
        query = query.filter(PendingMasterItem.status == status)
    if min_score is not None:
        query = query.filter(PendingMasterItem.quality_score >= min_score)
    if max_score is not None:
        query = query.filter(PendingMasterItem.quality_score <= max_score)
    if sec_code:
        query = query.filter(PendingMasterItem.sec_code == sec_code)

    query = query.order_by(PendingMasterItem.quality_score.desc())
    return query.offset(skip).limit(limit).all()


@router.get("/stats", response_model=PendingItemStats)
async def get_pending_stats(db: Session = Depends(get_db)):
    """Get statistics for pending items."""
    pending = db.query(PendingMasterItem).filter(
        PendingMasterItem.status == 'PENDING'
    ).count()
    approved = db.query(PendingMasterItem).filter(
        PendingMasterItem.status == 'APPROVED'
    ).count()
    rejected = db.query(PendingMasterItem).filter(
        PendingMasterItem.status == 'REJECTED'
    ).count()

    return PendingItemStats(
        pending=pending,
        approved=approved,
        rejected=rejected,
        total=pending + approved + rejected
    )


@router.get("/{pending_id}", response_model=PendingItemResponse)
async def get_pending_item(pending_id: int, db: Session = Depends(get_db)):
    """Get a single pending item."""
    item = db.query(PendingMasterItem).filter(
        PendingMasterItem.pending_id == pending_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Pending item not found")
    return item


@router.put("/{pending_id}", response_model=PendingItemResponse)
async def update_pending_item(
    pending_id: int,
    data: PendingItemUpdate,
    db: Session = Depends(get_db)
):
    """Update pending item (edit before approval)."""
    item = db.query(PendingMasterItem).filter(
        PendingMasterItem.pending_id == pending_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Pending item not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    # Update normalized description if description changed
    if 'description' in update_data and update_data['description']:
        item.description_normalized = update_data['description'].lower().strip()

    db.commit()
    db.refresh(item)
    return item


@router.post("/{pending_id}/approve", response_model=ApprovalResponse)
async def approve_pending_item(
    pending_id: int,
    data: ApprovalRequest,
    db: Session = Depends(get_db)
):
    """Approve pending item and create master item."""
    item = db.query(PendingMasterItem).filter(
        PendingMasterItem.pending_id == pending_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Pending item not found")

    if item.status != 'PENDING':
        raise HTTPException(status_code=400, detail=f"Item already processed (status: {item.status})")

    # Generate work code
    code_generator = WorkCodeGenerator(db)
    work_code = code_generator.generate_work_code(
        description=item.description,
        sec_code=item.sec_code or 'SEC-00',
        unit=item.unit_standard or 'unit'
    )

    # Create master item
    master_item = MasterWorkItem(
        work_code=work_code,
        description=item.description,
        description_normalized=item.description_normalized,
        sec_code=item.sec_code or 'SEC-00',
        unit_standard=item.unit_standard or 'unit',
        is_verified=True,
        verified_by=data.reviewer_id,
        verified_at=func.now()
    )
    db.add(master_item)
    db.flush()

    # Update pending item
    item.status = 'APPROVED'
    item.reviewed_by = data.reviewer_id
    item.reviewed_at = func.now()
    item.review_notes = data.notes
    item.master_id = master_item.master_id

    # Flywheel: auto-create synonym + training log
    flywheel = get_learning_flywheel(db)
    flywheel.on_pending_approved(
        pending_item=item,
        master_item=master_item,
        reviewer_id=data.reviewer_id,
    )

    db.commit()

    return ApprovalResponse(
        status="approved",
        master_id=master_item.master_id,
        work_code=work_code
    )


@router.post("/{pending_id}/reject")
async def reject_pending_item(
    pending_id: int,
    data: ApprovalRequest,
    db: Session = Depends(get_db)
):
    """Reject pending item."""
    item = db.query(PendingMasterItem).filter(
        PendingMasterItem.pending_id == pending_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Pending item not found")

    if item.status != 'PENDING':
        raise HTTPException(status_code=400, detail=f"Item already processed (status: {item.status})")

    item.status = 'REJECTED'
    item.reviewed_by = data.reviewer_id
    item.reviewed_at = func.now()
    item.review_notes = data.notes

    db.commit()

    return {"status": "rejected", "pending_id": pending_id}


@router.post("/bulk-approve", response_model=BulkApprovalResponse)
async def bulk_approve(
    data: BulkApprovalRequest,
    db: Session = Depends(get_db)
):
    """Bulk approve multiple pending items."""
    approved_count = 0

    for pending_id in data.pending_ids:
        item = db.query(PendingMasterItem).filter(
            PendingMasterItem.pending_id == pending_id,
            PendingMasterItem.status == 'PENDING'
        ).first()

        if not item:
            continue

        try:
            # Generate work code
            code_generator = WorkCodeGenerator(db)
            work_code = code_generator.generate_work_code(
                description=item.description,
                sec_code=item.sec_code or 'SEC-00',
                unit=item.unit_standard or 'unit'
            )

            # Create master item
            master_item = MasterWorkItem(
                work_code=work_code,
                description=item.description,
                description_normalized=item.description_normalized,
                sec_code=item.sec_code or 'SEC-00',
                unit_standard=item.unit_standard or 'unit',
                is_verified=True,
                verified_by=data.reviewer_id,
                verified_at=func.now()
            )
            db.add(master_item)
            db.flush()

            # Update pending item
            item.status = 'APPROVED'
            item.reviewed_by = data.reviewer_id
            item.reviewed_at = func.now()
            item.master_id = master_item.master_id

            approved_count += 1
        except Exception:
            continue

    db.commit()

    return BulkApprovalResponse(
        approved=approved_count,
        total=len(data.pending_ids)
    )


@router.post("/bulk-reject")
async def bulk_reject(
    data: BulkApprovalRequest,
    db: Session = Depends(get_db)
):
    """Bulk reject multiple pending items."""
    rejected_count = 0

    for pending_id in data.pending_ids:
        item = db.query(PendingMasterItem).filter(
            PendingMasterItem.pending_id == pending_id,
            PendingMasterItem.status == 'PENDING'
        ).first()

        if not item:
            continue

        item.status = 'REJECTED'
        item.reviewed_by = data.reviewer_id
        item.reviewed_at = func.now()
        rejected_count += 1

    db.commit()

    return {"rejected": rejected_count, "total": len(data.pending_ids)}
