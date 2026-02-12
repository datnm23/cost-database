"""
AI Training Log Model (Zone 3 - Knowledge Base)

Records human decisions on AI suggestions to build a training dataset
for continuous improvement of the matching and normalization pipeline.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Index, Enum
from sqlalchemy.sql import func
from app.core.database import Base


class AITrainingLog(Base):
    """
    Zone 3 table: Logs human corrections to AI suggestions.

    action_type:
    - ACCEPT: Human accepted AI suggestion as-is
    - EDIT: Human edited AI suggestion before accepting
    - REJECT: Human rejected AI suggestion entirely
    - REMAP: Human remapped a project work item to a different master item
    """
    __tablename__ = "ai_training_logs"

    # Primary key
    log_id = Column(Integer, primary_key=True, autoincrement=True)

    # Description pair
    original_description = Column(Text, nullable=False)
    normalized_description = Column(Text)

    # AI suggestion
    ai_suggestion = Column(Text)
    ai_confidence = Column(Float)
    ai_structured = Column(Text, comment='JSON: AI structured output')

    # Human decision
    human_choice = Column(Text)
    human_master_id = Column(Integer, ForeignKey('master_work_items.master_id'), nullable=True)
    action_type = Column(
        Enum('ACCEPT', 'EDIT', 'REJECT', 'REMAP', name='training_action_enum'),
        nullable=False,
        index=True,
    )
    edit_distance = Column(Integer, comment='Levenshtein distance between AI suggestion and human choice')

    # Source tracking
    project_id = Column(Integer, ForeignKey('projects.project_id'), nullable=True)
    source_pwi_id = Column(Integer, ForeignKey('project_work_items.pwi_id'), nullable=True)
    source_pending_id = Column(Integer, ForeignKey('pending_master_items.pending_id'), nullable=True)

    # Reviewer
    reviewed_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    reviewed_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_training_action', 'action_type'),
        Index('idx_training_project', 'project_id'),
        Index('idx_training_created', 'created_at'),
        Index('idx_training_master', 'human_master_id'),
    )

    def __repr__(self):
        return (
            f"<AITrainingLog(log_id={self.log_id}, "
            f"action={self.action_type}, "
            f"confidence={self.ai_confidence})>"
        )
