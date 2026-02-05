"""
Header Detector Service

Multi-heuristic header row detection for BOQ Excel files.
Uses weighted scoring to identify the header row.
"""
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from .keyword_dictionary import get_keyword_dictionary, KeywordDictionary

logger = logging.getLogger(__name__)


@dataclass
class HeaderDetectionResult:
    """Result of header detection."""
    header_row: int
    confidence_score: float  # 0-100
    keyword_score: float
    text_ratio_score: float
    density_score: float
    column_type_hints: Dict[str, int]


class HeaderDetector:
    """
    Multi-heuristic header row detector.

    Scoring formula (normalized 0-100):
        total_score = (keyword_score × 0.40) +
                      (text_ratio_score × 0.25) +
                      (density_score × 0.20) +
                      (consistency_score × 0.15)
    """

    # Weights for different heuristics
    KEYWORD_WEIGHT = 0.40
    TEXT_RATIO_WEIGHT = 0.25
    DENSITY_WEIGHT = 0.20
    CONSISTENCY_WEIGHT = 0.15

    # Maximum rows to scan
    MAX_ROWS_TO_SCAN = 25

    # Minimum score to consider as valid header
    MIN_CONFIDENCE = 20.0

    def __init__(self, keyword_dict: Optional[KeywordDictionary] = None):
        """
        Initialize header detector.

        Args:
            keyword_dict: Optional keyword dictionary instance
        """
        self.keyword_dict = keyword_dict or get_keyword_dictionary()

    def detect(self, df: pd.DataFrame) -> HeaderDetectionResult:
        """
        Detect header row in DataFrame.

        Args:
            df: DataFrame with header=None (raw data)

        Returns:
            HeaderDetectionResult with detection details
        """
        if df.empty:
            return HeaderDetectionResult(
                header_row=0,
                confidence_score=0.0,
                keyword_score=0.0,
                text_ratio_score=0.0,
                density_score=0.0,
                column_type_hints={}
            )

        num_rows = min(self.MAX_ROWS_TO_SCAN, len(df))
        num_cols = len(df.columns)

        # Analyze each row
        row_scores: List[Tuple[int, float, Dict[str, int]]] = []

        for row_idx in range(num_rows):
            row = df.iloc[row_idx]
            cells = [str(v) if pd.notna(v) else None for v in row]

            # Calculate individual scores
            keyword_score, column_hints = self._calculate_keyword_score(cells)
            text_ratio = self._calculate_text_ratio(cells)
            density = self._calculate_density(cells)

            # Calculate consistency score
            consistency = self._calculate_consistency(df, row_idx, cells)

            # Combine scores
            total = (
                keyword_score * self.KEYWORD_WEIGHT +
                text_ratio * self.TEXT_RATIO_WEIGHT +
                density * self.DENSITY_WEIGHT +
                consistency * self.CONSISTENCY_WEIGHT
            )

            row_scores.append((row_idx, total, column_hints))

            logger.debug(
                f"Row {row_idx}: keyword={keyword_score:.1f}, text={text_ratio:.1f}, "
                f"density={density:.1f}, consistency={consistency:.1f}, total={total:.1f}"
            )

        # Find best row
        if not row_scores:
            return HeaderDetectionResult(
                header_row=0,
                confidence_score=0.0,
                keyword_score=0.0,
                text_ratio_score=0.0,
                density_score=0.0,
                column_type_hints={}
            )

        # Sort by score
        row_scores.sort(key=lambda x: x[1], reverse=True)

        best_row, best_score, best_hints = row_scores[0]

        # Calculate confidence based on gap to second-best
        if len(row_scores) > 1:
            second_score = row_scores[1][1]
            score_gap = best_score - second_score
            # Confidence increases with larger gap
            confidence = min(100.0, best_score + score_gap * 0.5)
        else:
            confidence = best_score

        # Recalculate component scores for best row
        best_row_data = df.iloc[best_row]
        best_cells = [str(v) if pd.notna(v) else None for v in best_row_data]

        keyword_score, _ = self._calculate_keyword_score(best_cells)
        text_ratio = self._calculate_text_ratio(best_cells)
        density = self._calculate_density(best_cells)

        logger.info(f"Detected header at row {best_row} with confidence {confidence:.1f}")

        return HeaderDetectionResult(
            header_row=best_row,
            confidence_score=confidence,
            keyword_score=keyword_score,
            text_ratio_score=text_ratio,
            density_score=density,
            column_type_hints=best_hints
        )

    def _calculate_keyword_score(self, cells: List[Optional[str]]) -> Tuple[float, Dict[str, int]]:
        """
        Calculate keyword-based score for a row.

        Returns normalized score (0-100) and column type hints.
        """
        total_weight, hints = self.keyword_dict.score_row(cells)

        # Normalize: assume max reasonable score is ~50 (5 keywords × 5 weight + 10 bonus)
        # This gives us 0-100 range
        normalized = min(100.0, total_weight * 2.0)

        return normalized, hints

    def _calculate_text_ratio(self, cells: List[Optional[str]]) -> float:
        """
        Calculate text-to-numeric ratio score.

        Headers tend to have mostly text, not numbers.
        Returns normalized score (0-100).
        """
        text_count = 0
        numeric_count = 0

        for cell in cells:
            if cell is None:
                continue
            cell_clean = cell.strip()
            if not cell_clean:
                continue

            # Check if primarily text or numeric
            if self._is_primarily_text(cell_clean):
                text_count += 1
            elif self._is_primarily_numeric(cell_clean):
                numeric_count += 1

        total = text_count + numeric_count
        if total == 0:
            return 0.0

        # Score based on text ratio
        text_ratio = text_count / total
        return text_ratio * 100.0

    def _calculate_density(self, cells: List[Optional[str]]) -> float:
        """
        Calculate non-null cell density.

        Headers tend to have high density (most columns have headers).
        Returns normalized score (0-100).
        """
        non_null = 0
        total = len(cells)

        if total == 0:
            return 0.0

        for cell in cells:
            if cell is not None and cell.strip():
                non_null += 1

        return (non_null / total) * 100.0

    def _calculate_consistency(
        self,
        df: pd.DataFrame,
        row_idx: int,
        cells: List[Optional[str]]
    ) -> float:
        """
        Calculate consistency score.

        Good headers have text in columns that are mostly numeric below.
        Returns normalized score (0-100).
        """
        if row_idx >= len(df) - 3:  # Need at least 3 rows below to analyze
            return 50.0  # Neutral score

        consistency_points = 0
        analyzed_cols = 0

        for col_idx, cell in enumerate(cells):
            if cell is None or not cell.strip():
                continue

            # Check if this cell is text
            if not self._is_primarily_text(cell):
                continue

            analyzed_cols += 1

            # Check if column below is mostly numeric
            numeric_below = 0
            rows_checked = min(10, len(df) - row_idx - 1)

            for check_row in range(row_idx + 1, row_idx + 1 + rows_checked):
                val = df.iloc[check_row, col_idx]
                if pd.notna(val) and self._is_primarily_numeric(str(val)):
                    numeric_below += 1

            if rows_checked > 0:
                ratio = numeric_below / rows_checked
                if ratio > 0.5:  # More than half are numeric
                    consistency_points += 1

        if analyzed_cols == 0:
            return 50.0  # Neutral

        return (consistency_points / analyzed_cols) * 100.0

    def _is_primarily_text(self, value: str) -> bool:
        """Check if value is primarily text (contains letters)."""
        if not value:
            return False

        letter_count = sum(1 for c in value if c.isalpha())
        return letter_count > 0 and letter_count >= len(value.replace(' ', '')) * 0.3

    def _is_primarily_numeric(self, value: str) -> bool:
        """Check if value is primarily numeric."""
        if not value:
            return False

        # Remove common numeric formatting
        cleaned = value.replace(',', '').replace('.', '').replace(' ', '').replace('-', '')

        if not cleaned:
            return False

        digit_count = sum(1 for c in cleaned if c.isdigit())
        return digit_count > 0 and digit_count >= len(cleaned) * 0.7


# Module-level singleton
_header_detector: Optional[HeaderDetector] = None


def get_header_detector() -> HeaderDetector:
    """Get or create singleton HeaderDetector instance."""
    global _header_detector
    if _header_detector is None:
        _header_detector = HeaderDetector()
    return _header_detector
