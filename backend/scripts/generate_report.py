"""
Script to generate detailed normalization report from real BOQ file.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from app.services.priority_processor import PriorityProcessor

def load_boq_xd(filepath: str) -> list:
    """Load BoQ XD sheet and extract descriptions."""
    df = pd.read_excel(filepath, sheet_name='BoQ XD', header=4)
    descriptions = []
    if 'Nội dung công việc' in df.columns:
        col = 'Nội dung công việc'
    else:
        col = df.columns[1]
    for idx, row in df.iterrows():
        val = row[col]
        if pd.notna(val) and isinstance(val, str) and val.strip():
            if len(val) > 5 and not val.isupper():
                descriptions.append(val.strip())
    return descriptions

def load_boq_me(filepath: str) -> list:
    """Load BoQ M&E sheet and extract descriptions."""
    df_raw = pd.read_excel(filepath, sheet_name='BoQ M&E', header=None)
    header_row = 0
    for i in range(min(10, len(df_raw))):
        row_vals = df_raw.iloc[i].astype(str).tolist()
        if any('Nội dung' in str(v) for v in row_vals):
            header_row = i
            break
    df = pd.read_excel(filepath, sheet_name='BoQ M&E', header=header_row)
    descriptions = []
    desc_col = None
    for col in df.columns:
        if 'Nội dung' in str(col) or 'Mô tả' in str(col):
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

def main():
    boq_file = "/home/datnm/Downloads/BOQ moi thau Gói Thi công đường và hạ tầng kỹ thuật phân khu 1 - DA Hoang Long.xlsx"

    print("Loading BOQ file...")
    xd_descriptions = load_boq_xd(boq_file)
    me_descriptions = load_boq_me(boq_file)
    all_descriptions = list(set(xd_descriptions + me_descriptions))

    print(f"Total unique descriptions: {len(all_descriptions)}")

    processor = PriorityProcessor()

    # Generate detailed output
    results = []
    for desc in all_descriptions:
        result = processor.process(desc)
        results.append({
            'input': desc,
            'object_name': result.object_name,
            'priority': result.priority,
            'normalized': result.normalized,
            'confidence': result.confidence,
            'specs': str(result.specs),
        })

    # Save to Excel
    df = pd.DataFrame(results)
    output_file = "/tmp/normalization_results.xlsx"
    df.to_excel(output_file, index=False)
    print(f"\nDetailed results saved to: {output_file}")

    # Summary stats
    total = len(results)
    identified = sum(1 for r in results if r['object_name'])
    high_conf = sum(1 for r in results if r['confidence'] >= 0.7)

    print(f"\n=== SUMMARY ===")
    print(f"Total items: {total}")
    print(f"Object identified: {identified} ({100*identified/total:.1f}%)")
    print(f"High confidence (>=0.7): {high_conf} ({100*high_conf/total:.1f}%)")

    # Count by priority
    p1 = sum(1 for r in results if r['priority'] == 1)
    p2 = sum(1 for r in results if r['priority'] == 2)
    p3 = sum(1 for r in results if r['priority'] == 3)
    print(f"\nPriority breakdown:")
    print(f"  P1 (Methods): {p1}")
    print(f"  P2 (Components): {p2}")
    print(f"  P3 (Materials): {p3}")

    # Sample outputs
    print(f"\n=== SAMPLE CORRECT OUTPUTS ===")
    for i, r in enumerate(results[:20]):
        if r['object_name']:
            print(f"{i+1}. {r['input'][:60]}...")
            print(f"   → {r['normalized']}")
            print()

if __name__ == '__main__':
    main()
