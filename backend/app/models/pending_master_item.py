"""
Pending Master Item Model

Staging area for items that need human review before being added to Master DB.
Items with quality score 50-74 are placed here for review.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class PendingMasterItem(Base):
    """
    Staging table for items pending human review.
    These are items that passed minimum quality but need verification.
    """
    __tablename__ = "pending_master_items"

    # Primary key
    pending_id = Column(Integer, primary_key=True, autoincrement=True)

    # Item data (same structure as MasterWorkItem)
    description = Column(Text, nullable=False)
    description_normalized = Column(String(500))
    sec_code = Column(String(20))
    unit_standard = Column(String(20))

    # Source tracking
    source_file_id = Column(Integer, ForeignKey('boq_files.file_id'))
    original_description = Column(Text)

    # Gatekeeper validation results
    quality_score = Column(Float)
    quality_reasons = Column(Text)  # JSON array of reasons
    quality_indicators = Column(Text)  # JSON dict of indicator results

    # Review status
    status = Column(String(20), default='PENDING', index=True)
    # Status values: PENDING, APPROVED, REJECTED

    # Review info
    reviewed_by = Column(Integer, ForeignKey('users.user_id'))
    reviewed_at = Column(DateTime)
    review_notes = Column(Text)

    # If approved, link to created master item
    master_id = Column(Integer, ForeignKey('master_work_items.master_id'))

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_pending_status', 'status'),
        Index('idx_pending_score', 'quality_score'),
        Index('idx_pending_created', 'created_at'),
    )

    def __repr__(self):
        return f"<PendingMasterItem(id={self.pending_id}, score={self.quality_score}, status={self.status})>"
