"""
Test BOQ Processing Service with real Excel files
Tests the new processing flow:
    Upload BOQ → Extract → Dedupe Raw → Normalize → Match → Dedupe New → Add to Master
"""
import os
import sys
import pandas as pd
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import only what we need (avoid SQLAlchemy dependency)
from app.services.description_normalizer import DescriptionNormalizer

# Thresholds (same as in boq_processing_service.py)
EXACT_MATCH_THRESHOLD = 0.95  # ≥95% → Tự động gán mã
FUZZY_MATCH_THRESHOLD = 0.80  # 80-95% → Review


def extract_descriptions_from_excel(file_path: str, sheet_name: str = None) -> List[Dict]:
    """Extract work item descriptions from Excel BOQ file"""
    print(f"\nReading: {os.path.basename(file_path)}")
    print(f"Sheet: {sheet_name or 'First sheet'}")

    try:
        if sheet_name:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        else:
            df = pd.read_excel(file_path)
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

    print(f"Total rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")

    # Find description column
    desc_col = None
    possible_names = ['Mô tả công việc', 'Description', 'Nội dung công việc',
                      'Công việc', 'Hạng mục', 'Tên công việc', 'Diễn giải']

    for col in df.columns:
        col_str = str(col).strip().lower()
        for name in possible_names:
            if name.lower() in col_str:
                desc_col = col
                break
        if desc_col:
            break

    # Fallback: find column with most text content
    if not desc_col:
        max_text_len = 0
        for col in df.columns:
            if df[col].dtype == 'object':
                avg_len = df[col].astype(str).str.len().mean()
                if avg_len > max_text_len:
                    max_text_len = avg_len
                    desc_col = col

    if not desc_col:
        print("Could not identify description column!")
        return []

    print(f"Using description column: '{desc_col}'")

    # Extract descriptions
    items = []
    for idx, row in df.iterrows():
        desc = str(row[desc_col]).strip() if pd.notna(row[desc_col]) else ''
        if desc and desc != 'nan' and len(desc) > 5:
            # Skip headers/section titles
            if not desc.startswith(('I.', 'II.', 'III.', 'IV.', 'V.', 'VI.', 'VII.', 'VIII.', 'IX.', 'X.')):
                items.append({
                    'description': desc,
                    'unit': str(row.get('Đơn vị', row.get('Unit', ''))),
                    'quantity': 0,
                    'unit_price': 0
                })

    print(f"Extracted {len(items)} work items")
    return items


def test_processing_flow(items: List[Dict], file_name: str):
    """Test the full BOQ processing flow"""
    print("\n" + "=" * 100)
    print(f"TESTING BOQ PROCESSING FLOW: {file_name}")
    print(f"Thresholds: Exact >= {EXACT_MATCH_THRESHOLD*100}%, Fuzzy >= {FUZZY_MATCH_THRESHOLD*100}%")
    print("=" * 100)

    # Create mock service (no DB connection needed for this test)
    normalizer = DescriptionNormalizer()

    # Step 1: Raw count
    total = len(items)
    print(f"\n[Step 1] Total extracted: {total}")

    # Step 2: Dedupe raw
    raw_descs = [item['description'] for item in items]
    unique_raw = list(dict.fromkeys(raw_descs))  # Preserve order, remove duplicates
    print(f"[Step 2] After raw dedupe: {len(unique_raw)} (removed {total - len(unique_raw)} exact duplicates)")

    # Step 3: Normalize all
    normalized_map = {}  # normalized -> original
    for desc in unique_raw:
        try:
            norm = normalizer.normalize(desc)
            norm_key = norm.lower().strip()
            if norm_key not in normalized_map:
                normalized_map[norm_key] = (desc, norm)
        except Exception as e:
            print(f"  Error normalizing: {desc[:50]}... - {e}")

    unique_normalized = len(normalized_map)
    print(f"[Step 3] After normalize dedupe: {unique_normalized} (removed {len(unique_raw) - unique_normalized} similar items)")

    # Show some examples of deduplication
    if len(unique_raw) - unique_normalized > 0:
        print("\n  Sample deduplication examples:")
        shown = 0
        seen_normalized = {}
        for desc in unique_raw:
            try:
                norm = normalizer.normalize(desc).lower().strip()
                if norm in seen_normalized:
                    if shown < 5:
                        print(f"    '{desc[:60]}...'")
                        print(f"    → merged with: '{seen_normalized[norm][:60]}...'")
                        print()
                        shown += 1
                else:
                    seen_normalized[norm] = desc
            except:
                pass

    # Step 4: Show normalized samples
    print("\n[Step 4] Sample normalized descriptions:")
    for i, (norm_key, (original, normalized)) in enumerate(list(normalized_map.items())[:10]):
        print(f"\n  {i+1}. Original:   {original[:80]}{'...' if len(original) > 80 else ''}")
        print(f"     Normalized: {normalized[:80]}{'...' if len(normalized) > 80 else ''}")

    # Summary
    print("\n" + "-" * 100)
    print("PROCESSING SUMMARY")
    print("-" * 100)
    print(f"  Total extracted:       {total:,}")
    print(f"  After raw dedupe:      {len(unique_raw):,} ({(len(unique_raw)/total*100):.1f}%)")
    print(f"  After normalize:       {unique_normalized:,} ({(unique_normalized/total*100):.1f}%)")
    print(f"  Reduction:             {total - unique_normalized:,} items ({((total - unique_normalized)/total*100):.1f}%)")

    return {
        'total': total,
        'unique_raw': len(unique_raw),
        'unique_normalized': unique_normalized
    }


def main():
    # File 1: Test specific sheets
    files = [
        ("/home/datnm/Downloads/BOQ moi thau Gói Thi công đường và hạ tầng kỹ thuật phân khu 1 - DA Hoang Long.xlsx", "BoQ XD"),
        ("/home/datnm/Downloads/BOQ moi thau Gói Thi công đường và hạ tầng kỹ thuật phân khu 1 - DA Hoang Long.xlsx", "BoQ M&E"),
    ]

    # File 2: Process ALL sheets
    file2 = "/home/datnm/Downloads/20250503 BOQ FULL SỬA-OP B ( ORIGINAL) R2.xlsx"
    if os.path.exists(file2):
        import pandas as pd
        xl = pd.ExcelFile(file2)
        for sheet in xl.sheet_names:
            if sheet != '總表':  # Skip summary sheet
                files.append((file2, sheet))

    all_stats = []

    for file_path, sheet_name in files:
        if not os.path.exists(file_path):
            print(f"\nFile not found: {file_path}")
            continue

        items = extract_descriptions_from_excel(file_path, sheet_name)
        if items:
            stats = test_processing_flow(items, f"{os.path.basename(file_path)} - {sheet_name or 'Sheet1'}")
            all_stats.append({
                'file': os.path.basename(file_path),
                'sheet': sheet_name or 'Sheet1',
                **stats
            })

    # Final summary
    if all_stats:
        print("\n\n" + "=" * 100)
        print("FINAL SUMMARY - ALL FILES")
        print("=" * 100)
        print(f"{'File':<50} {'Sheet':<15} {'Total':>8} {'Raw':>8} {'Norm':>8} {'Saved':>8}")
        print("-" * 100)

        total_all = 0
        saved_all = 0
        for s in all_stats:
            saved = s['total'] - s['unique_normalized']
            total_all += s['total']
            saved_all += saved
            print(f"{s['file'][:48]:<50} {s['sheet']:<15} {s['total']:>8} {s['unique_raw']:>8} {s['unique_normalized']:>8} {saved:>8}")

        print("-" * 100)
        print(f"{'TOTAL':<50} {'':<15} {total_all:>8} {'':<8} {'':<8} {saved_all:>8}")
        print(f"\nOverall reduction: {saved_all:,} items ({(saved_all/total_all*100):.1f}% saved)")


if __name__ == "__main__":
    main()
