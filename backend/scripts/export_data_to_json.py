"""
Export hardcoded Python dictionaries to JSON files.

Usage:
    python -m scripts.export_data_to_json

Creates:
    app/services/dictionaries/data/priority_dictionaries.json
    app/services/dictionaries/data/master_resource.json
    app/services/dictionaries/data/imputation_defaults.json
"""
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.dictionaries.priority_objects import (
    PRIORITY_1_METHODS,
    PRIORITY_2_COMPONENTS,
    PRIORITY_3_MATERIALS,
    _EXCLUSION_PATTERNS,
)
from app.services.dictionaries.master_resource import MASTER_RESOURCE_DICTIONARY
from app.services.imputation_rules import IMPUTATION_DEFAULTS

DATA_DIR = backend_dir / 'app' / 'services' / 'dictionaries' / 'data'


def export_priority_dictionaries():
    data = {
        'priority_1_methods': PRIORITY_1_METHODS,
        'priority_2_components': PRIORITY_2_COMPONENTS,
        'priority_3_materials': PRIORITY_3_MATERIALS,
        'exclusion_patterns': _EXCLUSION_PATTERNS,
    }
    path = DATA_DIR / 'priority_dictionaries.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Exported {path} ({os.path.getsize(path):,} bytes)")
    return path


def _field_mapping_to_dict(fm):
    """Convert FieldMapping to a clean dict, omitting defaults."""
    d = {}
    d['source'] = fm.source
    if fm.key is not None:
        d['key'] = fm.key
    if fm.fallback != 'Theo thiết kế':
        d['fallback'] = fm.fallback
    if fm.transform is not None:
        d['transform'] = fm.transform
    if fm.combine:
        d['combine'] = fm.combine
    if fm.separator != ' ':
        d['separator'] = fm.separator
    return d


def export_master_resource():
    data = {}
    for obj_name, config in MASTER_RESOURCE_DICTIONARY.items():
        entry = {
            'object_name': config.object_name,
        }
        if config.extractor:
            entry['extractor'] = config.extractor
        if config.output_object:
            entry['output_object'] = config.output_object
        entry['part1'] = _field_mapping_to_dict(config.part1)
        entry['part2'] = _field_mapping_to_dict(config.part2)
        entry['part3'] = _field_mapping_to_dict(config.part3)
        if config.aliases:
            entry['aliases'] = config.aliases
        if config.defaults:
            entry['defaults'] = config.defaults
        data[obj_name] = entry

    path = DATA_DIR / 'master_resource.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Exported {path} ({os.path.getsize(path):,} bytes)")
    return path


def export_imputation_defaults():
    path = DATA_DIR / 'imputation_defaults.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(IMPUTATION_DEFAULTS, f, ensure_ascii=False, indent=2)
    print(f"Exported {path} ({os.path.getsize(path):,} bytes)")
    return path


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    export_priority_dictionaries()
    export_master_resource()
    export_imputation_defaults()
    print("\nAll exports complete.")


if __name__ == '__main__':
    main()
