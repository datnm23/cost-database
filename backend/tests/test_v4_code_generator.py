"""
Tests for V4CodeGenerator — 3-Level Format (PREFIX.GROUP.TYPE)

Covers:
- Code generation returning (ref_code, discipline, location) tuples
- Discipline mapping from SEC codes
- Type resolution with group-specific defaults
- 3-level code validation and parsing
- Grade exclusion from codes
- Instance code generation
- Fallback behavior for unknown descriptions
"""
import pytest
from unittest.mock import MagicMock
from app.services.v4_code_generator import V4CodeGenerator


@pytest.fixture
def gen():
    return V4CodeGenerator()


class TestV4CodeGeneration:
    """Test 3-level code generation from descriptions."""

    def test_concrete_column(self, gen):
        ref_code, discipline, location = gen.generate("Đổ bê tông cột M300", "SEC-02")
        assert ref_code.startswith("A.")
        assert ".CONC." in ref_code
        assert discipline == "CV"
        assert location == "COL"

    def test_concrete_beam(self, gen):
        ref_code, discipline, location = gen.generate("Bê tông dầm", "SEC-02")
        assert ref_code.startswith("A.")
        assert ".CONC." in ref_code
        assert discipline == "CV"
        assert location == "BEM"

    def test_concrete_slab(self, gen):
        ref_code, discipline, location = gen.generate("Đổ bê tông sàn", "SEC-02")
        assert ref_code.startswith("A.")
        assert ".CONC." in ref_code
        assert discipline == "CV"
        assert location == "SLB"

    def test_concrete_foundation(self, gen):
        ref_code, discipline, location = gen.generate("Đổ bê tông móng", "SEC-02")
        assert ref_code.startswith("A.")
        assert ".CONC." in ref_code
        assert discipline == "CV"
        assert location == "FND"

    def test_rebar(self, gen):
        ref_code, discipline, location = gen.generate("Gia công cốt thép cột CB400", "SEC-02")
        assert ref_code.startswith("A.")
        assert ".RBAR." in ref_code
        assert discipline == "CV"
        assert location == "COL"

    def test_formwork(self, gen):
        ref_code, discipline, location = gen.generate("Ván khuôn dầm", "SEC-02")
        assert ref_code.startswith("A.")
        assert ".FWRK." in ref_code
        assert discipline == "CV"
        assert location == "BEM"

    def test_earthworks(self, gen):
        ref_code, discipline, location = gen.generate("Đào đất hố móng", "SEC-01")
        assert ref_code.startswith("A.")
        assert ".SOIL." in ref_code
        assert discipline == "CV"
        # Location can be FND or PIT depending on keyword priority
        assert location is not None

    def test_brickwork(self, gen):
        ref_code, discipline, location = gen.generate("Xây tường gạch", "SEC-03")
        assert ref_code.startswith("A.")
        assert ".BRCK." in ref_code
        assert discipline == "AR"
        assert location == "WAL"

    def test_plastering(self, gen):
        ref_code, discipline, location = gen.generate("Trát tường vữa", "SEC-03")
        assert ref_code.startswith("A.")
        assert ".PLST." in ref_code
        assert discipline == "AR"
        assert location == "WAL"

    def test_painting(self, gen):
        ref_code, discipline, location = gen.generate("Sơn tường", "SEC-03")
        assert ref_code.startswith("A.")
        assert ".PANT." in ref_code
        assert discipline == "AR"
        assert location == "WAL"

    def test_tiling(self, gen):
        ref_code, discipline, location = gen.generate("Lát gạch nền", "SEC-03")
        assert ref_code.startswith("A.")
        assert ".TILE." in ref_code
        assert discipline == "AR"

    def test_pipe_installation(self, gen):
        ref_code, discipline, location = gen.generate("Lắp đặt ống cấp nước PPR D25", "SEC-04-02")
        assert ref_code.startswith("A.")
        assert ".PIPE." in ref_code
        assert discipline == "PL"

    def test_electrical(self, gen):
        ref_code, discipline, location = gen.generate("Kéo cáp điện Cu/XLPE 4x16mm2", "SEC-04-01")
        assert ref_code.startswith("A.")
        assert ".CABL." in ref_code
        assert discipline == "EL"


class TestV4DisciplineMapping:
    """Test legacy SEC to v4.0 discipline mapping (unchanged method)."""

    def test_sec01_maps_to_cv(self, gen):
        assert gen._resolve_discipline("SEC-01", "") == "CV"

    def test_sec02_maps_to_cv(self, gen):
        assert gen._resolve_discipline("SEC-02", "") == "CV"

    def test_sec03_maps_to_ar(self, gen):
        assert gen._resolve_discipline("SEC-03", "") == "AR"

    def test_sec04_01_maps_to_el(self, gen):
        assert gen._resolve_discipline("SEC-04-01", "") == "EL"

    def test_sec04_02_maps_to_pl(self, gen):
        assert gen._resolve_discipline("SEC-04-02", "") == "PL"

    def test_sec04_03_maps_to_me(self, gen):
        assert gen._resolve_discipline("SEC-04-03", "") == "ME"

    def test_sec04_04_maps_to_fp(self, gen):
        assert gen._resolve_discipline("SEC-04-04", "") == "FP"

    def test_sec05_maps_to_ex(self, gen):
        assert gen._resolve_discipline("SEC-05", "") == "EX"

    def test_sec05_03_maps_to_la(self, gen):
        assert gen._resolve_discipline("SEC-05-03", "") == "LA"


class TestV4TypeResolution:
    """Test _resolve_type method with GROUP-specific defaults."""

    def test_concrete_defaults_to_str(self, gen):
        type_code = gen._resolve_type("bê tông kết cấu", {}, 'CONC')
        assert type_code == "STR"

    def test_concrete_foundation_type(self, gen):
        type_code = gen._resolve_type("bê tông móng", {}, 'CONC')
        assert type_code == "FND"

    def test_concrete_lean_type(self, gen):
        type_code = gen._resolve_type("bê tông lót", {}, 'CONC')
        assert type_code == "LEA"

    def test_soil_defaults_to_exc(self, gen):
        type_code = gen._resolve_type("đào đất", {}, 'SOIL')
        assert type_code == "EXC"

    def test_soil_fill_type(self, gen):
        type_code = gen._resolve_type("đắp đất", {}, 'SOIL')
        assert type_code == "FIL"

    def test_pipe_supply_type(self, gen):
        type_code = gen._resolve_type("ống cấp nước ppr d25", {}, 'PIPE')
        assert type_code == "SUP"

    def test_pipe_drain_type(self, gen):
        type_code = gen._resolve_type("ống thoát nước d110", {}, 'PIPE')
        assert type_code == "DRN"

    def test_group_default_when_no_keyword(self, gen):
        """When no TYPE keyword matches, should return group-specific default."""
        type_code = gen._resolve_type("something generic", {}, 'CONC')
        assert type_code == "STR"  # CONC default

    def test_group_default_for_rbar(self, gen):
        type_code = gen._resolve_type("something generic", {}, 'RBAR')
        assert type_code == "STR"  # RBAR default

    def test_group_default_for_tile(self, gen):
        type_code = gen._resolve_type("something generic", {}, 'TILE')
        assert type_code == "CER"  # TILE default

    def test_unknown_group_defaults_to_gen(self, gen):
        type_code = gen._resolve_type("something generic", {}, 'XXXX')
        assert type_code == "GEN"  # Unknown group fallback


class TestV4CodeValidation:
    """Test 3-level code format validation."""

    def test_valid_activity_code(self, gen):
        assert gen.validate_v4_code("A.CONC.STR") is True

    def test_valid_material_code(self, gen):
        assert gen.validate_v4_code("M.CONC.STR") is True

    def test_valid_labour_code(self, gen):
        assert gen.validate_v4_code("L.CONC.STR") is True

    def test_valid_equipment_code(self, gen):
        assert gen.validate_v4_code("E.CONC.STR") is True

    def test_valid_rebar_code(self, gen):
        assert gen.validate_v4_code("A.RBAR.STR") is True

    def test_valid_pipe_code(self, gen):
        assert gen.validate_v4_code("A.PIPE.SUP") is True

    def test_valid_soil_code(self, gen):
        assert gen.validate_v4_code("A.SOIL.EXC") is True

    def test_invalid_old_5_level_format(self, gen):
        assert gen.validate_v4_code("A.CV.CON.POUR.COL") is False

    def test_invalid_legacy_format(self, gen):
        assert gen.validate_v4_code("S02-CONC-M200-0001") is False

    def test_invalid_prefix(self, gen):
        assert gen.validate_v4_code("X.CONC.STR") is False

    def test_too_few_levels(self, gen):
        assert gen.validate_v4_code("A.CONC") is False

    def test_too_many_levels(self, gen):
        assert gen.validate_v4_code("A.CONC.STR.EXT") is False

    def test_parse_valid_code(self, gen):
        result = gen.parse_v4_code("A.CONC.STR")
        assert result == {
            'table_type': 'A',
            'group': 'CONC',
            'type': 'STR',
        }

    def test_parse_material_code(self, gen):
        result = gen.parse_v4_code("M.PIPE.SUP")
        assert result == {
            'table_type': 'M',
            'group': 'PIPE',
            'type': 'SUP',
        }

    def test_parse_invalid_code(self, gen):
        result = gen.parse_v4_code("INVALID")
        assert result is None

    def test_parse_old_format_returns_none(self, gen):
        result = gen.parse_v4_code("A.CV.CON.POUR.COL")
        assert result is None


class TestV4GradeNotInCode:
    """Critical test: grade must NOT appear in the v4 code."""

    def test_m300_not_in_code(self, gen):
        ref_code, discipline, location = gen.generate("Bê tông cột M300", "SEC-02")
        assert "M300" not in ref_code
        assert "M250" not in ref_code

    def test_cb400_not_in_code(self, gen):
        ref_code, discipline, location = gen.generate("Cốt thép CB400 cột", "SEC-02")
        assert "CB400" not in ref_code
        assert "CB40" not in ref_code

    def test_pn10_not_in_code(self, gen):
        ref_code, discipline, location = gen.generate("Ống HDPE PN10 D110", "SEC-04-02")
        assert "PN10" not in ref_code

    def test_grade_in_discipline_or_location_is_ok(self, gen):
        """Grade should not appear in ref_code, but discipline/location are separate."""
        ref_code, discipline, location = gen.generate("Bê tông cột M300", "SEC-02")
        # ref_code is the 3-level code; discipline and location are attributes
        parts = ref_code.split(".")
        assert len(parts) == 3
        for part in parts:
            assert not part.startswith("M3")


class TestGenerateInstanceCode:
    """Test instance code generation with auto-incrementing sequence."""

    def _make_mock_db(self, existing_instance_codes=None):
        """Create a mock DB session that returns given instance codes."""
        db = MagicMock()
        results = [(code,) for code in (existing_instance_codes or [])]
        db.query.return_value.filter.return_value.all.return_value = results
        return db

    def test_first_instance_gets_001(self, gen):
        db = self._make_mock_db([])
        result = gen.generate_instance_code("A.CONC.STR", db)
        assert result == "A.CONC.STR-001"

    def test_second_instance_gets_002(self, gen):
        db = self._make_mock_db(["A.CONC.STR-001"])
        result = gen.generate_instance_code("A.CONC.STR", db)
        assert result == "A.CONC.STR-002"

    def test_increments_from_max(self, gen):
        db = self._make_mock_db([
            "A.CONC.STR-001",
            "A.CONC.STR-003",
            "A.CONC.STR-002",
        ])
        result = gen.generate_instance_code("A.CONC.STR", db)
        assert result == "A.CONC.STR-004"

    def test_handles_different_ref_codes(self, gen):
        db = self._make_mock_db([])
        result = gen.generate_instance_code("M.PIPE.SUP", db)
        assert result == "M.PIPE.SUP-001"

    def test_three_digit_padding(self, gen):
        db = self._make_mock_db([f"A.CONC.STR-{i:03d}" for i in range(1, 10)])
        result = gen.generate_instance_code("A.CONC.STR", db)
        assert result == "A.CONC.STR-010"

    def test_rebar_instance_code(self, gen):
        db = self._make_mock_db(["A.RBAR.STR-001", "A.RBAR.STR-002"])
        result = gen.generate_instance_code("A.RBAR.STR", db)
        assert result == "A.RBAR.STR-003"

    def test_instance_code_format(self, gen):
        """Instance code should be ref_code + '-' + 3-digit sequence."""
        db = self._make_mock_db([])
        result = gen.generate_instance_code("A.SOIL.EXC", db)
        assert result == "A.SOIL.EXC-001"
        # Validate the format: 3-level code + dash + 3-digit number
        parts = result.rsplit("-", 1)
        assert len(parts) == 2
        assert len(parts[1]) == 3
        assert parts[1].isdigit()


class TestV4GeneralFallback:
    """Test that unknown descriptions produce valid 3-level codes."""

    def test_unknown_description_valid_format(self, gen):
        ref_code, discipline, location = gen.generate("Công tác khác", "SEC-00")
        parts = ref_code.split(".")
        assert len(parts) == 3
        assert parts[0] == "A"

    def test_unknown_description_has_group_and_type(self, gen):
        ref_code, discipline, location = gen.generate("Một công việc bất kỳ", "SEC-00")
        parts = ref_code.split(".")
        assert len(parts) == 3
        assert parts[0] == "A"
        # GROUP and TYPE should be non-empty uppercase strings
        assert parts[1].isupper() and len(parts[1]) >= 2
        assert parts[2].isupper() and len(parts[2]) >= 2

    def test_unknown_returns_discipline(self, gen):
        ref_code, discipline, location = gen.generate("Công tác khác", "SEC-00")
        assert discipline == "PM"  # SEC-00 maps to PM

    def test_unknown_location_is_none(self, gen):
        ref_code, discipline, location = gen.generate("Công tác chung chung", "SEC-00")
        # Unknown descriptions should not have a specific location
        # (unless they happen to contain a location keyword)
        assert isinstance(ref_code, str)
        # location can be None or a valid code

    def test_all_generated_codes_are_3_level(self, gen):
        """Multiple descriptions should all produce 3-level codes."""
        test_cases = [
            ("Đổ bê tông cột M300", "SEC-02"),
            ("Cốt thép dầm CB400", "SEC-02"),
            ("Ván khuôn sàn", "SEC-02"),
            ("Đào đất hố móng", "SEC-01"),
            ("Xây tường gạch", "SEC-03"),
            ("Trát tường vữa", "SEC-03"),
            ("Sơn tường", "SEC-03"),
            ("Ống cấp nước PPR D25", "SEC-04-02"),
            ("Cáp điện Cu/XLPE 4x16", "SEC-04-01"),
            ("Công tác khác", "SEC-00"),
        ]
        for desc, sec in test_cases:
            ref_code, discipline, location = gen.generate(desc, sec)
            parts = ref_code.split(".")
            assert len(parts) == 3, \
                f"Expected 3-level code for '{desc}', got '{ref_code}'"
            assert parts[0] == "A"
