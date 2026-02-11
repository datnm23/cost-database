"""
SEC Code v4.0 Mapper Service

Maps legacy SEC-xx codes to v4.0 3-level codes (PREFIX.GROUP.TYPE)
and provides fuzzy matching against the sec_codes_v4 reference table.
"""
import logging
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.sec_code_v4 import SECCodeV4

logger = logging.getLogger(__name__)


# Legacy SEC → v4.0 discipline mapping
LEGACY_TO_V4_DISCIPLINE = {
    'SEC-00': 'PM',
    'SEC-01': 'CV',
    'SEC-01-01': 'CV',
    'SEC-01-02': 'CV',
    'SEC-01-03': 'CV',
    'SEC-02': 'CV',
    'SEC-02-01': 'CV',
    'SEC-02-02': 'CV',
    'SEC-02-03': 'CV',
    'SEC-02-04': 'CV',
    'SEC-02-05': 'CV',
    'SEC-02-06': 'CV',
    'SEC-03': 'AR',
    'SEC-03-01': 'AR',
    'SEC-03-02': 'AR',
    'SEC-03-03': 'AR',
    'SEC-03-04': 'AR',
    'SEC-03-05': 'AR',
    'SEC-03-06': 'AR',
    'SEC-04': 'EL',
    'SEC-04-01': 'EL',
    'SEC-04-02': 'PL',
    'SEC-04-03': 'ME',
    'SEC-04-04': 'FP',
    'SEC-05': 'EX',
    'SEC-05-01': 'EX',
    'SEC-05-02': 'EX',
    'SEC-05-03': 'LA',
}


class SECCodeV4Mapper:
    """Maps legacy SEC codes to v4.0 and provides fuzzy matching."""

    def __init__(self, db: Session):
        self.db = db

    def legacy_to_discipline(self, sec_code: str) -> str:
        """
        Convert legacy SEC code to v4.0 discipline.

        Args:
            sec_code: Legacy code like 'SEC-02' or 'SEC-04-01'

        Returns:
            Discipline code like 'CV', 'AR', 'EL', etc.
        """
        if sec_code in LEGACY_TO_V4_DISCIPLINE:
            return LEGACY_TO_V4_DISCIPLINE[sec_code]

        # Try prefix match
        for prefix_len in [10, 6, 3]:
            prefix = sec_code[:prefix_len]
            if prefix in LEGACY_TO_V4_DISCIPLINE:
                return LEGACY_TO_V4_DISCIPLINE[prefix]

        return 'CV'  # Default

    def get_full_mapping(self) -> dict:
        """Return the complete legacy→v4 mapping dict."""
        return dict(LEGACY_TO_V4_DISCIPLINE)

    def find_matching_codes(
        self,
        description: str,
        table_type: Optional[str] = None,
        group_code: Optional[str] = None,
        limit: int = 10,
    ) -> List[Tuple[SECCodeV4, float]]:
        """
        Find v4.0 reference codes matching a description using keyword search.

        Args:
            description: Work description to match
            table_type: Filter by table type (A/M/L/E)
            group_code: Filter by group code (CONC/RBAR/PIPE...)
            limit: Max results

        Returns:
            List of (SECCodeV4, score) tuples sorted by relevance
        """
        query = self.db.query(SECCodeV4).filter(SECCodeV4.is_active == True)

        if table_type:
            query = query.filter(SECCodeV4.table_type == table_type)
        if group_code:
            query = query.filter(SECCodeV4.group_code == group_code)

        candidates = query.all()
        if not candidates:
            return []

        desc_lower = description.lower()
        scored = []

        for code in candidates:
            score = 0.0

            # Match against Vietnamese name
            if code.name_vi and code.name_vi.lower() in desc_lower:
                score += 0.5
            elif code.name_vi:
                # Partial word overlap
                name_words = set(code.name_vi.lower().split())
                desc_words = set(desc_lower.split())
                overlap = name_words & desc_words
                if overlap:
                    score += 0.3 * len(overlap) / len(name_words)

            # Match against keywords
            if code.keywords_vi:
                import json
                try:
                    kws = json.loads(code.keywords_vi)
                    for kw in kws:
                        if kw.lower() in desc_lower:
                            score += 0.2
                except (json.JSONDecodeError, TypeError):
                    pass

            if score > 0:
                scored.append((code, round(score, 3)))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit]

    def list_codes(
        self,
        table_type: Optional[str] = None,
        group_code: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SECCodeV4]:
        """List v4.0 reference codes with filters."""
        query = self.db.query(SECCodeV4).filter(SECCodeV4.is_active == True)

        if table_type:
            query = query.filter(SECCodeV4.table_type == table_type)
        if group_code:
            query = query.filter(SECCodeV4.group_code == group_code)

        return query.order_by(SECCodeV4.code).offset(offset).limit(limit).all()


def get_sec_code_v4_mapper(db: Session) -> SECCodeV4Mapper:
    """Factory function."""
    return SECCodeV4Mapper(db)
