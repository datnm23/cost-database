"""
Unit tests for AbbreviationExpander service.

Tests cover:
1. Basic expansion tests
2. Technical spec preservation tests
3. Priority/ordering tests (BT vs BTCT vs BTN)
4. Case preservation tests
5. Word boundary tests
6. Edge cases (empty, None, whitespace)
7. Real-world BOQ examples
8. Batch processing tests
9. Custom abbreviation management
"""
import pytest
from app.services.abbreviation_expander import (
    AbbreviationExpander,
    ExpansionResult,
    expand_abbreviations,
    expand_abbreviations_detailed,
    get_abbreviation_expander,
    DEFAULT_ABBREVIATIONS,
)


class TestBasicExpansion:
    """Basic abbreviation expansion tests."""

    @pytest.fixture
    def expander(self):
        return AbbreviationExpander()

    def test_simple_concrete_expansion(self, expander):
        """Test basic BT -> Bê tông expansion."""
        result = expander.expand("BT M200")
        assert result.expanded == "Bê tông M200"
        assert len(result.expansions_applied) == 1

    def test_reinforced_concrete_expansion(self, expander):
        """Test BTCT -> Bê tông cốt thép expansion."""
        result = expander.expand("BTCT móng")
        assert result.expanded == "Bê tông cốt thép móng"

    def test_formwork_expansion(self, expander):
        """Test VK -> Ván khuôn expansion."""
        result = expander.expand("VK gỗ")
        assert result.expanded == "Ván khuôn gỗ"

    def test_rebar_expansion(self, expander):
        """Test CT -> Cốt thép expansion."""
        result = expander.expand("CT D16")
        assert result.expanded == "Cốt thép D16"

    def test_asphalt_concrete_expansion(self, expander):
        """Test BTN -> Bê tông nhựa expansion."""
        result = expander.expand("BTN C12.5")
        assert result.expanded == "Bê tông nhựa C12.5"

    def test_aggregate_expansion(self, expander):
        """Test CPĐD -> Cấp phối đá dăm expansion."""
        result = expander.expand("CPĐD loại 1")
        assert result.expanded == "Cấp phối đá dăm loại 1"

    def test_aggregate_without_diacritic(self, expander):
        """Test CPDD (without diacritic) expansion."""
        result = expander.expand("CPDD loại 2")
        assert result.expanded == "Cấp phối đá dăm loại 2"

    def test_geotextile_expansion(self, expander):
        """Test VĐKT -> Vải địa kỹ thuật expansion."""
        result = expander.expand("VĐKT")
        assert result.expanded == "Vải địa kỹ thuật"

    def test_fire_protection_expansion(self, expander):
        """Test PCCC -> Phòng cháy chữa cháy expansion."""
        result = expander.expand("PCCC tầng 1")
        assert result.expanded == "Phòng cháy chữa cháy tầng 1"

    def test_hvac_expansion(self, expander):
        """Test ĐHKK -> Điều hòa không khí expansion."""
        result = expander.expand("ĐHKK phòng họp")
        assert result.expanded == "Điều hòa không khí phòng họp"

    def test_construction_verb_expansion(self, expander):
        """Test TC -> Thi công expansion."""
        result = expander.expand("TC móng")
        assert result.expanded == "Thi công móng"

    def test_installation_expansion(self, expander):
        """Test LĐ -> Lắp đặt expansion."""
        result = expander.expand("LĐ thiết bị")
        assert result.expanded == "Lắp đặt thiết bị"

    def test_fabrication_expansion(self, expander):
        """Test GC -> Gia công expansion."""
        result = expander.expand("GC cốt thép")
        assert result.expanded == "Gia công cốt thép"

    def test_pile_expansion(self, expander):
        """Test CBTCT -> Cọc bê tông cốt thép expansion."""
        result = expander.expand("CBTCT D400")
        assert "Cọc bê tông cốt thép" in result.expanded

    def test_cement_expansion(self, expander):
        """Test XM -> Xi măng expansion."""
        result = expander.expand("Vữa XM")
        assert result.expanded == "Vữa Xi măng"


class TestTechSpecPreservation:
    """Test that technical specifications are NOT expanded."""

    @pytest.fixture
    def expander(self):
        return AbbreviationExpander()

    def test_preserve_concrete_grade_m200(self, expander):
        """M200 should not be modified."""
        result = expander.expand("BT M200")
        assert "M200" in result.expanded
        assert "M200" in result.tech_specs_preserved

    def test_preserve_concrete_grade_m350(self, expander):
        """M350 should not be modified."""
        result = expander.expand("BTCT M350")
        assert "M350" in result.expanded

    def test_preserve_rebar_diameter_d16(self, expander):
        """D16 should not be modified."""
        result = expander.expand("CT D16")
        assert "D16" in result.expanded

    def test_preserve_pipe_diameter_d110(self, expander):
        """D110 should not be modified."""
        result = expander.expand("Ống PVC D110")
        assert "D110" in result.expanded

    def test_preserve_compaction_k95(self, expander):
        """K95 should not be modified."""
        result = expander.expand("Đầm nền K95")
        assert "K95" in result.expanded

    def test_preserve_compaction_k98(self, expander):
        """K98 should not be modified."""
        result = expander.expand("Lu lèn K98")
        assert "K98" in result.expanded

    def test_preserve_pressure_pn16(self, expander):
        """PN16 should not be modified."""
        result = expander.expand("Ống HDPE PN16")
        assert "PN16" in result.expanded

    def test_preserve_steel_grade_cb400(self, expander):
        """CB400 should not be modified."""
        result = expander.expand("CT D16 CB400")
        assert "CB400" in result.expanded

    def test_preserve_steel_grade_ss400(self, expander):
        """SS400 should not be modified."""
        result = expander.expand("Thép hình SS400")
        assert "SS400" in result.expanded

    def test_preserve_dimensions_600x600(self, expander):
        """Tile dimensions 600x600 should not be modified."""
        result = expander.expand("Gạch lát 600x600")
        assert "600x600" in result.expanded

    def test_preserve_h_section(self, expander):
        """H-section H400x200x8x12 should not be modified."""
        result = expander.expand("Dầm thép H400x200x8x12")
        assert "H400x200x8x12" in result.expanded

    def test_preserve_pc_cement(self, expander):
        """PC30, PC40 cement grades should not be modified."""
        result = expander.expand("Vữa PC40")
        assert "PC40" in result.expanded


class TestPriorityOrdering:
    """Test that longer abbreviations are matched before shorter ones."""

    @pytest.fixture
    def expander(self):
        return AbbreviationExpander()

    def test_btct_before_bt(self, expander):
        """BTCT should be matched, not BT + CT separately."""
        result = expander.expand("BTCT móng")
        assert result.expanded == "Bê tông cốt thép móng"
        # Should only have one expansion, not two
        assert len(result.expansions_applied) == 1

    def test_btn_before_bt(self, expander):
        """BTN should be matched as 'Bê tông nhựa', not 'Bê tông N'."""
        result = expander.expand("BTN lớp trên")
        assert result.expanded == "Bê tông nhựa lớp trên"

    def test_btxm_before_bt(self, expander):
        """BTXM should be matched as 'Bê tông xi măng'."""
        result = expander.expand("BTXM móng")
        assert result.expanded == "Bê tông xi măng móng"

    def test_cpdd_l1_before_cpdd(self, expander):
        """CPĐDL1 should be matched before CPĐD."""
        result = expander.expand("CPĐDL1")
        assert result.expanded == "Cấp phối đá dăm loại 1"

    def test_gcld_before_gc(self, expander):
        """GCLD should be matched as one unit."""
        result = expander.expand("GCLD cốt thép")
        assert result.expanded == "Gia công lắp dựng cốt thép"

    def test_vkg_before_vk(self, expander):
        """VKG should be matched as 'Ván khuôn gỗ'."""
        result = expander.expand("VKG cột")
        assert result.expanded == "Ván khuôn gỗ cột"

    def test_mixed_abbreviations(self, expander):
        """Multiple abbreviations in one text should all be expanded correctly."""
        result = expander.expand("BT M200, VK gỗ, CT D16")
        assert "Bê tông M200" in result.expanded
        assert "Ván khuôn gỗ" in result.expanded
        assert "Cốt thép D16" in result.expanded


class TestCasePreservation:
    """Test that case patterns are preserved."""

    @pytest.fixture
    def expander(self):
        return AbbreviationExpander()

    def test_lowercase_preserved(self, expander):
        """Lowercase abbreviations should produce lowercase expansions."""
        result = expander.expand("bt m200")
        assert result.expanded == "bê tông m200"

    def test_uppercase_preserved(self, expander):
        """Uppercase abbreviations should produce uppercase expansions."""
        result = expander.expand("BT M200")
        assert result.expanded == "Bê tông M200"
        # First word should be capitalized by default

    def test_all_caps_preserved(self, expander):
        """ALL CAPS abbreviations should produce sentence case expansions.

        For construction domain, abbreviations like BTCT are treated as
        standard abbreviations and expanded to sentence case (Bê tông cốt thép),
        not ALL CAPS, for better readability and consistency.
        """
        result = expander.expand("BTCT DẦM")
        assert result.expanded == "Bê tông cốt thép DẦM"

    def test_capitalized_preserved(self, expander):
        """Capitalized abbreviations should produce capitalized expansions."""
        result = expander.expand("Bt móng")
        assert result.expanded == "Bê tông móng"

    def test_mixed_case_in_sentence(self, expander):
        """Mixed case should be handled per-abbreviation."""
        result = expander.expand("Công tác BT móng với ct D16")
        assert "Bê tông" in result.expanded or "BÊ TÔNG" in result.expanded
        assert "cốt thép" in result.expanded


class TestWordBoundary:
    """Test that partial matches are prevented."""

    @pytest.fixture
    def expander(self):
        return AbbreviationExpander()

    def test_no_partial_match_btm200(self, expander):
        """BTM200 (no space) should NOT be expanded."""
        result = expander.expand("BTM200")
        assert result.expanded == "BTM200"
        assert len(result.expansions_applied) == 0

    def test_no_partial_match_abc_bt_def(self, expander):
        """ABCBT should NOT expand BT."""
        result = expander.expand("ABCBT")
        assert result.expanded == "ABCBT"

    def test_no_partial_match_bt_suffix(self, expander):
        """BTCDE should NOT expand BT."""
        result = expander.expand("BTCDE")
        assert result.expanded == "BTCDE"

    def test_match_with_punctuation(self, expander):
        """BT followed by comma should be expanded."""
        result = expander.expand("BT, VK, CT")
        assert "Bê tông," in result.expanded
        assert "Ván khuôn," in result.expanded
        assert "Cốt thép" in result.expanded

    def test_match_with_parentheses(self, expander):
        """BT in parentheses should be expanded."""
        result = expander.expand("(BT)")
        assert "(Bê tông)" in result.expanded

    def test_match_at_start(self, expander):
        """BT at start of string should be expanded."""
        result = expander.expand("BT M200 cột")
        assert result.expanded.startswith("Bê tông")

    def test_match_at_end(self, expander):
        """BT at end of string should be expanded."""
        result = expander.expand("Đổ BT")
        assert result.expanded.endswith("Bê tông")


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def expander(self):
        return AbbreviationExpander()

    def test_empty_string(self, expander):
        """Empty string should return empty result."""
        result = expander.expand("")
        assert result.expanded == ""
        assert result.original == ""
        assert len(result.expansions_applied) == 0

    def test_none_input(self, expander):
        """None input should be handled gracefully."""
        result = expander.expand(None)
        assert result.expanded == ""
        assert result.original == ""

    def test_whitespace_only(self, expander):
        """Whitespace-only string should return same."""
        result = expander.expand("   ")
        assert result.expanded == "   "
        assert len(result.expansions_applied) == 0

    def test_no_abbreviations(self, expander):
        """Text without abbreviations should be unchanged."""
        text = "Đào đất móng bằng máy"
        result = expander.expand(text)
        assert result.expanded == text
        assert len(result.expansions_applied) == 0

    def test_unicode_normalization(self, expander):
        """Vietnamese diacritics should be handled correctly."""
        result = expander.expand("VĐKT")
        assert result.expanded == "Vải địa kỹ thuật"

    def test_long_text(self, expander):
        """Long text with multiple abbreviations should work."""
        text = "BT M200 cột, VK gỗ, CT D16 CB400, BTCT móng M300"
        result = expander.expand(text)
        assert "Bê tông M200" in result.expanded
        assert "Ván khuôn gỗ" in result.expanded
        assert "Cốt thép D16 CB400" in result.expanded
        assert "Bê tông cốt thép móng M300" in result.expanded


class TestRealWorldExamples:
    """Test with real-world BOQ descriptions."""

    @pytest.fixture
    def expander(self):
        return AbbreviationExpander()

    def test_concrete_column_work(self, expander):
        """Real example: concrete column work."""
        result = expander.expand("BT cột M300 thương phẩm")
        assert "Bê tông cột M300 thương phẩm" == result.expanded

    def test_reinforced_concrete_foundation(self, expander):
        """Real example: RC foundation."""
        result = expander.expand("BTCT móng M250")
        assert "Bê tông cốt thép móng M250" == result.expanded

    def test_formwork_with_film(self, expander):
        """Real example: film-coated formwork."""
        result = expander.expand("VK phủ phim cột")
        assert "Ván khuôn phủ phim cột" == result.expanded

    def test_rebar_fabrication(self, expander):
        """Real example: rebar fabrication."""
        result = expander.expand("GC CT D16 CB400")
        assert "Gia công Cốt thép D16 CB400" == result.expanded

    def test_asphalt_paving(self, expander):
        """Real example: asphalt paving."""
        result = expander.expand("Rải BTN C12.5 lớp dưới")
        assert "Bê tông nhựa" in result.expanded
        assert "C12.5" in result.expanded

    def test_aggregate_base(self, expander):
        """Real example: aggregate base course."""
        result = expander.expand("Lu lèn CPĐD K95")
        assert "Cấp phối đá dăm" in result.expanded
        assert "K95" in result.expanded

    def test_mep_fire_protection(self, expander):
        """Real example: fire protection system."""
        result = expander.expand("LĐ hệ thống PCCC")
        assert "Lắp đặt" in result.expanded
        assert "Phòng cháy chữa cháy" in result.expanded

    def test_mep_hvac(self, expander):
        """Real example: HVAC system."""
        result = expander.expand("TC ĐHKK văn phòng")
        assert "Thi công" in result.expanded
        assert "Điều hòa không khí" in result.expanded

    def test_complex_boq_line(self, expander):
        """Real example: complex BOQ description."""
        text = "GCLD CT móng D<=10 CB300"
        result = expander.expand(text)
        assert "Gia công lắp dựng" in result.expanded
        assert "Cốt thép" in result.expanded
        assert "CB300" in result.expanded

    def test_geotextile_work(self, expander):
        """Real example: geotextile installation."""
        result = expander.expand("Rải VĐKT nền đường")
        assert "Vải địa kỹ thuật" in result.expanded


class TestBatchProcessing:
    """Test batch processing functionality."""

    @pytest.fixture
    def expander(self):
        return AbbreviationExpander()

    def test_batch_expand_multiple(self, expander):
        """Batch expand multiple texts."""
        texts = [
            "BT M200",
            "BTCT móng",
            "VK gỗ",
            "CT D16",
        ]
        results = expander.expand_batch(texts)

        assert len(results) == 4
        assert results[0].expanded == "Bê tông M200"
        assert results[1].expanded == "Bê tông cốt thép móng"
        assert results[2].expanded == "Ván khuôn gỗ"
        assert results[3].expanded == "Cốt thép D16"

    def test_batch_expand_empty_list(self, expander):
        """Batch expand empty list."""
        results = expander.expand_batch([])
        assert len(results) == 0

    def test_batch_expand_with_none(self, expander):
        """Batch expand with None values."""
        texts = ["BT M200", None, "VK gỗ"]
        results = expander.expand_batch(texts)

        assert len(results) == 3
        assert results[0].expanded == "Bê tông M200"
        assert results[1].expanded == ""
        assert results[2].expanded == "Ván khuôn gỗ"


class TestCustomAbbreviations:
    """Test custom abbreviation management."""

    def test_add_abbreviation(self):
        """Add a custom abbreviation."""
        expander = AbbreviationExpander()
        expander.add_abbreviation("TEST", "Testing Value")

        result = expander.expand("TEST item")
        # Abbreviation in CAPS -> sentence case expansion
        assert result.expanded == "Testing value item"

    def test_remove_abbreviation(self):
        """Remove an existing abbreviation."""
        expander = AbbreviationExpander()

        # Verify BT works first
        result = expander.expand("BT M200")
        assert "Bê tông" in result.expanded

        # Remove BT
        removed = expander.remove_abbreviation("BT")
        assert removed is True

        # Now BT should not be expanded
        result = expander.expand("BT M200")
        assert result.expanded == "BT M200"

    def test_remove_nonexistent_abbreviation(self):
        """Remove a non-existent abbreviation."""
        expander = AbbreviationExpander()
        removed = expander.remove_abbreviation("NOTEXIST")
        assert removed is False

    def test_custom_abbreviation_dictionary(self):
        """Use custom abbreviation dictionary."""
        custom_abbrevs = {
            "CUSTOM1": "Custom Value One",
            "CUSTOM2": "Custom Value Two",
        }
        expander = AbbreviationExpander(abbreviations=custom_abbrevs)

        result = expander.expand("CUSTOM1 test CUSTOM2")
        # Abbreviations in CAPS -> sentence case expansion
        assert "Custom value one" in result.expanded
        assert "Custom value two" in result.expanded

        # Default abbreviations should NOT work
        result = expander.expand("BT M200")
        assert result.expanded == "BT M200"


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    def test_expand_abbreviations_simple(self):
        """Test expand_abbreviations function."""
        result = expand_abbreviations("BT M200")
        assert result == "Bê tông M200"

    def test_expand_abbreviations_detailed(self):
        """Test expand_abbreviations_detailed function."""
        result = expand_abbreviations_detailed("BT M200")
        assert isinstance(result, ExpansionResult)
        assert result.expanded == "Bê tông M200"
        assert len(result.expansions_applied) == 1

    def test_get_abbreviation_expander_singleton(self):
        """Test that get_abbreviation_expander returns singleton."""
        expander1 = get_abbreviation_expander()
        expander2 = get_abbreviation_expander()
        assert expander1 is expander2


class TestExpansionResult:
    """Test ExpansionResult dataclass."""

    @pytest.fixture
    def expander(self):
        return AbbreviationExpander()

    def test_result_has_original(self, expander):
        """Result should contain original text."""
        result = expander.expand("BT M200")
        assert result.original == "BT M200"

    def test_result_has_expanded(self, expander):
        """Result should contain expanded text."""
        result = expander.expand("BT M200")
        assert result.expanded == "Bê tông M200"

    def test_result_tracks_expansions(self, expander):
        """Result should track applied expansions."""
        result = expander.expand("BT M200, VK gỗ")
        assert len(result.expansions_applied) == 2

    def test_result_tracks_tech_specs(self, expander):
        """Result should track preserved tech specs."""
        result = expander.expand("BT M200 D16 CB400")
        assert "M200" in result.tech_specs_preserved
        assert "D16" in result.tech_specs_preserved
        assert "CB400" in result.tech_specs_preserved


class TestDefaultAbbreviations:
    """Test that default abbreviations dictionary is complete."""

    def test_concrete_abbreviations_exist(self):
        """Concrete abbreviations should be in defaults."""
        assert "BT" in DEFAULT_ABBREVIATIONS
        assert "BTCT" in DEFAULT_ABBREVIATIONS
        assert "BTXM" in DEFAULT_ABBREVIATIONS
        assert "BTN" in DEFAULT_ABBREVIATIONS

    def test_rebar_abbreviations_exist(self):
        """Rebar abbreviations should be in defaults."""
        assert "CT" in DEFAULT_ABBREVIATIONS
        assert "CTCT" in DEFAULT_ABBREVIATIONS

    def test_formwork_abbreviations_exist(self):
        """Formwork abbreviations should be in defaults."""
        assert "VK" in DEFAULT_ABBREVIATIONS
        assert "VKG" in DEFAULT_ABBREVIATIONS
        assert "VKT" in DEFAULT_ABBREVIATIONS

    def test_aggregate_abbreviations_exist(self):
        """Aggregate abbreviations should be in defaults."""
        assert "CPĐD" in DEFAULT_ABBREVIATIONS
        assert "CPDD" in DEFAULT_ABBREVIATIONS

    def test_mep_abbreviations_exist(self):
        """MEP abbreviations should be in defaults."""
        assert "PCCC" in DEFAULT_ABBREVIATIONS
        assert "ĐHKK" in DEFAULT_ABBREVIATIONS

    def test_work_verb_abbreviations_exist(self):
        """Work verb abbreviations should be in defaults."""
        assert "TC" in DEFAULT_ABBREVIATIONS
        assert "GC" in DEFAULT_ABBREVIATIONS
        assert "LĐ" in DEFAULT_ABBREVIATIONS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
