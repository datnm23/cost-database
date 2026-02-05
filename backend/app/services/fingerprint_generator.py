"""
Fingerprint Generator Service

Generates unique fingerprints for BOQ file structures to enable automatic template matching.
Uses column name normalization and semantic keyword extraction.
"""
import hashlib
import re
import logging
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)


@dataclass
class FingerprintComponents:
    """Detailed fingerprint components for fuzzy matching."""
    column_count: int
    column_keywords: List[str]  # Sorted, normalized keywords
    column_order_hash: str  # MD5 of column order
    data_type_signature: Optional[str] = None  # e.g., "TTNNN" format

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FingerprintResult:
    """Result of fingerprint generation."""
    fingerprint: str
    components: FingerprintComponents


class FingerprintGenerator:
    """
    Generates unique fingerprints for BOQ file column structures.

    Fingerprint algorithm:
    1. Normalize column names (lowercase, trim, remove special chars)
    2. Extract semantic keywords (description, unit, quantity, etc.)
    3. Sort keywords alphabetically
    4. Generate SHA256 hash of sorted keywords + column count
    5. Store components for fuzzy matching
    """

    # Semantic keyword patterns for Vietnamese and English BOQ columns
    KEYWORD_PATTERNS: Dict[str, List[str]] = {
        'description': [
            'mô tả', 'mo ta', 'nội dung', 'noi dung', 'hạng mục', 'hang muc',
            'công việc', 'cong viec', 'diễn giải', 'dien giai', 'description',
            'item description', 'work item', 'item', 'name'
        ],
        'unit': [
            'đơn vị', 'don vi', 'đơn vị tính', 'don vi tinh', 'đvt', 'dvt',
            'unit', 'uom', 'u/m'
        ],
        'quantity': [
            'khối lượng', 'khoi luong', 'số lượng', 'so luong', 'kl', 'sl',
            'quantity', 'qty', 'volume'
        ],
        'unit_price': [
            'đơn giá', 'don gia', 'giá đơn vị', 'gia don vi', 'đg', 'dg',
            'unit price', 'unit rate', 'rate', 'price'
        ],
        'amount': [
            'thành tiền', 'thanh tien', 'tổng tiền', 'tong tien', 'tổng cộng',
            'tong cong', 'tt', 'amount', 'total', 'value', 'sum'
        ],
        'index': [
            'số thứ tự', 'so thu tu', 'stt', 'no', 'no.', 's/n', '#', 'index'
        ],
        'code': [
            'mã hiệu', 'ma hieu', 'mã công tác', 'ma cong tac', 'mh',
            'item code', 'code', 'ref', 'reference'
        ],
        'material': [
            'vật liệu', 'vat lieu', 'vl', 'material', 'materials'
        ],
        'labor': [
            'nhân công', 'nhan cong', 'nc', 'labor', 'labour'
        ],
        'machine': [
            'máy thi công', 'may thi cong', 'máy', 'may', 'mtc',
            'machine', 'equipment'
        ],
        'note': [
            'ghi chú', 'ghi chu', 'chú thích', 'chu thich', 'note', 'notes', 'remark', 'remarks'
        ],
    }

    # Weights for similarity calculation
    SIMILARITY_WEIGHTS = {
        'keyword_overlap': 0.50,  # Jaccard similarity
        'column_count': 0.25,
        'order_hash': 0.15,
        'data_type': 0.10,
    }

    def __init__(self):
        """Initialize the fingerprint generator."""
        # Build reverse lookup: normalized pattern -> keyword type
        self._pattern_lookup: Dict[str, str] = {}
        for keyword_type, patterns in self.KEYWORD_PATTERNS.items():
            for pattern in patterns:
                normalized = self._normalize_text(pattern)
                self._pattern_lookup[normalized] = keyword_type

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison.

        - Convert to lowercase
        - Remove extra whitespace
        - Remove special characters (keep alphanumeric and Vietnamese chars)
        """
        if not text:
            return ""

        text = text.lower().strip()
        # Remove special characters but keep Vietnamese diacritics
        text = re.sub(r'[^\w\sàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]', '', text)
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _extract_keyword(self, column_name: str) -> Optional[str]:
        """
        Extract semantic keyword from a column name.

        Returns the keyword type if matched, None otherwise.
        """
        normalized = self._normalize_text(column_name)
        if not normalized:
            return None

        # Direct lookup (exact match)
        if normalized in self._pattern_lookup:
            return self._pattern_lookup[normalized]

        # Substring matching (for compound column names)
        # Only match if pattern is a significant portion of the text
        # Sort patterns by length (longer first) to prefer more specific matches
        sorted_patterns = sorted(self._pattern_lookup.items(), key=lambda x: len(x[0]), reverse=True)
        for pattern, keyword_type in sorted_patterns:
            # Skip very short patterns for substring matching (too many false positives)
            if len(pattern) < 3:
                continue
            # Pattern must be contained in the column name
            if pattern in normalized:
                return keyword_type

        return None

    def _infer_data_types(self, sample_data: List[List[Any]]) -> str:
        """
        Infer data types from sample data.

        Returns a signature like "TTNNN" where:
        - T = Text
        - N = Numeric
        - E = Empty/Unknown
        """
        if not sample_data or not sample_data[0]:
            return ""

        num_columns = len(sample_data[0])
        type_counts = [{} for _ in range(num_columns)]

        for row in sample_data:
            for i, cell in enumerate(row):
                if i >= num_columns:
                    break
                cell_type = self._detect_cell_type(cell)
                type_counts[i][cell_type] = type_counts[i].get(cell_type, 0) + 1

        # Determine dominant type for each column
        signature = ""
        for col_types in type_counts:
            if not col_types:
                signature += "E"
            else:
                dominant = max(col_types, key=col_types.get)
                signature += dominant
        return signature

    def _detect_cell_type(self, cell: Any) -> str:
        """Detect the type of a cell value."""
        if cell is None:
            return "E"
        if isinstance(cell, (int, float)):
            return "N"
        if isinstance(cell, str):
            cell = cell.strip()
            if not cell:
                return "E"
            # Try to parse as number
            try:
                float(cell.replace(',', '.').replace(' ', ''))
                return "N"
            except ValueError:
                return "T"
        return "T"

    def generate(
        self,
        column_names: List[str],
        sample_data: Optional[List[List[Any]]] = None
    ) -> FingerprintResult:
        """
        Generate fingerprint for a set of column names.

        Args:
            column_names: List of column header names
            sample_data: Optional sample data rows for type inference

        Returns:
            FingerprintResult with fingerprint hash and components
        """
        # Extract keywords from column names
        keywords = []
        for col in column_names:
            keyword = self._extract_keyword(col)
            if keyword:
                keywords.append(keyword)

        # Sort keywords for consistent fingerprint
        sorted_keywords = sorted(set(keywords))

        # Generate column order hash (MD5 of normalized column names in order)
        normalized_cols = [self._normalize_text(col) for col in column_names]
        order_string = "|".join(normalized_cols)
        order_hash = hashlib.md5(order_string.encode('utf-8')).hexdigest()[:16]

        # Infer data types if sample data provided
        data_type_sig = None
        if sample_data:
            data_type_sig = self._infer_data_types(sample_data)

        # Build components
        components = FingerprintComponents(
            column_count=len(column_names),
            column_keywords=sorted_keywords,
            column_order_hash=order_hash,
            data_type_signature=data_type_sig
        )

        # Generate main fingerprint (SHA256)
        fingerprint_input = f"{len(column_names)}|{','.join(sorted_keywords)}"
        fingerprint = hashlib.sha256(fingerprint_input.encode('utf-8')).hexdigest()

        logger.debug(f"Generated fingerprint: {fingerprint[:16]}... for {len(column_names)} columns")

        return FingerprintResult(
            fingerprint=fingerprint,
            components=components
        )

    def calculate_similarity(
        self,
        fp1: FingerprintComponents,
        fp2: FingerprintComponents
    ) -> float:
        """
        Calculate similarity between two fingerprints.

        Uses weighted scoring:
        - Keyword overlap (Jaccard): 50%
        - Column count similarity: 25%
        - Order hash match: 15%
        - Data type signature: 10%

        Returns:
            Similarity score from 0 to 100
        """
        scores = {}

        # Keyword overlap (Jaccard similarity)
        set1 = set(fp1.column_keywords)
        set2 = set(fp2.column_keywords)
        if set1 or set2:
            intersection = len(set1 & set2)
            union = len(set1 | set2)
            scores['keyword_overlap'] = (intersection / union) * 100 if union > 0 else 0
        else:
            scores['keyword_overlap'] = 100 if not set1 and not set2 else 0

        # Column count similarity (exponential decay)
        count_diff = abs(fp1.column_count - fp2.column_count)
        max_count = max(fp1.column_count, fp2.column_count, 1)
        scores['column_count'] = max(0, 100 - (count_diff / max_count) * 100)

        # Order hash match (exact match only)
        scores['order_hash'] = 100 if fp1.column_order_hash == fp2.column_order_hash else 0

        # Data type signature match
        if fp1.data_type_signature and fp2.data_type_signature:
            sig1 = fp1.data_type_signature
            sig2 = fp2.data_type_signature
            min_len = min(len(sig1), len(sig2))
            if min_len > 0:
                matches = sum(1 for a, b in zip(sig1, sig2) if a == b)
                scores['data_type'] = (matches / min_len) * 100
            else:
                scores['data_type'] = 0
        else:
            # No data type info - use neutral score
            scores['data_type'] = 50

        # Calculate weighted total
        total = sum(
            scores[key] * self.SIMILARITY_WEIGHTS[key]
            for key in scores
        )

        logger.debug(f"Similarity scores: {scores}, total: {total:.2f}")

        return round(total, 2)


# Module-level singleton
_fingerprint_generator: Optional[FingerprintGenerator] = None


def get_fingerprint_generator() -> FingerprintGenerator:
    """Get or create singleton FingerprintGenerator instance."""
    global _fingerprint_generator
    if _fingerprint_generator is None:
        _fingerprint_generator = FingerprintGenerator()
    return _fingerprint_generator
