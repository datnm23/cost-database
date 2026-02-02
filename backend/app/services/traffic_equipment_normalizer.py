"""
Traffic Equipment Normalizer Service
Handles normalization of traffic and road infrastructure equipment:
- Biển báo (traffic signs)
- Cột đèn (lamp posts)
- Bản quan trắc (monitoring plates)
- Lan can, hộ lan (guardrails)
- Cọc tiêu, cọc km (marker posts)
- Vạch sơn (road markings)
"""
import re
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TrafficEquipmentResult:
    """Result of traffic equipment normalization"""
    original: str
    normalized: str
    equipment_type: str
    specs: Dict[str, str]
    confidence: float


# Traffic sign patterns and templates
TRAFFIC_SIGNS = {
    'types': {
        'tam giác': ('Biển cảnh báo', 'A'),
        'tròn': ('Biển cấm', 'B'),
        'chữ nhật': ('Biển chỉ dẫn', 'C'),
        'bát giác': ('Biển dừng', 'STOP'),
        'vuông': ('Biển phụ', 'S'),
    },
    'size_pattern': r'([ABCRW]?)(\d+)(?:\s*x\s*\d+)?(?:cm|mm)?',
    'template': 'Biển báo {type} - {size}'
}

# Monitoring equipment patterns
MONITORING_EQUIPMENT = {
    'types': {
        'lún': 'quan trắc lún',
        'nghiêng': 'quan trắc nghiêng',
        'chuyển vị': 'quan trắc chuyển vị',
        'vỡ': 'quan trắc vỡ',
        'nứt': 'quan trắc nứt',
    },
    'template': 'Lắp đặt bản quan trắc {type}'
}

# Lamp post patterns
LAMP_POST = {
    'height_pattern': r'[Hh]=?\s*(\d+(?:\.\d+)?)\s*m?',
    'material_keywords': ['thép', 'mạ kẽm', 'composite', 'nhôm'],
    'template': 'Lắp đặt cột đèn {material} - H={height}m'
}

# Road marking patterns
ROAD_MARKINGS = {
    'types': {
        'vạch liền': 'vạch liền',
        'vạch đứt': 'vạch đứt đoạn',
        'vạch ngang': 'vạch ngang đường',
        'vạch dọc': 'vạch dọc đường',
        'vạch mũi tên': 'vạch mũi tên',
        'vạch chữ': 'vạch chữ',
        'vạch zebrafish': 'vạch sang đường',
        'vạch sang đường': 'vạch sang đường',
    },
    'color_keywords': ['trắng', 'vàng', 'đỏ'],
    'template': 'Sơn vạch {type} - {color}'
}

# Guardrail patterns
GUARDRAILS = {
    'types': {
        'tôn sóng': 'hộ lan tôn sóng',
        'lan can': 'lan can',
        'hộ lan': 'hộ lan',
        'barrier': 'barrier bê tông',
        'dải phân cách': 'dải phân cách',
    },
    'material_keywords': ['thép', 'bê tông', 'mạ kẽm', 'composite'],
    'template': 'Lắp đặt {type} - {material}'
}

# Marker posts
MARKER_POSTS = {
    'types': {
        'cọc tiêu': 'cọc tiêu',
        'cọc km': 'cọc km',
        'cọc h': 'cọc H',
        'cọc mốc': 'cọc mốc',
    },
    'template': 'Lắp đặt {type}'
}


class TrafficEquipmentNormalizer:
    """Normalizer specialized for traffic and road infrastructure equipment"""

    def __init__(self):
        pass

    def is_traffic_equipment(self, text: str) -> bool:
        """Check if description is traffic equipment related"""
        text_lower = text.lower()
        indicators = [
            'biển báo', 'biển cảnh báo', 'biển cấm', 'biển chỉ dẫn',
            'bản quan trắc', 'quan trắc lún', 'quan trắc',
            'cột đèn', 'đèn chiếu sáng', 'đèn đường',
            'vạch sơn', 'sơn vạch', 'vạch kẻ', 'kẻ vạch',
            'lan can', 'hộ lan', 'tôn sóng', 'barrier',
            'cọc tiêu', 'cọc km', 'cọc h',
        ]
        return any(ind in text_lower for ind in indicators)

    def normalize(self, description: str) -> TrafficEquipmentResult:
        """
        Normalize traffic equipment description

        Args:
            description: Original description

        Returns:
            TrafficEquipmentResult with normalized description and metadata
        """
        text_lower = description.lower()

        # Try each equipment type normalizer
        if 'biển báo' in text_lower or 'biển' in text_lower:
            return self._normalize_traffic_sign(description)
        elif 'bản quan trắc' in text_lower or 'quan trắc' in text_lower:
            return self._normalize_monitoring(description)
        elif 'cột đèn' in text_lower or 'đèn chiếu sáng' in text_lower:
            return self._normalize_lamp_post(description)
        elif any(kw in text_lower for kw in ['vạch sơn', 'sơn vạch', 'vạch kẻ', 'kẻ vạch']):
            return self._normalize_road_marking(description)
        elif any(kw in text_lower for kw in ['lan can', 'hộ lan', 'tôn sóng', 'barrier']):
            return self._normalize_guardrail(description)
        elif any(kw in text_lower for kw in ['cọc tiêu', 'cọc km', 'cọc h', 'cọc mốc']):
            return self._normalize_marker_post(description)

        # Fallback: return cleaned original
        return TrafficEquipmentResult(
            original=description,
            normalized=description,
            equipment_type='unknown',
            specs={},
            confidence=0.3
        )

    def _normalize_traffic_sign(self, description: str) -> TrafficEquipmentResult:
        """Normalize traffic sign description"""
        text_lower = description.lower()
        specs = {}

        # Detect sign type
        sign_type = None
        sign_series = None
        for type_key, (type_name, series) in TRAFFIC_SIGNS['types'].items():
            if type_key in text_lower:
                sign_type = type_name
                sign_series = series
                specs['sign_type'] = type_key
                break

        # If no type found, try to detect from series letter
        if not sign_type:
            series_match = re.search(r'\b([ABCRWS])(\d+)', description, re.IGNORECASE)
            if series_match:
                sign_series = series_match.group(1).upper()
                series_map = {
                    'A': 'Biển cảnh báo',
                    'B': 'Biển cấm',
                    'C': 'Biển chỉ dẫn',
                    'R': 'Biển báo',
                    'W': 'Biển cảnh báo',
                    'S': 'Biển phụ',
                }
                sign_type = series_map.get(sign_series, 'Biển báo')

        # Extract size
        size_match = re.search(r'(\d+)\s*(?:x\s*\d+)?\s*(?:cm|mm)?', text_lower)
        size = None
        if size_match:
            size = size_match.group(1)
            specs['size'] = f"{size}cm"

        # Build normalized description
        if sign_type and size:
            if sign_series:
                normalized = f"Biển báo {specs.get('sign_type', '')} - {sign_series}{size}"
            else:
                normalized = f"Biển báo {specs.get('sign_type', '')} - {size}cm"
            confidence = 0.95
        elif sign_type:
            normalized = f"Biển báo {specs.get('sign_type', '')}"
            confidence = 0.8
        elif size:
            normalized = f"Biển báo - {size}cm"
            confidence = 0.6
        else:
            normalized = "Biển báo"
            confidence = 0.4

        return TrafficEquipmentResult(
            original=description,
            normalized=normalized.strip(),
            equipment_type='traffic_sign',
            specs=specs,
            confidence=confidence
        )

    def _normalize_monitoring(self, description: str) -> TrafficEquipmentResult:
        """Normalize monitoring equipment description"""
        text_lower = description.lower()
        specs = {}

        # Detect monitoring type
        monitor_type = None
        for type_key, type_name in MONITORING_EQUIPMENT['types'].items():
            if type_key in text_lower:
                monitor_type = type_name
                specs['monitor_type'] = type_key
                break

        # Build normalized description
        if monitor_type:
            normalized = f"Lắp đặt bản {monitor_type}"
            confidence = 0.95
        else:
            normalized = "Lắp đặt bản quan trắc"
            confidence = 0.7

        return TrafficEquipmentResult(
            original=description,
            normalized=normalized,
            equipment_type='monitoring',
            specs=specs,
            confidence=confidence
        )

    def _normalize_lamp_post(self, description: str) -> TrafficEquipmentResult:
        """Normalize lamp post description"""
        text_lower = description.lower()
        specs = {}

        # Extract height
        height_match = re.search(LAMP_POST['height_pattern'], text_lower)
        height = None
        if height_match:
            height = height_match.group(1)
            specs['height'] = f"{height}m"

        # Detect material
        material = None
        for mat in LAMP_POST['material_keywords']:
            if mat in text_lower:
                material = mat
                specs['material'] = mat
                break

        # Build normalized description
        parts = ['Lắp đặt cột đèn']
        if material:
            parts.append(material)
        if height:
            parts.append(f"- H={height}m")

        normalized = ' '.join(parts)
        confidence = 0.9 if height or material else 0.6

        return TrafficEquipmentResult(
            original=description,
            normalized=normalized,
            equipment_type='lamp_post',
            specs=specs,
            confidence=confidence
        )

    def _normalize_road_marking(self, description: str) -> TrafficEquipmentResult:
        """Normalize road marking description"""
        text_lower = description.lower()
        specs = {}

        # Detect marking type
        marking_type = None
        for type_key, type_name in ROAD_MARKINGS['types'].items():
            if type_key in text_lower:
                marking_type = type_name
                specs['marking_type'] = type_key
                break

        # Detect color
        color = None
        for c in ROAD_MARKINGS['color_keywords']:
            if c in text_lower:
                color = c
                specs['color'] = c
                break

        # Build normalized description
        parts = ['Sơn vạch']
        if marking_type:
            parts.append(marking_type)
        if color:
            parts.append(f"- {color}")

        normalized = ' '.join(parts)
        confidence = 0.9 if marking_type else 0.6

        return TrafficEquipmentResult(
            original=description,
            normalized=normalized,
            equipment_type='road_marking',
            specs=specs,
            confidence=confidence
        )

    def _normalize_guardrail(self, description: str) -> TrafficEquipmentResult:
        """Normalize guardrail description"""
        text_lower = description.lower()
        specs = {}

        # Detect guardrail type
        rail_type = None
        for type_key, type_name in GUARDRAILS['types'].items():
            if type_key in text_lower:
                rail_type = type_name
                specs['rail_type'] = type_key
                break

        # Detect material
        material = None
        for mat in GUARDRAILS['material_keywords']:
            if mat in text_lower:
                material = mat
                specs['material'] = mat
                break

        # Build normalized description
        parts = ['Lắp đặt']
        if rail_type:
            parts.append(rail_type)
        else:
            parts.append('lan can')
        if material:
            parts.append(f"- {material}")

        normalized = ' '.join(parts)
        confidence = 0.9 if rail_type else 0.6

        return TrafficEquipmentResult(
            original=description,
            normalized=normalized,
            equipment_type='guardrail',
            specs=specs,
            confidence=confidence
        )

    def _normalize_marker_post(self, description: str) -> TrafficEquipmentResult:
        """Normalize marker post description"""
        text_lower = description.lower()
        specs = {}

        # Detect post type
        post_type = None
        for type_key, type_name in MARKER_POSTS['types'].items():
            if type_key in text_lower:
                post_type = type_name
                specs['post_type'] = type_key
                break

        # Build normalized description
        if post_type:
            normalized = f"Lắp đặt {post_type}"
            confidence = 0.95
        else:
            normalized = "Lắp đặt cọc tiêu"
            confidence = 0.6

        return TrafficEquipmentResult(
            original=description,
            normalized=normalized,
            equipment_type='marker_post',
            specs=specs,
            confidence=confidence
        )


# Singleton instance
_traffic_normalizer = None


def get_traffic_normalizer() -> TrafficEquipmentNormalizer:
    """Get or create traffic equipment normalizer singleton"""
    global _traffic_normalizer
    if _traffic_normalizer is None:
        _traffic_normalizer = TrafficEquipmentNormalizer()
    return _traffic_normalizer


def normalize_traffic_equipment(description: str) -> TrafficEquipmentResult:
    """Convenience function for normalizing traffic equipment"""
    normalizer = get_traffic_normalizer()
    return normalizer.normalize(description)
