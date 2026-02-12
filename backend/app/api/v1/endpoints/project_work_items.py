"""
API endpoints for Project Work Items management

Handles reviewing and resolving project work items (Zone 1 items)
that didn't pass the quality gate.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Optional

from app.core.database import get_db
from app.models.project_work_item import ProjectWorkItem
from app.models.master_work_item import MasterWorkItem
from app.services.learning_flywheel import get_learning_flywheel
from app.schemas.project_work_item import (
    ProjectWorkItemResponse,
    ProjectWorkItemResolveRequest,
    ProjectWorkItemBulkResolveRequest,
    ProjectWorkItemStats,
    ProjectWorkItemResolveResponse,
)

router = APIRouter()


@router.get("/", response_model=List[ProjectWorkItemResponse])
async def list_project_work_items(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    gate_status: Optional[str] = Query(None, description="Filter by gate status: GREEN, YELLOW, RED"),
    resolution_status: Optional[str] = Query(None, description="Filter by resolution: UNRESOLVED, MATCHED, APPROVED, MERGED"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List project work items with filters."""
    query = db.query(ProjectWorkItem)

    if project_id is not None:
        query = query.filter(ProjectWorkItem.project_id == project_id)
    if gate_status:
        query = query.filter(ProjectWorkItem.gate_status == gate_status)
    if resolution_status:
        query = query.filter(ProjectWorkItem.resolution_status == resolution_status)

    query = query.order_by(ProjectWorkItem.created_at.desc())
    return query.offset(skip).limit(limit).all()


@router.get("/stats", response_model=ProjectWorkItemStats)
async def get_project_work_item_stats(
    project_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Get statistics for project work items."""
    base_query = db.query(ProjectWorkItem)
    if project_id is not None:
        base_query = base_query.filter(ProjectWorkItem.project_id == project_id)

    total = base_query.count()
    unresolved = base_query.filter(ProjectWorkItem.resolution_status == 'UNRESOLVED').count()
    matched = base_query.filter(ProjectWorkItem.resolution_status == 'MATCHED').count()
    approved = base_query.filter(ProjectWorkItem.resolution_status == 'APPROVED').count()
    merged = base_query.filter(ProjectWorkItem.resolution_status == 'MERGED').count()

    green = base_query.filter(ProjectWorkItem.gate_status == 'GREEN').count()
    yellow = base_query.filter(ProjectWorkItem.gate_status == 'YELLOW').count()
    red = base_query.filter(ProjectWorkItem.gate_status == 'RED').count()

    return ProjectWorkItemStats(
        total=total,
        unresolved=unresolved,
        matched=matched,
        approved=approved,
        merged=merged,
        by_gate_status={'GREEN': green, 'YELLOW': yellow, 'RED': red},
    )


@router.get("/{pwi_id}", response_model=ProjectWorkItemResponse)
async def get_project_work_item(pwi_id: int, db: Session = Depends(get_db)):
    """Get a single project work item."""
    item = db.query(ProjectWorkItem).filter(
        ProjectWorkItem.pwi_id == pwi_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Project work item not found")
    return item


@router.post("/{pwi_id}/resolve", response_model=ProjectWorkItemResolveResponse)
async def resolve_project_work_item(
    pwi_id: int,
    data: ProjectWorkItemResolveRequest,
    db: Session = Depends(get_db),
):
    """Resolve a project work item by mapping it to a master item."""
    pwi = db.query(ProjectWorkItem).filter(
        ProjectWorkItem.pwi_id == pwi_id
    ).first()
    if not pwi:
        raise HTTPException(status_code=404, detail="Project work item not found")

    if pwi.resolution_status in ('APPROVED', 'MERGED'):
        raise HTTPException(
            status_code=400,
            detail=f"Item already resolved (status: {pwi.resolution_status})"
        )

    # Verify master item exists
    master = db.query(MasterWorkItem).filter(
        MasterWorkItem.master_id == data.master_work_item_id,
        MasterWorkItem.is_active == True,
    ).first()
    if not master:
        raise HTTPException(status_code=404, detail="Master work item not found")

    # Use flywheel to resolve
    flywheel = get_learning_flywheel(db)
    flywheel.on_project_item_resolved(
        pwi=pwi,
        master_item=master,
        reviewer_id=data.reviewer_id,
        edited_description=data.edited_description,
    )

    db.commit()

    return ProjectWorkItemResolveResponse(
        status="resolved",
        pwi_id=pwi.pwi_id,
        master_work_item_id=master.master_id,
        synonym_created=True,
    )


@router.post("/bulk-resolve")
async def bulk_resolve_project_work_items(
    data: ProjectWorkItemBulkResolveRequest,
    db: Session = Depends(get_db),
):
    """Bulk resolve multiple project work items."""
    resolved_count = 0
    errors = []

    flywheel = get_learning_flywheel(db)

    for resolution in data.resolutions:
        pwi_id = resolution.get('pwi_id')
        master_id = resolution.get('master_work_item_id')

        if not pwi_id or not master_id:
            errors.append({'pwi_id': pwi_id, 'error': 'Missing pwi_id or master_work_item_id'})
            continue

        pwi = db.query(ProjectWorkItem).filter(
            ProjectWorkItem.pwi_id == pwi_id,
        ).first()
        if not pwi or pwi.resolution_status in ('APPROVED', 'MERGED'):
            errors.append({'pwi_id': pwi_id, 'error': 'Not found or already resolved'})
            continue

        master = db.query(MasterWorkItem).filter(
            MasterWorkItem.master_id == master_id,
            MasterWorkItem.is_active == True,
        ).first()
        if not master:
            errors.append({'pwi_id': pwi_id, 'error': f'Master item {master_id} not found'})
            continue

        flywheel.on_project_item_resolved(
            pwi=pwi,
            master_item=master,
            reviewer_id=data.reviewer_id,
            edited_description=resolution.get('edited_description'),
        )
        resolved_count += 1

    db.commit()

    return {
        'resolved': resolved_count,
        'total': len(data.resolutions),
        'errors': errors,
    }
