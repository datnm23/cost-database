"""
Pydantic schemas for Column Mapping Template API
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TemplateVisibility(str, Enum):
    private = "private"
    team = "team"
    public = "public"


class MatchType(str, Enum):
    exact = "exact"
    fuzzy = "fuzzy"
    manual = "manual"


class UsageAction(str, Enum):
    auto_applied = "auto_applied"
    user_selected = "user_selected"
    user_modified = "user_modified"


# Template CRUD schemas
class TemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    column_mapping: Dict[str, str]
    header_row_hint: int = 0
    sheet_name_pattern: Optional[str] = None
    visibility: TemplateVisibility = TemplateVisibility.private


class TemplateCreate(TemplateBase):
    """Schema for creating a new template."""
    pass


class TemplateUpdate(BaseModel):
    """Schema for updating an existing template."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    column_mapping: Optional[Dict[str, str]] = None
    header_row_hint: Optional[int] = None
    sheet_name_pattern: Optional[str] = None
    visibility: Optional[TemplateVisibility] = None


class TemplateResponse(BaseModel):
    """Schema for template response."""
    template_id: int
    name: str
    description: Optional[str] = None
    column_mapping: Dict[str, str]
    header_row_hint: int
    sheet_name_pattern: Optional[str] = None
    fingerprint: str
    fingerprint_components: Optional[Dict[str, Any]] = None
    use_count: int
    last_used_at: Optional[datetime] = None
    match_success_rate: float
    created_by: Optional[int] = None
    visibility: TemplateVisibility
    is_system: bool
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    """Schema for paginated template list."""
    templates: List[TemplateResponse]
    total: int
    skip: int
    limit: int


# Fingerprint schemas
class FingerprintComponents(BaseModel):
    """Detailed fingerprint components for fuzzy matching."""
    column_count: int
    column_keywords: List[str]  # Sorted, normalized keywords
    column_order_hash: str  # MD5 of column order
    data_type_signature: Optional[str] = None  # e.g., "TTNNN" format


class FingerprintRequest(BaseModel):
    """Request schema for generating a fingerprint."""
    column_names: List[str]
    sample_data: Optional[List[List[Any]]] = None  # Optional sample rows for type inference


class FingerprintResponse(BaseModel):
    """Response schema for fingerprint generation."""
    fingerprint: str
    components: FingerprintComponents


# Template matching schemas
class TemplateMatchRequest(BaseModel):
    """Request schema for finding matching templates."""
    column_names: List[str]
    sheet_name: Optional[str] = None
    min_similarity: float = Field(75.0, ge=0, le=100)
    limit: int = Field(5, ge=1, le=20)


class TemplateMatchResult(BaseModel):
    """Single template match result."""
    template_id: int
    template_name: str
    similarity_score: float  # 0-100
    match_type: MatchType
    column_mapping: Dict[str, str]
    matched_columns: int
    total_columns: int
    fingerprint: str


class TemplateMatchResponse(BaseModel):
    """Response schema for template matching."""
    best_match: Optional[TemplateMatchResult] = None
    alternatives: List[TemplateMatchResult] = []
    input_fingerprint: str
    message: str


# Usage tracking schemas
class TemplateUsageCreate(BaseModel):
    """Schema for logging template usage."""
    template_id: int
    file_id: Optional[int] = None
    match_score: Optional[float] = None
    match_type: MatchType
    was_successful: bool = True
    columns_mapped: Optional[int] = None
    columns_total: Optional[int] = None
    action: UsageAction


class TemplateUsageResponse(BaseModel):
    """Schema for usage log response."""
    log_id: int
    template_id: int
    file_id: Optional[int] = None
    match_score: Optional[float] = None
    match_type: MatchType
    was_successful: bool
    columns_mapped: Optional[int] = None
    columns_total: Optional[int] = None
    user_id: Optional[int] = None
    action: UsageAction
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TemplateStatistics(BaseModel):
    """Template usage statistics."""
    total_templates: int
    active_templates: int
    system_templates: int
    user_templates: int
    total_uses: int
    successful_uses: int
    average_success_rate: float
    most_used_templates: List[Dict[str, Any]]
    recent_uses: List[TemplateUsageResponse]
