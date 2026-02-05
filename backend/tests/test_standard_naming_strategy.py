"""
Tests for Standard Naming Strategy implementation.

Nguyên tắc cốt lõi: "DANH TỪ TRƯỚC - THÔNG SỐ SAU"
Cấu trúc mới: [TÊN ĐỐI TƯỢNG] - [CHẤT LIỆU/BIẾN THỂ] - [THÔNG SỐ KỸ THUẬT]

3 Quy tắc "Làm Sạch":
1. Cắt bỏ động từ phụ trợ (Cung cấp, Lắp đặt, Thi công...)
2. Tách vị trí ra field riêng (location)
3. Quy đổi đơn vị về mm
"""
import pytest
from app.services.description_normalizer import DescriptionNormalizer
from app.services.normalization_orchestrator import NormalizationOrchestrator
from app.services.mep_equipment_normalizer import MEPEquipmentNormalizer
from app.services.traffic_equipment_normalizer import TrafficEquipmentNormalizer


class TestVerbStripping:
    """Test Rule 1: Strip auxiliary verbs, keep characteristic verbs"""

    def setup_method(self):
        self.normalizer = DescriptionNormalizer()

    def test_should_strip_cung_cap(self):
        """'Cung cấp' should be stripped"""
        assert self.normalizer.should_strip_verb('Cung cấp') is True
        assert self.normalizer.should_strip_verb('cung cấp') is True

    def test_should_strip_lap_dat(self):
        """'Lắp đặt' should be stripped"""
        assert self.normalizer.should_strip_verb('Lắp đặt') is True
        assert self.normalizer.should_strip_verb('lắp đặt') is True

    def test_should_strip_thi_cong(self):
        """'Thi công' should be stripped"""
        assert self.normalizer.should_strip_verb('Thi công') is True
        assert self.normalizer.should_strip_verb('thi công') is True

    def test_should_strip_san_xuat(self):
        """'Sản xuất' should be stripped"""
        assert self.normalizer.should_strip_verb('Sản xuất') is True

    def test_should_strip_gia_cong(self):
        """'Gia công' should be stripped"""
        assert self.normalizer.should_strip_verb('Gia công') is True

    def test_should_strip_van_chuyen(self):
        """'Vận chuyển' should be stripped"""
        assert self.normalizer.should_strip_verb('Vận chuyển') is True

    def test_should_keep_dao(self):
        """'Đào' should be kept (earthwork characteristic)"""
        assert self.normalizer.should_strip_verb('Đào') is False
        assert self.normalizer.should_strip_verb('đào') is False

    def test_should_keep_dap(self):
        """'Đắp' should be kept (earthwork characteristic)"""
        assert self.normalizer.should_strip_verb('Đắp') is False
        assert self.normalizer.should_strip_verb('đắp') is False

    def test_should_keep_xay(self):
        """'Xây' should be kept (finishing characteristic)"""
        assert self.normalizer.should_strip_verb('Xây') is False
        assert self.normalizer.should_strip_verb('xây') is False

    def test_should_keep_trat(self):
        """'Trát' should be kept (finishing characteristic)"""
        assert self.normalizer.should_strip_verb('Trát') is False
        assert self.normalizer.should_strip_verb('trát') is False

    def test_should_keep_lat(self):
        """'Lát' should be kept (finishing characteristic)"""
        assert self.normalizer.should_strip_verb('Lát') is False
        assert self.normalizer.should_strip_verb('lát') is False

    def test_should_keep_son(self):
        """'Sơn' should be kept (finishing characteristic)"""
        assert self.normalizer.should_strip_verb('Sơn') is False
        assert self.normalizer.should_strip_verb('sơn') is False


class TestLocationExtraction:
    """Test Rule 2: Extract location to separate field"""

    def setup_method(self):
        self.normalizer = DescriptionNormalizer()

    def test_extract_floor_location(self):
        """Floor numbers should be extracted"""
        text, location = self.normalizer.extract_location("Bê tông cột tầng 1")
        assert location == "tầng 1"

    def test_extract_room_location(self):
        """Room names should be extracted"""
        text, location = self.normalizer.extract_location("Lát gạch sàn phòng khách")
        assert location == "phòng khách"

    def test_extract_indoor_location(self):
        """Indoor/outdoor indicators should be extracted"""
        text, location = self.normalizer.extract_location("Trát tường trong nhà")
        # Note: "tường trong nhà" is a longer pattern that takes precedence
        assert location == "tường trong nhà"

    def test_extract_simple_indoor(self):
        """Simple indoor indicator should be extracted"""
        text, location = self.normalizer.extract_location("Lát gạch sàn trong nhà")
        assert location == "trong nhà"

    def test_extract_basement_location(self):
        """Basement should be extracted"""
        text, location = self.normalizer.extract_location("Xây tường gạch tầng hầm")
        assert location == "tầng hầm"

    def test_no_location_for_mep(self):
        """MEP items typically have no location"""
        text, location = self.normalizer.extract_location("Ống HDPE D110")
        assert location is None

    def test_structural_objects_not_extracted(self):
        """Structural objects (móng, cột, dầm) should NOT be extracted as location"""
        text, location = self.normalizer.extract_location("Bê tông móng M200")
        assert location is None  # móng is OBJECT, not LOCATION


class TestUnitConversion:
    """Test Rule 3: Convert dimensions to mm"""

    def setup_method(self):
        self.normalizer = DescriptionNormalizer()

    def test_convert_cm_to_mm(self):
        """cm should be converted to mm"""
        result = self.normalizer.convert_to_mm("15", "cm")
        assert result == "150mm"

    def test_convert_m_to_mm(self):
        """m should be converted to mm"""
        result = self.normalizer.convert_to_mm("1.5", "m")
        assert result == "1500mm"

    def test_mm_stays_mm(self):
        """mm should stay as mm"""
        result = self.normalizer.convert_to_mm("200", "mm")
        assert result == "200mm"

    def test_convert_met_to_mm(self):
        """Vietnamese 'mét' should be converted to mm"""
        result = self.normalizer.convert_to_mm("0.5", "mét")
        assert result == "500mm"

    def test_dimension_extraction_converts_cm(self):
        """Dimension extraction should convert cm to mm"""
        dimensions = self.normalizer.extract_dimensions("Trát tường dày 15cm M75")
        assert "dày 150mm" in dimensions


class TestMEPNormalization:
    """Test MEP equipment follows Standard Naming Strategy"""

    def setup_method(self):
        self.normalizer = MEPEquipmentNormalizer()

    def test_mccb_no_verb_prefix(self):
        """MCCB should not have verb prefix"""
        result = self.normalizer.normalize("MCCB 3P 400A 50kA")
        assert "Cung cấp" not in result.normalized
        assert "Lắp đặt" not in result.normalized
        assert result.normalized.startswith("MCCB")

    def test_mcb_no_verb_prefix(self):
        """MCB should not have verb prefix"""
        result = self.normalizer.normalize("MCB 1P 16A")
        assert "Cung cấp" not in result.normalized
        assert result.normalized.startswith("MCB")

    def test_pipe_no_verb_prefix(self):
        """Pipes should not have verb prefix"""
        result = self.normalizer.normalize("Ống HDPE D110 PN16")
        assert "Lắp đặt" not in result.normalized
        assert result.normalized.startswith("Ống")

    def test_cable_no_verb_prefix(self):
        """Cables should not have verb prefix"""
        result = self.normalizer.normalize("Cáp Cu/XLPE/PVC 4x300mm2")
        assert "Lắp đặt" not in result.normalized
        assert result.normalized.startswith("Cáp")

    def test_lighting_no_verb_prefix(self):
        """Lighting should not have verb prefix"""
        result = self.normalizer.normalize("Đèn chiếu sáng LED 100W")
        assert "Lắp đặt" not in result.normalized
        assert result.normalized.startswith("Đèn")


class TestTrafficNormalization:
    """Test traffic equipment follows Standard Naming Strategy"""

    def setup_method(self):
        self.normalizer = TrafficEquipmentNormalizer()

    def test_sign_no_verb_prefix(self):
        """Traffic signs should not have verb prefix"""
        result = self.normalizer.normalize("Lắp đặt biển báo tam giác A70")
        assert "Lắp đặt" not in result.normalized
        assert result.normalized.startswith("Biển")

    def test_lamp_post_no_verb_prefix(self):
        """Lamp posts should not have verb prefix"""
        result = self.normalizer.normalize("Lắp đặt cột đèn thép H=8m")
        assert "Lắp đặt" not in result.normalized
        assert result.normalized.startswith("Cột đèn")

    def test_road_marking_noun_first(self):
        """Road markings should be noun-first: 'Vạch sơn' not 'Sơn vạch'"""
        result = self.normalizer.normalize("Sơn vạch đường màu trắng")
        assert result.normalized.startswith("Vạch sơn")

    def test_guardrail_no_verb_prefix(self):
        """Guardrails should not have verb prefix"""
        result = self.normalizer.normalize("Lắp đặt hộ lan tôn sóng")
        assert "Lắp đặt" not in result.normalized
        assert "Hộ lan" in result.normalized

    def test_marker_post_no_verb_prefix(self):
        """Marker posts should not have verb prefix"""
        result = self.normalizer.normalize("Lắp đặt cọc tiêu")
        assert "Lắp đặt" not in result.normalized
        assert result.normalized == "Cọc tiêu"


class TestOrchestratorIntegration:
    """Test orchestrator uses Standard Naming Strategy correctly"""

    def setup_method(self):
        self.orchestrator = NormalizationOrchestrator()

    def test_mep_uses_standard_naming(self):
        """MEP items should use standard naming through orchestrator"""
        result = self.orchestrator.normalize("Cung cấp lắp đặt MCCB 3P 400A 50kA")
        assert "Cung cấp" not in result.normalized
        assert "Lắp đặt" not in result.normalized

    def test_traffic_uses_standard_naming(self):
        """Traffic items should use standard naming through orchestrator"""
        result = self.orchestrator.normalize("Lắp đặt biển báo tam giác A70")
        assert "Lắp đặt" not in result.normalized

    def test_earthwork_keeps_verb(self):
        """Earthwork items should keep characteristic verb but remove position"""
        result = self.orchestrator.normalize("Đào đất hố móng bằng máy")
        assert "Đào" in result.normalized
        # Position "hố móng" should NOT be in output
        assert "hố móng" not in result.normalized

    def test_finishing_keeps_verb(self):
        """Finishing items should keep characteristic verb"""
        result = self.orchestrator.normalize("Xây tường gạch đặc M75")
        assert "Xây" in result.normalized

    def test_concrete_strips_do(self):
        """Concrete 'Đổ' should be stripped, add default đá 1x2"""
        result = self.orchestrator.normalize("Đổ bê tông dầm sàn M350 thương phẩm")
        assert "Đổ" not in result.normalized
        assert result.normalized.startswith("Bê tông")
        assert "đá 1x2" in result.normalized

    def test_concrete_has_default_stone(self):
        """Concrete should have default đá 1x2"""
        result = self.orchestrator.normalize("Bê tông dầm sàn M350")
        assert "đá 1x2" in result.normalized

    def test_rebar_no_position(self):
        """Rebar should NOT include position"""
        result = self.orchestrator.normalize("Cốt thép dầm sàn CB400V")
        assert "dầm sàn" not in result.normalized
        assert result.normalized.startswith("Cốt thép")

    def test_location_extracted(self):
        """Location should be extracted to separate field"""
        result = self.orchestrator.normalize("Bê tông cột tầng 1")
        assert result.location == "tầng 1"


class TestNounFirstFormat:
    """Test that output follows noun-first format"""

    def setup_method(self):
        self.orchestrator = NormalizationOrchestrator()

    def test_mep_noun_first(self):
        """MEP: Ống HDPE - D110 - PN16"""
        result = self.orchestrator.normalize("Lắp đặt ống HDPE D110 PN16")
        assert result.normalized.startswith("Ống")

    def test_breaker_noun_first(self):
        """Breaker: MCCB - 3P - 400A"""
        result = self.orchestrator.normalize("MCCB 3P 400A")
        assert result.normalized.startswith("MCCB")

    def test_sign_noun_first(self):
        """Sign: Biển báo tam giác - A70"""
        result = self.orchestrator.normalize("Lắp đặt biển báo tam giác A70")
        assert result.normalized.startswith("Biển")

    def test_road_marking_noun_first(self):
        """Road marking: Vạch sơn (not Sơn vạch)"""
        result = self.orchestrator.normalize("Sơn vạch liền trắng")
        assert result.normalized.startswith("Vạch sơn")

    def test_concrete_noun_first(self):
        """Concrete: Bê tông dầm sàn - M350 - đá 1x2"""
        result = self.orchestrator.normalize("Đổ bê tông dầm sàn M350")
        assert result.normalized.startswith("Bê tông")
        assert "đá 1x2" in result.normalized


class TestSpecsAfterNoun:
    """Test that technical specs come after noun"""

    def setup_method(self):
        self.orchestrator = NormalizationOrchestrator()

    def test_mep_specs_after_noun(self):
        """Specs should come after noun with dash separator"""
        result = self.orchestrator.normalize("Ống HDPE D110 PN16")
        # Format: Ống HDPE - D110 - PN16
        parts = result.normalized.split(" - ")
        assert len(parts) >= 2
        assert parts[0].startswith("Ống")

    def test_breaker_specs_after_noun(self):
        """Breaker specs should come after noun"""
        result = self.orchestrator.normalize("MCCB 3P 400A 50kA")
        # Format: MCCB - 3P - 400A - 50kA
        parts = result.normalized.split(" - ")
        assert parts[0] == "MCCB"

    def test_concrete_grade_after_noun(self):
        """Concrete grade should come after position"""
        result = self.orchestrator.normalize("Bê tông dầm sàn M350")
        assert "M350" in result.normalized
        # M350 should come after the noun phrase
        assert result.normalized.index("Bê tông") < result.normalized.index("M350")
