"""
Synonym Service for Master Work Items

Handles:
- CRUD operations for synonyms
- Synonym-based matching lookup
- In-memory caching for fast O(1) lookup
"""
import logging
from typing import List, Optional, Dict

from sqlalchemy.orm import Session

from app.models.master_synonym import MasterSynonym
from app.models.master_work_item import MasterWorkItem

logger = logging.getLogger(__name__)


class SynonymService:
    """Service for managing master item synonyms."""

    def __init__(self, db: Session):
        self.db = db
        self._synonym_cache: Dict[str, int] = {}  # normalized_text -> master_id
        self._cache_built = False

    def build_synonym_cache(self) -> int:
        """
        Build in-memory cache of synonyms for fast lookup.

        Returns:
            Number of synonyms cached
        """
        synonyms = self.db.query(MasterSynonym).filter(
            MasterSynonym.is_active == True
        ).all()

        self._synonym_cache = {
            s.synonym_normalized.lower(): s.master_id
            for s in synonyms if s.synonym_normalized
        }
        self._cache_built = True

        logger.info(f"Built synonym cache with {len(self._synonym_cache)} entries")
        return len(self._synonym_cache)

    def find_by_synonym(self, text: str) -> Optional[MasterWorkItem]:
        """
        Find master item by synonym match.

        Args:
            text: Text to search for

        Returns:
            MasterWorkItem if found, None otherwise
        """
        if not self._cache_built:
            self.build_synonym_cache()

        text_lower = text.lower().strip()

        # Check cache first
        if text_lower in self._synonym_cache:
            master_id = self._synonym_cache[text_lower]
            return self.db.query(MasterWorkItem).filter(
                MasterWorkItem.master_id == master_id
            ).first()

        # Fallback to DB query
        synonym = self.db.query(MasterSynonym).filter(
            MasterSynonym.synonym_normalized == text_lower,
            MasterSynonym.is_active == True
        ).first()

        if synonym:
            # Update cache
            self._synonym_cache[text_lower] = synonym.master_id
            return synonym.master_item

        return None

    def add_synonym(
        self,
        master_id: int,
        synonym_text: str,
        synonym_type: str = 'alias',
        added_by: Optional[int] = None
    ) -> MasterSynonym:
        """
        Add a new synonym for a master item.

        Args:
            master_id: ID of the master work item
            synonym_text: The synonym text
            synonym_type: Type of synonym (alias, abbreviation, regional, english)
            added_by: User ID who added this synonym

        Returns:
            Created MasterSynonym instance
        """
        normalized = synonym_text.lower().strip()

        # Check for duplicates
        existing = self.db.query(MasterSynonym).filter(
            MasterSynonym.synonym_normalized == normalized,
            MasterSynonym.is_active == True
        ).first()

        if existing:
            raise ValueError(f"Synonym '{synonym_text}' already exists for master_id {existing.master_id}")

        synonym = MasterSynonym(
            master_id=master_id,
            synonym_text=synonym_text,
            synonym_normalized=normalized,
            synonym_type=synonym_type,
            added_by=added_by
        )
        self.db.add(synonym)
        self.db.commit()
        self.db.refresh(synonym)

        # Update cache
        self._synonym_cache[normalized] = master_id

        logger.info(f"Added synonym '{synonym_text}' for master_id {master_id}")
        return synonym

    def get_synonyms(self, master_id: int) -> List[MasterSynonym]:
        """
        Get all synonyms for a master item.

        Args:
            master_id: ID of the master work item

        Returns:
            List of MasterSynonym instances
        """
        return self.db.query(MasterSynonym).filter(
            MasterSynonym.master_id == master_id,
            MasterSynonym.is_active == True
        ).all()

    def get_synonym_by_id(self, synonym_id: int) -> Optional[MasterSynonym]:
        """Get a synonym by its ID."""
        return self.db.query(MasterSynonym).filter(
            MasterSynonym.synonym_id == synonym_id
        ).first()

    def delete_synonym(self, synonym_id: int) -> bool:
        """
        Soft delete a synonym.

        Args:
            synonym_id: ID of the synonym to delete

        Returns:
            True if deleted, False if not found
        """
        synonym = self.db.query(MasterSynonym).filter(
            MasterSynonym.synonym_id == synonym_id
        ).first()

        if synonym:
            synonym.is_active = False
            self.db.commit()

            # Remove from cache
            if synonym.synonym_normalized and synonym.synonym_normalized.lower() in self._synonym_cache:
                del self._synonym_cache[synonym.synonym_normalized.lower()]

            logger.info(f"Deleted synonym id={synonym_id}")
            return True

        return False

    def get_all_synonyms(
        self,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False
    ) -> List[MasterSynonym]:
        """
        Get all synonyms with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_inactive: Include inactive synonyms

        Returns:
            List of MasterSynonym instances
        """
        query = self.db.query(MasterSynonym)

        if not include_inactive:
            query = query.filter(MasterSynonym.is_active == True)

        return query.offset(skip).limit(limit).all()

    def get_statistics(self) -> Dict:
        """Get synonym statistics."""
        total = self.db.query(MasterSynonym).count()
        active = self.db.query(MasterSynonym).filter(
            MasterSynonym.is_active == True
        ).count()

        by_type = self.db.query(
            MasterSynonym.synonym_type,
            self.db.query(MasterSynonym).filter(
                MasterSynonym.synonym_type == MasterSynonym.synonym_type
            ).count()
        ).group_by(MasterSynonym.synonym_type).all()

        return {
            "total": total,
            "active": active,
            "inactive": total - active,
            "cached": len(self._synonym_cache),
            "by_type": {t: c for t, c in by_type} if by_type else {}
        }


# Module-level instance for singleton pattern
_synonym_service: Optional[SynonymService] = None


def get_synonym_service(db: Session) -> SynonymService:
    """
    Get or create SynonymService instance.

    Note: This creates a new instance per request since DB session is request-scoped.
    """
    return SynonymService(db)
