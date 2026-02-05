"""
Header Discovery Module

Intelligent header discovery for BOQ Excel files.

Features:
- Skips non-data sheets (Summary, Preliminary, Terms, Notes, Cover)
- Detects header row using multi-heuristic scoring
- Handles merged headers by flattening hierarchical structures
- Supports Vietnamese abbreviations (KL, ĐG, ĐVT, STT, MH, etc.)

Usage:
    from app.services.header_discovery import get_header_discovery_service

    service = get_header_discovery_service()
    result = service.discover("path/to/boq.xlsx")

    print(f"Sheet: {result.sheet_name}")
    print(f"Header row: {result.header_row}")
    print(f"Data starts: {result.data_start_row}")
    print(f"Columns: {result.column_names}")
    print(f"Confidence: {result.confidence_score}%")
"""

# Lazy imports to avoid import chain issues
def get_header_discovery_service():
    """Get or create singleton HeaderDiscoveryService instance."""
    from .header_discovery_service import get_header_discovery_service as _get
    return _get()


def get_sheet_filter():
    """Get or create singleton SheetFilter instance."""
    from .sheet_filter import get_sheet_filter as _get
    return _get()


def get_header_detector():
    """Get or create singleton HeaderDetector instance."""
    from .header_detector import get_header_detector as _get
    return _get()


def get_merged_cell_handler():
    """Get or create singleton MergedCellHandler instance."""
    from .merged_cell_handler import get_merged_cell_handler as _get
    return _get()


def get_keyword_dictionary():
    """Get or create singleton KeywordDictionary instance."""
    from .keyword_dictionary import get_keyword_dictionary as _get
    return _get()


# Dataclass exports
from .header_discovery_service import HeaderDiscoveryResult
from .sheet_filter import SheetInfo
from .header_detector import HeaderDetectionResult
from .merged_cell_handler import MergedHeaderResult
from .keyword_dictionary import KeywordMatch


__all__ = [
    # Factory functions
    "get_header_discovery_service",
    "get_sheet_filter",
    "get_header_detector",
    "get_merged_cell_handler",
    "get_keyword_dictionary",
    # Result types
    "HeaderDiscoveryResult",
    "SheetInfo",
    "HeaderDetectionResult",
    "MergedHeaderResult",
    "KeywordMatch",
]
