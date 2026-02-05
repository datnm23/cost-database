"""
Tests for SheetFilter
"""
import pytest
from app.services.header_discovery.sheet_filter import (
    SheetFilter,
    SheetInfo,
    get_sheet_filter
)


class TestSheetFilter:
    """Test cases for SheetFilter."""

    @pytest.fixture
    def sheet_filter(self):
        return SheetFilter()

    # Test skip patterns
    def test_skip_summary_sheet(self, sheet_filter):
        """Test that summary sheets are skipped."""
        skip, reason = sheet_filter.should_skip("Summary")
        assert skip is True
        assert "Summary" in reason

    def test_skip_vietnamese_summary(self, sheet_filter):
        """Test that Vietnamese summary sheets are skipped."""
        skip, reason = sheet_filter.should_skip("Tổng hợp")
        assert skip is True

    def test_skip_preliminary(self, sheet_filter):
        """Test that preliminary sheets are skipped."""
        skip, reason = sheet_filter.should_skip("Preliminary")
        assert skip is True

    def test_skip_terms_conditions(self, sheet_filter):
        """Test that terms and conditions sheets are skipped."""
        skip, reason = sheet_filter.should_skip("Terms and Conditions")
        assert skip is True

    def test_skip_cover_page(self, sheet_filter):
        """Test that cover pages are skipped."""
        skip, reason = sheet_filter.should_skip("Cover Page")
        assert skip is True

    def test_skip_notes(self, sheet_filter):
        """Test that notes sheets are skipped."""
        skip, reason = sheet_filter.should_skip("Notes")
        assert skip is True

    def test_skip_instructions(self, sheet_filter):
        """Test that instruction sheets are skipped."""
        skip, reason = sheet_filter.should_skip("Instructions")
        assert skip is True

    def test_skip_appendix(self, sheet_filter):
        """Test that appendix sheets are skipped."""
        skip, reason = sheet_filter.should_skip("Appendix")
        assert skip is True

    # Test non-skip sheets
    def test_not_skip_boq(self, sheet_filter):
        """Test that BOQ sheets are not skipped."""
        skip, _ = sheet_filter.should_skip("BOQ")
        assert skip is False

    def test_not_skip_data_sheet(self, sheet_filter):
        """Test that data sheets are not skipped."""
        skip, _ = sheet_filter.should_skip("Data")
        assert skip is False

    def test_not_skip_work_items(self, sheet_filter):
        """Test that work items sheets are not skipped."""
        skip, _ = sheet_filter.should_skip("Work Items")
        assert skip is False

    # Test priority patterns
    def test_priority_boq_highest(self, sheet_filter):
        """Test that BOQ has highest priority."""
        priority = sheet_filter.get_priority("BOQ")
        assert priority == 10.0

    def test_priority_boq_numbered(self, sheet_filter):
        """Test priority for numbered BOQ sheets."""
        priority = sheet_filter.get_priority("BOQ 1")
        assert priority >= 9.0

    def test_priority_bill_of_quantities(self, sheet_filter):
        """Test priority for 'Bill of Quantities'."""
        priority = sheet_filter.get_priority("Bill of Quantities")
        assert priority >= 9.0

    def test_priority_mep(self, sheet_filter):
        """Test priority for M&E/MEP sheets."""
        priority = sheet_filter.get_priority("M&E")
        assert priority >= 8.0

    def test_priority_xay_dung(self, sheet_filter):
        """Test priority for Vietnamese construction sheets."""
        priority = sheet_filter.get_priority("Xây dựng")
        assert priority >= 7.0

    def test_priority_detail(self, sheet_filter):
        """Test priority for detail sheets."""
        priority = sheet_filter.get_priority("Detail")
        assert priority >= 6.0

    def test_priority_unknown(self, sheet_filter):
        """Test priority for unknown sheets."""
        priority = sheet_filter.get_priority("RandomSheet")
        assert priority >= 1.0  # Default priority

    # Test analyze_sheet
    def test_analyze_sheet_boq(self, sheet_filter):
        """Test analyzing a BOQ sheet."""
        info = sheet_filter.analyze_sheet("BOQ", 0)

        assert info.name == "BOQ"
        assert info.index == 0
        assert info.should_skip is False
        assert info.priority_score == 10.0

    def test_analyze_sheet_summary(self, sheet_filter):
        """Test analyzing a summary sheet."""
        info = sheet_filter.analyze_sheet("Summary", 1)

        assert info.name == "Summary"
        assert info.index == 1
        assert info.should_skip is True
        assert info.skip_reason is not None

    # Test filter_sheets
    def test_filter_sheets_ordering(self, sheet_filter):
        """Test that filter_sheets orders correctly."""
        sheet_names = ["Summary", "BOQ", "Notes", "Detail", "Terms"]
        filtered = sheet_filter.filter_sheets(sheet_names)

        # Non-skipped sheets should come first
        non_skipped = [s for s in filtered if not s.should_skip]
        skipped = [s for s in filtered if s.should_skip]

        assert len(non_skipped) == 2  # BOQ, Detail
        assert len(skipped) == 3  # Summary, Notes, Terms

        # BOQ should be first (highest priority)
        assert non_skipped[0].name == "BOQ"

    def test_filter_sheets_all_skipped(self, sheet_filter):
        """Test when all sheets should be skipped."""
        sheet_names = ["Summary", "Notes", "Terms"]
        filtered = sheet_filter.filter_sheets(sheet_names)

        assert all(s.should_skip for s in filtered)

    # Test get_best_sheet
    def test_get_best_sheet(self, sheet_filter):
        """Test getting the best sheet."""
        sheet_names = ["Summary", "Detail", "BOQ", "Notes"]
        best = sheet_filter.get_best_sheet(sheet_names)

        assert best is not None
        assert best.name == "BOQ"

    def test_get_best_sheet_no_boq(self, sheet_filter):
        """Test getting best sheet when no BOQ sheet exists."""
        sheet_names = ["Summary", "Detail", "Work Items", "Notes"]
        best = sheet_filter.get_best_sheet(sheet_names)

        assert best is not None
        assert best.name in ["Detail", "Work Items"]

    def test_get_best_sheet_all_filtered(self, sheet_filter):
        """Test when all sheets are filtered."""
        sheet_names = ["Summary", "Notes", "Terms"]
        best = sheet_filter.get_best_sheet(sheet_names)

        assert best is None


class TestGetSheetFilter:
    """Test singleton factory function."""

    def test_singleton(self):
        """Test that factory returns singleton."""
        filter1 = get_sheet_filter()
        filter2 = get_sheet_filter()
        assert filter1 is filter2
