"""
Pydantic schemas for AI Training Logs API
"""
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime


class AITrainingLogResponse(BaseModel):
    """Schema for AI training log response."""
    log_id: int
    original_description: str
    normalized_description: Optional[str] = None
    ai_suggestion: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_structured: Optional[str] = None
    human_choice: Optional[str] = None
    human_master_id: Optional[int] = None
    action_type: str
    edit_distance: Optional[int] = None
    project_id: Optional[int] = None
    source_pwi_id: Optional[int] = None
    source_pending_id: Optional[int] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AITrainingLogStats(BaseModel):
    """Schema for training log statistics."""
    total: int
    by_action: Dict[str, int]
    avg_confidence: Optional[float] = None
    avg_edit_distance: Optional[float] = None
