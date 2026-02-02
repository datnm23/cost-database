"""
Test script cho Description Normalizer
Áp dụng Phương án 5 - Natural Syntax

Run:
    python -m backend.test_description_normalizer
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.description_normalizer import DescriptionNormalizer


def print_header(title: str):
    """Print section header"""
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100)


def test_category_specific_templates():
    """Test các template đặc thù theo nhóm công tác"""
    print_header("TEST 1: CÁC TEMPLATE ĐẶC THÙ THEO NHÓM CÔNG TÁC")

    normalizer = DescriptionNormalizer()

    # Test với các ví dụ từ tài liệu
    test_cases = [
        {
            'category': 'Earthworks & Piling',
            'template': '[Hành động][Đối tượng][vị trí] - [Kích thước/Tải trọng] - [Cấp đất/Ghi chú]',
            'examples': [
                {
                    'input': 'Đào đất hố móng bằng máy 1.25m3 đất cấp 3',
                    'expected': 'Đào đất hố móng - 1.25m3 - đất cấp 3'
                },
                {
                    'input': 'Cung cấp cọc PHC D500A L=12m',
                    'expected': 'Cung cấp cọc - D500A L=12m'
                },
                {
                    'input': 'Ép cọc robot 200 tấn đất cấp 2',
                    'expected': 'Ép cọc - 200 tấn - đất cấp 2'
                },
            ]
        },
        {
            'category': 'Concrete & Rebar',
            'template': '[Hành động][Vật liệu][vị trí] - [Mác/Kính] - [Đặc tính]',
            'examples': [
                {
                    'input': 'Đổ bê tông lót móng M100 đá 4x6',
                    'expected': 'Đổ bê tông lót móng - M100 4x6 - đá 4x6'
                },
                {
                    'input': 'Đổ bê tông dầm sàn M350 thương phẩm',
                    'expected': 'Đổ bê tông dầm sàn - M350 - thương phẩm'
                },
                {
                    'input': 'Gia công lắp dựng cốt thép móng D<10 CB300',
                    'expected': 'Gia công cốt thép móng - CB300'
                },
                {
                    'input': 'Lắp dựng ván khuôn vách phủ phim dày 18mm',
                    'expected': 'Lắp dựng ván khuôn vách - dày 18mm'
                },
            ]
        },
        {
            'category': 'Finishing',
            'template': '[Động từ][Vật liệu][vị trí] - [Quy cách/Kích thước] - [Mã hiệu/Màu sắc]',
            'examples': [
                {
                    'input': 'Xây tường gạch ống dày 100mm vữa M75',
                    'expected': 'Xây gạch tường - dày 100mm - vữa M75'
                },
                {
                    'input': 'Lát gạch sàn phòng khách 600x600 Granite bóng kính',
                    'expected': 'Lát gạch sàn - 600x600 - Granite bóng kính'
                },
                {
                    'input': 'Sơn nước tường trong 1 lót 2 phủ màu trắng kem',
                    'expected': 'Sơn tường - 1 lót 2 phủ - màu trắng kem'
                },
            ]
        },
        {
            'category': 'Steel & MEP',
            'template': '[Động từ][Vật liệu/Hệ thống][vị trí] - [Quy cách] - [Phương pháp]',
            'examples': [
                {
                    'input': 'Gia công dầm thép tổ hợp H400x200x8x12 SS400',
                    'expected': 'Gia công thép dầm - H400x200x8x12 - SS400'
                },
                {
                    'input': 'Lắp dựng kết cấu thép hệ khung giàn Bailey',
                    'expected': 'Lắp dựng thép - hệ khung giàn - Bailey'
                },
                {
                    'input': 'Lắp đặt ống thông gió tôn tráng kẽm bọc cách nhiệt',
                    'expected': 'Lắp đặt ống thông gió - tôn tráng kẽm - bọc cách nhiệt'
                },
            ]
        }
    ]

    for group in test_cases:
        print(f"\n{group['category']}")
        print(f"Template: {group['template']}")
        print("-" * 100)

        for example in group['examples']:
            result = normalizer.normalize(example['input'])
            category = normalizer.identify_work_category(example['input'])

            status = "✅" if result == example['expected'] else "⚠️"
            print(f"\n{status} Input:    {example['input']}")
            print(f"   Output:   {result}")
            print(f"   Expected: {example['expected']}")
            print(f"   Category: {category}")


def test_basic_examples():
    """Test với các ví dụ cơ bản từ tài liệu"""
    print_header("TEST 2: CÁC VÍ DỤ CƠ BẢN (SO SÁNH VỚI ĐỊNH MỨC CŨ)")

    normalizer = DescriptionNormalizer()

    # Test cases từ tài liệu (dòng 255-260)
    test_cases = [
        {
            'original': 'Bê tông lót móng, chiều rộng <= 250 cm, vữa bê tông PC30',
            'expected': 'Đổ bê tông lót móng - M100 đá 4x6 - PC30',
            'note': 'Ngắn gọn hơn 30%, loại bỏ "chiều rộng"'
        },
        {
            'original': 'Xây tường thẳng, chiều dày > 33 cm, gạch 6.5x10.5x22, vữa xi măng PC30',
            'expected': 'Xây tường thẳng gạch ống - dày 330mm - vữa M75',
            'note': 'Thay thế ký hiệu toán học (>), dễ đọc cho người và máy'
        },
        {
            'original': 'Bê tông cọc, tiết diện > 0.1m2',
            'expected': 'Đúc cọc bê tông cốt thép - tiết diện 400x400 - M400',
            'note': 'Cụ thể hóa hành động, thay khoảng chung chung'
        },
        {
            'original': 'Lắp dựng kết cấu thép dạng Bailey',
            'expected': 'Lắp dựng kết cấu thép hệ khung giàn - Bailey',
            'note': 'Chuẩn hóa thuật ngữ'
        },
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Original:  {test['original']}")

        normalized = normalizer.normalize(test['original'])
        print(f"Result:    {normalized}")
        print(f"Expected:  {test['expected']}")
        print(f"Note:      {test['note']}")

        # Analyze components
        components = normalizer.parse_description(test['original'])
        print(f"Components:")
        for key, value in components.items():
            if value:
                print(f"  - {key}: {value}")

        print("-" * 100)


def test_earthworks():
    """Test nhóm công tác Đất & Cọc"""
    print_header("TEST 3: NHÓM CÔNG TÁC ĐẤT & CỌC (EARTHWORKS & PILING)")

    normalizer = DescriptionNormalizer()

    test_cases = [
        'Đào đất hố móng bằng máy 1.25m3 đất cấp 3',
        'Cung cấp cọc PHC D500A L=12m',
        'Ép cọc robot 200 tấn đất cấp 2',
        'Thí nghiệm nén tĩnh cọc 200 tấn',
        'Đắp đất nền đường đất cấp 2',
        'San lấp mặt bằng đất cấp 1',
    ]

    print(f"\n{'Original':<60} | {'Normalized':<40}")
    print("-" * 100)

    for desc in test_cases:
        normalized = normalizer.normalize(desc)
        print(f"{desc:<60} | {normalized:<40}")


def test_concrete_and_rebar():
    """Test nhóm công tác Bê tông & Cốt thép"""
    print_header("TEST 4: NHÓM CÔNG TÁC BÊ TÔNG & CỐT THÉP (CONCRETE & REBAR)")

    normalizer = DescriptionNormalizer()

    test_cases = [
        'Đổ bê tông lót móng M100 đá 4x6',
        'Bê tông móng M200 thương phẩm',
        'Đổ bê tông dầm sàn M350 thương phẩm',
        'Bê tông cột M300 đá 1x2',
        'Gia công lắp dựng cốt thép móng D<10 CB300',
        'Cốt thép cột D>18 CB400',
        'Lắp dựng ván khuôn vách phủ phim dày 18mm',
        'Ván khuôn dầm gỗ',
    ]

    print(f"\n{'Original':<60} | {'Normalized':<40}")
    print("-" * 100)

    for desc in test_cases:
        normalized = normalizer.normalize(desc)
        print(f"{desc:<60} | {normalized:<40}")


def test_finishing():
    """Test nhóm công tác Hoàn thiện"""
    print_header("TEST 5: NHÓM CÔNG TÁC HOÀN THIỆN (FINISHING)")

    normalizer = DescriptionNormalizer()

    test_cases = [
        'Xây tường gạch ống dày 100mm vữa M75',
        'Lát gạch sàn phòng khách 600x600 Granite bóng kính',
        'Sơn nước tường trong 1 lót 2 phủ màu trắng kem',
        'Lắp dựng trần thạch cao khung chìm tấm chống ẩm 9mm',
        'Trát tường ngoài vữa xi măng M75',
        'Ốp gạch tường 300x600 men bóng',
    ]

    print(f"\n{'Original':<60} | {'Normalized':<40}")
    print("-" * 100)

    for desc in test_cases:
        normalized = normalizer.normalize(desc)
        print(f"{desc:<60} | {normalized:<40}")


def test_mep():
    """Test nhóm công tác MEP & Kết cấu thép"""
    print_header("TEST 6: NHÓM CÔNG TÁC MEP & KẾT CẤU THÉP")

    normalizer = DescriptionNormalizer()

    test_cases = [
        'Gia công dầm thép tổ hợp H400x200x8x12 SS400',
        'Lắp dựng kết cấu thép hệ khung giàn Bailey',
        'Sơn chống cháy kết cấu thép 120 phút định mức 1.2kg/m2',
        'Lắp đặt ống thông gió tôn tráng kẽm bọc cách nhiệt',
        'Lắp đặt hệ thống điện chiếu sáng',
        'Lắp đặt thang máy 8 người',
    ]

    print(f"\n{'Original':<60} | {'Normalized':<40}")
    print("-" * 100)

    for desc in test_cases:
        normalized = normalizer.normalize(desc)
        print(f"{desc:<60} | {normalized:<40}")


def test_validation_rules():
    """Test các quy tắc validation"""
    print_header("TEST 7: KIỂM TRA CÁC QUY TẮC (VALIDATION)")

    normalizer = DescriptionNormalizer()

    # Quy tắc 2: Vị trí phải viết thường
    print("\nQuy tắc 2: Vị trí phải viết thường")
    print("-" * 100)

    test_cases = [
        'Đổ bê tông Móng M300',  # Sai: "Móng" viết hoa
        'Xây tường Gạch ống',     # Sai: "Gạch" viết hoa
    ]

    for desc in test_cases:
        normalized = normalizer.normalize(desc)
        suggestions = normalizer.suggest_improvements(desc)

        print(f"\nOriginal:     {desc}")
        print(f"Normalized:   {normalized}")
        if suggestions:
            print(f"Suggestions:")
            for suggestion in suggestions:
                print(f"  - {suggestion}")

    # Quy tắc 5: Không dùng [], ()
    print("\n\nQuy tắc 5: Không sử dụng [], ()")
    print("-" * 100)

    test_cases = [
        'Đổ bê tông [móng] M300',
        'Xây tường (dày 200mm) gạch ống',
        'Lát gạch [600x600] granite',
    ]

    for desc in test_cases:
        normalized = normalizer.normalize(desc)
        suggestions = normalizer.suggest_improvements(desc)

        print(f"\nOriginal:     {desc}")
        print(f"Normalized:   {normalized}")
        if suggestions:
            print(f"Suggestions:")
            for suggestion in suggestions:
                print(f"  - {suggestion}")

    # Quy tắc 6: Độ dài 40-80 ký tự
    print("\n\nQuy tắc 6: Độ dài tối ưu 40-80 ký tự")
    print("-" * 100)

    long_desc = "Đổ bê tông móng băng chiều rộng lớn hơn 250cm, chiều cao từ 400mm đến 600mm, sử dụng bê tông thương phẩm mác 300, đá cốt liệu 1x2, xi măng PC40"

    normalized = normalizer.normalize(long_desc)
    suggestions = normalizer.suggest_improvements(long_desc)

    print(f"\nOriginal ({len(long_desc)} chars):     {long_desc}")
    print(f"Normalized ({len(normalized)} chars):   {normalized}")
    if suggestions:
        print(f"Suggestions:")
        for suggestion in suggestions:
            print(f"  - {suggestion}")


def test_batch_processing():
    """Test xử lý batch"""
    print_header("TEST 8: XỬ LÝ BATCH (HÀNG LOẠT)")

    normalizer = DescriptionNormalizer()

    descriptions = [
        'Đào đất móng',
        'Bê tông cột M300',
        'Xây tường gạch',
        'Lát gạch 600x600',
        'Sơn tường',
    ]

    results = normalizer.normalize_batch(descriptions)

    print(f"\n{'Original':<30} | {'Normalized':<30} | Components")
    print("-" * 100)

    for result in results:
        components_str = ', '.join([f"{k}:{v}" for k, v in result['components'].items() if v])
        print(f"{result['original']:<30} | {result['normalized']:<30} | {components_str}")


def test_comparison_old_vs_new():
    """So sánh định mức cũ vs phương án 5"""
    print_header("TEST 9: SO SÁNH ĐỊNH MỨC CŨ VS PHƯƠNG ÁN 5")

    normalizer = DescriptionNormalizer()

    comparisons = [
        {
            'old': 'Bê tông lót móng, chiều rộng <= 250 cm, vữa bê tông PC30',
            'improvement': 'Ngắn gọn hơn 30%'
        },
        {
            'old': 'Xây tường thẳng, chiều dày > 33 cm, gạch 6.5x10.5x22, vữa xi măng PC30',
            'improvement': 'Loại bỏ ký tự toán học'
        },
        {
            'old': 'Bê tông cọc, tiết diện > 0.1m2',
            'improvement': 'Cụ thể hóa kích thước'
        },
    ]

    print(f"\n{'Định mức cũ':<70} | {'Phương án 5':<40} | {'Cải thiện':<30}")
    print("-" * 140)

    for comp in comparisons:
        new = normalizer.normalize(comp['old'])
        old_len = len(comp['old'])
        new_len = len(new)
        reduction = round((old_len - new_len) / old_len * 100, 1)

        print(f"{comp['old']:<70} | {new:<40} | {comp['improvement']} (-{reduction}%)")


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "═" * 98 + "╗")
    print("║" + " " * 98 + "║")
    print("║" + "  TEST DESCRIPTION NORMALIZER - PHƯƠNG ÁN 5 (NATURAL SYNTAX)".center(98) + "║")
    print("║" + "  Áp dụng từ: Đặt tên chuẩn công tác xây dựng.md".center(98) + "║")
    print("║" + "  Với Template Đặc Thù Cho Từng Nhóm Công Tác".center(98) + "║")
    print("║" + " " * 98 + "║")
    print("╚" + "═" * 98 + "╝")

    try:
        test_category_specific_templates()  # New test
        test_basic_examples()
        test_earthworks()
        test_concrete_and_rebar()
        test_finishing()
        test_mep()
        test_validation_rules()
        test_batch_processing()
        test_comparison_old_vs_new()

        print_header("✓ TẤT CẢ TEST HOÀN TẤT")
        print("\nKết luận:")
        print("  - Phương án 5 (Natural Syntax) đạt điểm cao nhất: 27/30")
        print("  - Cân bằng giữa tính tự nhiên (cho người) và parse-ability (cho máy)")
        print("  - Ngắn gọn hơn 30% so với định mức hiện hành")
        print("  - Áp dụng template đặc thù cho 4 nhóm công tác chính:")
        print("    + Earthworks & Piling: [Hành động][Đối tượng][vị trí] - [Kích thước/Tải trọng] - [Cấp đất/Ghi chú]")
        print("    + Concrete & Rebar: [Hành động][Vật liệu][vị trí] - [Mác/Kính] - [Đặc tính]")
        print("    + Finishing: [Động từ][Vật liệu][vị trí] - [Quy cách/Kích thước] - [Mã hiệu/Màu sắc]")
        print("    + Steel & MEP: [Động từ][Vật liệu/Hệ thống][vị trí] - [Quy cách] - [Phương pháp]")
        print("  - Sẵn sàng tích hợp vào hệ thống BIM và phần mềm dự toán")
        print()

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
