"""
Pydantic schemas for Pending Items API
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class PendingItemBase(BaseModel):
    """Base schema for pending item."""
    description: str
    description_normalized: Optional[str] = None
    sec_code: Optional[str] = None
    unit_standard: Optional[str] = None


class PendingItemUpdate(BaseModel):
    """Schema for updating a pending item before approval."""
    description: Optional[str] = None
    description_normalized: Optional[str] = None
    sec_code: Optional[str] = None
    unit_standard: Optional[str] = None


class PendingItemResponse(BaseModel):
    """Schema for pending item response."""
    pending_id: int
    description: str
    description_normalized: Optional[str] = None
    sec_code: Optional[str] = None
    unit_standard: Optional[str] = None
    source_file_id: Optional[int] = None
    original_description: Optional[str] = None
    quality_score: Optional[float] = None
    quality_reasons: Optional[str] = None
    quality_indicators: Optional[str] = None
    status: str
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    master_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApprovalRequest(BaseModel):
    """Schema for approve/reject request."""
    reviewer_id: int
    notes: Optional[str] = None


class BulkApprovalRequest(BaseModel):
    """Schema for bulk approval."""
    pending_ids: List[int]
    reviewer_id: int


class PendingItemStats(BaseModel):
    """Schema for pending items statistics."""
    pending: int
    approved: int
    rejected: int
    total: int


class ApprovalResponse(BaseModel):
    """Schema for approval response."""
    status: str
    master_id: Optional[int] = None
    work_code: Optional[str] = None


class BulkApprovalResponse(BaseModel):
    """Schema for bulk approval response."""
    approved: int
    total: int
