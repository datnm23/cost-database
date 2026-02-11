"""
Spec Change Log — Audit trail for specification changes on master work items.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class SpecChangeLog(Base):
    """
    Logs every change to spec fields on a MasterWorkItem.
    Provides full audit trail: who changed what, when, old/new values.
    """
    __tablename__ = "spec_change_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    master_id = Column(
        Integer,
        ForeignKey("master_work_items.master_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # What changed
    field_name = Column(String(50), nullable=False, comment="Field that changed (spec_grade, spec_material, etc.)")
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)

    # Status transitions
    old_status = Column(String(20), nullable=True, comment="Previous spec_status")
    new_status = Column(String(20), nullable=True, comment="New spec_status")

    # Change metadata
    change_source = Column(
        String(20),
        nullable=False,
        default='manual',
        comment="Source: manual, boq, drawing, as_built, default, system",
    )
    changed_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    changed_at = Column(DateTime, server_default=func.now(), nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    master_item = relationship("MasterWorkItem", backref="spec_change_logs")

    def __repr__(self):
        return (
            f"<SpecChangeLog(master_id={self.master_id}, "
            f"field={self.field_name}, {self.old_value}->{self.new_value})>"
        )
