"""
Spec Lifecycle Service

Manages the lifecycle of specifications on MasterWorkItems:
  - draft → detailed → final
  - Tracks every change with audit trail (SpecChangeLog)
  - Computes completeness scores
  - Validates promotion rules
"""
import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.master_work_item import MasterWorkItem
from app.models.spec_change_log import SpecChangeLog

logger = logging.getLogger(__name__)

# Confidence mapping: how trustworthy is each source?
SOURCE_CONFIDENCE = {
    'default': 0.3,
    'boq': 0.5,
    'drawing': 0.8,
    'as_built': 1.0,
}

# Fields that count as "spec fields"
SPEC_FIELDS = {'spec_category', 'spec_material', 'spec_grade', 'spec_dimension'}

# Status ordering
STATUS_ORDER = ['draft', 'detailed', 'final']


class SpecLifecycleService:
    """Manages spec updates, promotions, and change tracking."""

    def __init__(self, db: Session):
        self.db = db

    def update_spec(
        self,
        master_id: int,
        field: str,
        value: str,
        source: str = 'manual',
        user_id: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> MasterWorkItem:
        """
        Update a single spec field with audit trail.

        Args:
            master_id: ID of the master work item
            field: Field name (spec_grade, spec_material, etc.)
            value: New value
            source: Change source (manual, boq, drawing, as_built, default)
            user_id: Who made the change
            notes: Optional notes

        Returns:
            Updated MasterWorkItem
        """
        item = self.db.query(MasterWorkItem).filter(
            MasterWorkItem.master_id == master_id
        ).first()
        if not item:
            raise ValueError(f"MasterWorkItem {master_id} not found")

        old_value = getattr(item, field, None)
        old_status = item.spec_status

        # Update the field
        setattr(item, field, value)

        # Update source and confidence
        item.spec_source = source
        item.spec_confidence = SOURCE_CONFIDENCE.get(source, 0.3)

        # Recompute completeness
        item.spec_completeness = item.compute_spec_completeness()

        # Log the change
        log = SpecChangeLog(
            master_id=master_id,
            field_name=field,
            old_value=str(old_value) if old_value else None,
            new_value=str(value) if value else None,
            old_status=old_status,
            new_status=item.spec_status,
            change_source=source,
            changed_by=user_id,
            notes=notes,
        )
        self.db.add(log)
        self.db.flush()

        return item

    def promote_status(
        self,
        master_id: int,
        target_status: str,
        user_id: Optional[int] = None,
    ) -> MasterWorkItem:
        """
        Promote spec status: draft → detailed → final.

        Validation rules:
          - draft → detailed: spec_completeness >= 0.50
          - detailed → final: spec_completeness >= 0.75 AND is_verified == True
        """
        item = self.db.query(MasterWorkItem).filter(
            MasterWorkItem.master_id == master_id
        ).first()
        if not item:
            raise ValueError(f"MasterWorkItem {master_id} not found")

        current_idx = STATUS_ORDER.index(item.spec_status)
        target_idx = STATUS_ORDER.index(target_status)

        if target_idx <= current_idx:
            raise ValueError(
                f"Cannot promote from '{item.spec_status}' to '{target_status}' — "
                f"target must be higher"
            )

        # Validate promotion rules
        if target_status == 'detailed':
            if item.spec_completeness < 0.50:
                raise ValueError(
                    f"Cannot promote to 'detailed': spec_completeness "
                    f"{item.spec_completeness:.0%} < 50% required"
                )
        elif target_status == 'final':
            if item.spec_completeness < 0.75:
                raise ValueError(
                    f"Cannot promote to 'final': spec_completeness "
                    f"{item.spec_completeness:.0%} < 75% required"
                )
            if not item.is_verified:
                raise ValueError(
                    "Cannot promote to 'final': item must be verified first"
                )

        old_status = item.spec_status
        item.spec_status = target_status

        # Log status change
        log = SpecChangeLog(
            master_id=master_id,
            field_name='spec_status',
            old_value=old_status,
            new_value=target_status,
            old_status=old_status,
            new_status=target_status,
            change_source='manual',
            changed_by=user_id,
            notes=f"Status promoted: {old_status} → {target_status}",
        )
        self.db.add(log)
        self.db.flush()

        return item

    def compute_completeness(self, item: MasterWorkItem) -> float:
        """Compute and update spec_completeness on an item."""
        item.spec_completeness = item.compute_spec_completeness()
        return item.spec_completeness

    def batch_set_defaults(
        self,
        items: List[MasterWorkItem],
        default_specs: Optional[dict] = None,
    ) -> int:
        """
        Apply category-specific defaults to items missing specs.

        Args:
            items: List of MasterWorkItems to process
            default_specs: Optional override dict {field: value}

        Returns:
            Number of items updated
        """
        updated = 0
        for item in items:
            changed = False

            # Apply defaults only if field is empty
            if default_specs:
                for field, value in default_specs.items():
                    if field in SPEC_FIELDS and not getattr(item, field, None):
                        setattr(item, field, value)
                        changed = True

            if changed:
                item.spec_source = 'default'
                item.spec_confidence = SOURCE_CONFIDENCE['default']
                item.spec_completeness = item.compute_spec_completeness()
                updated += 1

        return updated

    def get_change_history(
        self,
        master_id: int,
        limit: int = 50,
    ) -> List[SpecChangeLog]:
        """Get spec change history for a master item, newest first."""
        return (
            self.db.query(SpecChangeLog)
            .filter(SpecChangeLog.master_id == master_id)
            .order_by(SpecChangeLog.changed_at.desc())
            .limit(limit)
            .all()
        )

    def get_incomplete_items(
        self,
        threshold: float = 0.75,
        limit: int = 100,
    ) -> List[MasterWorkItem]:
        """Get items with spec_completeness below threshold."""
        return (
            self.db.query(MasterWorkItem)
            .filter(
                MasterWorkItem.is_active == True,
                MasterWorkItem.spec_completeness < threshold,
            )
            .order_by(MasterWorkItem.spec_completeness.asc())
            .limit(limit)
            .all()
        )


def get_spec_lifecycle_service(db: Session) -> SpecLifecycleService:
    """Factory function."""
    return SpecLifecycleService(db)
