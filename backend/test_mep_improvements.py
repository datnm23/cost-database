"""
Quick test for MEP and Landscaping normalization improvements
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.description_normalizer import DescriptionNormalizer
from app.services.mep_equipment_normalizer import get_mep_normalizer


def test_mep_cables():
    """Test improved cable normalization"""
    print("\n" + "=" * 80)
    print("TEST MEP CABLE NORMALIZATION")
    print("=" * 80)

    normalizer = get_mep_normalizer()

    test_cases = [
        "Cáp Cu/XLPE/PVC 4X300mm2",
        "Cáp Cu/XLPE/PVC 4X240mm2",
        "Cáp Cu/XLPE/PVC 4X185mm2",
        "Cáp đồng/XLPE/DSTA 3x185mm2",
        "Dây điện 1x2.5mm2",
        "Cáp ngầm trung thế 3x50mm2",
        "Ống luồn dây D20",
        "MCCB-3P-400A-50kA",
        "MCB 1P 16A",
    ]

    for desc in test_cases:
        if normalizer.is_mep_equipment(desc):
            result = normalizer.normalize(desc)
            print(f"\nOriginal:   {desc}")
            print(f"Normalized: {result.normalized}")
            print(f"Type:       {result.equipment_type}")
            print(f"Specs:      {result.specs}")
        else:
            print(f"\n{desc} - NOT detected as MEP")


def test_landscaping():
    """Test improved landscaping normalization"""
    print("\n" + "=" * 80)
    print("TEST LANDSCAPING NORMALIZATION")
    print("=" * 80)

    normalizer = DescriptionNormalizer()

    test_cases = [
        "Cây Bàng Đài Loan, chiều cao 3~4m, đường kính gốc 8-10cm",
        "Cây cỏ lạc",
        "Trồng cây xanh H=2m",
        "Rải đất màu trồng cây dày 20cm",
        "Thảm cỏ nhung",
    ]

    for desc in test_cases:
        category = normalizer.identify_work_category(desc)
        normalized = normalizer.normalize(desc)
        print(f"\nOriginal:   {desc}")
        print(f"Category:   {category}")
        print(f"Normalized: {normalized}")


def test_bilingual():
    """Test bilingual text handling"""
    print("\n" + "=" * 80)
    print("TEST BILINGUAL TEXT HANDLING")
    print("=" * 80)

    normalizer = DescriptionNormalizer()

    test_cases = [
        "Mái nối số 1~32\n雨棚",
        "Công trình ngoài nhà\n戶外工程",
        "San lấp mặt bằng\n場地土方回填",
        "Hệ thống thoát nước mưa\n雨水排水系統",
    ]

    for desc in test_cases:
        normalized = normalizer.normalize(desc)
        print(f"\nOriginal:   {repr(desc)}")
        print(f"Normalized: {normalized}")


def test_panels():
    """Test electrical panel normalization"""
    print("\n" + "=" * 80)
    print("TEST ELECTRICAL PANEL NORMALIZATION")
    print("=" * 80)

    normalizer = get_mep_normalizer()

    test_cases = [
        "Tủ gom công tơ hạ thế 500V- Vỏ tủ điện tôn dày 2,0mm mở 2 mặt",
        "Tủ điện hạ thế công tơ TĐ-1-II-TBA 10",
        "Tủ phân phối chính 380V 3 pha",
    ]

    for desc in test_cases:
        if normalizer.is_mep_equipment(desc):
            result = normalizer.normalize(desc)
            print(f"\nOriginal:   {desc[:60]}...")
            print(f"Normalized: {result.normalized[:80]}...")
            print(f"Type:       {result.equipment_type}")
        else:
            print(f"\n{desc[:40]}... - NOT detected as MEP")


if __name__ == "__main__":
    test_mep_cables()
    test_landscaping()
    test_bilingual()
    test_panels()
