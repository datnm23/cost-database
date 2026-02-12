"""
Learning Flywheel

Automatically creates synonyms and training logs when humans approve/resolve items.
This feeds the matching pipeline with new data, continuously improving accuracy.

Two entry points:
1. on_pending_approved() — when a pending item is approved and becomes a master item
2. on_project_item_resolved() — when a project work item is resolved to a master item
"""
import logging
import unicodedata
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.models.ai_training_log import AITrainingLog
from app.models.master_synonym import MasterSynonym
from app.models.master_work_item import MasterWorkItem
from app.models.pending_master_item import PendingMasterItem
from app.models.project_work_item import ProjectWorkItem

logger = logging.getLogger(__name__)


class LearningFlywheel:
    """
    Flywheel loop that learns from human decisions.

    Every human action (approve, edit, remap) creates:
    1. A synonym mapping (original → master) for future O(1) lookups
    2. A training log entry for analytics and model retraining
    """

    def __init__(self, db: Session):
        self.db = db

    def on_pending_approved(
        self,
        pending_item: PendingMasterItem,
        master_item: MasterWorkItem,
        reviewer_id: int,
        edited_description: Optional[str] = None,
    ) -> None:
        """
        Called when a pending item is approved and linked to a master item.

        Creates:
        - Synonym: pending_item.original_description → master_item
        - Training log with action ACCEPT or EDIT
        """
        original_desc = pending_item.original_description or pending_item.description

        # Determine action type
        action_type = 'ACCEPT'
        human_choice = master_item.description
        edit_distance = 0

        if edited_description and edited_description != master_item.description:
            action_type = 'EDIT'
            human_choice = edited_description
            edit_distance = self._levenshtein_distance(
                master_item.description or '', edited_description
            )

        # 1. Auto-create synonym
        self._create_synonym(
            master_id=master_item.master_id,
            synonym_text=original_desc,
            added_by=reviewer_id,
        )

        # 2. Log to ai_training_logs
        log = AITrainingLog(
            original_description=original_desc,
            normalized_description=pending_item.description,
            ai_suggestion=pending_item.description,
            ai_confidence=pending_item.quality_score / 100.0 if pending_item.quality_score else None,
            human_choice=human_choice,
            human_master_id=master_item.master_id,
            action_type=action_type,
            edit_distance=edit_distance,
            source_pending_id=pending_item.pending_id,
            reviewed_by=reviewer_id,
            reviewed_at=func.now(),
        )
        self.db.add(log)

        logger.info(
            f"Flywheel: pending #{pending_item.pending_id} → "
            f"master #{master_item.master_id} (action={action_type})"
        )

    def on_project_item_resolved(
        self,
        pwi: ProjectWorkItem,
        master_item: MasterWorkItem,
        reviewer_id: int,
        edited_description: Optional[str] = None,
    ) -> None:
        """
        Called when a project work item is resolved (mapped to a master item).

        Creates:
        - Synonym: pwi.original_description → master_item
        - Training log with action REMAP
        - Updates PWI resolution status
        """
        # 1. Auto-create synonym
        self._create_synonym(
            master_id=master_item.master_id,
            synonym_text=pwi.original_description,
            added_by=reviewer_id,
        )

        # 2. Log to ai_training_logs
        human_choice = edited_description or master_item.description
        edit_distance = 0
        if edited_description:
            edit_distance = self._levenshtein_distance(
                pwi.normalized_description or pwi.original_description,
                edited_description,
            )

        log = AITrainingLog(
            original_description=pwi.original_description,
            normalized_description=pwi.normalized_description,
            ai_suggestion=pwi.normalized_description,
            ai_confidence=pwi.quality_score / 100.0 if pwi.quality_score else None,
            ai_structured=pwi.ai_structured_output,
            human_choice=human_choice,
            human_master_id=master_item.master_id,
            action_type='REMAP',
            edit_distance=edit_distance,
            project_id=pwi.project_id,
            source_pwi_id=pwi.pwi_id,
            reviewed_by=reviewer_id,
            reviewed_at=func.now(),
        )
        self.db.add(log)

        # 3. Update PWI resolution
        pwi.resolution_status = 'APPROVED'
        pwi.master_work_item_id = master_item.master_id
        pwi.resolved_by = reviewer_id
        pwi.resolved_at = func.now()

        logger.info(
            f"Flywheel: PWI #{pwi.pwi_id} → master #{master_item.master_id} (REMAP)"
        )

    def _create_synonym(
        self,
        master_id: int,
        synonym_text: str,
        added_by: Optional[int] = None,
    ) -> Optional[MasterSynonym]:
        """Create a synonym if it doesn't already exist."""
        if not synonym_text or not synonym_text.strip():
            return None

        normalized = self._normalize_for_index(synonym_text)

        # Check for existing
        existing = self.db.query(MasterSynonym).filter(
            MasterSynonym.master_id == master_id,
            MasterSynonym.synonym_normalized == normalized,
        ).first()

        if existing:
            return existing

        synonym = MasterSynonym(
            master_id=master_id,
            synonym_text=synonym_text,
            synonym_normalized=normalized,
            synonym_type='alias',
            is_active=True,
            added_by=added_by,
        )
        self.db.add(synonym)
        return synonym

    def _normalize_for_index(self, text: str) -> str:
        """Normalize text for indexing."""
        if not text:
            return ''
        text = unicodedata.normalize('NFC', text)
        text = text.lower()
        text = ' '.join(text.split())
        return text.strip()

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Compute Levenshtein edit distance between two strings."""
        if not s1:
            return len(s2) if s2 else 0
        if not s2:
            return len(s1)

        m, n = len(s1), len(s2)
        # Use two-row optimization
        prev = list(range(n + 1))
        curr = [0] * (n + 1)

        for i in range(1, m + 1):
            curr[0] = i
            for j in range(1, n + 1):
                cost = 0 if s1[i - 1] == s2[j - 1] else 1
                curr[j] = min(
                    prev[j] + 1,      # deletion
                    curr[j - 1] + 1,   # insertion
                    prev[j - 1] + cost  # substitution
                )
            prev, curr = curr, prev

        return prev[n]


def get_learning_flywheel(db: Session) -> LearningFlywheel:
    """Factory function for LearningFlywheel."""
    return LearningFlywheel(db)
