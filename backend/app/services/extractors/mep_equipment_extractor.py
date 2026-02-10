"""
Context-aware extractor for MEP equipment.

Extracts specs specific to MEP equipment including:
- Electrical meters (Công tơ)
- Indicator lights (Đèn báo pha)
- Lighting fixtures (Cột đèn, Đèn chiếu sáng)
- Grounding rods (Cọc tiếp địa)
- Cable specifications
- Fire equipment (Trụ cứu hỏa, Bình chữa cháy)
"""
import re
from typing import Dict
from .base_extractor import BaseExtractor


class MEPEquipmentExtractor(BaseExtractor):
    """Extract specs specific to MEP equipment."""

    def extract(self, text: str) -> Dict:
        """
        Extract MEP equipment specs.

        Args:
            text: Input description

        Returns:
            Dict with extracted specifications
        """
        specs = {}
        text_lower = text.lower()

        # Extract poles/phases (1P, 3P)
        poles_match = re.search(r'(\d+)\s*[Pp](?:ha|oles?)?(?:\s|[-,]|$)', text)
        if poles_match:
            specs['poles'] = f"{poles_match.group(1)}P"

        # Extract current rating for meters (10(40)A, 20(40)A)
        meter_current = re.search(r'(\d+)\s*\(\s*(\d+)\s*\)\s*[Aa]', text)
        if meter_current:
            specs['current'] = f"{meter_current.group(1)}({meter_current.group(2)})A"
        else:
            # Simple current (5A, 10A)
            current_match = re.search(r'(\d+)\s*[Aa](?:\s|$|,)', text)
            if current_match:
                specs['current'] = f"{current_match.group(1)}A"

        # Extract voltage (220V, 500V)
        voltage_match = re.search(r'(\d+)\s*[Vv]', text)
        if voltage_match:
            specs['voltage'] = f"{voltage_match.group(1)}V"

        # Extract colors for indicator lights (xanh, đỏ, vàng)
        colors = []
        color_map = {
            'xanh': 'Xanh',
            'đỏ': 'Đỏ',
            'do': 'Đỏ',
            'vàng': 'Vàng',
            'vang': 'Vàng',
        }
        for color_key, color_val in color_map.items():
            if color_key in text_lower:
                if color_val not in colors:
                    colors.append(color_val)
        if colors:
            specs['colors'] = ', '.join(colors)

        # Extract height for poles (H8m, cao 8m)
        height_match = re.search(r'(?:[Hh]|cao\s*)(\d+(?:\.\d+)?)\s*m', text)
        if height_match:
            specs['height'] = f"H{height_match.group(1)}m"

        # Extract pole type (cần đơn, cần đôi, bát giác côn)
        if 'bát giác côn' in text_lower or 'bat giac con' in text_lower:
            specs['pole_type'] = 'Bát giác côn'
        if 'cần đơn' in text_lower or 'can don' in text_lower:
            specs['arm_type'] = 'Cần đơn'
        elif 'cần đôi' in text_lower or 'can doi' in text_lower:
            specs['arm_type'] = 'Cần đôi'

        # Extract light specs (LED, wattage)
        led_match = re.search(r'[Ll][Ee][Dd]\s*(\d+)\s*[Ww]', text)
        if led_match:
            specs['light_spec'] = f"LED {led_match.group(1)}W"

        # Extract lamp/fixture type (cầu D400)
        cau_match = re.search(r'(?:cầu|cau)\s*[Dd]?(\d+)', text_lower)
        if cau_match:
            specs['fixture_type'] = f"Cầu D{cau_match.group(1)}"

        # Extract grounding rod specs (L63x63x6, 2.5m)
        l_profile = re.search(r'[Ll](\d+)\s*[xX×]\s*(\d+)\s*[xX×]\s*(\d+)', text)
        if l_profile:
            specs['profile'] = f"Thép L{l_profile.group(1)}x{l_profile.group(2)}x{l_profile.group(3)}"

        # Extract length for rods
        length_match = re.search(r'(\d+(?:[.,]\d+)?)\s*m(?:\s|$|,)', text)
        if length_match:
            length_val = length_match.group(1).replace(',', '.')
            specs['length'] = f"L{length_val}m"

        # Extract diameter for pipes and fixtures
        diam_match = re.search(r'[Dd][Nn]?(\d{2,4})', text)
        if diam_match:
            prefix = 'DN' if 'dn' in text_lower else 'D'
            specs['diameter'] = f"{prefix}{diam_match.group(1)}"

        # Extract cable specifications (3x35+1x16mm2, 4X240mm2)
        cable_match = re.search(r'(\d+)\s*[xX×]\s*(\d+)(?:\s*\+\s*\d+\s*[xX×]\s*\d+)?\s*mm2?', text)
        if cable_match:
            # Get the full cable spec
            full_cable = re.search(r'(\d+\s*[xX×]\s*\d+(?:\s*\+\s*\d+\s*[xX×]\s*\d+)?)\s*mm2?', text)
            if full_cable:
                cable_spec = full_cable.group(1).lower().replace('×', 'x')
                specs['cable_size'] = f"{cable_spec}mm2"

        # Extract cable type (Cu/XLPE/PVC)
        cable_type = re.search(r'([Cc]u[\-/][A-Za-z/]+)', text)
        if cable_type:
            specs['cable_type'] = cable_type.group(1)

        # Extract fire extinguisher type (CO2, MT3)
        if 'co2' in text_lower:
            specs['ext_type'] = 'CO2'
        mt_match = re.search(r'[Mm][Tt](\d+)', text)
        if mt_match:
            specs['ext_model'] = f"MT{mt_match.group(1)}"

        # Extract switch type (Ampe, Vol)
        if 'ampe' in text_lower:
            specs['switch_type'] = 'Ampe'
        elif 'vol' in text_lower:
            specs['switch_type'] = 'Vol'

        # Extract material for general equipment
        if 'gang' in text_lower:
            specs['material'] = 'Gang'
        elif 'thép sơn tĩnh điện' in text_lower:
            specs['material'] = 'Thép sơn tĩnh điện'
        elif 'inox' in text_lower:
            specs['material'] = 'Inox'
        elif 'composite' in text_lower:
            specs['material'] = 'Composite'

        return specs
