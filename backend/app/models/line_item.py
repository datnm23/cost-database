from sqlalchemy import Column, BigInteger, Integer, String, ForeignKey, DECIMAL, Text, Enum, DateTime, Boolean, func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class ClassificationMethod(str, enum.Enum):
    auto = "auto"
    manual = "manual"


class LineItem(Base):
    __tablename__ = "line_items"

    line_item_id = Column(BigInteger, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("boq_files.file_id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False, index=True)
    row_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    unit = Column(String(10))
    quantity = Column(DECIMAL(18, 4))
    unit_price = Column(DECIMAL(18, 2))
    amount = Column(DECIMAL(18, 2))
    sec_code = Column(String(20), ForeignKey("sec_codes.sec_code"), index=True)
    confidence_score = Column(DECIMAL(5, 2))
    classification_method = Column(Enum(ClassificationMethod), default=ClassificationMethod.auto)

    # FR-DC-03: Data validation tracking
    needs_review = Column(Boolean, default=False, index=True, nullable=False)
    validation_issues = Column(Text, nullable=True)

    # Naming normalization fields
    normalized_description = Column(Text, nullable=True)
    normalization_confidence = Column(DECIMAL(5, 2), nullable=True)
    work_category = Column(String(50), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    boq_file = relationship("BOQFile", back_populates="line_items")
    project = relationship("Project", back_populates="line_items")
    sec = relationship("SECCode")

    def __repr__(self):
        return f"<LineItem {self.line_item_id}: {self.description[:30]}...>"
