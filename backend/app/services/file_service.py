from sqlalchemy.orm import Session
from typing import Optional, List, BinaryIO
from pathlib import Path
import shutil
import logging

from app.models.boq_file import BOQFile, FileStatus
from app.models.line_item import LineItem, ClassificationMethod
from app.utils.excel_processor import ExcelProcessor
from app.services.classifier_service import get_classifier
from app.services.rule_based_classifier import get_rule_based_classifier
from app.core.config import settings

logger = logging.getLogger(__name__)


class FileService:
    """Service for handling BOQ file operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.excel_processor = ExcelProcessor()
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def save_uploaded_file(
        self,
        file: BinaryIO,
        filename: str,
        project_id: int
    ) -> str:
        """
        Save uploaded file to disk
        Returns: file_path
        """
        # Create project-specific directory
        project_dir = self.upload_dir / f"project_{project_id}"
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = project_dir / filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file, buffer)
        
        logger.info(f"File saved: {file_path}")
        return str(file_path)
    
    def analyze_file_structure(self, file_path: str) -> dict:
        """
        Analyze Excel file structure without processing
        Returns structure metadata for preview
        """
        return self.excel_processor.parse_structure(file_path)
    
    def process_file(
        self,
        file_id: int,
        file_path: str,
        column_mapping: dict,
        user_id: Optional[int] = None
    ) -> dict:
        """
        Process Excel file: parse, clean, classify, and save to database
        """
        logger.info(f"Processing file {file_id}: {file_path}")
        
        # Get file record
        boq_file = self.db.query(BOQFile).filter(BOQFile.file_id == file_id).first()
        if not boq_file:
            raise ValueError(f"BOQ file {file_id} not found")
        
        # Read and process Excel
        df = self.excel_processor.read_excel(file_path)

        # Detect header row
        header_row = self.excel_processor.detect_header_row(df)
        df.columns = df.iloc[header_row]
        df = df.iloc[header_row + 1:].reset_index(drop=True)

        # Detect or use provided column mapping
        if not column_mapping:
            column_mapping = self.excel_processor.detect_columns(df.columns.tolist())
        else:
            # IMPORTANT: Frontend sends {standard_name: excel_column}
            # But clean_data needs {excel_column: standard_name}
            # So we need to invert the mapping
            column_mapping = {v: k for k, v in column_mapping.items()}
            logger.info(f"Inverted column mapping: {column_mapping}")

        # Clean data
        df_clean = self.excel_processor.clean_data(df, column_mapping)
        
        # Extract line items
        line_items_data = self.excel_processor.extract_line_items(
            df_clean,
            file_id=file_id,
            project_id=boq_file.project_id
        )

        # FR-CL-06: Configurable threshold (default 80%)
        confidence_threshold = settings.CLASSIFICATION_THRESHOLD * 100  # Convert 0.8 to 80

        # FR-CL-01 & FR-CL-04: Try ML classifier first, fallback to rule-based
        classifier = None
        classifier_type = None

        try:
            classifier = get_classifier(self.db)
            classifier_type = 'ML'
            logger.info("Using ML-based classifier")
        except Exception as e:
            logger.warning(f"ML classifier not available: {e}")
            try:
                # FR-CL-04: Rule-based fallback
                classifier = get_rule_based_classifier(self.db)
                classifier_type = 'RULE'
                logger.info("Using rule-based classifier as fallback")
            except Exception as e2:
                logger.error(f"Rule-based classifier also failed: {e2}")
                classifier = None
                classifier_type = None

        # Process and save each line item
        processed_count = 0
        total_amount = 0

        for item_data in line_items_data:
            # FR-CL-01: Auto classification
            if classifier and item_data.get('description'):
                try:
                    # FR-CL-03: Get top 3 SEC codes
                    classification_results = classifier.classify(
                        item_data['description'],
                        top_k=3
                    )

                    if classification_results:
                        # Use the best match (top 1)
                        sec_code, confidence = classification_results[0]
                        item_data['sec_code'] = sec_code
                        item_data['confidence_score'] = confidence
                        item_data['classification_method'] = ClassificationMethod.auto

                        # FR-DC-03: Flag for review if confidence is low
                        if confidence < confidence_threshold:
                            item_data['needs_review'] = True
                            current_issues = item_data.get('validation_issues', '')
                            item_data['validation_issues'] = (
                                (current_issues + '; ' if current_issues else '') +
                                f'Low confidence ({confidence:.1f}%)'
                            )

                        # Store top 3 suggestions as metadata (for future use)
                        # Could be stored in a separate table or JSON field
                        logger.debug(
                            f"Classified '{item_data['description'][:50]}...' as {sec_code} "
                            f"({confidence:.1f}%) using {classifier_type}"
                        )
                    else:
                        item_data['sec_code'] = None
                        item_data['confidence_score'] = 0
                        item_data['classification_method'] = ClassificationMethod.auto
                        item_data['needs_review'] = True
                        current_issues = item_data.get('validation_issues', '')
                        item_data['validation_issues'] = (
                            (current_issues + '; ' if current_issues else '') +
                            'No classification match'
                        )

                except Exception as e:
                    logger.warning(f"Classification failed for item: {e}")
                    item_data['sec_code'] = None
                    item_data['confidence_score'] = 0
                    item_data['classification_method'] = ClassificationMethod.auto
                    item_data['needs_review'] = True
                    current_issues = item_data.get('validation_issues', '')
                    item_data['validation_issues'] = (
                        (current_issues + '; ' if current_issues else '') +
                        'Classification error'
                    )
            else:
                # No classifier available or empty description
                item_data['sec_code'] = None
                item_data['confidence_score'] = 0
                item_data['classification_method'] = ClassificationMethod.auto
                if not item_data.get('description'):
                    item_data['needs_review'] = True

            # Create line item
            line_item = LineItem(**item_data)
            self.db.add(line_item)

            processed_count += 1
            total_amount += item_data['amount']

        # Update file record
        boq_file.total_rows = processed_count
        boq_file.total_amount = total_amount
        boq_file.status = FileStatus.draft  # lowercase

        # Commit all changes
        self.db.commit()

        logger.info(f"File processing complete: {processed_count} items, total amount: {total_amount}")
        
        return {
            'file_id': file_id,
            'processed_items': processed_count,
            'total_amount': float(total_amount),
            'status': 'success'
        }
    
    def get_file(self, file_id: int) -> Optional[BOQFile]:
        """Get BOQ file by ID"""
        return self.db.query(BOQFile).filter(BOQFile.file_id == file_id).first()
    
    def get_files_by_project(self, project_id: int) -> List[BOQFile]:
        """Get all files for a project"""
        return self.db.query(BOQFile).filter(
            BOQFile.project_id == project_id
        ).order_by(BOQFile.uploaded_at.desc()).all()
    
    def delete_file(self, file_id: int) -> bool:
        """Delete BOQ file and associated line items"""
        boq_file = self.get_file(file_id)
        if not boq_file:
            return False
        
        # Delete physical file
        if boq_file.file_path and Path(boq_file.file_path).exists():
            Path(boq_file.file_path).unlink()
        
        # Delete database record (cascade will delete line items)
        self.db.delete(boq_file)
        self.db.commit()
        
        logger.info(f"File {file_id} deleted")
        return True
    
    def check_duplicate(self, file_hash: str) -> Optional[BOQFile]:
        """Check if file with same hash already exists"""
        return self.db.query(BOQFile).filter(
            BOQFile.file_hash == file_hash
        ).first()
