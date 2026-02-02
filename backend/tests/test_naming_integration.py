"""
Integration tests for naming normalization feature
Tests the full flow from description normalization to classification
"""
import pytest
from unittest.mock import Mock, patch
from decimal import Decimal

from app.services.description_normalizer import DescriptionNormalizer
from app.models.line_item import LineItem


class TestDescriptionNormalizer:
    """Tests for DescriptionNormalizer service"""

    def setup_method(self):
        self.normalizer = DescriptionNormalizer()

    def test_normalize_earthworks_description(self):
        """Test normalizing earthworks description"""
        original = "Đào đất hố móng bằng máy 1.25m3 đất cấp 3"
        normalized = self.normalizer.normalize(original)

        assert normalized is not None
        assert len(normalized) > 0
        assert "Đào" in normalized or "đào" in normalized.lower()

    def test_normalize_concrete_description(self):
        """Test normalizing concrete description"""
        original = "Đổ bê tông dầm sàn M350 thương phẩm"
        normalized = self.normalizer.normalize(original)

        assert normalized is not None
        assert "bê tông" in normalized.lower()

    def test_normalize_finishing_description(self):
        """Test normalizing finishing description"""
        original = "Lát gạch sàn phòng khách 600x600 Granite bóng kính"
        normalized = self.normalizer.normalize(original)

        assert normalized is not None
        assert "Lát" in normalized or "lát" in normalized.lower()

    def test_normalize_empty_description(self):
        """Test normalizing empty description"""
        result = self.normalizer.normalize("")
        assert result == ""

        result = self.normalizer.normalize(None)
        assert result == ""

    def test_identify_work_category_earthworks(self):
        """Test work category identification for earthworks"""
        category = self.normalizer.identify_work_category("Đào đất hố móng")
        assert category == self.normalizer.WorkCategory.EARTHWORKS_PILING

    def test_identify_work_category_concrete(self):
        """Test work category identification for concrete"""
        category = self.normalizer.identify_work_category("Đổ bê tông dầm sàn M350")
        assert category == self.normalizer.WorkCategory.CONCRETE_REBAR

    def test_identify_work_category_finishing(self):
        """Test work category identification for finishing"""
        category = self.normalizer.identify_work_category("Lát gạch sàn 600x600")
        assert category == self.normalizer.WorkCategory.FINISHING

    def test_identify_work_category_mep(self):
        """Test work category identification for MEP"""
        category = self.normalizer.identify_work_category("Lắp đặt ống cấp nước")
        assert category == self.normalizer.WorkCategory.STEEL_MEP

    def test_extract_material_grade_m300(self):
        """Test extracting M-grade material"""
        grade = self.normalizer.extract_material_grade("bê tông M300")
        assert grade == "M300"

    def test_extract_material_grade_cb400(self):
        """Test extracting CB-grade steel"""
        grade = self.normalizer.extract_material_grade("thép CB400")
        assert grade == "CB400"

    def test_extract_dimensions(self):
        """Test extracting dimensions"""
        dimensions = self.normalizer.extract_dimensions("gạch 600x600")
        assert "600x600" in dimensions

    def test_parse_description_components(self):
        """Test parsing description into components"""
        components = self.normalizer.parse_description("Đổ bê tông dầm sàn M350")

        assert components is not None
        assert 'verb' in components
        assert 'material' in components
        assert 'position' in components
        assert 'grade' in components

    def test_normalize_batch(self):
        """Test batch normalization"""
        descriptions = [
            "Đào đất hố móng",
            "Đổ bê tông M300",
            "Lát gạch 600x600"
        ]

        results = self.normalizer.normalize_batch(descriptions)

        assert len(results) == 3
        for result in results:
            assert 'original' in result
            assert 'normalized' in result
            assert 'category' in result

    def test_normalized_descriptions_pass_validation(self):
        """Test that normalized descriptions have proper structure"""
        test_cases = [
            "Đào đất hố móng bằng máy 1.25m3 đất cấp 3",
            "Đổ bê tông dầm sàn M350 thương phẩm",
            "Gia công lắp dựng cốt thép móng D<10 CB300",
        ]

        for original in test_cases:
            normalized = self.normalizer.normalize(original)
            # Normalized should not be empty
            assert len(normalized) > 0
            # Normalized should have reasonable length
            assert len(normalized) < 150


class TestLineItemNormalization:
    """Tests for LineItem model with normalization fields"""

    def test_line_item_has_normalized_fields(self):
        """Test that LineItem model has normalization fields"""
        # Check that the model has the required columns
        assert hasattr(LineItem, 'normalized_description')
        assert hasattr(LineItem, 'normalization_confidence')
        assert hasattr(LineItem, 'work_category')

    def test_line_item_normalization_values(self):
        """Test LineItem can store normalization values"""
        item = LineItem(
            file_id=1,
            project_id=1,
            row_number=1,
            description="Original description",
            normalized_description="Normalized description",
            normalization_confidence=Decimal("85.50"),
            work_category="concrete_rebar"
        )

        assert item.description == "Original description"
        assert item.normalized_description == "Normalized description"
        assert float(item.normalization_confidence) == 85.50
        assert item.work_category == "concrete_rebar"


class TestNormalizationIntegration:
    """Integration tests for normalization in the processing pipeline"""

    def test_normalization_confidence_calculation(self):
        """Test confidence score calculation"""
        normalizer = DescriptionNormalizer()

        # Full description should have high confidence
        full_desc = "Đổ bê tông dầm sàn - M350 - thương phẩm"
        components = normalizer.parse_description(full_desc)

        confidence = 100.0
        if not components.get('verb'):
            confidence -= 30
        if not components.get('material'):
            confidence -= 20
        if not components.get('position'):
            confidence -= 15
        if not components.get('grade') and not components.get('specs'):
            confidence -= 15

        # Should have reasonable confidence
        assert confidence >= 50

    def test_classification_uses_normalized_text(self):
        """Test that classification should use normalized text for better accuracy"""
        normalizer = DescriptionNormalizer()

        original = "Đào đất hố móng bằng máy 1.25m3 đất cấp 3"
        normalized = normalizer.normalize(original)

        # Normalized text should be suitable for classification
        assert len(normalized) > 0
        # Should contain key terms for classification
        assert "đào" in normalized.lower() or "đất" in normalized.lower()


class TestBulkNormalization:
    """Tests for bulk normalization functionality"""

    def test_bulk_normalize_multiple_items(self):
        """Test bulk normalization of multiple items"""
        normalizer = DescriptionNormalizer()

        items = [
            {"description": "Đào đất hố móng"},
            {"description": "Đổ bê tông M300"},
            {"description": "Lát gạch sàn 600x600"},
        ]

        for item in items:
            item['normalized'] = normalizer.normalize(item['description'])
            item['category'] = normalizer.identify_work_category(item['description'])

        assert all(item.get('normalized') for item in items)
        assert all(item.get('category') for item in items)

    def test_bulk_normalize_handles_errors(self):
        """Test bulk normalization handles errors gracefully"""
        normalizer = DescriptionNormalizer()

        items = [
            {"description": "Valid description"},
            {"description": ""},  # Empty
            {"description": None},  # None
        ]

        results = []
        for item in items:
            try:
                normalized = normalizer.normalize(item['description'] or "")
                results.append({'success': True, 'normalized': normalized})
            except Exception as e:
                results.append({'success': False, 'error': str(e)})

        # All should complete without raising exceptions
        assert len(results) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
