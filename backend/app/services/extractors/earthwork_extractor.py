"""
Context-aware extractor for earthwork (Công tác đất).

Extracts specs specific to earthwork including:
- Compaction level (K90, K95, K98)
- Soil source (mua mới, tận dụng)
- Destination (bãi thải, nội bộ)
- Soil classification (đất cấp 3, đất không thích hợp)
"""
import re
from typing import Dict
from .base_extractor import BaseExtractor


class EarthworkExtractor(BaseExtractor):
    """Extract specs specific to earthwork (Đào/Đắp)."""

    def extract(self, text: str) -> Dict:
        """
        Extract earthwork specs.

        Args:
            text: Input description

        Returns:
            Dict with keys: compaction, source, destination, soil_type, context
        """
        specs = {}
        text_lower = text.lower()

        # Extract compaction level (K90, K95, K98, K=0.95, K=0,95)
        k_match = re.search(r'[Kk][=]?\s*(0[.,])?(\d{2})', text)
        if k_match:
            k_value = k_match.group(2)
            specs['compaction'] = f"Đất K{k_value}"

        # Extract soil source (mua mới, tận dụng)
        if 'mua mới' in text_lower or 'mua' in text_lower and 'đất' in text_lower:
            specs['source'] = 'Mua mới'
        elif 'tận dụng' in text_lower:
            if 'nội bộ' in text_lower or 'công trường' in text_lower:
                specs['source'] = 'Tận dụng nội bộ'
            else:
                specs['source'] = 'Tận dụng'

        # Extract destination (bãi đổ, nội bộ)
        if 'bãi đổ' in text_lower or 'bãi thải' in text_lower or 'ra bãi' in text_lower:
            specs['destination'] = 'Ra bãi thải'
        elif 'nội bộ' in text_lower or 'trong phạm vi' in text_lower:
            specs['destination'] = 'Nội bộ dự án'

        # Extract soil classification
        if 'không thích hợp' in text_lower:
            specs['soil_type'] = 'Đất không thích hợp'
        elif 'cấp 3' in text_lower or 'cấp iii' in text_lower:
            specs['soil_type'] = 'Đất cấp 3'
        elif 'cấp 4' in text_lower or 'cấp iv' in text_lower:
            specs['soil_type'] = 'Đất cấp 4'

        # Extract context (cống, mương, hố ga, nền đường)
        # Can have multiple contexts in one description
        context_patterns = [
            ('nền đường', 'Nền đường'),
            ('cống hộp đôi', 'Cống hộp đôi'),
            ('cống hộp', 'Cống hộp'),
            ('cống', 'Cống'),
            ('mương', 'Mương'),
            ('hố ga', 'Hố ga'),
            ('hiện trạng', 'Hiện trạng'),
        ]
        contexts = []
        for pattern, value in context_patterns:
            if pattern in text_lower:
                # Avoid adding sub-patterns if parent already added
                if value not in contexts and not any(value in c for c in contexts):
                    contexts.append(value)
        # Only add "Móng" if no other context found
        if not contexts and 'móng' in text_lower:
            contexts.append('Móng')
        if contexts:
            specs['context'] = '/'.join(contexts)

        # Extract transport content (đất, phế thải)
        if 'phế thải' in text_lower:
            if 'đất' in text_lower:
                specs['material'] = 'Đất/Phế thải'
            else:
                specs['material'] = 'Phế thải'
        elif 'đất đào' in text_lower:
            specs['material'] = 'Đất đào'
        elif 'đất' in text_lower and 'cát' in text_lower:
            specs['material'] = 'Đất/Cát'

        return specs
