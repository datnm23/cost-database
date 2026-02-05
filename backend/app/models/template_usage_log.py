"""
Template Usage Log Model

Tracks usage of column mapping templates for analytics and success rate calculation.
"""
import enum
from sqlalchemy import Column, Integer, Boolean, ForeignKey, DateTime, Enum, DECIMAL, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class MatchType(str, enum.Enum):
    exact = "exact"
    fuzzy = "fuzzy"
    manual = "manual"


class UsageAction(str, enum.Enum):
    auto_applied = "auto_applied"
    user_selected = "user_selected"
    user_modified = "user_modified"


class TemplateUsageLog(Base):
    """
    Usage log for tracking template applications.
    Used for analytics and improving match success rates.
    """
    __tablename__ = 'template_usage_logs'

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(
        Integer,
        ForeignKey('column_mapping_templates.template_id', ondelete='CASCADE'),
        nullable=False
    )
    file_id = Column(
        Integer,
        ForeignKey('boq_files.file_id', ondelete='SET NULL'),
        nullable=True
    )
    match_score = Column(DECIMAL(5, 2), nullable=True)
    match_type = Column(Enum(MatchType), nullable=False)
    was_successful = Column(Boolean, default=True)
    columns_mapped = Column(Integer, nullable=True)
    columns_total = Column(Integer, nullable=True)
    user_id = Column(
        Integer,
        ForeignKey('users.user_id', ondelete='SET NULL'),
        nullable=True
    )
    action = Column(Enum(UsageAction), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    template = relationship("ColumnMappingTemplate", back_populates="usage_logs")
    file = relationship("BOQFile")
    user = relationship("User")

    __table_args__ = (
        Index('idx_template', 'template_id'),
        Index('idx_file', 'file_id'),
        Index('idx_user', 'user_id'),
    )

    def __repr__(self):
        return f"<TemplateUsageLog(id={self.log_id}, template_id={self.template_id}, action='{self.action}')>"
