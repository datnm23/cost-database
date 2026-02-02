"""
Test normalization with real BOQ Excel file
Tests Multi-Pass AI Analysis Strategy
"""
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.description_normalizer import DescriptionNormalizer
from app.services.ai_normalizer import get_ai_normalizer
from app.services.traffic_equipment_normalizer import get_traffic_normalizer
from app.services.file_context_analyzer import get_file_context_analyzer
from app.core.config import settings


def test_traffic_equipment():
    """Test traffic equipment normalizer specifically"""
    print("\n" + "=" * 80)
    print("TESTING TRAFFIC EQUIPMENT NORMALIZER")
    print("=" * 80)

    normalizer = get_traffic_normalizer()

    test_cases = [
        "Biển báo tam giác A70cm",
        "Biển báo tròn B40",
        "Thi công lắp đặt bản quan trắc lún",
        "Lắp đặt cột đèn thép H=8m",
        "Sơn vạch kẻ đường màu trắng",
        "Lắp đặt lan can thép mạ kẽm",
        "Lắp đặt cọc tiêu",
    ]

    for desc in test_cases:
        result = normalizer.normalize(desc)
        print(f"\nOriginal:   {desc}")
        print(f"Normalized: {result.normalized}")
        print(f"Type:       {result.equipment_type}")
        print(f"Confidence: {result.confidence * 100:.1f}%")


def test_road_infrastructure_detection():
    """Test road infrastructure category detection"""
    print("\n" + "=" * 80)
    print("TESTING ROAD INFRASTRUCTURE DETECTION")
    print("=" * 80)

    normalizer = DescriptionNormalizer()

    test_cases = [
        ("Biển báo tam giác A70cm", "road_infrastructure"),
        ("Thi công lắp đặt bản quan trắc lún", "road_infrastructure"),
        ("Rải thảm mặt đường BTN C19", "road_infrastructure"),
        ("Tưới lớp thấm bám bằng nhựa pha dầu", "road_infrastructure"),
        ("Đào đất hố móng bằng máy", "earthworks_piling"),
        ("Đổ bê tông móng M300", "concrete_rebar"),
    ]

    for desc, expected in test_cases:
        category = normalizer.identify_work_category(desc)
        status = "✓" if category == expected else "✗"
        print(f"{status} '{desc[:50]}...' -> {category} (expected: {expected})")


def test_with_excel(file_path: str, sheet_name: str = None, max_rows: int = 30):
    """Test normalization with real Excel BOQ file"""

    print("=" * 120)
    print(f"TESTING WITH BOQ FILE: {os.path.basename(file_path)}")
    print(f"Provider: {settings.AI_PROVIDER}, Model: {settings.AI_MODEL}")
    print("=" * 120)

    # Read Excel file
    try:
        xl = pd.ExcelFile(file_path)
        print(f"Available sheets: {xl.sheet_names}")

        # Use specified sheet or find BOQ sheet
        if sheet_name:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        else:
            # Find sheet with BOQ data
            for name in xl.sheet_names:
                if 'boq' in name.lower() or 'tiên lượng' in name.lower():
                    sheet_name = name
                    break
            if not sheet_name:
                sheet_name = xl.sheet_names[1] if len(xl.sheet_names) > 1 else xl.sheet_names[0]
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

        print(f"\nUsing sheet: {sheet_name}")
        print(f"File loaded: {len(df)} rows, {len(df.columns)} columns")
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # Find description column - typically column B (index 1) for Vietnamese BOQ
    desc_col = 1  # Usually "Nội dung công việc" column

    # Find header row
    header_row = 0
    for i in range(min(10, len(df))):
        val = df.iloc[i, desc_col] if desc_col < len(df.columns) else None
        if pd.notna(val) and isinstance(val, str):
            val_lower = val.lower().strip()
            if 'nội dung' in val_lower or 'công việc' in val_lower or 'mô tả' in val_lower:
                header_row = i
                print(f"Found header at row {i}: '{val}'")
                break

    # Extract descriptions
    descriptions = []
    start_row = header_row + 1

    for i in range(start_row, len(df)):
        val = df.iloc[i, desc_col] if desc_col < len(df.columns) else None
        if pd.notna(val) and isinstance(val, str):
            val = val.strip()
            # Skip section headers, empty, or very short text
            if len(val) > 10:
                # Skip all-caps section headers
                if not (val.isupper() and len(val) < 50):
                    # Skip Roman numeral sections
                    if not val.startswith(('I.', 'II.', 'III.', 'IV.', 'V.', 'VI.', 'VII.', 'VIII.')):
                        descriptions.append((i, val))
                        if len(descriptions) >= max_rows:
                            break

    print(f"\nExtracted {len(descriptions)} work item descriptions for testing\n")

    # Initialize normalizers
    rule_normalizer = DescriptionNormalizer()
    traffic_normalizer = get_traffic_normalizer()

    try:
        ai_normalizer = get_ai_normalizer()
    except Exception as e:
        print(f"AI normalizer error: {e}")
        ai_normalizer = None

    # Test file context analysis
    try:
        context_analyzer = get_file_context_analyzer()
        file_context = context_analyzer.analyze(df, desc_col)
        print(f"File Context Analysis:")
        print(f"  Project Type: {file_context.project_type}")
        print(f"  Sections: {len(file_context.sections)}")
        print(f"  Common Materials: {file_context.common_materials[:5]}")
        print(f"  Common Verbs: {file_context.common_verbs[:5]}")
        print(f"  Confidence: {file_context.confidence:.2f}")
        print()
    except Exception as e:
        print(f"Context analysis error: {e}")
        file_context = None

    # Process and display results
    print("-" * 120)
    print(f"{'Row':>4} | {'Original (truncated)':<50} | {'Normalized':<55} | Cat")
    print("-" * 120)

    for row_num, desc in descriptions:
        # Check if traffic equipment first
        if traffic_normalizer.is_traffic_equipment(desc):
            result = traffic_normalizer.normalize(desc)
            normalized = result.normalized
            category = 'road_infrastructure'
        else:
            normalized = rule_normalizer.normalize(desc)
            category = rule_normalizer.identify_work_category(desc)

        # Short category names
        cat_short = {
            'earthworks_piling': 'EARTH',
            'concrete_rebar': 'CONC',
            'finishing': 'FIN',
            'steel_mep': 'MEP',
            'road_infrastructure': 'ROAD',
            'general': 'GEN'
        }.get(category, category[:5])

        # Truncate for display
        orig_display = desc[:47] + "..." if len(desc) > 50 else desc
        norm_display = normalized[:52] + "..." if len(normalized) > 55 else normalized

        print(f"{row_num:>4} | {orig_display:<50} | {norm_display:<55} | {cat_short}")

    print("-" * 120)
    print(f"\nProcessed {len(descriptions)} descriptions")

    # Show detailed examples
    print("\n" + "=" * 120)
    print("DETAILED EXAMPLES (first 10)")
    print("=" * 120)

    for row_num, desc in descriptions[:10]:
        print(f"\n--- Row {row_num} ---")
        print(f"Original:   {desc}")

        # Check traffic equipment
        if traffic_normalizer.is_traffic_equipment(desc):
            result = traffic_normalizer.normalize(desc)
            print(f"Normalized: {result.normalized}")
            print(f"Category:   road_infrastructure (traffic equipment: {result.equipment_type})")
            print(f"Confidence: {result.confidence * 100:.1f}%")
        else:
            normalized = rule_normalizer.normalize(desc)
            category = rule_normalizer.identify_work_category(desc)
            components = rule_normalizer.parse_description(desc)

            print(f"Normalized: {normalized}")
            print(f"Category:   {category}")
            print(f"Components: verb={components.get('verb')}, material={components.get('material')}, "
                  f"position={components.get('position')}, grade={components.get('grade')}")
            if components.get('specs'):
                print(f"            specs={components.get('specs')}")
            if components.get('details'):
                print(f"            details={components.get('details')}")


if __name__ == "__main__":
    # Run unit tests first
    test_traffic_equipment()
    test_road_infrastructure_detection()

    # Then test with real file if available
    file_path = "/home/datnm/Downloads/BOQ moi thau Gói Thi công đường và hạ tầng kỹ thuật phân khu 1 - DA Hoang Long.xlsx"

    if os.path.exists(file_path):
        # Test with construction (XD) sheet first
        test_with_excel(file_path, sheet_name="BoQ XD", max_rows=40)
    else:
        print(f"\nFile not found: {file_path}")
        print("Skipping Excel file test.")
