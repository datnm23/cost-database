"""
Centralized Material Registry.

Single source of truth for material detection across all extractors
and the priority processor. Uses normalized matching for diacritics tolerance.

Usage:
    from .material_registry import MaterialRegistry

    registry = MaterialRegistry()
    material = registry.detect(text)  # Returns material name or None
    material = registry.detect(text, category='pipe')  # Category-specific
"""
from typing import Optional, Dict, Set
from .text_normalizer import normalize_vietnamese, _is_word_boundary_match
from .materials import DICT_MATERIALS, DICT_PRESSURE


# Material aliases (abbreviations → canonical names)
MATERIAL_ALIASES = {
    'TTK': 'Thép Tráng kẽm',
    'BTCT': 'BTCT',
    'BT': 'Bê tông',
    'HDPE': 'HDPE',
    'PVC': 'PVC',
    'PPR': 'PPR',
    'BTN': 'BTN',
    'CPĐD': 'CPĐD',
}

# Category to material mapping for filtered detection
MATERIAL_CATEGORIES = {
    'pipe': {
        'HDPE', 'PE100', 'PE80', 'PPR', 'uPVC', 'CPVC', 'PVC', 'ABS', 'FRP', 'GRP',
        'Thép mạ kẽm', 'Thép đen', 'Inox', 'Gang', 'Đồng',
        'Thép Tráng kẽm', 'Ống mềm',
    },
    'electrical': {
        'Cu/XLPE/PVC/DSTA', 'Cu/XLPE/PVC', 'Cu/XLPE', 'Cu/PVC',
        'Al/XLPE/PVC', 'Nhôm bọc', 'Nhôm', 'Đồng trần', 'Đồng', 'XLPE',
    },
    'structural': {
        'BTCT', 'BT đúc sẵn', 'BT tươi', 'BT thương phẩm', 'Bê tông',
        'CB400V', 'CB300T', 'CB300', 'CB240', 'Thép cuộn', 'Thép thanh',
    },
    'precast': {
        'BTCT', 'Bê tông', 'Gang', 'Nhựa', 'Composite',
        'Đá Granite', 'Đá tự nhiên', 'Đá',
    },
    'finishing': {
        'Granite', 'Granite nhân tạo', 'Granite tự nhiên', 'Granite bóng kính',
        'Ceramic', 'Porcelain', 'Gạch men', 'Đá marble', 'Đá hoa cương',
        'Phủ phim', 'Ván ép',
    },
    'road': {
        'CPĐD', 'Đá dăm', 'BTN', 'Asphalt',
    },
}


class MaterialRegistry:
    """
    Centralized material detection using normalized matching.

    Consolidates all material dictionaries into a single registry
    with optional category filtering.
    """

    def __init__(self):
        # Build normalized lookup from DICT_MATERIALS
        self._norm_materials = {}
        for key, value in sorted(DICT_MATERIALS.items(), key=lambda x: len(x[0]), reverse=True):
            norm_key = normalize_vietnamese(key)
            if norm_key not in self._norm_materials:
                self._norm_materials[norm_key] = value

        # Build normalized pressure lookup
        self._norm_pressure = {}
        for key, value in sorted(DICT_PRESSURE.items(), key=lambda x: len(x[0]), reverse=True):
            norm_key = normalize_vietnamese(key)
            if norm_key not in self._norm_pressure:
                self._norm_pressure[norm_key] = value

    def detect(self, text: str, category: Optional[str] = None) -> Optional[str]:
        """
        Detect material in text.

        Args:
            text: Input text
            category: Optional category filter ('pipe', 'electrical', 'structural',
                      'precast', 'finishing', 'road')

        Returns:
            Material name or None
        """
        text_norm = normalize_vietnamese(text)
        allowed = MATERIAL_CATEGORIES.get(category) if category else None

        for keyword, material in self._norm_materials.items():
            if _is_word_boundary_match(text_norm, keyword):
                if allowed is None or material in allowed:
                    # Guard: "dong" inside "dong ho" is not copper material
                    if keyword == 'dong' and 'dong ho' in text_norm:
                        continue
                    # Guard: "dong" in "ro le dong" means current, not copper
                    if keyword == 'dong' and ('ro le' in text_norm or 'role' in text_norm):
                        continue
                    return material

        return None

    def detect_pressure(self, text: str) -> Optional[str]:
        """
        Detect pressure rating in text.

        Args:
            text: Input text

        Returns:
            Pressure rating (e.g., 'PN10') or None
        """
        text_norm = normalize_vietnamese(text)

        for keyword, pressure in self._norm_pressure.items():
            if keyword in text_norm:
                return pressure

        return None

    def resolve_alias(self, alias: str) -> Optional[str]:
        """
        Resolve a material alias to its canonical name.

        Args:
            alias: Material alias (e.g., 'TTK')

        Returns:
            Canonical material name or None
        """
        return MATERIAL_ALIASES.get(alias.upper())

    def get_all_for_category(self, category: str) -> Set[str]:
        """
        Get all material names for a category.

        Args:
            category: Category name

        Returns:
            Set of material names
        """
        return MATERIAL_CATEGORIES.get(category, set())


# Singleton instance
_registry = None


def get_material_registry() -> MaterialRegistry:
    """Get singleton MaterialRegistry instance."""
    global _registry
    if _registry is None:
        _registry = MaterialRegistry()
    return _registry
