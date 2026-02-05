"""
Unit Standard Schemas - Pydantic schemas for unit management API
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# =====================================================
# Unit Standard Schemas
# =====================================================

class UnitStandardBase(BaseModel):
    """Base schema for unit standardization"""
    raw_unit: str = Field(..., max_length=50, description="Raw unit notation (e.g., 'm3', 'sqm')")
    standard_unit: str = Field(..., max_length=50, description="Standardized unit (e.g., 'm³', 'm²')")
    unit_category: Optional[str] = Field(None, max_length=50, description="Category: volume, area, length, weight, count, other")
    description: Optional[str] = Field(None, description="Description of the unit mapping")


class UnitStandardCreate(UnitStandardBase):
    """Schema for creating a new unit standard"""
    pass


class UnitStandardUpdate(BaseModel):
    """Schema for updating a unit standard"""
    raw_unit: Optional[str] = Field(None, max_length=50)
    standard_unit: Optional[str] = Field(None, max_length=50)
    unit_category: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class UnitStandardResponse(UnitStandardBase):
    """Schema for unit standard response"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UnitStandardList(BaseModel):
    """Schema for list of unit standards"""
    items: List[UnitStandardResponse]
    total: int
    page: int
    page_size: int


# =====================================================
# SEC Code Default Unit Schemas
# =====================================================

class SecCodeDefaultUnitBase(BaseModel):
    """Base schema for SEC code default unit"""
    sec_code: str = Field(..., max_length=20, description="SEC code (e.g., 'SEC-02-01')")
    default_unit: str = Field(..., max_length=50, description="Default unit for this SEC code")
    category_name_vi: Optional[str] = Field(None, max_length=100, description="Vietnamese category name")
    category_name_en: Optional[str] = Field(None, max_length=100, description="English category name")
    notes: Optional[str] = Field(None, description="Additional notes")


class SecCodeDefaultUnitCreate(SecCodeDefaultUnitBase):
    """Schema for creating a new SEC code default unit"""
    pass


class SecCodeDefaultUnitUpdate(BaseModel):
    """Schema for updating a SEC code default unit"""
    sec_code: Optional[str] = Field(None, max_length=20)
    default_unit: Optional[str] = Field(None, max_length=50)
    category_name_vi: Optional[str] = Field(None, max_length=100)
    category_name_en: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class SecCodeDefaultUnitResponse(SecCodeDefaultUnitBase):
    """Schema for SEC code default unit response"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SecCodeDefaultUnitList(BaseModel):
    """Schema for list of SEC code default units"""
    items: List[SecCodeDefaultUnitResponse]
    total: int


# =====================================================
# Utility Schemas
# =====================================================

class StandardizeUnitRequest(BaseModel):
    """Request schema for standardizing a unit"""
    raw_unit: str = Field(..., description="Raw unit to standardize")
    sec_code: Optional[str] = Field(None, description="SEC code for default fallback")


class StandardizeUnitResponse(BaseModel):
    """Response schema for standardized unit"""
    raw_unit: str
    standardized_unit: str
    is_default_applied: bool
    source: str  # 'mapping', 'default', 'original'


class BulkStandardizeRequest(BaseModel):
    """Request schema for bulk unit standardization"""
    units: List[StandardizeUnitRequest]


class BulkStandardizeResponse(BaseModel):
    """Response schema for bulk unit standardization"""
    results: List[StandardizeUnitResponse]
