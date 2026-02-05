"""
Column Mapping Template Model

Stores reusable column mapping configurations with fingerprints for automatic matching.
"""
import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum, Text, DECIMAL, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class TemplateVisibility(str, enum.Enum):
    private = "private"
    team = "team"
    public = "public"


class ColumnMappingTemplate(Base):
    """
    Template table for storing column mapping configurations.
    Enables reuse of mappings across similar BOQ files.
    """
    __tablename__ = 'column_mapping_templates'

    template_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    column_mapping = Column(JSON, nullable=False)  # {"original_col": "standard_col"}
    header_row_hint = Column(Integer, default=0)
    sheet_name_pattern = Column(String(100), nullable=True)
    fingerprint = Column(String(64), nullable=False, index=True)  # SHA256 hash
    fingerprint_components = Column(JSON, nullable=True)  # Detailed parts for fuzzy matching
    use_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    match_success_rate = Column(DECIMAL(5, 2), default=100.00)
    created_by = Column(
        Integer,
        ForeignKey('users.user_id', ondelete='SET NULL'),
        nullable=True
    )
    visibility = Column(
        Enum(TemplateVisibility),
        default=TemplateVisibility.private
    )
    is_system = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    usage_logs = relationship("TemplateUsageLog", back_populates="template", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_visibility', 'visibility'),
        Index('idx_active', 'is_active'),
        Index('idx_name_owner', 'name', 'created_by', unique=True),
    )

    def __repr__(self):
        return f"<ColumnMappingTemplate(id={self.template_id}, name='{self.name}', fingerprint='{self.fingerprint[:8]}...')>"
