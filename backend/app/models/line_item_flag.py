"""
Line Item Flag Model
Quick notes and flags for line items during QS review
"""
from sqlalchemy import Column, BigInteger, Integer, String, ForeignKey, DateTime, Text, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class FlagType(str, enum.Enum):
    price_warning = "price_warning"
    needs_verify = "needs_verify"
    confirmed = "confirmed"
    important = "important"
    question = "question"


class LineItemFlag(Base):
    """
    Quick notes/flags for line items during review
    Enables QS to mark items for follow-up
    """
    __tablename__ = "line_item_flags"

    flag_id = Column(BigInteger, primary_key=True, autoincrement=True)
    line_item_id = Column(BigInteger, ForeignKey("line_items.line_item_id", ondelete="CASCADE"), nullable=False, index=True)
    flag_type = Column(Enum(FlagType), nullable=False)
    note = Column(Text)
    created_by = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"))
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    line_item = relationship("LineItem", backref="flags")
    user = relationship("User", backref="line_item_flags")

    # Indexes
    __table_args__ = (
        Index('idx_flag_type', 'flag_type'),
    )

    def __repr__(self):
        return f"<LineItemFlag {self.flag_id}: item={self.line_item_id}, type={self.flag_type}>"
