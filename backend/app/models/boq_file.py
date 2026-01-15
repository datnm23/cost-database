from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL, Enum, CHAR, func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class FileStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"


class BOQFile(Base):
    __tablename__ = "boq_files"
    
    file_id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_hash = Column(CHAR(64), unique=True, index=True)
    file_path = Column(String(500))
    total_rows = Column(Integer, default=0)
    total_amount = Column(DECIMAL(18, 2), default=0)
    status = Column(Enum(FileStatus), default=FileStatus.DRAFT)
    uploaded_at = Column(DateTime, server_default=func.now())
    uploaded_by = Column(Integer, ForeignKey("users.user_id"))
    
    # Relationships
    project = relationship("Project", back_populates="boq_files")
    line_items = relationship("LineItem", back_populates="boq_file", cascade="all, delete-orphan")
    uploader = relationship("User")
    
    def __repr__(self):
        return f"<BOQFile {self.file_id}: {self.file_name}>"
