"""
Dictionaries module for BOQ description normalization.

This module provides standardized dictionaries for:
- Objects (DICT_OBJECTS): Construction object names
- Materials (DICT_MATERIALS): Material types and variants
- Specs (SPEC_PATTERNS): Technical specification patterns
- Priority Objects (Priority 1-2-3): Priority-based object identification
- Master Resource (MASTER_RESOURCE_DICTIONARY): Data-driven assembly configuration
- Field Mappings (ObjectConfig, FieldMapping): Schema classes for configuration
- Transforms (TRANSFORMS): Transform functions registry
"""

from .objects import DICT_OBJECTS, DICT_OBJECTS_SORTED
from .materials import DICT_MATERIALS, DICT_PRESSURE
from .specs import SPEC_PATTERNS, extract_specs
from .priority_objects import (
    PRIORITY_1_METHODS,
    PRIORITY_2_COMPONENTS,
    PRIORITY_3_MATERIALS,
    ALL_PRIORITY_OBJECTS,
    ALL_PRIORITY_OBJECTS_SORTED,
    identify_object,
    identify_object_with_details,
)
from .field_mappings import ObjectConfig, FieldMapping
from .master_resource import MASTER_RESOURCE_DICTIONARY, get_config
from .transforms import TRANSFORMS

__all__ = [
    'DICT_OBJECTS',
    'DICT_OBJECTS_SORTED',
    'DICT_MATERIALS',
    'DICT_PRESSURE',
    'SPEC_PATTERNS',
    'extract_specs',
    # Priority objects
    'PRIORITY_1_METHODS',
    'PRIORITY_2_COMPONENTS',
    'PRIORITY_3_MATERIALS',
    'ALL_PRIORITY_OBJECTS',
    'ALL_PRIORITY_OBJECTS_SORTED',
    'identify_object',
    'identify_object_with_details',
    # Master resource dictionary
    'ObjectConfig',
    'FieldMapping',
    'MASTER_RESOURCE_DICTIONARY',
    'get_config',
    'TRANSFORMS',
]
