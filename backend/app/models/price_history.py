"""
Price History Model
Tracks historical price data for master work items from different projects
"""
from sqlalchemy import Column, BigInteger, Integer, String, ForeignKey, DECIMAL, DateTime, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class ProjectTypeEnum(str, enum.Enum):
    residential = "residential"
    commercial = "commercial"
    industrial = "industrial"
    infrastructure = "infrastructure"


class PriceHistory(Base):
    """
    Stores individual price records from different projects/files
    Used for price drill-down and transparency
    """
    __tablename__ = "price_history"

    price_id = Column(BigInteger, primary_key=True, autoincrement=True)
    master_item_id = Column(Integer, ForeignKey("master_work_items.master_id", ondelete="CASCADE"), nullable=False, index=True)
    file_id = Column(Integer, ForeignKey("boq_files.file_id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True)
    unit_price = Column(DECIMAL(18, 2), nullable=False)
    quantity = Column(DECIMAL(18, 4))
    recorded_at = Column(DateTime, server_default=func.now())
    region = Column(String(100))
    project_type = Column(Enum(ProjectTypeEnum))

    # Relationships
    master_item = relationship("MasterWorkItem", backref="price_history")
    boq_file = relationship("BOQFile", backref="price_history")
    project = relationship("Project", backref="price_history")

    # Composite index for efficient queries
    __table_args__ = (
        Index('idx_price_history_composite', 'master_item_id', 'recorded_at'),
    )

    def __repr__(self):
        return f"<PriceHistory {self.price_id}: master={self.master_item_id}, price={self.unit_price}>"
