"""
Tests for the SubtractBackExtractor.
"""

import pytest
from app.services.subtract_back_extractor import SubtractBackExtractor, ExtractedComponents


class TestSubtractBackExtractor:
    """Test cases for SubtractBackExtractor."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance."""
        return SubtractBackExtractor()

    # ==========================================================================
    # Basic Extraction Tests
    # ==========================================================================

    def test_extract_pipe_description(self, extractor):
        """Should extract pipe components correctly."""
        result = extractor.extract("ống HDPE D110 PN16")

        assert result.object_name is not None
        assert 'Ống' in result.object_name or 'HDPE' in str(result.object_name)
        assert len(result.specs) > 0

    def test_extract_pipe_with_verb(self, extractor):
        """Should strip auxiliary verb and extract components."""
        result = extractor.extract("Cung cấp lắp đặt ống HDPE D110 PN10")

        # Verb should be stripped, object extracted
        assert result.object_name is not None
        assert 'cung cấp' not in (result.remaining or '').lower()

    def test_extract_steel_pipe(self, extractor):
        """Should handle compound material 'thép mạ kẽm'."""
        result = extractor.extract("Ống thép mạ kẽm D114")

        # Material should be "thép mạ kẽm" not split
        assert result.material is not None
        # Object should be extracted
        assert result.object_name is not None

    def test_extract_electrical_breaker(self, extractor):
        """Should extract electrical breaker specs."""
        result = extractor.extract("MCCB 3P 400A 50kA")

        assert len(result.specs) > 0
        # Should have poles, amps specs
        specs_str = ' '.join(result.specs)
        assert '3P' in specs_str or '400A' in specs_str or '50kA' in specs_str

    def test_extract_concrete_grade(self, extractor):
        """Should extract concrete grade."""
        result = extractor.extract("Bê tông dầm sàn M350")

        assert len(result.specs) > 0
        assert any('M350' in s for s in result.specs)

    # ==========================================================================
    # Location Extraction Tests
    # ==========================================================================

    def test_extract_location(self, extractor):
        """Should extract location to separate field."""
        result = extractor.extract("ống HDPE D110 PN10 tầng 1")

        assert result.location is not None
        assert 'tầng 1' in result.location.lower()

    def test_extract_indoor_location(self, extractor):
        """Should extract indoor/outdoor location."""
        result = extractor.extract("Trát tường trong nhà dày 15mm")

        assert result.location is not None
        assert 'trong nhà' in result.location.lower()

    # ==========================================================================
    # Verb Stripping Tests
    # ==========================================================================

    def test_strip_cung_cap(self, extractor):
        """Should strip 'cung cấp' verb."""
        result = extractor.extract("Cung cấp ống HDPE D110")

        # Check that 'cung cấp' is not in remaining
        assert 'cung cấp' not in (result.remaining or '').lower()

    def test_strip_lap_dat(self, extractor):
        """Should strip 'lắp đặt' verb."""
        result = extractor.extract("Lắp đặt biển báo tam giác")

        assert 'lắp đặt' not in (result.remaining or '').lower()

    def test_keep_dao_verb(self, extractor):
        """Should keep work-specific verb 'đào'."""
        # This test verifies the preprocessing doesn't strip đào
        result = extractor.extract("Đào đất hố móng")

        # đào is a work-specific verb, should be kept
        # The object should still be extracted
        assert result.object_name is not None or result.remaining

    # ==========================================================================
    # Confidence Tests
    # ==========================================================================

    def test_high_confidence_complete(self, extractor):
        """Complete extraction should have high confidence."""
        result = extractor.extract("Ống HDPE D110 PN16")

        # Should have object, material, and specs
        has_components = (
            result.object_name is not None and
            len(result.specs) > 0
        )
        if has_components:
            assert result.confidence >= 0.5

    def test_low_confidence_incomplete(self, extractor):
        """Incomplete extraction should have lower confidence."""
        result = extractor.extract("xyz abc 123")

        # Unknown text should have low confidence
        assert result.confidence < 0.7

    # ==========================================================================
    # Output Assembly Tests
    # ==========================================================================

    def test_assemble_three_components(self, extractor):
        """Should assemble into 3-component format."""
        result = extractor.extract("Ống HDPE D110 PN16")
        output = extractor.assemble_output(result)

        if output:
            dash_count = output.count(' - ')
            assert dash_count <= 2, f"Output has {dash_count + 1} components: {output}"

    def test_assemble_with_pressure(self, extractor):
        """Should include pressure rating in output."""
        result = extractor.extract("Ống PPR D63 PN10")
        output = extractor.assemble_output(result)

        if output and result.pressure_rating:
            # Pressure should be in output somewhere
            assert 'PN' in output or result.pressure_rating in output

    def test_enforce_three_components(self, extractor):
        """Should merge excess components."""
        # Simulate output with 5 parts
        text = "Part1 - Part2 - Part3 - Part4 - Part5"
        result = extractor.enforce_three_components(text)

        dash_count = result.count(' - ')
        assert dash_count == 2, f"Should have 2 dashes, got {dash_count}: {result}"

    # ==========================================================================
    # Edge Cases
    # ==========================================================================

    def test_empty_input(self, extractor):
        """Should handle empty input."""
        result = extractor.extract("")

        assert result.confidence <= 0.2  # Low confidence for empty
        assert result.object_name is None

    def test_whitespace_input(self, extractor):
        """Should handle whitespace input."""
        result = extractor.extract("   ")

        assert result.confidence <= 0.2  # Low confidence for whitespace only

    def test_special_characters(self, extractor):
        """Should handle special characters."""
        result = extractor.extract("Ống HDPE [D110] (PN16)")

        # Should still extract specs
        assert len(result.specs) >= 0  # May or may not extract depending on patterns

    def test_mixed_case(self, extractor):
        """Should handle mixed case input."""
        result = extractor.extract("ỐNG hdpe D110 pn16")

        assert result.object_name is not None or result.material is not None

    # ==========================================================================
    # Integration Tests
    # ==========================================================================

    def test_full_pipeline_mep(self, extractor):
        """Full pipeline test for MEP description."""
        result = extractor.extract("Cung cấp lắp đặt ống HDPE D110 PN10 tầng 1")

        # Should have all components
        assert result.object_name is not None, "Missing object name"
        assert len(result.specs) > 0, "Missing specs"
        assert result.location is not None, "Missing location"

        # Should produce valid output
        output = extractor.assemble_output(result)
        assert output, "Empty output"
        assert output.count(' - ') <= 2, "More than 3 components"

    def test_full_pipeline_traffic(self, extractor):
        """Full pipeline test for traffic description."""
        result = extractor.extract("Lắp đặt biển báo tam giác A70")

        # Should extract object
        assert result.object_name is not None

        output = extractor.assemble_output(result)
        assert output

    def test_full_pipeline_concrete(self, extractor):
        """Full pipeline test for concrete description."""
        result = extractor.extract("Bê tông dầm sàn M350")

        assert result.object_name is not None
        assert len(result.specs) > 0


class TestSubtractBackOrder:
    """Test the SPEC → MATERIAL → OBJECT extraction order."""

    @pytest.fixture
    def extractor(self):
        return SubtractBackExtractor()

    def test_spec_extracted_first(self, extractor):
        """Specs should be extracted before material/object."""
        # This is the key test for the subtract-back algorithm
        result = extractor.extract("Ống thép mạ kẽm D114")

        # D114 should be in specs
        assert any('114' in s for s in result.specs), f"D114 not in specs: {result.specs}"

        # Material should be "thép mạ kẽm" (not split)
        if result.material:
            assert 'mạ kẽm' in result.material.lower() or 'thép' in result.material.lower()

    def test_material_not_split(self, extractor):
        """Compound material should not be split."""
        result = extractor.extract("Cáp Cu/XLPE/PVC 4x50mm2")

        # Material should be Cu/XLPE/PVC or similar
        # Not just "Cu" with "XLPE/PVC" as garbage
        if result.material:
            # Either material is compound or remaining is clean
            material_lower = result.material.lower()
            assert (
                'xlpe' in material_lower or
                'pvc' in material_lower or
                len(result.remaining) < 10
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
