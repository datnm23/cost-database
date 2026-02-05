"""
Normalization Orchestrator - Coordinates Multiple Normalizers

Resolves normalizer conflicts and enables MEP/Traffic specialization.
Priority-based delegation with hybrid detection:

1. Traffic detection → TrafficEquipmentNormalizer
2. MEP detection → MEPEquipmentNormalizer
3. Fallback → DescriptionNormalizer

Also handles hybrid items (construction work + specialized specs):
- "Đào rãnh lắp ống HDPE D110" → HYBRID (earthwork + MEP pipe specs)
- "Thi công cột đèn H=8m" → HYBRID (construction + traffic specs)
"""
import re
import logging
from typing import List, Optional, Dict, Any, Tuple

from app.services.normalization_result import (
    NormalizationResult,
    NormalizerType,
    WorkCategory,
    HybridAnalysis
)
from app.services.description_normalizer import DescriptionNormalizer
from app.services.mep_equipment_normalizer import (
    MEPEquipmentNormalizer,
    MEPEquipmentResult,
    get_mep_normalizer
)
from app.services.traffic_equipment_normalizer import (
    TrafficEquipmentNormalizer,
    TrafficEquipmentResult,
    get_traffic_normalizer
)
from app.services.abbreviation_expander import (
    AbbreviationExpander,
    get_abbreviation_expander
)

logger = logging.getLogger(__name__)


# Construction verbs that indicate hybrid items
CONSTRUCTION_VERBS = [
    'đào', 'đắp', 'san', 'thi công', 'lắp đặt', 'rải', 'lu',
    'đóng', 'ép', 'khoan', 'đổ', 'đúc', 'xây', 'gia công',
    'lắp dựng', 'kéo', 'luồn', 'đấu nối'
]

# Earthwork verbs - indicate hybrid when combined with MEP/Traffic specs
EARTHWORK_VERBS = [
    'đào', 'đắp', 'san', 'lu', 'đầm', 'rải'
]


class NormalizationOrchestrator:
    """
    Orchestrator for coordinating multiple normalizers.

    Provides priority-based delegation and hybrid detection to ensure
    MEP and Traffic items are properly handled with specialized normalizers
    while still supporting general construction descriptions.
    """

    def __init__(self, enable_ai: bool = False):
        """
        Initialize the orchestrator.

        Args:
            enable_ai: Enable AI-enhanced normalization (future feature)
        """
        self.description_normalizer = DescriptionNormalizer()
        self.traffic_normalizer = get_traffic_normalizer()
        self.mep_normalizer = get_mep_normalizer()
        self.abbreviation_expander = get_abbreviation_expander()
        self.enable_ai = enable_ai

    def normalize(self, description: str) -> NormalizationResult:
        """
        Main normalization method with priority-based delegation.

        Priority:
        1. If traffic equipment → TrafficEquipmentNormalizer
        2. If MEP equipment → MEPEquipmentNormalizer
        3. Else → DescriptionNormalizer

        Also handles hybrid items that combine construction work with
        specialized specs (e.g., "Đào rãnh lắp ống HDPE D110").

        Args:
            description: Raw description from BOQ

        Returns:
            NormalizationResult with unified result structure
        """
        if not description or not description.strip():
            return NormalizationResult(
                original=description or '',
                normalized='',
                work_category=WorkCategory.GENERAL,
                confidence=0.0,
                normalizer_used=NormalizerType.DESCRIPTION
            )

        original = description.strip()

        # Step 1: Expand abbreviations
        expansion_result = self.abbreviation_expander.expand(original)
        expanded = expansion_result.expanded

        # Step 2: Analyze for hybrid patterns
        hybrid = self._analyze_hybrid(expanded)

        # Step 3: Normalize with priority delegation
        result = self._normalize_with_priority(expanded, original, hybrid)

        return result

    def _analyze_hybrid(self, text: str) -> HybridAnalysis:
        """
        Analyze text for hybrid patterns (construction verb + specialized specs).

        Examples:
        - "Đào rãnh lắp ống HDPE D110 PN16" → hybrid (earthwork + MEP)
        - "Thi công cột đèn H=8m" → hybrid (construction + traffic)
        - "Cáp Cu/XLPE/PVC 4x300mm2" → pure MEP (no construction verb)
        - "Lắp đặt biển báo" → pure Traffic (lắp đặt is expected for traffic)
        """
        analysis = HybridAnalysis()
        text_lower = text.lower()

        # Check for construction verbs
        for verb in CONSTRUCTION_VERBS:
            if text_lower.startswith(verb) or f' {verb} ' in text_lower:
                analysis.has_construction_verb = True
                analysis.construction_verb = verb
                break

        # Check for earthwork verbs specifically (stronger hybrid indicator)
        is_earthwork_verb = any(
            text_lower.startswith(v) or f' {v} ' in text_lower
            for v in EARTHWORK_VERBS
        )

        # Check for MEP specs
        mep_specs = self._extract_mep_specs(text)
        if mep_specs:
            analysis.has_mep_specs = True
            analysis.mep_specs = mep_specs

        # Check for traffic specs
        traffic_specs = self._extract_traffic_specs(text)
        if traffic_specs:
            analysis.has_traffic_specs = True
            analysis.traffic_specs = traffic_specs

        # Determine if hybrid
        # Note: "lắp đặt" is the expected verb for MEP/Traffic equipment,
        # so we only consider it hybrid if there's also an earthwork verb
        # or if it's combined with specs from a different domain
        if analysis.has_construction_verb:
            is_expected_verb = analysis.construction_verb in ['lắp đặt', 'cung cấp', 'thi công']

            # For traffic items, "lắp đặt" is expected, not hybrid
            if analysis.has_traffic_specs and is_expected_verb and not is_earthwork_verb:
                analysis.is_hybrid = False
                analysis.primary_category = WorkCategory.ROAD_INFRASTRUCTURE
            # For MEP items, "lắp đặt" is expected, not hybrid
            elif analysis.has_mep_specs and is_expected_verb and not is_earthwork_verb:
                analysis.is_hybrid = False
                analysis.primary_category = WorkCategory.STEEL_MEP
            # Earthwork verb + specialized specs = hybrid
            elif is_earthwork_verb and (analysis.has_mep_specs or analysis.has_traffic_specs):
                analysis.is_hybrid = True
                analysis.primary_category = WorkCategory.EARTHWORKS_PILING
            # "thi công" with specialized specs = hybrid
            elif analysis.construction_verb == 'thi công' and (analysis.has_mep_specs or analysis.has_traffic_specs):
                analysis.is_hybrid = True
                if analysis.has_traffic_specs:
                    analysis.primary_category = WorkCategory.ROAD_INFRASTRUCTURE
                elif analysis.has_mep_specs:
                    analysis.primary_category = WorkCategory.STEEL_MEP
                else:
                    analysis.primary_category = WorkCategory.GENERAL

        return analysis

    def _extract_mep_specs(self, text: str) -> Dict[str, str]:
        """Extract MEP-specific specifications from text."""
        specs = {}
        text_upper = text.upper()

        # Pipe diameter: D50, D63, D110, DN100, etc.
        pipe_match = re.search(r'\bD[N]?(\d{2,3})\b', text_upper)
        if pipe_match:
            specs['diameter'] = pipe_match.group(1)

        # Pressure rating: PN6, PN10, PN16, PN25
        pn_match = re.search(r'\bPN\s*(\d+)\b', text_upper)
        if pn_match:
            specs['pressure'] = f"PN{pn_match.group(1)}"

        # Pipe material: HDPE, PVC, PPR
        for material in ['HDPE', 'PVC', 'PPR', 'UPVC']:
            if material in text_upper:
                specs['pipe_material'] = material
                break

        # Cable specs: Cu/XLPE/PVC, 4x300mm2
        if 'XLPE' in text_upper or 'CU/' in text_upper:
            specs['cable_type'] = 'XLPE'
            # Extract cross section
            cs_match = re.search(r'(\d+)[xX](\d+)\s*(?:mm2?)?', text)
            if cs_match:
                specs['cable_cores'] = cs_match.group(1)
                specs['cable_size'] = cs_match.group(2)

        return specs

    def _extract_traffic_specs(self, text: str) -> Dict[str, str]:
        """Extract traffic-specific specifications from text."""
        specs = {}
        text_lower = text.lower()

        # Sign size: A70, R50, 70x70, etc.
        sign_match = re.search(r'\b([ABCRW])(\d+)\b', text, re.IGNORECASE)
        if sign_match:
            specs['sign_type'] = sign_match.group(1).upper()
            specs['sign_size'] = sign_match.group(2)

        # Post height: H=8m, cao 8m, H8m
        height_match = re.search(r'[Hh]=?\s*(\d+(?:\.\d+)?)\s*m\b', text)
        if height_match:
            specs['height'] = height_match.group(1)

        # Marking type
        marking_keywords = ['vạch sơn', 'sơn vạch', 'vạch kẻ']
        for kw in marking_keywords:
            if kw in text_lower:
                specs['marking'] = True
                break

        return specs

    def _normalize_with_priority(
        self,
        expanded: str,
        original: str,
        hybrid: HybridAnalysis
    ) -> NormalizationResult:
        """
        Apply normalizers with priority delegation.

        Priority:
        1. Traffic equipment (signs, markers, posts)
        2. MEP equipment (pipes, cables, electrical)
        3. General description normalizer
        """
        text_lower = expanded.lower()

        # Priority 1: Traffic equipment
        if self.traffic_normalizer.is_traffic_equipment(expanded):
            traffic_result = self.traffic_normalizer.normalize(expanded)

            if hybrid.is_hybrid:
                return self._create_hybrid_result(
                    original=original,
                    expanded=expanded,
                    specialized_result=traffic_result,
                    hybrid=hybrid,
                    normalizer_type=NormalizerType.TRAFFIC
                )

            return self._convert_traffic_result(original, traffic_result)

        # Priority 2: MEP equipment
        if self.mep_normalizer.is_mep_equipment(expanded):
            mep_result = self.mep_normalizer.normalize(expanded)

            if hybrid.is_hybrid:
                return self._create_hybrid_result(
                    original=original,
                    expanded=expanded,
                    specialized_result=mep_result,
                    hybrid=hybrid,
                    normalizer_type=NormalizerType.MEP
                )

            return self._convert_mep_result(original, mep_result)

        # Priority 3: General description normalizer
        desc_result = self.description_normalizer.normalize(expanded)
        category = self._map_work_category(
            self.description_normalizer.identify_work_category(expanded)
        )
        components = self.description_normalizer.parse_description(expanded)

        # Extract location for Standard Naming Strategy
        _, location = self.description_normalizer.extract_location(expanded)

        return NormalizationResult(
            original=original,
            normalized=desc_result,
            work_category=category,
            confidence=80.0,  # Default confidence for description normalizer
            normalizer_used=NormalizerType.DESCRIPTION,
            is_hybrid=False,
            components=components,
            specs=self._extract_specs_from_components(components),
            location=location
        )

    def _convert_mep_result(
        self,
        original: str,
        mep_result: MEPEquipmentResult
    ) -> NormalizationResult:
        """Convert MEPEquipmentResult to unified NormalizationResult."""
        return NormalizationResult(
            original=original,
            normalized=mep_result.normalized,
            work_category=WorkCategory.STEEL_MEP,
            equipment_type=mep_result.equipment_type,
            confidence=mep_result.confidence * 100,  # Convert to 0-100 scale
            normalizer_used=NormalizerType.MEP,
            is_hybrid=False,
            specs=mep_result.specs,
            is_material_only=mep_result.is_material_only
        )

    def _convert_traffic_result(
        self,
        original: str,
        traffic_result: TrafficEquipmentResult
    ) -> NormalizationResult:
        """Convert TrafficEquipmentResult to unified NormalizationResult."""
        return NormalizationResult(
            original=original,
            normalized=traffic_result.normalized,
            work_category=WorkCategory.ROAD_INFRASTRUCTURE,
            equipment_type=traffic_result.equipment_type,
            confidence=traffic_result.confidence * 100,  # Convert to 0-100 scale
            normalizer_used=NormalizerType.TRAFFIC,
            is_hybrid=False,
            specs=traffic_result.specs
        )

    def _create_hybrid_result(
        self,
        original: str,
        expanded: str,
        specialized_result,
        hybrid: HybridAnalysis,
        normalizer_type: NormalizerType
    ) -> NormalizationResult:
        """
        Create a hybrid result combining construction work with specialized specs.

        For hybrid items, we preserve the normalized description from the
        specialized normalizer but also include construction context.
        """
        # Get description normalization for construction components
        desc_normalized = self.description_normalizer.normalize(expanded)
        components = self.description_normalizer.parse_description(expanded)

        # Merge specs from specialized result
        merged_specs = {}
        if hasattr(specialized_result, 'specs'):
            merged_specs.update(specialized_result.specs)

        # Add hybrid-specific specs
        if hybrid.has_mep_specs:
            merged_specs.update(hybrid.mep_specs)
        if hybrid.has_traffic_specs:
            merged_specs.update(hybrid.traffic_specs)

        # Determine confidence (lower for hybrid due to complexity)
        base_confidence = getattr(specialized_result, 'confidence', 0.8)
        if isinstance(base_confidence, float) and base_confidence <= 1:
            base_confidence *= 100  # Convert to 0-100 scale
        hybrid_confidence = base_confidence * 0.95  # Slight penalty for hybrid

        return NormalizationResult(
            original=original,
            normalized=specialized_result.normalized,
            work_category=hybrid.primary_category,
            equipment_type=getattr(specialized_result, 'equipment_type', None),
            confidence=hybrid_confidence,
            normalizer_used=NormalizerType.HYBRID,
            is_hybrid=True,
            specs=merged_specs,
            components=components
        )

    def _map_work_category(self, category_str: str) -> WorkCategory:
        """Map DescriptionNormalizer category string to WorkCategory enum."""
        mapping = {
            'earthworks_piling': WorkCategory.EARTHWORKS_PILING,
            'concrete_rebar': WorkCategory.CONCRETE_REBAR,
            'finishing': WorkCategory.FINISHING,
            'steel_mep': WorkCategory.STEEL_MEP,
            'road_infrastructure': WorkCategory.ROAD_INFRASTRUCTURE,
            'landscaping': WorkCategory.LANDSCAPING,
            'general': WorkCategory.GENERAL,
        }
        return mapping.get(category_str, WorkCategory.GENERAL)

    def _extract_specs_from_components(self, components: Dict) -> Dict[str, Any]:
        """Extract specs from parsed components."""
        specs = {}

        if components.get('grade'):
            specs['grade'] = components['grade']

        if components.get('specs'):
            for spec in components['specs']:
                # Parse dimension specs like "D16", "600x600"
                if spec.startswith('D') and spec[1:].isdigit():
                    specs['diameter'] = spec[1:]
                elif 'x' in spec.lower():
                    specs['dimensions'] = spec
                else:
                    specs.setdefault('other', []).append(spec)

        if components.get('material_type'):
            specs['material_type'] = components['material_type']

        return specs

    def normalize_batch(self, descriptions: List[str]) -> List[NormalizationResult]:
        """
        Normalize a batch of descriptions.

        Args:
            descriptions: List of descriptions to normalize

        Returns:
            List of NormalizationResult objects
        """
        return [self.normalize(desc) for desc in descriptions]

    def get_normalizer_stats(
        self,
        results: List[NormalizationResult]
    ) -> Dict[str, int]:
        """
        Get statistics on normalizer usage from results.

        Args:
            results: List of normalization results

        Returns:
            Dict with counts by normalizer type
        """
        stats = {
            'total': len(results),
            'description': 0,
            'mep': 0,
            'traffic': 0,
            'hybrid': 0,
            'ai': 0,
        }

        for result in results:
            if result.is_hybrid:
                stats['hybrid'] += 1
            elif result.normalizer_used == NormalizerType.DESCRIPTION:
                stats['description'] += 1
            elif result.normalizer_used == NormalizerType.MEP:
                stats['mep'] += 1
            elif result.normalizer_used == NormalizerType.TRAFFIC:
                stats['traffic'] += 1
            elif result.normalizer_used == NormalizerType.AI:
                stats['ai'] += 1

        return stats


# Singleton instance
_orchestrator: Optional[NormalizationOrchestrator] = None


def get_normalization_orchestrator() -> NormalizationOrchestrator:
    """Get or create the singleton NormalizationOrchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = NormalizationOrchestrator()
    return _orchestrator


def normalize_description(description: str) -> NormalizationResult:
    """
    Convenience function to normalize a description.

    Args:
        description: Input description

    Returns:
        NormalizationResult
    """
    orchestrator = get_normalization_orchestrator()
    return orchestrator.normalize(description)


def normalize_descriptions_batch(descriptions: List[str]) -> List[NormalizationResult]:
    """
    Convenience function to normalize a batch of descriptions.

    Args:
        descriptions: List of descriptions

    Returns:
        List of NormalizationResult objects
    """
    orchestrator = get_normalization_orchestrator()
    return orchestrator.normalize_batch(descriptions)


# Test function
def test_normalization_orchestrator():
    """Test the normalization orchestrator with sample inputs."""
    orchestrator = NormalizationOrchestrator()

    test_cases = [
        # Pure MEP
        ("Cáp Cu/XLPE/PVC 4x300mm2", NormalizerType.MEP, False),
        ("Ống HDPE D110 PN16", NormalizerType.MEP, False),
        ("Ống PVC D63", NormalizerType.MEP, False),
        ("MCCB 3P 400A 50kA", NormalizerType.MEP, False),

        # Pure Traffic
        ("Biển báo tam giác A70cm", NormalizerType.TRAFFIC, False),
        ("Cọc tiêu km", NormalizerType.TRAFFIC, False),
        ("Bản quan trắc lún", NormalizerType.TRAFFIC, False),
        ("Sơn vạch đường màu trắng", NormalizerType.TRAFFIC, False),

        # Pure Construction
        ("Đào đất hố móng", NormalizerType.DESCRIPTION, False),
        ("Bê tông M200 cột", NormalizerType.DESCRIPTION, False),
        ("Xây tường gạch", NormalizerType.DESCRIPTION, False),

        # Hybrid MEP (earthwork verb + MEP specs)
        ("Đào rãnh lắp ống HDPE D110", NormalizerType.HYBRID, True),

        # These are NOT hybrid - "thi công" + MEP/Traffic is expected pattern
        ("Thi công lắp đặt ống PVC D63 PN16", NormalizerType.MEP, False),
        ("Thi công cột đèn H=8m", NormalizerType.TRAFFIC, False),
        ("Lắp đặt biển báo tam giác A70", NormalizerType.TRAFFIC, False),

        # Edge cases
        ("", NormalizerType.DESCRIPTION, False),
        ("BT M200 móng", NormalizerType.DESCRIPTION, False),  # With abbreviation
    ]

    print("=" * 80)
    print("NORMALIZATION ORCHESTRATOR TEST")
    print("=" * 80)

    passed = 0
    failed = 0

    for input_text, expected_type, expected_hybrid in test_cases:
        result = orchestrator.normalize(input_text)

        type_match = result.normalizer_used == expected_type
        hybrid_match = result.is_hybrid == expected_hybrid

        if type_match and hybrid_match:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1

        print(f"\nInput:    {input_text}")
        print(f"Normalized: {result.normalized}")
        print(f"Expected: type={expected_type.value}, hybrid={expected_hybrid}")
        print(f"Actual:   type={result.normalizer_used.value}, hybrid={result.is_hybrid}")
        print(f"Category: {result.work_category.value}")
        print(f"Specs:    {result.specs}")
        print(f"Status:   {status}")
        print("-" * 40)

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    test_normalization_orchestrator()
