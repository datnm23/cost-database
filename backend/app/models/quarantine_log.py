"""
Quarantine Log Model

Log of rejected items for analysis.
Items with quality score < 50 are logged here for analysis and potential pattern improvement.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Index
from sqlalchemy.sql import func
from app.core.database import Base


class QuarantineLog(Base):
    """
    Log table for rejected items.
    Used for analysis and improving validation patterns.
    """
    __tablename__ = "quarantine_logs"

    # Primary key
    log_id = Column(Integer, primary_key=True, autoincrement=True)

    # Original data
    description = Column(Text)
    description_normalized = Column(String(500))
    source_file_id = Column(Integer, ForeignKey('boq_files.file_id'))

    # Rejection info
    rejection_reason = Column(String(500))  # Primary reason for rejection
    quality_score = Column(Float)
    matched_forbidden_pattern = Column(String(100))  # If rejected due to forbidden pattern
    quality_indicators = Column(Text)  # JSON dict of indicator results

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_quarantine_file', 'source_file_id'),
        Index('idx_quarantine_created', 'created_at'),
        Index('idx_quarantine_reason', 'rejection_reason'),
    )

    def __repr__(self):
        return f"<QuarantineLog(id={self.log_id}, reason={self.rejection_reason[:50] if self.rejection_reason else 'N/A'})>"
