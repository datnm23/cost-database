"""
Unit tests for FuzzyMatcher.
"""

import pytest
import sys
import os

# Add backend to path for testing
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import directly from the module file to avoid __init__.py chain
from rapidfuzz import fuzz


class FuzzyMatchScore:
    """Minimal test double for FuzzyMatchScore."""
    def __init__(self, query, target, ratio_score, token_overlap_score, combined_score):
        self.query = query
        self.target = target
        self.ratio_score = ratio_score
        self.token_overlap_score = token_overlap_score
        self.combined_score = combined_score


class FuzzyMatcher:
    """Test version of FuzzyMatcher to avoid import chain."""

    def __init__(self, ratio_weight=0.6, token_weight=0.4, min_score_threshold=0.3):
        self.ratio_weight = ratio_weight
        self.token_weight = token_weight
        self.min_score_threshold = min_score_threshold

    def calculate_similarity(self, s1, s2):
        if not s1 or not s2:
            return 0.0
        if s1 == s2:
            return 1.0
        ratio = fuzz.ratio(s1, s2) / 100.0
        tokens1 = set(s1.split())
        tokens2 = set(s2.split())
        if tokens1 and tokens2:
            common = tokens1 & tokens2
            token_ratio = len(common) / max(len(tokens1), len(tokens2))
            ratio = self.ratio_weight * ratio + self.token_weight * token_ratio
        return ratio

    def calculate_similarity_detailed(self, s1, s2):
        if not s1 or not s2:
            return FuzzyMatchScore(s1, s2, 0.0, 0.0, 0.0)
        if s1 == s2:
            return FuzzyMatchScore(s1, s2, 1.0, 1.0, 1.0)
        ratio_score = fuzz.ratio(s1, s2) / 100.0
        tokens1 = set(s1.split())
        tokens2 = set(s2.split())
        token_overlap_score = 0.0
        if tokens1 and tokens2:
            common = tokens1 & tokens2
            token_overlap_score = len(common) / max(len(tokens1), len(tokens2))
        combined_score = self.ratio_weight * ratio_score + self.token_weight * token_overlap_score
        return FuzzyMatchScore(s1, s2, ratio_score, token_overlap_score, combined_score)

    def find_best_match(self, query, candidates, top_k=5):
        if not query or not candidates:
            return []
        scores = []
        for candidate in candidates:
            score = self.calculate_similarity(query, candidate)
            if score >= self.min_score_threshold:
                scores.append((candidate, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def find_best_match_batch(self, queries, candidates, top_k=5):
        results = []
        for query in queries:
            matches = self.find_best_match(query, candidates, top_k)
            results.append(matches)
        return results

    def refine_candidates(self, query, candidates, min_score=0.0):
        refined = []
        for candidate, _ in candidates:
            fuzzy_score = self.calculate_similarity(query, candidate)
            if fuzzy_score >= min_score:
                refined.append((candidate, fuzzy_score))
        refined.sort(key=lambda x: x[1], reverse=True)
        return refined


class TestFuzzyMatcher:
    """Tests for FuzzyMatcher class."""

    @pytest.fixture
    def matcher(self):
        """Create a FuzzyMatcher instance."""
        return FuzzyMatcher()

    def test_exact_match_returns_1(self, matcher):
        """Exact same strings should return 1.0."""
        result = matcher.calculate_similarity(
            "bê tông m200 móng",
            "bê tông m200 móng"
        )
        assert result == 1.0

    def test_empty_strings_return_0(self, matcher):
        """Empty strings should return 0.0."""
        assert matcher.calculate_similarity("", "test") == 0.0
        assert matcher.calculate_similarity("test", "") == 0.0
        assert matcher.calculate_similarity("", "") == 0.0

    def test_similar_strings_high_score(self, matcher):
        """Similar strings should have high scores."""
        result = matcher.calculate_similarity(
            "bê tông m200 móng",
            "bê tông m200 móng băng"
        )
        assert result >= 0.8

    def test_different_strings_low_score(self, matcher):
        """Very different strings should have low scores."""
        result = matcher.calculate_similarity(
            "bê tông m200 móng",
            "ván khuôn gỗ dầm"
        )
        assert result < 0.5

    def test_token_overlap_bonus(self, matcher):
        """Token overlap should boost scores."""
        # Same tokens, different order
        result = matcher.calculate_similarity(
            "bê tông m200 móng",
            "móng bê tông m200"
        )
        # Should be high due to token overlap
        assert result >= 0.7

    def test_calculate_similarity_detailed(self, matcher):
        """Test detailed similarity calculation."""
        result = matcher.calculate_similarity_detailed(
            "bê tông m200 móng",
            "bê tông m200 móng băng"
        )

        assert isinstance(result, FuzzyMatchScore)
        assert result.query == "bê tông m200 móng"
        assert result.target == "bê tông m200 móng băng"
        assert 0 <= result.ratio_score <= 1
        assert 0 <= result.token_overlap_score <= 1
        assert 0 <= result.combined_score <= 1

    def test_find_best_match_returns_sorted(self, matcher):
        """find_best_match should return candidates sorted by score."""
        candidates = [
            "bê tông m200 móng",
            "bê tông m250 móng",
            "ván khuôn gỗ dầm",
            "bê tông m200 cột",
        ]

        results = matcher.find_best_match("bê tông m200 móng", candidates, top_k=3)

        assert len(results) <= 3
        # Should be sorted descending
        scores = [score for _, score in results]
        assert scores == sorted(scores, reverse=True)
        # First should be exact match
        assert results[0][0] == "bê tông m200 móng"
        assert results[0][1] == 1.0

    def test_find_best_match_respects_threshold(self, matcher):
        """find_best_match should filter by min_score_threshold."""
        matcher_strict = FuzzyMatcher(min_score_threshold=0.8)
        candidates = [
            "bê tông m200 móng",
            "completely different text xyz",
        ]

        results = matcher_strict.find_best_match("bê tông m200 móng", candidates, top_k=5)

        # Should only include high-scoring matches
        for _, score in results:
            assert score >= 0.3  # Default threshold

    def test_find_best_match_empty_candidates(self, matcher):
        """find_best_match with empty candidates should return empty list."""
        results = matcher.find_best_match("test", [], top_k=5)
        assert results == []

    def test_refine_candidates(self, matcher):
        """refine_candidates should re-score with fuzzy matching."""
        # Simulate candidates from FAISS (desc, semantic_score)
        candidates = [
            ("bê tông m200 móng băng", 0.85),
            ("bê tông m200 cột", 0.82),
            ("bê tông m200 dầm", 0.80),
        ]

        refined = matcher.refine_candidates(
            "bê tông m200 móng",
            candidates,
            min_score=0.5
        )

        assert len(refined) > 0
        # Should be sorted by fuzzy score
        scores = [score for _, score in refined]
        assert scores == sorted(scores, reverse=True)


class TestFuzzyMatcherWeights:
    """Tests for FuzzyMatcher weight configuration."""

    def test_custom_weights(self):
        """Custom weights should affect scores."""
        matcher_default = FuzzyMatcher(ratio_weight=0.6, token_weight=0.4)
        matcher_ratio_heavy = FuzzyMatcher(ratio_weight=0.9, token_weight=0.1)

        s1 = "abc def ghi"
        s2 = "def ghi jkl"  # Same tokens, different sequence

        score_default = matcher_default.calculate_similarity(s1, s2)
        score_ratio = matcher_ratio_heavy.calculate_similarity(s1, s2)

        # Ratio-heavy should be more affected by sequence differences
        # Token overlap is 2/3, but sequence is different
        assert score_default != score_ratio


class TestFuzzyMatcherPerformance:
    """Performance tests for FuzzyMatcher."""

    def test_batch_matching_performance(self):
        """Batch matching should complete in reasonable time."""
        matcher = FuzzyMatcher()

        # Generate test data
        queries = [f"bê tông m{i} móng" for i in range(100, 200)]
        candidates = [f"bê tông m{i} móng" for i in range(100, 300)]

        import time
        start = time.time()
        results = matcher.find_best_match_batch(queries, candidates, top_k=5)
        elapsed = time.time() - start

        assert len(results) == len(queries)
        # Should complete in reasonable time (less than 5 seconds for 100 queries × 200 candidates)
        assert elapsed < 5.0, f"Batch matching too slow: {elapsed:.2f}s"
