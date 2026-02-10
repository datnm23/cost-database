"""
Subtract-Back Extractor for BOQ Description Normalization.

Implements the "Subtract-Back Algorithm" with order: SPEC → MATERIAL → OBJECT
This reverse order prevents compound word splitting issues.
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from .dictionaries.objects import DICT_OBJECTS_SORTED
from .dictionaries.materials import DICT_MATERIALS, DICT_PRESSURE
from .dictionaries.specs import extract_specs


@dataclass
class ExtractedComponents:
    """Container for extracted description components."""
    object_name: Optional[str] = None
    material: Optional[str] = None
    specs: List[str] = field(default_factory=list)
    location: Optional[str] = None
    pressure_rating: Optional[str] = None
    remaining: str = ""
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'object_name': self.object_name,
            'material': self.material,
            'specs': self.specs,
            'location': self.location,
            'pressure_rating': self.pressure_rating,
            'remaining': self.remaining,
            'confidence': self.confidence,
        }


class SubtractBackExtractor:
    """
    Thuật toán "Trừ lùi" với thứ tự: SPEC → MATERIAL → OBJECT

    Key insight: Extract most deterministic patterns first (regex specs),
    then progressively less deterministic (dictionary lookups).
    This prevents compound words from being incorrectly split.

    Example:
        Input: "Ống thép mạ kẽm D114"

        Old (wrong) OBJECT→MATERIAL→SPEC:
            1. Match "Ống" → object="Ống", remain="thép mạ kẽm D114"
            2. Match "thép" → material="thép", remain="mạ kẽm D114"
            3. SPEC = "mạ kẽm D114" ← WRONG! "mạ kẽm" is material

        New (correct) SPEC→MATERIAL→OBJECT:
            1. Regex D\\d+ → specs=["D114"], remain="Ống thép mạ kẽm"
            2. Longest match material → material="thép mạ kẽm", remain="Ống"
            3. Match object → object="Ống"
            → Output: "Ống - thép mạ kẽm - D114" ✓
    """

    # Verbs to strip from input (auxiliary/general)
    VERBS_TO_STRIP = [
        'cung cấp', 'cung cap',
        'lắp đặt', 'lap dat', 'lắp dặt',
        'thi công', 'thi cong',
        'sản xuất', 'san xuat',
        'gia công', 'gia cong',
        # 'vận chuyển' - MOVED to VERBS_TO_KEEP (work-specific verb)
        'bơm', 'bom',
        'đổ', 'do',
        'và', 'va',
    ]

    # Verbs to keep (work-specific)
    VERBS_TO_KEEP = [
        # Earthwork
        'đào', 'dao',
        'đắp', 'dap',
        'san', 'lu',
        'đầm', 'dam',
        'rải', 'rai',
        # Transport (work-specific, keep it)
        'vận chuyển', 'van chuyen',
        # Finishing
        'xây', 'xay',
        'trát', 'trat',
        'lát', 'lat',
        'ốp', 'op',
        'sơn', 'son',
        'quét', 'quet',
    ]

    # Location keywords to extract separately
    LOCATION_KEYWORDS = [
        # Floor levels
        'tầng hầm', 'tầng trệt', 'tầng lửng',
        'tầng 1', 'tầng 2', 'tầng 3', 'tầng 4', 'tầng 5',
        'tầng 6', 'tầng 7', 'tầng 8', 'tầng 9', 'tầng 10',
        'tầng mái', 'tầng thượng', 'tầng kỹ thuật',
        'tang ham', 'tang tret', 'tang lung',
        'tang 1', 'tang 2', 'tang 3', 'tang 4', 'tang 5',
        # Indoor/Outdoor
        'trong nhà', 'ngoài nhà', 'ngoài trời',
        'trong nha', 'ngoai nha', 'ngoai troi',
        # Building areas
        'khu a', 'khu b', 'khu c', 'khu d',
        'khối a', 'khối b', 'khối c', 'khối d',
        'block a', 'block b', 'block c', 'block d',
        # Axis references
        'trục a', 'trục b', 'trục c', 'trục d',
        'truc a', 'truc b', 'truc c', 'truc d',
        # Rooms
        'phòng ngủ', 'phòng khách', 'phòng bếp', 'phòng wc',
        'phòng làm việc', 'hành lang', 'sảnh', 'ban công',
        # Structure positions
        'lót móng', 'lot mong',
        'đáy móng', 'day mong',
        'thân móng', 'than mong',
    ]

    def __init__(self):
        """Initialize extractor with sorted dictionaries."""
        # Sort materials by length for longest match
        self._materials_sorted = dict(
            sorted(DICT_MATERIALS.items(), key=lambda x: len(x[0]), reverse=True)
        )
        # Pressure ratings sorted
        self._pressure_sorted = dict(
            sorted(DICT_PRESSURE.items(), key=lambda x: len(x[0]), reverse=True)
        )
        # Location keywords sorted by length
        self._locations_sorted = sorted(
            self.LOCATION_KEYWORDS, key=len, reverse=True
        )

    def extract(self, text: str) -> ExtractedComponents:
        """
        Main extraction method using subtract-back algorithm.

        Args:
            text: Raw BOQ description

        Returns:
            ExtractedComponents with parsed fields
        """
        result = ExtractedComponents(specs=[])

        # Pre-process: normalize and clean
        working_text = self._preprocess(text)

        # Step 0: Extract location first (moves to separate field)
        location, working_text = self._extract_location(working_text)
        result.location = location

        # Step 1: Extract SPECS first (most deterministic - regex)
        specs, working_text = extract_specs(working_text)
        result.specs = specs

        # Step 1b: Extract pressure rating (special case)
        pressure, working_text = self._extract_pressure(working_text)
        result.pressure_rating = pressure

        # Step 2: Extract MATERIAL (longest match from dictionary)
        material, working_text = self._extract_material(working_text)
        result.material = material

        # Step 3: Extract OBJECT (longest match - last)
        object_name, working_text = self._extract_object(working_text)
        result.object_name = object_name

        # Store remaining text
        result.remaining = self._clean_remaining(working_text)

        # Calculate confidence score
        result.confidence = self._calculate_confidence(result)

        return result

    def _preprocess(self, text: str) -> str:
        """
        Preprocess text: lowercase, strip verbs, normalize.

        Args:
            text: Raw input text

        Returns:
            Cleaned text ready for extraction
        """
        # Convert to lowercase for matching
        working = text.lower().strip()

        # Remove auxiliary verbs (not work-specific)
        for verb in self.VERBS_TO_STRIP:
            # Match verb at word boundary
            pattern = rf'\b{re.escape(verb)}\b'
            working = re.sub(pattern, '', working, flags=re.IGNORECASE)

        # Normalize whitespace
        working = re.sub(r'\s+', ' ', working).strip()

        # Remove leading punctuation
        working = re.sub(r'^[\s,\-\.;:]+', '', working)

        return working

    def _extract_location(self, text: str) -> tuple[Optional[str], str]:
        """
        Extract location information from text.

        Args:
            text: Working text

        Returns:
            Tuple of (extracted location, remaining text)
        """
        text_lower = text.lower()
        extracted_location = None

        for loc in self._locations_sorted:
            if loc in text_lower:
                # Find the actual case-insensitive match
                pattern = re.compile(re.escape(loc), re.IGNORECASE)
                match = pattern.search(text)
                if match:
                    extracted_location = match.group(0).strip()
                    text = text[:match.start()] + text[match.end():]
                    text = re.sub(r'\s+', ' ', text).strip()
                    break

        return extracted_location, text

    def _extract_pressure(self, text: str) -> tuple[Optional[str], str]:
        """
        Extract pressure rating (PN) from text.

        Args:
            text: Working text

        Returns:
            Tuple of (pressure rating, remaining text)
        """
        text_lower = text.lower()
        extracted_pressure = None

        for pn_key, pn_value in self._pressure_sorted.items():
            if pn_key in text_lower:
                extracted_pressure = pn_value
                # Remove from text
                pattern = re.compile(re.escape(pn_key), re.IGNORECASE)
                text = pattern.sub('', text, count=1)
                text = re.sub(r'\s+', ' ', text).strip()
                break

        return extracted_pressure, text

    def _extract_material(self, text: str) -> tuple[Optional[str], str]:
        """
        Extract material using longest match from dictionary.

        Args:
            text: Working text

        Returns:
            Tuple of (material name, remaining text)
        """
        text_lower = text.lower()
        extracted_material = None

        for mat_key, mat_value in self._materials_sorted.items():
            if mat_key in text_lower:
                extracted_material = mat_value
                # Remove from text (case-insensitive)
                pattern = re.compile(re.escape(mat_key), re.IGNORECASE)
                text = pattern.sub('', text, count=1)
                text = re.sub(r'\s+', ' ', text).strip()
                break

        return extracted_material, text

    def _extract_object(self, text: str) -> tuple[Optional[str], str]:
        """
        Extract object name using longest match from dictionary.

        Args:
            text: Working text

        Returns:
            Tuple of (object name, remaining text)
        """
        text_lower = text.lower()
        extracted_object = None

        for obj_key, obj_value in DICT_OBJECTS_SORTED.items():
            if obj_key in text_lower:
                extracted_object = obj_value
                # Remove from text (case-insensitive)
                pattern = re.compile(re.escape(obj_key), re.IGNORECASE)
                text = pattern.sub('', text, count=1)
                text = re.sub(r'\s+', ' ', text).strip()
                break

        return extracted_object, text

    def _clean_remaining(self, text: str) -> str:
        """
        Clean remaining text after extraction.

        Args:
            text: Remaining text

        Returns:
            Cleaned remaining text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Remove leading/trailing punctuation
        text = re.sub(r'^[\s,\-\.;:()]+|[\s,\-\.;:()]+$', '', text)

        # Remove standalone numbers (likely orphaned from specs)
        text = re.sub(r'\b\d+\b', '', text)

        # Final cleanup
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _calculate_confidence(self, result: ExtractedComponents) -> float:
        """
        Calculate confidence score based on extraction completeness.

        Scoring:
        - Object found: +0.4
        - Material found: +0.3
        - Specs found: +0.2
        - Little remaining text: +0.1

        Args:
            result: Extracted components

        Returns:
            Confidence score between 0.0 and 1.0
        """
        score = 0.0

        if result.object_name:
            score += 0.4

        if result.material:
            score += 0.3

        if result.specs:
            score += 0.2

        # Bonus for clean extraction (little garbage left)
        remaining_len = len(result.remaining)
        if remaining_len == 0:
            score += 0.1
        elif remaining_len < 5:
            score += 0.05

        return min(score, 1.0)

    def assemble_output(self, components: ExtractedComponents) -> str:
        """
        Assemble normalized output from components.
        Enforces 3-component structure: OBJECT - MATERIAL - SPECS

        Args:
            components: Extracted components

        Returns:
            Normalized description string
        """
        parts = []

        # Part 1: Object name
        if components.object_name:
            parts.append(components.object_name)

        # Part 2: Material (with pressure rating if applicable)
        if components.material:
            mat_part = components.material
            if components.pressure_rating:
                mat_part = f"{mat_part} {components.pressure_rating}"
            parts.append(mat_part)
        elif components.pressure_rating:
            parts.append(components.pressure_rating)

        # Part 3: Specs (joined with space)
        if components.specs:
            specs_str = ' '.join(components.specs)
            parts.append(specs_str)

        # Ensure we have content
        if len(parts) == 0:
            return ""
        elif len(parts) == 1:
            return parts[0]
        elif len(parts) == 2:
            return f"{parts[0]} - {parts[1]}"
        else:
            # Standard 3-component format
            return f"{parts[0]} - {parts[1]} - {parts[2]}"

    def enforce_three_components(self, text: str) -> str:
        """
        Ensure output has exactly 3 components (max 2 dashes).

        Args:
            text: Input text with components

        Returns:
            Text with exactly 3 components
        """
        if ' - ' not in text:
            return text

        parts = text.split(' - ')

        if len(parts) <= 3:
            return text

        # Merge middle parts if more than 3
        return f"{parts[0]} - {' '.join(parts[1:-1])} - {parts[-1]}"
