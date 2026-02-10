"""
Context-aware extractor for Ván khuôn (Formwork).

Extracts specs specific to formwork including:
- Position (móng, cột, dầm, sàn, vách)
- Type (phủ phim, thép, gỗ, nhựa)
- Dimensions
"""
import re
from typing import Dict, List, Optional
from .base_extractor import BaseExtractor


class FormworkExtractor(BaseExtractor):
    """Extract specs specific to formwork."""

    # Vị trí cấu kiện (structural positions)
    POSITIONS = [
        'lót móng', 'đế móng', 'bệ móng', 'đài móng', 'giằng móng',
        'móng', 'cột', 'dầm sàn', 'dầm', 'sàn', 'vách', 'tường',
        'lanh tô', 'ô văng', 'trần', 'cầu thang',
        'khóa mái', 'khoa mai',  # Canal lock cover
    ]

    # Loại ván khuôn (formwork types)
    TYPES = {
        'phủ phim': 'Phủ phim',
        'phu phim': 'Phủ phim',
        'thép': 'Thép',
        'thep': 'Thép',
        'gỗ': 'Gỗ',
        'go': 'Gỗ',
        'nhựa': 'Nhựa',
        'nhua': 'Nhựa',
        'ván ép': 'Ván ép',
        'van ep': 'Ván ép',
    }

    def extract(self, text: str) -> Dict:
        """
        Extract formwork-specific specs.

        Args:
            text: Input description

        Returns:
            Dict with keys: position, type, dimensions, thickness
        """
        specs = {}
        text_lower = text.lower()

        # Extract position (longest match first)
        sorted_positions = sorted(self.POSITIONS, key=len, reverse=True)
        for pos in sorted_positions:
            if pos in text_lower:
                specs['position'] = pos.capitalize()
                break

        # Extract type
        sorted_types = sorted(self.TYPES.items(), key=lambda x: len(x[0]), reverse=True)
        for type_key, type_val in sorted_types:
            if type_key in text_lower:
                specs['type'] = type_val
                break

        # NOTE: Removed default type imputation to prevent hallucination (Bug 3)
        # If input doesn't specify formwork type, don't assume "Phủ phim"
        # The user can specify type via imputation_rules.py with explicit config
        # if 'type' not in specs:
        #     specs['type'] = 'Phủ phim'  # REMOVED: Causes hallucination

        # Extract dimensions
        dimensions = self._extract_dimensions(text)
        if dimensions:
            specs['dimensions'] = dimensions

        # Extract thickness (for formwork panels)
        thickness_match = re.search(r'dày\s*(\d+(?:\.\d+)?)\s*mm', text_lower)
        if thickness_match:
            specs['thickness'] = f"dày {thickness_match.group(1)}mm"

        return specs

    def get_position_weight(self, position: str) -> int:
        """
        Get weight for position (for sorting/priority).

        Higher weight = more important/common position.
        """
        weights = {
            'dầm sàn': 10,
            'sàn': 9,
            'cột': 8,
            'dầm': 7,
            'móng': 6,
            'vách': 5,
            'tường': 4,
            'cầu thang': 3,
        }
        return weights.get(position.lower(), 1)
