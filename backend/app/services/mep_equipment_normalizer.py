"""
MEP Equipment Normalizer Service
Handles normalization of MEP (Mechanical, Electrical, Plumbing) equipment:
- Electrical panels (tủ điện)
- Circuit breakers (MCCB, MCB)
- Pipes (ống HDPE, PVC, PPR)
- Cables (cáp điện Cu/XLPE/PVC)
- Lighting (đèn)
- Valves (van cổng, van bướm, van bi)
- Pipe fittings (côn thu, cút, tê, bích, khớp nối)
- Electrical accessories (contactor, aptomat)
- Instruments (đồng hồ)
- Pumps (bơm)
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


# Valve patterns
VALVE_PATTERNS = {
    'gate': {
        'pattern': r'[Vv]an\s*cổng\s*D?N?([\d]+)',
        'template': 'Van cổng - DN{diameter}',
    },
    'butterfly': {
        'pattern': r'[Vv]an\s*bướm\s*D?N?([\d]+)',
        'template': 'Van bướm - DN{diameter}',
    },
    'ball': {
        'pattern': r'[Vv]an\s*bi\s*D?N?([\d]+)',
        'template': 'Van bi - DN{diameter}',
    },
    'check': {
        'pattern': r'[Vv]an\s*(?:một\s*chiều|1\s*chiều)\s*D?N?([\d]+)',
        'template': 'Van một chiều - DN{diameter}',
    },
    'generic': {
        'pattern': r'[Vv]an\s+(?!(?:khuôn|ván))([\w]+)\s*D?N?([\d]+)',
        'template': 'Van {subtype} - DN{diameter}',
    },
}

# Pipe fitting patterns
FITTING_PATTERNS = {
    'reducer': {
        'pattern': r'[Cc]ôn\s*thu\s*(?:(uPVC|PVC|HDPE|PPR|thép)\s*)?D?N?([\d]+)\s*[/xX]\s*D?N?([\d]+)',
        'template': 'Côn thu - {material} - D{d1}/D{d2}',
    },
    'elbow': {
        'pattern': r'[Cc]út\s*(?:(thép|uPVC|PVC|HDPE|PPR)\s*)?(?:mạ\s*kẽm\s*)?D?N?([\d]+)',
        'template': 'Cút - {material} - DN{diameter}',
    },
    'tee': {
        'pattern': r'[Tt]ê\s*(?:(thép|uPVC|PVC|HDPE|PPR)\s*)?(?:mạ\s*kẽm\s*)?D?N?([\d]+)',
        'template': 'Tê - {material} - DN{diameter}',
    },
    'flange': {
        'pattern': r'[Bb]ích\s*(?:(thép|uPVC|PVC|HDPE|PPR)\s*)?(?:mạ\s*kẽm\s*)?D?N?([\d]+)',
        'template': 'Bích - {material} - DN{diameter}',
    },
    'flexible_joint': {
        'pattern': r'[Kk]hớp\s*nối\s*(?:mềm\s*)?(?:(thép|uPVC|PVC|HDPE|PPR|inox)\s*)?D?N?([\d]+)',
        'template': 'Khớp nối mềm - {material} - DN{diameter}',
    },
    'coupling': {
        'pattern': r'(?:măng\s*sông|nối\s*ống)\s*(?:(thép|uPVC|PVC|HDPE|PPR)\s*)?D?N?([\d]+)',
        'template': 'Măng sông - {material} - DN{diameter}',
    },
}

# Electrical accessory patterns
ELECTRICAL_ACCESSORY_PATTERNS = {
    'contactor': {
        'pattern': r'[Cc]ontactor\s*(\d+)\s*[Pp]?\s*[-]?\s*(\d+)\s*[Aa]?',
        'template': 'Contactor - {poles}P - {amps}A',
    },
    'contactor_simple': {
        'pattern': r'[Cc]ontactor\s*(\d+)\s*[Aa]',
        'template': 'Contactor - {amps}A',
    },
    'aptomat_full': {
        'pattern': r'[Aa]ptomat\s*(\d+)\s*[Pp]\s*[-]?\s*(\d+)\s*[Aa]',
        'template': 'Aptomat - {poles}P - {amps}A',
    },
    'aptomat_simple': {
        'pattern': r'[Aa]ptomat\s*(\d+)\s*[Aa]',
        'template': 'Aptomat - {amps}A',
    },
    'fuse': {
        'pattern': r'[Cc]ầu\s*chì\s*(\d+)\s*[Aa]',
        'template': 'Cầu chì - {amps}A',
    },
    'busbar': {
        'pattern': r'[Tt]hanh\s*cái\s*(?:đồng\s*)?(\d+)\s*[Aa]?',
        'template': 'Thanh cái đồng - {amps}A',
    },
    'indicator_light': {
        'pattern': r'[Đđ]èn\s*báo\s*(?:pha\s*)?(?:(\w+)\s*)?',
        'template': 'Đèn báo pha',
    },
    'timer': {
        'pattern': r'[Tt]imer\s*(?:hẹn\s*giờ\s*)?(\d+)\s*[Aa]?',
        'template': 'Timer hẹn giờ - {amps}A',
    },
    'relay': {
        'pattern': r'[Rr](?:ơ\s*le|elay)\s*(?:trung\s*gian\s*)?(\d+)\s*[Aa]?',
        'template': 'Rơ le trung gian - {amps}A',
    },
}

# Instrument patterns
INSTRUMENT_PATTERNS = {
    'water_meter': {
        'pattern': r'[Đđ]ồng\s*hồ\s*(?:nước|đo\s*nước)\s*D?N?([\d]+)',
        'template': 'Đồng hồ nước - DN{diameter}',
    },
    'pressure_gauge': {
        'pattern': r'[Đđ]ồng\s*hồ\s*(?:đo\s*)?áp\s*(?:suất\s*)?(?:(\d+)\s*bar)?',
        'template': 'Đồng hồ đo áp suất',
    },
    'flow_meter': {
        'pattern': r'[Đđ]ồng\s*hồ\s*(?:đo\s*)?lưu\s*lượng\s*D?N?([\d]+)?',
        'template': 'Đồng hồ lưu lượng - DN{diameter}',
    },
    'thermometer': {
        'pattern': r'[Nn]hiệt\s*kế\s*(?:(\d+)\s*°?[Cc])?',
        'template': 'Nhiệt kế',
    },
}

# Pump patterns
PUMP_PATTERNS = {
    'submersible': {
        'pattern': r'[Bb]ơm\s*chìm\s*(?:(\d+(?:\.\d+)?)\s*(?:HP|kW|KW))?',
        'template': 'Bơm chìm - {power}',
    },
    'centrifugal': {
        'pattern': r'[Bb]ơm\s*ly\s*tâm\s*(?:(\d+(?:\.\d+)?)\s*(?:HP|kW|KW))?',
        'template': 'Bơm ly tâm - {power}',
    },
    'booster': {
        'pattern': r'[Bb]ơm\s*(?:tăng\s*áp|bù\s*áp)\s*(?:(\d+(?:\.\d+)?)\s*(?:HP|kW|KW))?',
        'template': 'Bơm tăng áp - {power}',
    },
    'fire': {
        'pattern': r'[Bb]ơm\s*(?:chữa\s*cháy|pccc|PCCC)\s*(?:(\d+(?:\.\d+)?)\s*(?:HP|kW|KW))?',
        'template': 'Bơm chữa cháy - {power}',
    },
    'generic': {
        'pattern': r'[Bb]ơm\s+(?!chìm|ly|tăng|bù|chữa|pccc)([\w]+)\s*(?:(\d+(?:\.\d+)?)\s*(?:HP|kW|KW))?',
        'template': 'Bơm {subtype} - {power}',
    },
}

# HVAC patterns
HVAC_PATTERNS = {
    'ahu': {
        'pattern': r'(?:AHU|[Aa]ir\s*[Hh]andling)\s*(?:(\d+(?:\.\d+)?)\s*(?:HP|kW|TR|ton))?',
        'template': 'AHU - {capacity}',
    },
    'fcu': {
        'pattern': r'(?:FCU|[Ff]an\s*[Cc]oil)\s*(?:(\d+(?:\.\d+)?)\s*(?:HP|kW|TR|BTU))?',
        'template': 'FCU - {capacity}',
    },
    'ac': {
        'pattern': r'[Đđ]iều\s*hòa\s*(?:không\s*khí\s*)?(?:(\d+(?:\.\d+)?)\s*(?:HP|kW|BTU))?',
        'template': 'Điều hòa - {capacity}',
    },
    'indoor_unit': {
        'pattern': r'[Dd]àn\s*lạnh\s*(?:(\d+(?:\.\d+)?)\s*(?:HP|kW|BTU))?',
        'template': 'Dàn lạnh - {capacity}',
    },
    'outdoor_unit': {
        'pattern': r'[Dd]àn\s*nóng\s*(?:(\d+(?:\.\d+)?)\s*(?:HP|kW|BTU))?',
        'template': 'Dàn nóng - {capacity}',
    },
    'duct': {
        'pattern': r'[Ốố]ng\s*gió\s*(?:tôn\s*)?(?:(\d+)\s*[xX]\s*(\d+))?',
        'template': 'Ống gió - {dims}',
    },
    'fan': {
        'pattern': r'[Qq]uạt\s*(?:thông\s*gió|hút|thổi)\s*(?:(\d+(?:\.\d+)?)\s*(?:m3/h|CFM|W))?',
        'template': 'Quạt thông gió - {capacity}',
    },
}

# Fire protection patterns
FIRE_PATTERNS = {
    'sprinkler': {
        'pattern': r'[Ss]prinkler\s*(?:D?N?([\d]+))?',
        'template': 'Sprinkler - DN{diameter}',
    },
    'fire_alarm': {
        'pattern': r'(?:[Đđ]ầu\s*)?[Bb]áo\s*cháy\s*(?:khói|nhiệt)?',
        'template': 'Đầu báo cháy',
    },
    'fire_extinguisher': {
        'pattern': r'[Bb]ình\s*chữa\s*cháy\s*(?:(\d+)\s*(?:kg|l))?',
        'template': 'Bình chữa cháy - {capacity}',
    },
    'fire_hose': {
        'pattern': r'(?:[Cc]uộn\s*)?[Vv]òi\s*(?:chữa\s*cháy|cứu\s*hỏa)\s*D?N?([\d]+)?',
        'template': 'Vòi chữa cháy - DN{diameter}',
    },
    'fire_cabinet': {
        'pattern': r'[Tt]ủ\s*(?:chữa\s*cháy|cứu\s*hỏa|pccc|PCCC)',
        'template': 'Tủ chữa cháy',
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
            'cầu chì', 'thanh cái', 'aptomat', 'contactor', 'đèn báo',
            'rơ le', 'relay', 'timer',
            'ống luồn', 'ống gen',
        ]

        # Pipe keywords
        pipe_keywords = [
            'ống hdpe', 'ống pvc', 'ống ppr', 'ống thép',
            'ống ttk', 'ống nhựa', 'ống nước', 'ống thoát',
        ]

        # Valve keywords (careful: "van" must not match "ván khuôn")
        valve_keywords = [
            'van cổng', 'van bướm', 'van bi', 'van một chiều',
            'van 1 chiều', 'van giảm áp', 'van xả', 'van điều khiển',
        ]

        # Pipe fitting keywords
        fitting_keywords = [
            'côn thu', 'cút thép', 'cút pvc', 'cút hdpe', 'cút upvc',
            'tê thép', 'tê pvc', 'tê hdpe',
            'bích thép', 'bích pvc', 'bích hdpe',
            'khớp nối', 'măng sông', 'nối ống',
        ]

        # Instrument keywords
        instrument_keywords = [
            'đồng hồ nước', 'đồng hồ áp', 'đồng hồ đo', 'đồng hồ lưu lượng',
            'nhiệt kế', 'áp kế',
        ]

        # Pump keywords
        pump_keywords = [
            'bơm chìm', 'bơm ly tâm', 'bơm tăng áp', 'bơm bù áp',
            'bơm chữa cháy', 'bơm pccc', 'bơm nước',
        ]

        # HVAC keywords
        hvac_keywords = [
            'điều hòa', 'ahu', 'fcu', 'dàn lạnh', 'dàn nóng',
            'ống gió', 'quạt thông gió', 'quạt hút',
        ]

        # Fire protection keywords
        fire_keywords = [
            'sprinkler', 'báo cháy', 'bình chữa cháy', 'vòi chữa cháy',
            'tủ chữa cháy', 'tủ pccc', 'đầu báo',
        ]

        # Cable pattern check
        cable_pattern = r'[Cc]áp.*?(\d+)[xX](\d+)'
        if re.search(cable_pattern, text):
            return True

        all_keywords = (
            elec_keywords + pipe_keywords + valve_keywords +
            fitting_keywords + instrument_keywords + pump_keywords +
            hvac_keywords + fire_keywords
        )
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
        Standard Naming Strategy: [TÊN ĐỐI TƯỢNG] - [CHẤT LIỆU/BIẾN THỂ] - [THÔNG SỐ KỸ THUẬT]
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

        # Try electrical accessory patterns (contactor, aptomat, etc.)
        for acc_type, config in ELECTRICAL_ACCESSORY_PATTERNS.items():
            match = re.search(config['pattern'], description, re.IGNORECASE)
            if match:
                return self._normalize_electrical_accessory(description, acc_type, match, config, is_material)

        # Try valve patterns (before pipe patterns - "van" check is more specific)
        for valve_type, config in VALVE_PATTERNS.items():
            match = re.search(config['pattern'], description, re.IGNORECASE)
            if match:
                return self._normalize_valve(description, valve_type, match, config, is_material)

        # Try pipe fitting patterns (before pipe patterns - "côn thu", "cút" are more specific)
        for fitting_type, config in FITTING_PATTERNS.items():
            match = re.search(config['pattern'], description, re.IGNORECASE)
            if match:
                return self._normalize_fitting(description, fitting_type, match, config, is_material)

        # Try pipe patterns
        for pipe_type, config in PIPE_PATTERNS.items():
            match = re.search(config['pattern'], description, re.IGNORECASE)
            if match:
                return self._normalize_pipe(description, pipe_type, match, config, is_material)

        # Try HVAC patterns
        for hvac_type, config in HVAC_PATTERNS.items():
            match = re.search(config['pattern'], description, re.IGNORECASE)
            if match:
                return self._normalize_hvac(description, hvac_type, match, config, is_material)

        # Try pump patterns
        for pump_type, config in PUMP_PATTERNS.items():
            match = re.search(config['pattern'], description, re.IGNORECASE)
            if match:
                return self._normalize_pump(description, pump_type, match, config, is_material)

        # Try instrument patterns
        for inst_type, config in INSTRUMENT_PATTERNS.items():
            match = re.search(config['pattern'], description, re.IGNORECASE)
            if match:
                return self._normalize_instrument(description, inst_type, match, config, is_material)

        # Try lighting patterns
        for light_type, config in LIGHTING_PATTERNS.items():
            match = re.search(config['pattern'], description, re.IGNORECASE)
            if match:
                return self._normalize_lighting(description, light_type, match, config, is_material)

        # Try fire protection patterns
        for fire_type, config in FIRE_PATTERNS.items():
            match = re.search(config['pattern'], description, re.IGNORECASE)
            if match:
                return self._normalize_fire(description, fire_type, match, config, is_material)

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
            ka = match.group(4) if (match.lastindex or 0) >= 4 else None
            specs = {'poles': poles, 'amps': amps, 'ka': ka}
            # Standard Naming Strategy: kA should be part of the 3rd component, not a 4th component
            ka_str = f" {ka}kA" if ka else ""
            normalized = f"MCB - {poles}P - {amps}A{ka_str}"

        elif breaker_type == 'rccb':
            breaker = match.group(1)
            poles = match.group(2)
            amps = match.group(3)
            ka = match.group(4) if (match.lastindex or 0) >= 4 else None
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
        diameter = match.group(1) if (match.lastindex or 0) >= 1 else None
        if diameter:
            specs['diameter'] = diameter

        # Extract pressure (for HDPE, PVC, PPR)
        pressure = None
        if (match.lastindex or 0) >= 2 and match.group(2):
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
            wattage = match.group(1) if (match.lastindex or 0) >= 1 else None
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

    def _normalize_valve(
        self,
        description: str,
        valve_type: str,
        match: re.Match,
        config: dict,
        is_material: bool
    ) -> MEPEquipmentResult:
        """Normalize valve description: Van cổng - DN80"""
        specs = {}

        if valve_type == 'generic':
            subtype = match.group(1)
            diameter = match.group(2)
            specs = {'subtype': subtype, 'diameter': diameter}
            normalized = f"Van {subtype} - DN{diameter}"
        else:
            diameter = match.group(1) if (match.lastindex or 0) >= 1 else None
            if diameter:
                specs['diameter'] = diameter

            valve_name_map = {
                'gate': 'Van cổng',
                'butterfly': 'Van bướm',
                'ball': 'Van bi',
                'check': 'Van một chiều',
            }
            name = valve_name_map.get(valve_type, f'Van {valve_type}')
            normalized = f"{name} - DN{diameter}" if diameter else name

        return MEPEquipmentResult(
            original=description,
            normalized=normalized,
            equipment_type=f'valve_{valve_type}',
            specs=specs,
            confidence=0.9,
            is_material_only=is_material
        )

    def _normalize_fitting(
        self,
        description: str,
        fitting_type: str,
        match: re.Match,
        config: dict,
        is_material: bool
    ) -> MEPEquipmentResult:
        """Normalize pipe fitting: Côn thu - uPVC - D110/D60"""
        specs = {}

        if fitting_type == 'reducer':
            material = match.group(1) or ''
            d1 = match.group(2)
            d2 = match.group(3)
            specs = {'material': material, 'd1': d1, 'd2': d2}
            parts = ['Côn thu']
            if material:
                parts.append(material)
            parts.append(f'D{d1}/D{d2}')
            normalized = ' - '.join(parts)

        elif fitting_type in ('elbow', 'tee', 'flange'):
            material = match.group(1) or ''
            diameter = match.group(2) if (match.lastindex or 0) >= 2 else None
            specs = {'material': material, 'diameter': diameter}

            fitting_name_map = {
                'elbow': 'Cút',
                'tee': 'Tê',
                'flange': 'Bích',
            }
            name = fitting_name_map[fitting_type]

            # Check for "mạ kẽm" in original description
            if 'mạ kẽm' in description.lower():
                material = (material + ' mạ kẽm').strip() if material else 'thép mạ kẽm'

            parts = [name]
            if material:
                parts.append(material)
            if diameter:
                parts.append(f'DN{diameter}')
            normalized = ' - '.join(parts)

        elif fitting_type == 'flexible_joint':
            material = match.group(1) or ''
            diameter = match.group(2) if (match.lastindex or 0) >= 2 else None
            specs = {'material': material, 'diameter': diameter}

            parts = ['Khớp nối mềm']
            if material:
                parts.append(material)
            if diameter:
                parts.append(f'DN{diameter}')
            normalized = ' - '.join(parts)

        elif fitting_type == 'coupling':
            material = match.group(1) or ''
            diameter = match.group(2) if (match.lastindex or 0) >= 2 else None
            specs = {'material': material, 'diameter': diameter}

            parts = ['Măng sông']
            if material:
                parts.append(material)
            if diameter:
                parts.append(f'DN{diameter}')
            normalized = ' - '.join(parts)

        else:
            normalized = description

        return MEPEquipmentResult(
            original=description,
            normalized=normalized,
            equipment_type=f'fitting_{fitting_type}',
            specs=specs,
            confidence=0.9,
            is_material_only=is_material
        )

    def _normalize_electrical_accessory(
        self,
        description: str,
        acc_type: str,
        match: re.Match,
        config: dict,
        is_material: bool
    ) -> MEPEquipmentResult:
        """Normalize electrical accessory: Contactor - 3P - 12A, Aptomat - 3P - 32A"""
        specs = {}

        if acc_type == 'contactor':
            poles = match.group(1)
            amps = match.group(2)
            specs = {'poles': poles, 'amps': amps}
            normalized = f"Contactor - {poles}P - {amps}A"

        elif acc_type == 'contactor_simple':
            amps = match.group(1)
            specs = {'amps': amps}
            normalized = f"Contactor - {amps}A"

        elif acc_type == 'aptomat_full':
            poles = match.group(1)
            amps = match.group(2)
            specs = {'poles': poles, 'amps': amps}
            normalized = f"Aptomat - {poles}P - {amps}A"

        elif acc_type == 'aptomat_simple':
            amps = match.group(1)
            specs = {'amps': amps}
            normalized = f"Aptomat - {amps}A"

        elif acc_type == 'fuse':
            amps = match.group(1)
            specs = {'amps': amps}
            normalized = f"Cầu chì - {amps}A"

        elif acc_type == 'busbar':
            amps = match.group(1)
            specs = {'amps': amps}
            normalized = f"Thanh cái đồng - {amps}A"

        elif acc_type == 'indicator_light':
            normalized = "Đèn báo pha"

        elif acc_type == 'timer':
            amps = match.group(1) if (match.lastindex or 0) >= 1 else None
            specs = {'amps': amps}
            normalized = f"Timer hẹn giờ - {amps}A" if amps else "Timer hẹn giờ"

        elif acc_type == 'relay':
            amps = match.group(1) if (match.lastindex or 0) >= 1 else None
            specs = {'amps': amps}
            normalized = f"Rơ le trung gian - {amps}A" if amps else "Rơ le trung gian"

        else:
            normalized = description

        return MEPEquipmentResult(
            original=description,
            normalized=normalized,
            equipment_type=f'electrical_{acc_type}',
            specs=specs,
            confidence=0.9,
            is_material_only=is_material
        )

    def _normalize_instrument(
        self,
        description: str,
        inst_type: str,
        match: re.Match,
        config: dict,
        is_material: bool
    ) -> MEPEquipmentResult:
        """Normalize instrument: Đồng hồ nước - DN25"""
        specs = {}

        if inst_type == 'water_meter':
            diameter = match.group(1)
            specs = {'diameter': diameter}
            normalized = f"Đồng hồ nước - DN{diameter}"

        elif inst_type == 'pressure_gauge':
            bar = match.group(1) if (match.lastindex or 0) >= 1 and match.group(1) else None
            specs = {'range': f'{bar}bar'} if bar else {}
            normalized = f"Đồng hồ đo áp suất - {bar}bar" if bar else "Đồng hồ đo áp suất"

        elif inst_type == 'flow_meter':
            diameter = match.group(1) if (match.lastindex or 0) >= 1 and match.group(1) else None
            specs = {'diameter': diameter} if diameter else {}
            normalized = f"Đồng hồ lưu lượng - DN{diameter}" if diameter else "Đồng hồ lưu lượng"

        elif inst_type == 'thermometer':
            normalized = "Nhiệt kế"

        else:
            normalized = description

        return MEPEquipmentResult(
            original=description,
            normalized=normalized,
            equipment_type=f'instrument_{inst_type}',
            specs=specs,
            confidence=0.85,
            is_material_only=is_material
        )

    def _normalize_pump(
        self,
        description: str,
        pump_type: str,
        match: re.Match,
        config: dict,
        is_material: bool
    ) -> MEPEquipmentResult:
        """Normalize pump: Bơm chìm - 2HP"""
        specs = {}

        # Extract power spec from the original description
        power_match = re.search(r'(\d+(?:\.\d+)?)\s*(HP|kW|KW)', description, re.IGNORECASE)
        power_str = f"{power_match.group(1)}{power_match.group(2).upper()}" if power_match else None
        if power_str:
            # Normalize kW casing
            power_str = power_str.replace('KW', 'kW')
            specs['power'] = power_str

        pump_name_map = {
            'submersible': 'Bơm chìm',
            'centrifugal': 'Bơm ly tâm',
            'booster': 'Bơm tăng áp',
            'fire': 'Bơm chữa cháy',
        }

        if pump_type == 'generic':
            subtype = match.group(1)
            name = f"Bơm {subtype}"
        else:
            name = pump_name_map.get(pump_type, f'Bơm {pump_type}')

        normalized = f"{name} - {power_str}" if power_str else name

        return MEPEquipmentResult(
            original=description,
            normalized=normalized,
            equipment_type=f'pump_{pump_type}',
            specs=specs,
            confidence=0.85,
            is_material_only=is_material
        )

    def _normalize_hvac(
        self,
        description: str,
        hvac_type: str,
        match: re.Match,
        config: dict,
        is_material: bool
    ) -> MEPEquipmentResult:
        """Normalize HVAC equipment: Điều hòa - 12000BTU"""
        specs = {}

        # Extract capacity from original description
        cap_match = re.search(r'(\d+(?:\.\d+)?)\s*(HP|kW|KW|BTU|TR|ton)', description, re.IGNORECASE)
        cap_str = f"{cap_match.group(1)}{cap_match.group(2).upper()}" if cap_match else None
        if cap_str:
            cap_str = cap_str.replace('KW', 'kW')
            specs['capacity'] = cap_str

        hvac_name_map = {
            'ahu': 'AHU',
            'fcu': 'FCU',
            'ac': 'Điều hòa',
            'indoor_unit': 'Dàn lạnh',
            'outdoor_unit': 'Dàn nóng',
            'fan': 'Quạt thông gió',
        }

        if hvac_type == 'duct':
            # Duct has dimensions WxH
            w = match.group(1) if (match.lastindex or 0) >= 1 and match.group(1) else None
            h = match.group(2) if (match.lastindex or 0) >= 2 and match.group(2) else None
            if w and h:
                specs = {'width': w, 'height': h}
                normalized = f"Ống gió - {w}x{h}"
            else:
                normalized = "Ống gió"
        else:
            name = hvac_name_map.get(hvac_type, hvac_type)
            normalized = f"{name} - {cap_str}" if cap_str else name

        return MEPEquipmentResult(
            original=description,
            normalized=normalized,
            equipment_type=f'hvac_{hvac_type}',
            specs=specs,
            confidence=0.85,
            is_material_only=is_material
        )

    def _normalize_fire(
        self,
        description: str,
        fire_type: str,
        match: re.Match,
        config: dict,
        is_material: bool
    ) -> MEPEquipmentResult:
        """Normalize fire protection equipment: Sprinkler - DN15"""
        specs = {}

        if fire_type == 'sprinkler':
            diameter = match.group(1) if (match.lastindex or 0) >= 1 and match.group(1) else None
            if diameter:
                specs['diameter'] = diameter
            normalized = f"Sprinkler - DN{diameter}" if diameter else "Sprinkler"

        elif fire_type == 'fire_alarm':
            # Check if khói or nhiệt
            if 'khói' in description.lower():
                normalized = "Đầu báo cháy khói"
            elif 'nhiệt' in description.lower():
                normalized = "Đầu báo cháy nhiệt"
            else:
                normalized = "Đầu báo cháy"

        elif fire_type == 'fire_extinguisher':
            capacity = match.group(1) if (match.lastindex or 0) >= 1 and match.group(1) else None
            unit_match = re.search(r'(\d+)\s*(kg|l)', description, re.IGNORECASE)
            if unit_match:
                specs = {'capacity': unit_match.group(1), 'unit': unit_match.group(2)}
                normalized = f"Bình chữa cháy - {unit_match.group(1)}{unit_match.group(2)}"
            else:
                normalized = "Bình chữa cháy"

        elif fire_type == 'fire_hose':
            diameter = match.group(1) if (match.lastindex or 0) >= 1 and match.group(1) else None
            if diameter:
                specs['diameter'] = diameter
            normalized = f"Vòi chữa cháy - DN{diameter}" if diameter else "Vòi chữa cháy"

        elif fire_type == 'fire_cabinet':
            normalized = "Tủ chữa cháy"

        else:
            normalized = description

        return MEPEquipmentResult(
            original=description,
            normalized=normalized,
            equipment_type=f'fire_{fire_type}',
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
