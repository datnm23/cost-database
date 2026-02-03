from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Literal
import logging

from app.core.database import get_db
from app.core.config import settings
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.line_item import LineItem, ClassificationMethod
from app.models.line_item_flag import LineItemFlag, FlagType
from app.services.classifier_service import get_classifier
from app.services.description_normalizer import DescriptionNormalizer
from app.services.ai_normalizer import get_ai_normalizer

from pydantic import BaseModel


class UpdateLineItemRequest(BaseModel):
    sec_code: Optional[str] = None
    needs_review: Optional[bool] = None


class BulkUpdateRequest(BaseModel):
    line_item_ids: List[int]
    sec_code: Optional[str] = None
    needs_review: Optional[bool] = None


class BulkNormalizeRequest(BaseModel):
    line_item_ids: List[int]


class CreateFlagRequest(BaseModel):
    line_item_id: int
    flag_type: str
    note: Optional[str] = None


class BulkCreateFlagRequest(BaseModel):
    line_item_ids: List[int]
    flag_type: str
    note: Optional[str] = None


class FlagResponse(BaseModel):
    flag_id: int
    line_item_id: int
    flag_type: str
    note: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def get_line_items(
    project_id: Optional[int] = None,
    file_id: Optional[int] = None,
    sec_code: Optional[str] = None,
    needs_review: bool = False,
    confidence_range: Optional[Literal["low", "medium", "high"]] = Query(
        None,
        description="Filter by confidence range: low (<80%), medium (80-95%), high (≥95%)"
    ),
    match_type: Optional[Literal["exact", "fuzzy", "none"]] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=10000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get line items with filters

    - **confidence_range**: Filter by confidence score range
      - low: <80% (needs attention)
      - medium: 80-95% (review recommended)
      - high: ≥95% (high confidence)
    - **match_type**: Filter by match type with master database
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

    # Confidence range filter
    if confidence_range == "low":
        query = query.filter(LineItem.confidence_score < 80)
    elif confidence_range == "medium":
        query = query.filter(LineItem.confidence_score >= 80, LineItem.confidence_score < 95)
    elif confidence_range == "high":
        query = query.filter(LineItem.confidence_score >= 95)

    # Match type filter
    if match_type:
        query = query.filter(LineItem.match_type == match_type)

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
                "normalized_description": item.normalized_description if hasattr(item, 'normalized_description') else None,
                "normalization_confidence": float(item.normalization_confidence) if hasattr(item, 'normalization_confidence') and item.normalization_confidence else None,
                "work_category": item.work_category if hasattr(item, 'work_category') else None,
                "unit": item.unit,
                "quantity": float(item.quantity) if item.quantity else 0,
                "unit_price": float(item.unit_price) if item.unit_price else 0,
                "amount": float(item.amount) if item.amount else 0,
                "sec_code": item.sec_code,
                "confidence_score": float(item.confidence_score) if item.confidence_score else 0,
                "classification_method": item.classification_method,
                "needs_review": item.needs_review if hasattr(item, 'needs_review') else False,
                "validation_issues": item.validation_issues if hasattr(item, 'validation_issues') else None,
                "matched_master_id": item.matched_master_id if hasattr(item, 'matched_master_id') else None,
                "match_similarity": float(item.match_similarity) if hasattr(item, 'match_similarity') and item.match_similarity else None,
                "match_type": item.match_type.value if hasattr(item, 'match_type') and item.match_type else None,
                "original_sheet_name": item.original_sheet_name if hasattr(item, 'original_sheet_name') else None,
                "flags": [
                    {"flag_type": f.flag_type.value, "note": f.note}
                    for f in (item.flags if hasattr(item, 'flags') else [])
                ],
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
        "normalized_description": item.normalized_description if hasattr(item, 'normalized_description') else None,
        "normalization_confidence": float(item.normalization_confidence) if hasattr(item, 'normalization_confidence') and item.normalization_confidence else None,
        "work_category": item.work_category if hasattr(item, 'work_category') else None,
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


@router.post("/{line_item_id}/normalize")
async def normalize_line_item(
    line_item_id: int,
    use_ai: bool = Query(True, description="Use AI-enhanced normalization"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Normalize a single line item's description.
    Uses AI-enhanced normalization by default for better accuracy.
    """
    item = db.query(LineItem).filter(LineItem.line_item_id == line_item_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Line item not found")

    if not item.description:
        raise HTTPException(status_code=400, detail="Line item has no description to normalize")

    try:
        ai_enhanced = False
        ai_corrections = []

        # Use AI normalizer if enabled and requested
        if use_ai and settings.AI_NORMALIZATION_ENABLED:
            try:
                ai_normalizer = get_ai_normalizer()
                result = ai_normalizer.normalize(item.description, use_ai=True)
                normalized = result.normalized
                work_category = result.work_category
                confidence = result.confidence
                ai_enhanced = result.ai_enhanced
                ai_corrections = result.ai_corrections or []
            except Exception as e:
                logger.warning(f"AI normalization failed, falling back to rule-based: {e}")
                use_ai = False

        # Fallback to rule-based normalization
        if not use_ai or not settings.AI_NORMALIZATION_ENABLED:
            normalizer = DescriptionNormalizer()
            normalized = normalizer.normalize(item.description)
            work_category = normalizer.identify_work_category(item.description)

            # Calculate confidence
            components = normalizer.parse_description(item.description)
            confidence = 100.0
            if not components.get('verb'):
                confidence -= 30
            if not components.get('material'):
                confidence -= 20
            if not components.get('position'):
                confidence -= 15
            if not components.get('grade') and not components.get('specs'):
                confidence -= 15
            confidence = max(0, confidence)

        # Update the item
        item.normalized_description = normalized
        item.work_category = work_category
        item.normalization_confidence = confidence

        db.commit()
        db.refresh(item)

        return {
            "message": "Line item normalized successfully",
            "line_item_id": item.line_item_id,
            "original_description": item.description,
            "normalized_description": item.normalized_description,
            "work_category": item.work_category,
            "normalization_confidence": float(item.normalization_confidence) if item.normalization_confidence else 0,
            "ai_enhanced": ai_enhanced,
            "ai_corrections": ai_corrections
        }
    except Exception as e:
        logger.error(f"Normalization failed for line item {line_item_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Normalization failed: {str(e)}")


@router.post("/bulk-normalize")
async def bulk_normalize(
    request: BulkNormalizeRequest,
    use_ai: bool = Query(True, description="Use AI-enhanced normalization"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Bulk normalize multiple line items.
    Uses AI-enhanced normalization by default for better accuracy.
    """
    # Get AI normalizer or fallback to rule-based
    ai_normalizer = None
    rule_normalizer = DescriptionNormalizer()

    if use_ai and settings.AI_NORMALIZATION_ENABLED:
        try:
            ai_normalizer = get_ai_normalizer()
        except Exception as e:
            logger.warning(f"AI normalizer not available: {e}")

    items = db.query(LineItem).filter(
        LineItem.line_item_id.in_(request.line_item_ids)
    ).all()

    if not items:
        raise HTTPException(status_code=404, detail="No line items found")

    results = {
        "total": len(items),
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "ai_enhanced_count": 0,
        "items": []
    }

    for item in items:
        if not item.description:
            results["skipped"] += 1
            continue

        try:
            ai_enhanced = False
            ai_corrections = []

            # Try AI normalization first
            if ai_normalizer:
                try:
                    result = ai_normalizer.normalize(item.description, use_ai=True)
                    normalized = result.normalized
                    work_category = result.work_category
                    confidence = result.confidence
                    ai_enhanced = result.ai_enhanced
                    ai_corrections = result.ai_corrections or []
                    if ai_enhanced:
                        results["ai_enhanced_count"] += 1
                except Exception as e:
                    logger.warning(f"AI normalization failed for item {item.line_item_id}: {e}")
                    ai_normalizer = None  # Disable for remaining items

            # Fallback to rule-based
            if not ai_normalizer:
                normalized = rule_normalizer.normalize(item.description)
                work_category = rule_normalizer.identify_work_category(item.description)

                # Calculate confidence
                components = rule_normalizer.parse_description(item.description)
                confidence = 100.0
                if not components.get('verb'):
                    confidence -= 30
                if not components.get('material'):
                    confidence -= 20
                if not components.get('position'):
                    confidence -= 15
                if not components.get('grade') and not components.get('specs'):
                    confidence -= 15
                confidence = max(0, confidence)

            item.normalized_description = normalized
            item.work_category = work_category
            item.normalization_confidence = confidence

            results["success"] += 1
            results["items"].append({
                "line_item_id": item.line_item_id,
                "normalized_description": normalized,
                "work_category": work_category,
                "confidence": confidence,
                "ai_enhanced": ai_enhanced,
                "ai_corrections": ai_corrections
            })
        except Exception as e:
            results["failed"] += 1
            logger.error(f"Normalization failed for line item {item.line_item_id}: {e}")

    db.commit()

    return {
        "message": "Bulk normalization completed",
        **results
    }


# ==============================================
# Flag Endpoints
# ==============================================

@router.post("/flags")
async def create_flag(
    request: CreateFlagRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a flag/note for a line item
    """
    # Validate flag type
    try:
        flag_type = FlagType(request.flag_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid flag type. Must be one of: {[t.value for t in FlagType]}"
        )

    # Verify line item exists
    item = db.query(LineItem).filter(LineItem.line_item_id == request.line_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Line item not found")

    flag = LineItemFlag(
        line_item_id=request.line_item_id,
        flag_type=flag_type,
        note=request.note,
        created_by=current_user.user_id
    )
    db.add(flag)
    db.commit()
    db.refresh(flag)

    return {
        "message": "Flag created successfully",
        "flag_id": flag.flag_id,
        "line_item_id": flag.line_item_id,
        "flag_type": flag.flag_type.value,
        "note": flag.note
    }


@router.post("/flags/bulk")
async def bulk_create_flags(
    request: BulkCreateFlagRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create flags for multiple line items
    """
    # Validate flag type
    try:
        flag_type = FlagType(request.flag_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid flag type. Must be one of: {[t.value for t in FlagType]}"
        )

    created_count = 0
    for line_item_id in request.line_item_ids:
        flag = LineItemFlag(
            line_item_id=line_item_id,
            flag_type=flag_type,
            note=request.note,
            created_by=current_user.user_id
        )
        db.add(flag)
        created_count += 1

    db.commit()

    return {
        "message": "Bulk flags created successfully",
        "created_count": created_count
    }


@router.delete("/{line_item_id}/flags/{flag_type}")
async def remove_flag(
    line_item_id: int,
    flag_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Remove a specific flag type from a line item
    """
    # Validate flag type
    try:
        ft = FlagType(flag_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid flag type. Must be one of: {[t.value for t in FlagType]}"
        )

    deleted_count = db.query(LineItemFlag).filter(
        LineItemFlag.line_item_id == line_item_id,
        LineItemFlag.flag_type == ft
    ).delete()

    db.commit()

    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Flag not found")

    return {
        "message": "Flag removed successfully",
        "deleted_count": deleted_count
    }


@router.get("/{line_item_id}/flags")
async def get_line_item_flags(
    line_item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all flags for a line item
    """
    flags = db.query(LineItemFlag).filter(
        LineItemFlag.line_item_id == line_item_id
    ).all()

    return {
        "line_item_id": line_item_id,
        "flags": [
            {
                "flag_id": f.flag_id,
                "flag_type": f.flag_type.value,
                "note": f.note,
                "created_at": f.created_at.isoformat() if f.created_at else None
            }
            for f in flags
        ]
    }
