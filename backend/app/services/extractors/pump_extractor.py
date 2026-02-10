"""
Context-aware extractor for pumps (Bơm).

Extracts specs specific to pumps including:
- Flow rate (Q=80l/s, Q=110m3/h)
- Head (H=56m, H=30m)
- Power (P=75kW, P=7.5kW)
- Type (trục ngang, trục đứng, điện)
- Volume (200L) for pressure tanks
- Pressure (16bar) for pressure tanks
"""
import re
from typing import Dict
from .base_extractor import BaseExtractor


class PumpExtractor(BaseExtractor):
    """Extract specs specific to pumps."""

    def extract(self, text: str) -> Dict:
        """
        Extract pump specs.

        Args:
            text: Input description

        Returns:
            Dict with keys: flow_rate, head, power, type, volume, pressure
        """
        specs = {}
        text_lower = text.lower()

        # Extract pump type
        type_parts = []
        if 'bơm điện' in text_lower or 'bom dien' in text_lower:
            type_parts.append('Điện')
        if 'trục ngang' in text_lower or 'truc ngang' in text_lower:
            type_parts.append('trục ngang')
        elif 'trục đứng' in text_lower or 'truc dung' in text_lower:
            type_parts.append('Trục đứng')
        elif 'bình đứng' in text_lower or 'binh dung' in text_lower:
            type_parts.append('Đứng')

        if type_parts:
            specs['type'] = ' '.join(type_parts)
        elif 'điện' not in text_lower and 'bơm' in text_lower:
            # Default to electric pump if not specified
            specs['type'] = 'Điện'

        # Extract flow rate (Q=80l/s, Q=110m3/h)
        flow_match = re.search(r'[Qq]\s*[=:]\s*(\d+(?:\.\d+)?)\s*([lm][/]?[sh]|m3/h)', text)
        if flow_match:
            value = flow_match.group(1)
            unit = flow_match.group(2).replace(' ', '')
            specs['flow_rate'] = f"Q={value}{unit}"

        # Extract head (H=56m, H=30m)
        head_match = re.search(r'[Hh]\s*[=:]\s*(\d+(?:\.\d+)?)\s*m', text)
        if head_match:
            specs['head'] = f"H={head_match.group(1)}m"

        # Extract power (P=75kW, P=7.5kW)
        power_match = re.search(r'[Pp]\s*[=:]\s*(\d+(?:\.\d+)?)\s*[Kk][Ww]', text)
        if power_match:
            specs['power'] = f"P={power_match.group(1)}kW"

        # Extract volume for pressure tanks (200L)
        volume_match = re.search(r'(\d+)\s*[Ll](?:ít|it|itre)?(?:\s|,|$)', text)
        if volume_match:
            specs['volume'] = f"{volume_match.group(1)}L"

        # Extract pressure for tanks (16bar)
        bar_match = re.search(r'(\d+)\s*bar', text_lower)
        if bar_match:
            specs['pressure'] = f"{bar_match.group(1)}bar"

        # Extract pump purpose/application
        if 'chữa cháy' in text_lower or 'cứu hỏa' in text_lower:
            specs['purpose'] = 'Bơm chữa cháy'
        elif 'bù áp' in text_lower:
            specs['purpose'] = 'Bơm bù áp'
        elif 'thoát nước' in text_lower or 'nước thải' in text_lower:
            specs['purpose'] = 'Bơm chìm nước thải'

        return specs

    def format_pump_specs(self, specs: Dict) -> str:
        """
        Format pump specs for output.

        Args:
            specs: Extracted specs

        Returns:
            Formatted spec string (e.g., "Q=80l/s H=56m P=75kW")
        """
        parts = []
        for key in ['flow_rate', 'head', 'power', 'volume', 'pressure']:
            if key in specs:
                parts.append(specs[key])
        return ' '.join(parts)
