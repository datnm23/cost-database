"""
BOQ Keyword Dictionary

Enhanced BOQ keyword matching with weighted scores for Vietnamese and English headers.
Supports full Vietnamese words and common abbreviations.
"""
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class KeywordMatch:
    """Result of keyword matching."""
    keyword: str
    weight: float
    column_type: str  # 'description', 'unit', 'quantity', 'unit_price', 'amount', 'index', 'code'


class KeywordDictionary:
    """
    BOQ keyword dictionary with weighted scoring.

    Weight scale:
    - 5.0: Core BOQ keywords (description, quantity, unit price, amount)
    - 4.0-4.5: Primary keywords (unit, item code)
    - 3.5-4.0: Vietnamese abbreviations
    - 3.0: Secondary keywords
    """

    # Primary Vietnamese keywords (full words)
    PRIMARY_KEYWORDS: Dict[str, Tuple[float, str]] = {
        # Description
        'mô tả': (5.0, 'description'),
        'mo ta': (5.0, 'description'),
        'nội dung': (4.5, 'description'),
        'noi dung': (4.5, 'description'),
        'hạng mục': (4.5, 'description'),
        'hang muc': (4.5, 'description'),
        'công việc': (4.5, 'description'),
        'cong viec': (4.5, 'description'),
        'diễn giải': (4.5, 'description'),
        'dien giai': (4.5, 'description'),

        # Unit
        'đơn vị': (5.0, 'unit'),
        'don vi': (5.0, 'unit'),
        'đơn vị tính': (5.0, 'unit'),
        'don vi tinh': (5.0, 'unit'),

        # Quantity
        'khối lượng': (5.0, 'quantity'),
        'khoi luong': (5.0, 'quantity'),
        'số lượng': (5.0, 'quantity'),
        'so luong': (5.0, 'quantity'),

        # Unit price
        'đơn giá': (5.0, 'unit_price'),
        'don gia': (5.0, 'unit_price'),
        'giá đơn vị': (4.5, 'unit_price'),
        'gia don vi': (4.5, 'unit_price'),

        # Amount/Total
        'thành tiền': (5.0, 'amount'),
        'thanh tien': (5.0, 'amount'),
        'tổng tiền': (4.5, 'amount'),
        'tong tien': (4.5, 'amount'),
        'tổng cộng': (4.0, 'amount'),
        'tong cong': (4.0, 'amount'),

        # Index/STT
        'số thứ tự': (4.0, 'index'),
        'so thu tu': (4.0, 'index'),

        # Code
        'mã hiệu': (4.0, 'code'),
        'ma hieu': (4.0, 'code'),
        'mã công tác': (4.0, 'code'),
        'ma cong tac': (4.0, 'code'),
    }

    # Vietnamese abbreviations
    ABBREVIATIONS: Dict[str, Tuple[float, str]] = {
        'stt': (4.0, 'index'),
        'đvt': (4.5, 'unit'),
        'dvt': (4.5, 'unit'),
        'kl': (4.0, 'quantity'),
        'đg': (4.5, 'unit_price'),
        'dg': (4.5, 'unit_price'),
        'tt': (3.5, 'amount'),  # Could be "thành tiền" or "thứ tự"
        'mh': (3.5, 'code'),  # Mã hiệu
        'sl': (4.0, 'quantity'),  # Số lượng
        'nc': (3.0, 'labor'),  # Nhân công
        'vl': (3.0, 'material'),  # Vật liệu
        'mtc': (3.0, 'machine'),  # Máy thi công
    }

    # English keywords - longer/more specific keywords first for proper matching
    ENGLISH_KEYWORDS: Dict[str, Tuple[float, str]] = {
        'item description': (5.0, 'description'),
        'description': (5.0, 'description'),
        'work item': (4.5, 'description'),
        'item': (3.5, 'description'),

        'unit price': (5.0, 'unit_price'),  # Must be before 'unit'
        'unit rate': (5.0, 'unit_price'),   # Must be before 'unit'
        'unit': (5.0, 'unit'),
        'uom': (4.5, 'unit'),
        'u/m': (4.0, 'unit'),

        'quantity': (5.0, 'quantity'),
        'qty': (4.5, 'quantity'),
        'volume': (4.0, 'quantity'),

        'rate': (4.0, 'unit_price'),
        'price': (3.5, 'unit_price'),

        'amount': (5.0, 'amount'),
        'total': (4.0, 'amount'),
        'value': (3.5, 'amount'),
        'sum': (3.5, 'amount'),

        'no': (3.5, 'index'),
        'no.': (3.5, 'index'),
        's/n': (3.5, 'index'),
        '#': (3.0, 'index'),

        'item code': (4.5, 'code'),  # Must be before 'code'
        'code': (4.0, 'code'),
        'ref': (3.5, 'code'),
        'reference': (3.5, 'code'),
    }

    # Combined headers (multi-level)
    COMBINED_PATTERNS: List[Tuple[str, float, str]] = [
        (r'vật\s*liệu.*đơn\s*giá|vat\s*lieu.*don\s*gia', 4.0, 'material_price'),
        (r'nhân\s*công.*đơn\s*giá|nhan\s*cong.*don\s*gia', 4.0, 'labor_price'),
        (r'máy.*đơn\s*giá|may.*don\s*gia', 4.0, 'machine_price'),
        (r'vật\s*liệu.*thành\s*tiền|vat\s*lieu.*thanh\s*tien', 4.0, 'material_amount'),
        (r'nhân\s*công.*thành\s*tiền|nhan\s*cong.*thanh\s*tien', 4.0, 'labor_amount'),
    ]

    def __init__(self):
        """Initialize keyword dictionary with compiled patterns."""
        self._compiled_patterns: List[Tuple[re.Pattern, float, str]] = []

        # Compile combined patterns
        for pattern, weight, col_type in self.COMBINED_PATTERNS:
            self._compiled_patterns.append(
                (re.compile(pattern, re.IGNORECASE | re.UNICODE), weight, col_type)
            )

    def match_cell(self, text: str) -> Optional[KeywordMatch]:
        """
        Match a cell value against the keyword dictionary.

        Args:
            text: Cell text to match

        Returns:
            KeywordMatch if found, None otherwise
        """
        if not text or not isinstance(text, str):
            return None

        text_clean = text.strip().lower()
        text_no_space = text_clean.replace(' ', '')

        # Check combined patterns first
        for pattern, weight, col_type in self._compiled_patterns:
            if pattern.search(text_clean):
                return KeywordMatch(keyword=text_clean, weight=weight, column_type=col_type)

        # Check primary Vietnamese keywords (exact or contained)
        for keyword, (weight, col_type) in self.PRIMARY_KEYWORDS.items():
            if keyword in text_clean or keyword.replace(' ', '') in text_no_space:
                return KeywordMatch(keyword=keyword, weight=weight, column_type=col_type)

        # Check abbreviations (exact match, case-insensitive)
        for abbr, (weight, col_type) in self.ABBREVIATIONS.items():
            # Exact match or with common suffixes
            if text_clean == abbr or text_no_space == abbr:
                return KeywordMatch(keyword=abbr, weight=weight, column_type=col_type)
            # Check if abbreviation is the main content (e.g., "STT." or "(STT)")
            abbr_pattern = rf'^[\(\[\s]*{re.escape(abbr)}[\)\]\.\s]*$'
            if re.match(abbr_pattern, text_clean, re.IGNORECASE):
                return KeywordMatch(keyword=abbr, weight=weight, column_type=col_type)

        # Check English keywords - sorted by length (longer first) for proper matching
        sorted_english = sorted(
            self.ENGLISH_KEYWORDS.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )
        for keyword, (weight, col_type) in sorted_english:
            if keyword in text_clean:
                return KeywordMatch(keyword=keyword, weight=weight, column_type=col_type)

        return None

    def score_row(self, cells: List[str]) -> Tuple[float, Dict[str, int]]:
        """
        Score a row based on keyword matches.

        Args:
            cells: List of cell values in the row

        Returns:
            Tuple of (total_score, column_type_hints)
            where column_type_hints maps column_type to column_index
        """
        total_score = 0.0
        column_hints: Dict[str, int] = {}
        matched_types = set()

        for idx, cell in enumerate(cells):
            if cell is None:
                continue
            cell_str = str(cell).strip()
            match = self.match_cell(cell_str)
            if match:
                total_score += match.weight
                if match.column_type not in matched_types:
                    column_hints[match.column_type] = idx
                    matched_types.add(match.column_type)

        # Bonus for complete BOQ header (has description + unit + quantity)
        core_types = {'description', 'unit', 'quantity'}
        if core_types.issubset(matched_types):
            total_score += 10.0  # Significant bonus
        elif len(core_types.intersection(matched_types)) >= 2:
            total_score += 5.0  # Partial bonus

        return total_score, column_hints


# Module-level singleton
_keyword_dictionary: Optional[KeywordDictionary] = None


def get_keyword_dictionary() -> KeywordDictionary:
    """Get or create singleton KeywordDictionary instance."""
    global _keyword_dictionary
    if _keyword_dictionary is None:
        _keyword_dictionary = KeywordDictionary()
    return _keyword_dictionary
