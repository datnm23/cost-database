"""
Tests for the Master Resource Dictionary and Dictionary-Based Assembler.

These tests verify that the data-driven assembly produces identical
output to the original if-else based _assemble() method.
"""

import pytest
from app.services.dictionary_assembler import (
    DictionaryBasedAssembler,
    get_assembler,
    assemble_with_dictionary,
)
from app.services.dictionaries.master_resource import (
    MASTER_RESOURCE_DICTIONARY,
    get_config,
)
from app.services.dictionaries.field_mappings import ObjectConfig, FieldMapping
from app.services.dictionaries.transforms import TRANSFORMS


class TestFieldMappings:
    """Test the schema classes."""

    def test_field_mapping_defaults(self):
        """FieldMapping should have sensible defaults."""
        mapping = FieldMapping()
        assert mapping.source == "default"
        assert mapping.fallback == "Theo thiết kế"
        assert mapping.key is None
        assert mapping.transform is None

    def test_object_config_defaults(self):
        """ObjectConfig should have sensible defaults."""
        config = ObjectConfig(object_name="Test")
        assert config.object_name == "Test"
        assert config.extractor is None
        assert config.output_object is None
        assert config.part1.source == "object_name"
        assert config.aliases == []


class TestTransforms:
    """Test transform functions."""

    def test_combine_electrical_specs(self):
        """Should combine amps and breaking capacity."""
        specs = {'amps': '400A', 'breaking_capacity': '36kA'}
        result = TRANSFORMS['combine_electrical_specs'](specs, '')
        assert result == '400A 36kA'

    def test_combine_electrical_specs_empty(self):
        """Should return fallback when no specs."""
        result = TRANSFORMS['combine_electrical_specs']({}, '')
        assert result == 'Theo thiết kế'

    def test_extract_busbar_material_dong(self):
        """Should extract Đồng material."""
        result = TRANSFORMS['extract_busbar_material']({}, 'Thanh cái đồng 400A')
        assert result == 'Đồng'

    def test_extract_busbar_material_nhom(self):
        """Should extract Nhôm material."""
        result = TRANSFORMS['extract_busbar_material']({}, 'Thanh cái nhôm')
        assert result == 'Nhôm'

    def test_extract_colors(self):
        """Should extract color list."""
        result = TRANSFORMS['extract_colors']({}, 'Đèn báo pha đỏ, vàng, xanh')
        assert 'Đỏ' in result
        assert 'Vàng' in result
        assert 'Xanh' in result

    def test_combine_layer_compaction(self):
        """Should combine layer and compaction."""
        specs = {'compaction': 'K98'}
        result = TRANSFORMS['combine_layer_compaction'](specs, 'CPĐD lớp dưới K98')
        assert 'K98' in result

    def test_determine_earth_source_tan_dung(self):
        """Should detect Tận dụng source."""
        result = TRANSFORMS['determine_earth_source']({}, 'Đắp đất, cát K95')
        assert result == 'Tận dụng'

    def test_determine_earth_source_mua_moi(self):
        """Should default to Mua mới."""
        result = TRANSFORMS['determine_earth_source']({}, 'Đắp đất nền K95')
        assert result == 'Mua mới'


class TestMasterResourceDictionary:
    """Test the master resource dictionary structure."""

    def test_dictionary_has_electrical_objects(self):
        """Dictionary should contain electrical objects."""
        assert 'MCCB' in MASTER_RESOURCE_DICTIONARY
        assert 'MCB' in MASTER_RESOURCE_DICTIONARY
        assert 'RCCB' in MASTER_RESOURCE_DICTIONARY
        assert 'ACB' in MASTER_RESOURCE_DICTIONARY

    def test_dictionary_has_road_objects(self):
        """Dictionary should contain road construction objects."""
        assert 'Móng đường' in MASTER_RESOURCE_DICTIONARY
        assert 'Mặt đường' in MASTER_RESOURCE_DICTIONARY
        assert 'Tưới nhựa' in MASTER_RESOURCE_DICTIONARY

    def test_dictionary_has_earthwork_objects(self):
        """Dictionary should contain earthwork objects."""
        assert 'Đào đất' in MASTER_RESOURCE_DICTIONARY
        assert 'Đắp đất' in MASTER_RESOURCE_DICTIONARY
        assert 'Vận chuyển' in MASTER_RESOURCE_DICTIONARY

    def test_dictionary_has_pipe_fittings(self):
        """Dictionary should contain pipe fittings."""
        assert 'Cút' in MASTER_RESOURCE_DICTIONARY
        assert 'Tê' in MASTER_RESOURCE_DICTIONARY
        assert 'Côn' in MASTER_RESOURCE_DICTIONARY

    def test_get_config_found(self):
        """get_config should return config for known object."""
        config = get_config('MCCB')
        assert config is not None
        assert config.object_name == 'MCCB'

    def test_get_config_not_found(self):
        """get_config should return None for unknown object."""
        config = get_config('Unknown Object')
        assert config is None


class TestDictionaryBasedAssembler:
    """Test the dictionary-based assembler."""

    @pytest.fixture
    def assembler(self):
        return DictionaryBasedAssembler()

    def test_assemble_mccb(self, assembler):
        """Should assemble MCCB correctly."""
        specs = {'poles': '3P', 'amps': '400A', 'breaking_capacity': '36kA'}
        result = assembler.assemble('MCCB', specs, 'MCCB-3P-400A-36kA')

        assert result == 'MCCB - 3P - 400A 36kA'

    def test_assemble_mcb(self, assembler):
        """Should assemble MCB correctly."""
        specs = {'poles': '2P', 'amps': '32A', 'breaking_capacity': '6kA'}
        result = assembler.assemble('MCB', specs, 'MCB 2P 32A 6kA')

        assert result == 'MCB - 2P - 32A 6kA'

    def test_assemble_mong_duong_with_k98(self, assembler):
        """Should preserve K98 in Móng đường output."""
        specs = {'material': 'CPĐD', 'compaction': 'K98'}
        result = assembler.assemble('Móng đường', specs, 'Móng đường CPĐD lớp dưới K98')

        assert 'K98' in result
        assert 'CPĐD' in result

    def test_assemble_van_khuon(self, assembler):
        """Should assemble Ván khuôn with 3 components."""
        specs = {'position': 'Móng'}
        result = assembler.assemble('Ván khuôn', specs, 'Ván khuôn móng')

        parts = result.split(' - ')
        assert len(parts) == 3
        assert parts[0] == 'Ván khuôn'
        assert 'Móng' in parts[1] or 'Móng' in result

    def test_assemble_tu_gom_cong_to(self, assembler):
        """Should transform Tủ gom công tơ to Tủ điện with 2 components."""
        specs = {}
        result = assembler.assemble('Tủ gom công tơ', specs, 'Tủ gom công tơ')

        parts = result.split(' - ')
        assert len(parts) == 2
        assert parts[0] == 'Tủ điện'
        assert parts[1] == 'Tủ gom công tơ'

    def test_assemble_thanh_cai(self, assembler):
        """Should assemble Thanh cái with material."""
        specs = {}
        result = assembler.assemble('Thanh cái', specs, 'Thanh cái đồng')

        parts = result.split(' - ')
        assert len(parts) == 3
        assert parts[0] == 'Thanh cái'
        assert 'Đồng' in result

    def test_assemble_den_tin_hieu(self, assembler):
        """Should assemble Đèn tín hiệu with 3 components."""
        specs = {}
        result = assembler.assemble('Đèn tín hiệu', specs, 'Đèn tín hiệu báo pha đỏ')

        parts = result.split(' - ')
        assert len(parts) == 3
        assert parts[0] == 'Đèn tín hiệu'

    def test_assemble_cot_thep(self, assembler):
        """Should assemble Cốt thép with 3 components."""
        specs = {}
        result = assembler.assemble('Cốt thép', specs, 'Cốt thép')

        parts = result.split(' - ')
        assert len(parts) == 3
        assert parts[0] == 'Cốt thép'

    def test_assemble_cot_thep_with_diameter(self, assembler):
        """Should include diameter for Cốt thép."""
        specs = {'diameter': 'D12'}
        result = assembler.assemble('Cốt thép', specs, 'Cốt thép D12')

        assert 'D12' in result

    def test_assemble_unknown_object(self, assembler):
        """Should use generic assembly for unknown objects."""
        specs = {'material': 'Thép', 'dimensions': '100x50'}
        result = assembler.assemble('Unknown Object', specs, 'Unknown Object')

        parts = result.split(' - ')
        assert len(parts) == 3
        assert parts[0] == 'Unknown Object'

    def test_enforce_three_components_empty(self, assembler):
        """Empty parts should return empty string."""
        result = assembler._enforce_three_components([])
        assert result == ""

    def test_enforce_three_components_one(self, assembler):
        """One part should get two defaults."""
        result = assembler._enforce_three_components(['Object'])
        assert result == 'Object - Theo thiết kế - Theo thiết kế'

    def test_enforce_three_components_two(self, assembler):
        """Two parts should get one default."""
        result = assembler._enforce_three_components(['Object', 'Material'])
        assert result == 'Object - Material - Theo thiết kế'

    def test_enforce_three_components_three(self, assembler):
        """Three parts should be joined correctly."""
        result = assembler._enforce_three_components(['Object', 'Material', 'Specs'])
        assert result == 'Object - Material - Specs'

    def test_enforce_three_components_four(self, assembler):
        """Four parts should merge middle parts."""
        result = assembler._enforce_three_components(['A', 'B', 'C', 'D'])
        assert result == 'A - B C - D'


class TestAssemblerSingleton:
    """Test singleton and convenience functions."""

    def test_get_assembler_singleton(self):
        """Should return same instance."""
        a1 = get_assembler()
        a2 = get_assembler()
        assert a1 is a2

    def test_assemble_with_dictionary_function(self):
        """Convenience function should work."""
        specs = {'poles': '3P', 'amps': '400A', 'breaking_capacity': '36kA'}
        result = assemble_with_dictionary('MCCB', specs, 'MCCB-3P-400A-36kA')

        assert result == 'MCCB - 3P - 400A 36kA'


class TestRegressionAgainstOriginal:
    """
    Regression tests to verify dictionary-based assembly matches original.

    These tests compare output from the new assembler against expected
    output from the original _assemble() method.
    """

    @pytest.fixture
    def assembler(self):
        return DictionaryBasedAssembler()

    def test_regression_mccb_3p_400a_36ka(self, assembler):
        """MCCB-3P-400A-36kA should produce MCCB - 3P - 400A 36kA."""
        specs = {'poles': '3P', 'amps': '400A', 'breaking_capacity': '36kA'}
        result = assembler.assemble('MCCB', specs, 'MCCB-3P-400A-36kA')
        assert result == 'MCCB - 3P - 400A 36kA'

    def test_regression_van_khuon_mong(self, assembler):
        """Ván khuôn móng should have 3 components with Theo thiết kế."""
        specs = {'position': 'Móng'}
        result = assembler.assemble('Ván khuôn', specs, 'Ván khuôn móng bê tông M200')

        parts = result.split(' - ')
        assert len(parts) == 3
        assert parts[0] == 'Ván khuôn'
        assert 'Theo thiết kế' in result

    def test_regression_mong_duong_cpdd_k98(self, assembler):
        """Móng đường CPĐD K98 should preserve K98."""
        specs = {'material': 'CPĐD', 'compaction': 'K98', 'layer': 'Lớp dưới'}
        result = assembler.assemble('Móng đường', specs, 'Móng đường CPĐD lớp dưới K98')

        assert 'K98' in result
        assert 'Móng đường' in result
        assert 'CPĐD' in result

    def test_regression_tu_gom_cong_to(self, assembler):
        """Tủ gom công tơ should become Tủ điện - Tủ gom công tơ (2 parts)."""
        specs = {}
        result = assembler.assemble('Tủ gom công tơ', specs, 'Tủ gom công tơ')

        parts = result.split(' - ')
        assert len(parts) == 2
        assert parts[0] == 'Tủ điện'
        assert parts[1] == 'Tủ gom công tơ'

    def test_regression_thanh_cai_dong(self, assembler):
        """Thanh cái đồng should have 3 components."""
        specs = {}
        result = assembler.assemble('Thanh cái', specs, 'Thanh cái đồng')

        parts = result.split(' - ')
        assert len(parts) == 3
        assert parts[0] == 'Thanh cái'
        assert 'Đồng' in result

    def test_regression_cot_thep(self, assembler):
        """Cốt thép should have 3 components."""
        specs = {}
        result = assembler.assemble('Cốt thép', specs, 'Cốt thép')

        parts = result.split(' - ')
        assert len(parts) == 3
        assert parts[0] == 'Cốt thép'

    def test_regression_den_tin_hieu(self, assembler):
        """Đèn tín hiệu should have 3 components."""
        specs = {}
        result = assembler.assemble('Đèn tín hiệu', specs, 'Đèn tín hiệu giao thông')

        parts = result.split(' - ')
        assert len(parts) == 3
        assert parts[0] == 'Đèn tín hiệu'

    def test_all_outputs_have_expected_components(self, assembler):
        """Dictionary-based outputs should have expected number of components."""
        # Most have 3 components (2 dashes), some have 2 components (1 dash)
        test_cases = [
            ('MCCB', {'poles': '3P', 'amps': '400A'}, 'MCCB 3P 400A', 2),
            ('MCB', {'poles': '2P'}, 'MCB 2P', 2),
            ('Ván khuôn', {'position': 'Móng'}, 'Ván khuôn móng', 2),
            ('Móng đường', {'material': 'CPĐD'}, 'Móng đường CPĐD', 2),
            ('Thanh cái', {}, 'Thanh cái đồng', 2),
            ('Đèn tín hiệu', {}, 'Đèn tín hiệu', 2),
            ('Cốt thép', {}, 'Cốt thép', 2),
            ('Tủ gom công tơ', {}, 'Tủ gom công tơ', 1),  # Only 2 components
            ('Bê tông', {'grade': 'M250'}, 'Bê tông M250', 2),
            ('Đào đất', {'soil_type': 'Đất cấp 3'}, 'Đào đất', 2),
        ]

        for obj_name, specs, original, expected_dashes in test_cases:
            result = assembler.assemble(obj_name, specs, original)
            if result:  # Skip empty results
                dash_count = result.count(' - ')
                assert dash_count == expected_dashes, \
                    f"'{obj_name}' → '{result}' has {dash_count} dashes, expected {expected_dashes}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
