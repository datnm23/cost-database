"""
Unit Standard Models - Database models for unit standardization and defaults

Tables:
1. unit_standards - Maps raw unit variations to standardized units
2. sec_code_default_units - Maps SEC codes to default units
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Index
from app.core.database import Base


class UnitStandard(Base):
    """
    Unit standardization mapping table.
    Maps various unit notations to their standardized form.

    Examples:
        'm3' -> 'm³'
        'sqm' -> 'm²'
        'pcs' -> 'cái'
    """
    __tablename__ = "unit_standards"

    id = Column(Integer, primary_key=True, index=True)
    raw_unit = Column(String(50), nullable=False, unique=True, index=True)
    standard_unit = Column(String(50), nullable=False)
    unit_category = Column(String(50), nullable=True)  # volume, area, length, weight, count, other
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Index for faster lookups
    __table_args__ = (
        Index('ix_unit_standards_raw_lower', 'raw_unit'),
    )

    def __repr__(self):
        return f"<UnitStandard('{self.raw_unit}' -> '{self.standard_unit}')>"


class SecCodeDefaultUnit(Base):
    """
    SEC code to default unit mapping table.
    Defines the default measurement unit for each work category.

    Examples:
        'SEC-02-01' (Concrete) -> 'm³'
        'SEC-03-03' (Painting) -> 'm²'
        'SEC-02-06' (Rebar) -> 'kg'
    """
    __tablename__ = "sec_code_default_units"

    id = Column(Integer, primary_key=True, index=True)
    sec_code = Column(String(20), nullable=False, unique=True, index=True)
    default_unit = Column(String(50), nullable=False)
    category_name_vi = Column(String(100), nullable=True)  # Vietnamese name
    category_name_en = Column(String(100), nullable=True)  # English name
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SecCodeDefaultUnit('{self.sec_code}' -> '{self.default_unit}')>"
