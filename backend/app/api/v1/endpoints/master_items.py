"""
API Endpoints for Master Work Items
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.master_work_item import MasterWorkItem
from app.models.line_item import LineItem
from app.services.master_data_service import MasterDataService
from app.services.work_code_generator import WorkCodeGenerator
from app.services.boq_processing_service import get_boq_processing_service
from app.services.boq_export_service import get_boq_export_service
from app.services.master_database_builder import (
    MasterDatabaseBuilder,
    BuildConfig,
    get_master_database_builder,
)

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
    processing_method: str = "3_tier"  # "3_tier" (hybrid) or "ai_only" (100% AI semantic)


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


class MasterBuildBatchRequest(BaseModel):
    """Request for batch master database build (3-step pipeline)"""
    file_ids: List[int] = Field(..., min_length=1)
    project_id: Optional[int] = None
    pareto_threshold: float = Field(0.80, ge=0.0, le=1.0)
    clustering_threshold: float = Field(0.85, ge=0.5, le=1.0)
    min_frequency: int = Field(1, ge=1)
    auto_approve: bool = False
    clear_existing: bool = False
    include_only_pareto: bool = False


class StepStatsResponse(BaseModel):
    input_count: int
    output_count: int
    details: dict


class MasterBuildBatchResponse(BaseModel):
    """Response from batch master database build"""
    step1_aggregation: StepStatsResponse
    step2_standardization: StepStatsResponse
    step3_coding_tagging: StepStatsResponse
    total_master_added: int
    total_pending: int
    total_quarantined: int
    total_updated: int
    total_synonyms_added: int


class AggregationPreviewItem(BaseModel):
    description: str
    unit: Optional[str]
    frequency: int
    source_file_count: int


class AggregationPreviewResponse(BaseModel):
    """Preview response for step 1 aggregation"""
    total_unique_descriptions: int
    total_line_items: int
    top_items: List[AggregationPreviewItem]
    frequency_distribution: dict
    estimated_pareto_count: int


class MatchAcceptItem(BaseModel):
    """Single accepted match item"""
    line_item_id: int
    description: str
    matched_master_id: Optional[int]
    match_similarity: Optional[float]
    sec_code: Optional[str]


class MatchAcceptResponse(BaseModel):
    """Response from accepting exact matches"""
    accepted_count: int
    items: List[MatchAcceptItem]


class FuzzyReviewItem(BaseModel):
    """Single fuzzy match item for review"""
    line_item_id: int
    description: str
    normalized_description: Optional[str]
    matched_master_id: Optional[int]
    matched_master_description: Optional[str]
    match_similarity: Optional[float]
    sec_code: Optional[str]


class FuzzyReviewResponse(BaseModel):
    """Response from reviewing fuzzy matches"""
    pending_count: int
    items: List[FuzzyReviewItem]


class AcceptMatchResponse(BaseModel):
    """Response from accepting a single match"""
    line_item_id: int
    accepted: bool
    message: str


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
        auto_add_to_master=data.auto_add_to_master,
        processing_method=data.processing_method
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


@router.post("/build-master-batch", response_model=MasterBuildBatchResponse)
def build_master_batch(
    data: MasterBuildBatchRequest,
    db: Session = Depends(get_db)
):
    """
    Execute full 3-step master database build from multiple BOQ files.

    Steps:
    1. **Aggregation**: Scan line_items grouped by (description, unit), count frequency
    2. **Standardization**: Normalize, cluster similar descriptions, elect canonical names, apply Pareto
    3. **Coding & Tagging**: Classify SEC, extract specs, generate work codes, validate, persist

    Suitable for small-to-medium batches (synchronous).
    """
    builder = get_master_database_builder(db)
    config = BuildConfig(
        pareto_threshold=data.pareto_threshold,
        clustering_threshold=data.clustering_threshold,
        min_frequency=data.min_frequency,
        auto_approve=data.auto_approve,
        clear_existing=data.clear_existing,
        include_only_pareto=data.include_only_pareto,
    )

    result = builder.build(file_ids=data.file_ids, config=config)

    return {
        "step1_aggregation": {
            "input_count": result.step1_stats.input_count,
            "output_count": result.step1_stats.output_count,
            "details": result.step1_stats.details,
        },
        "step2_standardization": {
            "input_count": result.step2_stats.input_count,
            "output_count": result.step2_stats.output_count,
            "details": result.step2_stats.details,
        },
        "step3_coding_tagging": {
            "input_count": result.step3_stats.input_count,
            "output_count": result.step3_stats.output_count,
            "details": result.step3_stats.details,
        },
        "total_master_added": result.total_master_added,
        "total_pending": result.total_pending,
        "total_quarantined": result.total_quarantined,
        "total_updated": result.total_updated,
        "total_synonyms_added": result.total_synonyms_added,
    }


@router.post("/build-master-batch/preview", response_model=AggregationPreviewResponse)
def preview_master_batch(
    data: MasterBuildBatchRequest,
    db: Session = Depends(get_db)
):
    """
    Preview step 1 (aggregation only) without modifying the database.

    Returns:
    - Top items by frequency
    - Frequency distribution
    - Estimated Pareto count (how many items cover 80% of total frequency)
    """
    builder = get_master_database_builder(db)
    aggregated = builder.step1_aggregate(
        file_ids=data.file_ids,
        min_frequency=data.min_frequency,
    )

    if not aggregated:
        return {
            "total_unique_descriptions": 0,
            "total_line_items": 0,
            "top_items": [],
            "frequency_distribution": {},
            "estimated_pareto_count": 0,
        }

    total_line_items = sum(a.frequency for a in aggregated)

    # Top 50 items
    top_items = [
        {
            "description": a.representative_description,
            "unit": a.unit,
            "frequency": a.frequency,
            "source_file_count": len(a.source_file_ids),
        }
        for a in aggregated[:50]
    ]

    # Frequency distribution buckets
    freq_dist = {"1": 0, "2-5": 0, "6-10": 0, "11-50": 0, "50+": 0}
    for a in aggregated:
        if a.frequency == 1:
            freq_dist["1"] += 1
        elif a.frequency <= 5:
            freq_dist["2-5"] += 1
        elif a.frequency <= 10:
            freq_dist["6-10"] += 1
        elif a.frequency <= 50:
            freq_dist["11-50"] += 1
        else:
            freq_dist["50+"] += 1

    # Estimate Pareto count
    target = total_line_items * data.pareto_threshold
    cumulative = 0
    pareto_count = 0
    for a in aggregated:
        cumulative += a.frequency
        pareto_count += 1
        if cumulative >= target:
            break

    return {
        "total_unique_descriptions": len(aggregated),
        "total_line_items": total_line_items,
        "top_items": top_items,
        "frequency_distribution": freq_dist,
        "estimated_pareto_count": pareto_count,
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


# ==============================================
# Auto-assign match endpoints
# ==============================================

@router.post("/process-boq/{file_id}/accept-exact-matches", response_model=MatchAcceptResponse)
def accept_exact_matches(
    file_id: int,
    db: Session = Depends(get_db),
):
    """
    Accept all exact matches (≥95% similarity) for a BOQ file.

    Queries line_items with match_type='exact' and needs_review=False,
    and returns the list of accepted items.
    """
    items = db.query(LineItem).filter(
        LineItem.file_id == file_id,
        LineItem.match_type == 'exact',
        LineItem.needs_review == False,
        LineItem.matched_master_id.isnot(None),
    ).all()

    result_items = []
    for li in items:
        result_items.append(MatchAcceptItem(
            line_item_id=li.line_item_id,
            description=li.description or '',
            matched_master_id=li.matched_master_id,
            match_similarity=float(li.match_similarity) if li.match_similarity else None,
            sec_code=li.sec_code,
        ))

    return MatchAcceptResponse(
        accepted_count=len(result_items),
        items=result_items,
    )


@router.post("/process-boq/{file_id}/review-fuzzy-matches", response_model=FuzzyReviewResponse)
def review_fuzzy_matches(
    file_id: int,
    db: Session = Depends(get_db),
):
    """
    Get all fuzzy matches (80-95% similarity) that need manual review.

    Returns pending items with match details for user review.
    """
    items = db.query(LineItem).filter(
        LineItem.file_id == file_id,
        LineItem.match_type == 'fuzzy',
        LineItem.needs_review == True,
    ).all()

    result_items = []
    for li in items:
        # Get matched master description if available
        master_desc = None
        if li.matched_master_id:
            master = db.query(MasterWorkItem).filter(
                MasterWorkItem.master_id == li.matched_master_id
            ).first()
            if master:
                master_desc = master.description

        result_items.append(FuzzyReviewItem(
            line_item_id=li.line_item_id,
            description=li.description or '',
            normalized_description=li.normalized_description,
            matched_master_id=li.matched_master_id,
            matched_master_description=master_desc,
            match_similarity=float(li.match_similarity) if li.match_similarity else None,
            sec_code=li.sec_code,
        ))

    return FuzzyReviewResponse(
        pending_count=len(result_items),
        items=result_items,
    )


@router.post("/process-boq/accept-match/{line_item_id}", response_model=AcceptMatchResponse)
def accept_single_match(
    line_item_id: int,
    db: Session = Depends(get_db),
):
    """
    Accept an individual fuzzy match, setting needs_review=False.
    """
    li = db.query(LineItem).filter(
        LineItem.line_item_id == line_item_id,
    ).first()

    if not li:
        raise HTTPException(status_code=404, detail="Line item not found")

    if li.match_type != 'fuzzy':
        raise HTTPException(
            status_code=400,
            detail=f"Line item match_type is '{li.match_type}', expected 'fuzzy'",
        )

    li.needs_review = False
    db.commit()

    return AcceptMatchResponse(
        line_item_id=line_item_id,
        accepted=True,
        message="Fuzzy match accepted successfully",
    )
