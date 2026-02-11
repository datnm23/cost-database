"""
Activity BOM (Bill of Materials)

Links an Activity code (A.*) to its constituent resources:
  Material (M.*), Labour (L.*), Equipment (E.*)

Enables the quad-table N:M relationship model.
Code format: PREFIX.GROUP.TYPE (3 levels)
"""
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, Enum, Index
from app.core.database import Base


class ActivityBOM(Base):
    """
    Maps Activity → Resource with quantity factors.
    E.g. A.CONC.STR requires:
      - M.CONC.STR (concrete) × 1.05
      - L.CONC.STR (worker) × 0.15 md/m3
      - E.CONC.STR (pump) × 0.02 ca/m3
    """
    __tablename__ = "activity_bom"

    bom_id = Column(Integer, primary_key=True, autoincrement=True)

    activity_code = Column(
        String(15),
        ForeignKey("sec_codes_v4.code", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Activity code (A.* prefix)",
    )

    resource_code = Column(
        String(15),
        ForeignKey("sec_codes_v4.code", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Resource code (M.*/L.*/E.* prefix)",
    )

    resource_type = Column(
        Enum('M', 'L', 'E', name='bom_resource_type'),
        nullable=False,
        comment="M=Material, L=Labour, E=Equipment",
    )

    quantity_factor = Column(
        Float,
        nullable=False,
        default=1.0,
        comment="Resource qty per unit of activity (e.g. 1.05 m3 concrete per 1 m3 pour)",
    )

    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index('idx_bom_activity_resource', 'activity_code', 'resource_code', unique=True),
    )

    def __repr__(self):
        return (
            f"<ActivityBOM({self.activity_code} -> {self.resource_code} "
            f"x{self.quantity_factor})>"
        )
