"""
Pydantic schemas for Synonym API
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SynonymBase(BaseModel):
    """Base schema for synonym."""
    synonym_text: str
    synonym_type: str = 'alias'


class SynonymCreate(SynonymBase):
    """Schema for creating a synonym."""
    pass


class SynonymResponse(BaseModel):
    """Schema for synonym response."""
    synonym_id: int
    master_id: int
    synonym_text: str
    synonym_normalized: Optional[str] = None
    synonym_type: str
    is_active: bool
    added_by: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
