"""
Rule-based SEC Code Classifier (FR-CL-04)
Fallback when ML model is not available
"""
import re
import logging
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
import json

from app.models.sec_code import SECCode

logger = logging.getLogger(__name__)


class RuleBasedClassifier:
    """
    Simple keyword-based classifier for SEC codes
    Used as fallback when ML model is unavailable
    """

    def __init__(self, db: Session):
        self.db = db
        self.sec_keywords = {}
        self._load_sec_codes()

    def _load_sec_codes(self):
        """Load SEC codes and their keywords from database"""
        try:
            sec_codes = self.db.query(SECCode).filter(SECCode.is_active == True).all()

            for sec in sec_codes:
                # Parse keywords from JSON
                keywords = []
                if sec.keywords:
                    try:
                        keywords = json.loads(sec.keywords) if isinstance(sec.keywords, str) else sec.keywords
                    except Exception as e:
                        logger.warning(f"Failed to parse keywords for {sec.sec_code}: {e}")
                        keywords = []

                # Combine all searchable text
                search_terms = []

                # Add Vietnamese name
                if sec.sec_name_vi:
                    search_terms.append(sec.sec_name_vi.lower())

                # Add English name
                if sec.sec_name_en:
                    search_terms.append(sec.sec_name_en.lower())

                # Add description
                if sec.description:
                    search_terms.append(sec.description.lower())

                # Add keywords
                search_terms.extend([k.lower() for k in keywords])

                self.sec_keywords[sec.sec_code] = {
                    'terms': search_terms,
                    'name': sec.sec_name_vi or sec.sec_name_en,
                }

            logger.info(f"Loaded {len(self.sec_keywords)} SEC codes for rule-based matching")

        except Exception as e:
            logger.error(f"Error loading SEC codes: {e}")
            self.sec_keywords = {}

    def classify(
        self,
        description: str,
        top_k: int = 3
    ) -> List[Tuple[str, float]]:
        """
        Classify description using keyword matching

        Args:
            description: Text to classify
            top_k: Number of results to return

        Returns:
            List of (sec_code, confidence_score) tuples
        """
        if not description or not description.strip():
            return []

        description_lower = description.lower().strip()

        # Calculate match scores for each SEC code
        scores = {}

        for sec_code, data in self.sec_keywords.items():
            score = 0
            matches = 0

            for term in data['terms']:
                if not term:
                    continue

                # Exact match (case insensitive)
                if term in description_lower:
                    # Longer matches get higher scores
                    match_score = len(term) / max(len(description_lower), 1)
                    score += match_score * 100
                    matches += 1

                # Word boundary match (more precise)
                pattern = r'\b' + re.escape(term) + r'\b'
                if re.search(pattern, description_lower):
                    score += 20  # Bonus for word boundary match

            # Normalize score based on number of terms
            if matches > 0:
                # Average score, capped at 95% (rule-based never 100% confident)
                normalized_score = min(score / matches, 95.0)
                scores[sec_code] = normalized_score

        # Sort by score and return top k
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # FR-CL-03: Return top 3 (or top_k)
        top_results = sorted_results[:top_k]

        if top_results:
            logger.debug(
                f"Rule-based classification for '{description[:50]}...': "
                f"Top match = {top_results[0][0]} ({top_results[0][1]:.1f}%)"
            )

        return top_results


def get_rule_based_classifier(db: Session) -> RuleBasedClassifier:
    """Get or create rule-based classifier instance"""
    return RuleBasedClassifier(db)
