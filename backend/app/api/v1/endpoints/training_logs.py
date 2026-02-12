"""
API endpoints for AI Training Logs

Read-only endpoints for viewing training logs and statistics.
Used for monitoring the learning flywheel and preparing training data.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Optional

from app.core.database import get_db
from app.models.ai_training_log import AITrainingLog
from app.schemas.ai_training_log import (
    AITrainingLogResponse,
    AITrainingLogStats,
)

router = APIRouter()


@router.get("/", response_model=List[AITrainingLogResponse])
async def list_training_logs(
    action_type: Optional[str] = Query(None, description="Filter by action: ACCEPT, EDIT, REJECT, REMAP"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List AI training logs with filters."""
    query = db.query(AITrainingLog)

    if action_type:
        query = query.filter(AITrainingLog.action_type == action_type)
    if project_id is not None:
        query = query.filter(AITrainingLog.project_id == project_id)

    query = query.order_by(AITrainingLog.created_at.desc())
    return query.offset(skip).limit(limit).all()


@router.get("/stats", response_model=AITrainingLogStats)
async def get_training_log_stats(
    project_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Get training log statistics."""
    base_query = db.query(AITrainingLog)
    if project_id is not None:
        base_query = base_query.filter(AITrainingLog.project_id == project_id)

    total = base_query.count()

    # Count by action type
    by_action = {}
    for action in ('ACCEPT', 'EDIT', 'REJECT', 'REMAP'):
        count = base_query.filter(AITrainingLog.action_type == action).count()
        by_action[action] = count

    # Average confidence
    avg_conf = base_query.with_entities(
        func.avg(AITrainingLog.ai_confidence)
    ).scalar()

    # Average edit distance
    avg_edit = base_query.filter(
        AITrainingLog.edit_distance.isnot(None)
    ).with_entities(
        func.avg(AITrainingLog.edit_distance)
    ).scalar()

    return AITrainingLogStats(
        total=total,
        by_action=by_action,
        avg_confidence=round(float(avg_conf), 3) if avg_conf else None,
        avg_edit_distance=round(float(avg_edit), 1) if avg_edit else None,
    )
