"""
Project Work Item Model (Zone 1 - Project Lake)

Stores work items extracted from project BOQ files before they are resolved
to master database items. Items that don't pass the quality gate (RED/YELLOW)
are stored here for human review and resolution.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Index, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ProjectWorkItem(Base):
    """
    Zone 1 table: Project-level work items awaiting resolution to Master DB.

    Traffic gate status:
    - GREEN (score >= 90): Auto-resolved to master
    - YELLOW (score 60-89): Needs review
    - RED (score < 60): Low quality, needs significant review

    Resolution status:
    - UNRESOLVED: Not yet matched to a master item
    - MATCHED: AI suggested a match, pending confirmation
    - APPROVED: Human approved the match/new master item
    - MERGED: Merged with existing master item
    """
    __tablename__ = "project_work_items"

    # Primary key
    pwi_id = Column(Integer, primary_key=True, autoincrement=True)

    # Source tracking
    project_id = Column(Integer, ForeignKey('projects.project_id'), nullable=False, index=True)
    file_id = Column(Integer, ForeignKey('boq_files.file_id'), nullable=False, index=True)
    line_item_id = Column(Integer, ForeignKey('line_items.line_item_id'), nullable=True)

    # Description
    original_description = Column(Text, nullable=False)
    normalized_description = Column(Text)

    # Temporary code (unique within project)
    temp_code = Column(String(50), unique=True, nullable=False, index=True,
                       comment='Format: PRJ.{project_id}-TEMP-{seq:03d}')

    # Resolution to master
    master_work_item_id = Column(Integer, ForeignKey('master_work_items.master_id'), nullable=True)

    # WBS context (JSON text)
    wbs_context = Column(Text, comment='JSON: parent_title, section_path, neighbors, section_type')
    wbs_level = Column(Integer, default=0)

    # Quality assessment
    quality_score = Column(Float, default=0.0)
    gate_status = Column(
        Enum('GREEN', 'YELLOW', 'RED', name='gate_status_enum'),
        nullable=False,
        default='RED',
        index=True,
    )

    # Unit and pricing
    unit = Column(String(20))
    quantity = Column(Float)
    unit_price = Column(Float)
    amount = Column(Float)

    # Resolution tracking
    resolution_status = Column(
        Enum('UNRESOLVED', 'MATCHED', 'APPROVED', 'MERGED', name='resolution_status_enum'),
        nullable=False,
        default='UNRESOLVED',
        index=True,
    )
    resolved_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # AI structured output cache (JSON text)
    ai_structured_output = Column(Text, comment='Cached LLM structured output JSON')

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_pwi_project', 'project_id'),
        Index('idx_pwi_file', 'file_id'),
        Index('idx_pwi_gate_status', 'gate_status'),
        Index('idx_pwi_resolution', 'resolution_status'),
        Index('idx_pwi_master', 'master_work_item_id'),
        Index('idx_pwi_temp_code', 'temp_code'),
    )

    def __repr__(self):
        return (
            f"<ProjectWorkItem(pwi_id={self.pwi_id}, "
            f"temp_code={self.temp_code}, "
            f"gate={self.gate_status}, "
            f"resolution={self.resolution_status})>"
        )
