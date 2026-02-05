"""
Pydantic schemas for Quarantine API
"""
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime


class QuarantineLogResponse(BaseModel):
    """Schema for quarantine log response."""
    log_id: int
    description: Optional[str] = None
    description_normalized: Optional[str] = None
    source_file_id: Optional[int] = None
    rejection_reason: Optional[str] = None
    quality_score: Optional[float] = None
    matched_forbidden_pattern: Optional[str] = None
    quality_indicators: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class QuarantineStats(BaseModel):
    """Schema for quarantine statistics."""
    by_reason: Dict[str, int]
    total: int


class RetryValidationResponse(BaseModel):
    """Schema for retry validation response."""
    status: str
    score: Optional[float] = None
    reasons: Optional[str] = None
