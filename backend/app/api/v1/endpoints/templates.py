"""
API endpoints for Column Mapping Templates

Provides CRUD operations, fingerprint generation, template matching, and usage tracking.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.services.template_service import TemplateService
from app.services.fingerprint_generator import get_fingerprint_generator
from app.models.column_mapping_template import TemplateVisibility
from app.models.template_usage_log import MatchType, UsageAction
from app.schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateListResponse,
    FingerprintRequest,
    FingerprintResponse,
    FingerprintComponents,
    TemplateMatchRequest,
    TemplateMatchResponse,
    TemplateUsageCreate,
    TemplateUsageResponse,
    TemplateStatistics,
    TemplateVisibility as SchemaVisibility,
)

router = APIRouter()


@router.post("/", response_model=TemplateResponse, status_code=201)
async def create_template(
    data: TemplateCreate,
    db: Session = Depends(get_db),
    user_id: Optional[int] = None  # Would come from auth in production
):
    """
    Create a new column mapping template.

    The fingerprint is automatically generated from the column_mapping keys.
    """
    service = TemplateService(db)

    try:
        template = service.create_template(
            name=data.name,
            description=data.description,
            column_mapping=data.column_mapping,
            header_row_hint=data.header_row_hint,
            sheet_name_pattern=data.sheet_name_pattern,
            visibility=TemplateVisibility(data.visibility.value),
            created_by=user_id
        )
        return template
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=TemplateListResponse)
async def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    visibility: Optional[SchemaVisibility] = None,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    user_id: Optional[int] = None
):
    """
    List column mapping templates with pagination.

    By default, returns templates visible to the user (own + team + public).
    """
    service = TemplateService(db)

    visibility_model = TemplateVisibility(visibility.value) if visibility else None

    templates, total = service.get_templates(
        user_id=user_id,
        visibility=visibility_model,
        include_inactive=include_inactive,
        skip=skip,
        limit=limit
    )

    return TemplateListResponse(
        templates=templates,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """Get a template by ID."""
    service = TemplateService(db)
    template = service.get_template(template_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return template


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    data: TemplateUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing template.

    If column_mapping is updated, the fingerprint will be regenerated.
    """
    service = TemplateService(db)

    update_data = data.model_dump(exclude_unset=True)

    # Convert visibility enum if present
    if 'visibility' in update_data and update_data['visibility']:
        update_data['visibility'] = TemplateVisibility(update_data['visibility'].value)

    template = service.update_template(template_id, **update_data)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return template


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    hard: bool = False,
    db: Session = Depends(get_db)
):
    """
    Delete a template.

    By default, performs soft delete (marks as inactive).
    Use hard=true for permanent deletion.
    """
    service = TemplateService(db)

    success = service.delete_template(template_id, soft=not hard)

    if not success:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "status": "success",
        "message": f"Template {'permanently deleted' if hard else 'deactivated'}"
    }


@router.post("/fingerprint", response_model=FingerprintResponse)
async def generate_fingerprint(data: FingerprintRequest):
    """
    Generate a fingerprint from column names.

    This can be used to preview the fingerprint before creating a template,
    or to check if a similar template already exists.
    """
    generator = get_fingerprint_generator()

    result = generator.generate(
        column_names=data.column_names,
        sample_data=data.sample_data
    )

    return FingerprintResponse(
        fingerprint=result.fingerprint,
        components=FingerprintComponents(
            column_count=result.components.column_count,
            column_keywords=result.components.column_keywords,
            column_order_hash=result.components.column_order_hash,
            data_type_signature=result.components.data_type_signature
        )
    )


@router.post("/match", response_model=TemplateMatchResponse)
async def find_matching_templates(
    data: TemplateMatchRequest,
    db: Session = Depends(get_db),
    user_id: Optional[int] = None
):
    """
    Find templates that match the given column structure.

    Returns the best match (if above similarity threshold) and alternatives.
    Uses exact fingerprint matching first, then fuzzy matching.
    """
    service = TemplateService(db)

    best_match, alternatives, input_fingerprint = service.find_matching_templates(
        column_names=data.column_names,
        sheet_name=data.sheet_name,
        min_similarity=data.min_similarity,
        limit=data.limit,
        user_id=user_id
    )

    if best_match:
        message = f"Found matching template with {best_match.similarity_score}% similarity"
    else:
        message = f"No templates found matching above {data.min_similarity}% threshold"

    return TemplateMatchResponse(
        best_match=best_match,
        alternatives=alternatives,
        input_fingerprint=input_fingerprint,
        message=message
    )


@router.post("/usage", response_model=TemplateUsageResponse, status_code=201)
async def log_template_usage(
    data: TemplateUsageCreate,
    db: Session = Depends(get_db),
    user_id: Optional[int] = None
):
    """
    Log template usage for analytics and success rate tracking.

    This should be called when a template is applied to a file.
    """
    service = TemplateService(db)

    # Verify template exists
    template = service.get_template(data.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    usage_log = service.log_usage(
        template_id=data.template_id,
        file_id=data.file_id,
        match_score=data.match_score,
        match_type=MatchType(data.match_type.value),
        was_successful=data.was_successful,
        columns_mapped=data.columns_mapped,
        columns_total=data.columns_total,
        action=UsageAction(data.action.value),
        user_id=user_id
    )

    return usage_log


@router.get("/statistics/", response_model=TemplateStatistics)
async def get_template_statistics(
    db: Session = Depends(get_db),
    user_id: Optional[int] = None
):
    """
    Get template usage statistics.

    Includes counts, success rates, most used templates, and recent usage.
    """
    service = TemplateService(db)
    stats = service.get_statistics(user_id=user_id)

    # Convert recent_uses to response schema
    recent_uses = [
        TemplateUsageResponse(
            log_id=log.log_id,
            template_id=log.template_id,
            file_id=log.file_id,
            match_score=float(log.match_score) if log.match_score else None,
            match_type=log.match_type,
            was_successful=log.was_successful,
            columns_mapped=log.columns_mapped,
            columns_total=log.columns_total,
            user_id=log.user_id,
            action=log.action,
            created_at=log.created_at
        )
        for log in stats.get('recent_uses', [])
    ]

    return TemplateStatistics(
        total_templates=stats['total_templates'],
        active_templates=stats['active_templates'],
        system_templates=stats['system_templates'],
        user_templates=stats['user_templates'],
        total_uses=stats['total_uses'],
        successful_uses=stats['successful_uses'],
        average_success_rate=stats['average_success_rate'],
        most_used_templates=stats['most_used_templates'],
        recent_uses=recent_uses
    )
