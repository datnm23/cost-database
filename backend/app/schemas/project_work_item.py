"""
Pydantic schemas for Project Work Items API
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ProjectWorkItemBase(BaseModel):
    """Base schema for project work item."""
    original_description: str
    normalized_description: Optional[str] = None
    unit: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    amount: Optional[float] = None


class ProjectWorkItemResponse(BaseModel):
    """Schema for project work item response."""
    pwi_id: int
    project_id: int
    file_id: int
    line_item_id: Optional[int] = None
    original_description: str
    normalized_description: Optional[str] = None
    temp_code: str
    master_work_item_id: Optional[int] = None
    wbs_context: Optional[str] = None
    wbs_level: Optional[int] = None
    quality_score: Optional[float] = None
    gate_status: str
    unit: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    amount: Optional[float] = None
    resolution_status: str
    resolved_by: Optional[int] = None
    resolved_at: Optional[datetime] = None
    ai_structured_output: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectWorkItemResolveRequest(BaseModel):
    """Schema for resolving a project work item."""
    master_work_item_id: int
    reviewer_id: int
    edited_description: Optional[str] = None
    notes: Optional[str] = None


class ProjectWorkItemBulkResolveRequest(BaseModel):
    """Schema for bulk resolving project work items."""
    resolutions: List[Dict[str, Any]]
    reviewer_id: int


class ProjectWorkItemStats(BaseModel):
    """Schema for project work items statistics."""
    total: int
    unresolved: int
    matched: int
    approved: int
    merged: int
    by_gate_status: Dict[str, int]


class ProjectWorkItemResolveResponse(BaseModel):
    """Schema for resolve response."""
    status: str
    pwi_id: int
    master_work_item_id: Optional[int] = None
    synonym_created: bool = False
