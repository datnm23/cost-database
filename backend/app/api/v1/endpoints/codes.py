"""
API Endpoints for Multi-Code System
Legal Codes, ISO Codes, and Code Mapping
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.services.legal_code_service import LegalCodeService
from app.services.iso_classification_service import ISOClassificationService


router = APIRouter(prefix="/api/v1/codes", tags=["Code Management"])


# ==================== Pydantic Models ====================

class LegalCodeInfo(BaseModel):
    """Legal Code information"""
    legal_code: str
    prefix: str
    number: str
    suffix: Optional[str]
    category_vn: str
    category_en: str
    appendix: str
    suggested_sec_codes: List[str]


class ISOCodeInfo(BaseModel):
    """ISO Code information"""
    iso_code: str
    level: int
    entity: Optional[str]
    entity_name_vn: Optional[str]
    system: Optional[str]
    system_name_vn: Optional[str]
    element: Optional[str]
    element_name_vn: Optional[str]
    product: Optional[str]
    product_name_vn: Optional[str]
    suggested_sec: Optional[str]


class CodeMappingRequest(BaseModel):
    """Request to map codes"""
    description: str
    sec_code: Optional[str] = None
    unit: Optional[str] = None
    material_grade: Optional[str] = None


class CodeMappingResponse(BaseModel):
    """Response with all codes"""
    description: str
    work_code: Optional[str]
    legal_code: Optional[str]
    iso_code: Optional[str]
    sec_code: Optional[str]
    material_grade: Optional[str]
    confidence_score: float


class MultiCodeSearch(BaseModel):
    """Search across all code systems"""
    query: str
    results: List[dict]


# ==================== Legal Code Endpoints ====================

@router.get("/legal/parse/{legal_code}", response_model=LegalCodeInfo)
def parse_legal_code(
    legal_code: str,
    db: Session = Depends(get_db)
):
    """
    Phân tích legal code thành các thành phần
    
    Example: GET /api/v1/codes/legal/parse/AA.1111
    """
    service = LegalCodeService(db)
    result = service.parse_legal_code(legal_code)
    
    if not result:
        raise HTTPException(status_code=400, detail="Invalid legal code format")
    
    return result


@router.get("/legal/search")
def search_legal_codes(
    query: Optional[str] = Query(None, description="Search query"),
    prefix: Optional[str] = Query(None, description="Filter by prefix (AA, AF, etc.)"),
    appendix: Optional[str] = Query(None, description="Filter by appendix (I, II, III)"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Tìm kiếm legal codes
    
    Example: GET /api/v1/codes/legal/search?prefix=AF&limit=10
    """
    service = LegalCodeService(db)
    results = service.search_legal_codes(
        query=query,
        prefix=prefix,
        appendix=appendix,
        limit=limit
    )
    
    return {
        "total": len(results),
        "results": results
    }


@router.post("/legal/generate")
def generate_legal_code(
    request: CodeMappingRequest,
    db: Session = Depends(get_db)
):
    """
    Tạo legal code từ description
    
    Example:
    POST /api/v1/codes/legal/generate
    {
        "description": "Đào đất hố móng bằng máy",
        "sec_code": "SEC-01-01"
    }
    """
    service = LegalCodeService(db)
    legal_code = service.generate_legal_code_from_description(
        request.description,
        request.sec_code
    )
    
    # Parse to get details
    parsed = service.parse_legal_code(legal_code)
    
    return {
        "description": request.description,
        "legal_code": legal_code,
        "details": parsed
    }


@router.get("/legal/statistics")
def get_legal_code_statistics(db: Session = Depends(get_db)):
    """
    Thống kê legal codes theo prefix
    
    Example: GET /api/v1/codes/legal/statistics
    """
    service = LegalCodeService(db)
    stats = service.get_prefix_statistics()
    
    return {
        "total_prefixes": len(stats),
        "statistics": stats
    }


# ==================== ISO Code Endpoints ====================

@router.get("/iso/parse/{iso_code}", response_model=ISOCodeInfo)
def parse_iso_code(
    iso_code: str,
    db: Session = Depends(get_db)
):
    """
    Phân tích ISO code thành các thành phần
    
    Example: GET /api/v1/codes/iso/parse/Pr_21_31_13
    """
    service = ISOClassificationService(db)
    result = service.parse_iso_code(iso_code)
    
    if not result:
        raise HTTPException(status_code=400, detail="Invalid ISO code format")
    
    return result


@router.post("/iso/generate")
def generate_iso_code(
    request: CodeMappingRequest,
    db: Session = Depends(get_db)
):
    """
    Tạo ISO code từ description
    
    Example:
    POST /api/v1/codes/iso/generate
    {
        "description": "Đổ bê tông dầm M200",
        "sec_code": "SEC-02",
        "material_grade": "M200"
    }
    """
    service = ISOClassificationService(db)
    iso_code = service.generate_iso_code(
        request.description,
        request.sec_code,
        material_grade=request.material_grade
    )
    
    # Parse to get details
    parsed = service.parse_iso_code(iso_code)
    
    return {
        "description": request.description,
        "iso_code": iso_code,
        "details": parsed
    }


@router.get("/iso/hierarchy/{iso_code}")
def get_iso_hierarchy(
    iso_code: str,
    db: Session = Depends(get_db)
):
    """
    Lấy hierarchy path của ISO code
    
    Example: GET /api/v1/codes/iso/hierarchy/Pr_21_31_13
    """
    service = ISOClassificationService(db)
    path = service.get_hierarchy_path(iso_code)
    
    if not path:
        raise HTTPException(status_code=400, detail="Invalid ISO code")
    
    return {
        "iso_code": iso_code,
        "hierarchy": path
    }


# ==================== Multi-Code Mapping Endpoints ====================

@router.post("/map/auto", response_model=CodeMappingResponse)
def auto_map_codes(
    request: CodeMappingRequest,
    db: Session = Depends(get_db)
):
    """
    Tự động map tất cả codes (Work, Legal, ISO) từ description
    
    Example:
    POST /api/v1/codes/map/auto
    {
        "description": "Đào đất hố móng bằng máy - 1.25m - đất cấp 3",
        "sec_code": "SEC-01-01",
        "unit": "m3"
    }
    """
    from app.services.work_code_generator import WorkCodeGenerator
    
    work_gen = WorkCodeGenerator(db)
    legal_svc = LegalCodeService(db)
    iso_svc = ISOClassificationService(db)
    
    # Extract material grade
    material_grade = work_gen.extract_material_grade(request.description)
    if request.material_grade:
        material_grade = request.material_grade
    
    # Generate all codes
    work_code = work_gen.generate_work_code(
        request.description,
        request.sec_code or 'SEC-99',
        request.unit
    )
    
    legal_code = legal_svc.generate_legal_code_from_description(
        request.description,
        request.sec_code
    )
    
    iso_code = iso_svc.generate_iso_code(
        request.description,
        request.sec_code,
        legal_code,
        material_grade
    )
    
    # Calculate confidence (simplified)
    confidence = 75.0
    if material_grade:
        confidence += 10.0
    if request.sec_code:
        confidence += 10.0
    
    return {
        "description": request.description,
        "work_code": work_code,
        "legal_code": legal_code,
        "iso_code": iso_code,
        "sec_code": request.sec_code,
        "material_grade": material_grade,
        "confidence_score": min(confidence, 95.0)
    }


@router.post("/map/batch")
def batch_map_codes(
    items: List[CodeMappingRequest],
    db: Session = Depends(get_db)
):
    """
    Batch mapping cho nhiều items
    
    Example:
    POST /api/v1/codes/map/batch
    [
        {"description": "Đào đất móng", "sec_code": "SEC-01-01"},
        {"description": "Đổ bê tông dầm", "sec_code": "SEC-02"}
    ]
    """
    from app.services.work_code_generator import WorkCodeGenerator
    
    work_gen = WorkCodeGenerator(db)
    legal_svc = LegalCodeService(db)
    iso_svc = ISOClassificationService(db)
    
    results = []
    
    for request in items:
        try:
            material_grade = work_gen.extract_material_grade(request.description)
            
            work_code = work_gen.generate_work_code(
                request.description,
                request.sec_code or 'SEC-99',
                request.unit
            )
            
            legal_code = legal_svc.generate_legal_code_from_description(
                request.description,
                request.sec_code
            )
            
            iso_code = iso_svc.generate_iso_code(
                request.description,
                request.sec_code,
                legal_code,
                material_grade
            )
            
            results.append({
                "description": request.description,
                "work_code": work_code,
                "legal_code": legal_code,
                "iso_code": iso_code,
                "material_grade": material_grade,
                "status": "success"
            })
        
        except Exception as e:
            results.append({
                "description": request.description,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "total": len(items),
        "successful": len([r for r in results if r.get("status") == "success"]),
        "failed": len([r for r in results if r.get("status") == "error"]),
        "results": results
    }


@router.get("/search/multi")
def multi_code_search(
    query: str = Query(..., description="Search across all code systems"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Tìm kiếm đồng thời trên Work Code, Legal Code, ISO Code

    Example: GET /api/v1/codes/search/multi?query=bê tông&limit=10
    """
    # Would search across all tables
    # Simplified placeholder

    return {
        "query": query,
        "total_results": 0,
        "results": {
            "work_codes": [],
            "legal_codes": [],
            "iso_codes": []
        }
    }


# ==================== SEC Code v4.0 Endpoints ====================

class SECCodeV4Response(BaseModel):
    """SEC Code v4.0 information (3-level format: PREFIX.GROUP.TYPE)"""
    code: str
    table_type: str
    group_code: str
    type_code: str
    name_vi: Optional[str]
    name_en: Optional[str]
    unit: Optional[str]
    keywords_vi: Optional[str]
    keywords_en: Optional[str]
    waste_percent: Optional[float]
    is_active: bool

    class Config:
        from_attributes = True


@router.get("/v4/", response_model=list)
def list_v4_codes(
    table_type: Optional[str] = Query(None, pattern="^[AMLE]$", description="Filter: A/M/L/E"),
    group_code: Optional[str] = Query(None, description="Filter by group (CONC, RBAR, PIPE, etc.)"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    List v4.0 reference codes (3-level format) with optional filters.

    Code format: PREFIX.GROUP.TYPE  (e.g. A.CONC.STR)

    Examples:
    - GET /api/v1/codes/v4/?table_type=A — All activity codes
    - GET /api/v1/codes/v4/?group_code=CONC — All concrete codes across tables
    - GET /api/v1/codes/v4/?table_type=M&group_code=CONC — Concrete material codes
    """
    from app.services.sec_code_v4_mapper import get_sec_code_v4_mapper

    mapper = get_sec_code_v4_mapper(db)
    codes = mapper.list_codes(
        table_type=table_type,
        group_code=group_code,
        limit=limit,
        offset=offset,
    )

    return [
        {
            "code": c.code,
            "table_type": c.table_type,
            "group_code": c.group_code,
            "type_code": c.type_code,
            "name_vi": c.name_vi,
            "name_en": c.name_en,
            "unit": c.unit,
            "keywords_vi": c.keywords_vi,
            "keywords_en": c.keywords_en,
            "waste_percent": c.waste_percent,
            "is_active": c.is_active,
        }
        for c in codes
    ]


@router.get("/v4/mapping")
def get_legacy_to_v4_mapping(
    db: Session = Depends(get_db),
):
    """
    Get the complete legacy SEC-xx → v4.0 discipline mapping.

    Returns a dict mapping legacy SEC codes to v4.0 discipline codes.
    """
    from app.services.sec_code_v4_mapper import get_sec_code_v4_mapper

    mapper = get_sec_code_v4_mapper(db)
    mapping = mapper.get_full_mapping()

    return {
        "total_mappings": len(mapping),
        "mapping": mapping,
    }


@router.post("/v4/map-item/{master_id}")
def map_item_to_v4(
    master_id: int,
    table_type: str = Query("A", pattern="^[AMLE]$"),
    db: Session = Depends(get_db),
):
    """
    Map a master item to a v4.0 code.

    Generates and saves a v4.0 code for the given master item.
    """
    from app.models.master_work_item import MasterWorkItem
    from app.services.v4_code_generator import V4CodeGenerator

    item = db.query(MasterWorkItem).filter(
        MasterWorkItem.master_id == master_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Master item not found")

    generator = V4CodeGenerator()
    specs = {
        'category': item.spec_category,
        'material': item.spec_material,
        'grade': item.spec_grade,
        'dimension': item.spec_dimension,
    }

    v4_code = generator.generate(
        description=item.description,
        sec_code=item.sec_code,
        specs=specs,
        table_type=table_type,
    )

    # Save
    if not item.work_code_legacy:
        item.work_code_legacy = item.work_code
    item.sec_code_v4 = v4_code
    item.item_table_type = table_type

    # Generate unique instance code
    instance_code = generator.generate_instance_code(
        ref_code=v4_code,
        db=db,
    )
    item.instance_code = instance_code
    db.commit()

    return {
        "master_id": master_id,
        "v4_code": v4_code,
        "instance_code": instance_code,
        "saved": True,
        "work_code_legacy": item.work_code_legacy,
    }
