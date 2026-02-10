"""
Imputation rules for filling missing values.

This module provides default values for common construction items
when specifications are not explicitly provided in the description.

Default values are based on Vietnam construction domain knowledge
and common industry practices.
"""
from typing import Dict, Optional

# --- Data Source: Try JSON first, fallback to hardcoded ---
_DATA_SOURCE = 'hardcoded'
try:
    from .dictionaries.data_loader import load_imputation_defaults
    IMPUTATION_DEFAULTS = load_imputation_defaults()
    _DATA_SOURCE = 'json'
except Exception:
    pass

# Hardcoded fallback
_HARDCODED_IMPUTATION_DEFAULTS = {
    # ==========================================================================
    # Công tác đất (Earthwork)
    # ==========================================================================
    'Đào': {
        'method': 'Máy đào 0.8m3',
        'soil_class': 'Đất cấp 3',
    },
    'Đào đất': {
        'method': 'Máy đào 0.8m3',
        'soil_class': 'Đất cấp 3',
    },
    'Đào phá dỡ': {
        'position': 'Nền đường',
    },
    'Đào khuôn đường': {
        'soil_class': 'Đất cấp 3',
        'method': 'Máy/Thủ công',
    },
    'Đắp': {
        'method': 'Lu rung 6T',
        'compaction': 'Đất K95',
    },
    'Đắp đất': {
        'method': 'Lu rung 6T',
        'compaction': 'Đất K95',
    },
    'Đắp đất nền': {
        'compaction': 'Đất K95',
    },
    'Đắp đất hoàn trả': {
        'compaction': 'Đất K95',
    },
    'San nền': {
        'method': 'Máy ủi D6',
        'compaction': 'K95',
    },
    'Lu lèn': {
        'method': 'Lu rung 10T',
    },
    'Đầm nén': {
        'method': 'Đầm cóc',
        'compaction': 'K95',
    },

    # ==========================================================================
    # Vận chuyển (Transport)
    # ==========================================================================
    'Vận chuyển': {
        'distance': '≤5km',
        'destination': 'Đổ đúng nơi quy định',
    },

    # ==========================================================================
    # Bê tông (Concrete)
    # ==========================================================================
    'Bê tông': {
        # Position-based defaults (checked in order)
        'lót': 'M100',
        'lót móng': 'M100',
        'móng': 'M250',
        'đế móng': 'M250',
        'đài móng': 'M300',
        'cột': 'M300',
        'dầm': 'M350',
        'sàn': 'M350',
        'dầm sàn': 'M350',
        'vách': 'M300',
        'cầu thang': 'M300',
        'default': 'M250',
        'stone': 'Đá 1x2',
    },
    'Bê tông lót': {
        'grade': 'M100',
        'stone': 'Đá 4x6',
    },
    'Bê tông mặt đường': {
        'grade': 'M250',
        'stone': 'Đá 1x2',
    },
    'Bê tông vỉa hè': {
        'grade': 'M200',
        'stone': 'Đá 1x2',
    },
    'Bê tông thương phẩm': {
        'type': 'Thương phẩm',
        'stone': 'Đá 1x2',
    },

    # ==========================================================================
    # Cốt thép (Rebar)
    # ==========================================================================
    'Cốt thép': {
        'grade': 'Theo thiết kế',
    },

    # ==========================================================================
    # Ván khuôn (Formwork)
    # ==========================================================================
    'Ván khuôn': {
        'type_if_needed': 'Theo thiết kế',
    },

    # ==========================================================================
    # Hoàn thiện (Finishing)
    # ==========================================================================
    'Trát': {
        'mortar': 'Vữa xi măng',
    },
    'Láng': {
        'mortar': 'Vữa xi măng',
    },
    'Chèn vữa': {
        'mortar': 'Xi măng',
    },
    'Xây': {
        'mortar': 'M75',
    },
    'Xây gạch': {
        'material': 'Gạch đặc M75',
    },
    'Xây đá': {
        'material': 'Đá hộc',
        'mortar': 'Vữa M100',
    },
    'Xây bể cáp': {
        'material': 'Gạch',
    },
    'Xây tường': {
        'material': 'Đá/Gạch',
    },
    'Lát': {
        'mortar': 'M50',
    },
    'Ốp': {
        'mortar': 'M50',
    },
    'Sơn': {
        'coat': '1 lót 2 phủ',
    },

    # ==========================================================================
    # Đường (Road)
    # ==========================================================================
    'CPĐD': {
        'compaction': 'K98',
    },
    'Móng đường': {
        'material': 'CPĐD',
    },
    'BTN': {
        'type': 'Nóng',
    },
    'Mặt đường': {
        'material': 'Bê tông nhựa',
    },
    'Tưới nhựa': {
        'type': 'Thấm bám',
    },

    # ==========================================================================
    # Bó vỉa / Tấm đan (Curb / Cover)
    # ==========================================================================
    'Bó vỉa': {
        'material': 'Đá tự nhiên',
    },
    'Tấm đan': {
        'material': 'Đá',
    },
    'Tấm đan rãnh': {
        'material': 'Đá',
    },
    'Tấm lát mái': {
        'material': 'Bê tông đúc sẵn',
    },

    # ==========================================================================
    # Cọc tre (Bamboo piles)
    # ==========================================================================
    'Cọc tre': {
        'purpose': 'Gia cố nền',
        'spec': 'Theo thiết kế',
    },

    # ==========================================================================
    # MEP - Ống (Piping)
    # ==========================================================================
    'Ống': {
        'material': 'HDPE',
    },
    'Ống HDPE': {
        'pressure': 'PN10',
    },
    'Ống PVC': {
        'pressure': 'PN6',
    },
    'Ống PPR': {
        'pressure': 'PN10',
    },
    'Ống uPVC': {
        'pressure': 'PN8',
    },
    'Ống thép': {
        'type': 'Đen',
    },
    'Ống luồn dây': {
        'type': 'HDPE Gân xoắn',
    },
    'Ống nhựa': {
        'material': 'HDPE',
    },

    # ==========================================================================
    # MEP - Thiết bị (Equipment)
    # ==========================================================================
    'Trụ cứu hỏa': {
        'material': 'Gang',
    },
    'Hộp đựng bình chữa cháy': {
        'material': 'Thép sơn tĩnh điện',
    },
    'Cửa xả': {
        'material': 'Bê tông cốt thép',
    },
    'Nắp hố ga': {
        'material': 'Gang',
    },
    'Van báo động (Alarm Valve)': {
        'material': 'Gang',
    },
    'Gối đỡ ống': {
        'material': 'Bê tông/Composite',
    },
    'Đồng hồ nước': {
        'type': 'Theo thiết kế',
    },
    'Cụm van quản lý': {
        'spec': 'Trọn bộ',
    },
    'Cụm van xả khí': {
        'spec': 'Trọn bộ',
    },
    'Lò xo giảm chấn': {
        'material': 'Thép/Cao su',
    },

    # ==========================================================================
    # Vật liệu khác (Other materials)
    # ==========================================================================
    'Vải địa kỹ thuật': {
        'type': 'Không dệt',
    },
    'Nilon': {
        'type': 'Tái sinh',
        'position': 'Lót móng',
    },
    'Đất màu': {
        'purpose': 'Trồng cây',
    },
    'Đá hộc': {
        'type': 'Xếp khan',
    },
    'Đá dăm': {
        'purpose': 'Đệm móng',
    },
    'Thang thép': {
        'material': 'Thép hình',
    },

    # ==========================================================================
    # Chi phí / Vật tư phụ (Costs / Auxiliary)
    # ==========================================================================
    'Chi phí': {
        'type': 'Kiểm định/Thí nghiệm',
        'scope': 'Trọn gói',
    },
    'Vật tư phụ': {
        'purpose': 'Đấu nối tủ điện',
        'scope': 'Trọn gói',
    },
    'Bản quan trắc': {
        'type': 'Quan trắc lún',
        'scope': 'Trọn bộ',
    },
}

if _DATA_SOURCE == 'hardcoded':
    IMPUTATION_DEFAULTS = _HARDCODED_IMPUTATION_DEFAULTS


def get_default_for_object(object_type: str, spec_key: str) -> Optional[str]:
    """
    Get default value for an object type and spec key.

    Args:
        object_type: The object type (e.g., 'Bê tông', 'Đào')
        spec_key: The specification key (e.g., 'grade', 'method')

    Returns:
        Default value or None if not found
    """
    defaults = IMPUTATION_DEFAULTS.get(object_type, {})
    return defaults.get(spec_key)


def impute_missing(object_type: str, specs: Dict, position: Optional[str] = None) -> Dict:
    """
    Fill missing values based on object type and context.

    Args:
        object_type: The identified object type
        specs: Current extracted specifications
        position: Optional structural position (for concrete grade inference)

    Returns:
        Updated specs dict with imputed values.
        The dict will contain a special '_imputed_keys' key listing which
        keys were imputed (not extracted from input).
    """
    result = specs.copy()
    imputed_keys = []
    defaults = IMPUTATION_DEFAULTS.get(object_type, {})

    if not defaults:
        result['_imputed_keys'] = []
        return result

    # ==========================================================================
    # Earthwork (Đào, Đắp, San, Lu)
    # ==========================================================================
    if object_type in ['Đào', 'Đào đất']:
        if 'method' not in result:
            result['method'] = defaults.get('method')
            imputed_keys.append('method')
        if 'soil_class' not in result:
            result['soil_class'] = defaults.get('soil_class')
            imputed_keys.append('soil_class')

    elif object_type in ['Đắp', 'Đắp đất', 'Đầm nén', 'Lu lèn', 'San nền']:
        if 'method' not in result:
            result['method'] = defaults.get('method')
            imputed_keys.append('method')
        if 'compaction' not in result and 'compaction' in defaults:
            result['compaction'] = defaults.get('compaction')
            imputed_keys.append('compaction')

    # ==========================================================================
    # Transport (Vận chuyển)
    # ==========================================================================
    elif object_type == 'Vận chuyển':
        if 'distance' not in result:
            result['distance'] = defaults.get('distance')
            imputed_keys.append('distance')

    # ==========================================================================
    # Concrete (Bê tông)
    # ==========================================================================
    elif object_type in ['Bê tông', 'Bê tông thương phẩm', 'Bê tông lót']:
        if 'grade' not in result:
            # Position-based grade inference
            if position:
                pos_lower = position.lower()
                for pos_key in ['lót móng', 'lót', 'móng', 'đài móng', 'cột', 'dầm sàn', 'dầm', 'sàn', 'vách']:
                    if pos_key in pos_lower:
                        result['grade'] = defaults.get(pos_key)
                        imputed_keys.append('grade')
                        break

            # Fallback to default if still not set
            if 'grade' not in result:
                if object_type == 'Bê tông lót':
                    result['grade'] = 'M100'
                else:
                    result['grade'] = defaults.get('default', 'M250')
                imputed_keys.append('grade')

        # Add default stone size
        if 'stone' not in result:
            if object_type == 'Bê tông lót':
                result['stone'] = 'đá 4x6'
            else:
                result['stone'] = defaults.get('stone', 'đá 1x2')
            imputed_keys.append('stone')

    # ==========================================================================
    # Rebar (Cốt thép)
    # ==========================================================================
    elif object_type == 'Cốt thép':
        if 'grade' not in result:
            result['grade'] = defaults.get('grade', 'CB300')
            imputed_keys.append('grade')

    # ==========================================================================
    # Formwork (Ván khuôn)
    # NOTE: Removed default type imputation to prevent hallucination (Bug 3)
    # ==========================================================================
    elif object_type == 'Ván khuôn':
        # Do NOT auto-fill type - let user decide
        pass

    # ==========================================================================
    # Finishing (Hoàn thiện)
    # ==========================================================================
    elif object_type == 'Trát':
        if 'thickness' not in result:
            result['thickness'] = defaults.get('thickness')
            imputed_keys.append('thickness')
        if 'mortar' not in result:
            result['mortar'] = defaults.get('mortar')
            imputed_keys.append('mortar')

    elif object_type in ['Xây', 'Lát', 'Ốp']:
        if 'mortar' not in result:
            result['mortar'] = defaults.get('mortar')
            imputed_keys.append('mortar')

    elif object_type == 'Sơn':
        if 'coat' not in result:
            result['coat'] = defaults.get('coat')
            imputed_keys.append('coat')

    # ==========================================================================
    # Road (CPĐD, BTN)
    # ==========================================================================
    elif object_type == 'CPĐD':
        if 'compaction' not in result:
            result['compaction'] = defaults.get('compaction', 'K98')
            imputed_keys.append('compaction')

    # ==========================================================================
    # MEP (Ống)
    # ==========================================================================
    elif 'Ống' in object_type:
        if 'pressure' not in result and 'pressure' in defaults:
            result['pressure'] = defaults.get('pressure')
            imputed_keys.append('pressure')

    result['_imputed_keys'] = imputed_keys
    return result


def get_concrete_grade_for_position(position: str) -> str:
    """
    Get default concrete grade based on structural position.

    Args:
        position: Structural position (e.g., 'dầm sàn', 'móng')

    Returns:
        Concrete grade (e.g., 'M350', 'M250')
    """
    pos_lower = position.lower() if position else ''

    grade_map = {
        'lót móng': 'M100',
        'lót': 'M100',
        'đế móng': 'M250',
        'bệ móng': 'M250',
        'móng': 'M250',
        'đài móng': 'M300',
        'giằng móng': 'M300',
        'cột': 'M300',
        'dầm sàn': 'M350',
        'dầm': 'M350',
        'sàn': 'M350',
        'vách': 'M300',
        'tường': 'M300',
        'cầu thang': 'M300',
    }

    for pos_key, grade in grade_map.items():
        if pos_key in pos_lower:
            return grade

    return 'M250'  # Default grade


# CPDD layer mapping (loại 1/2 → lớp trên/dưới)
CPDD_LAYER_MAP = {
    'loại 1': 'Lớp trên',
    'loai 1': 'Lớp trên',
    'loại i': 'Lớp trên',
    'loại 2': 'Lớp dưới',
    'loai 2': 'Lớp dưới',
    'loại ii': 'Lớp dưới',
    'lớp trên': 'Lớp trên',
    'lop tren': 'Lớp trên',
    'lớp dưới': 'Lớp dưới',
    'lop duoi': 'Lớp dưới',
}


def get_cpdd_layer(text: str) -> str:
    """
    Get CPDD layer from text.

    Maps loại 1/I to Lớp trên and loại 2/II to Lớp dưới.

    Args:
        text: Input text

    Returns:
        Layer name or empty string if not found
    """
    text_lower = text.lower()

    # Sort by length to match longer patterns first
    sorted_patterns = sorted(CPDD_LAYER_MAP.items(), key=lambda x: len(x[0]), reverse=True)
    for pattern, layer in sorted_patterns:
        if pattern in text_lower:
            return layer

    return ''

