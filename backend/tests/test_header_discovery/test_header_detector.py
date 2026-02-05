"""
Tests for HeaderDetector
"""
import pytest
import pandas as pd
import numpy as np
from app.services.header_discovery.header_detector import (
    HeaderDetector,
    HeaderDetectionResult,
    get_header_detector
)


class TestHeaderDetector:
    """Test cases for HeaderDetector."""

    @pytest.fixture
    def detector(self):
        return HeaderDetector()

    # Test standard header at row 0
    def test_detect_header_row_0(self, detector):
        """Test detection when header is at row 0."""
        df = pd.DataFrame([
            ["STT", "Mô tả", "Đơn vị", "Khối lượng", "Đơn giá", "Thành tiền"],
            [1, "Bê tông M200", "m3", 10, 1000000, 10000000],
            [2, "Thép CB400", "kg", 500, 15000, 7500000],
        ])

        result = detector.detect(df)

        assert result.header_row == 0
        assert result.confidence_score > 50.0

    # Test header at row 5 (after project info)
    def test_detect_header_row_5(self, detector):
        """Test detection when header is at row 5."""
        # Create rows with project info first
        data = [
            ["Project Name", "ABC Building", None, None, None, None],
            ["Location", "Hanoi", None, None, None, None],
            ["Date", "2024-01-01", None, None, None, None],
            [None, None, None, None, None, None],
            [None, None, None, None, None, None],
            ["STT", "Mô tả", "Đơn vị", "Khối lượng", "Đơn giá", "Thành tiền"],
            [1, "Bê tông M200", "m3", 10, 1000000, 10000000],
            [2, "Thép CB400", "kg", 500, 15000, 7500000],
        ]
        df = pd.DataFrame(data)

        result = detector.detect(df)

        assert result.header_row == 5
        assert result.confidence_score > 30.0

    # Test Vietnamese abbreviated headers
    def test_detect_abbreviated_headers(self, detector):
        """Test detection with Vietnamese abbreviations."""
        df = pd.DataFrame([
            ["STT", "Nội dung công việc", "ĐVT", "KL", "ĐG", "TT"],
            [1, "Đào đất", "m3", 100, 50000, 5000000],
            [2, "Đắp đất", "m3", 80, 40000, 3200000],
        ])

        result = detector.detect(df)

        assert result.header_row == 0
        assert result.confidence_score > 40.0
        assert 'quantity' in result.column_type_hints or 'unit' in result.column_type_hints

    # Test English headers
    def test_detect_english_headers(self, detector):
        """Test detection with English headers."""
        df = pd.DataFrame([
            ["No.", "Description", "Unit", "Quantity", "Unit Price", "Amount"],
            [1, "Concrete M200", "m3", 10, 1000000, 10000000],
            [2, "Rebar CB400", "kg", 500, 15000, 7500000],
        ])

        result = detector.detect(df)

        assert result.header_row == 0
        assert result.confidence_score > 50.0

    # Test empty DataFrame
    def test_detect_empty_dataframe(self, detector):
        """Test detection with empty DataFrame."""
        df = pd.DataFrame()

        result = detector.detect(df)

        assert result.header_row == 0
        assert result.confidence_score == 0.0

    # Test single row DataFrame
    def test_detect_single_row(self, detector):
        """Test detection with single row."""
        df = pd.DataFrame([
            ["STT", "Mô tả", "Đơn vị", "Khối lượng"],
        ])

        result = detector.detect(df)

        assert result.header_row == 0

    # Test DataFrame with all numeric first row
    def test_detect_numeric_first_row(self, detector):
        """Test that numeric first row is not selected as header."""
        df = pd.DataFrame([
            [1, 2, 3, 4, 5],
            ["STT", "Mô tả", "Đơn vị", "KL", "TT"],
            [1, "Work item 1", "m3", 10, 100000],
        ])

        result = detector.detect(df)

        # Should select row 1 (the text header), not row 0 (numbers)
        assert result.header_row == 1

    # Test column type hints
    def test_column_type_hints(self, detector):
        """Test that column type hints are populated correctly."""
        df = pd.DataFrame([
            ["Description", "Unit", "Quantity", "Amount"],
            ["Item 1", "m3", 10, 100000],
        ])

        result = detector.detect(df)

        assert 'description' in result.column_type_hints
        assert result.column_type_hints['description'] == 0
        assert 'unit' in result.column_type_hints
        assert result.column_type_hints['unit'] == 1

    # Test mixed content rows
    def test_detect_mixed_content(self, detector):
        """Test detection with mixed content rows."""
        df = pd.DataFrame([
            ["Section A", None, None, None],
            [1.0, 2.0, 3.0, 4.0],
            ["STT", "Mô tả công việc", "Đơn vị", "Khối lượng"],
            [1, "Item 1", "m3", 10],
            [2, "Item 2", "m2", 20],
        ])

        result = detector.detect(df)

        # Should detect row 2 as header
        assert result.header_row == 2

    # Test confidence score
    def test_confidence_score_high_for_clear_header(self, detector):
        """Test that clear headers get high confidence."""
        df = pd.DataFrame([
            ["STT", "Mô tả", "Đơn vị", "Khối lượng", "Đơn giá", "Thành tiền"],
            [1, "Item", "m3", 10, 1000, 10000],
            [2, "Item", "m3", 20, 1000, 20000],
            [3, "Item", "m3", 30, 1000, 30000],
        ])

        result = detector.detect(df)

        assert result.confidence_score > 60.0

    def test_confidence_score_low_for_ambiguous(self, detector):
        """Test that ambiguous data gets lower confidence."""
        df = pd.DataFrame([
            ["A", "B", "C"],
            ["X", "Y", "Z"],
            ["1", "2", "3"],
        ])

        result = detector.detect(df)

        # Both rows look similar, so confidence should be lower
        assert result.confidence_score < 80.0


class TestGetHeaderDetector:
    """Test singleton factory function."""

    def test_singleton(self):
        """Test that factory returns singleton."""
        detector1 = get_header_detector()
        detector2 = get_header_detector()
        assert detector1 is detector2
