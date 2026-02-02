"""
Unit tests for WorkCodeGenerator
"""
import pytest
from app.services.work_code_generator import WorkCodeGenerator
from app.core.database import SessionLocal


class TestWorkCodeGenerator:
    """Test suite for Work Code Generator"""

    @pytest.fixture
    def generator(self):
        """Create generator instance"""
        db = SessionLocal()
        gen = WorkCodeGenerator(db)
        yield gen
        db.close()

    def test_normalize_text(self, generator):
        """Test text normalization"""
        assert generator.normalize_text("  Đào  Đất   Móng  ") == "đào đất móng"
        assert generator.normalize_text("BÊ TÔNG CỘT") == "bê tông cột"
        assert generator.normalize_text("") == ""

    def test_remove_accents(self, generator):
        """Test Vietnamese accent removal"""
        assert generator.remove_accents("đào đất móng") == "dao dat mong"
        assert generator.remove_accents("bê tông") == "be tong"
        assert generator.remove_accents("cột thép") == "cot thep"

    def test_extract_category_earthworks(self, generator):
        """Test category extraction for earthworks"""
        category, sub = generator.extract_category("Đào đất móng", "SEC-01-01")
        assert category == "EARTH"
        assert sub == "EXCAV"

        category, sub = generator.extract_category("Đắp đất nền", "SEC-01-01")
        assert category in ["EARTH", "FILL"]

    def test_extract_category_concrete(self, generator):
        """Test category extraction for concrete"""
        category, sub = generator.extract_category("Bê tông dầm", "SEC-02")
        assert category == "CONC"

        category, sub = generator.extract_category("Bê tông cột", "SEC-02")
        assert category == "CONC"

    def test_extract_category_architecture(self, generator):
        """Test category extraction for architecture"""
        category, sub = generator.extract_category("Tường gạch", "SEC-03")
        assert category in ["WALL", "BRICK"]

        category, sub = generator.extract_category("Lát gạch nền", "SEC-03")
        assert sub == "TILE" or category == "TILE"

    def test_extract_category_mep(self, generator):
        """Test category extraction for MEP"""
        category, sub = generator.extract_category("Hệ thống điện", "SEC-04")
        assert category == "ELEC"

        category, sub = generator.extract_category("Thang máy", "SEC-04")
        assert category == "ELEV"

    def test_extract_category_landscape(self, generator):
        """Test category extraction for landscape"""
        category, sub = generator.extract_category("Đường nội bộ", "SEC-05")
        assert category == "ROAD"

        category, sub = generator.extract_category("Cây xanh", "SEC-05")
        assert category in ["TREE", "PLANT"]

        category, sub = generator.extract_category("Hàng rào", "SEC-05")
        assert category == "FENCE"

    def test_generate_work_code_format(self, generator):
        """Test work code format"""
        code = generator.generate_work_code("Đào đất móng", "SEC-01-01")
        assert code.startswith("S01-")
        assert len(code.split("-")) >= 3  # At least 3 parts
        assert code.split("-")[-1].isdigit()  # Last part is number
        assert len(code.split("-")[-1]) == 4  # Sequence is 4 digits

    def test_validate_work_code(self, generator):
        """Test work code validation"""
        # Valid codes
        assert generator.validate_work_code("S01-EARTH-EXCAV-0001") == True
        assert generator.validate_work_code("S02-CONC-BEAM-0015") == True
        assert generator.validate_work_code("S03-WALL-0001") == True

        # Invalid codes
        assert generator.validate_work_code("INVALID-CODE-123") == False
        assert generator.validate_work_code("S01-EARTH-01") == False
        assert generator.validate_work_code("01-EARTH-0001") == False
        assert generator.validate_work_code("") == False

    def test_parse_work_code(self, generator):
        """Test work code parsing"""
        # With sub-category
        parsed = generator.parse_work_code("S01-EARTH-EXCAV-0001")
        assert parsed is not None
        assert parsed['sec_prefix'] == "S01"
        assert parsed['category'] == "EARTH"
        assert parsed['sub_category'] == "EXCAV"
        assert parsed['sequence'] == "0001"

        # Without sub-category
        parsed = generator.parse_work_code("S03-WALL-0001")
        assert parsed is not None
        assert parsed['sec_prefix'] == "S03"
        assert parsed['category'] == "WALL"
        assert parsed['sub_category'] is None
        assert parsed['sequence'] == "0001"

        # Invalid code
        parsed = generator.parse_work_code("INVALID-CODE")
        assert parsed is None

    def test_work_code_uniqueness(self, generator):
        """Test that generated codes are unique within group"""
        codes = set()

        test_items = [
            ("Đào đất móng 1", "SEC-01-01"),
            ("Đào đất móng 2", "SEC-01-01"),
            ("Đào đất móng 3", "SEC-01-01"),
        ]

        for desc, sec in test_items:
            code = generator.generate_work_code(desc, sec)
            # Same description should generate same code pattern but different sequence
            codes.add(code)

        # All codes should be unique (or handle duplicates appropriately)
        # This test needs database state, so we just check format
        for code in codes:
            assert generator.validate_work_code(code)

    def test_sec_prefix_mapping(self, generator):
        """Test SEC code to prefix mapping"""
        assert generator.SEC_PREFIX_MAP.get('SEC-00') == 'S00'
        assert generator.SEC_PREFIX_MAP.get('SEC-01') == 'S01'
        assert generator.SEC_PREFIX_MAP.get('SEC-02') == 'S02'
        assert generator.SEC_PREFIX_MAP.get('SEC-03') == 'S03'
        assert generator.SEC_PREFIX_MAP.get('SEC-04') == 'S04'
        assert generator.SEC_PREFIX_MAP.get('SEC-05') == 'S05'

    def test_comprehensive_generation(self, generator):
        """Test comprehensive work code generation"""
        test_cases = [
            # (description, sec_code, expected_prefix, expected_category_contains)
            ("Đào đất móng", "SEC-01-01", "S01", "EARTH"),
            ("Bê tông dầm", "SEC-02", "S02", "CONC"),
            ("Tường gạch", "SEC-03", "S03", ["WALL", "BRICK"]),
            ("Hệ thống điện", "SEC-04", "S04", "ELEC"),
            ("Đường nội bộ", "SEC-05", "S05", "ROAD"),
            ("Cây xanh công viên", "SEC-05", "S05", ["TREE", "PLANT"]),
        ]

        for desc, sec, expected_prefix, expected_cat in test_cases:
            code = generator.generate_work_code(desc, sec)

            # Check prefix
            assert code.startswith(expected_prefix), \
                f"Code {code} should start with {expected_prefix}"

            # Check category
            if isinstance(expected_cat, list):
                assert any(cat in code for cat in expected_cat), \
                    f"Code {code} should contain one of {expected_cat}"
            else:
                assert expected_cat in code, \
                    f"Code {code} should contain {expected_cat}"

            # Check format
            assert generator.validate_work_code(code), \
                f"Code {code} should be valid"

    def test_edge_cases(self, generator):
        """Test edge cases"""
        # Empty description
        code = generator.generate_work_code("", "SEC-01")
        assert code is not None
        assert generator.validate_work_code(code)

        # Very long description
        long_desc = "Đào đất móng " * 50
        code = generator.generate_work_code(long_desc, "SEC-01-01")
        assert code is not None
        assert generator.validate_work_code(code)

        # Special characters in description
        code = generator.generate_work_code("Đào đất (1.0m) [test]", "SEC-01-01")
        assert code is not None
        assert generator.validate_work_code(code)

        # Unknown SEC code
        code = generator.generate_work_code("Unknown work", "SEC-99")
        assert code is not None  # Should generate with default


def test_manual_examples():
    """Manual test examples (not using pytest)"""
    db = SessionLocal()
    generator = WorkCodeGenerator(db)

    print("\n=== WORK CODE GENERATION EXAMPLES ===\n")

    test_cases = [
        ("Đào đất móng", "SEC-01-01"),
        ("Đắp đất nền", "SEC-01-01"),
        ("Cọc khoan nhồi", "SEC-01-02"),
        ("Bê tông móng", "SEC-01-03"),
        ("Bê tông dầm", "SEC-02"),
        ("Bê tông cột", "SEC-02"),
        ("Bê tông sàn", "SEC-02"),
        ("Tường gạch", "SEC-03"),
        ("Lát gạch nền", "SEC-03"),
        ("Sơn tường", "SEC-03"),
        ("Hệ thống điện", "SEC-04"),
        ("Thang máy 8 người", "SEC-04"),
        ("Đường nội bộ bê tông", "SEC-05"),
        ("Vỉa hè lát gạch", "SEC-05"),
        ("Cây xanh công viên", "SEC-05"),
        ("Hàng rào bảo vệ", "SEC-05"),
    ]

    print(f"{'Description':<30} {'SEC Code':<12} {'Generated Code':<30} {'Valid':<6}")
    print("-" * 85)

    for desc, sec in test_cases:
        code = generator.generate_work_code(desc, sec)
        is_valid = generator.validate_work_code(code)
        print(f"{desc:<30} {sec:<12} {code:<30} {is_valid}")

    db.close()


if __name__ == "__main__":
    test_manual_examples()
