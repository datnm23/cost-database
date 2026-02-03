"""
BOQ Version Model
Tracks different versions of BOQ files for comparison
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class BOQVersion(Base):
    """
    Tracks BOQ file versions for a project
    Enables version comparison to see changes over time
    """
    __tablename__ = "boq_versions"

    version_id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    version_name = Column(String(100))
    file_id = Column(Integer, ForeignKey("boq_files.file_id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    notes = Column(Text)

    # Relationships
    project = relationship("Project", backref="boq_versions")
    boq_file = relationship("BOQFile", backref="versions")

    # Unique constraint: one version number per project
    __table_args__ = (
        Index('uk_project_version', 'project_id', 'version_number', unique=True),
    )

    def __repr__(self):
        return f"<BOQVersion {self.version_id}: project={self.project_id}, v{self.version_number}>"
