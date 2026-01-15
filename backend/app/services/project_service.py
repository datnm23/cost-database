from sqlalchemy.orm import Session
from typing import Optional, Tuple, List

from app.models.project import Project, ProjectType, ProjectStatus
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """Service layer for project operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, project_in: ProjectCreate) -> Project:
        """Create a new project"""
        project = Project(**project_in.model_dump())
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project
    
    def get_by_id(self, project_id: int) -> Optional[Project]:
        """Get project by ID"""
        return self.db.query(Project).filter(Project.project_id == project_id).first()
    
    def get_by_code(self, project_code: str) -> Optional[Project]:
        """Get project by code"""
        return self.db.query(Project).filter(Project.project_code == project_code).first()
    
    def get_list(
        self,
        skip: int = 0,
        limit: int = 20,
        project_type: Optional[ProjectType] = None,
        status: Optional[ProjectStatus] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Project], int]:
        """Get list of projects with filters"""
        query = self.db.query(Project)
        
        # Apply filters
        if project_type:
            query = query.filter(Project.project_type == project_type)
        if status:
            query = query.filter(Project.status == status)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Project.project_name.like(search_pattern)) |
                (Project.project_code.like(search_pattern)) |
                (Project.client_name.like(search_pattern))
            )
        
        total = query.count()
        projects = query.order_by(Project.created_at.desc()).offset(skip).limit(limit).all()
        
        return projects, total
    
    def update(self, project_id: int, project_in: ProjectUpdate) -> Optional[Project]:
        """Update project"""
        project = self.get_by_id(project_id)
        if not project:
            return None
        
        update_data = project_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)
        
        self.db.commit()
        self.db.refresh(project)
        return project
    
    def delete(self, project_id: int) -> bool:
        """Delete project"""
        project = self.get_by_id(project_id)
        if not project:
            return False
        
        self.db.delete(project)
        self.db.commit()
        return True
