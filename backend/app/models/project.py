from sqlalchemy import Column, Integer, String, DateTime, Enum, DECIMAL, Text, func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class ProjectType(str, enum.Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    INFRASTRUCTURE = "infrastructure"


class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Project(Base):
    __tablename__ = "projects"
    
    project_id = Column(Integer, primary_key=True, index=True)
    project_code = Column(String(50), unique=True, nullable=False, index=True)
    project_name = Column(String(255), nullable=False)
    project_type = Column(Enum(ProjectType), nullable=False)
    location = Column(String(255))
    client_name = Column(String(255))
    contract_value = Column(DECIMAL(18, 2))
    start_date = Column(DateTime)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.ACTIVE)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    boq_files = relationship("BOQFile", back_populates="project", cascade="all, delete-orphan")
    line_items = relationship("LineItem", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project {self.project_code}: {self.project_name}>"
