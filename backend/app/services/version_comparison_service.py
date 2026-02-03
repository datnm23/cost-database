"""
Version Comparison Service
Compares different versions of BOQ files to identify changes
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session

from app.models.boq_version import BOQVersion
from app.models.line_item import LineItem
from app.models.boq_file import BOQFile


class ChangeStatus(str, Enum):
    unchanged = "unchanged"
    price_changed = "price_changed"
    added = "added"
    removed = "removed"
    quantity_changed = "quantity_changed"


@dataclass
class ComparisonItem:
    """Represents a single item comparison between versions"""
    description: str
    normalized_description: Optional[str]
    sec_code: Optional[str]
    status: ChangeStatus
    v1_quantity: Optional[float]
    v2_quantity: Optional[float]
    v1_unit_price: Optional[float]
    v2_unit_price: Optional[float]
    v1_amount: Optional[float]
    v2_amount: Optional[float]
    price_diff_percent: Optional[float]
    quantity_diff_percent: Optional[float]


@dataclass
class ComparisonSummary:
    """Summary of changes between versions"""
    v1_version_number: int
    v2_version_number: int
    v1_total_items: int
    v2_total_items: int
    v1_total_amount: float
    v2_total_amount: float
    amount_diff: float
    amount_diff_percent: float
    unchanged_count: int
    price_changed_count: int
    quantity_changed_count: int
    added_count: int
    removed_count: int


@dataclass
class VersionComparisonResult:
    """Full comparison result"""
    project_id: int
    summary: ComparisonSummary
    items: List[ComparisonItem]


class VersionComparisonService:
    """Service for comparing BOQ versions"""

    def __init__(self, db: Session):
        self.db = db

    def compare_versions(
        self,
        project_id: int,
        v1: int,
        v2: int,
        price_threshold: float = 5.0
    ) -> VersionComparisonResult:
        """
        Compare two versions of BOQ for a project

        Args:
            project_id: Project ID
            v1: First version number
            v2: Second version number
            price_threshold: Percentage threshold to consider price as "changed"

        Returns:
            VersionComparisonResult with summary and item-level comparisons
        """
        # Get version records
        version1 = self.db.query(BOQVersion).filter(
            BOQVersion.project_id == project_id,
            BOQVersion.version_number == v1
        ).first()

        version2 = self.db.query(BOQVersion).filter(
            BOQVersion.project_id == project_id,
            BOQVersion.version_number == v2
        ).first()

        if not version1 or not version2:
            raise ValueError(f"Version not found: v1={v1}, v2={v2}")

        # Get line items for each version
        v1_items = self.db.query(LineItem).filter(
            LineItem.file_id == version1.file_id
        ).all()

        v2_items = self.db.query(LineItem).filter(
            LineItem.file_id == version2.file_id
        ).all()

        # Create lookup dictionaries by normalized description
        v1_by_desc = self._create_item_lookup(v1_items)
        v2_by_desc = self._create_item_lookup(v2_items)

        # Compare items
        comparison_items = []
        unchanged_count = 0
        price_changed_count = 0
        quantity_changed_count = 0
        added_count = 0
        removed_count = 0

        # Find items in both versions and those removed
        all_descriptions = set(v1_by_desc.keys()) | set(v2_by_desc.keys())

        for desc in all_descriptions:
            v1_item = v1_by_desc.get(desc)
            v2_item = v2_by_desc.get(desc)

            if v1_item and v2_item:
                # Item exists in both versions
                status, price_diff, qty_diff = self._compare_items(
                    v1_item, v2_item, price_threshold
                )

                if status == ChangeStatus.unchanged:
                    unchanged_count += 1
                elif status == ChangeStatus.price_changed:
                    price_changed_count += 1
                elif status == ChangeStatus.quantity_changed:
                    quantity_changed_count += 1

                comparison_items.append(ComparisonItem(
                    description=v1_item.description,
                    normalized_description=v1_item.normalized_description,
                    sec_code=v1_item.sec_code,
                    status=status,
                    v1_quantity=float(v1_item.quantity) if v1_item.quantity else None,
                    v2_quantity=float(v2_item.quantity) if v2_item.quantity else None,
                    v1_unit_price=float(v1_item.unit_price) if v1_item.unit_price else None,
                    v2_unit_price=float(v2_item.unit_price) if v2_item.unit_price else None,
                    v1_amount=float(v1_item.amount) if v1_item.amount else None,
                    v2_amount=float(v2_item.amount) if v2_item.amount else None,
                    price_diff_percent=price_diff,
                    quantity_diff_percent=qty_diff
                ))

            elif v1_item and not v2_item:
                # Item removed in v2
                removed_count += 1
                comparison_items.append(ComparisonItem(
                    description=v1_item.description,
                    normalized_description=v1_item.normalized_description,
                    sec_code=v1_item.sec_code,
                    status=ChangeStatus.removed,
                    v1_quantity=float(v1_item.quantity) if v1_item.quantity else None,
                    v2_quantity=None,
                    v1_unit_price=float(v1_item.unit_price) if v1_item.unit_price else None,
                    v2_unit_price=None,
                    v1_amount=float(v1_item.amount) if v1_item.amount else None,
                    v2_amount=None,
                    price_diff_percent=None,
                    quantity_diff_percent=None
                ))

            else:
                # Item added in v2
                added_count += 1
                comparison_items.append(ComparisonItem(
                    description=v2_item.description,
                    normalized_description=v2_item.normalized_description,
                    sec_code=v2_item.sec_code,
                    status=ChangeStatus.added,
                    v1_quantity=None,
                    v2_quantity=float(v2_item.quantity) if v2_item.quantity else None,
                    v1_unit_price=None,
                    v2_unit_price=float(v2_item.unit_price) if v2_item.unit_price else None,
                    v1_amount=None,
                    v2_amount=float(v2_item.amount) if v2_item.amount else None,
                    price_diff_percent=None,
                    quantity_diff_percent=None
                ))

        # Calculate totals
        v1_total = sum(float(i.amount) for i in v1_items if i.amount)
        v2_total = sum(float(i.amount) for i in v2_items if i.amount)
        amount_diff = v2_total - v1_total
        amount_diff_percent = (amount_diff / v1_total * 100) if v1_total else 0

        summary = ComparisonSummary(
            v1_version_number=v1,
            v2_version_number=v2,
            v1_total_items=len(v1_items),
            v2_total_items=len(v2_items),
            v1_total_amount=v1_total,
            v2_total_amount=v2_total,
            amount_diff=amount_diff,
            amount_diff_percent=round(amount_diff_percent, 2),
            unchanged_count=unchanged_count,
            price_changed_count=price_changed_count,
            quantity_changed_count=quantity_changed_count,
            added_count=added_count,
            removed_count=removed_count
        )

        return VersionComparisonResult(
            project_id=project_id,
            summary=summary,
            items=comparison_items
        )

    def _create_item_lookup(self, items: List[LineItem]) -> Dict[str, LineItem]:
        """Create lookup by normalized description (or raw description)"""
        lookup = {}
        for item in items:
            key = (item.normalized_description or item.description or "").lower().strip()
            if key:
                lookup[key] = item
        return lookup

    def _compare_items(
        self,
        v1: LineItem,
        v2: LineItem,
        price_threshold: float
    ) -> Tuple[ChangeStatus, Optional[float], Optional[float]]:
        """Compare two items and return status and diff percentages"""
        v1_price = float(v1.unit_price) if v1.unit_price else 0
        v2_price = float(v2.unit_price) if v2.unit_price else 0
        v1_qty = float(v1.quantity) if v1.quantity else 0
        v2_qty = float(v2.quantity) if v2.quantity else 0

        price_diff = None
        qty_diff = None

        if v1_price > 0:
            price_diff = ((v2_price - v1_price) / v1_price) * 100
        if v1_qty > 0:
            qty_diff = ((v2_qty - v1_qty) / v1_qty) * 100

        # Determine status
        if price_diff is not None and abs(price_diff) > price_threshold:
            return ChangeStatus.price_changed, round(price_diff, 2), round(qty_diff, 2) if qty_diff else None
        elif qty_diff is not None and abs(qty_diff) > 1:  # 1% threshold for quantity
            return ChangeStatus.quantity_changed, round(price_diff, 2) if price_diff else None, round(qty_diff, 2)
        else:
            return ChangeStatus.unchanged, round(price_diff, 2) if price_diff else None, round(qty_diff, 2) if qty_diff else None


def get_version_comparison_service(db: Session) -> VersionComparisonService:
    """Factory function"""
    return VersionComparisonService(db)
