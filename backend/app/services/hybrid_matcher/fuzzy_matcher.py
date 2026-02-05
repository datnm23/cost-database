"""
Fuzzy Matcher using RapidFuzz

10x faster than Python's difflib.SequenceMatcher while maintaining
the same token overlap bonus logic from the original implementation.
"""

import logging
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

from rapidfuzz import fuzz
from rapidfuzz.distance import Levenshtein

logger = logging.getLogger(__name__)


@dataclass
class FuzzyMatchScore:
    """Result of fuzzy matching between two strings"""
    query: str
    target: str
    ratio_score: float  # 0-1, normalized similarity
    token_overlap_score: float  # 0-1, token-based bonus
    combined_score: float  # Weighted combination


class FuzzyMatcher:
    """
    Fast fuzzy string matching using RapidFuzz.

    Preserves the existing weighted scoring logic:
    - 60% sequence similarity (using RapidFuzz ratio)
    - 40% token overlap bonus
    """

    def __init__(
        self,
        ratio_weight: float = 0.6,
        token_weight: float = 0.4,
        min_score_threshold: float = 0.3
    ):
        """
        Initialize FuzzyMatcher.

        Args:
            ratio_weight: Weight for sequence similarity (default 0.6)
            token_weight: Weight for token overlap (default 0.4)
            min_score_threshold: Minimum score to consider (default 0.3)
        """
        self.ratio_weight = ratio_weight
        self.token_weight = token_weight
        self.min_score_threshold = min_score_threshold

    def calculate_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate weighted similarity between two strings.

        Mirrors the original _calculate_similarity() logic but uses
        RapidFuzz for 10x speedup.

        Args:
            s1: First string (query)
            s2: Second string (target)

        Returns:
            Combined similarity score (0-1)
        """
        if not s1 or not s2:
            return 0.0

        # Exact match
        if s1 == s2:
            return 1.0

        # RapidFuzz ratio (equivalent to SequenceMatcher.ratio())
        # fuzz.ratio returns 0-100, normalize to 0-1
        ratio = fuzz.ratio(s1, s2) / 100.0

        # Token-based bonus for construction terms
        tokens1 = set(s1.split())
        tokens2 = set(s2.split())

        if tokens1 and tokens2:
            common = tokens1 & tokens2
            token_ratio = len(common) / max(len(tokens1), len(tokens2))
            # Weighted average (same as original)
            ratio = self.ratio_weight * ratio + self.token_weight * token_ratio

        return ratio

    def calculate_similarity_detailed(self, s1: str, s2: str) -> FuzzyMatchScore:
        """
        Calculate similarity with detailed breakdown.

        Args:
            s1: First string (query)
            s2: Second string (target)

        Returns:
            FuzzyMatchScore with component scores
        """
        if not s1 or not s2:
            return FuzzyMatchScore(
                query=s1,
                target=s2,
                ratio_score=0.0,
                token_overlap_score=0.0,
                combined_score=0.0
            )

        # Exact match
        if s1 == s2:
            return FuzzyMatchScore(
                query=s1,
                target=s2,
                ratio_score=1.0,
                token_overlap_score=1.0,
                combined_score=1.0
            )

        # RapidFuzz ratio
        ratio_score = fuzz.ratio(s1, s2) / 100.0

        # Token overlap
        tokens1 = set(s1.split())
        tokens2 = set(s2.split())

        token_overlap_score = 0.0
        if tokens1 and tokens2:
            common = tokens1 & tokens2
            token_overlap_score = len(common) / max(len(tokens1), len(tokens2))

        # Combined score
        combined_score = (
            self.ratio_weight * ratio_score +
            self.token_weight * token_overlap_score
        )

        return FuzzyMatchScore(
            query=s1,
            target=s2,
            ratio_score=ratio_score,
            token_overlap_score=token_overlap_score,
            combined_score=combined_score
        )

    def find_best_match(
        self,
        query: str,
        candidates: List[str],
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Find best matches from a list of candidates.

        Args:
            query: Query string to match
            candidates: List of candidate strings
            top_k: Number of top matches to return

        Returns:
            List of (candidate, score) tuples, sorted by score descending
        """
        if not query or not candidates:
            return []

        scores = []
        for candidate in candidates:
            score = self.calculate_similarity(query, candidate)
            if score >= self.min_score_threshold:
                scores.append((candidate, score))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)

        return scores[:top_k]

    def find_best_match_batch(
        self,
        queries: List[str],
        candidates: List[str],
        top_k: int = 5
    ) -> List[List[Tuple[str, float]]]:
        """
        Find best matches for multiple queries.

        Args:
            queries: List of query strings
            candidates: List of candidate strings
            top_k: Number of top matches per query

        Returns:
            List of match results for each query
        """
        results = []
        for query in queries:
            matches = self.find_best_match(query, candidates, top_k)
            results.append(matches)
        return results

    def refine_candidates(
        self,
        query: str,
        candidates: List[Tuple[str, float]],
        min_score: float = 0.0
    ) -> List[Tuple[str, float]]:
        """
        Refine a list of candidates with fuzzy scoring.

        Used in Tier 3 to re-score candidates from FAISS search.

        Args:
            query: Query string
            candidates: List of (candidate, semantic_score) tuples from FAISS
            min_score: Minimum fuzzy score threshold

        Returns:
            Re-scored and filtered candidates
        """
        refined = []
        for candidate, _ in candidates:
            fuzzy_score = self.calculate_similarity(query, candidate)
            if fuzzy_score >= min_score:
                refined.append((candidate, fuzzy_score))

        # Sort by fuzzy score descending
        refined.sort(key=lambda x: x[1], reverse=True)
        return refined


# Module-level singleton
_fuzzy_matcher: Optional[FuzzyMatcher] = None


def get_fuzzy_matcher() -> FuzzyMatcher:
    """Get or create singleton FuzzyMatcher instance."""
    global _fuzzy_matcher
    if _fuzzy_matcher is None:
        _fuzzy_matcher = FuzzyMatcher()
    return _fuzzy_matcher
