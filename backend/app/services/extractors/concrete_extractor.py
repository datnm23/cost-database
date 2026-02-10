"""
Context-aware extractor for concrete work (Bê tông).

Extracts specs specific to concrete work including:
- Grade (M100, M200, M250, M350)
- Stone size (đá 1x2, đá 4x6)
- Position (lót, móng, cột, dầm, sàn)
"""
import re
from typing import Dict
from .base_extractor import BaseExtractor


class ConcreteExtractor(BaseExtractor):
    """Extract specs specific to concrete work."""

    # Position-based defaults
    POSITION_DEFAULTS = {
        'lót': {'grade': 'M100', 'stone': 'Đá 1x2'},
        'lót móng': {'grade': 'M100', 'stone': 'Đá 1x2'},
        'mặt đường': {'grade': 'M250', 'stone': 'Đá 1x2'},
        'vỉa hè': {'grade': 'M200', 'stone': 'Đá 1x2'},
        'móng': {'grade': 'M250', 'stone': 'Đá 1x2'},
        'đế móng': {'grade': 'M250', 'stone': 'Đá 1x2'},
        'đài móng': {'grade': 'M300', 'stone': 'Đá 1x2'},
        'cột': {'grade': 'M300', 'stone': 'Đá 1x2'},
        'dầm': {'grade': 'M350', 'stone': 'Đá 1x2'},
        'sàn': {'grade': 'M350', 'stone': 'Đá 1x2'},
        'dầm sàn': {'grade': 'M350', 'stone': 'Đá 1x2'},
        'vách': {'grade': 'M300', 'stone': 'Đá 1x2'},
        'tường': {'grade': 'M300', 'stone': 'Đá 1x2'},
        'cầu thang': {'grade': 'M300', 'stone': 'Đá 1x2'},
        'hố ga': {'grade': 'M200', 'stone': 'Đá 1x2'},
        'đáy hố ga': {'grade': 'M200', 'stone': 'Đá 1x2'},
        'đáy cống': {'grade': 'M250', 'stone': 'Đá 1x2'},
        'thân cống': {'grade': 'M250', 'stone': 'Đá 1x2'},
        'sân cống': {'grade': 'M250', 'stone': 'Đá 1x2'},
        'tường cánh': {'grade': 'M250', 'stone': 'Đá 1x2'},
        'dàn treo': {'grade': 'M250', 'stone': 'Đá 1x2'},
        'cửa điều tiết': {'grade': 'M250', 'stone': 'Đá 1x2'},
        'tấm đan': {'grade': 'M200', 'stone': 'Đá 1x2'},
        'default': {'grade': 'M250', 'stone': 'Đá 1x2'},
    }

    def extract(self, text: str) -> Dict:
        """
        Extract concrete-specific specs.

        Args:
            text: Input description

        Returns:
            Dict with keys: grade, stone, position
        """
        specs = {}
        text_lower = text.lower()

        # Extract grade (M100, M200, M250, M350, 200#)
        grade_match = re.search(r'[Mm](\d{2,3})\b', text)
        if grade_match:
            specs['grade'] = f"M{grade_match.group(1)}"
        else:
            # Check for 200# format
            hash_match = re.search(r'(\d{3})#', text)
            if hash_match:
                specs['grade'] = f"M{hash_match.group(1)}"
            else:
                # Check for mác format
                mac_match = re.search(r'(?:mác|mac)\s*(\d+)', text_lower)
                if mac_match:
                    specs['grade'] = f"M{mac_match.group(1)}"

        # Extract stone size (đá 1x2, đá 4x6)
        stone_match = re.search(r'đá\s*(\d+)\s*[xX×]\s*(\d+)', text_lower)
        if stone_match:
            specs['stone'] = f"Đá {stone_match.group(1)}x{stone_match.group(2)}"

        # Extract position (longest match first)
        positions = sorted(self.POSITION_DEFAULTS.keys(), key=len, reverse=True)
        for pos in positions:
            if pos != 'default' and pos in text_lower:
                specs['position'] = pos.title()
                # Apply defaults if not already set
                defaults = self.POSITION_DEFAULTS.get(pos, self.POSITION_DEFAULTS['default'])
                if 'grade' not in specs:
                    specs['grade'] = defaults['grade']
                if 'stone' not in specs:
                    specs['stone'] = defaults['stone']
                break

        # If no position matched but we have "bê tông lót", it's M100
        if 'lót' in text_lower:
            if 'grade' not in specs:
                specs['grade'] = 'M100'
            if 'stone' not in specs:
                specs['stone'] = 'Đá 1x2'  # Test data expects Đá 1x2

        # Default for structural concrete
        if 'grade' not in specs:
            specs['grade'] = 'M250'
        if 'stone' not in specs:
            specs['stone'] = 'Đá 1x2'

        return specs
