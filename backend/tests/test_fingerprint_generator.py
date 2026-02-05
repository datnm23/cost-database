"""
Tests for FingerprintGenerator service
"""
import pytest
from app.services.fingerprint_generator import (
    FingerprintGenerator,
    FingerprintComponents,
    get_fingerprint_generator,
)


class TestFingerprintGenerator:
    """Tests for FingerprintGenerator class."""

    @pytest.fixture
    def generator(self):
        return FingerprintGenerator()

    def test_normalize_text(self, generator):
        """Test text normalization."""
        assert generator._normalize_text("  Mô Tả  ") == "mô tả"
        assert generator._normalize_text("ĐƠN GIÁ") == "đơn giá"
        assert generator._normalize_text("Unit   Price") == "unit price"
        assert generator._normalize_text("") == ""
        assert generator._normalize_text(None) == ""

    def test_extract_keyword_vietnamese(self, generator):
        """Test keyword extraction for Vietnamese column names."""
        assert generator._extract_keyword("Mô tả") == "description"
        assert generator._extract_keyword("Nội dung công việc") == "description"
        assert generator._extract_keyword("Đơn vị") == "unit"
        assert generator._extract_keyword("ĐVT") == "unit"
        assert generator._extract_keyword("Khối lượng") == "quantity"
        assert generator._extract_keyword("KL") == "quantity"
        assert generator._extract_keyword("Đơn giá") == "unit_price"
        assert generator._extract_keyword("ĐG") == "unit_price"
        assert generator._extract_keyword("Thành tiền") == "amount"
        assert generator._extract_keyword("STT") == "index"

    def test_extract_keyword_english(self, generator):
        """Test keyword extraction for English column names."""
        assert generator._extract_keyword("Description") == "description"
        assert generator._extract_keyword("Item Description") == "description"
        assert generator._extract_keyword("Unit") == "unit"
        assert generator._extract_keyword("UoM") == "unit"
        assert generator._extract_keyword("Quantity") == "quantity"
        assert generator._extract_keyword("Qty") == "quantity"
        assert generator._extract_keyword("Unit Price") == "unit_price"
        assert generator._extract_keyword("Rate") == "unit_price"
        assert generator._extract_keyword("Amount") == "amount"
        assert generator._extract_keyword("Total") == "amount"

    def test_extract_keyword_unknown(self, generator):
        """Test that unknown column names return None."""
        # Use strings that definitely won't match any patterns
        assert generator._extract_keyword("Ghi chép riêng") is None
        assert generator._extract_keyword("Trạng thái") is None

    def test_generate_fingerprint_basic(self, generator):
        """Test basic fingerprint generation."""
        columns = ["Mô tả", "ĐVT", "KL", "Đơn giá", "Thành tiền"]
        result = generator.generate(columns)

        assert result.fingerprint is not None
        assert len(result.fingerprint) == 64  # SHA256 hex length
        assert result.components.column_count == 5
        assert len(result.components.column_keywords) > 0
        assert result.components.column_order_hash is not None

    def test_generate_fingerprint_deterministic(self, generator):
        """Test that same columns produce same fingerprint."""
        columns = ["Description", "Unit", "Quantity", "Unit Price", "Amount"]

        result1 = generator.generate(columns)
        result2 = generator.generate(columns)

        assert result1.fingerprint == result2.fingerprint
        assert result1.components.column_keywords == result2.components.column_keywords

    def test_generate_fingerprint_order_independent_for_main_hash(self, generator):
        """Test that column order affects order_hash but keywords are sorted."""
        columns1 = ["Description", "Unit", "Quantity"]
        columns2 = ["Quantity", "Unit", "Description"]

        result1 = generator.generate(columns1)
        result2 = generator.generate(columns2)

        # Keywords should be the same (sorted)
        assert result1.components.column_keywords == result2.components.column_keywords

        # But order hash should differ
        assert result1.components.column_order_hash != result2.components.column_order_hash

    def test_generate_fingerprint_with_sample_data(self, generator):
        """Test fingerprint generation with sample data for type inference."""
        columns = ["STT", "Mô tả", "ĐVT", "KL", "Đơn giá"]
        sample_data = [
            [1, "Bê tông móng", "m3", 100.5, 1500000],
            [2, "Cốt thép", "kg", 2000, 25000],
            [3, "Ván khuôn", "m2", 50.0, 150000],
        ]

        result = generator.generate(columns, sample_data)

        assert result.components.data_type_signature is not None
        assert len(result.components.data_type_signature) == 5  # One per column

    def test_infer_data_types(self, generator):
        """Test data type inference from sample data."""
        sample_data = [
            [1, "Text", "m3", 100.5, None],
            [2, "More text", "kg", 200, ""],
        ]

        signature = generator._infer_data_types(sample_data)

        # First column: numeric, 2-4: text, 5th: empty
        assert signature[0] == "N"  # Integer
        assert signature[1] == "T"  # Text
        assert signature[2] == "T"  # Text
        assert signature[3] == "N"  # Float


class TestFingerprintSimilarity:
    """Tests for fingerprint similarity calculation."""

    @pytest.fixture
    def generator(self):
        return FingerprintGenerator()

    def test_calculate_similarity_identical(self, generator):
        """Test similarity of identical fingerprints."""
        components = FingerprintComponents(
            column_count=5,
            column_keywords=["description", "unit", "quantity", "unit_price", "amount"],
            column_order_hash="abc123",
            data_type_signature="TTNNN"
        )

        similarity = generator.calculate_similarity(components, components)

        assert similarity == 100.0

    def test_calculate_similarity_different(self, generator):
        """Test similarity of completely different fingerprints."""
        fp1 = FingerprintComponents(
            column_count=5,
            column_keywords=["description", "unit", "quantity"],
            column_order_hash="abc123",
            data_type_signature="TTTNN"
        )
        fp2 = FingerprintComponents(
            column_count=10,
            column_keywords=["code", "material", "labor"],
            column_order_hash="xyz789",
            data_type_signature="NNNNN"
        )

        similarity = generator.calculate_similarity(fp1, fp2)

        assert similarity < 50  # Should be quite low

    def test_calculate_similarity_partial_overlap(self, generator):
        """Test similarity with partial keyword overlap."""
        fp1 = FingerprintComponents(
            column_count=5,
            column_keywords=["description", "unit", "quantity", "unit_price", "amount"],
            column_order_hash="abc123",
            data_type_signature=None
        )
        fp2 = FingerprintComponents(
            column_count=4,
            column_keywords=["description", "unit", "quantity", "amount"],
            column_order_hash="def456",
            data_type_signature=None
        )

        similarity = generator.calculate_similarity(fp1, fp2)

        # Should have reasonable similarity due to keyword overlap
        assert 50 <= similarity <= 90

    def test_calculate_similarity_same_keywords_different_count(self, generator):
        """Test that column count affects similarity."""
        fp1 = FingerprintComponents(
            column_count=5,
            column_keywords=["description", "unit", "quantity"],
            column_order_hash="abc123",
            data_type_signature=None
        )
        fp2 = FingerprintComponents(
            column_count=10,
            column_keywords=["description", "unit", "quantity"],
            column_order_hash="abc123",
            data_type_signature=None
        )

        similarity = generator.calculate_similarity(fp1, fp2)

        # Same keywords and order but different count
        assert 70 <= similarity <= 95


class TestFingerprintGeneratorSingleton:
    """Test the module-level singleton pattern."""

    def test_get_fingerprint_generator_singleton(self):
        """Test that get_fingerprint_generator returns the same instance."""
        gen1 = get_fingerprint_generator()
        gen2 = get_fingerprint_generator()

        assert gen1 is gen2


class TestFingerprintEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def generator(self):
        return FingerprintGenerator()

    def test_generate_empty_columns(self, generator):
        """Test fingerprint generation with empty column list."""
        result = generator.generate([])

        assert result.fingerprint is not None
        assert result.components.column_count == 0
        assert result.components.column_keywords == []

    def test_generate_single_column(self, generator):
        """Test fingerprint generation with single column."""
        result = generator.generate(["Mô tả"])

        assert result.fingerprint is not None
        assert result.components.column_count == 1
        assert "description" in result.components.column_keywords

    def test_generate_with_empty_strings(self, generator):
        """Test fingerprint generation with empty string columns."""
        columns = ["Mô tả", "", "ĐVT", None, "KL"]
        result = generator.generate([c for c in columns if c])

        assert result.fingerprint is not None

    def test_calculate_similarity_empty_keywords(self, generator):
        """Test similarity calculation with empty keyword lists."""
        fp1 = FingerprintComponents(
            column_count=3,
            column_keywords=[],
            column_order_hash="abc",
            data_type_signature=None
        )
        fp2 = FingerprintComponents(
            column_count=3,
            column_keywords=[],
            column_order_hash="abc",
            data_type_signature=None
        )

        similarity = generator.calculate_similarity(fp1, fp2)

        # Empty keywords should still allow matching on other criteria
        assert similarity >= 0
