"""
Script to test normalization pipeline on MEP BOQ file.
Processes all BOQ sheets and exports results to Excel.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from app.services.priority_processor import PriorityProcessor


BOQ_FILE = "/home/datnm/Downloads/5. BOQ mời thầu MEP (final).xlsx"
OUTPUT_FILE = "/home/datnm/Downloads/MEP_BOQ_normalization_output.xlsx"

# Sheets to process (skip TH=summary, DMVL=material list, Prelim)
BOQ_SHEETS = [
    '1.1. Cấp điện',
    '1.2. Điện nhẹ',
    '1.3. ĐHKK + Thông gió',
    '1.4. PCCC',
    '1.5. Cấp thoát nước',
    '1.6. Chống sét',
    '1.7 Hệ thống nối đất',
    '2.1. Điện Hạ tầng',
    '2.2. Điện nhẹ',
    '2.3. Cấp thoát nước',
    '3.1. Điện Phụ trợ',
    '3.2. TN Phụ trợ',
]


def load_sheet_descriptions(filepath: str, sheet_name: str) -> list[dict]:
    """Load a BOQ sheet and extract descriptions with row info."""
    df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)

    # Find header row containing "Nội dung"
    header_row = None
    desc_col = None
    for i in range(min(15, len(df))):
        for j, val in enumerate(df.iloc[i]):
            if pd.notna(val) and 'Nội dung' in str(val):
                header_row = i
                desc_col = j
                break
        if header_row is not None:
            break

    if header_row is None or desc_col is None:
        return []

    items = []
    for i in range(header_row + 2, len(df)):
        val = df.iloc[i, desc_col]
        if pd.notna(val) and isinstance(val, str) and len(val.strip()) > 3:
            text = val.strip()
            # Skip section headers (all uppercase, very short, or numbering only)
            if text.isupper() and len(text) < 50:
                continue
            if len(text) <= 5:
                continue
            items.append({
                'sheet': sheet_name,
                'row': i + 1,
                'original': text,
            })

    return items


def process_all(filepath: str) -> pd.DataFrame:
    """Process all BOQ sheets and return results DataFrame."""
    processor = PriorityProcessor()
    all_rows = []

    for sheet in BOQ_SHEETS:
        try:
            items = load_sheet_descriptions(filepath, sheet)
        except Exception as e:
            print(f"  SKIP {sheet}: {e}")
            continue

        print(f"  {sheet}: {len(items)} items")

        for item in items:
            result = processor.process(item['original'])
            parts = result.normalized.split(' - ')

            row = {
                'Sheet': item['sheet'],
                'Row': item['row'],
                'Original': item['original'],
                'Normalized': result.normalized,
                'Object': result.object_name or '',
                'Part1': parts[0] if len(parts) >= 1 else '',
                'Part2': parts[1] if len(parts) >= 2 else '',
                'Part3': parts[2] if len(parts) >= 3 else '',
                'Priority': result.priority,
                'PriorityType': result.priority_type,
                'Confidence': round(result.confidence, 2),
                'Extractor': result.extractor_used or '',
                'MatchType': result.match_type or '',
                'Secondary': result.secondary_object or '',
                'SecondaryPriority': result.secondary_priority,
            }
            all_rows.append(row)

    return pd.DataFrame(all_rows)


def print_summary(df: pd.DataFrame):
    """Print summary statistics."""
    total = len(df)
    identified = len(df[df['Object'] != ''])
    unknown = total - identified

    print(f"\n{'='*70}")
    print(f" SUMMARY: {total} items total")
    print(f"{'='*70}")
    print(f"  Identified: {identified} ({100*identified/total:.1f}%)")
    print(f"  Unknown:    {unknown} ({100*unknown/total:.1f}%)")
    print()

    print("PRIORITY BREAKDOWN:")
    for p in [1, 2, 3]:
        count = len(df[df['Priority'] == p])
        print(f"  P{p}: {count}")
    print()

    print("CONFIDENCE:")
    high = len(df[df['Confidence'] >= 0.7])
    med = len(df[(df['Confidence'] >= 0.4) & (df['Confidence'] < 0.7)])
    low = len(df[df['Confidence'] < 0.4])
    print(f"  High (>=0.7):  {high} ({100*high/total:.1f}%)")
    print(f"  Medium:        {med} ({100*med/total:.1f}%)")
    print(f"  Low (<0.4):    {low} ({100*low/total:.1f}%)")
    print()

    print("TOP OBJECTS:")
    obj_counts = df['Object'].value_counts().head(20)
    for obj, count in obj_counts.items():
        label = obj if obj else 'UNKNOWN'
        print(f"  {label}: {count}")

    print()
    print("BY SHEET:")
    for sheet in df['Sheet'].unique():
        sheet_df = df[df['Sheet'] == sheet]
        sheet_id = len(sheet_df[sheet_df['Object'] != ''])
        print(f"  {sheet}: {len(sheet_df)} items, {sheet_id} identified ({100*sheet_id/len(sheet_df):.0f}%)")


def main():
    if not os.path.exists(BOQ_FILE):
        print(f"ERROR: File not found: {BOQ_FILE}")
        return

    print(f"Processing: {BOQ_FILE}")
    print(f"Loading sheets...")

    df = process_all(BOQ_FILE)
    print_summary(df)

    # Export to Excel with formatting
    with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
        # Full results
        df.to_excel(writer, sheet_name='All Results', index=False)

        # Unknown items only
        unknown_df = df[df['Object'] == ''].copy()
        unknown_df.to_excel(writer, sheet_name='Unknown Items', index=False)

        # Summary by object
        summary = df.groupby('Object').agg(
            Count=('Object', 'size'),
            AvgConfidence=('Confidence', 'mean'),
            Sheets=('Sheet', lambda x: ', '.join(sorted(x.unique()))),
        ).sort_values('Count', ascending=False)
        summary.to_excel(writer, sheet_name='By Object')

        # Per-sheet summary
        sheet_summary = []
        for sheet in df['Sheet'].unique():
            s = df[df['Sheet'] == sheet]
            sheet_summary.append({
                'Sheet': sheet,
                'Total': len(s),
                'Identified': len(s[s['Object'] != '']),
                'Unknown': len(s[s['Object'] == '']),
                'Rate': f"{100*len(s[s['Object'] != ''])/len(s):.0f}%",
                'AvgConfidence': round(s['Confidence'].mean(), 2),
            })
        pd.DataFrame(sheet_summary).to_excel(writer, sheet_name='By Sheet', index=False)

    print(f"\nOutput exported to: {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
