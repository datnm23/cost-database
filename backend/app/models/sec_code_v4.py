"""
SEC Code v4.0 Reference Table — 3-Level Format

Stores the master reference codes for the 4-table architecture:
  A (Activity), M (Material), L (Labour), E (Equipment)

Code format: [PREFIX].[GROUP].[TYPE]
  e.g. A.CONC.STR — Activity: Concrete, Structural

Same GROUP.TYPE across all 4 prefixes = same work package:
  A.CONC.STR, M.CONC.STR, L.CONC.STR, E.CONC.STR
"""
from sqlalchemy import Column, String, Text, Float, Boolean, Enum, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class SECCodeV4(Base):
    """
    v4.0 reference code table — 3-level format.
    Each row is a standard code in the quad-table system.
    """
    __tablename__ = "sec_codes_v4"

    # Primary key: the full dot-separated code (e.g. A.CONC.STR)
    code = Column(String(15), primary_key=True, comment="Full code e.g. A.CONC.STR")

    # Decomposed levels
    table_type = Column(
        Enum('A', 'M', 'L', 'E', name='sec_v4_table_type'),
        nullable=False,
        comment="L0: A=Activity, M=Material, L=Labour, E=Equipment",
    )
    group_code = Column(String(5), nullable=False, comment="L1: CONC, RBAR, PIPE, BRCK, CABL...")
    type_code = Column(String(4), nullable=False, comment="L2: STR, LEA, SUP, DRN, SOL, AAC...")

    # Descriptive
    name_vi = Column(String(200), nullable=True, comment="Vietnamese name")
    name_en = Column(String(200), nullable=True, comment="English name")
    unit = Column(String(20), nullable=True, comment="Default unit (m3, kg, md, ca)")

    # NLP matching
    keywords_vi = Column(Text, nullable=True, comment="Vietnamese keywords for fuzzy matching (JSON array)")
    keywords_en = Column(Text, nullable=True, comment="English keywords for fuzzy matching (JSON array)")

    # Construction factor
    waste_percent = Column(Float, default=0.0, comment="Default waste percentage")

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    master_items = relationship("MasterWorkItem", back_populates="ref_code_rel", foreign_keys="MasterWorkItem.sec_code_v4")

    __table_args__ = (
        Index('idx_sec_v4_table_type', 'table_type'),
        Index('idx_sec_v4_group', 'group_code'),
        Index('idx_sec_v4_type', 'type_code'),
    )

    def __repr__(self):
        return f"<SECCodeV4({self.code}: {self.name_vi or self.name_en})>"
