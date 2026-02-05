"""
Sheet Filter Service

Filters and prioritizes Excel sheets for BOQ processing.
Skips non-data sheets (Summary, Preliminary, Terms, Notes, Cover).
"""
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class SheetInfo:
    """Information about a sheet."""
    name: str
    index: int
    priority_score: float
    should_skip: bool
    skip_reason: Optional[str] = None


class SheetFilter:
    """
    Filter and prioritize Excel sheets for BOQ processing.

    Uses regex patterns to:
    1. Skip non-data sheets (summary, terms, cover, etc.)
    2. Prioritize BOQ-related sheets
    """

    # Patterns for sheets to skip (case-insensitive)
    SKIP_PATTERNS: List[Tuple[str, str]] = [
        (r'preliminary|prelim', 'Preliminary sheet'),
        (r'summary|tổng hợp|tong\s*hop|總表|总表', 'Summary sheet'),
        (r'^terms$|terms?\s*(and|&)?\s*conditions?', 'Terms and conditions'),
        (r'cover\s*page?|bìa|bia', 'Cover page'),
        (r'instruction|hướng dẫn|huong\s*dan', 'Instructions'),
        (r'^notes?$|ghi chú|ghi\s*chu', 'Notes sheet'),
        (r'appendix|phụ lục|phu\s*luc', 'Appendix'),
        (r'^index$|mục lục|muc\s*luc', 'Index sheet'),
        (r'^sheet\d*$', 'Default sheet name'),
        (r'^table\s*of\s*contents?$|^toc$', 'Table of contents'),
        (r'change\s*log|revision', 'Change log'),
        (r'^blank$|^empty$', 'Empty sheet'),
    ]

    # Patterns for prioritizing sheets (higher score = higher priority)
    PRIORITY_PATTERNS: List[Tuple[str, float]] = [
        (r'^boq$', 10.0),
        (r'^boq\s*\d+$', 9.5),
        (r'boq\s*-?\s*\d*', 9.0),
        (r'bill\s*(of)?\s*quantit', 9.0),
        (r'xây\s*dựng|xay\s*dung|^xd$', 8.0),
        (r'm\s*&\s*e|mep|cơ\s*điện|co\s*dien', 8.5),
        (r'điện|dien|electrical', 8.0),
        (r'nước|nuoc|plumbing|water', 8.0),
        (r'pccc|fire\s*protect|phòng\s*cháy', 8.0),
        (r'hvac|điều\s*hòa|dieu\s*hoa|air\s*con', 8.0),
        (r'work\s*item|hạng\s*mục|hang\s*muc', 8.0),
        (r'detail|chi\s*tiết|chi\s*tiet', 7.0),
        (r'schedule|bảng|bang', 6.0),
        (r'main|chính|chinh', 5.0),
        (r'data|dữ\s*liệu|du\s*lieu', 4.0),
    ]

    def __init__(self):
        """Initialize with compiled patterns."""
        self._skip_patterns = [
            (re.compile(pattern, re.IGNORECASE | re.UNICODE), reason)
            for pattern, reason in self.SKIP_PATTERNS
        ]
        self._priority_patterns = [
            (re.compile(pattern, re.IGNORECASE | re.UNICODE), score)
            for pattern, score in self.PRIORITY_PATTERNS
        ]

    def should_skip(self, sheet_name: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a sheet should be skipped.

        Args:
            sheet_name: Name of the sheet

        Returns:
            Tuple of (should_skip, reason)
        """
        if not sheet_name:
            return True, "Empty sheet name"

        name_clean = sheet_name.strip()

        for pattern, reason in self._skip_patterns:
            if pattern.search(name_clean):
                return True, reason

        return False, None

    def get_priority(self, sheet_name: str) -> float:
        """
        Get priority score for a sheet.

        Args:
            sheet_name: Name of the sheet

        Returns:
            Priority score (higher = more likely to be BOQ data)
        """
        if not sheet_name:
            return 0.0

        name_clean = sheet_name.strip()
        max_score = 1.0  # Default score for unmatched sheets

        for pattern, score in self._priority_patterns:
            if pattern.search(name_clean):
                max_score = max(max_score, score)

        return max_score

    def analyze_sheet(self, sheet_name: str, index: int) -> SheetInfo:
        """
        Analyze a single sheet.

        Args:
            sheet_name: Name of the sheet
            index: Sheet index in workbook

        Returns:
            SheetInfo with analysis results
        """
        skip, reason = self.should_skip(sheet_name)
        priority = 0.0 if skip else self.get_priority(sheet_name)

        return SheetInfo(
            name=sheet_name,
            index=index,
            priority_score=priority,
            should_skip=skip,
            skip_reason=reason
        )

    def filter_sheets(self, sheet_names: List[str]) -> List[SheetInfo]:
        """
        Filter and rank all sheets in a workbook.

        Args:
            sheet_names: List of sheet names

        Returns:
            List of SheetInfo sorted by priority (highest first),
            with skipped sheets at the end
        """
        results = []
        for idx, name in enumerate(sheet_names):
            info = self.analyze_sheet(name, idx)
            results.append(info)

        # Sort: non-skipped first by priority, then skipped
        results.sort(key=lambda x: (x.should_skip, -x.priority_score))

        return results

    def get_best_sheet(self, sheet_names: List[str]) -> Optional[SheetInfo]:
        """
        Get the best sheet for BOQ processing.

        Args:
            sheet_names: List of sheet names

        Returns:
            SheetInfo for the best sheet, or None if all should be skipped
        """
        filtered = self.filter_sheets(sheet_names)

        for info in filtered:
            if not info.should_skip:
                return info

        return None


# Module-level singleton
_sheet_filter: Optional[SheetFilter] = None


def get_sheet_filter() -> SheetFilter:
    """Get or create singleton SheetFilter instance."""
    global _sheet_filter
    if _sheet_filter is None:
        _sheet_filter = SheetFilter()
    return _sheet_filter
