"""
Data loader for externalized JSON configuration files.

Provides a dual-source pattern: loads from JSON files if available,
falls back to hardcoded Python dicts if JSON files are missing or corrupted.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache

_DATA_DIR = Path(__file__).parent / 'data'


class DataLoadError(Exception):
    """Raised when JSON data cannot be loaded."""
    pass


@lru_cache(maxsize=1)
def load_priority_dictionaries() -> Dict[str, Any]:
    """
    Load priority dictionaries from JSON.

    Returns:
        Dict with keys: priority_1_methods, priority_2_components,
        priority_3_materials, exclusion_patterns
    """
    path = _DATA_DIR / 'priority_dictionaries.json'
    return _load_json(path)


@lru_cache(maxsize=1)
def load_master_resource() -> Dict[str, Any]:
    """
    Load master resource dictionary from JSON.

    Returns:
        Dict mapping object_name to config dict.
    """
    path = _DATA_DIR / 'master_resource.json'
    return _load_json(path)


@lru_cache(maxsize=1)
def load_imputation_defaults() -> Dict[str, Dict[str, str]]:
    """
    Load imputation defaults from JSON.

    Returns:
        Dict mapping object_name to {spec_key: default_value}.
    """
    path = _DATA_DIR / 'imputation_defaults.json'
    return _load_json(path)


def _load_json(path: Path) -> Dict:
    """Load and parse a JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_data_source(data_type: str) -> str:
    """
    Check which data source is active for a given data type.

    Args:
        data_type: 'priority', 'master_resource', or 'imputation'

    Returns:
        'json' if JSON file exists and is loadable, 'hardcoded' otherwise.
    """
    loaders = {
        'priority': load_priority_dictionaries,
        'master_resource': load_master_resource,
        'imputation': load_imputation_defaults,
    }
    loader = loaders.get(data_type)
    if not loader:
        return 'unknown'
    try:
        loader()
        return 'json'
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return 'hardcoded'
