from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.project import Project
from app.models.boq_file import BOQFile
from app.models.line_item import LineItem
from app.models.sec_code import SECCode

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get dashboard statistics
    """
    # Total projects
    total_projects = db.query(func.count(Project.project_id)).scalar()
    
    # Total files
    total_files = db.query(func.count(BOQFile.file_id)).scalar()
    
    # Total line items
    total_items = db.query(func.count(LineItem.line_item_id)).scalar()
    
    # Total value
    total_value = db.query(func.sum(LineItem.amount)).scalar() or 0
    
    # Items needing review
    items_needing_review = db.query(func.count(LineItem.line_item_id)).filter(
        (LineItem.confidence_score < 80) | (LineItem.sec_code.is_(None))
    ).scalar()
    
    # Classification accuracy
    auto_classified = db.query(func.count(LineItem.line_item_id)).filter(
        LineItem.classification_method == 'auto'
    ).scalar()
    
    manual_classified = db.query(func.count(LineItem.line_item_id)).filter(
        LineItem.classification_method == 'manual'
    ).scalar()
    
    return {
        "total_projects": total_projects,
        "total_files": total_files,
        "total_items": total_items,
        "total_value": float(total_value),
        "items_needing_review": items_needing_review,
        "auto_classified": auto_classified,
        "manual_classified": manual_classified,
        "classification_rate": round((auto_classified + manual_classified) / total_items * 100, 2) if total_items > 0 else 0
    }


@router.get("/project/{project_id}/stats")
async def get_project_stats(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get statistics for a specific project
    """
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Total items
    total_items = db.query(func.count(LineItem.line_item_id)).filter(
        LineItem.project_id == project_id
    ).scalar()
    
    # Total value
    total_value = db.query(func.sum(LineItem.amount)).filter(
        LineItem.project_id == project_id
    ).scalar() or 0
    
    # Average confidence
    avg_confidence = db.query(func.avg(LineItem.confidence_score)).filter(
        LineItem.project_id == project_id
    ).scalar() or 0
    
    # Items by classification method
    by_method = db.query(
        LineItem.classification_method,
        func.count(LineItem.line_item_id)
    ).filter(
        LineItem.project_id == project_id
    ).group_by(LineItem.classification_method).all()
    
    return {
        "project_id": project_id,
        "project_name": project.project_name,
        "total_items": total_items,
        "total_value": float(total_value),
        "avg_confidence": float(avg_confidence),
        "classification_breakdown": {
            method: count for method, count in by_method
        }
    }


@router.get("/project/{project_id}/sec-distribution")
async def get_sec_distribution(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get SEC code distribution for a project
    """
    distribution = db.query(
        LineItem.sec_code,
        SECCode.sec_name_vi,
        func.count(LineItem.line_item_id).label('item_count'),
        func.sum(LineItem.amount).label('total_amount')
    ).join(
        SECCode, LineItem.sec_code == SECCode.sec_code
    ).filter(
        LineItem.project_id == project_id
    ).group_by(
        LineItem.sec_code, SECCode.sec_name_vi
    ).order_by(
        func.sum(LineItem.amount).desc()
    ).all()
    
    return {
        "project_id": project_id,
        "distribution": [
            {
                "sec_code": sec_code,
                "sec_name": sec_name,
                "item_count": item_count,
                "total_amount": float(total_amount or 0)
            }
            for sec_code, sec_name, item_count, total_amount in distribution
        ]
    }


@router.get("/classification/accuracy")
async def get_classification_accuracy(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get overall classification accuracy statistics
    """
    # By classification method
    by_method = db.query(
        LineItem.classification_method,
        func.count(LineItem.line_item_id).label('count'),
        func.avg(LineItem.confidence_score).label('avg_confidence')
    ).group_by(LineItem.classification_method).all()
    
    # By confidence range
    confidence_ranges = [
        (0, 50, "Very Low"),
        (50, 70, "Low"),
        (70, 80, "Medium"),
        (80, 90, "High"),
        (90, 100, "Very High")
    ]
    
    by_confidence = []
    for min_conf, max_conf, label in confidence_ranges:
        count = db.query(func.count(LineItem.line_item_id)).filter(
            LineItem.confidence_score >= min_conf,
            LineItem.confidence_score < max_conf
        ).scalar()
        by_confidence.append({
            "range": f"{min_conf}-{max_conf}",
            "label": label,
            "count": count
        })
    
    return {
        "by_method": [
            {
                "method": method,
                "count": count,
                "avg_confidence": float(avg_conf or 0)
            }
            for method, count, avg_conf in by_method
        ],
        "by_confidence": by_confidence
    }
