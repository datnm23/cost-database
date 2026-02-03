"""
BOQ Export Service - Export processed BOQ results to Excel

Creates structured Excel templates with:
1. Summary sheet with statistics
2. Processed items with normalization results
3. Matching results against Master database
4. Items needing review
5. New items to add to Master
"""
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import logging

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from sqlalchemy.orm import Session

from app.models.line_item import LineItem
from app.models.master_work_item import MasterWorkItem
from app.models.boq_file import BOQFile
from app.models.project import Project
from app.services.boq_processing_service import BOQProcessingService, ProcessingResult, MatchResult

logger = logging.getLogger(__name__)


# Styles
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
HEADER_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
HEADER_FILL_GREEN = PatternFill(start_color="70AD47", end_color="70AD47", fill_type="solid")
HEADER_FILL_ORANGE = PatternFill(start_color="ED7D31", end_color="ED7D31", fill_type="solid")
HEADER_FILL_RED = PatternFill(start_color="C00000", end_color="C00000", fill_type="solid")
HEADER_FILL_PURPLE = PatternFill(start_color="7030A0", end_color="7030A0", fill_type="solid")

EXACT_MATCH_FILL = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
FUZZY_MATCH_FILL = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
NEW_ITEM_FILL = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

THIN_BORDER = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)

CENTER_ALIGN = Alignment(horizontal='center', vertical='center')
LEFT_ALIGN = Alignment(horizontal='left', vertical='center', wrap_text=True)
RIGHT_ALIGN = Alignment(horizontal='right', vertical='center')


class BOQExportService:
    """Service to export processed BOQ results to Excel"""

    def __init__(self, db: Session):
        self.db = db
        self.processing_service = BOQProcessingService(db)

    def export_processing_result(
        self,
        file_id: int,
        output_path: str,
        include_master_match: bool = True
    ) -> str:
        """
        Export BOQ processing result to Excel file

        Args:
            file_id: BOQ file ID
            output_path: Path to save Excel file
            include_master_match: Include matching against Master database

        Returns:
            Path to created file
        """
        # Get file info
        boq_file = self.db.query(BOQFile).filter(BOQFile.file_id == file_id).first()
        if not boq_file:
            raise ValueError(f"BOQ file {file_id} not found")

        project = self.db.query(Project).filter(Project.project_id == boq_file.project_id).first()

        # Process BOQ
        result = self.processing_service.process_line_items(file_id)

        # Create workbook
        wb = Workbook()

        # Sheet 1: Summary
        self._create_summary_sheet(wb, boq_file, project, result)

        # Sheet 2: All Processed Items
        self._create_processed_items_sheet(wb, result)

        # Sheet 3: Exact Matches
        self._create_match_sheet(wb, result, 'exact', "Exact Matches", HEADER_FILL_GREEN)

        # Sheet 4: Fuzzy Matches (Needs Review)
        self._create_match_sheet(wb, result, 'fuzzy', "Needs Review", HEADER_FILL_ORANGE)

        # Sheet 5: New Items
        self._create_match_sheet(wb, result, 'new', "New Items", HEADER_FILL_RED)

        # Sheet 6: Master Database Reference
        if include_master_match:
            self._create_master_reference_sheet(wb)

        # Remove default sheet
        if 'Sheet' in wb.sheetnames:
            del wb['Sheet']

        # Save
        wb.save(output_path)
        logger.info(f"Exported BOQ processing result to {output_path}")

        return output_path

    def _create_summary_sheet(
        self,
        wb: Workbook,
        boq_file: BOQFile,
        project: Optional[Project],
        result: ProcessingResult
    ):
        """Create summary sheet with statistics"""
        ws = wb.create_sheet("Summary", 0)

        # Title
        ws.merge_cells('A1:F1')
        ws['A1'] = "BOQ PROCESSING RESULT"
        ws['A1'].font = Font(bold=True, size=16)
        ws['A1'].alignment = CENTER_ALIGN

        # File Info
        row = 3
        info_data = [
            ("File Name:", boq_file.file_name),
            ("Project:", project.project_name if project else "N/A"),
            ("Project Code:", project.project_code if project else "N/A"),
            ("Processed At:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        ]

        for label, value in info_data:
            ws.cell(row=row, column=1, value=label).font = Font(bold=True)
            ws.cell(row=row, column=2, value=value)
            row += 1

        # Statistics
        row += 1
        ws.merge_cells(f'A{row}:F{row}')
        ws[f'A{row}'] = "PROCESSING STATISTICS"
        ws[f'A{row}'].font = Font(bold=True, size=14)
        ws[f'A{row}'].fill = HEADER_FILL
        ws[f'A{row}'].font = HEADER_FONT
        row += 1

        stats = [
            ("Total Extracted", result.total_extracted, "100%"),
            ("After Raw Dedupe", result.unique_raw, f"{result.unique_raw/result.total_extracted*100:.1f}%"),
            ("After Normalization", result.unique_normalized, f"{result.unique_normalized/result.total_extracted*100:.1f}%"),
            ("", "", ""),
            ("Exact Matches (≥95%)", result.exact_matches, f"{result.exact_matches/result.unique_normalized*100:.1f}%" if result.unique_normalized else "0%"),
            ("Fuzzy Matches (80-95%)", result.fuzzy_matches, f"{result.fuzzy_matches/result.unique_normalized*100:.1f}%" if result.unique_normalized else "0%"),
            ("New Items (<80%)", result.new_items, f"{result.new_items/result.unique_normalized*100:.1f}%" if result.unique_normalized else "0%"),
            ("", "", ""),
            ("New Items (Deduped)", result.new_items_deduped, "Ready to add to Master"),
        ]

        headers = ["Metric", "Count", "Percentage/Note"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        row += 1

        for metric, count, pct in stats:
            ws.cell(row=row, column=1, value=metric)
            if count != "":
                ws.cell(row=row, column=2, value=count)
            ws.cell(row=row, column=3, value=pct)
            row += 1

        # Match Type Legend
        row += 2
        ws[f'A{row}'] = "MATCH TYPE LEGEND"
        ws[f'A{row}'].font = Font(bold=True)
        row += 1

        legends = [
            ("Exact Match", "≥95% similarity - Auto assign work code", EXACT_MATCH_FILL),
            ("Fuzzy Match", "80-95% similarity - Needs review", FUZZY_MATCH_FILL),
            ("New Item", "<80% similarity - New work item", NEW_ITEM_FILL),
        ]

        for name, desc, fill in legends:
            ws.cell(row=row, column=1, value=name).fill = fill
            ws.cell(row=row, column=2, value=desc)
            row += 1

        # Column widths
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 40
        ws.column_dimensions['C'].width = 25

    def _create_processed_items_sheet(self, wb: Workbook, result: ProcessingResult):
        """Create sheet with all processed items"""
        ws = wb.create_sheet("All Items")

        headers = [
            "No.",
            "Original Description",
            "Normalized Description",
            "Match Type",
            "Similarity %",
            "Master Work Code",
            "Needs Review",
            "Suggested Matches"
        ]

        # Write headers
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = HEADER_FONT
            cell.fill = HEADER_FILL
            cell.alignment = CENTER_ALIGN
            cell.border = THIN_BORDER

        # Write data
        for row_idx, item in enumerate(result.items, 2):
            # Determine fill based on match type
            if item.match_type == 'exact':
                fill = EXACT_MATCH_FILL
            elif item.match_type == 'fuzzy':
                fill = FUZZY_MATCH_FILL
            else:
                fill = NEW_ITEM_FILL

            data = [
                row_idx - 1,
                item.original_description[:200] if len(item.original_description) > 200 else item.original_description,
                item.normalized_description[:200] if len(item.normalized_description) > 200 else item.normalized_description,
                item.match_type.upper(),
                round(item.similarity_score * 100, 1),
                item.master_work_code or "",
                "Yes" if item.needs_review else "No",
                "; ".join([f"{m['work_code']} ({m['similarity']}%)" for m in item.suggested_matches[:3]]) if item.suggested_matches else ""
            ]

            for col, value in enumerate(data, 1):
                cell = ws.cell(row=row_idx, column=col, value=value)
                cell.fill = fill
                cell.border = THIN_BORDER
                if col in [1, 4, 5, 7]:
                    cell.alignment = CENTER_ALIGN
                else:
                    cell.alignment = LEFT_ALIGN

        # Column widths
        col_widths = [6, 60, 60, 12, 12, 20, 12, 50]
        for col, width in enumerate(col_widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = width

        # Freeze header row
        ws.freeze_panes = 'A2'

    def _create_match_sheet(
        self,
        wb: Workbook,
        result: ProcessingResult,
        match_type: str,
        sheet_name: str,
        header_fill: PatternFill
    ):
        """Create sheet for specific match type"""
        ws = wb.create_sheet(sheet_name)

        # Filter items
        items = [i for i in result.items if i.match_type == match_type]

        if not items:
            ws['A1'] = f"No {match_type} matches found"
            return

        # Headers based on match type
        if match_type == 'new':
            headers = [
                "No.",
                "Original Description",
                "Normalized Description",
                "Work Category",
                "Suggested SEC Code",
                "Unit",
                "Action"
            ]
        else:
            headers = [
                "No.",
                "Original Description",
                "Normalized Description",
                "Similarity %",
                "Matched Work Code",
                "Matched Description",
                "SEC Code",
                "Action"
            ]

        # Write headers
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = HEADER_FONT
            cell.fill = header_fill
            cell.alignment = CENTER_ALIGN
            cell.border = THIN_BORDER

        # Write data
        for row_idx, item in enumerate(items, 2):
            if match_type == 'new':
                # Get suggested SEC from top match if available
                suggested_sec = ""
                if item.suggested_matches:
                    suggested_sec = item.suggested_matches[0].get('sec_code', '')

                data = [
                    row_idx - 1,
                    item.original_description[:200],
                    item.normalized_description[:200],
                    "",  # Work category - to be filled
                    suggested_sec,
                    "",  # Unit - to be filled
                    "ADD TO MASTER"
                ]
            else:
                # Get matched master item description
                matched_desc = ""
                matched_sec = ""
                if item.suggested_matches:
                    matched_desc = item.suggested_matches[0].get('description', '')[:100]
                    matched_sec = item.suggested_matches[0].get('sec_code', '')

                data = [
                    row_idx - 1,
                    item.original_description[:150],
                    item.normalized_description[:150],
                    round(item.similarity_score * 100, 1),
                    item.master_work_code or "",
                    matched_desc,
                    matched_sec,
                    "APPROVE" if match_type == 'exact' else "REVIEW"
                ]

            for col, value in enumerate(data, 1):
                cell = ws.cell(row=row_idx, column=col, value=value)
                cell.border = THIN_BORDER
                if col == 1:
                    cell.alignment = CENTER_ALIGN
                elif col == len(data):
                    cell.alignment = CENTER_ALIGN
                    cell.font = Font(bold=True)
                else:
                    cell.alignment = LEFT_ALIGN

        # Column widths
        if match_type == 'new':
            col_widths = [6, 50, 50, 20, 15, 10, 15]
        else:
            col_widths = [6, 45, 45, 12, 20, 40, 12, 12]

        for col, width in enumerate(col_widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = width

        # Freeze header row
        ws.freeze_panes = 'A2'

    def _create_master_reference_sheet(self, wb: Workbook):
        """Create sheet with Master database reference"""
        ws = wb.create_sheet("Master Reference")

        # Get top 100 master items
        master_items = self.db.query(MasterWorkItem).filter(
            MasterWorkItem.is_active == True
        ).order_by(MasterWorkItem.occurrence_count.desc()).limit(100).all()

        if not master_items:
            ws['A1'] = "No master items found"
            return

        headers = [
            "Work Code",
            "Description",
            "SEC Code",
            "Unit",
            "Price (Min)",
            "Price (Avg)",
            "Price (Max)",
            "Occurrences",
            "Verified"
        ]

        # Write headers
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = HEADER_FONT
            cell.fill = HEADER_FILL_PURPLE
            cell.alignment = CENTER_ALIGN
            cell.border = THIN_BORDER

        # Write data
        for row_idx, item in enumerate(master_items, 2):
            data = [
                item.work_code,
                item.description[:100] if item.description and len(item.description) > 100 else item.description,
                item.sec_code,
                item.unit_standard,
                float(item.ref_unit_price_min) if item.ref_unit_price_min else "",
                float(item.ref_unit_price_avg) if item.ref_unit_price_avg else "",
                float(item.ref_unit_price_max) if item.ref_unit_price_max else "",
                item.occurrence_count,
                "Yes" if item.is_verified else "No"
            ]

            for col, value in enumerate(data, 1):
                cell = ws.cell(row=row_idx, column=col, value=value)
                cell.border = THIN_BORDER
                if col in [5, 6, 7]:
                    cell.alignment = RIGHT_ALIGN
                    if value:
                        cell.number_format = '#,##0'
                elif col in [8, 9]:
                    cell.alignment = CENTER_ALIGN
                else:
                    cell.alignment = LEFT_ALIGN

        # Column widths
        col_widths = [25, 60, 12, 8, 15, 15, 15, 12, 10]
        for col, width in enumerate(col_widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = width

        # Freeze header row
        ws.freeze_panes = 'A2'

    def export_line_items_with_classification(
        self,
        file_id: int,
        output_path: str
    ) -> str:
        """
        Export line items with SEC classification results

        Args:
            file_id: BOQ file ID
            output_path: Path to save Excel file

        Returns:
            Path to created file
        """
        # Get line items
        line_items = self.db.query(LineItem).filter(
            LineItem.file_id == file_id
        ).order_by(LineItem.row_number).all()

        if not line_items:
            raise ValueError(f"No line items found for file {file_id}")

        # Get file info
        boq_file = self.db.query(BOQFile).filter(BOQFile.file_id == file_id).first()

        # Create workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Line Items"

        headers = [
            "Row",
            "Original Description",
            "Normalized Description",
            "Work Category",
            "SEC Code",
            "Confidence %",
            "Method",
            "Unit",
            "Quantity",
            "Unit Price",
            "Amount",
            "Needs Review",
            "Validation Issues"
        ]

        # Write headers
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = HEADER_FONT
            cell.fill = HEADER_FILL
            cell.alignment = CENTER_ALIGN
            cell.border = THIN_BORDER

        # Write data
        for row_idx, item in enumerate(line_items, 2):
            # Determine fill based on confidence
            if item.confidence_score and item.confidence_score >= 90:
                fill = EXACT_MATCH_FILL
            elif item.confidence_score and item.confidence_score >= 70:
                fill = FUZZY_MATCH_FILL
            elif item.needs_review:
                fill = NEW_ITEM_FILL
            else:
                fill = PatternFill()  # No fill

            data = [
                item.row_number,
                item.description[:150] if item.description else "",
                item.normalized_description[:150] if item.normalized_description else "",
                item.work_category or "",
                item.sec_code or "",
                float(item.confidence_score) if item.confidence_score else "",
                item.classification_method.value if item.classification_method else "",
                item.unit or "",
                float(item.quantity) if item.quantity else "",
                float(item.unit_price) if item.unit_price else "",
                float(item.amount) if item.amount else "",
                "Yes" if item.needs_review else "No",
                item.validation_issues or ""
            ]

            for col, value in enumerate(data, 1):
                cell = ws.cell(row=row_idx, column=col, value=value)
                if fill.fill_type:
                    cell.fill = fill
                cell.border = THIN_BORDER

                # Alignment and formatting
                if col in [1, 6, 7, 12]:
                    cell.alignment = CENTER_ALIGN
                elif col in [9, 10, 11]:
                    cell.alignment = RIGHT_ALIGN
                    if value:
                        cell.number_format = '#,##0.00' if col == 10 else '#,##0'
                else:
                    cell.alignment = LEFT_ALIGN

        # Column widths
        col_widths = [6, 50, 50, 20, 12, 12, 10, 8, 12, 15, 18, 12, 30]
        for col, width in enumerate(col_widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = width

        # Freeze header row
        ws.freeze_panes = 'A2'

        # Save
        wb.save(output_path)
        logger.info(f"Exported line items to {output_path}")

        return output_path


def get_boq_export_service(db: Session) -> BOQExportService:
    """Factory function to get BOQ export service"""
    return BOQExportService(db)
