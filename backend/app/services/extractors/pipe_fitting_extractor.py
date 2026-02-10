"""
Context-aware extractor for pipe fittings (Phụ kiện ống).

Extracts specs specific to pipe fittings including:
- Material (HDPE, PPR, uPVC, Gang, Thép)
- Angle (45 độ, 90 độ, 135 độ)
- Diameter (D200, DN80, D315)
- Reduction sizes (D200-D160, D50/32)
- Pressure rating (PN8, PN10)
- Connection type (Nối bích, Ren, Hàn)
"""
import re
from typing import Dict
from .base_extractor import BaseExtractor


class PipeFittingExtractor(BaseExtractor):
    """Extract specs specific to pipe fittings."""

    # Materials for pipe fittings
    MATERIALS = {
        'hdpe': 'HDPE',
        'ppr': 'PPR',
        'u.pvc': 'uPVC',
        'upvc': 'uPVC',
        'pvc': 'PVC',
        'gang': 'Gang',
        'thép tráng kẽm': 'Thép Tráng kẽm',
        'thep trang kem': 'Thép Tráng kẽm',
        'ttk': 'Thép Tráng kẽm',
        'thép đen': 'Thép đen',
        'thep den': 'Thép đen',
        'thép': 'Thép',
        'thep': 'Thép',
        'đồng': 'Đồng',
        'dong': 'Đồng',
        'inox': 'Inox',
    }

    # Connection types
    CONNECTION_TYPES = {
        'nối bích': 'Nối bích',
        'noi bich': 'Nối bích',
        'bb': 'Nối bích',  # Body/Body (Bích)
        'be': 'BE',  # Flange/Spigot
        'ee': 'EE',  # End/End
        'ren trong': 'Ren trong',
        'ren ngoài': 'Ren ngoài',
        'ren ngoai': 'Ren ngoài',
        'hàn': 'Hàn',
        'han': 'Hàn',
        'ren đồng': 'Đồng ren',
        'ren dong': 'Đồng ren',
        'ren': 'Ren',
    }

    def extract(self, text: str) -> Dict:
        """
        Extract pipe fitting specs.

        Args:
            text: Input description

        Returns:
            Dict with keys: material, angle, diameter, reduction, pressure, connection
        """
        specs = {}
        text_lower = text.lower()

        # Extract material (longest match first)
        sorted_materials = sorted(self.MATERIALS.items(), key=lambda x: len(x[0]), reverse=True)
        for mat_key, mat_val in sorted_materials:
            if mat_key in text_lower:
                specs['material'] = mat_val
                break

        # Extract angle (45 độ, 90 độ, 135 độ)
        angle_match = re.search(r'(\d+)\s*(?:độ|do)', text_lower)
        if angle_match:
            specs['angle'] = f"{angle_match.group(1)} độ"

        # Extract diameter patterns
        # Pattern 1: D200-D140 or D50-25 (reduction with dash)
        reduction_match = re.search(r'[Dd](\d+)\s*[-]\s*[Dd]?(\d+)', text)
        if reduction_match:
            specs['diameter'] = f"D{reduction_match.group(1)}/{reduction_match.group(2)}"
        else:
            # Pattern 2: D200/140 or D50/32 (reduction with slash)
            slash_match = re.search(r'[Dd](\d+)\s*/\s*(\d+)', text)
            if slash_match:
                specs['diameter'] = f"D{slash_match.group(1)}/{slash_match.group(2)}"
            else:
                # Pattern 3: D110 ra D50 (explicit reduction)
                ra_match = re.search(r'[Dd](\d+)\s*ra\s*[Dd]?(\d+)', text_lower)
                if ra_match:
                    specs['diameter'] = f"D{ra_match.group(1)}/{ra_match.group(2)}"
                else:
                    # Pattern 4: đường kính 315mm
                    dk_match = re.search(r'đường kính\s*(\d+)\s*mm', text_lower)
                    if dk_match:
                        specs['diameter'] = f"D{dk_match.group(1)}"
                    else:
                        # Pattern 5: 195/150 (no D prefix)
                        double_match = re.search(r'(\d{2,3})\s*/\s*(\d{2,3})', text)
                        if double_match:
                            specs['diameter'] = f"D{double_match.group(1)}/{double_match.group(2)}"
                        else:
                            # Pattern 6: Simple diameter D200 or DN80
                            diam_match = re.search(r'[Dd][Nn]?(\d{2,4})', text)
                            if diam_match:
                                prefix = 'DN' if 'dn' in text_lower else 'D'
                                specs['diameter'] = f"{prefix}{diam_match.group(1)}"

        # phi diameter format (phi 9.52, phi9.52, φ9.52)
        if 'diameter' not in specs:
            phi_match = re.search(r'(?:phi|φ)\s*(\d+(?:[.,]\d+)?)', text_lower)
            if phi_match:
                specs['diameter'] = f"phi {phi_match.group(1).replace(',', '.')}"

        # Extract pressure rating (PN8, PN10, PN16)
        pn_match = re.search(r'[Pp][Nn]\s*(\d+)', text)
        if pn_match:
            specs['pressure'] = f"PN{pn_match.group(1)}"

        # Extract connection type (longest match first)
        sorted_connections = sorted(self.CONNECTION_TYPES.items(), key=lambda x: len(x[0]), reverse=True)
        for conn_key, conn_val in sorted_connections:
            if conn_key in text_lower:
                specs['connection'] = conn_val
                break

        # Extract load rating for covers (D400, B125, etc.)
        load_match = re.search(r'\b([ABCD])(\d+)\b', text)
        if load_match:
            specs['load_rating'] = f"{load_match.group(1)}{load_match.group(2)}"

        # Extract position (lòng đường, vỉa hè)
        if 'lòng đường' in text_lower or 'long duong' in text_lower:
            specs['position'] = 'Lòng đường'
        elif 'vỉa hè' in text_lower or 'via he' in text_lower:
            specs['position'] = 'Vỉa hè'

        # Extract tay gạt for valves
        if 'tay gạt' in text_lower or 'tay gat' in text_lower:
            specs['handle'] = 'Tay gạt'

        return specs
