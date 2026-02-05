"""
Spec Extractor Service

Extracts structured specs from normalized descriptions:
- Category: Be tong, Thep, Ong, Cap, etc.
- Material: HDPE, PPR, Cu/XLPE, gach dac, etc.
- Grade: M200, CB400, PN16, K95, etc.
- Dimension: D110, 4x16mm2, 600x600, etc.

Usage:
    extractor = SpecExtractor()
    specs = extractor.extract("Ong nhua HDPE D110 PN10")
    # ExtractedSpecs(category='ong', material='HDPE', grade='PN10', dimension='D110')
"""
import re
from dataclasses import dataclass
from typing import Optional, List, Tuple


@dataclass
class ExtractedSpecs:
    """Extracted specification fields from a description."""
    category: Optional[str] = None
    material: Optional[str] = None
    grade: Optional[str] = None
    dimension: Optional[str] = None

    def to_matching_key(self) -> str:
        """
        Generate matching key from specs.

        Format: "category|material|grade|dimension"
        Use 'X' for missing fields.
        """
        parts = [
            self.category or 'X',
            self.material or 'X',
            self.grade or 'X',
            self.dimension or 'X'
        ]
        return '|'.join(p.lower().strip() for p in parts)

    def is_empty(self) -> bool:
        """Check if no specs were extracted."""
        return all(v is None for v in [self.category, self.material, self.grade, self.dimension])


class SpecExtractor:
    """
    Extract structured specs from normalized Vietnamese construction descriptions.

    Supports:
    - Concrete (be tong): M150, M200, M300, B15, B20, B25
    - Reinforcing steel (cot thep): CB300, CB400, D10, D12, D16
    - Pipes (ong): HDPE, PPR, PVC, DN, PN ratings
    - Cables (cap): Cu/XLPE, cross-section (4x16mm2)
    - Bricks/tiles (gach): dimensions (600x600, 400x200)
    - Formwork (van khuon): types
    - Earthwork (dao dat): categories
    """

    # Category patterns - order matters (more specific first)
    # Support both accented (Unicode) and non-accented (ASCII) Vietnamese
    CATEGORY_PATTERNS: List[Tuple[str, str]] = [
        ('be tong cot thep', r'b[eê]\s*t[oô]ng\s*c[oố]t\s*th[eé]p|btct'),
        ('cot thep', r'c[oố]t\s*th[eé]p|th[eé]p\s*c[oố]t|ct(?!\w)|rebar'),
        ('be tong', r'b[eê]\s*t[oô]ng|beton|concrete|bt(?!\w)'),
        ('thep hinh', r'th[eé]p\s*h[iì]nh|th[eé]p\s*h|thep\s*i|thep\s*u'),
        ('thep', r'(?<![a-z])th[eé]p(?!\s*c[oố]t)'),
        ('ong', r'(?<![a-z])[oố]ng(?!\s*gen)|pipe|tube'),
        ('cap dien', r'c[aá]p\s*[dđ]i[eệ]n|d[aâ]y\s*[dđ]i[eệ]n|cap\s*dien'),
        ('cap', r'(?<![a-z])c[aá]p(?!\s*treo)|cable'),
        ('gach lat', r'g[aạ]ch\s*l[aá]t|gach\s*lat|tile'),
        ('dao dat', r'[dđ][aà]o\s*[dđ][aấ]t|dao\s*dat|excavat'),
        ('dap dat', r'[dđ][aắ]p\s*[dđ][aấ]t|dap\s*dat|backfill'),
        ('van khuon', r'v[aá]n\s*khu[oô]n|van\s*khuon|formwork|vk(?!\w)'),
        ('chong tham', r'ch[oố]ng\s*th[aấ]m|chong\s*tham|waterproof'),
        ('xay', r'(?<![a-z])x[aâ]y(?!\s*d[uự]ng)|masonry'),
        ('trat', r'(?<![a-z])tr[aá]t|plaster'),
        ('son', r'(?<![a-z])s[oơ]n|paint'),
        ('gach', r'(?<![a-z])g[aạ]ch|brick'),
    ]

    # Grade patterns with capture groups
    GRADE_PATTERNS = [
        (r'\bM(\d{2,3})\b', 'M'),           # M150, M200, M300 (concrete)
        (r'\bB(\d{1,2}\.?\d?)\b', 'B'),     # B15, B20, B25, B22.5 (concrete)
        (r'\bCB(\d{3})\b', 'CB'),           # CB300, CB400 (rebar)
        (r'\bCT(\d)\b', 'CT'),              # CT3, CT5 (steel)
        (r'\bPN(\d{1,2})\b', 'PN'),         # PN10, PN16 (pipe pressure)
        (r'\bK9(\d)\b', 'K9'),              # K95, K98 (compaction)
        (r'\bC(\d{1,2}/\d{1,2})\b', 'C'),   # C16/20, C20/25 (Eurocode concrete)
        (r'\bSDR(\d{1,2})\b', 'SDR'),       # SDR11, SDR17 (pipe)
    ]

    # Dimension patterns
    DIMENSION_PATTERNS = [
        r'\bD(\d{1,4})\b',                   # D10, D16, D110, D315
        r'\bDN(\d{2,4})\b',                  # DN50, DN100, DN200
        r'\bØ(\d{1,3})\b',                   # O16, O110
        r'\b(\d{1,4})\s*[xX×]\s*(\d{1,4})(?:\s*[xX×]\s*(\d{1,4}))?\s*(?:mm)?\b',  # 600x600, 400x200x8
        r'\b(\d+(?:[.,]\d+)?)\s*mm\d?\b',    # 15mm, 0.3mm, 4mm2
        r'\b(\d+(?:[.,]\d+)?)\s*cm\b',       # 20cm, 5.5cm
        r'\b(\d+(?:[.,]\d+)?)\s*m(?![m\d])', # 1.5m, 2m (not mm)
    ]

    # Cross-section patterns for cables
    CROSS_SECTION_PATTERNS = [
        r'\b(\d+)\s*[xX×]\s*(\d+(?:[.,]\d+)?)\s*mm2?\b',  # 4x16mm2, 3x10mm2
        r'\b(\d+(?:[.,]\d+)?)\s*mm2\b',      # 240mm2, 16mm2
    ]

    # Material patterns
    MATERIAL_PATTERNS = {
        'HDPE': r'\bHDPE\b',
        'PPR': r'\bPPR\b',
        'PVC': r'\bPVC\b|u?PVC',
        'PE': r'(?<![A-Z])\bPE\b(?![A-Z])',
        'Cu/XLPE': r'\bCu[/-]?XLPE\b|XLPE[/-]?Cu',
        'XLPE': r'\bXLPE\b',
        'Cu': r'(?<![A-Z/])\bCu\b|copper|[dđ][oồ]ng',
        'Al': r'\bAl\b|nh[oô]m|nhom|aluminum',
        'gang': r'\bgang\b|cast\s*iron',
        'inox': r'\binox\b|stainless',
        'thep ma kem': r'th[eé]p\s*m[aạ]\s*k[eẽ]m|thep\s*ma\s*kem|galvanized',
        'go': r'(?<![a-z])g[oỗ]\b|go\b|wood|timber',
        'gach dac': r'g[aạ]ch\s*[dđ][aặ]c|gach\s*dac',
        'gach rong': r'g[aạ]ch\s*r[oỗ]ng|gach\s*rong|hollow',
        'ceramic': r'ceramic|g[aạ]ch\s*men|s[uứ]',
        'granite': r'granite|[dđ][aá]\s*granite',
    }

    def __init__(self):
        """Initialize the spec extractor with compiled patterns."""
        # Compile category patterns
        self._category_patterns = [
            (cat, re.compile(pattern, re.IGNORECASE | re.UNICODE))
            for cat, pattern in self.CATEGORY_PATTERNS
        ]

        # Compile grade patterns
        self._grade_patterns = [
            (re.compile(pattern, re.IGNORECASE), prefix)
            for pattern, prefix in self.GRADE_PATTERNS
        ]

        # Compile dimension patterns
        self._dimension_patterns = [
            re.compile(pattern, re.IGNORECASE | re.UNICODE)
            for pattern in self.DIMENSION_PATTERNS
        ]

        # Compile cross-section patterns
        self._cross_section_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.CROSS_SECTION_PATTERNS
        ]

        # Compile material patterns
        self._material_patterns = {
            mat: re.compile(pattern, re.IGNORECASE | re.UNICODE)
            for mat, pattern in self.MATERIAL_PATTERNS.items()
        }

    def extract(self, description: str) -> ExtractedSpecs:
        """
        Extract specs from description.

        Args:
            description: Normalized or raw description text

        Returns:
            ExtractedSpecs with extracted fields
        """
        if not description:
            return ExtractedSpecs()

        return ExtractedSpecs(
            category=self._extract_category(description),
            material=self._extract_material(description),
            grade=self._extract_grade(description),
            dimension=self._extract_dimension(description)
        )

    def _extract_category(self, desc: str) -> Optional[str]:
        """Extract primary category from description."""
        for category, pattern in self._category_patterns:
            if pattern.search(desc):
                return category
        return None

    def _extract_material(self, desc: str) -> Optional[str]:
        """Extract material type from description."""
        # Check in priority order (Cu/XLPE before XLPE, before Cu)
        priority_order = [
            'Cu/XLPE', 'XLPE', 'Cu', 'Al',
            'HDPE', 'PPR', 'PVC', 'PE',
            'thep ma kem', 'inox', 'gang',
            'gach dac', 'gach rong', 'ceramic', 'granite',
            'go'
        ]

        for material in priority_order:
            if material in self._material_patterns:
                pattern = self._material_patterns[material]
                if pattern.search(desc):
                    return material

        # Check remaining materials
        for material, pattern in self._material_patterns.items():
            if material not in priority_order:
                if pattern.search(desc):
                    return material

        return None

    def _extract_grade(self, desc: str) -> Optional[str]:
        """Extract grade/class from description."""
        for pattern, prefix in self._grade_patterns:
            match = pattern.search(desc)
            if match:
                # Return full match (e.g., "M200", "CB400")
                return match.group(0).upper()
        return None

    def _extract_dimension(self, desc: str) -> Optional[str]:
        """
        Extract dimension from description.

        Priority:
        1. Cross-section for cables (4x16mm2)
        2. Diameter (D110, DN200)
        3. Size (600x600, 400x200x8)
        4. Simple measurement (15mm, 20cm)
        """
        # Check cross-section first (for cables)
        for pattern in self._cross_section_patterns:
            match = pattern.search(desc)
            if match:
                return match.group(0).lower().replace(' ', '')

        # Check standard dimensions
        for pattern in self._dimension_patterns:
            match = pattern.search(desc)
            if match:
                result = match.group(0)
                # Normalize format
                result = result.replace(' ', '').replace('×', 'x').replace('X', 'x')
                return result

        return None


# Module-level singleton
_spec_extractor: Optional[SpecExtractor] = None


def get_spec_extractor() -> SpecExtractor:
    """Get or create singleton SpecExtractor instance."""
    global _spec_extractor
    if _spec_extractor is None:
        _spec_extractor = SpecExtractor()
    return _spec_extractor
