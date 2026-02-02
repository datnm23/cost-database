"""
MEP Equipment Normalizer Service
Handles normalization of MEP (Mechanical, Electrical, Plumbing) equipment:
- Electrical panels (tủ điện)
- Circuit breakers (MCCB, MCB)
- Pipes (ống HDPE, PVC, PPR)
- Cables (cáp điện)
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


# Electrical equipment patterns
ELECTRICAL_EQUIPMENT = {
    'panel': {
        'keywords': ['tủ điện', 'tủ gom', 'tủ hạ thế', 'tủ công tơ'],
        'template': 'Cung cấp lắp đặt {type}',
    },
    'breaker': {
        'patterns': [
            r'(MCCB|MCB|RCCB|RCBO|ELCB)-?(\d+P)?-?(\d+A)?',
            r'(MCCB|MCB)-(\d+)P-(\d+)A-(\d+)kA',
        ],
        'template': 'Cung cấp lắp đặt {type}',
    },
    'meter': {
        'keywords': ['công tơ', 'đồng hồ điện'],
        'patterns': [r'công tơ\s*(\d+P)?'],
        'template': 'Cung cấp lắp đặt {type}',
    },
    'cable': {
        'keywords': ['cáp điện', 'cáp ngầm', 'dây điện'],
        'patterns': [r'cáp\s*(CU|Cu|AL|Al)?.*?(\d+x\d+)'],
        'template': 'Lắp đặt {type}',
    },
    'lighting': {
        'keywords': ['đèn chiếu sáng', 'đèn đường', 'đèn led', 'đèn tín hiệu'],
        'template': 'Lắp đặt {type}',
    },
}

# Pipe patterns (HDPE, PVC, PPR, steel)
PIPE_PATTERNS = {
    'hdpe': {
        'pattern': r'ống\s*HDPE\s*D?(\d+)\s*(PN\d+)?',
        'template': 'Lắp đặt ống HDPE - D{diameter} - {pressure}',
    },
    'pvc': {
        'pattern': r'ống\s*(?:u)?PVC\s*D?(\d+)\s*(PN\d+)?',
        'template': 'Lắp đặt ống PVC - D{diameter} - {pressure}',
    },
    'ppr': {
        'pattern': r'ống\s*PPR\s*D?(\d+)\s*(PN\d+)?',
        'template': 'Lắp đặt ống PPR - D{diameter} - {pressure}',
    },
    'steel': {
        'pattern': r'ống\s*thép\s*(?:đen|mạ)?\s*DN?(\d+)',
        'template': 'Lắp đặt ống thép - DN{diameter}',
    },
    'ttk': {
        'pattern': r'ống\s*TTK\s*DN?(\d+)',
        'template': 'Lắp đặt ống TTK - DN{diameter}',
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
            'tủ điện', 'tủ gom', 'mccb', 'mcb', 'rccb', 'công tơ',
            'cáp điện', 'dây điện', 'đèn chiếu sáng', 'đèn tín hiệu',
            'cầu chì', 'thanh cái', 'aptomat',
        ]

        # Pipe keywords
        pipe_keywords = [
            'ống hdpe', 'ống pvc', 'ống ppr', 'ống thép',
            'ống ttk', 'ống nhựa', 'ống nước',
        ]

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

        Args:
            description: Original description

        Returns:
            MEPEquipmentResult with normalized description and metadata
        """
        text_lower = description.lower().strip()
        is_material = self.is_material_only(description)

        # Try pipe patterns first
        for pipe_type, config in PIPE_PATTERNS.items():
            match = re.search(config['pattern'], description, re.IGNORECASE)
            if match:
                return self._normalize_pipe(description, pipe_type, match, config, is_material)

        # Try electrical equipment
        for equip_type, config in ELECTRICAL_EQUIPMENT.items():
            if 'keywords' in config:
                for kw in config['keywords']:
                    if kw in text_lower:
                        return self._normalize_electrical(description, equip_type, config, is_material)
            if 'patterns' in config:
                for pattern in config['patterns']:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        return self._normalize_electrical_pattern(description, equip_type, match, config, is_material)

        # Fallback
        normalized = description
        if is_material and not any(description.lower().startswith(v) for v in ['lắp đặt', 'cung cấp', 'thi công']):
            normalized = f"Cung cấp lắp đặt {description}"

        return MEPEquipmentResult(
            original=description,
            normalized=normalized,
            equipment_type='unknown',
            specs={},
            confidence=0.5,
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

        # Extract pressure
        pressure = None
        if match.lastindex >= 2 and match.group(2):
            pressure = match.group(2).upper()
            specs['pressure'] = pressure

        # Build normalized string
        parts = [f"Lắp đặt ống {pipe_type.upper()}"]
        if diameter:
            parts.append(f"D{diameter}")
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

    def _normalize_electrical(
        self,
        description: str,
        equip_type: str,
        config: dict,
        is_material: bool
    ) -> MEPEquipmentResult:
        """Normalize electrical equipment by keyword"""
        specs = {}

        # Clean up description
        desc_clean = description.strip()

        # Add verb if material only
        if is_material:
            normalized = f"Cung cấp lắp đặt {desc_clean}"
        else:
            normalized = desc_clean

        return MEPEquipmentResult(
            original=description,
            normalized=normalized,
            equipment_type=equip_type,
            specs=specs,
            confidence=0.8,
            is_material_only=is_material
        )

    def _normalize_electrical_pattern(
        self,
        description: str,
        equip_type: str,
        match: re.Match,
        config: dict,
        is_material: bool
    ) -> MEPEquipmentResult:
        """Normalize electrical equipment by pattern match"""
        specs = {}

        # Extract specs from pattern
        matched_text = match.group(0)
        specs['model'] = matched_text

        # Build normalized string
        if is_material:
            normalized = f"Cung cấp lắp đặt {matched_text}"
        else:
            normalized = description

        return MEPEquipmentResult(
            original=description,
            normalized=normalized,
            equipment_type=equip_type,
            specs=specs,
            confidence=0.85,
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
