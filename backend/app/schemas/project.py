from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal

from app.models.project import ProjectType, ProjectStatus


class ProjectBase(BaseModel):
    project_code: str = Field(..., min_length=1, max_length=50)
    project_name: str = Field(..., min_length=1, max_length=255)
    project_type: ProjectType
    location: Optional[str] = None
    client_name: Optional[str] = None
    contract_value: Optional[Decimal] = None
    start_date: Optional[datetime] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    project_type: Optional[ProjectType] = None
    location: Optional[str] = None
    client_name: Optional[str] = None
    contract_value: Optional[Decimal] = None
    start_date: Optional[datetime] = None
    status: Optional[ProjectStatus] = None


class ProjectResponse(ProjectBase):
    project_id: int
    status: ProjectStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
