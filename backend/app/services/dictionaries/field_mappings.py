"""
Field mappings and configuration classes for the Master Resource Dictionary.

This module provides schema classes that define how to assemble
the 3-part normalized output for each object type.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class FieldMapping:
    """
    Defines how to obtain a value for one part of the output.

    Sources:
        - "object_name": Use the object name directly
        - "fixed": Use a fixed value (from 'key' field)
        - "spec": Get value from specs dict (using 'key')
        - "computed": Use a transform function
        - "default": Use fallback value
    """
    source: str = "default"      # object_name, fixed, spec, computed, default
    key: Optional[str] = None    # Key in specs dict or fixed value
    fallback: str = "Theo thiết kế"
    transform: Optional[str] = None  # Name of transform function
    combine: List[str] = field(default_factory=list)  # Keys to combine
    separator: str = " "


@dataclass
class ObjectConfig:
    """
    Configuration for how to process and assemble output for an object type.

    The 3-part output format is:
        [PART1] - [PART2] - [PART3]

    Example:
        MCCB - 3P - 400A 36kA
        Móng đường - CPĐD - Lớp dưới K98
    """
    object_name: str
    extractor: Optional[str] = None
    output_object: Optional[str] = None  # Transform object name (e.g., "Tủ điện")
    part1: FieldMapping = field(default_factory=lambda: FieldMapping(source="object_name"))
    part2: FieldMapping = field(default_factory=FieldMapping)
    part3: FieldMapping = field(default_factory=FieldMapping)
    aliases: List[str] = field(default_factory=list)
    defaults: Dict[str, str] = field(default_factory=dict)
