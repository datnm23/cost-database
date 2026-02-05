"""
API endpoints for Quarantine Log management

View and analyze rejected items for pattern improvement.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func
from typing import List, Optional

from app.core.database import get_db
from app.models.quarantine_log import QuarantineLog
from app.schemas.quarantine import (
    QuarantineLogResponse,
    QuarantineStats,
    RetryValidationResponse,
)

router = APIRouter()


@router.get("/", response_model=List[QuarantineLogResponse])
async def list_quarantine_logs(
    rejection_reason: Optional[str] = Query(None, description="Filter by rejection reason"),
    source_file_id: Optional[int] = Query(None, description="Filter by source file"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """List quarantined items with filters."""
    query = db.query(QuarantineLog)

    if rejection_reason:
        query = query.filter(QuarantineLog.rejection_reason.ilike(f"%{rejection_reason}%"))
    if source_file_id:
        query = query.filter(QuarantineLog.source_file_id == source_file_id)

    return query.order_by(QuarantineLog.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/stats", response_model=QuarantineStats)
async def get_quarantine_stats(db: Session = Depends(get_db)):
    """Get quarantine statistics by rejection reason."""
    stats = db.query(
        QuarantineLog.rejection_reason,
        sql_func.count(QuarantineLog.log_id).label('count')
    ).group_by(QuarantineLog.rejection_reason).all()

    by_reason = {}
    for reason, count in stats:
        key = reason if reason else 'unknown'
        by_reason[key] = count

    total = sum(by_reason.values())

    return QuarantineStats(
        by_reason=by_reason,
        total=total
    )


@router.get("/{log_id}", response_model=QuarantineLogResponse)
async def get_quarantine_log(log_id: int, db: Session = Depends(get_db)):
    """Get a single quarantine log entry."""
    log = db.query(QuarantineLog).filter(QuarantineLog.log_id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Quarantine log not found")
    return log


@router.delete("/{log_id}")
async def delete_quarantine_log(log_id: int, db: Session = Depends(get_db)):
    """Delete a quarantine log entry."""
    log = db.query(QuarantineLog).filter(QuarantineLog.log_id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Quarantine log not found")

    db.delete(log)
    db.commit()

    return {"status": "deleted", "log_id": log_id}


@router.get("/reasons/list")
async def get_rejection_reasons(db: Session = Depends(get_db)):
    """Get list of unique rejection reasons."""
    reasons = db.query(QuarantineLog.rejection_reason).distinct().all()
    return [r[0] for r in reasons if r[0]]


@router.post("/{log_id}/promote-to-pending")
async def promote_to_pending(
    log_id: int,
    db: Session = Depends(get_db)
):
    """
    Promote a quarantined item to pending for manual review.

    Use this when a quarantined item was incorrectly rejected.
    """
    from app.models.pending_master_item import PendingMasterItem

    log = db.query(QuarantineLog).filter(QuarantineLog.log_id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Quarantine log not found")

    # Create pending item from quarantined data
    pending_item = PendingMasterItem(
        description=log.description,
        description_normalized=log.description_normalized,
        source_file_id=log.source_file_id,
        quality_score=log.quality_score,
        quality_indicators=log.quality_indicators,
        quality_reasons=f"Promoted from quarantine. Original reason: {log.rejection_reason}",
        status='PENDING'
    )
    db.add(pending_item)

    # Optionally delete the quarantine log
    db.delete(log)

    db.commit()
    db.refresh(pending_item)

    return {
        "status": "promoted",
        "pending_id": pending_item.pending_id,
        "original_log_id": log_id
    }
