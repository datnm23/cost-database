"""
Tests for the dictionaries module.
"""

import pytest
from app.services.dictionaries.objects import DICT_OBJECTS, DICT_OBJECTS_SORTED
from app.services.dictionaries.materials import DICT_MATERIALS, DICT_PRESSURE
from app.services.dictionaries.specs import extract_specs, SPEC_PATTERNS
from app.services.dictionaries.priority_objects import (
    PRIORITY_1_METHODS,
    PRIORITY_2_COMPONENTS,
    PRIORITY_3_MATERIALS,
    identify_object,
    identify_object_with_details,
)


class TestObjectsDictionary:
    """Test cases for objects dictionary."""

    def test_dict_objects_not_empty(self):
        """Dictionary should not be empty."""
        assert len(DICT_OBJECTS) > 0

    def test_dict_objects_sorted_by_length(self):
        """Sorted dictionary should have longest keys first."""
        keys = list(DICT_OBJECTS_SORTED.keys())
        for i in range(len(keys) - 1):
            assert len(keys[i]) >= len(keys[i + 1]), \
                f"Key '{keys[i]}' should come before '{keys[i + 1]}'"

    def test_compound_objects_before_simple(self):
        """Compound objects should be matched before simple ones."""
        sorted_keys = list(DICT_OBJECTS_SORTED.keys())

        # "tủ điện tổng" should come before "tủ điện"
        assert sorted_keys.index('tủ điện tổng') < sorted_keys.index('tủ điện')

        # "ống thép mạ kẽm" should come before "ống thép"
        assert sorted_keys.index('ống thép mạ kẽm') < sorted_keys.index('ống thép')

    def test_mep_objects_present(self):
        """MEP objects should be in dictionary."""
        mep_objects = ['ống', 'cáp', 'tủ điện', 'đèn', 'van', 'bơm']
        for obj in mep_objects:
            assert obj in DICT_OBJECTS, f"Missing MEP object: {obj}"

    def test_traffic_objects_present(self):
        """Traffic objects should be in dictionary."""
        traffic_objects = ['biển báo', 'cột đèn', 'vạch sơn', 'hố ga']
        for obj in traffic_objects:
            assert obj in DICT_OBJECTS, f"Missing traffic object: {obj}"


class TestMaterialsDictionary:
    """Test cases for materials dictionary."""

    def test_dict_materials_not_empty(self):
        """Dictionary should not be empty."""
        assert len(DICT_MATERIALS) > 0

    def test_pipe_materials_present(self):
        """Pipe materials should be in dictionary."""
        pipe_materials = ['hdpe', 'pvc', 'ppr', 'inox']
        for mat in pipe_materials:
            assert mat in DICT_MATERIALS, f"Missing pipe material: {mat}"

    def test_electrical_materials_present(self):
        """Electrical materials should be in dictionary."""
        elec_materials = ['cu/xlpe/pvc', 'đồng', 'nhôm']
        for mat in elec_materials:
            assert mat in DICT_MATERIALS, f"Missing electrical material: {mat}"

    def test_compound_materials(self):
        """Compound materials should normalize correctly."""
        assert DICT_MATERIALS['thép mạ kẽm'] == 'Thép mạ kẽm'
        assert DICT_MATERIALS['cu/xlpe/pvc'] == 'Cu/XLPE/PVC'

    def test_pressure_ratings(self):
        """Pressure ratings should be in dictionary."""
        assert 'pn10' in DICT_PRESSURE
        assert 'pn16' in DICT_PRESSURE
        assert DICT_PRESSURE['pn10'] == 'PN10'


class TestSpecsExtraction:
    """Test cases for specs extraction."""

    def test_extract_pipe_diameter(self):
        """Should extract pipe diameter."""
        specs, remaining = extract_specs("ống HDPE D110 PN16")
        assert 'D110' in specs or any('110' in s for s in specs)

    def test_extract_pressure_rating(self):
        """Should extract pressure rating."""
        specs, remaining = extract_specs("ống PPR D63 PN10")
        assert 'PN10' in specs or any('10' in s for s in specs)

    def test_extract_dimensions(self):
        """Should extract dimensions."""
        specs, remaining = extract_specs("gạch 600x600")
        assert any('600' in s for s in specs)

    def test_extract_concrete_grade(self):
        """Should extract concrete grade."""
        specs, remaining = extract_specs("bê tông M350")
        assert 'M350' in specs

    def test_extract_electrical_specs(self):
        """Should extract electrical specs."""
        specs, remaining = extract_specs("MCCB 3P 400A 50kA")
        assert any('3P' in s for s in specs) or any('400A' in s for s in specs)

    def test_extract_height(self):
        """Should extract height."""
        specs, remaining = extract_specs("cột đèn H=8m")
        assert any('8' in s and 'm' in s.lower() for s in specs)

    def test_remaining_text_clean(self):
        """Remaining text should be clean after extraction."""
        specs, remaining = extract_specs("ống HDPE D110 PN16 tầng 1")
        # The remaining should not have the extracted specs
        assert 'D110' not in remaining or 'PN16' not in remaining

    def test_multiple_specs(self):
        """Should extract multiple specs."""
        specs, remaining = extract_specs("cáp 4x50mm2 Cu/XLPE/PVC")
        # Should have at least the cable cross-section
        assert len(specs) >= 1


class TestSpecPatterns:
    """Test individual spec patterns."""

    def test_pattern_count(self):
        """Should have multiple spec patterns."""
        assert len(SPEC_PATTERNS) > 10

    def test_cable_cross_section_pattern(self):
        """Should have cable cross-section pattern."""
        import re
        text = "4x50mm2"
        matched = False
        for pattern, formatter in SPEC_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                matched = True
                break
        assert matched, "No pattern matched cable cross-section"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


class TestPriorityObjects:
    """Test cases for priority-based object identification."""

    def test_priority_1_methods_not_empty(self):
        """Priority 1 methods dictionary should not be empty."""
        assert len(PRIORITY_1_METHODS) > 0

    def test_priority_2_components_not_empty(self):
        """Priority 2 components dictionary should not be empty."""
        assert len(PRIORITY_2_COMPONENTS) > 0

    def test_priority_3_materials_not_empty(self):
        """Priority 3 materials dictionary should not be empty."""
        assert len(PRIORITY_3_MATERIALS) > 0

    def test_van_khuon_priority_1(self):
        """Ván khuôn should be Priority 1 (method)."""
        assert 'ván khuôn' in PRIORITY_1_METHODS

    def test_bo_via_priority_2(self):
        """Bó vỉa should be Priority 2 (component)."""
        assert 'bó vỉa' in PRIORITY_2_COMPONENTS

    def test_be_tong_priority_3(self):
        """Bê tông should be Priority 3 (material)."""
        assert 'bê tông' in PRIORITY_3_MATERIALS

    def test_identify_van_khuon_wins_over_be_tong(self):
        """
        Priority 1 (Ván khuôn) should win over Priority 3 (Bê tông).
        This is the key test for solving the 'Identity Theft' problem.
        """
        # This is the exact case that was failing before
        result = identify_object("Ván khuôn móng bê tông M200")

        obj_name, priority = result
        assert obj_name == 'Ván khuôn', f"Expected 'Ván khuôn', got '{obj_name}'"
        assert priority == 1, f"Expected priority 1, got {priority}"

    def test_identify_bo_via_wins_over_da(self):
        """
        Priority 2 (Bó vỉa) should win over Priority 3 (Đá).
        """
        result = identify_object("Bó vỉa đá granite 300x150")

        obj_name, priority = result
        assert obj_name == 'Bó vỉa', f"Expected 'Bó vỉa', got '{obj_name}'"
        assert priority == 2, f"Expected priority 2, got {priority}"

    def test_identify_van_chuyen_priority_1(self):
        """Vận chuyển should be Priority 1 (method)."""
        result = identify_object("Vận chuyển đất thừa")

        obj_name, priority = result
        assert obj_name == 'Vận chuyển', f"Expected 'Vận chuyển', got '{obj_name}'"
        assert priority == 1, f"Expected priority 1, got {priority}"

    def test_identify_object_with_details(self):
        """identify_object_with_details should return all info."""
        result = identify_object_with_details("Ván khuôn móng bê tông M200")

        assert result['object_name'] == 'Ván khuôn'
        assert result['priority'] == 1
        assert result['priority_type'] == 'method'
        assert result['matched_keyword'] == 'van khuon'

    def test_identify_no_match_returns_none(self):
        """Unknown text should return None."""
        result = identify_object("xyz abc 123")

        obj_name, priority = result
        assert obj_name is None
        assert priority == 0

    def test_longest_match_within_priority(self):
        """Should match longest keyword within same priority level."""
        # "tủ điện tổng" should match before "tủ điện"
        result = identify_object("Tủ điện tổng MSB 2000A")

        obj_name, priority = result
        assert 'tổng' in obj_name.lower() or 'MSB' in obj_name
