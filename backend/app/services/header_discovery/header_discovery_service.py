"""
Header Discovery Service

Main orchestrator for intelligent header discovery in BOQ Excel files.
Combines sheet filtering, header detection, and merged cell handling.
"""
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from .sheet_filter import get_sheet_filter, SheetFilter, SheetInfo
from .header_detector import get_header_detector, HeaderDetector, HeaderDetectionResult
from .merged_cell_handler import get_merged_cell_handler, MergedCellHandler

logger = logging.getLogger(__name__)


@dataclass
class HeaderDiscoveryResult:
    """Result of header discovery for a sheet."""
    sheet_name: str
    sheet_index: int
    header_row: int
    data_start_row: int
    column_names: List[str]
    confidence_score: float  # 0-100
    is_merged_header: bool
    column_type_hints: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'sheet_name': self.sheet_name,
            'sheet_index': self.sheet_index,
            'header_row': self.header_row,
            'data_start_row': self.data_start_row,
            'column_names': self.column_names,
            'confidence_score': self.confidence_score,
            'is_merged_header': self.is_merged_header,
            'column_type_hints': self.column_type_hints
        }


class HeaderDiscoveryService:
    """
    Main service for intelligent header discovery.

    Flow:
        discover(file_path) →
          1. Get sheet list
          2. Filter/rank sheets (SheetFilter)
          3. Read raw DataFrame (header=None)
          4. Detect header row (HeaderDetector)
          5. Handle merged cells (MergedCellHandler)
          6. Return HeaderDiscoveryResult
    """

    def __init__(
        self,
        sheet_filter: Optional[SheetFilter] = None,
        header_detector: Optional[HeaderDetector] = None,
        merged_handler: Optional[MergedCellHandler] = None
    ):
        """
        Initialize header discovery service.

        Args:
            sheet_filter: Optional SheetFilter instance
            header_detector: Optional HeaderDetector instance
            merged_handler: Optional MergedCellHandler instance
        """
        self.sheet_filter = sheet_filter or get_sheet_filter()
        self.header_detector = header_detector or get_header_detector()
        self.merged_handler = merged_handler or get_merged_cell_handler()

    def discover(
        self,
        file_path: str,
        sheet_name: Optional[str] = None
    ) -> HeaderDiscoveryResult:
        """
        Discover headers in an Excel file.

        Args:
            file_path: Path to Excel file
            sheet_name: Optional specific sheet to analyze.
                       If None, uses best sheet from filter.

        Returns:
            HeaderDiscoveryResult with discovery details
        """
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Starting header discovery for: {file_path}")

        # Get sheet list
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names

        # Determine target sheet
        if sheet_name:
            if sheet_name not in sheet_names:
                raise ValueError(f"Sheet '{sheet_name}' not found in workbook")
            target_sheet = sheet_name
            sheet_index = sheet_names.index(sheet_name)
            logger.info(f"Using specified sheet: {sheet_name}")
        else:
            # Use sheet filter to find best sheet
            best_sheet = self.sheet_filter.get_best_sheet(sheet_names)
            if best_sheet is None:
                # Fall back to first sheet if all are filtered
                target_sheet = sheet_names[0]
                sheet_index = 0
                logger.warning(f"All sheets filtered, using first: {target_sheet}")
            else:
                target_sheet = best_sheet.name
                sheet_index = best_sheet.index
                logger.info(f"Selected sheet: {target_sheet} (priority: {best_sheet.priority_score})")

        # Read raw DataFrame (no header)
        df = pd.read_excel(file_path, sheet_name=target_sheet, header=None)

        if df.empty:
            logger.warning(f"Sheet '{target_sheet}' is empty")
            return HeaderDiscoveryResult(
                sheet_name=target_sheet,
                sheet_index=sheet_index,
                header_row=0,
                data_start_row=1,
                column_names=[f"Column_{i+1}" for i in range(df.shape[1] if df.shape[1] > 0 else 1)],
                confidence_score=0.0,
                is_merged_header=False,
                column_type_hints={}
            )

        # Detect header row
        detection_result = self.header_detector.detect(df)
        header_row = detection_result.header_row

        logger.info(f"Detected header at row {header_row} (confidence: {detection_result.confidence_score:.1f})")

        # Handle merged headers
        num_columns = len(df.columns)
        merged_result = self.merged_handler.process_headers(
            file_path, target_sheet, header_row, num_columns
        )

        # Calculate data start row
        data_start_row = header_row + merged_result.header_depth

        # Clean up column names
        column_names = self._clean_column_names(merged_result.column_names)

        return HeaderDiscoveryResult(
            sheet_name=target_sheet,
            sheet_index=sheet_index,
            header_row=header_row,
            data_start_row=data_start_row,
            column_names=column_names,
            confidence_score=detection_result.confidence_score,
            is_merged_header=merged_result.is_merged,
            column_type_hints=detection_result.column_type_hints
        )

    def discover_all_sheets(self, file_path: str) -> List[HeaderDiscoveryResult]:
        """
        Discover headers in all valid sheets.

        Args:
            file_path: Path to Excel file

        Returns:
            List of HeaderDiscoveryResult for each non-skipped sheet
        """
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names

        # Filter sheets
        filtered = self.sheet_filter.filter_sheets(sheet_names)

        results = []
        for sheet_info in filtered:
            if sheet_info.should_skip:
                logger.debug(f"Skipping sheet '{sheet_info.name}': {sheet_info.skip_reason}")
                continue

            try:
                result = self.discover(file_path, sheet_name=sheet_info.name)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing sheet '{sheet_info.name}': {e}")

        return results

    def _clean_column_names(self, names: List[str]) -> List[str]:
        """Clean and deduplicate column names."""
        cleaned = []
        seen: Dict[str, int] = {}

        for name in names:
            # Clean the name
            clean_name = name.strip()

            # Replace newlines with spaces
            clean_name = clean_name.replace('\n', ' ').replace('\r', ' ')

            # Collapse multiple spaces
            clean_name = ' '.join(clean_name.split())

            if not clean_name:
                clean_name = f"Column_{len(cleaned) + 1}"

            # Handle duplicates
            base_name = clean_name
            if base_name in seen:
                seen[base_name] += 1
                clean_name = f"{base_name}_{seen[base_name]}"
            else:
                seen[base_name] = 0

            cleaned.append(clean_name)

        return cleaned


# Module-level singleton
_header_discovery_service: Optional[HeaderDiscoveryService] = None


def get_header_discovery_service() -> HeaderDiscoveryService:
    """Get or create singleton HeaderDiscoveryService instance."""
    global _header_discovery_service
    if _header_discovery_service is None:
        _header_discovery_service = HeaderDiscoveryService()
    return _header_discovery_service
