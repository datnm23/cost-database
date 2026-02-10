"""
Script to test normalization pipeline on real BOQ file.
Processes all items and reports accuracy metrics.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from app.services.priority_processor import PriorityProcessor, process_with_priority
from app.services.subtract_back_extractor import SubtractBackExtractor

def load_boq_xd(filepath: str) -> list:
    """Load BoQ XD sheet and extract descriptions."""
    # Header at row 4, data starts from row 8
    df = pd.read_excel(filepath, sheet_name='BoQ XD', header=4)

    descriptions = []

    # Column 1 is "Nội dung công việc"
    if 'Nội dung công việc' in df.columns:
        col = 'Nội dung công việc'
    else:
        col = df.columns[1]  # Second column

    for idx, row in df.iterrows():
        val = row[col]
        if pd.notna(val) and isinstance(val, str) and val.strip():
            # Skip section headers (e.g., "I", "I.1", "NỀN ĐƯỜNG")
            if len(val) > 5 and not val.isupper():
                descriptions.append(val.strip())

    return descriptions

def load_boq_me(filepath: str) -> list:
    """Load BoQ M&E sheet and extract descriptions."""
    # Need to find header row first
    df_raw = pd.read_excel(filepath, sheet_name='BoQ M&E', header=None)

    # Find header row (contains "Nội dung công việc" or similar)
    header_row = 0
    for i in range(min(10, len(df_raw))):
        row_vals = df_raw.iloc[i].astype(str).tolist()
        if any('Nội dung' in str(v) for v in row_vals):
            header_row = i
            break

    df = pd.read_excel(filepath, sheet_name='BoQ M&E', header=header_row)

    descriptions = []

    # Find description column
    desc_col = None
    for col in df.columns:
        if 'Nội dung' in str(col) or 'Mô tả' in str(col) or 'công việc' in str(col).lower():
            desc_col = col
            break

    if desc_col is None and len(df.columns) > 1:
        desc_col = df.columns[1]

    if desc_col:
        for val in df[desc_col]:
            if pd.notna(val) and isinstance(val, str) and val.strip():
                if len(val) > 5:
                    descriptions.append(val.strip())

    return descriptions

def test_priority_processor(descriptions: list) -> dict:
    """Test priority processor on all descriptions."""
    processor = PriorityProcessor()

    results = {
        'total': len(descriptions),
        'object_identified': 0,
        'high_confidence': 0,
        'medium_confidence': 0,
        'low_confidence': 0,
        'three_component': 0,
        'two_component': 0,
        'one_component': 0,
        'priority_1_matches': 0,
        'priority_2_matches': 0,
        'priority_3_matches': 0,
        'no_match': 0,
        'samples': [],
        'failures': [],
        'by_object': {},
    }

    for desc in descriptions:
        if not desc.strip():
            continue

        result = processor.process(desc)

        # Track by object type
        obj = result.object_name or "UNKNOWN"
        if obj not in results['by_object']:
            results['by_object'][obj] = 0
        results['by_object'][obj] += 1

        if result.object_name:
            results['object_identified'] += 1

            if result.priority == 1:
                results['priority_1_matches'] += 1
            elif result.priority == 2:
                results['priority_2_matches'] += 1
            elif result.priority == 3:
                results['priority_3_matches'] += 1
        else:
            results['no_match'] += 1
            if len(results['failures']) < 50:
                results['failures'].append({
                    'input': desc,
                    'output': result.normalized,
                })

        if result.confidence >= 0.7:
            results['high_confidence'] += 1
        elif result.confidence >= 0.4:
            results['medium_confidence'] += 1
        else:
            results['low_confidence'] += 1

        dash_count = result.normalized.count(' - ')
        if dash_count == 2:
            results['three_component'] += 1
        elif dash_count == 1:
            results['two_component'] += 1
        else:
            results['one_component'] += 1

        if len(results['samples']) < 50:
            results['samples'].append({
                'input': desc[:100],
                'output': result.normalized,
                'object': result.object_name,
                'priority': result.priority,
                'confidence': result.confidence,
            })

    return results

def test_subtract_back(descriptions: list) -> dict:
    """Test subtract-back extractor on all descriptions."""
    extractor = SubtractBackExtractor()

    results = {
        'total': len(descriptions),
        'object_found': 0,
        'material_found': 0,
        'specs_found': 0,
        'location_found': 0,
        'high_confidence': 0,
        'samples': [],
    }

    for desc in descriptions:
        if not desc.strip():
            continue

        components = extractor.extract(desc)

        if components.object_name:
            results['object_found'] += 1
        if components.material:
            results['material_found'] += 1
        if components.specs:
            results['specs_found'] += 1
        if components.location:
            results['location_found'] += 1
        if components.confidence >= 0.7:
            results['high_confidence'] += 1

        if len(results['samples']) < 30:
            results['samples'].append({
                'input': desc[:80],
                'object': components.object_name,
                'material': components.material,
                'specs': components.specs[:3] if components.specs else [],
                'output': extractor.assemble_output(components),
                'confidence': components.confidence,
            })

    return results

def print_results(title: str, results: dict):
    """Print formatted results."""
    print(f"\n{'='*70}")
    print(f" {title}")
    print('='*70)

    total = results['total']
    if total == 0:
        print("No items to process")
        return

    print(f"Total items: {total}")
    print()

    if 'object_identified' in results:
        print("OBJECT IDENTIFICATION:")
        print(f"  Object identified: {results['object_identified']} ({100*results['object_identified']/total:.1f}%)")
        print(f"  No match: {results['no_match']} ({100*results['no_match']/total:.1f}%)")
        print()
        print("PRIORITY BREAKDOWN:")
        print(f"  Priority 1 (Methods): {results['priority_1_matches']}")
        print(f"  Priority 2 (Components): {results['priority_2_matches']}")
        print(f"  Priority 3 (Materials): {results['priority_3_matches']}")
        print()
        print("CONFIDENCE LEVELS:")
        print(f"  High (>=0.7): {results['high_confidence']} ({100*results['high_confidence']/total:.1f}%)")
        print(f"  Medium (0.4-0.7): {results['medium_confidence']} ({100*results['medium_confidence']/total:.1f}%)")
        print(f"  Low (<0.4): {results['low_confidence']} ({100*results['low_confidence']/total:.1f}%)")
        print()
        print("COMPONENT STRUCTURE:")
        print(f"  3-component: {results['three_component']} ({100*results['three_component']/total:.1f}%)")
        print(f"  2-component: {results['two_component']} ({100*results['two_component']/total:.1f}%)")
        print(f"  1-component: {results['one_component']} ({100*results['one_component']/total:.1f}%)")
        print()

        # Top object types
        print("TOP OBJECT TYPES:")
        sorted_objects = sorted(results['by_object'].items(), key=lambda x: x[1], reverse=True)
        for obj, count in sorted_objects[:15]:
            print(f"  {obj}: {count}")
    else:
        print("EXTRACTION RATES:")
        print(f"  Object found: {results['object_found']} ({100*results['object_found']/total:.1f}%)")
        print(f"  Material found: {results['material_found']} ({100*results['material_found']/total:.1f}%)")
        print(f"  Specs found: {results['specs_found']} ({100*results['specs_found']/total:.1f}%)")
        print(f"  Location found: {results['location_found']} ({100*results['location_found']/total:.1f}%)")
        print(f"  High confidence: {results['high_confidence']} ({100*results['high_confidence']/total:.1f}%)")

def print_samples(results: dict, count: int = 30):
    """Print sample outputs."""
    print(f"\n{'='*70}")
    print(" SAMPLE OUTPUTS")
    print('='*70)

    for i, sample in enumerate(results['samples'][:count]):
        print(f"\n{i+1}. INPUT: {sample['input']}")
        print(f"   OUTPUT: {sample.get('output', 'N/A')}")
        if 'object' in sample:
            print(f"   Object: {sample['object']}, Priority: {sample.get('priority')}, Conf: {sample.get('confidence', 0):.2f}")

def print_failures(results: dict, count: int = 30):
    """Print failure analysis."""
    failures = results.get('failures', [])
    if not failures:
        return

    print(f"\n{'='*70}")
    print(f" FAILURES (Items with no object identified) - Showing {min(count, len(failures))}/{len(failures)}")
    print('='*70)

    for i, failure in enumerate(failures[:count]):
        print(f"\n{i+1}. {failure['input']}")

def main():
    boq_file = "/home/datnm/Downloads/BOQ moi thau Gói Thi công đường và hạ tầng kỹ thuật phân khu 1 - DA Hoang Long.xlsx"

    if not os.path.exists(boq_file):
        print(f"ERROR: File not found: {boq_file}")
        return

    print(f"Loading BOQ file: {boq_file}")

    # Load BoQ XD
    print("\nLoading BoQ XD sheet...")
    xd_descriptions = load_boq_xd(boq_file)
    print(f"  Extracted {len(xd_descriptions)} descriptions")

    # Load BoQ M&E
    print("\nLoading BoQ M&E sheet...")
    me_descriptions = load_boq_me(boq_file)
    print(f"  Extracted {len(me_descriptions)} descriptions")

    # Combine and deduplicate
    all_descriptions = list(set(xd_descriptions + me_descriptions))
    print(f"\nTotal unique descriptions: {len(all_descriptions)}")

    # Test Priority Processor
    print("\n" + "="*70)
    print(" TESTING PRIORITY PROCESSOR")
    print("="*70)
    priority_results = test_priority_processor(all_descriptions)
    print_results("PRIORITY PROCESSOR RESULTS", priority_results)
    print_samples(priority_results, 40)
    print_failures(priority_results, 30)

    # Test Subtract-Back Extractor
    print("\n" + "="*70)
    print(" TESTING SUBTRACT-BACK EXTRACTOR")
    print("="*70)
    subtract_results = test_subtract_back(all_descriptions)
    print_results("SUBTRACT-BACK EXTRACTOR RESULTS", subtract_results)

if __name__ == '__main__':
    main()
