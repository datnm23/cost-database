"""
Unit Standard Service - Service layer for unit standardization and default unit management

This service provides:
1. Database-backed unit standardization (replaces hardcoded UNIT_STANDARDIZATION)
2. Database-backed SEC code default units (replaces hardcoded SEC_CODE_DEFAULT_UNIT)
3. Fallback to hardcoded values when database is empty
"""
import logging
from typing import Optional, Tuple, Dict, List
from functools import lru_cache

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.unit_standard import UnitStandard, SecCodeDefaultUnit
from app.schemas.unit_standard import (
    UnitStandardCreate, UnitStandardUpdate,
    SecCodeDefaultUnitCreate, SecCodeDefaultUnitUpdate
)

logger = logging.getLogger(__name__)

# Fallback hardcoded values (used when database is empty)
FALLBACK_UNIT_STANDARDIZATION = {
    'm3': 'm³', 'm³': 'm³', 'mét khối': 'm³', 'm khối': 'm³',
    'khối': 'm³', 'cbm': 'm³', 'cubic meter': 'm³', 'cubic m': 'm³',
    'm2': 'm²', 'm²': 'm²', 'mét vuông': 'm²', 'm vuông': 'm²',
    'sqm': 'm²', 'sq.m': 'm²', 'square meter': 'm²', 'sq m': 'm²',
    'm': 'm', 'mét': 'm', 'met': 'm', 'meter': 'm',
    'mm': 'mm', 'cm': 'cm', 'km': 'km',
    'kg': 'kg', 'kilo': 'kg', 'kilogram': 'kg',
    'tấn': 'tấn', 'tan': 'tấn', 'ton': 'tấn', 't': 'tấn', 'tonne': 'tấn',
    'cái': 'cái', 'chiếc': 'cái', 'pc': 'cái', 'pcs': 'cái',
    'bộ': 'bộ', 'set': 'bộ',
    'điểm': 'điểm', 'point': 'điểm',
    'cây': 'cây', 'tree': 'cây',
    'ls': 'trọn gói', 'lump sum': 'trọn gói', 'trọn gói': 'trọn gói',
    'công': 'công', 'man-day': 'công',
}

FALLBACK_SEC_CODE_DEFAULT_UNIT = {
    'SEC-00': 'trọn gói', 'SEC-01': 'm³', 'SEC-02': 'm³',
    'SEC-03': 'm²', 'SEC-04': 'bộ', 'SEC-05': 'm²',
    'SEC-01-01': 'm³', 'SEC-01-02': 'm', 'SEC-01-03': 'm³',
    'SEC-02-01': 'm³', 'SEC-02-02': 'm³', 'SEC-02-03': 'm³',
    'SEC-02-04': 'm³', 'SEC-02-05': 'm³', 'SEC-02-06': 'kg',
    'SEC-03-01': 'm³', 'SEC-03-02': 'm²', 'SEC-03-03': 'm²',
    'SEC-03-04': 'm²', 'SEC-03-05': 'm²', 'SEC-03-06': 'bộ',
    'SEC-04-01': 'điểm', 'SEC-04-02': 'điểm', 'SEC-04-03': 'bộ', 'SEC-04-04': 'bộ',
    'SEC-05-01': 'm²', 'SEC-05-02': 'm²', 'SEC-05-03': 'cây',
}


class UnitStandardService:
    """Service for managing unit standards and SEC code default units"""

    def __init__(self, db: Session):
        self.db = db
        self._unit_cache: Optional[Dict[str, str]] = None
        self._sec_cache: Optional[Dict[str, str]] = None

    def _load_unit_mappings(self) -> Dict[str, str]:
        """Load unit standardization mappings from database"""
        if self._unit_cache is not None:
            return self._unit_cache

        mappings = self.db.query(UnitStandard).filter(
            UnitStandard.is_active == True
        ).all()

        if mappings:
            self._unit_cache = {m.raw_unit.lower(): m.standard_unit for m in mappings}
        else:
            # Fallback to hardcoded values
            self._unit_cache = FALLBACK_UNIT_STANDARDIZATION.copy()

        return self._unit_cache

    def _load_sec_defaults(self) -> Dict[str, str]:
        """Load SEC code default units from database"""
        if self._sec_cache is not None:
            return self._sec_cache

        defaults = self.db.query(SecCodeDefaultUnit).filter(
            SecCodeDefaultUnit.is_active == True
        ).all()

        if defaults:
            self._sec_cache = {d.sec_code: d.default_unit for d in defaults}
        else:
            # Fallback to hardcoded values
            self._sec_cache = FALLBACK_SEC_CODE_DEFAULT_UNIT.copy()

        return self._sec_cache

    def clear_cache(self):
        """Clear the in-memory cache"""
        self._unit_cache = None
        self._sec_cache = None

    # =====================================================
    # Unit Standardization
    # =====================================================

    def standardize_unit(self, unit: str) -> str:
        """
        Standardize unit notation to Vietnamese convention.

        Args:
            unit: Raw unit string (e.g., 'm3', 'sqm', 'pcs')

        Returns:
            Standardized unit (e.g., 'm³', 'm²', 'cái')
        """
        if not unit:
            return ""

        unit_clean = unit.strip().lower()
        mappings = self._load_unit_mappings()
        return mappings.get(unit_clean, unit)

    def get_default_unit_for_sec_code(self, sec_code: str) -> str:
        """
        Get default unit for a SEC code, falling back to parent level.

        Args:
            sec_code: SEC code like 'SEC-02-01' or 'SEC-02'

        Returns:
            Default unit string (e.g., 'm³', 'm²', 'bộ')
        """
        if not sec_code:
            return ""

        defaults = self._load_sec_defaults()

        # Try exact match first
        if sec_code in defaults:
            return defaults[sec_code]

        # Try parent level (SEC-XX-YY -> SEC-XX)
        parts = sec_code.split('-')
        if len(parts) >= 2:
            parent = f"{parts[0]}-{parts[1]}"
            if parent in defaults:
                return defaults[parent]

        return ""

    def get_unit_with_default(self, raw_unit: str, sec_code: str) -> Tuple[str, bool]:
        """
        Get standardized unit, falling back to SEC code default if empty.

        Args:
            raw_unit: Original unit from BOQ
            sec_code: SEC code for default fallback

        Returns:
            Tuple of (standardized_unit, is_default_applied)
        """
        if raw_unit and raw_unit.strip():
            return self.standardize_unit(raw_unit), False

        default = self.get_default_unit_for_sec_code(sec_code)
        return default, bool(default)

    # =====================================================
    # CRUD Operations - Unit Standards
    # =====================================================

    def get_unit_standards(
        self,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        active_only: bool = True
    ) -> Tuple[List[UnitStandard], int]:
        """Get list of unit standards with pagination"""
        query = self.db.query(UnitStandard)

        if active_only:
            query = query.filter(UnitStandard.is_active == True)

        if category:
            query = query.filter(UnitStandard.unit_category == category)

        total = query.count()
        items = query.order_by(UnitStandard.unit_category, UnitStandard.raw_unit).offset(skip).limit(limit).all()

        return items, total

    def get_unit_standard_by_id(self, unit_id: int) -> Optional[UnitStandard]:
        """Get a unit standard by ID"""
        return self.db.query(UnitStandard).filter(UnitStandard.id == unit_id).first()

    def get_unit_standard_by_raw(self, raw_unit: str) -> Optional[UnitStandard]:
        """Get a unit standard by raw unit"""
        return self.db.query(UnitStandard).filter(
            func.lower(UnitStandard.raw_unit) == raw_unit.lower()
        ).first()

    def create_unit_standard(self, data: UnitStandardCreate) -> UnitStandard:
        """Create a new unit standard"""
        unit = UnitStandard(
            raw_unit=data.raw_unit.strip().lower(),
            standard_unit=data.standard_unit,
            unit_category=data.unit_category,
            description=data.description
        )
        self.db.add(unit)
        self.db.commit()
        self.db.refresh(unit)
        self.clear_cache()
        return unit

    def update_unit_standard(self, unit_id: int, data: UnitStandardUpdate) -> Optional[UnitStandard]:
        """Update a unit standard"""
        unit = self.get_unit_standard_by_id(unit_id)
        if not unit:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key == 'raw_unit' and value:
                value = value.strip().lower()
            setattr(unit, key, value)

        self.db.commit()
        self.db.refresh(unit)
        self.clear_cache()
        return unit

    def delete_unit_standard(self, unit_id: int) -> bool:
        """Delete a unit standard (soft delete)"""
        unit = self.get_unit_standard_by_id(unit_id)
        if not unit:
            return False

        unit.is_active = False
        self.db.commit()
        self.clear_cache()
        return True

    # =====================================================
    # CRUD Operations - SEC Code Default Units
    # =====================================================

    def get_sec_code_defaults(self, active_only: bool = True) -> Tuple[List[SecCodeDefaultUnit], int]:
        """Get list of SEC code default units"""
        query = self.db.query(SecCodeDefaultUnit)

        if active_only:
            query = query.filter(SecCodeDefaultUnit.is_active == True)

        items = query.order_by(SecCodeDefaultUnit.sec_code).all()
        total = len(items)

        return items, total

    def get_sec_code_default_by_id(self, default_id: int) -> Optional[SecCodeDefaultUnit]:
        """Get a SEC code default by ID"""
        return self.db.query(SecCodeDefaultUnit).filter(SecCodeDefaultUnit.id == default_id).first()

    def get_sec_code_default_by_code(self, sec_code: str) -> Optional[SecCodeDefaultUnit]:
        """Get a SEC code default by SEC code"""
        return self.db.query(SecCodeDefaultUnit).filter(
            SecCodeDefaultUnit.sec_code == sec_code
        ).first()

    def create_sec_code_default(self, data: SecCodeDefaultUnitCreate) -> SecCodeDefaultUnit:
        """Create a new SEC code default unit"""
        default = SecCodeDefaultUnit(
            sec_code=data.sec_code,
            default_unit=data.default_unit,
            category_name_vi=data.category_name_vi,
            category_name_en=data.category_name_en,
            notes=data.notes
        )
        self.db.add(default)
        self.db.commit()
        self.db.refresh(default)
        self.clear_cache()
        return default

    def update_sec_code_default(self, default_id: int, data: SecCodeDefaultUnitUpdate) -> Optional[SecCodeDefaultUnit]:
        """Update a SEC code default unit"""
        default = self.get_sec_code_default_by_id(default_id)
        if not default:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(default, key, value)

        self.db.commit()
        self.db.refresh(default)
        self.clear_cache()
        return default

    def delete_sec_code_default(self, default_id: int) -> bool:
        """Delete a SEC code default (soft delete)"""
        default = self.get_sec_code_default_by_id(default_id)
        if not default:
            return False

        default.is_active = False
        self.db.commit()
        self.clear_cache()
        return True

    # =====================================================
    # Utility Methods
    # =====================================================

    def get_all_unit_categories(self) -> List[str]:
        """Get list of distinct unit categories"""
        result = self.db.query(UnitStandard.unit_category).filter(
            UnitStandard.is_active == True,
            UnitStandard.unit_category.isnot(None)
        ).distinct().all()
        return [r[0] for r in result if r[0]]

    def bulk_import_unit_standards(self, items: List[UnitStandardCreate]) -> int:
        """Bulk import unit standards"""
        count = 0
        for item in items:
            existing = self.get_unit_standard_by_raw(item.raw_unit)
            if not existing:
                self.create_unit_standard(item)
                count += 1
        return count


def get_unit_standard_service(db: Session) -> UnitStandardService:
    """Factory function to get unit standard service"""
    return UnitStandardService(db)
