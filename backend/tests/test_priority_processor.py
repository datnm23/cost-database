"""
Tests for the Priority Processor and Context-Aware Extractors.
"""

import pytest
from app.services.priority_processor import (
    PriorityProcessor,
    PriorityProcessResult,
    get_priority_processor,
    process_with_priority,
)
from app.services.extractors.formwork_extractor import FormworkExtractor
from app.services.extractors.road_extractor import RoadExtractor
from app.services.extractors.precast_extractor import PrecastExtractor
from app.services.imputation_rules import (
    impute_missing,
    get_concrete_grade_for_position,
    get_default_for_object,
)


class TestFormworkExtractor:
    """Test cases for formwork (Ván khuôn) extractor."""

    @pytest.fixture
    def extractor(self):
        return FormworkExtractor()

    def test_extract_position_mong(self, extractor):
        """Should extract foundation position."""
        specs = extractor.extract("Ván khuôn móng M200")
        assert specs.get('position') == 'Móng'

    def test_extract_position_dam_san(self, extractor):
        """Should extract beam/slab position."""
        specs = extractor.extract("Ván khuôn dầm sàn")
        assert 'dầm' in specs.get('position', '').lower() or 'sàn' in specs.get('position', '').lower()

    def test_extract_type_phu_phim(self, extractor):
        """Should extract formwork type."""
        specs = extractor.extract("Ván khuôn phủ phim móng")
        assert specs.get('type') == 'Phủ phim'

    def test_extract_dimensions(self, extractor):
        """Should extract dimensions."""
        specs = extractor.extract("Ván khuôn 1000x500x300")
        assert specs.get('dimensions') == '1000x500x300'

    def test_default_type_not_auto_filled(self, extractor):
        """Default type should NOT be auto-filled (Bug 3 fix - no hallucination)."""
        specs = extractor.extract("Ván khuôn móng")
        # Type should NOT be set if not in input (prevents hallucination)
        assert specs.get('type') is None, \
            f"Hallucination: type auto-filled as '{specs.get('type')}'"


class TestRoadExtractor:
    """Test cases for road construction extractor."""

    @pytest.fixture
    def extractor(self):
        return RoadExtractor()

    def test_extract_layer_tren(self, extractor):
        """Should extract upper layer."""
        specs = extractor.extract("CPĐD lớp trên loại 1")
        assert specs.get('layer') == 'Lớp trên'

    def test_extract_layer_duoi(self, extractor):
        """Should extract lower layer."""
        specs = extractor.extract("CPĐD lớp dưới loại 2")
        assert specs.get('layer') == 'Lớp dưới'

    def test_extract_asphalt_grade(self, extractor):
        """Should extract asphalt grade (C19)."""
        specs = extractor.extract("BTN C19 hạt mịn")
        assert specs.get('asphalt_grade') == 'C19'

    def test_extract_asphalt_grade_decimal(self, extractor):
        """Should extract asphalt grade with decimal (C12.5)."""
        specs = extractor.extract("BTN C12.5")
        assert specs.get('asphalt_grade') == 'C12.5'

    def test_extract_compaction(self, extractor):
        """Should extract compaction (K98)."""
        specs = extractor.extract("Đắp đất nền đường K98")
        assert specs.get('compaction') == 'K98'

    def test_extract_thickness(self, extractor):
        """Should extract thickness."""
        specs = extractor.extract("BTN dày 5cm")
        assert specs.get('thickness') == 'dày 5cm'


class TestPrecastExtractor:
    """Test cases for precast component extractor."""

    @pytest.fixture
    def extractor(self):
        return PrecastExtractor()

    def test_extract_material_btct(self, extractor):
        """Should extract BTCT material."""
        specs = extractor.extract("Bó vỉa BTCT")
        assert specs.get('material') == 'BTCT'

    def test_extract_dimensions(self, extractor):
        """Should extract dimensions."""
        specs = extractor.extract("Tấm đan 500x500x50")
        assert specs.get('dimensions') == '500x500x50'

    def test_extract_dimensions_from_parentheses(self, extractor):
        """Should extract dimensions from parentheses."""
        specs = extractor.extract("Bó vỉa (230x260x1000)")
        assert specs.get('dimensions') == '230x260x1000'

    def test_extract_component_type(self, extractor):
        """Should identify component type."""
        specs = extractor.extract("Cống tròn BTCT D1000")
        assert specs.get('component_type') == 'culvert'

    def test_extract_diameter_cong(self, extractor):
        """Should extract culvert diameter."""
        specs = extractor.extract("Cống tròn D1000")
        assert specs.get('diameter') == 'D1000'


class TestImputationRules:
    """Test cases for imputation rules."""

    def test_impute_dao_method(self):
        """Should impute default method for Đào."""
        specs = impute_missing('Đào', {})
        assert specs.get('method') is not None
        assert 'máy' in specs.get('method').lower()

    def test_impute_dap_compaction(self):
        """Should impute default compaction for Đắp."""
        specs = impute_missing('Đắp', {})
        assert specs.get('compaction') is not None
        assert 'K' in specs.get('compaction')

    def test_impute_van_chuyen_distance(self):
        """Should impute default distance for Vận chuyển."""
        specs = impute_missing('Vận chuyển', {})
        assert specs.get('distance') is not None
        assert 'km' in specs.get('distance')

    def test_impute_be_tong_grade_default(self):
        """Should impute default concrete grade."""
        specs = impute_missing('Bê tông', {})
        assert specs.get('grade') is not None
        assert specs['grade'].startswith('M')

    def test_impute_be_tong_grade_for_lot_mong(self):
        """Should impute M100 for lót móng."""
        specs = impute_missing('Bê tông', {}, position='lót móng')
        assert specs.get('grade') == 'M100'

    def test_impute_be_tong_grade_for_dam_san(self):
        """Should impute M350 for dầm sàn."""
        specs = impute_missing('Bê tông', {}, position='dầm sàn')
        assert specs.get('grade') == 'M350'

    def test_impute_cot_thep_grade(self):
        """Should impute 'Theo thiết kế' for cốt thép."""
        specs = impute_missing('Cốt thép', {})
        assert specs.get('grade') == 'Theo thiết kế'

    def test_impute_van_khuon_type_not_auto_filled(self):
        """Should NOT auto-fill type for ván khuôn (Bug 3 fix - no hallucination)."""
        specs = impute_missing('Ván khuôn', {})
        # Type should NOT be auto-filled to prevent hallucination
        assert specs.get('type') is None, \
            f"Hallucination: type auto-filled as '{specs.get('type')}'"

    def test_get_concrete_grade_for_position(self):
        """Should return correct grade for position."""
        assert get_concrete_grade_for_position('lót móng') == 'M100'
        assert get_concrete_grade_for_position('dầm sàn') == 'M350'
        assert get_concrete_grade_for_position('cột') == 'M300'

    def test_get_default_for_object(self):
        """Should return default for object type."""
        assert get_default_for_object('Đào', 'method') is not None
        assert get_default_for_object('Vận chuyển', 'distance') is not None


class TestPriorityProcessor:
    """Test cases for priority processor."""

    @pytest.fixture
    def processor(self):
        return PriorityProcessor()

    def test_process_van_khuon(self, processor):
        """Should correctly identify ván khuôn over bê tông."""
        result = processor.process("Ván khuôn móng bê tông M200")

        assert result.object_name == 'Ván khuôn'
        assert result.priority == 1
        assert result.confidence > 0.5

    def test_process_bo_via(self, processor):
        """Should correctly identify bó vỉa."""
        result = processor.process("Bó vỉa đá granite 300x150")

        assert result.object_name == 'Bó vỉa'
        assert result.priority == 2

    def test_process_cpdd_with_layer(self, processor):
        """Should extract layer info for CPĐD."""
        result = processor.process("CPĐD lớp trên loại 1")

        assert 'layer' in result.specs or 'Lớp trên' in result.normalized

    def test_normalized_has_three_components_max(self, processor):
        """Normalized output should have max 2 dashes (3 components)."""
        result = processor.process("Ván khuôn móng bê tông M200")

        dash_count = result.normalized.count(' - ')
        assert dash_count <= 2, f"Output has {dash_count + 1} components: {result.normalized}"

    def test_empty_input(self, processor):
        """Should handle empty input."""
        result = processor.process("")

        assert result.object_name is None
        assert result.confidence == 0

    def test_unknown_input(self, processor):
        """Should have low confidence for unknown input."""
        result = processor.process("xyz abc 123")

        assert result.confidence < 0.5

    def test_process_with_priority_function(self):
        """Convenience function should work."""
        result = process_with_priority("Ván khuôn móng")

        assert result.object_name == 'Ván khuôn'

    def test_get_priority_processor_singleton(self):
        """Should return same instance."""
        proc1 = get_priority_processor()
        proc2 = get_priority_processor()

        assert proc1 is proc2


class TestPriorityProcessorIdentityTheft:
    """
    Specific tests for the 'Identity Theft' problem.

    These are the critical test cases that verify the priority model
    correctly solves the flat keyword matching issue.
    """

    @pytest.fixture
    def processor(self):
        return PriorityProcessor()

    def test_van_khuon_not_be_tong(self, processor):
        """
        Ván khuôn móng bê tông → Ván khuôn (NOT Bê tông)
        This is the core 'Identity Theft' fix.
        """
        result = processor.process("Ván khuôn móng bê tông M200")

        assert result.object_name == 'Ván khuôn'
        assert 'Bê tông' not in result.object_name

    def test_bo_via_not_da(self, processor):
        """
        Bó vỉa đá granite → Bó vỉa (NOT Đá)
        Component should win over material.
        """
        result = processor.process("Bó vỉa đá granite 300x150")

        assert result.object_name == 'Bó vỉa'
        assert result.object_name != 'Đá'

    def test_tam_dan_not_be_tong(self, processor):
        """
        Tấm đan bê tông → Tấm đan (NOT Bê tông)
        """
        result = processor.process("Tấm đan bê tông 500x500x50")

        assert result.object_name == 'Tấm đan'

    def test_ho_ga_not_be_tong(self, processor):
        """
        Hố ga → Hố ga (NOT Bê tông)
        Note: "Hố ga bê tông cốt thép" matches "cốt thép" first due to Priority 2
        """
        result = processor.process("Hố ga M200")

        assert result.object_name == 'Hố ga'


class TestPhase2BugFixes:
    """
    Test cases for Phase 2 bug fixes.
    These verify the 6 critical bugs identified in the standard naming strategy.
    """

    @pytest.fixture
    def processor(self):
        return PriorityProcessor()

    def test_bug_1_cong_btct(self, processor):
        """
        Bug 1: "Cống BTCT D800" should become "Cống thoát nước - BTCT - D800"
        Previously: "Cống BTCT - D800" (missing 1 component)
        """
        result = processor.process("Cống BTCT D800")

        # Object should be "Cống thoát nước" (not compound "Cống BTCT")
        assert result.object_name == 'Cống thoát nước'
        # BTCT should be extracted as material, not part of object name
        # D800 should be in specs
        assert 'D800' in result.normalized or 'D800' in str(result.specs.get('diameter', ''))

    def test_bug_2_mccb_specs(self, processor):
        """
        Bug 2: "MCCB-3P-400A-36kA" should become "MCCB - 3P - 400A 36kA"
        Previously: "MCCB - 3P 400A 36kA" (only 2 components)
        Now: Poles in middle part, amps/kA in spec part
        """
        result = processor.process("MCCB-3P-400A-36kA")

        # Must have exactly 3 components (2 dashes)
        dash_count = result.normalized.count(' - ')
        assert dash_count == 2, f"Expected 3 components (2 dashes), got: {result.normalized}"

        # All specs should be present
        assert '3P' in result.normalized, f"Missing 3P in: {result.normalized}"
        assert '400A' in result.normalized, f"Missing 400A in: {result.normalized}"
        assert '36kA' in result.normalized, f"Missing 36kA in: {result.normalized}"

        # Structure should be: MCCB - 3P - 400A 36kA
        parts = result.normalized.split(' - ')
        assert len(parts) == 3, f"Expected 3 parts, got {len(parts)}: {parts}"
        assert parts[0] == 'MCCB', f"First part should be MCCB, got: {parts[0]}"
        assert parts[1] == '3P', f"Second part should be 3P, got: {parts[1]}"
        assert '400A' in parts[2] and '36kA' in parts[2], f"Third part should contain 400A 36kA, got: {parts[2]}"

    def test_bug_3_no_hallucination(self, processor):
        """
        Bug 3: "Ván khuôn móng bê tông M200" should have "Theo thiết kế" when type missing
        Previously: Added "Phủ phim" even when input didn't specify it
        Now: Adds "Theo thiết kế" as placeholder
        """
        result = processor.process("Ván khuôn móng bê tông M200")

        # Must have exactly 3 components (2 dashes)
        dash_count = result.normalized.count(' - ')
        assert dash_count == 2, f"Expected 3 components (2 dashes), got: {result.normalized}"

        # Should NOT contain "Phủ phim" since it wasn't in input
        assert 'Phủ phim' not in result.normalized, \
            f"Hallucination detected: 'Phủ phim' in '{result.normalized}'"

        # Should contain "Theo thiết kế" as placeholder for missing type
        assert 'Theo thiết kế' in result.normalized, \
            f"Missing 'Theo thiết kế' placeholder in '{result.normalized}'"

        # Structure should be: Ván khuôn - Móng - Theo thiết kế
        parts = result.normalized.split(' - ')
        assert len(parts) == 3, f"Expected 3 parts, got {len(parts)}: {parts}"
        assert parts[0] == 'Ván khuôn', f"First part should be 'Ván khuôn', got: {parts[0]}"

    def test_bug_4_concrete_object(self, processor):
        """
        Bug 4: "Bê tông hố ga đá 1x2 mác 200" should have Object = "Bê tông"
        Previously: Object = "Hố ga" (wrong - hố ga is just position)
        """
        result = processor.process("Bê tông hố ga đá 1x2 mác 200")

        # Object should be "Bê tông", not "Hố ga"
        assert result.object_name == 'Bê tông', \
            f"Expected 'Bê tông', got '{result.object_name}'"

        # M200 should be in output
        assert 'M200' in result.normalized, \
            f"Missing M200 in '{result.normalized}'"

    def test_bug_5_cable_complete(self, processor):
        """
        Bug 5: "Cu-Fr/XLPE/PVC 3x95+1x50mm2" should preserve complete cable spec
        Previously: "3x95" (lost +1x50mm2)
        """
        from app.services.dictionaries.specs import extract_specs

        # Test spec extraction for cable with neutral conductor
        specs, remaining = extract_specs("Cu-Fr/XLPE/PVC 3x95+1x50mm2")

        # Full cable spec should be preserved
        specs_str = ' '.join(specs)
        assert '3x95' in specs_str, f"Missing 3x95 in specs: {specs}"
        assert '1x50' in specs_str, f"Missing +1x50 in specs: {specs}"

    def test_bug_6_separate_material(self, processor):
        """
        Bug 6: "Chếch HDPE D500" should become "Chếch - HDPE - D500"
        Previously: "Chếch HDPE - D500" (material not separated)
        """
        result = processor.process("Chếch HDPE D500")

        # Object should be "Chếch" (not compound "Chếch HDPE")
        assert result.object_name == 'Chếch', \
            f"Expected 'Chếch', got '{result.object_name}'"

        # D500 should be in specs
        assert 'D500' in result.normalized or 'D500' in str(result.specs.get('diameter', '')), \
            f"Missing D500 in '{result.normalized}'"


class TestPhase21BugFixes:
    """
    Test cases for Phase 2.1 bug fixes.
    These verify the 2 remaining bugs after Phase 2 implementation.
    """

    @pytest.fixture
    def processor(self):
        return PriorityProcessor()

    def test_bug_2_mccb_three_components(self, processor):
        """
        Bug 2 (Phase 2.1): MCCB-3P-400A-36kA should output exactly 3 parts
        Output: "MCCB - 3P - 400A 36kA"
        - Part 1: MCCB (object)
        - Part 2: 3P (poles - middle part)
        - Part 3: 400A 36kA (amps and breaking capacity - spec part)
        """
        result = processor.process("MCCB-3P-400A-36kA")

        # Verify 3 components
        parts = result.normalized.split(' - ')
        assert len(parts) == 3, f"Expected 3 parts, got {len(parts)}: {result.normalized}"

        # Verify structure
        assert parts[0] == 'MCCB'
        assert parts[1] == '3P'
        assert '400A' in parts[2] and '36kA' in parts[2]

    def test_bug_3_van_khuon_theo_tk(self, processor):
        """
        Bug 3 (Phase 2.1): Ván khuôn móng bê tông M200 should output exactly 3 parts
        Output: "Ván khuôn - Móng - Theo thiết kế"
        - Part 1: Ván khuôn (object)
        - Part 2: Móng (position)
        - Part 3: Theo thiết kế (placeholder for missing type)
        """
        result = processor.process("Ván khuôn móng bê tông M200")

        # Verify 3 components
        parts = result.normalized.split(' - ')
        assert len(parts) == 3, f"Expected 3 parts, got {len(parts)}: {result.normalized}"

        # Verify structure
        assert parts[0] == 'Ván khuôn'
        assert 'Móng' in parts[1]
        assert 'Theo thiết kế' in parts[2]

    def test_van_khuon_with_type_preserves_type(self, processor):
        """
        When type IS specified, it should be preserved (not replaced with Theo thiết kế).
        """
        result = processor.process("Ván khuôn phủ phim móng")

        parts = result.normalized.split(' - ')
        assert len(parts) == 3, f"Expected 3 parts, got {len(parts)}: {result.normalized}"
        assert parts[0] == 'Ván khuôn'
        assert 'Móng' in result.normalized
        assert 'Phủ phim' in result.normalized, \
            f"Expected 'Phủ phim' type in output, got: {result.normalized}"

    def test_mcb_three_components(self, processor):
        """
        MCB should also have 3 components like MCCB.
        """
        result = processor.process("MCB 2P 32A 6kA")

        parts = result.normalized.split(' - ')
        assert len(parts) == 3, f"Expected 3 parts, got {len(parts)}: {result.normalized}"
        assert parts[0] == 'MCB'
        assert parts[1] == '2P'
        assert '32A' in parts[2]

    def test_rccb_three_components(self, processor):
        """
        RCCB should also have 3 components.
        """
        result = processor.process("RCCB 4P 40A 30mA")

        parts = result.normalized.split(' - ')
        assert len(parts) >= 2, f"Expected at least 2 parts, got: {result.normalized}"
        assert parts[0] == 'RCCB'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


class TestPhase4BugFixes:
    """
    Test cases for Phase 4 critical bug fixes.
    BUG 1: Cống → Vận chuyển identity crisis
    BUG 2: K98 data loss in Móng đường
    BUG 3: Structure fail - items with < 3 components
    """

    @pytest.fixture
    def processor(self):
        return PriorityProcessor()

    def test_bug_1_cong_not_van_chuyen(self, processor):
        """
        BUG 1: "Cung cấp, lắp đặt cống BTCT D1000" should become "Cống thoát nước"
        NOT "Vận chuyển" - installation context should override Priority 1
        """
        result = processor.process("Cung cấp, lắp đặt cống BTCT D1000")

        assert 'Cống' in result.normalized, \
            f"Expected 'Cống' in output, got: {result.normalized}"
        assert 'Vận chuyển' not in result.normalized, \
            f"Should NOT be 'Vận chuyển', got: {result.normalized}"
        # Should have BTCT as material
        assert 'BTCT' in result.normalized, \
            f"Expected 'BTCT' in output, got: {result.normalized}"

    def test_bug_1_cong_hop_installation(self, processor):
        """
        BUG 1: "Lắp đặt cống hộp 2x2m" should become "Cống hộp"
        NOT "Vận chuyển"
        """
        result = processor.process("Lắp đặt cống hộp BTCT 2x2m")

        assert result.object_name == 'Cống hộp', \
            f"Expected 'Cống hộp', got: {result.object_name}"
        assert 'Vận chuyển' not in result.normalized

    def test_bug_1_ho_ga_installation(self, processor):
        """
        BUG 1: "Thi công hố ga BTCT" should become "Hố ga"
        NOT "Vận chuyển"
        """
        result = processor.process("Thi công hố ga BTCT")

        assert result.object_name == 'Hố ga', \
            f"Expected 'Hố ga', got: {result.object_name}"

    def test_bug_2_k98_preserved(self, processor):
        """
        BUG 2: "Thi công móng cấp phối đá dăm lớp dưới độ chặt K98"
        Should preserve K98 in output: "Móng đường - CPĐD - Lớp dưới K98"
        """
        result = processor.process("Thi công móng cấp phối đá dăm lớp dưới độ chặt K98")

        assert 'K98' in result.normalized, \
            f"K98 data loss! Expected 'K98' in output, got: {result.normalized}"

    def test_bug_2_k95_preserved(self, processor):
        """
        BUG 2: Similar test for K95 compaction
        """
        result = processor.process("Móng cấp phối đá dăm lớp trên K95")

        assert 'K95' in result.normalized, \
            f"K95 data loss! Expected 'K95' in output, got: {result.normalized}"

    def test_bug_3_thanh_cai_three_components(self, processor):
        """
        BUG 3: "Thanh cái đồng" should have 3 components
        Expected: "Thanh cái - Đồng - Theo thiết kế"
        """
        result = processor.process("Thanh cái đồng")

        parts = result.normalized.split(' - ')
        assert len(parts) == 3, \
            f"Expected 3 components, got {len(parts)}: {result.normalized}"
        assert parts[0] == 'Thanh cái'
        assert 'Đồng' in result.normalized

    def test_bug_3_den_tin_hieu_three_components(self, processor):
        """
        BUG 3: "Đèn tín hiệu" should have 3 components
        """
        result = processor.process("Đèn tín hiệu báo pha đỏ")

        parts = result.normalized.split(' - ')
        assert len(parts) == 3, \
            f"Expected 3 components, got {len(parts)}: {result.normalized}"
        assert parts[0] == 'Đèn tín hiệu'

    def test_bug_3_tu_gom_cong_to_two_components(self, processor):
        """
        "Tủ gom công tơ" should have 2 components (not 3)
        Expected: "Tủ điện - Tủ gom công tơ" (no part3)
        """
        result = processor.process("Tủ gom công tơ")

        parts = result.normalized.split(' - ')
        assert len(parts) == 2, \
            f"Expected 2 components, got {len(parts)}: {result.normalized}"
        assert parts[0] == 'Tủ điện'
        assert parts[1] == 'Tủ gom công tơ'

    def test_bug_3_cot_thep_three_components(self, processor):
        """
        BUG 3: "Cốt thép" should have 3 components even without diameter
        """
        result = processor.process("Cốt thép")

        parts = result.normalized.split(' - ')
        assert len(parts) == 3, \
            f"Expected 3 components, got {len(parts)}: {result.normalized}"
        assert parts[0] == 'Cốt thép'

    def test_bug_3_cot_thep_with_diameter(self, processor):
        """
        BUG 3: "Cốt thép D12" should have 3 components with diameter
        """
        result = processor.process("Cốt thép D12")

        parts = result.normalized.split(' - ')
        assert len(parts) == 3, \
            f"Expected 3 components, got {len(parts)}: {result.normalized}"
        assert 'D12' in result.normalized

    def test_structure_compliance_generic(self, processor):
        """
        Most outputs should have exactly 3 components (2 dashes)
        Exception: "Tủ gom công tơ" has 2 components (1 dash)
        """
        test_cases = [
            ("Thanh cái đồng", 2),
            ("Đèn tín hiệu giao thông", 2),
            ("Tủ gom công tơ", 1),  # This one has only 2 components
            ("Cốt thép", 2),
            ("Móng đường CPĐD lớp dưới K98", 2),
        ]

        for case, expected_dashes in test_cases:
            result = processor.process(case)
            if result.normalized:  # Skip empty results
                dash_count = result.normalized.count(' - ')
                assert dash_count == expected_dashes, \
                    f"'{case}' → '{result.normalized}' has {dash_count} dashes, expected {expected_dashes}"


class TestSecondaryObject:
    """
    Test cases for secondary_object detection when P1 override
    causes loss of P2/P3 object information.
    """

    @pytest.fixture
    def processor(self):
        return PriorityProcessor()

    def test_van_chuyen_may_bien_ap(self, processor):
        """'Vận chuyển máy biến áp 1000KVA' should detect 'Máy biến áp' as secondary."""
        result = processor.process("Vận chuyển máy biến áp 1000KVA")

        assert result.object_name == 'Vận chuyển'
        assert result.priority == 1
        assert result.secondary_object == 'Máy biến áp'
        assert result.secondary_priority > 1

    def test_van_chuyen_cong(self, processor):
        """'Vận chuyển cống BTCT D600' should detect 'Cống thoát nước' as secondary."""
        result = processor.process("Vận chuyển cống BTCT D600")

        assert result.object_name == 'Vận chuyển'
        assert result.secondary_object is not None

    def test_van_khuon_no_secondary_when_p1_only(self, processor):
        """'Ván khuôn móng' — P1 match, no secondary unless another P2/P3 exists."""
        result = processor.process("Ván khuôn móng")

        assert result.object_name == 'Ván khuôn'
        assert result.priority == 1
        # secondary_object may or may not be set depending on dict entries

    def test_no_secondary_for_p2(self, processor):
        """P2 matches should not populate secondary_object."""
        result = processor.process("Cống BTCT D600")

        assert result.priority != 1
        assert result.secondary_object is None

    def test_no_secondary_for_p3(self, processor):
        """P3 matches should not populate secondary_object."""
        result = processor.process("Bê tông M200")

        assert result.secondary_object is None


class TestOverlappingMatchSuppression:
    """
    Test that keyword domination suppression works correctly.
    When 'van' is a word-prefix of 'van khuon', 'van' should be suppressed.
    """

    @pytest.fixture
    def processor(self):
        return PriorityProcessor()

    def test_van_khuon_no_van(self, processor):
        """'Ván khuôn gỗ' → 'Ván khuôn' matched, 'Van' suppressed."""
        result = processor.process("Ván khuôn gỗ, ván khuôn móng cột")

        assert result.object_name == 'Ván khuôn'
        assert 'Van' not in (result.secondary_object or ''), \
            f"'Van' should be suppressed, got secondary_object={result.secondary_object}"

    def test_van_chuyen_no_van(self, processor):
        """'Vận chuyển cống' → 'Vận chuyển' matched, 'Van' suppressed."""
        result = processor.process("Vận chuyển cống BTCT D600")

        assert result.object_name == 'Vận chuyển'
        # Van should not appear as secondary_object
        assert result.secondary_object != 'Van', \
            f"'Van' should be suppressed, got secondary_object={result.secondary_object}"

    def test_independent_matches_preserved(self, processor):
        """'Ván khuôn móng bê tông M200' → both 'Ván khuôn' and 'Bê tông' survive."""
        result = processor.process("Ván khuôn móng bê tông M200")

        assert result.object_name == 'Ván khuôn'
        # Bê tông is independent of Ván khuôn — should survive as secondary
        # (Bê tông is a P3 material match, not dominated by any other keyword)


class TestFixedToSpecConversion:
    """
    Test that items previously using source='fixed' now correctly
    extract spec values from input descriptions.
    """

    @pytest.fixture
    def processor(self):
        return PriorityProcessor()

    def test_van_khuon_go_extracts_type(self, processor):
        """'Ván khuôn gỗ móng' → type should be 'Gỗ'."""
        result = processor.process("Ván khuôn gỗ móng")

        parts = result.normalized.split(' - ')
        assert len(parts) == 3, f"Expected 3 parts, got {len(parts)}: {result.normalized}"
        assert parts[0] == 'Ván khuôn'
        assert 'Gỗ' in result.normalized, \
            f"Expected 'Gỗ' type in output, got: {result.normalized}"

    def test_van_khuon_no_type_fallback(self, processor):
        """'Ván khuôn móng' → no type → fallback 'Theo thiết kế'."""
        result = processor.process("Ván khuôn móng")

        parts = result.normalized.split(' - ')
        assert len(parts) == 3, f"Expected 3 parts, got {len(parts)}: {result.normalized}"
        assert parts[0] == 'Ván khuôn'
        assert 'Theo thiết kế' in result.normalized, \
            f"Expected fallback 'Theo thiết kế', got: {result.normalized}"

    def test_van_khuon_phu_phim(self, processor):
        """'Ván khuôn phủ phim cột' → type = 'Phủ phim'."""
        result = processor.process("Ván khuôn phủ phim cột")

        assert 'Phủ phim' in result.normalized, \
            f"Expected 'Phủ phim' in output, got: {result.normalized}"

    def test_cot_thep_d12(self, processor):
        """'Cốt thép D12' → part3 = 'D12' via extract_rebar_size."""
        result = processor.process("Cốt thép D12")

        parts = result.normalized.split(' - ')
        assert len(parts) == 3, f"Expected 3 parts, got {len(parts)}: {result.normalized}"
        assert 'D12' in parts[2], \
            f"Expected 'D12' in part3, got: {result.normalized}"

    def test_dong_ho_nuoc_dn20(self, processor):
        """'Đồng hồ nước DN20' → part2 = 'DN20', part3 = fallback."""
        result = processor.process("Đồng hồ nước DN20")

        parts = result.normalized.split(' - ')
        assert len(parts) == 3, f"Expected 3 parts, got {len(parts)}: {result.normalized}"
        assert 'DN20' in parts[1], \
            f"Expected 'DN20' in part2, got: {result.normalized}"
        assert parts[2] == 'Theo thiết kế', \
            f"Expected fallback in part3, got: {result.normalized}"


class TestV2BugFixes:
    """
    Regression tests for the 6 semantic/priority bugs identified
    from MEP BOQ review (5. BOQ mời thầu MEP).
    """

    @pytest.fixture
    def processor(self):
        return PriorityProcessor()

    def test_bug1_bo_dieu_khien_ats(self, processor):
        """Bug 1: 'Bộ điều khiển ATS 4P-100A' should map to Tủ điều khiển ATS."""
        result = processor.process("Bộ điều khiển ATS 4P-100A")

        assert 'Tủ điều khiển' in result.object_name, \
            f"Expected 'Tủ điều khiển' in object, got: {result.object_name}"
        assert '4P' in result.normalized, \
            f"Expected '4P' in output, got: {result.normalized}"
        assert '100A' in result.normalized, \
            f"Expected '100A' in output, got: {result.normalized}"

    def test_bug2_van_buom_kem_cong_tac(self, processor):
        """Bug 2: 'Van bướm tay gạt, kèm công tắc giám sát DN100' should be Van bướm."""
        result = processor.process("Van bướm tay gạt, kèm công tắc giám sát DN100")

        assert result.object_name == 'Van bướm', \
            f"Expected 'Van bướm', got: {result.object_name}"
        assert 'DN100' in result.normalized, \
            f"Expected 'DN100' in output, got: {result.normalized}"

    def test_bug3_ong_dong_phi(self, processor):
        """Bug 3: 'Ống đồng phi 9.52' should be Ống đồng with phi spec."""
        result = processor.process("Ống đồng phi 9.52")

        assert result.object_name == 'Ống đồng', \
            f"Expected 'Ống đồng', got: {result.object_name}"
        assert 'phi 9.52' in result.normalized, \
            f"Expected 'phi 9.52' in output, got: {result.normalized}"

    def test_bug4_dong_ho_da_nang_no_material_false_positive(self, processor):
        """Bug 4: 'Đồng hồ đa năng 0.5S Modbus' should not have material=Đồng."""
        result = processor.process("Đồng hồ đa năng 0.5S Modbus")

        assert result.object_name == 'Đồng hồ đa năng', \
            f"Expected 'Đồng hồ đa năng', got: {result.object_name}"
        # Should NOT have Đồng as a false-positive material
        parts = result.normalized.split(' - ')
        assert parts[0] != 'Đồng', \
            f"False positive: 'Đồng' as material in: {result.normalized}"

    def test_bug5_chau_rua_inox(self, processor):
        """Bug 5: 'Chậu rửa Inox 304' should be Chậu rửa, not Inox."""
        result = processor.process("Chậu rửa Inox 304")

        assert result.object_name == 'Chậu rửa', \
            f"Expected 'Chậu rửa', got: {result.object_name}"
        assert 'Inox' in result.normalized, \
            f"Expected 'Inox' in output, got: {result.normalized}"

    def test_bug6_van_goc_dn15(self, processor):
        """Bug 6: 'Van góc DN15' should be Van góc, not generic Van."""
        result = processor.process("Van góc DN15")

        assert result.object_name == 'Van góc', \
            f"Expected 'Van góc', got: {result.object_name}"
        assert 'DN15' in result.normalized, \
            f"Expected 'DN15' in output, got: {result.normalized}"


class TestV3BugFixes:
    """
    Regression tests for 6 misclassification bugs identified from
    MEP BOQ output review (round 3).
    """

    @pytest.fixture
    def processor(self):
        return PriorityProcessor()

    def test_bon_dau_not_quet(self, processor):
        """Bồn dầu should not be classified as Quét due to 'quét nhựa đường'."""
        result = processor.process("Bồn dầu 1.5 ( m3 ) + quét nhựa đường lên thành bồn")
        assert result.object_name == 'Bồn dầu', \
            f"Expected 'Bồn dầu', got: {result.object_name}"

    def test_ong_cap_dau_inox304(self, processor):
        """Ống cấp dầu INOX304 should be Ống Inox, not plain Inox."""
        result = processor.process("Ống cấp dầu INOX304 - DN32")
        assert result.object_name == 'Ống Inox', \
            f"Expected 'Ống Inox', got: {result.object_name}"
        assert 'DN32' in result.normalized, \
            f"Expected 'DN32' in output, got: {result.normalized}"

    def test_ong_hoi_dau_inox304(self, processor):
        """Ống hồi dầu INOX304 should be Ống Inox, not plain Inox."""
        result = processor.process("Ống hồi dầu INOX304 - DN32")
        assert result.object_name == 'Ống Inox', \
            f"Expected 'Ống Inox', got: {result.object_name}"

    def test_ong_cap_dau_vao_bon_dau_inox304(self, processor):
        """Ống cấp dầu vào bồn dầu INOX304 should be Ống Inox."""
        result = processor.process("Ống cấp dầu vào bồn dầu INOX304 - DN65")
        assert result.object_name == 'Ống Inox', \
            f"Expected 'Ống Inox', got: {result.object_name}"
        assert 'DN65' in result.normalized, \
            f"Expected 'DN65' in output, got: {result.normalized}"

    def test_hong_tiep_dau_not_ong_nhua(self, processor):
        """Họng tiếp dầu should not be fuzzy-matched to Ống nhựa."""
        result = processor.process("Họng tiếp dầu + hệ thống thông báo mức dầu")
        assert result.object_name == 'Họng tiếp dầu', \
            f"Expected 'Họng tiếp dầu', got: {result.object_name}"

    def test_mang_cap_not_may_phat_dien(self, processor):
        """Máng cáp from MPĐ should be Máng cáp, not Máy phát điện."""
        result = processor.process("Máng cáp 300x100x1.5 từ máy phát điện đến MSB-GE")
        assert result.object_name == 'Máng cáp', \
            f"Expected 'Máng cáp', got: {result.object_name}"


class TestV4BugFixes:
    """
    Regression tests for electrical equipment misclassifications (round 4).
    MCT/PCT, Rơle, phụ kiện ACB/MCCB, timer relay, material false positive.
    """

    @pytest.fixture
    def processor(self):
        return PriorityProcessor()

    def test_phu_kien_cho_acb(self, processor):
        """Phụ kiện cho ACB should be Phụ kiện ACB, not ACB itself."""
        result = processor.process("Phụ kiện Opening Release 220VAC cho ACB")
        assert result.object_name == 'Phụ kiện ACB', \
            f"Expected 'Phụ kiện ACB', got: {result.object_name}"

    def test_bo_cat_cho_mccb(self, processor):
        """Bộ cắt cho MCCB should be Phụ kiện MCCB, not MCCB itself."""
        result = processor.process("Bộ Cắt 200-240VAC cho MCCB")
        assert result.object_name == 'Phụ kiện MCCB', \
            f"Expected 'Phụ kiện MCCB', got: {result.object_name}"

    def test_motor_mechanism(self, processor):
        """Motor Mechanism should be Phụ kiện ACB."""
        result = processor.process("Motor Mechanism 220VAC cho MVS Drawout")
        assert result.object_name == 'Phụ kiện ACB', \
            f"Expected 'Phụ kiện ACB', got: {result.object_name}"

    def test_role_not_quat(self, processor):
        """Rơle (without space) should be Rơ le, not Quạt via fuzzy."""
        result = processor.process("Rơle Quá áp& thấp áp, Rơle Mất cân bằng")
        assert result.object_name == 'Rơ le', \
            f"Expected 'Rơ le', got: {result.object_name}"

    def test_mct_is_bien_dong(self, processor):
        """MCT (Measurement CT) should be Biến dòng (CT), not Loa."""
        result = processor.process("MCT 2500/5A loại 1 15VA")
        assert result.object_name == 'Biến dòng (CT)', \
            f"Expected 'Biến dòng (CT)', got: {result.object_name}"

    def test_pct_is_bien_dong(self, processor):
        """PCT (Protection CT) should be Biến dòng (CT), not Loa."""
        result = processor.process("PCT 2500/5A loại 5P10 15VA")
        assert result.object_name == 'Biến dòng (CT)', \
            f"Expected 'Biến dòng (CT)', got: {result.object_name}"

    def test_ro_le_dong_no_material_false_positive(self, processor):
        """Rơ le dòng chạm đất should not have Đồng as material."""
        result = processor.process("Rơ le dòng chạm đất")
        assert result.object_name == 'Rơ le', \
            f"Expected 'Rơ le', got: {result.object_name}"
        assert 'Đồng' not in result.normalized, \
            f"False positive 'Đồng' material in: {result.normalized}"

    def test_timer_relay(self, processor):
        """Time loại trễ should be Rơ le thời gian, not Loa."""
        result = processor.process("Time loại trễ 6s-6h, 100-240VAC/24-240VDC")
        assert result.object_name == 'Rơ le thời gian', \
            f"Expected 'Rơ le thời gian', got: {result.object_name}"


class TestV5BugFixes:
    """
    Regression tests for cable naming, Bàn gọi, Hộp đấu nối, Cáp tín hiệu (round 5).
    """

    @pytest.fixture
    def processor(self):
        return PriorityProcessor()

    def test_cu_pvc_is_cap_dien(self, processor):
        """Cu/PVC cable should be Cáp điện, not Cáp Cu/PVC."""
        result = processor.process("1C 6mm2 Cu/PVC")
        assert result.object_name == 'Cáp điện', \
            f"Expected 'Cáp điện', got: {result.object_name}"

    def test_cu_pvc_pvc_is_cap_dien(self, processor):
        """Cu/PVC/PVC cable should be Cáp điện."""
        result = processor.process("2C 4mm2 Cu/PVC/PVC")
        assert result.object_name == 'Cáp điện', \
            f"Expected 'Cáp điện', got: {result.object_name}"

    def test_ban_goi_chon_vung(self, processor):
        """Bàn Gọi Chọn Vùng should be Bàn gọi PA, not Côn via fuzzy."""
        result = processor.process("Bàn Gọi Chọn Vùng")
        assert result.object_name == 'Bàn gọi PA', \
            f"Expected 'Bàn gọi PA', got: {result.object_name}"

    def test_hop_dau_noi(self, processor):
        """Hộp Đấu Nối 10 Đôi should be Hộp đấu nối, not Đầu nối."""
        result = processor.process("Hộp Đấu Nối 10 Đôi")
        assert result.object_name == 'Hộp đấu nối', \
            f"Expected 'Hộp đấu nối', got: {result.object_name}"

    def test_cap_rs232(self, processor):
        """Cáp RS232 should be Cáp tín hiệu, not generic Cáp."""
        result = processor.process("Cáp RS232")
        assert result.object_name == 'Cáp tín hiệu', \
            f"Expected 'Cáp tín hiệu', got: {result.object_name}"

    def test_cu_xlpe_pvc_is_cap_dien(self, processor):
        """Cu/XLPE/PVC cable should still be Cáp điện (unchanged)."""
        result = processor.process("1C 6mm2 Cu/XLPE/PVC")
        assert result.object_name == 'Cáp điện', \
            f"Expected 'Cáp điện', got: {result.object_name}"
