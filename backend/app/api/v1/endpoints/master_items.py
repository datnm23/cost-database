"""
API Endpoints for Master Work Items
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.master_work_item import MasterWorkItem
from app.services.master_data_service import MasterDataService
from app.services.work_code_generator import WorkCodeGenerator
from app.services.boq_processing_service import get_boq_processing_service
from app.services.boq_export_service import get_boq_export_service

router = APIRouter()


# ==============================================
# Pydantic Schemas
# ==============================================

from pydantic import BaseModel, Field
from datetime import datetime


class MasterItemResponse(BaseModel):
    master_id: int
    work_code: str
    description: str
    description_normalized: Optional[str]
    sec_code: str
    category: Optional[str]
    unit_standard: str
    ref_unit_price_min: Optional[float]
    ref_unit_price_avg: Optional[float]
    ref_unit_price_max: Optional[float]
    occurrence_count: int
    source_files: Optional[str]
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MasterItemCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    sec_code: str = Field(..., pattern=r'^SEC-\d{2}(-\d{2})?$')
    unit: str = Field(..., max_length=20)
    unit_price: Optional[float] = Field(None, ge=0)


class MasterItemUpdate(BaseModel):
    description: Optional[str] = None
    sec_code: Optional[str] = None
    unit_standard: Optional[str] = None
    is_verified: Optional[bool] = None


class WorkCodeGenerateRequest(BaseModel):
    description: str
    sec_code: str
    unit: Optional[str] = None
    include_grade: bool = True


class WorkCodeGenerateResponse(BaseModel):
    work_code: str
    description: str
    sec_code: str
    material_grade: Optional[str]
    is_valid: bool
    parsed: Optional[dict]


class MasterStatisticsResponse(BaseModel):
    total_master_items: int
    verified_items: int
    unverified_items: int
    by_sec_code: dict
    by_material_grade: Optional[dict] = None


class BuildMasterRequest(BaseModel):
    file_id: int
    min_confidence: float = 60.0
    skip_unclassified: bool = False


class BuildMasterResponse(BaseModel):
    total_items: int
    added: int
    updated: int
    fuzzy_matched: Optional[int] = 0
    skipped: int
    by_sec_code: dict
    needs_review: Optional[List[dict]] = None


class BOQProcessRequest(BaseModel):
    """Request for processing BOQ file with new flow"""
    file_id: int
    auto_add_to_master: bool = False


class BOQProcessResponse(BaseModel):
    """Response from BOQ processing"""
    total_extracted: int
    after_raw_dedup: int
    after_normalize_dedup: int
    exact_matches: int
    fuzzy_matches: int
    new_items: int
    new_items_deduped: int
    needs_review: int
    ready_to_add: int


class MatchItemResponse(BaseModel):
    """Single match result"""
    original_description: str
    normalized_description: str
    match_type: str
    similarity_score: float
    master_work_code: Optional[str] = None
    needs_review: bool
    suggested_matches: Optional[List[dict]] = None


# ==============================================
# Endpoints
# ==============================================

@router.get("/", response_model=List[MasterItemResponse])
def list_master_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sec_code: Optional[str] = None,
    search: Optional[str] = None,
    verified_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    List master work items with filters

    - **skip**: Number of items to skip (pagination)
    - **limit**: Max number of items to return
    - **sec_code**: Filter by SEC code (e.g., SEC-01)
    - **search**: Search in description
    - **verified_only**: Only return verified items
    """
    query = db.query(MasterWorkItem).filter(MasterWorkItem.is_active == True)

    if sec_code:
        query = query.filter(MasterWorkItem.sec_code.like(f"{sec_code}%"))

    if search:
        query = query.filter(
            MasterWorkItem.description_normalized.like(f"%{search.lower()}%")
        )

    if verified_only:
        query = query.filter(MasterWorkItem.is_verified == True)

    items = query.order_by(MasterWorkItem.sec_code, MasterWorkItem.work_code)\
                 .offset(skip)\
                 .limit(limit)\
                 .all()

    return items


@router.get("/statistics", response_model=MasterStatisticsResponse)
def get_master_statistics(db: Session = Depends(get_db)):
    """
    Get statistics about master database
    """
    service = MasterDataService(db)
    stats = service.get_statistics()

    # Add material grade statistics
    from sqlalchemy import func
    grade_stats = db.query(
        func.substring_index(func.substring_index(MasterWorkItem.work_code, '-', 3), '-', -1).label('grade'),
        func.count(MasterWorkItem.master_id).label('count')
    ).filter(
        MasterWorkItem.work_code.like('%-M%-%')
    ).group_by('grade').all()

    stats['by_material_grade'] = {grade: count for grade, count in grade_stats}

    return stats


@router.get("/{master_id}", response_model=MasterItemResponse)
def get_master_item(master_id: int, db: Session = Depends(get_db)):
    """
    Get a specific master item by ID
    """
    item = db.query(MasterWorkItem).filter(
        MasterWorkItem.master_id == master_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Master item not found")

    return item


@router.post("/", response_model=MasterItemResponse, status_code=201)
def create_master_item(
    data: MasterItemCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new master work item manually
    """
    service = MasterDataService(db)
    generator = WorkCodeGenerator(db)

    # Generate work code
    work_code = generator.generate_work_code(
        description=data.description,
        sec_code=data.sec_code,
        unit=data.unit
    )

    # Check if work code already exists
    existing = db.query(MasterWorkItem).filter(
        MasterWorkItem.work_code == work_code
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Work code {work_code} already exists"
        )

    # Create master item
    desc_normalized = service.normalize_description(data.description)

    master_item = MasterWorkItem(
        work_code=work_code,
        description=data.description,
        description_normalized=desc_normalized,
        sec_code=data.sec_code,
        unit_standard=data.unit,
        ref_unit_price_avg=data.unit_price,
        ref_unit_price_min=data.unit_price,
        ref_unit_price_max=data.unit_price,
        occurrence_count=1,
        is_verified=False
    )

    db.add(master_item)
    db.commit()
    db.refresh(master_item)

    return master_item


@router.put("/{master_id}", response_model=MasterItemResponse)
def update_master_item(
    master_id: int,
    data: MasterItemUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a master work item
    """
    item = db.query(MasterWorkItem).filter(
        MasterWorkItem.master_id == master_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Master item not found")

    # Update fields
    if data.description is not None:
        item.description = data.description
        service = MasterDataService(db)
        item.description_normalized = service.normalize_description(data.description)

    if data.sec_code is not None:
        item.sec_code = data.sec_code

    if data.unit_standard is not None:
        item.unit_standard = data.unit_standard

    if data.is_verified is not None:
        item.is_verified = data.is_verified

    db.commit()
    db.refresh(item)

    return item


@router.delete("/{master_id}", status_code=204)
def delete_master_item(master_id: int, db: Session = Depends(get_db)):
    """
    Soft delete a master work item (set is_active = False)
    """
    item = db.query(MasterWorkItem).filter(
        MasterWorkItem.master_id == master_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Master item not found")

    item.is_active = False
    db.commit()

    return None


@router.post("/generate-code", response_model=WorkCodeGenerateResponse)
def generate_work_code(
    data: WorkCodeGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Generate work code for a description (preview only, doesn't save)
    """
    generator = WorkCodeGenerator(db)

    work_code = generator.generate_work_code(
        description=data.description,
        sec_code=data.sec_code,
        unit=data.unit,
        include_grade=data.include_grade
    )

    material_grade = generator.extract_material_grade(data.description)
    is_valid = generator.validate_work_code(work_code)
    parsed = generator.parse_work_code(work_code)

    return {
        "work_code": work_code,
        "description": data.description,
        "sec_code": data.sec_code,
        "material_grade": material_grade,
        "is_valid": is_valid,
        "parsed": parsed
    }


@router.post("/build", response_model=BuildMasterResponse)
def build_master_from_file(
    data: BuildMasterRequest,
    db: Session = Depends(get_db)
):
    """
    Build master database from a BOQ file
    """
    service = MasterDataService(db)

    stats = service.build_master_from_file(
        file_id=data.file_id,
        min_confidence=data.min_confidence,
        skip_unclassified=data.skip_unclassified
    )

    return stats


@router.post("/rebuild-all")
def rebuild_all_master_items(
    dry_run: bool = Query(True),
    db: Session = Depends(get_db)
):
    """
    Regenerate all work codes in master database

    - **dry_run**: If True, only preview changes without applying
    """
    generator = WorkCodeGenerator(db)

    stats = generator.regenerate_all_codes(dry_run=dry_run)

    return {
        "dry_run": dry_run,
        "total": stats['total'],
        "updated": stats['updated'],
        "skipped": stats['skipped'],
        "previews": stats['previews'][:20]  # First 20 changes
    }


@router.get("/search/by-code")
def search_by_work_code(
    code_pattern: str = Query(..., min_length=3),
    db: Session = Depends(get_db)
):
    """
    Search master items by work code pattern

    Examples:
    - S01-* : All SEC-01 items
    - *-M200-* : All M200 grade items
    - S02-CONC-* : All concrete items in SEC-02
    """
    items = db.query(MasterWorkItem).filter(
        MasterWorkItem.work_code.like(code_pattern.replace('*', '%')),
        MasterWorkItem.is_active == True
    ).order_by(MasterWorkItem.work_code).all()

    return {
        "pattern": code_pattern,
        "count": len(items),
        "items": items
    }


@router.get("/export/csv")
def export_master_csv(db: Session = Depends(get_db)):
    """
    Export master database to CSV

    Returns download URL
    """
    import os
    from datetime import datetime

    service = MasterDataService(db)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"master_work_items_{timestamp}.csv"
    output_path = f"/app/exports/{filename}"

    # Ensure exports directory exists
    os.makedirs("/app/exports", exist_ok=True)

    # Export
    service.export_master_csv(output_path)

    return {
        "filename": filename,
        "path": output_path,
        "message": "CSV exported successfully"
    }


# ==============================================
# BOQ Processing Flow Endpoints (New)
# ==============================================

@router.post("/process-boq", response_model=BOQProcessResponse)
def process_boq_file(
    data: BOQProcessRequest,
    db: Session = Depends(get_db)
):
    """
    Process BOQ file với flow mới:

    1. Extract tất cả công tác
    2. Lọc trùng tên gốc GIỐNG HỆT
    3. Chuẩn hóa toàn bộ
    4. So khớp với Master:
       - Exact match (≥95%) → Gán mã có sẵn
       - Fuzzy match (80-95%) → Review
       - No match (<80%) → Công tác mới
    5. Lọc trùng trong công tác mới
    6. (Optional) Thêm vào Master với mã mới

    Returns processing summary and statistics
    """
    service = get_boq_processing_service(db)

    result = service.process_line_items(
        file_id=data.file_id,
        auto_add_to_master=data.auto_add_to_master
    )

    summary = service.get_match_summary(result)
    return summary


@router.get("/process-boq/{file_id}/details")
def get_process_details(
    file_id: int,
    match_type: Optional[str] = Query(None, pattern="^(exact|fuzzy|new)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Get detailed processing results for a BOQ file

    - **match_type**: Filter by match type (exact, fuzzy, new)
    - **skip/limit**: Pagination
    """
    service = get_boq_processing_service(db)

    result = service.process_line_items(file_id=file_id, auto_add_to_master=False)

    items = result.items
    if match_type:
        items = [i for i in items if i.match_type == match_type]

    # Paginate
    total = len(items)
    items = items[skip:skip + limit]

    return {
        "file_id": file_id,
        "match_type_filter": match_type,
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [
            {
                "original_description": i.original_description,
                "normalized_description": i.normalized_description,
                "match_type": i.match_type,
                "similarity_score": round(i.similarity_score * 100, 1),
                "master_work_code": i.master_work_code,
                "needs_review": i.needs_review,
                "suggested_matches": i.suggested_matches[:3] if i.suggested_matches else []
            }
            for i in items
        ]
    }


@router.post("/process-boq/{file_id}/add-new")
def add_new_items_to_master(
    file_id: int,
    confirm: bool = Query(False, description="Confirm adding new items"),
    db: Session = Depends(get_db)
):
    """
    Add new items (không match với master) vào Master database

    - Chỉ thêm sau khi user review và confirm
    - Tự động tạo work code mới
    """
    if not confirm:
        # Dry run - show what would be added
        service = get_boq_processing_service(db)
        result = service.process_line_items(file_id=file_id, auto_add_to_master=False)

        new_items = [i for i in result.items if i.match_type == 'new']

        return {
            "action": "preview",
            "message": f"Found {len(new_items)} new items to add",
            "items": [
                {
                    "normalized_description": i.normalized_description,
                    "suggested_sec_code": "UNCLASSIFIED"
                }
                for i in new_items[:50]  # Preview first 50
            ],
            "confirm_url": f"/api/v1/master_items/process-boq/{file_id}/add-new?confirm=true"
        }

    # Actually add items
    service = get_boq_processing_service(db)
    result = service.process_line_items(file_id=file_id, auto_add_to_master=True)

    return {
        "action": "completed",
        "message": f"Added {result.new_items_deduped} new items to master",
        "added": result.new_items_deduped
    }


@router.post("/match-description")
def match_single_description(
    description: str = Query(..., min_length=5),
    db: Session = Depends(get_db)
):
    """
    Match a single description against master database

    Useful for testing or real-time matching during input
    """
    from app.services.description_normalizer import DescriptionNormalizer

    normalizer = DescriptionNormalizer()
    normalized = normalizer.normalize(description)

    service = get_boq_processing_service(db)

    # Use internal matching
    result = service.process_boq_items(
        file_id=0,
        items=[{"description": description}],
        auto_add_to_master=False
    )

    if result.items:
        item = result.items[0]
        return {
            "original": description,
            "normalized": normalized,
            "match_type": item.match_type,
            "similarity": round(item.similarity_score * 100, 1),
            "master_work_code": item.master_work_code,
            "suggested_matches": item.suggested_matches[:5] if item.suggested_matches else []
        }

    return {
        "original": description,
        "normalized": normalized,
        "match_type": "new",
        "similarity": 0,
        "master_work_code": None,
        "suggested_matches": []
    }


@router.get("/process-boq/{file_id}/export")
def export_processing_result(
    file_id: int,
    include_master: bool = Query(True, description="Include Master database reference sheet"),
    db: Session = Depends(get_db)
):
    """
    Export BOQ processing result to Excel file

    Returns:
        - Summary sheet with statistics
        - All processed items with match type
        - Exact matches (ready to assign)
        - Fuzzy matches (needs review)
        - New items (to add to Master)
        - Master database reference (optional)
    """
    import os
    from datetime import datetime

    export_service = get_boq_export_service(db)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"BOQ_Processing_Result_{file_id}_{timestamp}.xlsx"
    output_dir = "/tmp/exports"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    try:
        export_service.export_processing_result(
            file_id=file_id,
            output_path=output_path,
            include_master_match=include_master
        )

        return {
            "success": True,
            "filename": filename,
            "path": output_path,
            "message": "Export completed successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/process-boq/{file_id}/export/download")
def download_export_file(
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    Export and download BOQ processing result as Excel file
    """
    import os
    from datetime import datetime
    from fastapi.responses import FileResponse

    export_service = get_boq_export_service(db)

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"BOQ_Processing_Result_{file_id}_{timestamp}.xlsx"
    output_dir = "/tmp/exports"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    try:
        export_service.export_processing_result(
            file_id=file_id,
            output_path=output_path,
            include_master_match=True
        )

        return FileResponse(
            path=output_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/line-items/{file_id}/export")
def export_line_items(
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    Export line items with SEC classification to Excel
    """
    import os
    from datetime import datetime

    export_service = get_boq_export_service(db)

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Line_Items_Classified_{file_id}_{timestamp}.xlsx"
    output_dir = "/tmp/exports"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    try:
        export_service.export_line_items_with_classification(
            file_id=file_id,
            output_path=output_path
        )

        return {
            "success": True,
            "filename": filename,
            "path": output_path,
            "message": "Export completed successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/line-items/{file_id}/export/original")
def export_with_original_format(
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    Export line items with original Excel format preserved

    This endpoint:
    - Copies the original uploaded Excel file
    - Adds a new "Processing Results" sheet with all line items
    - Preserves all original formatting, comments, formulas, and notes
    - Adds hyperlinks from results back to original rows

    Returns the exported file for download.
    """
    import os
    from datetime import datetime
    from fastapi.responses import FileResponse

    export_service = get_boq_export_service(db)

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"BOQ_Original_Format_{file_id}_{timestamp}.xlsx"
    output_dir = "/tmp/exports"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    try:
        export_service.export_with_original_format(
            file_id=file_id,
            output_path=output_path
        )

        return FileResponse(
            path=output_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
