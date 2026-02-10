"""
MEP Equipment Normalizer Service
Handles normalization of MEP (Mechanical, Electrical, Plumbing) equipment:
- Electrical panels (tủ điện)
- Circuit breakers (MCCB, MCB)
- Pipes (ống HDPE, PVC, PPR)
- Cables (cáp điện Cu/XLPE/PVC)
- Lighting (đèn)
"""
import re
from typing import Dict, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class MEPEquipmentResult:
    """Result of MEP equipment normalization"""
    original: str
    normalized: str
    equipment_type: str
    specs: Dict[str, str]
    confidence: float
    is_material_only: bool  # True if just material/equipment name without work verb


# Cable patterns - IMPROVED to preserve material info
CABLE_PATTERNS = {
    # Pattern: Cáp Cu/XLPE/PVC 4x300mm2 or Cáp đồng/XLPE/PVC 4X300
    'xlpe': {
        'pattern': r'[Cc]áp\s*(?:đồng|Cu)?[/\s]*(?:XLPE)[/\s]*(PVC|PE|DSTA)?\s*(\d+)[xX](\d+)\s*(?:mm2?)?',
        'template': 'Cáp Cu/XLPE/{jacket} - {cores}x{size}mm2',
    },
    # Pattern: Cáp đồng bọc PVC 1x6mm2
    'pvc_single': {
        'pattern': r'[Cc]áp\s*(?:đồng|Cu)?\s*(?:bọc\s*)?(PVC)\s*(\d+)[xX](\d+)\s*(?:mm2?)?',
        'template': 'Cáp Cu/PVC - {cores}x{size}mm2',
    },
    # Pattern: Dây điện 1x2.5mm2
    'wire': {
        'pattern': r'[Dd]ây\s*(?:điện|đồng)?\s*(\d+)[xX](\d+(?:\.\d+)?)\s*(?:mm2?)?',
        'template': 'Dây điện Cu - {cores}x{size}mm2',
    },
    # Pattern: Cáp ngầm trung thế
    'mv_cable': {
        'pattern': r'[Cc]áp\s*ngầm\s*(?:trung\s*thế)?\s*(\d+)[xX](\d+)',
        'template': 'Cáp ngầm trung thế - {cores}x{size}mm2',
    },
}

# Electrical panel patterns
PANEL_PATTERNS = {
    'distribution': {
        'keywords': ['tủ điện', 'tủ phân phối', 'tủ hạ thế'],
        'preserve_specs': True,  # Keep original specs
    },
    'meter': {
        'keywords': ['tủ gom', 'tủ công tơ', 'tủ đo đếm'],
        'preserve_specs': True,
    },
    'control': {
        'keywords': ['tủ điều khiển', 'tủ ats', 'tủ mts'],
        'preserve_specs': True,
    },
}

# Pipe patterns (HDPE, PVC, PPR, steel)
PIPE_PATTERNS = {
    'hdpe': {
        'pattern': r'(?:cung\s*cấp\s*)?(?:lắp\s*đặt\s*)?[Ốố]ng\s*HDPE\s*D?N?(\d+)\s*(PN\d+)?',
        'template': 'Ống HDPE - D{diameter}{pressure}',
    },
    'pvc': {
        'pattern': r'(?:cung\s*cấp\s*)?(?:lắp\s*đặt\s*)?[Ốố]ng\s*(?:u)?PVC\s*D?N?(\d+)\s*(PN\d+)?',
        'template': 'Ống PVC - D{diameter}{pressure}',
    },
    'ppr': {
        'pattern': r'(?:cung\s*cấp\s*)?(?:lắp\s*đặt\s*)?[Ốố]ng\s*PPR\s*D?N?(\d+)\s*(PN\d+)?',
        'template': 'Ống PPR - D{diameter}{pressure}',
    },
    'steel_galvanized': {
        'pattern': r'(?:cung\s*cấp\s*)?(?:lắp\s*đặt\s*)?[Ốố]ng\s*thép\s*mạ\s*kẽm\s*D?N?(\d+)',
        'template': 'Ống thép mạ kẽm - DN{diameter}',
    },
    'steel_black': {
        'pattern': r'(?:cung\s*cấp\s*)?(?:lắp\s*đặt\s*)?[Ốố]ng\s*thép\s*đen\s*D?N?(\d+)',
        'template': 'Ống thép đen - DN{diameter}',
    },
    'steel': {
        'pattern': r'(?:cung\s*cấp\s*)?(?:lắp\s*đặt\s*)?[Ốố]ng\s*thép\s*D?N?(\d+)',
        'template': 'Ống thép - DN{diameter}',
    },
    'ttk': {
        'pattern': r'[Ốố]ng\s*TTK\s*D?N?(\d+)',
        'template': 'Ống TTK - DN{diameter}',
    },
    'conduit': {
        'pattern': r'[Ốố]ng\s*(?:luồn\s*dây|gen)\s*D?(\d+)',
        'template': 'Ống luồn dây - D{diameter}',
    },
}

# Breaker patterns
BREAKER_PATTERNS = {
    'mccb': {
        'pattern': r'(MCCB)\s*[-]?\s*(\d+)[Pp]?\s*[-]?\s*(\d+)[Aa]?\s*[-]?\s*(\d+)?[kK]?[Aa]?',
        'template': 'MCCB - {poles}P - {amps}A{ka}',
    },
    'mcb': {
        'pattern': r'(MCB)\s*[-]?\s*(\d+)[Pp]?\s*[-]?\s*(\d+)[Aa]?\s*[-]?\s*(\d+)?[kK]?[Aa]?',
        'template': 'MCB - {poles}P - {amps}A{ka}',
    },
    'rccb': {
        'pattern': r'(RCCB|RCBO|ELCB)\s*[-]?\s*(\d+)[Pp]?\s*[-]?\s*(\d+)[Aa]?\s*[-]?\s*(\d+)?[kK]?[Aa]?',
        'template': '{type} - {poles}P - {amps}A{ka}',
    },
}

# Lighting patterns
LIGHTING_PATTERNS = {
    'street_light': {
        'pattern': r'[Đđ]èn\s*(?:chiếu\s*sáng|đường)\s*(?:LED)?\s*(\d+)[Ww]?',
        'template': 'Đèn chiếu sáng LED - {wattage}W',
    },
    'signal_light': {
        'pattern': r'[Đđ]èn\s*tín\s*hiệu\s*(?:báo\s*pha)?',
        'template': 'Đèn tín hiệu báo pha',
    },
    'led_panel': {
        'pattern': r'[Đđ]èn\s*(?:LED\s*)?(?:panel|âm\s*trần)\s*(\d+)[Ww]?',
        'template': 'Đèn LED panel - {wattage}W',
    },
}


class MEPEquipmentNormalizer:
    """Normalizer specialized for MEP equipment and materials"""

    def __init__(self):
        pass

    def is_mep_equipment(self, text: str) -> bool:
        """Check if description is MEP equipment related"""
        text_lower = text.lower()

        # Electrical keywords
        elec_keywords = [
            'tủ điện', 'tủ gom', 'tủ hạ thế', 'tủ công tơ', 'tủ phân phối',
            'mccb', 'mcb', 'rccb', 'rcbo', 'elcb', 'công tơ',
            'cáp điện', 'cáp cu', 'cáp đồng', 'dây điện', 'xlpe',
            'đèn chiếu sáng', 'đèn tín hiệu', 'đèn led', 'đèn đường',
            'cầu chì', 'thanh cái', 'aptomat',
            'ống luồn', 'ống gen',
        ]

        # Pipe keywords
        pipe_keywords = [
            'ống hdpe', 'ống pvc', 'ống ppr', 'ống thép',
            'ống ttk', 'ống nhựa', 'ống nước', 'ống thoát',
        ]

        # Cable pattern check
        cable_pattern = r'[Cc]áp.*?(\d+)[xX](\d+)'
        if re.search(cable_pattern, text):
            return True

        all_keywords = elec_keywords + pipe_keywords
        return any(kw in text_lower for kw in all_keywords)

    def is_material_only(self, text: str) -> bool:
        """Check if text is just material/equipment name without work verb"""
        text_lower = text.lower().strip()

        # Common work verbs
        work_verbs = [
            'lắp đặt', 'thi công', 'cung cấp', 'đào', 'đắp',
            'rải', 'kéo', 'luồn', 'đấu nối', 'thử',
        ]

        # If starts with a work verb, it's a work description
        for verb in work_verbs:
            if text_lower.startswith(verb):
                return False

        # If starts with equipment type, it's material only
        material_starters = [
            'ống', 'cáp', 'dây', 'tủ', 'mccb', 'mcb', 'công tơ',
            'đèn', 'van', 'máy', 'bơm', 'quạt',
        ]

        for starter in material_starters:
            if text_lower.startswith(starter):
                return True

        return False

    def normalize(self, description: str) -> MEPEquipmentResult:
        """
        Normalize MEP equipment description
        IMPROVED: Preserves important technical specs like Cu/XLPE/PVC
        """
        text_lower = description.lower().strip()
        is_material = self.is_material_only(description)

        # Try cable patterns first (highest priority for electrical)
        for cable_type, config in CABLE_PATTERNS.items():
            match = re.search(config['pattern'], description, re.IGNORECASE)
            if match:
                return self._normalize_cable(description, cable_type, match, config, is_material)

        # Try breaker patterns
        for breaker_type, config in BREAKER_PATTERNS.items():
            match = re.search(config['pattern'], description, re.IGNORECASE)
            if match:
                return self._normalize_breaker(description, breaker_type, match, config, is_material)

        # Try pipe patterns
        for pipe_type, config in PIPE_PATTERNS.items():
            match = re.search(config['pattern'], description, re.IGNORECASE)
            if match:
                return self._normalize_pipe(description, pipe_type, match, config, is_material)

        # Try lighting patterns
        for light_type, config in LIGHTING_PATTERNS.items():
            match = re.search(config['pattern'], description, re.IGNORECASE)
            if match:
                return self._normalize_lighting(description, light_type, match, config, is_material)

        # Try panel keywords
        for panel_type, config in PANEL_PATTERNS.items():
            for kw in config['keywords']:
                if kw in text_lower:
                    return self._normalize_panel(description, panel_type, config, is_material)

        # Fallback: preserve original, remove verb prefix if present (Standard Naming Strategy)
        normalized = description.strip()
        # Remove common verb prefixes
        verb_prefixes = ['cung cấp lắp đặt', 'lắp đặt', 'cung cấp', 'thi công']
        normalized_lower = normalized.lower()
        for prefix in verb_prefixes:
            if normalized_lower.startswith(prefix):
                normalized = normalized[len(prefix):].strip()
                break

        return MEPEquipmentResult(
            original=description,
            normalized=normalized,
            equipment_type='unknown',
            specs={},
            confidence=0.5,
            is_material_only=is_material
        )

    def _normalize_cable(
        self,
        description: str,
        cable_type: str,
        match: re.Match,
        config: dict,
        is_material: bool
    ) -> MEPEquipmentResult:
        """Normalize cable description - PRESERVES Cu/XLPE/PVC info"""
        specs = {}

        if cable_type == 'xlpe':
            # Groups: jacket(PVC/PE), cores, size
            jacket = match.group(1) or 'PVC'
            cores = match.group(2)
            size = match.group(3)
            specs = {'jacket': jacket, 'cores': cores, 'size': size}
            normalized = f"Cáp Cu/XLPE/{jacket} - {cores}x{size}mm2"

        elif cable_type == 'pvc_single':
            cores = match.group(2)
            size = match.group(3)
            specs = {'cores': cores, 'size': size}
            normalized = f"Cáp Cu/PVC - {cores}x{size}mm2"

        elif cable_type == 'wire':
            cores = match.group(1)
            size = match.group(2)
            specs = {'cores': cores, 'size': size}
            normalized = f"Dây điện Cu - {cores}x{size}mm2"

        elif cable_type == 'mv_cable':
            cores = match.group(1)
            size = match.group(2)
            specs = {'cores': cores, 'size': size}
            normalized = f"Cáp ngầm trung thế - {cores}x{size}mm2"

        else:
            normalized = description

        # Standard Naming Strategy: Don't add verb prefix, keep noun-first format
        return MEPEquipmentResult(
            original=description,
            normalized=normalized,
            equipment_type=f'cable_{cable_type}',
            specs=specs,
            confidence=0.9,
            is_material_only=is_material
        )

    def _normalize_breaker(
        self,
        description: str,
        breaker_type: str,
        match: re.Match,
        config: dict,
        is_material: bool
    ) -> MEPEquipmentResult:
        """Normalize circuit breaker description"""
        specs = {}

        if breaker_type == 'mccb':
            breaker = match.group(1)
            poles = match.group(2) or '3'
            amps = match.group(3)
            ka = match.group(4)
            specs = {'type': breaker, 'poles': poles, 'amps': amps, 'ka': ka}
            # Standard Naming Strategy: kA should be part of the 3rd component, not a 4th component
            ka_str = f" {ka}kA" if ka else ""
            # Standard Naming Strategy: MCCB - 3P - 400A 50kA (no verb prefix)
            normalized = f"MCCB - {poles}P - {amps}A{ka_str}"

        elif breaker_type == 'mcb':
            poles = match.group(2)
            amps = match.group(3)
            ka = match.group(4) if match.lastindex >= 4 else None
            specs = {'poles': poles, 'amps': amps, 'ka': ka}
            # Standard Naming Strategy: kA should be part of the 3rd component, not a 4th component
            ka_str = f" {ka}kA" if ka else ""
            normalized = f"MCB - {poles}P - {amps}A{ka_str}"

        elif breaker_type == 'rccb':
            breaker = match.group(1)
            poles = match.group(2)
            amps = match.group(3)
            ka = match.group(4) if match.lastindex >= 4 else None
            specs = {'type': breaker, 'poles': poles, 'amps': amps, 'ka': ka}
            # Standard Naming Strategy: kA should be part of the 3rd component, not a 4th component
            ka_str = f" {ka}kA" if ka else ""
            normalized = f"{breaker} - {poles}P - {amps}A{ka_str}"

        else:
            normalized = description

        return MEPEquipmentResult(
            original=description,
            normalized=normalized,
            equipment_type=f'breaker_{breaker_type}',
            specs=specs,
            confidence=0.9,
            is_material_only=is_material
        )

    def _normalize_pipe(
        self,
        description: str,
        pipe_type: str,
        match: re.Match,
        config: dict,
        is_material: bool
    ) -> MEPEquipmentResult:
        """Normalize pipe description"""
        specs = {}

        # Extract diameter
        diameter = match.group(1) if match.lastindex >= 1 else None
        if diameter:
            specs['diameter'] = diameter

        # Extract pressure (for HDPE, PVC, PPR)
        pressure = None
        if match.lastindex >= 2 and match.group(2):
            pressure = match.group(2).upper()
            specs['pressure'] = pressure

        # Build normalized string based on pipe type (Standard Naming Strategy: no verb prefix)
        # Map pipe_type to proper Vietnamese name
        pipe_name_map = {
            'hdpe': 'HDPE',
            'pvc': 'PVC',
            'ppr': 'PPR',
            'steel': 'thép',
            'steel_galvanized': 'thép mạ kẽm',
            'steel_black': 'thép đen',
            'ttk': 'TTK',
            'conduit': 'luồn dây',
        }

        pipe_material = pipe_name_map.get(pipe_type, pipe_type.upper())

        if pipe_type in ['steel', 'steel_galvanized', 'steel_black']:
            normalized = f"Ống {pipe_material} - DN{diameter}"
        elif pipe_type == 'conduit':
            normalized = f"Ống luồn dây - D{diameter}"
        else:
            parts = [f"Ống {pipe_material}", f"D{diameter}"]
            if pressure:
                parts.append(pressure)
            normalized = ' - '.join(parts)

        return MEPEquipmentResult(
            original=description,
            normalized=normalized,
            equipment_type=f'pipe_{pipe_type}',
            specs=specs,
            confidence=0.9,
            is_material_only=is_material
        )

    def _normalize_lighting(
        self,
        description: str,
        light_type: str,
        match: re.Match,
        config: dict,
        is_material: bool
    ) -> MEPEquipmentResult:
        """Normalize lighting equipment description (Standard Naming Strategy: no verb prefix)"""
        specs = {}

        if light_type == 'signal_light':
            normalized = "Đèn tín hiệu báo pha"
        else:
            wattage = match.group(1) if match.lastindex >= 1 else None
            if wattage:
                specs['wattage'] = wattage

            if light_type == 'street_light':
                normalized = f"Đèn chiếu sáng LED - {wattage}W" if wattage else "Đèn chiếu sáng LED"
            elif light_type == 'led_panel':
                normalized = f"Đèn LED panel - {wattage}W" if wattage else "Đèn LED panel"
            else:
                normalized = description

        return MEPEquipmentResult(
            original=description,
            normalized=normalized,
            equipment_type=f'lighting_{light_type}',
            specs=specs,
            confidence=0.85,
            is_material_only=is_material
        )

    def _normalize_panel(
        self,
        description: str,
        panel_type: str,
        config: dict,
        is_material: bool
    ) -> MEPEquipmentResult:
        """Normalize electrical panel - PRESERVES original specs (Standard Naming Strategy: no verb prefix)"""
        specs = {}

        # For panels, preserve the original description but clean it up
        desc_clean = description.strip()

        # Remove common verb prefixes if present
        verb_prefixes = ['cung cấp lắp đặt', 'lắp đặt', 'cung cấp', 'thi công']
        desc_lower = desc_clean.lower()
        for prefix in verb_prefixes:
            if desc_lower.startswith(prefix):
                desc_clean = desc_clean[len(prefix):].strip()
                break

        # Extract key specs if present
        voltage_match = re.search(r'(\d+)\s*[Vv]', description)
        if voltage_match:
            specs['voltage'] = voltage_match.group(1)

        phase_match = re.search(r'(\d+)\s*pha', description, re.IGNORECASE)
        if phase_match:
            specs['phase'] = phase_match.group(1)

        # Standard Naming Strategy: Don't add verb prefix
        normalized = desc_clean

        return MEPEquipmentResult(
            original=description,
            normalized=normalized,
            equipment_type=f'panel_{panel_type}',
            specs=specs,
            confidence=0.8,
            is_material_only=is_material
        )


# Singleton instance
_mep_normalizer = None


def get_mep_normalizer() -> MEPEquipmentNormalizer:
    """Get or create MEP equipment normalizer singleton"""
    global _mep_normalizer
    if _mep_normalizer is None:
        _mep_normalizer = MEPEquipmentNormalizer()
    return _mep_normalizer


def normalize_mep_equipment(description: str) -> MEPEquipmentResult:
    """Convenience function for normalizing MEP equipment"""
    normalizer = get_mep_normalizer()
    return normalizer.normalize(description)
