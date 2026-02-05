"""
Unit tests for SpecExtractor service.

Tests extraction of structured specs from Vietnamese construction descriptions.
"""
import pytest
from app.services.spec_extractor import SpecExtractor, ExtractedSpecs, get_spec_extractor


class TestExtractedSpecs:
    """Tests for ExtractedSpecs dataclass."""

    def test_to_matching_key_all_values(self):
        """Test matching key generation with all values present."""
        specs = ExtractedSpecs(
            category='be tong',
            material='HDPE',
            grade='M200',
            dimension='D110'
        )
        assert specs.to_matching_key() == 'be tong|hdpe|m200|d110'

    def test_to_matching_key_partial_values(self):
        """Test matching key with missing values uses 'X'."""
        specs = ExtractedSpecs(
            category='ong',
            material=None,
            grade='PN16',
            dimension=None
        )
        assert specs.to_matching_key() == 'ong|x|pn16|x'

    def test_to_matching_key_empty(self):
        """Test matching key with no values."""
        specs = ExtractedSpecs()
        assert specs.to_matching_key() == 'x|x|x|x'

    def test_is_empty_true(self):
        """Test is_empty returns True when no specs."""
        specs = ExtractedSpecs()
        assert specs.is_empty() is True

    def test_is_empty_false(self):
        """Test is_empty returns False when any spec exists."""
        specs = ExtractedSpecs(category='be tong')
        assert specs.is_empty() is False


class TestSpecExtractorCategories:
    """Tests for category extraction."""

    @pytest.fixture
    def extractor(self):
        return SpecExtractor()

    @pytest.mark.parametrize("description,expected_category", [
        # Concrete
        ("Be tong lot mong M150", "be tong"),
        ("BT cot M200", "be tong"),
        ("concrete foundation", "be tong"),
        # Reinforced concrete
        ("be tong cot thep dam M300", "be tong cot thep"),
        ("btct san M250", "be tong cot thep"),
        # Rebar/steel
        ("cot thep D16", "cot thep"),
        ("thep cot CB400", "cot thep"),
        ("rebar D12", "cot thep"),
        # Pipes
        ("Ong nhua HDPE D110", "ong"),
        ("ong PVC DN50", "ong"),
        ("pipe HDPE", "ong"),
        # Cables
        ("cap dien Cu/XLPE 4x16mm2", "cap dien"),
        ("day dien 2.5mm2", "cap dien"),
        ("cap dong 240mm2", "cap"),
        # Bricks
        ("gach lat 600x600", "gach lat"),
        ("xay tuong gach", "xay"),  # "xay" category takes precedence
        ("brick wall 200mm", "gach"),
        # Earthwork
        ("dao dat mong bang may", "dao dat"),
        ("excavation 2m deep", "dao dat"),
        ("dap dat nen K95", "dap dat"),
        # Formwork
        ("van khuon mong", "van khuon"),
        ("formwork column", "van khuon"),
        ("VK dam", "van khuon"),
        # Masonry
        ("xay tuong gach", "xay"),
        # Plaster
        ("trat tuong day 15mm", "trat"),
        # Paint
        ("son nuoc ngoai nha", "son"),
        # Waterproofing
        ("chong tham san mai", "chong tham"),
    ])
    def test_category_extraction(self, extractor, description, expected_category):
        """Test various category extractions."""
        specs = extractor.extract(description)
        assert specs.category == expected_category, f"Expected '{expected_category}' for '{description}'"


class TestSpecExtractorMaterials:
    """Tests for material extraction."""

    @pytest.fixture
    def extractor(self):
        return SpecExtractor()

    @pytest.mark.parametrize("description,expected_material", [
        # Plastics
        ("ong HDPE D110", "HDPE"),
        ("ong nhua PPR D20", "PPR"),
        ("ong PVC DN50", "PVC"),
        ("ong PE D63", "PE"),
        # Cables
        ("cap Cu/XLPE 4x16mm2", "Cu/XLPE"),
        ("cap XLPE 240mm2", "XLPE"),
        ("cap dong 16mm2", "Cu"),
        ("day nhom 95mm2", "Al"),
        # Metal
        ("ong gang DN100", "gang"),
        ("ong inox D34", "inox"),
        ("thep ma kem D48", "thep ma kem"),
        # Brick types
        ("gach dac xay tuong", "gach dac"),
        ("gach rong 8x8x18", "gach rong"),
        ("gach men lat san", "ceramic"),
        ("da granite lat san", "granite"),
        # Wood
        ("van khuon go", "go"),
    ])
    def test_material_extraction(self, extractor, description, expected_material):
        """Test various material extractions."""
        specs = extractor.extract(description)
        assert specs.material == expected_material, f"Expected '{expected_material}' for '{description}'"


class TestSpecExtractorGrades:
    """Tests for grade extraction."""

    @pytest.fixture
    def extractor(self):
        return SpecExtractor()

    @pytest.mark.parametrize("description,expected_grade", [
        # Concrete grades
        ("be tong M150", "M150"),
        ("BT M200", "M200"),
        ("be tong M300", "M300"),
        ("concrete B25", "B25"),
        ("BT B22.5", "B22.5"),
        # Rebar grades
        ("thep CB300", "CB300"),
        ("cot thep CB400", "CB400"),
        # Steel grades
        ("thep CT3", "CT3"),
        # Pipe pressure
        ("ong HDPE PN10", "PN10"),
        ("ong PPR PN16", "PN16"),
        # Compaction
        ("dap dat K95", "K95"),
        ("nen dat K98", "K98"),
        # Eurocode
        ("be tong C20/25", "C20/25"),
        # SDR
        ("ong HDPE SDR11", "SDR11"),
    ])
    def test_grade_extraction(self, extractor, description, expected_grade):
        """Test various grade extractions."""
        specs = extractor.extract(description)
        assert specs.grade == expected_grade, f"Expected '{expected_grade}' for '{description}'"


class TestSpecExtractorDimensions:
    """Tests for dimension extraction."""

    @pytest.fixture
    def extractor(self):
        return SpecExtractor()

    @pytest.mark.parametrize("description,expected_dimension", [
        # Pipe diameters
        ("ong HDPE D110", "D110"),
        ("ong DN200", "DN200"),
        ("ong D315", "D315"),
        # Rebar diameters
        ("thep D10", "D10"),
        ("cot thep D16", "D16"),
        ("rebar D25", "D25"),
        # Cable cross-section
        ("cap 4x16mm2", "4x16mm2"),
        ("cap dong 3x10mm2", "3x10mm2"),
        ("cap 240mm2", "240mm2"),
        # Tile sizes
        ("gach lat 600x600", "600x600"),
        ("gach 400x400", "400x400"),
        # Block sizes
        ("gach 400x200x8", "400x200x8"),
        # Simple measurements
        ("day 15mm", "15mm"),
        ("trat 20mm", "20mm"),
    ])
    def test_dimension_extraction(self, extractor, description, expected_dimension):
        """Test various dimension extractions."""
        specs = extractor.extract(description)
        assert specs.dimension == expected_dimension, f"Expected '{expected_dimension}' for '{description}'"


class TestSpecExtractorComplexDescriptions:
    """Tests for complex real-world descriptions."""

    @pytest.fixture
    def extractor(self):
        return SpecExtractor()

    def test_pipe_full_description(self, extractor):
        """Test full pipe description."""
        specs = extractor.extract("Ong nhua HDPE D110 PN10 SDR11")
        assert specs.category == 'ong'
        assert specs.material == 'HDPE'
        assert specs.grade == 'PN10'  # First matched grade
        assert specs.dimension == 'D110'

    def test_concrete_full_description(self, extractor):
        """Test full concrete description."""
        specs = extractor.extract("Be tong cot thep dam san M300 B25")
        assert specs.category == 'be tong cot thep'
        assert specs.grade == 'M300'  # First matched grade

    def test_rebar_full_description(self, extractor):
        """Test full rebar description."""
        specs = extractor.extract("Cot thep dam CB400 D16")
        assert specs.category == 'cot thep'
        assert specs.grade == 'CB400'
        assert specs.dimension == 'D16'

    def test_cable_full_description(self, extractor):
        """Test full cable description."""
        specs = extractor.extract("Cap dien ngam Cu/XLPE/PVC 4x16mm2")
        assert specs.category == 'cap dien'
        assert specs.material == 'Cu/XLPE'
        assert specs.dimension == '4x16mm2'

    def test_tile_full_description(self, extractor):
        """Test full tile description."""
        specs = extractor.extract("Gach lat nen ceramic 600x600")
        assert specs.category == 'gach lat'
        assert specs.material == 'ceramic'
        assert specs.dimension == '600x600'

    def test_earthwork_full_description(self, extractor):
        """Test full earthwork description."""
        specs = extractor.extract("Dap dat nen duong K95")
        assert specs.category == 'dap dat'
        assert specs.grade == 'K95'

    def test_waterproofing_description(self, extractor):
        """Test waterproofing description."""
        specs = extractor.extract("Chong tham san ve sinh day 3mm")
        assert specs.category == 'chong tham'
        assert specs.dimension == '3mm'


class TestSpecExtractorEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.fixture
    def extractor(self):
        return SpecExtractor()

    def test_empty_string(self, extractor):
        """Test empty string input."""
        specs = extractor.extract("")
        assert specs.is_empty()

    def test_none_input(self, extractor):
        """Test None input."""
        specs = extractor.extract(None)
        assert specs.is_empty()

    def test_no_matches(self, extractor):
        """Test description with no recognizable specs."""
        specs = extractor.extract("Some random text without specs")
        # May or may not extract anything depending on patterns
        # Just ensure it doesn't crash
        assert isinstance(specs, ExtractedSpecs)

    def test_case_insensitive_matching(self, extractor):
        """Test case insensitive matching."""
        specs1 = extractor.extract("HDPE D110")
        specs2 = extractor.extract("hdpe d110")
        assert specs1.material == specs2.material

    def test_unicode_vietnamese(self, extractor):
        """Test Vietnamese Unicode characters."""
        specs = extractor.extract("Bê tông cốt thép M200")
        assert specs.category == 'be tong cot thep'
        assert specs.grade == 'M200'


class TestGetSpecExtractor:
    """Tests for singleton pattern."""

    def test_get_spec_extractor_returns_instance(self):
        """Test get_spec_extractor returns SpecExtractor."""
        extractor = get_spec_extractor()
        assert isinstance(extractor, SpecExtractor)

    def test_get_spec_extractor_singleton(self):
        """Test get_spec_extractor returns same instance."""
        extractor1 = get_spec_extractor()
        extractor2 = get_spec_extractor()
        assert extractor1 is extractor2
