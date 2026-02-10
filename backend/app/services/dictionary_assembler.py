"""
Dictionary-based assembler for 3-part output format.

This class replaces the 68 if-else blocks in PriorityProcessor._assemble()
with a data-driven approach using the Master Resource Dictionary.
"""
import logging
from typing import Dict, List, Optional
from .dictionaries.master_resource import MASTER_RESOURCE_DICTIONARY, get_config
from .dictionaries.field_mappings import ObjectConfig, FieldMapping
from .dictionaries.transforms import TRANSFORMS

logger = logging.getLogger(__name__)


class DictionaryBasedAssembler:
    """
    Assembles 3-part normalized output using dictionary configuration.

    Format: [PART1] - [PART2] - [PART3]

    Example outputs:
        MCCB - 3P - 400A 36kA
        Móng đường - CPĐD - Lớp dưới K98
        Ván khuôn - Móng - Theo thiết kế
    """

    def __init__(self, dictionary: Dict[str, ObjectConfig] = None):
        """
        Initialize with dictionary.

        Args:
            dictionary: Object configurations. Defaults to MASTER_RESOURCE_DICTIONARY.
        """
        self.dictionary = dictionary or MASTER_RESOURCE_DICTIONARY
        self.transforms = TRANSFORMS

        # Validate configs at init time to catch errors early
        from .dictionaries.master_resource import validate_configs
        validate_configs()

    def assemble(self, object_name: str, specs: Dict, original: str = '') -> str:
        """
        Assemble 3-part normalized output.

        Args:
            object_name: Identified object name (e.g., "MCCB", "Móng đường")
            specs: Extracted specifications dict
            original: Original description text for context

        Returns:
            Normalized 3-part string: "[PART1] - [PART2] - [PART3]"
        """
        config = get_config(object_name)

        if not config:
            # No config found - use generic assembly
            return self._generic_assemble(object_name, specs)

        # Resolve each part using the configuration
        part1 = self._resolve(config.part1, object_name, specs, original)
        part2 = self._resolve(config.part2, object_name, specs, original)
        part3 = self._resolve(config.part3, object_name, specs, original)

        return self._enforce_three_components([part1, part2, part3])

    def _resolve(self, mapping: FieldMapping, object_name: str, specs: Dict, original: str) -> str:
        """
        Resolve a field mapping to its value.

        Args:
            mapping: FieldMapping configuration
            object_name: Object name
            specs: Extracted specs
            original: Original text

        Returns:
            Resolved value string
        """
        if mapping.source == "object_name":
            return object_name

        elif mapping.source == "fixed":
            # Empty string is valid (for 2-part outputs), only use fallback if key is None
            if mapping.key is not None:
                return mapping.key
            return mapping.fallback if mapping.fallback is not None else ""

        elif mapping.source == "spec":
            value = specs.get(mapping.key) if mapping.key else None
            return value if value else mapping.fallback

        elif mapping.source == "computed":
            if mapping.transform and mapping.transform in self.transforms:
                func = self.transforms[mapping.transform]
                try:
                    result = func(specs, original)
                    return result if result else mapping.fallback
                except Exception:
                    logger.warning(
                        "Transform '%s' failed for object '%s'",
                        mapping.transform, object_name,
                        exc_info=True,
                    )
                    return mapping.fallback
            return mapping.fallback

        elif mapping.source == "default":
            return mapping.fallback

        # Fallback for unknown source
        return mapping.fallback

    def _generic_assemble(self, object_name: str, specs: Dict) -> str:
        """
        Generic assembly when no specific configuration exists.

        Uses a pattern of:
        [OBJECT] - [MATERIAL/TYPE] - [SPECS]

        Args:
            object_name: Object name
            specs: Extracted specs

        Returns:
            3-part normalized string
        """
        parts = [object_name]

        # Middle part: material, type, position, or layer
        middle_keys = ['material', 'type', 'position', 'layer', 'variant', 'purpose']
        middle_parts = []
        for key in middle_keys:
            if key in specs and specs[key]:
                value = specs[key]
                if value.lower() != object_name.lower():
                    middle_parts.append(value)
        if middle_parts:
            parts.append(' '.join(middle_parts[:2]))

        # Spec part: grade, diameter, dimensions, etc.
        spec_keys = [
            'grade', 'diameter', 'dimensions', 'asphalt_grade',
            'compaction', 'thickness', 'pressure', 'distance',
            'method', 'stone', 'mortar', 'coat', 'soil_class',
            'scope', 'spec'
        ]
        spec_parts = []
        for key in spec_keys:
            if key in specs and specs[key]:
                spec_parts.append(specs[key])
        if spec_parts:
            parts.append(' '.join(spec_parts[:3]))

        return self._enforce_three_components(parts)

    def _enforce_three_components(self, parts: List[str]) -> str:
        """
        Enforce exactly 3 components (max 2 dashes) with defaults.
        If part3 is empty, output only 2 components.

        Args:
            parts: List of parts to join

        Returns:
            String with exactly 2 dashes (3 components) or 1 dash (2 components)
        """
        # Filter out None values but keep empty strings to detect intentionally empty parts
        filtered_parts = []
        for p in parts:
            if p is None:
                continue
            # Empty string means intentionally no part
            if p == "":
                filtered_parts.append(None)  # Mark as intentionally empty
            else:
                filtered_parts.append(p)

        # Now filter out the None markers
        active_parts = [p for p in filtered_parts if p is not None]

        if len(active_parts) == 0:
            return ""
        elif len(active_parts) == 1:
            return f"{active_parts[0]} - Theo thiết kế - Theo thiết kế"
        elif len(active_parts) == 2:
            # Check if this is intentionally 2-part (part3 was empty string)
            if len(filtered_parts) == 3 and filtered_parts[2] is None:
                return f"{active_parts[0]} - {active_parts[1]}"
            return f"{active_parts[0]} - {active_parts[1]} - Theo thiết kế"
        elif len(active_parts) == 3:
            return f"{active_parts[0]} - {active_parts[1]} - {active_parts[2]}"
        else:
            # Merge middle parts if more than 3
            middle = ' '.join(active_parts[1:-1])
            return f"{active_parts[0]} - {middle} - {active_parts[-1]}"


# Singleton instance
_assembler = None


def get_assembler() -> DictionaryBasedAssembler:
    """Get or create the dictionary-based assembler singleton."""
    global _assembler
    if _assembler is None:
        _assembler = DictionaryBasedAssembler()
    return _assembler


def assemble_with_dictionary(object_name: str, specs: Dict, original: str = '') -> str:
    """
    Convenience function for dictionary-based assembly.

    Args:
        object_name: Identified object name
        specs: Extracted specifications
        original: Original description

    Returns:
        Normalized 3-part string
    """
    return get_assembler().assemble(object_name, specs, original)
