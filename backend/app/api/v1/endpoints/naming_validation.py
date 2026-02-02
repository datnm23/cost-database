"""
API Endpoints for Natural Name Validation
Implement validate_natural_name() and related endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.services.enhanced_naming_service import EnhancedNamingService


router = APIRouter(prefix="/api/v1/naming", tags=["Naming Validation"])


# ==================== Pydantic Models ====================

class ValidationRequest(BaseModel):
    """Request to validate natural name"""
    name: str
    sec_code: Optional[str] = None
    strict_mode: bool = False


class ValidationResponse(BaseModel):
    """Validation response"""
    name: str
    is_valid: bool
    has_verb: bool
    has_specs: bool
    length: int
    parts_count: int
    issues: List[str]
    suggestions: Optional[List[str]] = None
    confidence_score: float


class NaturalNameGenerateRequest(BaseModel):
    """Request to generate natural name"""
    description: str
    sec_code: str
    material_grade: Optional[str] = None
    material_spec: Optional[dict] = None


class NaturalNameGenerateResponse(BaseModel):
    """Generate response"""
    original_description: str
    natural_name: str
    material_spec: Optional[dict]
    validation: ValidationResponse


class VerbDictionaryItem(BaseModel):
    """Verb dictionary item"""
    en_key: str
    vn_verb: str
    category: str
    examples: List[str]


class LocationDictionaryItem(BaseModel):
    """Location dictionary item"""
    en_key: str
    vn_location: str
    category: str
    sec_codes: List[str]


# ==================== Validation Endpoints ====================

@router.post("/validate", response_model=ValidationResponse)
def validate_natural_name(
    request: ValidationRequest,
    db: Session = Depends(get_db)
):
    """
    Validate tên tự nhiên theo quy chuẩn 4-part syntax
    
    Example:
    POST /api/v1/naming/validate
    {
        "name": "Lắp ống cấp nước trục đứng - PPR - D63 - PN16",
        "sec_code": "SEC-04",
        "strict_mode": false
    }
    """
    service = EnhancedNamingService(db)
    validation = service.validate_natural_name(request.name)
    
    # Add suggestions if not valid
    suggestions = []
    if not validation['is_valid']:
        if not validation['has_verb']:
            suggestions.append("Thêm động từ đầu tên (Đào, Lắp, Xây, etc.)")
        
        if validation['parts_count'] < 2:
            suggestions.append("Phân tách thành phần bằng dấu ' - '")
        
        if validation['length'] < 20:
            suggestions.append("Bổ sung thông tin chi tiết (vật liệu, kích thước)")
        elif validation['length'] > 100:
            suggestions.append("Rút gọn bớt, giữ trong 80 ký tự")
    
    # Calculate confidence score
    confidence = 100.0
    if not validation['has_verb']:
        confidence -= 30
    if not validation['has_specs']:
        confidence -= 20
    if validation['parts_count'] < 2:
        confidence -= 25
    if validation['length'] < 20 or validation['length'] > 100:
        confidence -= 15
    
    confidence = max(0, confidence)
    
    return ValidationResponse(
        name=request.name,
        is_valid=validation['is_valid'] if not request.strict_mode else (confidence >= 80),
        has_verb=validation['has_verb'],
        has_specs=validation['has_specs'],
        length=validation['length'],
        parts_count=validation['parts_count'],
        issues=validation['issues'],
        suggestions=suggestions if suggestions else None,
        confidence_score=confidence
    )


@router.post("/generate", response_model=NaturalNameGenerateResponse)
def generate_natural_name(
    request: NaturalNameGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Tạo tên tự nhiên từ description
    
    Example:
    POST /api/v1/naming/generate
    {
        "description": "Lắp ống cấp nước trục đứng PPR D63 PN16",
        "sec_code": "SEC-04",
        "material_grade": null
    }
    """
    service = EnhancedNamingService(db)
    
    # Generate natural name
    natural_name = service.generate_natural_name(
        request.description,
        request.sec_code,
        request.material_grade
    )
    
    # Extract MEP specs
    mep_specs = service.extract_mep_specs(request.description)
    
    # Build material_spec JSON
    material_spec_json = service.build_material_spec_json(**mep_specs)
    
    # Validate generated name
    validation_result = service.validate_natural_name(natural_name)
    
    # Build validation response
    validation = ValidationResponse(
        name=natural_name,
        is_valid=validation_result['is_valid'],
        has_verb=validation_result['has_verb'],
        has_specs=validation_result['has_specs'],
        length=validation_result['length'],
        parts_count=validation_result['parts_count'],
        issues=validation_result['issues'],
        confidence_score=85.0 if validation_result['is_valid'] else 60.0
    )
    
    return NaturalNameGenerateResponse(
        original_description=request.description,
        natural_name=natural_name,
        material_spec=material_spec_json if material_spec_json else None,
        validation=validation
    )


@router.post("/batch/validate")
def batch_validate(
    names: List[str],
    strict_mode: bool = False,
    db: Session = Depends(get_db)
):
    """
    Batch validation cho nhiều tên
    
    Example:
    POST /api/v1/naming/batch/validate
    [
        "Đào đất hố móng - Máy đào - Đất cấp 3",
        "Lắp ống PPR - D63 - PN16",
        "Xây tường gạch ống"
    ]
    """
    service = EnhancedNamingService(db)
    results = []
    
    for name in names:
        validation = service.validate_natural_name(name)
        
        confidence = 100.0
        if not validation['has_verb']:
            confidence -= 30
        if not validation['has_specs']:
            confidence -= 20
        if validation['parts_count'] < 2:
            confidence -= 25
        confidence = max(0, confidence)
        
        results.append({
            'name': name,
            'is_valid': validation['is_valid'] if not strict_mode else (confidence >= 80),
            'confidence_score': confidence,
            'issues': validation['issues']
        })
    
    return {
        'total': len(names),
        'valid': len([r for r in results if r['is_valid']]),
        'invalid': len([r for r in results if not r['is_valid']]),
        'results': results
    }


@router.post("/batch/generate")
def batch_generate(
    items: List[NaturalNameGenerateRequest],
    db: Session = Depends(get_db)
):
    """
    Batch generation cho nhiều items
    
    Example:
    POST /api/v1/naming/batch/generate
    [
        {"description": "Đào đất móng", "sec_code": "SEC-01-01"},
        {"description": "Lắp ống PPR D63", "sec_code": "SEC-04"}
    ]
    """
    service = EnhancedNamingService(db)
    results = []
    
    for item in items:
        try:
            natural_name = service.generate_natural_name(
                item.description,
                item.sec_code,
                item.material_grade
            )
            
            mep_specs = service.extract_mep_specs(item.description)
            material_spec = service.build_material_spec_json(**mep_specs)
            
            validation = service.validate_natural_name(natural_name)
            
            results.append({
                'original': item.description,
                'natural_name': natural_name,
                'material_spec': material_spec,
                'is_valid': validation['is_valid'],
                'status': 'success'
            })
        
        except Exception as e:
            results.append({
                'original': item.description,
                'status': 'error',
                'error': str(e)
            })
    
    return {
        'total': len(items),
        'successful': len([r for r in results if r.get('status') == 'success']),
        'failed': len([r for r in results if r.get('status') == 'error']),
        'results': results
    }


# ==================== Dictionary Endpoints ====================

@router.get("/dictionary/verbs", response_model=List[VerbDictionaryItem])
def get_verb_dictionary(
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    """
    Lấy từ điển động từ chuẩn
    
    Example: GET /api/v1/naming/dictionary/verbs?category=construction
    """
    service = EnhancedNamingService(db)
    
    # Categorize verbs
    categorized = {
        'construction': [],
        'mep': [],
        'finishing': [],
        'commissioning': []
    }
    
    for en_key, vn_verb in service.STANDARD_VERBS.items():
        # Simple categorization
        if any(kw in en_key for kw in ['excavate', 'pile', 'concrete', 'steel']):
            cat = 'construction'
        elif any(kw in en_key for kw in ['install', 'mount', 'wire', 'pipe']):
            cat = 'mep'
        elif any(kw in en_key for kw in ['paint', 'tile', 'plaster', 'lay']):
            cat = 'finishing'
        elif any(kw in en_key for kw in ['test', 'commission', 'train']):
            cat = 'commissioning'
        else:
            cat = 'construction'
        
        categorized[cat].append({
            'en_key': en_key,
            'vn_verb': vn_verb,
            'category': cat,
            'examples': [f"{vn_verb} ..."]
        })
    
    # Filter by category if provided
    if category and category in categorized:
        return categorized[category]
    
    # Return all
    all_verbs = []
    for cat_items in categorized.values():
        all_verbs.extend(cat_items)
    
    return all_verbs


@router.get("/dictionary/locations", response_model=List[LocationDictionaryItem])
def get_location_dictionary(
    db: Session = Depends(get_db)
):
    """
    Lấy từ điển vị trí/môi trường chuẩn
    
    Example: GET /api/v1/naming/dictionary/locations
    """
    service = EnhancedNamingService(db)
    
    locations = []
    
    for en_key, vn_loc in service.STANDARD_LOCATIONS.items():
        # Categorize
        if en_key in ['foundation', 'pile', 'column', 'beam', 'slab', 'wall', 'roof']:
            cat = 'structural'
            sec = ['SEC-02']
        elif en_key in ['underground', 'in_wall', 'in_slab', 'above_ceiling', 'vertical_shaft', 'exposed']:
            cat = 'mep_environment'
            sec = ['SEC-04']
        else:
            cat = 'zone'
            sec = ['SEC-03']
        
        locations.append({
            'en_key': en_key,
            'vn_location': vn_loc,
            'category': cat,
            'sec_codes': sec
        })
    
    return locations


@router.get("/templates/{sec_code}")
def get_naming_template(
    sec_code: str,
    db: Session = Depends(get_db)
):
    """
    Lấy naming template cho SEC code
    
    Example: GET /api/v1/naming/templates/SEC-04
    """
    service = EnhancedNamingService(db)
    
    template = service.TEMPLATES.get(sec_code)
    
    if not template:
        raise HTTPException(status_code=404, detail=f"Template not found for {sec_code}")
    
    return {
        'sec_code': sec_code,
        'template': template
    }


@router.get("/examples")
def get_naming_examples(
    sec_code: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Lấy examples tên tự nhiên chuẩn
    
    Example: GET /api/v1/naming/examples?sec_code=SEC-04&limit=5
    """
    examples = [
        {
            'sec_code': 'SEC-01-01',
            'natural_name': 'Đào đất hố móng - Máy đào 0.8m3 - Đất cấp 3',
            'parts': ['Đào đất hố móng', 'Máy đào 0.8m3', 'Đất cấp 3'],
            'has_verb': True,
            'has_specs': True
        },
        {
            'sec_code': 'SEC-02',
            'natural_name': 'Đổ bê tông dầm sàn - M350 - Đá 1x2',
            'parts': ['Đổ bê tông dầm sàn', 'M350', 'Đá 1x2'],
            'has_verb': True,
            'has_specs': True
        },
        {
            'sec_code': 'SEC-03',
            'natural_name': 'Xây tường ngoài - Gạch đặc - Dày 220',
            'parts': ['Xây tường ngoài', 'Gạch đặc', 'Dày 220'],
            'has_verb': True,
            'has_specs': True
        },
        {
            'sec_code': 'SEC-04',
            'natural_name': 'Lắp ống cấp nước trục đứng - PPR - D63 - PN16',
            'parts': ['Lắp ống cấp nước trục đứng', 'PPR', 'D63', 'PN16'],
            'has_verb': True,
            'has_specs': True
        },
        {
            'sec_code': 'SEC-04',
            'natural_name': 'Rải dây cáp điện ngầm - Cu/XLPE/PVC - 4x50',
            'parts': ['Rải dây cáp điện ngầm', 'Cu/XLPE/PVC', '4x50'],
            'has_verb': True,
            'has_specs': True
        },
        {
            'sec_code': 'SEC-04',
            'natural_name': 'Lắp ống gió cấp - Tôn tráng kẽm - 1200x400 - 0.75mm',
            'parts': ['Lắp ống gió cấp', 'Tôn tráng kẽm', '1200x400', '0.75mm'],
            'has_verb': True,
            'has_specs': True
        }
    ]
    
    # Filter by sec_code if provided
    if sec_code:
        examples = [e for e in examples if e['sec_code'] == sec_code]
    
    return {
        'total': len(examples),
        'examples': examples[:limit]
    }
