"""
Context-aware extractor for Precast components.

Extracts specs specific to precast elements including:
- Material (BTCT, gang, nhựa)
- Dimensions (MUST find for precast)
- Variant (from parentheses content)
"""
import re
from typing import Dict, Optional
from .base_extractor import BaseExtractor


class PrecastExtractor(BaseExtractor):
    """Extract specs specific to precast components."""

    # Precast materials
    MATERIALS = {
        'btct': 'BTCT',
        'bê tông cốt thép': 'BTCT',
        'be tong cot thep': 'BTCT',
        'bê tông': 'Bê tông',
        'be tong': 'Bê tông',
        'gang': 'Gang',
        'nhựa': 'Nhựa',
        'nhua': 'Nhựa',
        'composite': 'Composite',
        'đá granite': 'Đá Granite',
        'da granite': 'Đá Granite',
        'đá tự nhiên': 'Đá tự nhiên',
        'da tu nhien': 'Đá tự nhiên',
        # For Bó vỉa đá - treat standalone 'đá' as 'Đá tự nhiên' for curbs
        'đá': 'Đá',
        'da': 'Đá',
    }

    # Default materials for specific component types
    COMPONENT_DEFAULT_MATERIALS = {
        'curb': 'Đá tự nhiên',  # Bó vỉa defaults to natural stone
        'cover': 'Đá',  # Tấm đan defaults to stone
    }

    # Component types (for classification)
    COMPONENT_TYPES = {
        'bó vỉa': 'curb',
        'bo via': 'curb',
        'tấm đan': 'cover',
        'tam dan': 'cover',
        'cống': 'culvert',
        'cong': 'culvert',
        'hố ga': 'manhole',
        'ho ga': 'manhole',
        'rãnh': 'channel',
        'ranh': 'channel',
    }

    def extract(self, text: str) -> Dict:
        """
        Extract precast-specific specs.

        Args:
            text: Input description

        Returns:
            Dict with keys: material, dimensions, variant, component_type
        """
        specs = {}
        text_lower = text.lower()

        # Extract component type
        for type_key, type_val in self.COMPONENT_TYPES.items():
            if type_key in text_lower:
                specs['component_type'] = type_val
                break

        # Extract material
        sorted_materials = sorted(self.MATERIALS.items(), key=lambda x: len(x[0]), reverse=True)
        for mat_key, mat_val in sorted_materials:
            if mat_key in text_lower:
                specs['material'] = mat_val
                break

        # For curbs (Bó vỉa), if material is just "Đá", upgrade to "Đá tự nhiên"
        if specs.get('component_type') == 'curb' and specs.get('material') == 'Đá':
            specs['material'] = 'Đá tự nhiên'

        # Extract dimensions (MUST find for precast)
        dimensions = self._extract_dimensions(text)
        if dimensions:
            specs['dimensions'] = dimensions

        # Extract from parentheses (often contains critical specs)
        paren_match = re.search(r'\(([^)]+)\)', text)
        if paren_match:
            paren_content = paren_match.group(1).strip()

            # Check if it's dimensions
            if re.match(r'\d+\s*[xX×]\s*\d+', paren_content):
                if 'dimensions' not in specs:
                    specs['dimensions'] = paren_content.replace(' ', '')
            else:
                # It's a variant specification
                specs['variant'] = paren_content

        # Extract KT (kích thước) format: KT 230x260x1000
        kt_match = re.search(r'[Kk][Tt]\s*(\d+)\s*[xX×]\s*(\d+)(?:\s*[xX×]\s*(\d+))?', text)
        if kt_match and 'dimensions' not in specs:
            dims = [kt_match.group(1), kt_match.group(2)]
            if kt_match.group(3):
                dims.append(kt_match.group(3))
            specs['dimensions'] = 'x'.join(dims)

        # Extract diameter for circular elements (cống tròn)
        if specs.get('component_type') == 'culvert':
            diam_match = re.search(r'[Dd](\d{3,4})', text)
            if diam_match:
                specs['diameter'] = f"D{diam_match.group(1)}"

        # Extract height for manholes
        if specs.get('component_type') == 'manhole':
            height = self._extract_height(text)
            if height:
                specs['height'] = height

        return specs

    def validate_precast_specs(self, specs: Dict) -> bool:
        """
        Validate that required specs are present for precast.

        Args:
            specs: Extracted specifications

        Returns:
            True if required specs are present
        """
        # Precast should have at least dimensions or diameter
        return 'dimensions' in specs or 'diameter' in specs
