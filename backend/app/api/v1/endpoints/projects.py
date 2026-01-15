from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.project import Project, ProjectStatus, ProjectType
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse
from app.services.project_service import ProjectService

router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new project
    """
    service = ProjectService(db)
    
    # Check if project code already exists
    if service.get_by_code(project_in.project_code):
        raise HTTPException(status_code=400, detail="Project code already exists")
    
    project = service.create(project_in)
    return project


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    project_type: Optional[ProjectType] = None,
    status: Optional[ProjectStatus] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all projects with filters and pagination
    """
    service = ProjectService(db)
    projects, total = service.get_list(
        skip=skip,
        limit=limit,
        project_type=project_type,
        status=status,
        search=search
    )
    
    return {
        "items": projects,
        "total": total,
        "page": skip // limit + 1,
        "page_size": limit,
        "total_pages": (total + limit - 1) // limit
    }


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get project by ID
    """
    service = ProjectService(db)
    project = service.get_by_id(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update project
    """
    service = ProjectService(db)
    project = service.update(project_id, project_in)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete project
    """
    service = ProjectService(db)
    success = service.delete(project_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return None
