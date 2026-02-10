"""
Context-aware extractor for Road construction.

Extracts specs specific to road work including:
- Layer (lớp trên, lớp dưới, loại 1, loại 2)
- Asphalt grade (C12.5, C19)
- Compaction (K95, K98)
- Thickness
"""
import re
from typing import Dict, Optional
from .base_extractor import BaseExtractor


class RoadExtractor(BaseExtractor):
    """Extract specs specific to road construction."""

    # Layer keywords
    LAYERS = {
        'lớp trên': 'Lớp trên',
        'lop tren': 'Lớp trên',
        'lớp dưới': 'Lớp dưới',
        'lop duoi': 'Lớp dưới',
        'loại 1': 'Loại I',
        'loai 1': 'Loại I',
        'loại i': 'Loại I',
        'loại 2': 'Loại II',
        'loai 2': 'Loại II',
        'loại ii': 'Loại II',
        'lớp móng trên': 'Lớp móng trên',
        'lop mong tren': 'Lớp móng trên',
        'lớp móng dưới': 'Lớp móng dưới',
        'lop mong duoi': 'Lớp móng dưới',
    }

    # Road material types
    MATERIALS = {
        'btn': 'BTN',
        'bê tông nhựa': 'BTN',
        'be tong nhua': 'BTN',
        'cpđd': 'CPĐD',
        'cấp phối đá dăm': 'CPĐD',
        'cap phoi da dam': 'CPĐD',
        'cấp phối': 'CPĐD',
        'cap phoi': 'CPĐD',
        'đá dăm': 'Đá dăm',
        'da dam': 'Đá dăm',
        'nhựa đường': 'Nhựa đường',
        'nhua duong': 'Nhựa đường',
    }

    def extract(self, text: str) -> Dict:
        """
        Extract road-specific specs.

        Args:
            text: Input description

        Returns:
            Dict with keys: layer, material, asphalt_grade, compaction, thickness
        """
        specs = {}
        text_lower = text.lower()

        # Extract layer (QUAN TRỌNG: không được mất thông tin lớp)
        sorted_layers = sorted(self.LAYERS.items(), key=lambda x: len(x[0]), reverse=True)
        for layer_key, layer_val in sorted_layers:
            if layer_key in text_lower:
                specs['layer'] = layer_val
                break

        # Extract material
        sorted_materials = sorted(self.MATERIALS.items(), key=lambda x: len(x[0]), reverse=True)
        for mat_key, mat_val in sorted_materials:
            if mat_key in text_lower:
                specs['material'] = mat_val
                break

        # Extract asphalt grade (C12.5, C19, etc.) - KHÔNG được mất
        grade_match = re.search(r'[Cc](\d+(?:\.\d+)?)', text)
        if grade_match:
            specs['asphalt_grade'] = f"C{grade_match.group(1)}"

        # Extract compaction (K95, K98, etc.)
        compaction_match = re.search(r'[Kk](\d{2})', text)
        if compaction_match:
            specs['compaction'] = f"K{compaction_match.group(1)}"

        # Extract thickness
        thickness_patterns = [
            (r'dày\s*(\d+(?:\.\d+)?)\s*cm', 'cm'),
            (r'dày\s*(\d+(?:\.\d+)?)\s*mm', 'mm'),
            (r'dày\s*(\d+(?:\.\d+)?)', 'cm'),  # Default to cm if no unit
        ]
        for pattern, unit in thickness_patterns:
            thickness_match = re.search(pattern, text_lower)
            if thickness_match:
                specs['thickness'] = f"dày {thickness_match.group(1)}{unit}"
                break

        return specs

    def get_layer_order(self, layer: str) -> int:
        """
        Get order for layer (for proper sequencing).

        Lower number = processed first (bottom layer).
        """
        order = {
            'lớp móng dưới': 1,
            'lớp dưới': 2,
            'loại ii': 2,
            'lớp móng trên': 3,
            'lớp trên': 4,
            'loại i': 4,
        }
        return order.get(layer.lower(), 5)
