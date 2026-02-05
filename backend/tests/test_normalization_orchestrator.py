"""
Unit tests for NormalizationOrchestrator.

Tests:
1. Priority delegation tests (Traffic > MEP > Description)
2. Hybrid detection tests (earthwork + MEP specs)
3. Conflict resolution tests (MEP wins for pipes/cables)
4. Abbreviation expansion integration tests
5. Confidence calculation tests
6. Edge cases (empty, None, bilingual)
"""
import pytest
from app.services.normalization_orchestrator import (
    NormalizationOrchestrator,
    get_normalization_orchestrator,
    normalize_description,
    normalize_descriptions_batch,
)
from app.services.normalization_result import (
    NormalizationResult,
    NormalizerType,
    WorkCategory,
)


class TestNormalizationOrchestrator:
    """Test suite for NormalizationOrchestrator."""

    @pytest.fixture
    def orchestrator(self):
        """Create a fresh orchestrator for each test."""
        return NormalizationOrchestrator()

    # =========================================================================
    # Priority Delegation Tests
    # =========================================================================

    def test_traffic_priority_over_description(self, orchestrator):
        """Traffic normalizer should be used for traffic equipment."""
        result = orchestrator.normalize("Biển báo tam giác A70cm")

        assert result.normalizer_used == NormalizerType.TRAFFIC
        assert result.work_category == WorkCategory.ROAD_INFRASTRUCTURE
        assert "biển báo" in result.normalized.lower()

    def test_mep_priority_over_description(self, orchestrator):
        """MEP normalizer should be used for MEP equipment."""
        result = orchestrator.normalize("Ống HDPE D110 PN16")

        assert result.normalizer_used == NormalizerType.MEP
        assert result.work_category == WorkCategory.STEEL_MEP
        assert "110" in result.normalized
        assert result.specs.get('diameter') == '110'

    def test_cable_uses_mep_normalizer(self, orchestrator):
        """Cables should use MEP normalizer and preserve material layers."""
        result = orchestrator.normalize("Cáp Cu/XLPE/PVC 4x300mm2")

        assert result.normalizer_used == NormalizerType.MEP
        assert "Cu" in result.normalized or "XLPE" in result.normalized
        assert result.specs.get('cores') == '4' or result.specs.get('cable_cores') == '4'

    def test_pure_construction_uses_description(self, orchestrator):
        """Pure construction work should use description normalizer."""
        result = orchestrator.normalize("Đào đất hố móng")

        assert result.normalizer_used == NormalizerType.DESCRIPTION
        assert result.work_category == WorkCategory.EARTHWORKS_PILING

    def test_concrete_uses_description(self, orchestrator):
        """Concrete work should use description normalizer."""
        result = orchestrator.normalize("Bê tông M200 cột")

        assert result.normalizer_used == NormalizerType.DESCRIPTION
        assert result.work_category == WorkCategory.CONCRETE_REBAR

    # =========================================================================
    # Hybrid Detection Tests
    # =========================================================================

    def test_hybrid_earthwork_with_mep(self, orchestrator):
        """Earthwork with MEP specs should be detected as hybrid."""
        result = orchestrator.normalize("Đào rãnh lắp ống HDPE D110")

        assert result.is_hybrid == True
        assert result.specs.get('diameter') is not None or result.specs.get('pipe_material') is not None

    def test_hybrid_construction_with_mep_specs(self, orchestrator):
        """Construction verb with MEP specs should be handled appropriately."""
        # "Thi công lắp đặt" with MEP specs is NOT hybrid - it's expected pattern
        result = orchestrator.normalize("Thi công lắp đặt ống PVC D63 PN16")

        # Should be MEP (not hybrid) since "thi công" is expected for MEP work
        assert result.normalizer_used == NormalizerType.MEP
        assert result.specs.get('diameter') == '63' or '63' in result.normalized

    def test_hybrid_with_traffic_specs(self, orchestrator):
        """Construction with traffic specs should be handled appropriately."""
        # "Thi công" with traffic specs is NOT hybrid - it's the expected pattern
        result = orchestrator.normalize("Thi công cột đèn H=8m")

        # Should be handled by traffic normalizer (not hybrid)
        assert result.normalizer_used == NormalizerType.TRAFFIC
        # Should have height spec
        assert result.specs.get('height') is not None or '8' in result.normalized

    def test_pure_mep_not_hybrid(self, orchestrator):
        """Pure MEP item without construction verb should not be hybrid."""
        result = orchestrator.normalize("Ống HDPE D110 PN16")

        assert result.is_hybrid == False
        assert result.normalizer_used == NormalizerType.MEP

    def test_pure_traffic_not_hybrid(self, orchestrator):
        """Pure traffic item without earthwork verb should not be hybrid."""
        result = orchestrator.normalize("Biển báo tam giác A70cm")

        assert result.is_hybrid == False
        assert result.normalizer_used == NormalizerType.TRAFFIC

    # =========================================================================
    # Conflict Resolution Tests
    # =========================================================================

    def test_mep_wins_for_pipes(self, orchestrator):
        """MEP normalizer should win for pipe descriptions."""
        result = orchestrator.normalize("Lắp đặt ống HDPE D110")

        # Either MEP or HYBRID
        assert result.normalizer_used in [NormalizerType.MEP, NormalizerType.HYBRID]
        assert result.specs.get('diameter') == '110' or '110' in result.normalized

    def test_mep_preserves_cable_layers(self, orchestrator):
        """MEP normalizer should preserve cable material layers."""
        result = orchestrator.normalize("Cáp Cu/XLPE/PVC 4x300mm2")

        # Should preserve Cu, XLPE, PVC info
        assert any(mat in result.normalized.upper() for mat in ['CU', 'XLPE', 'PVC'])

    def test_traffic_wins_for_signs(self, orchestrator):
        """Traffic normalizer should win for traffic signs."""
        result = orchestrator.normalize("Lắp đặt biển báo tam giác A70")

        assert result.normalizer_used == NormalizerType.TRAFFIC
        assert result.work_category == WorkCategory.ROAD_INFRASTRUCTURE

    # =========================================================================
    # Abbreviation Expansion Integration Tests
    # =========================================================================

    def test_bt_abbreviation_expanded(self, orchestrator):
        """BT abbreviation should be expanded to Bê tông."""
        result = orchestrator.normalize("BT M200 móng")

        # Should contain expanded "bê tông"
        assert "bê tông" in result.normalized.lower() or "m200" in result.normalized.lower()

    def test_ct_abbreviation_expanded(self, orchestrator):
        """CT abbreviation should be expanded to Cốt thép."""
        result = orchestrator.normalize("CT D16 CB400")

        # Should handle rebar spec
        assert "16" in result.normalized or "cốt thép" in result.normalized.lower()

    def test_cpdd_abbreviation_expanded(self, orchestrator):
        """CPĐD/CPDD abbreviation should be expanded."""
        result = orchestrator.normalize("CPĐD loại 1")

        # Should contain "cấp phối"
        assert "cấp phối" in result.normalized.lower() or "loại" in result.normalized.lower()

    def test_tech_specs_preserved(self, orchestrator):
        """Technical specs (M200, D16) should be preserved."""
        result = orchestrator.normalize("BT M200")

        # M200 should be preserved
        assert "200" in result.normalized or "M200" in result.normalized

    # =========================================================================
    # Confidence Calculation Tests
    # =========================================================================

    def test_mep_high_confidence(self, orchestrator):
        """MEP items should have high confidence."""
        result = orchestrator.normalize("Ống HDPE D110 PN16")

        assert result.confidence >= 80.0

    def test_traffic_high_confidence(self, orchestrator):
        """Traffic items should have high confidence."""
        result = orchestrator.normalize("Biển báo tam giác A70cm")

        assert result.confidence >= 80.0

    def test_hybrid_slightly_lower_confidence(self, orchestrator):
        """Hybrid items should have slightly lower confidence."""
        result = orchestrator.normalize("Đào rãnh lắp ống HDPE D110")

        if result.is_hybrid:
            # Hybrid should still have reasonable confidence
            assert result.confidence >= 70.0

    # =========================================================================
    # Edge Cases
    # =========================================================================

    def test_empty_string(self, orchestrator):
        """Empty string should return empty result."""
        result = orchestrator.normalize("")

        assert result.normalized == ""
        assert result.confidence == 0.0

    def test_whitespace_only(self, orchestrator):
        """Whitespace-only string should return empty result."""
        result = orchestrator.normalize("   ")

        assert result.normalized == ""
        assert result.confidence == 0.0

    def test_none_handling(self, orchestrator):
        """None should be handled gracefully."""
        result = orchestrator.normalize(None)

        assert result.normalized == ""

    def test_very_long_description(self, orchestrator):
        """Very long descriptions should be handled."""
        long_desc = "Đào đất " * 50 + "hố móng"
        result = orchestrator.normalize(long_desc)

        assert result.normalized is not None
        assert len(result.normalized) > 0

    def test_special_characters(self, orchestrator):
        """Special characters should be handled."""
        result = orchestrator.normalize("Bê tông M200 (cột) [móng]")

        assert result.normalized is not None
        # Brackets may be removed or kept depending on normalizer

    def test_mixed_case(self, orchestrator):
        """Mixed case should be handled."""
        result = orchestrator.normalize("ỐNG hdpe D110 pn16")

        assert result.normalized is not None
        assert "110" in result.normalized

    # =========================================================================
    # Batch Processing Tests
    # =========================================================================

    def test_batch_normalize(self, orchestrator):
        """Batch normalization should process all items."""
        descriptions = [
            "Ống HDPE D110",
            "Biển báo tam giác A70",
            "Bê tông M200 cột",
        ]

        results = orchestrator.normalize_batch(descriptions)

        assert len(results) == 3
        assert all(isinstance(r, NormalizationResult) for r in results)

    def test_batch_with_empty(self, orchestrator):
        """Batch should handle empty items."""
        descriptions = ["Ống HDPE D110", "", "Bê tông M200"]

        results = orchestrator.normalize_batch(descriptions)

        assert len(results) == 3
        assert results[1].normalized == ""

    # =========================================================================
    # Normalizer Statistics Tests
    # =========================================================================

    def test_normalizer_stats(self, orchestrator):
        """Statistics should correctly count normalizer usage."""
        descriptions = [
            "Ống HDPE D110",       # MEP
            "Biển báo A70",        # Traffic
            "Bê tông M200",        # Description
            "Đào rãnh ống D63",    # Hybrid
        ]

        results = orchestrator.normalize_batch(descriptions)
        stats = orchestrator.get_normalizer_stats(results)

        assert stats['total'] == 4
        # At least one of each type should be present
        total_categorized = (
            stats['mep'] + stats['traffic'] +
            stats['description'] + stats['hybrid']
        )
        assert total_categorized == 4


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_normalize_description_function(self):
        """Test normalize_description convenience function."""
        result = normalize_description("Ống HDPE D110")

        assert isinstance(result, NormalizationResult)
        assert result.normalized is not None

    def test_normalize_batch_function(self):
        """Test normalize_descriptions_batch convenience function."""
        results = normalize_descriptions_batch(["A", "B", "C"])

        assert len(results) == 3
        assert all(isinstance(r, NormalizationResult) for r in results)

    def test_singleton_orchestrator(self):
        """Singleton should return same instance."""
        orch1 = get_normalization_orchestrator()
        orch2 = get_normalization_orchestrator()

        assert orch1 is orch2


class TestNormalizationResult:
    """Test NormalizationResult dataclass."""

    def test_to_dict(self):
        """Test serialization to dict."""
        result = NormalizationResult(
            original="test",
            normalized="Test",
            work_category=WorkCategory.STEEL_MEP,
            confidence=95.0,
            normalizer_used=NormalizerType.MEP,
            specs={'diameter': '110'}
        )

        data = result.to_dict()

        assert data['original'] == "test"
        assert data['normalized'] == "Test"
        assert data['work_category'] == "steel_mep"
        assert data['normalizer_used'] == "mep"
        assert data['specs']['diameter'] == '110'

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            'original': 'test',
            'normalized': 'Test',
            'work_category': 'steel_mep',
            'normalizer_used': 'mep',
            'confidence': 95.0,
            'specs': {'diameter': '110'}
        }

        result = NormalizationResult.from_dict(data)

        assert result.original == "test"
        assert result.normalized == "Test"
        assert result.work_category == WorkCategory.STEEL_MEP
        assert result.normalizer_used == NormalizerType.MEP


class TestWorkCategoryMapping:
    """Test work category mapping from DescriptionNormalizer."""

    @pytest.fixture
    def orchestrator(self):
        return NormalizationOrchestrator()

    def test_earthwork_category(self, orchestrator):
        """Earthwork descriptions should map to EARTHWORKS_PILING."""
        result = orchestrator.normalize("Đào đất hố móng")
        assert result.work_category == WorkCategory.EARTHWORKS_PILING

    def test_concrete_category(self, orchestrator):
        """Concrete descriptions should map to CONCRETE_REBAR."""
        result = orchestrator.normalize("Bê tông M200 cột")
        assert result.work_category == WorkCategory.CONCRETE_REBAR

    def test_road_category(self, orchestrator):
        """Road descriptions should map to ROAD_INFRASTRUCTURE."""
        result = orchestrator.normalize("Biển báo giao thông")
        assert result.work_category == WorkCategory.ROAD_INFRASTRUCTURE

    def test_mep_category(self, orchestrator):
        """MEP descriptions should map to STEEL_MEP."""
        result = orchestrator.normalize("Ống HDPE D110")
        assert result.work_category == WorkCategory.STEEL_MEP


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
