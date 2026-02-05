"""
Unified Normalization Result for all normalizers.

Provides a common data structure for normalization results from:
- DescriptionNormalizer (general construction work)
- MEPEquipmentNormalizer (pipes, cables, electrical)
- TrafficEquipmentNormalizer (signs, markers, road equipment)

This enables the NormalizationOrchestrator to delegate to specialized
normalizers while returning a unified result type.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List


class NormalizerType(Enum):
    """Type of normalizer used for the result"""
    DESCRIPTION = "description"     # General DescriptionNormalizer
    MEP = "mep"                     # MEPEquipmentNormalizer
    TRAFFIC = "traffic"             # TrafficEquipmentNormalizer
    AI = "ai"                       # AI-enhanced normalization (future)
    HYBRID = "hybrid"               # Combined result from multiple normalizers


class WorkCategory(Enum):
    """Work category classification"""
    EARTHWORKS_PILING = "earthworks_piling"      # Earthworks & Piling
    CONCRETE_REBAR = "concrete_rebar"            # Concrete & Rebar
    FINISHING = "finishing"                      # Finishing
    STEEL_MEP = "steel_mep"                      # Steel structure & MEP
    ROAD_INFRASTRUCTURE = "road_infrastructure"  # Road infrastructure
    LANDSCAPING = "landscaping"                  # Landscaping
    GENERAL = "general"                          # General/unclassified


@dataclass
class NormalizationResult:
    """
    Unified result from any normalizer.

    Attributes:
        original: Original input description
        normalized: Normalized description text
        work_category: Classified work category
        equipment_type: Specific equipment type (for MEP/Traffic)
        confidence: Confidence score (0-100)
        normalizer_used: Which normalizer produced this result
        is_hybrid: True if result combines multiple normalizers
        specs: Extracted technical specifications (diameter, pressure, etc.)
        components: Parsed components (verb, material, position)
        ai_enhanced: Whether AI was used to enhance the result
        is_material_only: True if description is material without work verb
        location: Separated location/zone info (e.g., "tầng 1", "phòng khách")
    """
    original: str
    normalized: str
    work_category: WorkCategory = WorkCategory.GENERAL
    equipment_type: Optional[str] = None
    confidence: float = 0.0
    normalizer_used: NormalizerType = NormalizerType.DESCRIPTION
    is_hybrid: bool = False
    specs: Dict[str, Any] = field(default_factory=dict)
    components: Dict[str, Any] = field(default_factory=dict)
    ai_enhanced: bool = False
    is_material_only: bool = False
    location: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'original': self.original,
            'normalized': self.normalized,
            'work_category': self.work_category.value,
            'equipment_type': self.equipment_type,
            'confidence': self.confidence,
            'normalizer_used': self.normalizer_used.value,
            'is_hybrid': self.is_hybrid,
            'specs': self.specs,
            'components': self.components,
            'ai_enhanced': self.ai_enhanced,
            'is_material_only': self.is_material_only,
            'location': self.location,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NormalizationResult':
        """Create from dictionary"""
        return cls(
            original=data.get('original', ''),
            normalized=data.get('normalized', ''),
            work_category=WorkCategory(data.get('work_category', 'general')),
            equipment_type=data.get('equipment_type'),
            confidence=data.get('confidence', 0.0),
            normalizer_used=NormalizerType(data.get('normalizer_used', 'description')),
            is_hybrid=data.get('is_hybrid', False),
            specs=data.get('specs', {}),
            components=data.get('components', {}),
            ai_enhanced=data.get('ai_enhanced', False),
            is_material_only=data.get('is_material_only', False),
            location=data.get('location'),
        )


@dataclass
class HybridAnalysis:
    """
    Analysis result for hybrid detection.

    Hybrid items contain both construction work verbs AND specialized specs.
    E.g., "Excavate trench for HDPE pipe D110" has:
    - Construction verb: excavate (earthwork)
    - Specialized specs: HDPE, D110 (MEP pipe)
    """
    has_construction_verb: bool = False
    construction_verb: Optional[str] = None
    has_mep_specs: bool = False
    mep_specs: Dict[str, str] = field(default_factory=dict)
    has_traffic_specs: bool = False
    traffic_specs: Dict[str, str] = field(default_factory=dict)
    is_hybrid: bool = False
    primary_category: WorkCategory = WorkCategory.GENERAL

    @property
    def specialized_type(self) -> Optional[NormalizerType]:
        """Get the specialized normalizer type if applicable"""
        if self.has_traffic_specs:
            return NormalizerType.TRAFFIC
        elif self.has_mep_specs:
            return NormalizerType.MEP
        return None
