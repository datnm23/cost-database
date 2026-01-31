from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.line_item import LineItem, ClassificationMethod
from app.services.classifier_service import get_classifier

from pydantic import BaseModel


class UpdateLineItemRequest(BaseModel):
    sec_code: Optional[str] = None
    needs_review: Optional[bool] = None


class BulkUpdateRequest(BaseModel):
    line_item_ids: List[int]
    sec_code: Optional[str] = None
    needs_review: Optional[bool] = None


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def get_line_items(
    project_id: Optional[int] = None,
    file_id: Optional[int] = None,
    sec_code: Optional[str] = None,
    needs_review: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=10000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get line items with filters
    """
    query = db.query(LineItem)
    
    # Apply filters
    if project_id:
        query = query.filter(LineItem.project_id == project_id)
    if file_id:
        query = query.filter(LineItem.file_id == file_id)
    if sec_code:
        query = query.filter(LineItem.sec_code == sec_code)
    if needs_review:
        query = query.filter(
            (LineItem.confidence_score < 80) | (LineItem.sec_code.is_(None))
        )
    
    total = query.count()
    items = query.order_by(LineItem.line_item_id).offset(skip).limit(limit).all()
    
    return {
        "items": [
            {
                "line_item_id": item.line_item_id,
                "file_id": item.file_id,
                "project_id": item.project_id,
                "row_number": item.row_number,
                "description": item.description,
                "unit": item.unit,
                "quantity": float(item.quantity) if item.quantity else 0,
                "unit_price": float(item.unit_price) if item.unit_price else 0,
                "amount": float(item.amount) if item.amount else 0,
                "sec_code": item.sec_code,
                "confidence_score": float(item.confidence_score) if item.confidence_score else 0,
                "classification_method": item.classification_method,
                "needs_review": item.needs_review if hasattr(item, 'needs_review') else False,
                "validation_issues": item.validation_issues if hasattr(item, 'validation_issues') else None,
            }
            for item in items
        ],
        "total": total,
        "page": skip // limit + 1,
        "page_size": limit,
        "total_pages": (total + limit - 1) // limit
    }


@router.get("/{line_item_id}")
async def get_line_item(
    line_item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get single line item"""
    item = db.query(LineItem).filter(LineItem.line_item_id == line_item_id).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Line item not found")
    
    return {
        "line_item_id": item.line_item_id,
        "file_id": item.file_id,
        "project_id": item.project_id,
        "row_number": item.row_number,
        "description": item.description,
        "unit": item.unit,
        "quantity": float(item.quantity) if item.quantity else 0,
        "unit_price": float(item.unit_price) if item.unit_price else 0,
        "amount": float(item.amount) if item.amount else 0,
        "sec_code": item.sec_code,
        "confidence_score": float(item.confidence_score) if item.confidence_score else 0,
        "classification_method": item.classification_method,
    }


@router.put("/{line_item_id}")
async def update_line_item(
    line_item_id: int,
    request: UpdateLineItemRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update line item fields
    """
    item = db.query(LineItem).filter(LineItem.line_item_id == line_item_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Line item not found")

    # Update fields if provided
    if request.sec_code is not None:
        item.sec_code = request.sec_code
    if request.needs_review is not None:
        item.needs_review = request.needs_review

    db.commit()
    db.refresh(item)

    return {
        "message": "Line item updated successfully",
        "line_item_id": item.line_item_id,
    }


@router.put("/{line_item_id}/classify")
async def update_classification(
    line_item_id: int,
    sec_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Manually update line item classification
    """
    item = db.query(LineItem).filter(LineItem.line_item_id == line_item_id).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Line item not found")
    
    # Update classification
    item.sec_code = sec_code
    item.classification_method = ClassificationMethod.MANUAL
    item.confidence_score = 100  # Manual classification is 100% confidence
    
    db.commit()
    db.refresh(item)
    
    return {
        "message": "Classification updated successfully",
        "line_item_id": item.line_item_id,
        "sec_code": item.sec_code
    }


@router.post("/bulk-update")
async def bulk_update(
    request: BulkUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Bulk update line items
    """
    update_data = {}
    if request.sec_code is not None:
        update_data[LineItem.sec_code] = request.sec_code
    if request.needs_review is not None:
        update_data[LineItem.needs_review] = request.needs_review

    if not update_data:
        raise HTTPException(status_code=400, detail="No update fields provided")

    updated_count = db.query(LineItem).filter(
        LineItem.line_item_id.in_(request.line_item_ids)
    ).update(update_data, synchronize_session=False)

    db.commit()

    return {
        "message": "Bulk update completed",
        "updated_count": updated_count
    }


@router.post("/bulk-classify")
async def bulk_classify(
    line_item_ids: List[int],
    sec_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Bulk update classification for multiple line items
    """
    updated_count = db.query(LineItem).filter(
        LineItem.line_item_id.in_(line_item_ids)
    ).update(
        {
            LineItem.sec_code: sec_code,
            LineItem.classification_method: ClassificationMethod.MANUAL,
            LineItem.confidence_score: 100
        },
        synchronize_session=False
    )
    
    db.commit()
    
    return {
        "message": "Bulk classification completed",
        "updated_count": updated_count
    }


@router.post("/{line_item_id}/reclassify")
async def reclassify_item(
    line_item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Re-run automatic classification for a line item
    """
    item = db.query(LineItem).filter(LineItem.line_item_id == line_item_id).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Line item not found")
    
    # Get classifier and reclassify
    classifier = get_classifier(db)
    results = classifier.classify(item.description, top_k=3)
    
    if results:
        sec_code, confidence = results[0]
        item.sec_code = sec_code
        item.confidence_score = confidence
        item.classification_method = ClassificationMethod.AUTO
        
        db.commit()
        db.refresh(item)
    
    return {
        "message": "Item reclassified",
        "line_item_id": item.line_item_id,
        "sec_code": item.sec_code,
        "confidence_score": float(item.confidence_score),
        "suggestions": [
            {"sec_code": code, "confidence": conf}
            for code, conf in results[:3]
        ]
    }


@router.delete("/all", status_code=200)
async def delete_all_line_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete all line items (for testing purposes)"""
    deleted_count = db.query(LineItem).delete()
    db.commit()

    return {
        "message": "All line items deleted",
        "deleted_count": deleted_count
    }


@router.delete("/{line_item_id}", status_code=204)
async def delete_line_item(
    line_item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a line item"""
    item = db.query(LineItem).filter(LineItem.line_item_id == line_item_id).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Line item not found")
    
    db.delete(item)
    db.commit()
    
    return None
