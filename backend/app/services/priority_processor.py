"""
3-Layer Priority Processor.

This module implements the priority-based object identification
to solve the "Identity Theft" problem where flat keyword matching
incorrectly identifies objects.

The 3-layer model:
1. Object Identification (Priority 1-2-3 dictionary)
2. Attribute Extraction (Context-aware extractors)
3. Assembly & Imputation (Fill missing values)

Example:
    Input: "Ván khuôn móng bê tông M200"

    Before (Wrong): Matched "Bê tông" → Output: "Bê tông - M200"
    After (Correct): Matched "Ván khuôn" (Priority 1) → Output: "Ván khuôn - Móng - Phủ phim"
"""
import re
from dataclasses import dataclass, field
from typing import Dict, Optional, List

from .dictionaries.priority_objects import identify_object, identify_object_with_details, identify_all_objects, fuzzy_identify
from .dictionaries.text_normalizer import normalize_vietnamese, _is_word_boundary_match
from .extractors.formwork_extractor import FormworkExtractor
from .extractors.road_extractor import RoadExtractor
from .extractors.precast_extractor import PrecastExtractor
from .extractors.electrical_extractor import ElectricalExtractor
from .extractors.earthwork_extractor import EarthworkExtractor
from .extractors.concrete_extractor import ConcreteExtractor
from .extractors.pipe_fitting_extractor import PipeFittingExtractor
from .extractors.pump_extractor import PumpExtractor
from .extractors.mep_equipment_extractor import MEPEquipmentExtractor
from .imputation_rules import impute_missing, get_cpdd_layer, IMPUTATION_DEFAULTS
from .dictionary_assembler import DictionaryBasedAssembler


@dataclass
class PriorityProcessResult:
    """Result of priority-based processing."""
    object_name: Optional[str] = None
    priority: int = 0
    priority_type: str = 'unknown'
    specs: Dict = field(default_factory=dict)
    normalized: str = ''
    confidence: float = 0.0
    extractor_used: Optional[str] = None
    match_type: str = 'exact'  # 'exact' or 'fuzzy'
    confidence_breakdown: Dict = field(default_factory=dict)
    imputed_keys: List[str] = field(default_factory=list)
    secondary_object: Optional[str] = None
    secondary_priority: int = 0
    secondary_priority_type: str = 'unknown'


class PriorityProcessor:
    """
    Main processor using 3-layer priority model.

    This replaces flat keyword matching with priority-based
    object identification to solve the "Identity Theft" problem.
    """

    # Positions that indicate concrete is the main object, not the position itself
    # "Bê tông hố ga" → Object = Bê tông, position = hố ga
    CONCRETE_POSITIONS = [
        'đáy hố ga', 'đáy cống', 'thân cống', 'sân cống',
        'thành cống', 'nắp hố ga', 'thành hố ga',
        'hố ga',
        'mương',
        'móng',
        'cột',
        'dầm',
        'sàn',
        'vách',
        'tường',
        'tường cánh', 'dàn treo', 'cửa điều tiết',
    ]

    # Materials for extraction
    MATERIALS = {
        'hdpe': 'HDPE',
        'ppr': 'PPR',
        'u.pvc': 'uPVC',
        'upvc': 'uPVC',
        'pvc': 'PVC',
        'btct': 'BTCT',
        'bê tông cốt thép': 'BTCT',
        'gang': 'Gang',
        'thép tráng kẽm': 'Thép Tráng kẽm',
        'ttk': 'Thép Tráng kẽm',
        'thép đen': 'Đen',
        'thép': 'Thép',
        'composite': 'Composite',
        'inox': 'Inox',
        'gi': 'Mạ kẽm',
    }

    def __init__(self):
        """Initialize with context-aware extractors."""
        # Shared extractor instances
        formwork_ext = FormworkExtractor()
        road_ext = RoadExtractor()
        precast_ext = PrecastExtractor()
        electrical_ext = ElectricalExtractor()
        earthwork_ext = EarthworkExtractor()
        concrete_ext = ConcreteExtractor()
        pipe_ext = PipeFittingExtractor()
        pump_ext = PumpExtractor()
        mep_ext = MEPEquipmentExtractor()

        self.extractors = {
            # Priority 1: Methods/Activities
            'Ván khuôn': formwork_ext,
            'Đào đất': earthwork_ext,
            'Đào': earthwork_ext,
            'Đào phá dỡ': earthwork_ext,
            'Đào khuôn đường': earthwork_ext,
            'Đắp đất': earthwork_ext,
            'Đắp đất nền': earthwork_ext,
            'Đắp đất hoàn trả': earthwork_ext,
            'Đắp': earthwork_ext,
            'Vận chuyển': earthwork_ext,
            'Tưới nhựa': road_ext,
            'Mặt đường': road_ext,
            'Rải thảm': road_ext,

            # Priority 2: Specific Components
            'Bó vỉa': precast_ext,
            'Tấm đan': precast_ext,
            'Tấm đan rãnh': precast_ext,
            'Hố ga': precast_ext,
            'Cống thoát nước': precast_ext,
            'Cống hộp': precast_ext,
            'Cống tròn': precast_ext,
            'Rãnh thoát nước': precast_ext,
            'Nắp hố ga': pipe_ext,
            'Song chắn rác': pipe_ext,

            # Concrete types
            'Bê tông': concrete_ext,
            'Bê tông lót': concrete_ext,
            'Bê tông mặt đường': concrete_ext,
            'Bê tông vỉa hè': concrete_ext,

            # Road materials
            'Móng đường': road_ext,
            'BTN': road_ext,
            'CPĐD': road_ext,

            # Electrical devices
            'MCCB': electrical_ext,
            'MCB': electrical_ext,
            'RCCB': electrical_ext,
            'RCBO': electrical_ext,
            'ACB': electrical_ext,
            'Công tơ điện': mep_ext,
            'Đèn báo pha': mep_ext,
            'Đèn tín hiệu': mep_ext,
            'Thanh cái': mep_ext,
            'Cầu chì': mep_ext,
            'Khóa chuyển mạch': mep_ext,
            'Tủ điện': mep_ext,
            'Tủ gom công tơ': mep_ext,
            'Biển báo': mep_ext,
            'Cột đèn': mep_ext,
            'Đèn chiếu sáng': mep_ext,
            'Cọc tiếp địa': mep_ext,

            # New MEP objects
            'Công tắc': mep_ext,
            'Công tắc hẹn giờ': mep_ext,
            'Công tắc nhiệt độ': mep_ext,
            'Công tắc chọn': mep_ext,
            'Chống sét': mep_ext,
            'Chống sét lan truyền': mep_ext,
            'Máy biến áp': mep_ext,
            'Máy phát điện': mep_ext,
            'Máy điều hòa': mep_ext,
            'ATS': electrical_ext,
            'Tủ điều khiển ATS': electrical_ext,
            'Tủ điều khiển': electrical_ext,
            'Quạt': mep_ext,
            'Quạt hướng trục': mep_ext,
            'Quạt gắn tường': mep_ext,
            'Quạt gió thải': mep_ext,
            'Quạt hút': mep_ext,
            'Quạt thông gió': mep_ext,
            'Camera': mep_ext,
            'Switch mạng': mep_ext,
            'Đầu ghi hình': mep_ext,
            'Loa': mep_ext,
            'UPS': mep_ext,
            'Tủ rack': mep_ext,
            'Đồng hồ đa năng': mep_ext,
            'Đồng hồ điện': mep_ext,
            'Đồng hồ đo dòng': mep_ext,
            'Đồng hồ đo áp': mep_ext,
            'Hộp đấu nối quang': mep_ext,
            'Hộp nối cáp': mep_ext,
            'Máng cáp': mep_ext,
            'Rơ le': mep_ext,
            'Rơ le thời gian': mep_ext,
            'Phụ kiện ACB': mep_ext,
            'Phụ kiện MCCB': mep_ext,
            'Chậu rửa': mep_ext,
            'Bồn dầu': mep_ext,
            'Họng tiếp dầu': mep_ext,
            'Bàn gọi PA': mep_ext,
            'Hộp đấu nối': mep_ext,
            'Cáp tín hiệu': mep_ext,
            'Contactor': mep_ext,
            'Biến dòng (CT)': mep_ext,
            'Biến tần (VSD)': mep_ext,

            # HVAC Ductwork
            'Miệng gió': mep_ext,
            'Ống gió': mep_ext,
            'Fire Damper': mep_ext,
            'Chuyển vuông tròn': mep_ext,
            'Gót giày ống gió': mep_ext,
            'Co ống gió': mep_ext,
            'Giảm ống gió': mep_ext,

            # Pipes - new types
            'Ống GI': pipe_ext,
            'Ống Inox': pipe_ext,
            'Ống đồng': pipe_ext,

            # Pipe fittings
            'Cút': pipe_ext,
            'Cút 45 độ': pipe_ext,
            'Cút 90 độ': pipe_ext,
            'Chếch': pipe_ext,
            'Chếch 45 độ': pipe_ext,
            'Tê': pipe_ext,
            'Tê đều': pipe_ext,
            'Tê thu': pipe_ext,
            'Tê hàn': pipe_ext,
            'Côn': pipe_ext,
            'Côn thu': pipe_ext,
            'Y thu': pipe_ext,
            'Măng sông': pipe_ext,
            'Măng sông ren trong': pipe_ext,
            'Măng sông nối ống': pipe_ext,
            'Rắc co': pipe_ext,
            'Rắc co ren ngoài': pipe_ext,
            'Nút bịt': pipe_ext,
            'Đầu bịt': pipe_ext,
            'Đầu bịt/Nút bịt': pipe_ext,
            'Đai khởi thủy': pipe_ext,
            'Khớp nối mềm': pipe_ext,
            'Mặt bích (Bích hàn)': pipe_ext,
            'Đầu nối ren ngoài': pipe_ext,
            'Nút loe': pipe_ext,

            # Valves
            'Van khóa tay gạt': pipe_ext,
            'Van cổng': pipe_ext,
            'Van 1 chiều': pipe_ext,
            'Van bướm': pipe_ext,
            'Van góc': pipe_ext,
            'Van bi': pipe_ext,
            'Van bi rắc co đôi': pipe_ext,
            'Van báo động (Alarm Valve)': pipe_ext,
            'Cụm van quản lý': mep_ext,
            'Cụm van xả khí': mep_ext,

            # Pumps
            'Bơm chữa cháy': pump_ext,
            'Bơm bù áp': pump_ext,
            'Bơm chìm nước thải': pump_ext,
            'Bơm nước': pump_ext,
            'Bơm': pump_ext,
            'Bình tích áp': pump_ext,

            # Pipes
            'Ống HDPE': pipe_ext,
            'Ống uPVC': pipe_ext,
            'Ống PVC': pipe_ext,
            'Ống PPR': pipe_ext,
            'Ống thép': pipe_ext,
            'Ống luồn dây': pipe_ext,
            'Ống nhựa': pipe_ext,
            'Ống': pipe_ext,

            # Fire equipment
            'Trụ cứu hỏa': mep_ext,
            'Bình chữa cháy': mep_ext,
            'Hộp đựng bình chữa cháy': mep_ext,
            'Lò xo giảm chấn': mep_ext,

            # Cables
            'Cáp điện': mep_ext,
            'Cáp trung thế': mep_ext,
            'Cáp hạ thế': mep_ext,

            # Other equipment
            'Đồng hồ nước': mep_ext,
            'Hộp đồng hồ': mep_ext,
            'Cọc tre': earthwork_ext,
            'Cửa xả': precast_ext,
            'Móng trụ': concrete_ext,
            'Khung móng': mep_ext,
            'Bệ tủ': concrete_ext,
            'Thang thép': mep_ext,
            'Gối đỡ ống': pipe_ext,

            # Materials
            'Vải địa kỹ thuật': mep_ext,
            'Nilon': mep_ext,
            'Đất màu': mep_ext,
            'Đá hộc': precast_ext,
            'Đá dăm': precast_ext,
            'Cốt thép': mep_ext,

            # Activities
            'Trát': mep_ext,
            'Láng': mep_ext,
            'Chèn vữa': mep_ext,
            'Xây gạch': mep_ext,
            'Xây đá': mep_ext,
            'Xây tường': mep_ext,
            'Xây bể cáp': mep_ext,
            'Trồng cỏ': mep_ext,

            # Costs
            'Chi phí': mep_ext,
            'Vật tư phụ': mep_ext,
            'Bản quan trắc': mep_ext,
        }

        # Dictionary-based assembler (replaces 68 if-else blocks)
        self.assembler = DictionaryBasedAssembler()

    def process(self, description: str) -> PriorityProcessResult:
        """
        Process description using 3-layer model.

        Layer 1: Object Identification (Priority 1-2-3)
        Layer 2: Attribute Extraction (Context-aware)
        Layer 3: Imputation & Assembly (Fill missing, format output)

        Args:
            description: Original BOQ description

        Returns:
            PriorityProcessResult with identified object and normalized output
        """
        result = PriorityProcessResult()

        if not description or not description.strip():
            return result

        # ==========================================================================
        # Pre-check: "Cáp đến/từ tủ" context (prevents "đến" matching "đèn")
        # ==========================================================================
        cable_route_result = self._check_cable_route_context(description)
        if cable_route_result:
            return cable_route_result

        # ==========================================================================
        # Pre-check: "Phụ kiện/Bộ cắt cho ACB/MCCB" context
        # Prevents accessory items from being classified as the parent device
        # ==========================================================================
        accessory_result = self._check_accessory_context(description)
        if accessory_result:
            return accessory_result

        # ==========================================================================
        # Pre-check: Installation context detection (BUG 1 fix)
        # When "lắp đặt cống" appears, the object should be "Cống", NOT "Vận chuyển"
        # ==========================================================================
        installation_result = self._check_installation_context(description)
        if installation_result:
            return installation_result

        # ==========================================================================
        # Pre-check: Context detection for "Bê tông + vị trí" (Bug 4 fix)
        # When "bê tông" appears with position like "hố ga", "cống", etc.
        # the MAIN OBJECT is "Bê tông", position becomes a modifier
        # ==========================================================================
        concrete_result = self._check_concrete_context(description)
        if concrete_result:
            return concrete_result

        # ==========================================================================
        # Layer 1: Object Identification
        # ==========================================================================
        id_result = identify_object_with_details(description)

        result.object_name = id_result['object_name']
        result.priority = id_result['priority']
        result.priority_type = id_result['priority_type']

        # If primary is P1 (method), scan for secondary objects (P2/P3)
        if result.priority == 1:
            all_matches = identify_all_objects(description)
            for match in all_matches:
                if match['object_name'] != result.object_name:
                    result.secondary_object = match['object_name']
                    result.secondary_priority = match['priority']
                    result.secondary_priority_type = match['priority_type']
                    break

        if not result.object_name:
            # Fuzzy matching fallback for P2/P3 patterns
            fuzzy_result = fuzzy_identify(description)
            if fuzzy_result['object_name']:
                result.object_name = fuzzy_result['object_name']
                result.priority = fuzzy_result['priority']
                result.priority_type = fuzzy_result['priority_type']
                result.match_type = 'fuzzy'
            else:
                # No object identified - return with low confidence
                result.normalized = description
                result.confidence = 0.3
                return result

        # ==========================================================================
        # Layer 2: Attribute Extraction
        # ==========================================================================
        extractor = self.extractors.get(result.object_name)

        if extractor:
            result.specs = extractor.extract(description)
            result.extractor_used = type(extractor).__name__
        else:
            result.specs = self._generic_extract(description)
            result.extractor_used = 'generic'

        # Extract material if not already present
        if 'material' not in result.specs:
            material = self._extract_material(description)
            if material:
                result.specs['material'] = material

        # ==========================================================================
        # Layer 3: Imputation & Assembly
        # ==========================================================================
        # Get position for imputation context
        position = result.specs.get('position')

        # Fill missing values based on object type
        result.specs = impute_missing(result.object_name, result.specs, position)

        # Track imputed keys
        result.imputed_keys = result.specs.pop('_imputed_keys', [])

        # Assemble final output
        result.normalized = self._assemble(result.object_name, result.specs, description)
        result.confidence = self._calculate_confidence(result)

        return result

    def _extract_material(self, description: str) -> Optional[str]:
        """Extract material from description using centralized registry."""
        from .dictionaries.material_registry import get_material_registry
        registry = get_material_registry()
        return registry.detect(description)

    def _generic_extract(self, description: str) -> Dict:
        """
        Generic extraction for objects without specialized extractor.

        Args:
            description: Input text

        Returns:
            Dict with basic extracted specs
        """
        specs = {}
        text_lower = description.lower()

        # Extract grade (M200, CB300, 200#, etc.)
        grade_match = re.search(r'\b[Mm](\d{2,3})\b', description)
        if grade_match:
            specs['grade'] = f"M{grade_match.group(1)}"
        else:
            hash_match = re.search(r'(\d{3})#', description)
            if hash_match:
                specs['grade'] = f"M{hash_match.group(1)}"

        cb_match = re.search(r'\bCB(\d{3})([VvWw])?\b', description, re.IGNORECASE)
        if cb_match:
            suffix = cb_match.group(2).upper() if cb_match.group(2) else ''
            specs['grade'] = f"CB{cb_match.group(1)}{suffix}"

        # Extract dimensions
        dim_match = re.search(
            r'(\d+)\s*[xX×]\s*(\d+)(?:\s*[xX×]\s*(\d+))?',
            description
        )
        if dim_match:
            dims = [dim_match.group(1), dim_match.group(2)]
            if dim_match.group(3):
                dims.append(dim_match.group(3))
            specs['dimensions'] = 'x'.join(dims)

        # Extract diameter (various formats)
        # D200-D140 or D50/32 patterns
        reduction_match = re.search(r'[Dd](\d+)\s*[-]\s*[Dd]?(\d+)', description)
        if reduction_match:
            specs['diameter'] = f"D{reduction_match.group(1)}/{reduction_match.group(2)}"
        else:
            slash_match = re.search(r'[Dd](\d+)\s*/\s*(\d+)', description)
            if slash_match:
                specs['diameter'] = f"D{slash_match.group(1)}/{slash_match.group(2)}"
            else:
                double_match = re.search(r'(\d{2,3})\s*/\s*(\d{2,3})', description)
                if double_match:
                    specs['diameter'] = f"D{double_match.group(1)}/{double_match.group(2)}"
                else:
                    diam_match = re.search(r'[Dd][Nn]?(\d{2,4})\b', description)
                    if diam_match:
                        prefix = 'DN' if 'dn' in text_lower else 'D'
                        specs['diameter'] = f"{prefix}{diam_match.group(1)}"

        # Extract pressure rating
        pn_match = re.search(r'[Pp][Nn]\s*(\d+)', description)
        if pn_match:
            specs['pressure'] = f"PN{pn_match.group(1)}"

        # Extract compaction
        k_match = re.search(r'[Kk][=]?\s*(?:0[.,])?(\d{2})', description)
        if k_match:
            specs['compaction'] = f"K{k_match.group(1)}"

        # Extract rebar diameter
        thep_d_match = re.search(r'thép\s+[Dd](\d+)', text_lower)
        if thep_d_match:
            specs['rebar_diameter'] = f"D{thep_d_match.group(1)}"
        else:
            # Pattern: ≤10mm, ≤18mm
            rebar_size = re.search(r'[≤<](\d+)\s*mm', description)
            if rebar_size:
                specs['rebar_diameter'] = f"≤{rebar_size.group(1)}mm"

        return specs

    def _assemble(self, object_name: str, specs: Dict, original: str = '') -> str:
        """
        Assemble into 3-component format.

        Format: [OBJECT] - [VARIANT/MATERIAL] - [SPECS]

        This method now delegates to the DictionaryBasedAssembler which uses
        the Master Resource Dictionary for data-driven assembly.

        Args:
            object_name: Identified object name
            specs: Extracted and imputed specifications
            original: Original description for context

        Returns:
            Normalized string with max 2 dashes (3 components)
        """
        return self.assembler.assemble(object_name, specs, original)

    def _calculate_confidence(self, result: PriorityProcessResult) -> float:
        """
        Calculate confidence score V2.

        Distinguishes extraction quality from imputation to give
        more meaningful confidence values.

        Formula:
            base = priority_score (0.3-0.4)
            extraction_bonus = extracted_count / total_fields * 0.3
            extractor_bonus = 0.15 if specialized extractor used
            imputation_penalty = -0.05 per imputed field
            confidence = clamp(base + bonuses - penalties, 0, 1)

        Args:
            result: Current process result

        Returns:
            Confidence score (0.0 - 1.0)
        """
        breakdown = {}

        # Base score from priority level
        if result.object_name:
            priority_scores = {1: 0.4, 2: 0.35, 3: 0.3}
            base = priority_scores.get(result.priority, 0.2)
        else:
            base = 0.0
        breakdown['base'] = base

        # Extraction bonus: ratio of extracted (non-imputed) meaningful fields
        meaningful_specs = ['grade', 'dimensions', 'diameter', 'pressure',
                           'compaction', 'material', 'position', 'layer',
                           'thickness', 'mortar', 'coat', 'method',
                           'soil_class', 'distance', 'stone', 'type']
        total_fields = sum(1 for k in meaningful_specs if k in result.specs)
        imputed_count = len(result.imputed_keys)
        extracted_count = max(total_fields - imputed_count, 0)

        if total_fields > 0:
            extraction_bonus = (extracted_count / total_fields) * 0.3
        else:
            extraction_bonus = 0.0
        breakdown['extraction_bonus'] = round(extraction_bonus, 3)

        # Extractor bonus
        extractor_bonus = 0.0
        if result.extractor_used and result.extractor_used not in ('generic', None):
            extractor_bonus = 0.15
        breakdown['extractor_bonus'] = extractor_bonus

        # Imputation penalty
        imputation_penalty = imputed_count * 0.05
        breakdown['imputation_penalty'] = round(imputation_penalty, 3)

        # Final score
        score = base + extraction_bonus + extractor_bonus - imputation_penalty
        score = max(0.0, min(score, 1.0))

        breakdown['total'] = round(score, 3)
        result.confidence_breakdown = breakdown

        return round(score, 3)

    def _check_concrete_context(self, description: str) -> Optional[PriorityProcessResult]:
        """
        Check if description is a "Bê tông + vị trí" context (Bug 4 fix).

        When input like "Bê tông hố ga đá 1x2 mác 200" appears:
        - Object should be "Bê tông", NOT "Hố ga"
        - "Hố ga" becomes a position modifier
        - Output: "Bê tông - M200 - Đá 1x2"

        IMPORTANT: This check should NOT override Priority 1 objects like "Ván khuôn".
        If "Ván khuôn bê tông móng" is input, "Ván khuôn" should win (Priority 1).

        Args:
            description: Input description

        Returns:
            PriorityProcessResult if concrete context detected, None otherwise
        """
        text_norm = normalize_vietnamese(description)

        # ==========================================================================
        # Skip if "bê tông lót" is present - it's a specific object type
        # ==========================================================================
        if 'be tong lot' in text_norm:
            return None

        # ==========================================================================
        # IMPORTANT: Check if a Priority 1 keyword exists BEFORE concrete
        # If so, skip concrete context - let the normal priority system handle it
        # ==========================================================================
        from .dictionaries.priority_objects import _NORM_P1

        for keyword in _NORM_P1.keys():
            if _is_word_boundary_match(text_norm, keyword):
                keyword_pos = text_norm.find(keyword)
                concrete_pos = text_norm.find('be tong')

                # If Priority 1 keyword appears BEFORE or WITHOUT concrete, skip concrete check
                if concrete_pos == -1 or keyword_pos < concrete_pos:
                    return None

        # Check if "bê tông" is present (as main material, not modifier)
        has_concrete = 'be tong' in text_norm

        if not has_concrete:
            return None

        # Check if a position keyword follows concrete
        found_position = None
        for pos in self.CONCRETE_POSITIONS:
            pos_norm = normalize_vietnamese(pos)
            if _is_word_boundary_match(text_norm, pos_norm):
                # Make sure concrete appears BEFORE the position
                concrete_pos = text_norm.find('be tong')
                pos_pos = text_norm.find(pos_norm)

                if concrete_pos < pos_pos:
                    found_position = pos
                    break

        if not found_position:
            return None

        # This is a concrete context - process as Bê tông object
        result = PriorityProcessResult()
        result.object_name = 'Bê tông'
        result.priority = 3
        result.priority_type = 'material'
        result.extractor_used = 'concrete_context'

        # Extract specs using concrete extractor
        from .extractors.concrete_extractor import ConcreteExtractor
        concrete_ext = ConcreteExtractor()
        specs = concrete_ext.extract(description)

        # Capitalize position for display
        specs['position'] = found_position.title()

        result.specs = specs

        # Assemble output: "Bê tông - M200 - Đá 1x2"
        result.normalized = self._assemble(result.object_name, specs, description)
        result.confidence = self._calculate_confidence(result)

        return result

    def _check_cable_route_context(self, description: str) -> Optional[PriorityProcessResult]:
        """
        Check for cable route descriptions like "Cáp đến tủ DB-xxx" or "Cáp từ TX đến MSB".

        Without this check, "đến" normalizes to "den" which matches "đèn" (lamp) at P2.
        These items should be identified as "Cáp" (cable), not "Đèn" (lamp).
        """
        text_norm = normalize_vietnamese(description)

        # Pattern: starts with "cap den tu" or "cap tu ... den tu"
        cable_route_patterns = [
            'cap den tu',      # "Cáp đến tủ"
            'cap tu ',         # "Cáp từ TX đến tủ"
            'cap den tu ',     # "Cáp đến từ tủ"
        ]

        is_cable_route = any(text_norm.startswith(p) or (' ' + p) in text_norm[:30] for p in cable_route_patterns)

        if not is_cable_route:
            return None

        result = PriorityProcessResult()
        result.object_name = 'Cáp'
        result.priority = 3
        result.priority_type = 'material'

        # Extract cable specs using generic extractor
        result.specs = self._generic_extract(description)
        result.extractor_used = 'cable_route'

        # Try to extract route info from the description
        # e.g., "Cáp đến tủ DB-B-1F-TI1" → route = "DB-B-1F-TI1"
        import re
        route_match = re.search(r'(?:đến|từ)\s+(?:tủ|tu)\s+(\S+)', description, re.IGNORECASE)
        if route_match:
            result.specs['route'] = route_match.group(1)

        result.normalized = self._assemble(result.object_name, result.specs, description)
        result.confidence = self._calculate_confidence(result)

        return result

    def _check_accessory_context(self, description: str) -> Optional[PriorityProcessResult]:
        """
        Check for accessory/component patterns like "Phụ kiện ... cho ACB"
        or "Bộ cắt ... cho MCCB".

        Without this check, "ACB" or "MCCB" would match as the main object,
        but the item is actually an accessory FOR that device.
        """
        text_norm = normalize_vietnamese(description)

        # Map: (prefix_keyword, device_keyword) → object_name
        ACCESSORY_PATTERNS = {
            ('phu kien', 'acb'): 'Phụ kiện ACB',
            ('phu kien', 'mccb'): 'Phụ kiện MCCB',
            ('bo cat', 'acb'): 'Phụ kiện ACB',
            ('bo cat', 'mccb'): 'Phụ kiện MCCB',
        }

        for (prefix, device), obj_name in ACCESSORY_PATTERNS.items():
            if prefix in text_norm and device in text_norm:
                prefix_pos = text_norm.find(prefix)
                device_pos = text_norm.find(device)
                # Prefix must appear before the device keyword
                if prefix_pos < device_pos:
                    result = PriorityProcessResult()
                    result.object_name = obj_name
                    result.priority = 2
                    result.priority_type = 'component'

                    extractor = self.extractors.get(obj_name)
                    if extractor:
                        result.specs = extractor.extract(description)
                        result.extractor_used = type(extractor).__name__
                    else:
                        result.specs = self._generic_extract(description)
                        result.extractor_used = 'accessory_context'

                    result.normalized = self._assemble(obj_name, result.specs, description)
                    result.confidence = self._calculate_confidence(result)
                    return result

        return None

    def _check_installation_context(self, description: str) -> Optional[PriorityProcessResult]:
        """
        Check for installation context that should override Priority 1 methods (BUG 1 fix).

        When "lắp đặt cống" appears, the object should be "Cống", NOT "Vận chuyển".
        This prevents high-value installation work from being incorrectly classified
        as low-value transport.

        Args:
            description: Input description

        Returns:
            PriorityProcessResult if installation context detected, None otherwise
        """
        text_norm = normalize_vietnamese(description)

        # Installation verbs (already ASCII-normalized)
        INSTALLATION_VERBS = ['lap dat', 'cung cap', 'thi cong']

        # Objects that should take precedence when installation context is detected
        # NOTE: 'cong' alone is excluded because it collides with 'công' (work/construction)
        # which appears in 'thi công', 'công tác', 'công trồng', etc.
        # More specific patterns like 'cong hop', 'cong btct' handle actual culvert cases.
        INSTALLATION_OBJECTS = {
            'nap ho ga': 'Nắp hố ga',
            'cong hop': 'Cống hộp',
            'cong tron': 'Cống tròn',
            'cong btct': 'Cống thoát nước',
            'ho ga': 'Hố ga',
        }

        # Check if any installation verb is present
        found_verb = None
        for verb in INSTALLATION_VERBS:
            if verb in text_norm:
                found_verb = verb
                break
        if not found_verb:
            return None

        # ==========================================================================
        # IMPORTANT: If "bê tông" precedes the object (e.g., "bê tông đáy hố ga"),
        # this is a concrete pour, NOT an installation of the object
        # ==========================================================================
        concrete_pos = text_norm.find('be tong')

        # Check for objects (longest match first to get most specific)
        # Use word boundary matching to prevent "cong" matching inside "thi cong"
        for obj_key, obj_name in sorted(INSTALLATION_OBJECTS.items(), key=lambda x: len(x[0]), reverse=True):
            if _is_word_boundary_match(text_norm, obj_key):
                obj_pos = text_norm.find(obj_key)

                # Skip if the matched object is part of the installation verb itself
                # e.g., "thi cong" contains "cong" but that means "construction", not "culvert"
                verb_pos = text_norm.find(found_verb)
                if verb_pos != -1 and obj_pos >= verb_pos and obj_pos < verb_pos + len(found_verb) + 1:
                    continue

                # Skip if "bê tông" appears before this object - it's a concrete pour
                if concrete_pos != -1 and concrete_pos < obj_pos:
                    return None

                result = PriorityProcessResult()
                result.object_name = obj_name
                result.priority = 2
                result.priority_type = 'component'

                # Use appropriate extractor
                extractor = self.extractors.get(obj_name)
                if extractor:
                    result.specs = extractor.extract(description)
                    result.extractor_used = type(extractor).__name__
                else:
                    result.specs = self._generic_extract(description)

                # Extract material if not already present
                if 'material' not in result.specs:
                    material = self._extract_material(description)
                    if material:
                        result.specs['material'] = material

                result.normalized = self._assemble(result.object_name, result.specs, description)
                result.confidence = self._calculate_confidence(result)
                return result

        return None


# ==========================================================================
# Convenience functions
# ==========================================================================

_priority_processor = None


def get_priority_processor() -> PriorityProcessor:
    """Get or create priority processor singleton."""
    global _priority_processor
    if _priority_processor is None:
        _priority_processor = PriorityProcessor()
    return _priority_processor


def process_with_priority(description: str) -> PriorityProcessResult:
    """
    Convenience function for processing with priority model.

    Args:
        description: BOQ description

    Returns:
        PriorityProcessResult
    """
    processor = get_priority_processor()
    return processor.process(description)
