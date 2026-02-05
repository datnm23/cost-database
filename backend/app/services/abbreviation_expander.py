"""
Vietnamese Construction Abbreviation Expander Service

Expands common Vietnamese construction abbreviations before normalization
to improve SBERT matching accuracy.

Problem: SBERT treats "BT" and "Bê tông" as completely different tokens,
resulting in ~65-75% similarity instead of 95%+.

Solution: Expand abbreviations BEFORE normalization so SBERT can match
the full Vietnamese text properly.

Example:
    Input:  "BT M200 cột, VK gỗ, CT D16 CB400"
    Output: "Bê tông M200 cột, Ván khuôn gỗ, Cốt thép D16 CB400"
"""
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExpansionResult:
    """Result of abbreviation expansion"""
    original: str
    expanded: str
    expansions_applied: List[Dict[str, str]] = field(default_factory=list)
    tech_specs_preserved: List[str] = field(default_factory=list)


# Default abbreviation dictionary
# Sorted by length (longest first) to handle overlapping abbreviations
# E.g., "BTCT" should be matched before "BT"
DEFAULT_ABBREVIATIONS: Dict[str, str] = {
    # ============================================================
    # CONCRETE (Bê tông) - Most common, highest priority
    # ============================================================
    # Longer patterns first
    'BTXM': 'Bê tông xi măng',      # Cement concrete
    'BTCT': 'Bê tông cốt thép',     # Reinforced concrete
    'BTĐS': 'Bê tông đá sỏi',       # Gravel concrete
    'BTLT': 'Bê tông lót',          # Lean concrete / base concrete
    'BTDC': 'Bê tông đúc sẵn',      # Precast concrete
    'BTDS': 'Bê tông đúc sẵn',      # Precast concrete (variant)
    # Asphalt concrete
    'BTNC': 'Bê tông nhựa chặt',    # Dense asphalt concrete
    'BTNN': 'Bê tông nhựa nóng',    # Hot asphalt concrete
    'BTN': 'Bê tông nhựa',          # Asphalt concrete
    # Basic
    'BT': 'Bê tông',                # Concrete

    # ============================================================
    # REINFORCEMENT (Cốt thép)
    # ============================================================
    'CTCT': 'Cốt thép cọc tràm',    # Melaleuca pile rebar
    'CTCS': 'Cốt thép cọc sắt',     # Steel pile rebar
    'CT': 'Cốt thép',               # Reinforcement / rebar

    # ============================================================
    # FORMWORK (Ván khuôn)
    # ============================================================
    'VKGỖ': 'Ván khuôn gỗ',         # Timber formwork
    'VKG': 'Ván khuôn gỗ',          # Timber formwork (short)
    'VKTHÉP': 'Ván khuôn thép',     # Steel formwork
    'VKT': 'Ván khuôn thép',        # Steel formwork (short)
    'VKPP': 'Ván khuôn phủ phim',   # Film-coated formwork
    'VK': 'Ván khuôn',              # Formwork

    # ============================================================
    # AGGREGATES (Cấp phối đá dăm)
    # ============================================================
    'CPĐDL1': 'Cấp phối đá dăm loại 1',  # Type 1 aggregate
    'CPĐDL2': 'Cấp phối đá dăm loại 2',  # Type 2 aggregate
    'CPĐD': 'Cấp phối đá dăm',      # Crushed stone aggregate
    'CPDD': 'Cấp phối đá dăm',      # Without diacritic
    'CPĐ': 'Cấp phối đá',           # Aggregate
    'CPD': 'Cấp phối đá',           # Without diacritic
    'CP': 'Cấp phối',               # Aggregate (general)

    # ============================================================
    # GEOTECHNICAL (Địa kỹ thuật)
    # ============================================================
    'VĐKT': 'Vải địa kỹ thuật',     # Geotextile fabric
    'VDKT': 'Vải địa kỹ thuật',     # Without diacritic
    'ĐKT': 'Địa kỹ thuật',          # Geotechnical
    'DKT': 'Địa kỹ thuật',          # Without diacritic

    # ============================================================
    # MEP (Cơ điện)
    # ============================================================
    'ĐHKK': 'Điều hòa không khí',   # Air conditioning
    'DHKK': 'Điều hòa không khí',   # Without diacritic
    'PCCC': 'Phòng cháy chữa cháy', # Fire protection
    'ĐNHT': 'Điện nhẹ hạ thế',      # Low voltage electrical
    'DNHT': 'Điện nhẹ hạ thế',      # Without diacritic
    'ĐHT': 'Điện hạ thế',           # Low voltage
    'DHT': 'Điện hạ thế',           # Without diacritic
    'TĐN': 'Tủ điện nhánh',         # Branch electrical panel
    'TDN': 'Tủ điện nhánh',         # Without diacritic
    'TM': 'Thương mại',             # Commercial
    'CN': 'Công nghiệp',            # Industrial

    # ============================================================
    # ROAD INFRASTRUCTURE (Hạ tầng đường)
    # ============================================================
    'LTB': 'Lớp thấm bám',          # Tack coat
    'VH': 'Vỉa hè',                 # Sidewalk
    'BV': 'Bó vỉa',                 # Curb
    'HG': 'Hố ga',                  # Manhole
    'CM': 'Cống mương',             # Drain culvert
    'TL': 'Taluy',                  # Slope

    # ============================================================
    # WORK VERBS (Động từ công việc)
    # ============================================================
    'GCLD': 'Gia công lắp dựng',    # Fabrication and erection
    'GCBT': 'Gia công bê tông',     # Concrete work
    'GCCT': 'Gia công cốt thép',    # Rebar fabrication
    'GCVK': 'Gia công ván khuôn',   # Formwork fabrication
    'TC': 'Thi công',               # Construction
    'LĐ': 'Lắp đặt',                # Installation
    'LD': 'Lắp đặt',                # Without diacritic
    'GC': 'Gia công',               # Fabrication
    'VC': 'Vận chuyển',             # Transportation
    'CC': 'Cung cấp',               # Supply

    # ============================================================
    # PILING (Cọc)
    # ============================================================
    'CBTCT': 'Cọc bê tông cốt thép',  # RC pile
    'CBTDUS': 'Cọc bê tông dự ứng lực',  # Prestressed concrete pile
    'CÉPBT': 'Cọc ép bê tông',      # Pressed concrete pile
    'CKBT': 'Cọc khoan bê tông',    # Bored concrete pile
    'CKHOAN': 'Cọc khoan',          # Bored pile
    'CÉP': 'Cọc ép',                # Pressed pile
    'CEP': 'Cọc ép',                # Without diacritic

    # ============================================================
    # MATERIALS (Vật liệu)
    # ============================================================
    'XM': 'Xi măng',                # Cement
    'ĐD': 'Đá dăm',                 # Crushed stone
    'DD': 'Đá dăm',                 # Without diacritic
    'CL': 'Cát lọc',                # Filter sand
    'CV': 'Cát vàng',               # Yellow sand
    'SX': 'Sản xuất',               # Production
    'NK': 'Nhập khẩu',              # Imported

    # ============================================================
    # STRUCTURE TYPES (Loại kết cấu)
    # ============================================================
    'KC': 'Kết cấu',                # Structure
    'KCT': 'Kết cấu thép',          # Steel structure
    'KCBT': 'Kết cấu bê tông',      # Concrete structure
}


# Technical specifications to preserve (NOT expand)
# These look like abbreviations but are actually technical specs
TECH_SPEC_PATTERNS = [
    # Concrete grades: M100, M150, M200, M250, M300, M350, M400, M500
    r'\bM\d{2,3}\b',

    # Rebar diameter: D6, D8, D10, D12, D14, D16, D18, D20, D22, D25, D28, D32
    # Also pipe diameter: D50, D63, D75, D90, D110, D160, D200, D250, D315
    r'\bD\d{1,3}\b',

    # Compaction grade: K90, K95, K98
    r'\bK9[0-8]\b',

    # Pressure rating: PN6, PN10, PN16, PN20, PN25
    r'\bPN\d{1,2}\b',

    # Steel grade: CB240, CB300, CB400, CB500
    r'\bCB\d{3}\b',

    # Structural steel: SS400, SS490, SS540
    r'\bSS\d{3}\b',

    # PC cement: PC30, PC40, PC50
    r'\bPC\d{2}\b',

    # B grade concrete: B15, B20, B22, B25, B30, B35, B40
    r'\bB\d{2}\b',

    # Asphalt grade: BTN C12.5, BTN C19, BTN C25
    r'\bC\d{1,2}(?:\.\d+)?\b',

    # Dimensions: 600x600, 400x200x8, 1200x2400
    r'\b\d{2,4}x\d{2,4}(?:x\d{1,4})?\b',

    # H-section: H400x200x8x12
    r'\bH\d{2,4}x\d{2,4}x\d{1,2}x\d{1,2}\b',

    # L angle: L50x50x5, L75x75x8
    r'\bL\d{2,3}x\d{2,3}x\d{1,2}\b',

    # U channel: U100, U150, U200
    r'\bU\d{2,3}\b',

    # I beam: I100, I150, I200
    r'\bI\d{2,3}\b',

    # Wire diameter with unit: 1x6mm2, 4x300mm2
    r'\b\d+x\d+(?:mm2?)?\b',

    # Thickness: 0.3mm, 15mm, 220mm
    r'\b\d+(?:\.\d+)?mm\b',

    # Layer thickness: dày 20, dày 15cm
    r'dày\s+\d+',
]


class AbbreviationExpander:
    """
    Expands Vietnamese construction abbreviations in text.

    Features:
    - Case-preserving expansion (lowercase input -> lowercase output)
    - Word boundary-aware matching (prevents partial matches)
    - Technical specification preservation (M200, D16, etc. are NOT expanded)
    - Priority handling for overlapping abbreviations (BTCT before BT)
    """

    def __init__(
        self,
        abbreviations: Optional[Dict[str, str]] = None,
        tech_spec_patterns: Optional[List[str]] = None
    ):
        """
        Initialize the expander.

        Args:
            abbreviations: Custom abbreviation dictionary (uses default if None)
            tech_spec_patterns: Custom tech spec patterns (uses default if None)
        """
        self.abbreviations = abbreviations or DEFAULT_ABBREVIATIONS.copy()
        self.tech_spec_patterns = tech_spec_patterns or TECH_SPEC_PATTERNS.copy()

        # Sort abbreviations by length (longest first) for proper matching
        self._sorted_abbrevs = sorted(
            self.abbreviations.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )

        # Pre-compile tech spec patterns
        self._tech_spec_regex = re.compile(
            '|'.join(f'({p})' for p in self.tech_spec_patterns),
            re.IGNORECASE
        )

        # Build word boundary regex for each abbreviation
        self._abbrev_patterns: List[Tuple[re.Pattern, str, str]] = []
        for abbrev, expansion in self._sorted_abbrevs:
            # Word boundary pattern - handles Vietnamese and ASCII
            # Use negative lookbehind/lookahead for word boundaries
            pattern = re.compile(
                r'(?<![a-zA-ZÀ-ỹ0-9])' + re.escape(abbrev) + r'(?![a-zA-ZÀ-ỹ0-9])',
                re.IGNORECASE
            )
            self._abbrev_patterns.append((pattern, abbrev, expansion))

    def _protect_tech_specs(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Replace technical specifications with placeholders.

        Returns:
            (protected_text, placeholder_map)
        """
        placeholder_map = {}
        protected = text

        def replace_match(match):
            spec = match.group(0)
            # Create unique placeholder
            placeholder = f"__TECHSPEC_{len(placeholder_map):03d}__"
            placeholder_map[placeholder] = spec
            return placeholder

        protected = self._tech_spec_regex.sub(replace_match, protected)
        return protected, placeholder_map

    def _restore_tech_specs(self, text: str, placeholder_map: Dict[str, str]) -> str:
        """Restore technical specifications from placeholders."""
        result = text
        for placeholder, spec in placeholder_map.items():
            result = result.replace(placeholder, spec)
        return result

    def _match_case(self, original: str, replacement: str) -> str:
        """
        Match the case pattern of the original text in the replacement.

        For construction abbreviations, the most common pattern is:
        - Abbreviation is in CAPS (BT, BTCT, CPĐD, etc.)
        - Expansion should be sentence case (Bê tông, Cấp phối đá dăm, etc.)

        Rules:
        - all lower -> all lower (bt -> bê tông)
        - Contains lowercase after first char -> Capitalize (Btct -> Bê tông cốt thép)
        - ALL CAPS (abbreviation) -> Capitalize first only (BT -> Bê tông)
        """
        if not original:
            return replacement

        if original.islower():
            # All lowercase -> lowercase expansion
            return replacement.lower()
        else:
            # For any other case (ALL CAPS, Capitalized, Mixed)
            # Use sentence case (capitalize first letter only)
            return replacement.capitalize()

    def expand(self, text: str) -> ExpansionResult:
        """
        Expand abbreviations in the given text.

        Args:
            text: Input text potentially containing abbreviations

        Returns:
            ExpansionResult with expanded text and details
        """
        if not text or not text.strip():
            return ExpansionResult(
                original=text or '',
                expanded=text or '',
                expansions_applied=[],
                tech_specs_preserved=[]
            )

        # Step 1: Protect technical specifications
        protected_text, placeholder_map = self._protect_tech_specs(text)
        tech_specs_preserved = list(placeholder_map.values())

        # Step 2: Apply abbreviation expansions (longest first)
        expanded_text = protected_text
        expansions_applied = []

        for pattern, abbrev, expansion in self._abbrev_patterns:
            # Find all matches
            matches = list(pattern.finditer(expanded_text))

            if not matches:
                continue

            # Process matches in reverse order to preserve positions
            for match in reversed(matches):
                original_match = match.group(0)

                # Skip if the match overlaps with a placeholder
                # We only check if the match position itself is inside a placeholder
                is_inside_placeholder = False
                for placeholder in placeholder_map.keys():
                    ph_start = expanded_text.find(placeholder)
                    if ph_start >= 0:
                        ph_end = ph_start + len(placeholder)
                        # Check if match overlaps with placeholder
                        if not (match.end() <= ph_start or match.start() >= ph_end):
                            is_inside_placeholder = True
                            break

                if is_inside_placeholder:
                    continue

                # Match case of the original
                case_matched_expansion = self._match_case(original_match, expansion)

                # Replace
                expanded_text = (
                    expanded_text[:match.start()] +
                    case_matched_expansion +
                    expanded_text[match.end():]
                )

                expansions_applied.append({
                    'original': original_match,
                    'expanded': case_matched_expansion,
                    'position': match.start()
                })

        # Step 3: Restore technical specifications
        final_text = self._restore_tech_specs(expanded_text, placeholder_map)

        return ExpansionResult(
            original=text,
            expanded=final_text,
            expansions_applied=expansions_applied,
            tech_specs_preserved=tech_specs_preserved
        )

    def expand_batch(self, texts: List[str]) -> List[ExpansionResult]:
        """
        Expand abbreviations in a batch of texts.

        Args:
            texts: List of input texts

        Returns:
            List of ExpansionResult objects
        """
        return [self.expand(text) for text in texts]

    def add_abbreviation(self, abbrev: str, expansion: str) -> None:
        """
        Add a new abbreviation to the dictionary.

        Args:
            abbrev: The abbreviation (e.g., "BT")
            expansion: The full form (e.g., "Bê tông")
        """
        self.abbreviations[abbrev] = expansion

        # Rebuild sorted list and patterns
        self._sorted_abbrevs = sorted(
            self.abbreviations.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )

        # Rebuild patterns
        self._abbrev_patterns = []
        for ab, exp in self._sorted_abbrevs:
            pattern = re.compile(
                r'(?<![a-zA-ZÀ-ỹ0-9])' + re.escape(ab) + r'(?![a-zA-ZÀ-ỹ0-9])',
                re.IGNORECASE
            )
            self._abbrev_patterns.append((pattern, ab, exp))

    def remove_abbreviation(self, abbrev: str) -> bool:
        """
        Remove an abbreviation from the dictionary.

        Args:
            abbrev: The abbreviation to remove

        Returns:
            True if removed, False if not found
        """
        if abbrev in self.abbreviations:
            del self.abbreviations[abbrev]

            # Rebuild sorted list and patterns
            self._sorted_abbrevs = sorted(
                self.abbreviations.items(),
                key=lambda x: len(x[0]),
                reverse=True
            )

            # Rebuild patterns
            self._abbrev_patterns = []
            for ab, exp in self._sorted_abbrevs:
                pattern = re.compile(
                    r'(?<![a-zA-ZÀ-ỹ0-9])' + re.escape(ab) + r'(?![a-zA-ZÀ-ỹ0-9])',
                    re.IGNORECASE
                )
                self._abbrev_patterns.append((pattern, ab, exp))

            return True
        return False


# Singleton instance
_abbreviation_expander: Optional[AbbreviationExpander] = None


def get_abbreviation_expander() -> AbbreviationExpander:
    """Get or create the singleton AbbreviationExpander instance."""
    global _abbreviation_expander
    if _abbreviation_expander is None:
        _abbreviation_expander = AbbreviationExpander()
    return _abbreviation_expander


def expand_abbreviations(text: str) -> str:
    """
    Convenience function to expand abbreviations in text.

    Args:
        text: Input text

    Returns:
        Expanded text
    """
    expander = get_abbreviation_expander()
    return expander.expand(text).expanded


def expand_abbreviations_detailed(text: str) -> ExpansionResult:
    """
    Convenience function to expand abbreviations with full details.

    Args:
        text: Input text

    Returns:
        ExpansionResult with full expansion details
    """
    expander = get_abbreviation_expander()
    return expander.expand(text)


# Test function
def test_abbreviation_expander():
    """Test the abbreviation expander with sample inputs."""
    expander = AbbreviationExpander()

    test_cases = [
        # Basic expansions
        ("BT M200", "Bê tông M200"),
        ("BTCT móng", "Bê tông cốt thép móng"),
        ("VK gỗ", "Ván khuôn gỗ"),
        ("CT D16", "Cốt thép D16"),
        ("BT M200 cột, VK gỗ, CT D16 CB400", "Bê tông M200 cột, Ván khuôn gỗ, Cốt thép D16 CB400"),

        # Case preservation
        ("bt m200", "bê tông m200"),
        ("BTCT DẦM", "Bê tông cốt thép DẦM"),  # Abbreviations always expand to sentence case

        # Tech spec preservation
        ("BT M350", "Bê tông M350"),
        ("CT D16 CB400", "Cốt thép D16 CB400"),

        # BTN vs BT (longer should match first)
        ("BTN lớp trên", "Bê tông nhựa lớp trên"),

        # CPĐD
        ("CPĐD loại 1", "Cấp phối đá dăm loại 1"),
        ("CPDD loại 1", "Cấp phối đá dăm loại 1"),

        # Word boundary (should NOT expand)
        ("BTM200", "BTM200"),  # No space, not an abbreviation

        # MEP
        ("PCCC tầng 1", "Phòng cháy chữa cháy tầng 1"),
        ("ĐHKK phòng họp", "Điều hòa không khí phòng họp"),
    ]

    print("=" * 80)
    print("ABBREVIATION EXPANDER TEST")
    print("=" * 80)

    passed = 0
    failed = 0

    for input_text, expected in test_cases:
        result = expander.expand(input_text)
        actual = result.expanded

        if actual == expected:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1

        print(f"\nInput:    {input_text}")
        print(f"Expected: {expected}")
        print(f"Actual:   {actual}")
        print(f"Status:   {status}")
        if result.expansions_applied:
            print(f"Expansions: {result.expansions_applied}")
        if result.tech_specs_preserved:
            print(f"Tech specs: {result.tech_specs_preserved}")
        print("-" * 40)

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    test_abbreviation_expander()
