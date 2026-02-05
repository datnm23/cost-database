"""
Master Synonym Model

Stores synonyms/aliases for master work items to enable matching variations.
Examples:
- "BT lót móng" = "Bê tông lót móng" = "Concrete lót móng"
- "Cọc khoan nhồi" = "Bored pile"
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class MasterSynonym(Base):
    """
    Synonym table for master work items.
    Enables matching variations and alternative names.
    """
    __tablename__ = 'master_synonyms'

    synonym_id = Column(Integer, primary_key=True, autoincrement=True)
    master_id = Column(
        Integer,
        ForeignKey('master_work_items.master_id', ondelete='CASCADE'),
        nullable=False
    )
    synonym_text = Column(String(500), nullable=False)
    synonym_normalized = Column(String(500), index=True)
    synonym_type = Column(
        Enum('alias', 'abbreviation', 'regional', 'english', name='synonym_type_enum'),
        default='alias'
    )
    is_active = Column(Boolean, default=True)
    added_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationship
    master_item = relationship("MasterWorkItem", back_populates="synonyms")

    __table_args__ = (
        Index('idx_synonym_master', 'master_id'),
        Index('idx_synonym_active', 'is_active'),
    )

    def __repr__(self):
        return f"<MasterSynonym(id={self.synonym_id}, text='{self.synonym_text[:30]}...', master_id={self.master_id})>"
