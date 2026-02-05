"""
Tests for KeywordDictionary
"""
import pytest
from app.services.header_discovery.keyword_dictionary import (
    KeywordDictionary,
    KeywordMatch,
    get_keyword_dictionary
)


class TestKeywordDictionary:
    """Test cases for KeywordDictionary."""

    @pytest.fixture
    def keyword_dict(self):
        return KeywordDictionary()

    # Test Vietnamese full words
    def test_match_vietnamese_description(self, keyword_dict):
        """Test matching Vietnamese description keywords."""
        match = keyword_dict.match_cell("Mô tả")
        assert match is not None
        assert match.column_type == 'description'
        assert match.weight >= 4.5

    def test_match_vietnamese_unit(self, keyword_dict):
        """Test matching Vietnamese unit keywords."""
        match = keyword_dict.match_cell("Đơn vị")
        assert match is not None
        assert match.column_type == 'unit'
        assert match.weight >= 4.5

    def test_match_vietnamese_quantity(self, keyword_dict):
        """Test matching Vietnamese quantity keywords."""
        match = keyword_dict.match_cell("Khối lượng")
        assert match is not None
        assert match.column_type == 'quantity'
        assert match.weight >= 4.5

    def test_match_vietnamese_unit_price(self, keyword_dict):
        """Test matching Vietnamese unit price keywords."""
        match = keyword_dict.match_cell("Đơn giá")
        assert match is not None
        assert match.column_type == 'unit_price'
        assert match.weight >= 4.5

    def test_match_vietnamese_amount(self, keyword_dict):
        """Test matching Vietnamese amount keywords."""
        match = keyword_dict.match_cell("Thành tiền")
        assert match is not None
        assert match.column_type == 'amount'
        assert match.weight >= 4.5

    # Test Vietnamese abbreviations
    def test_match_abbreviation_stt(self, keyword_dict):
        """Test matching STT abbreviation."""
        match = keyword_dict.match_cell("STT")
        assert match is not None
        assert match.column_type == 'index'
        assert match.weight >= 3.5

    def test_match_abbreviation_dvt(self, keyword_dict):
        """Test matching ĐVT abbreviation."""
        match = keyword_dict.match_cell("ĐVT")
        assert match is not None
        assert match.column_type == 'unit'
        assert match.weight >= 4.0

    def test_match_abbreviation_kl(self, keyword_dict):
        """Test matching KL abbreviation."""
        match = keyword_dict.match_cell("KL")
        assert match is not None
        assert match.column_type == 'quantity'
        assert match.weight >= 3.5

    def test_match_abbreviation_dg(self, keyword_dict):
        """Test matching ĐG abbreviation."""
        match = keyword_dict.match_cell("ĐG")
        assert match is not None
        assert match.column_type == 'unit_price'
        assert match.weight >= 4.0

    def test_match_abbreviation_with_punctuation(self, keyword_dict):
        """Test matching abbreviations with punctuation."""
        match = keyword_dict.match_cell("STT.")
        assert match is not None
        assert match.column_type == 'index'

    # Test English keywords
    def test_match_english_description(self, keyword_dict):
        """Test matching English description keyword."""
        match = keyword_dict.match_cell("Description")
        assert match is not None
        assert match.column_type == 'description'
        assert match.weight >= 4.5

    def test_match_english_quantity(self, keyword_dict):
        """Test matching English quantity keyword."""
        match = keyword_dict.match_cell("Quantity")
        assert match is not None
        assert match.column_type == 'quantity'
        assert match.weight >= 4.5

    def test_match_english_unit_price(self, keyword_dict):
        """Test matching English unit price keyword."""
        match = keyword_dict.match_cell("Unit Price")
        assert match is not None
        assert match.column_type == 'unit_price'
        assert match.weight >= 4.5

    def test_match_english_amount(self, keyword_dict):
        """Test matching English amount keyword."""
        match = keyword_dict.match_cell("Amount")
        assert match is not None
        assert match.column_type == 'amount'
        assert match.weight >= 4.5

    # Test case insensitivity
    def test_case_insensitive_matching(self, keyword_dict):
        """Test that matching is case-insensitive."""
        assert keyword_dict.match_cell("DESCRIPTION") is not None
        assert keyword_dict.match_cell("description") is not None
        assert keyword_dict.match_cell("Description") is not None

    # Test non-matching values
    def test_no_match_for_numbers(self, keyword_dict):
        """Test that numbers don't match."""
        assert keyword_dict.match_cell("12345") is None

    def test_no_match_for_random_text(self, keyword_dict):
        """Test that random text doesn't match."""
        assert keyword_dict.match_cell("xyz123") is None

    def test_no_match_for_empty(self, keyword_dict):
        """Test that empty values don't match."""
        assert keyword_dict.match_cell("") is None
        assert keyword_dict.match_cell(None) is None

    # Test row scoring
    def test_score_row_complete_boq(self, keyword_dict):
        """Test scoring a complete BOQ header row."""
        cells = ["STT", "Mô tả", "Đơn vị", "Khối lượng", "Đơn giá", "Thành tiền"]
        score, hints = keyword_dict.score_row(cells)

        assert score > 30.0  # Should have high score
        assert 'description' in hints
        assert 'unit' in hints
        assert 'quantity' in hints
        assert 'unit_price' in hints
        assert 'amount' in hints

    def test_score_row_partial_boq(self, keyword_dict):
        """Test scoring a partial BOQ header row."""
        cells = ["No.", "Description", "Unit"]
        score, hints = keyword_dict.score_row(cells)

        assert score > 10.0
        assert 'description' in hints
        assert 'unit' in hints

    def test_score_row_empty(self, keyword_dict):
        """Test scoring an empty row."""
        cells = [None, "", None]
        score, hints = keyword_dict.score_row(cells)

        assert score == 0.0
        assert len(hints) == 0

    def test_score_row_with_bonus(self, keyword_dict):
        """Test that complete BOQ gets bonus score."""
        # Complete row (description + unit + quantity)
        complete_cells = ["Description", "Unit", "Quantity"]
        complete_score, _ = keyword_dict.score_row(complete_cells)

        # Incomplete row (missing one core element)
        incomplete_cells = ["Description", "Unit", "Notes"]
        incomplete_score, _ = keyword_dict.score_row(incomplete_cells)

        # Complete should have bonus
        assert complete_score > incomplete_score


class TestGetKeywordDictionary:
    """Test singleton factory function."""

    def test_singleton(self):
        """Test that factory returns singleton."""
        dict1 = get_keyword_dictionary()
        dict2 = get_keyword_dictionary()
        assert dict1 is dict2
