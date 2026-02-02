from sqlalchemy.orm import Session
from typing import Optional, List, BinaryIO
from pathlib import Path
import shutil
import logging
import pandas as pd

from app.models.boq_file import BOQFile, FileStatus
from app.models.line_item import LineItem, ClassificationMethod
from app.utils.excel_processor import ExcelProcessor
from app.services.classifier_service import get_classifier
from app.services.rule_based_classifier import get_rule_based_classifier
from app.services.description_normalizer import DescriptionNormalizer
from app.services.ai_normalizer import get_ai_normalizer, AINormalizer
from app.services.file_context_analyzer import get_file_context_analyzer, FileContext
from app.services.domain_validator import get_domain_validator
from app.services.traffic_equipment_normalizer import get_traffic_normalizer
from app.services.mep_equipment_normalizer import get_mep_normalizer
from app.core.config import settings

logger = logging.getLogger(__name__)


class FileService:
    """Service for handling BOQ file operations"""

    def __init__(self, db: Session):
        self.db = db
        self.excel_processor = ExcelProcessor()
        self.normalizer = DescriptionNormalizer()
        self.ai_normalizer = None
        self.context_analyzer = None
        self.domain_validator = None
        self.traffic_normalizer = None
        self.mep_normalizer = None

        # Initialize AI normalizer if enabled
        if settings.AI_NORMALIZATION_ENABLED:
            try:
                self.ai_normalizer = get_ai_normalizer()
                logger.info("AI normalizer initialized for enhanced accuracy")
            except Exception as e:
                logger.warning(f"AI normalizer not available: {e}")

        # Initialize context analyzer if enabled
        if settings.AI_CONTEXT_ANALYSIS_ENABLED:
            try:
                self.context_analyzer = get_file_context_analyzer()
                logger.info("File context analyzer initialized")
            except Exception as e:
                logger.warning(f"Context analyzer not available: {e}")

        # Initialize domain validator if enabled
        if settings.AI_DOMAIN_VALIDATION_ENABLED:
            try:
                self.domain_validator = get_domain_validator()
                logger.info("Domain validator initialized")
            except Exception as e:
                logger.warning(f"Domain validator not available: {e}")

        # Initialize traffic equipment normalizer
        try:
            self.traffic_normalizer = get_traffic_normalizer()
        except Exception as e:
            logger.warning(f"Traffic normalizer not available: {e}")

        # Initialize MEP equipment normalizer
        try:
            self.mep_normalizer = get_mep_normalizer()
        except Exception as e:
            logger.warning(f"MEP normalizer not available: {e}")

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

        Multi-Pass AI Analysis:
        - Pass 1: Analyze file context (project type, sections, terms)
        - Pass 2: Contextual extraction with neighboring rows
        - Pass 3: Batch normalization with AI enhancement
        - Pass 4: Domain validation and correction
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

        # ===== PASS 1: Analyze file context =====
        file_context = None
        if self.context_analyzer and settings.AI_CONTEXT_ANALYSIS_ENABLED:
            try:
                # Find description column index
                desc_col = 1  # Default
                for i, col in enumerate(df_clean.columns):
                    if 'description' in str(col).lower():
                        desc_col = i
                        break

                file_context = self.context_analyzer.analyze(df_clean, desc_col)
                logger.info(
                    f"File context: project_type={file_context.project_type}, "
                    f"sections={len(file_context.sections)}, confidence={file_context.confidence:.2f}"
                )
            except Exception as e:
                logger.warning(f"File context analysis failed: {e}")

        # Extract line items
        line_items_data = self.excel_processor.extract_line_items(
            df_clean,
            file_id=file_id,
            project_id=boq_file.project_id
        )

        # ===== PASS 2 & 3: Multi-pass normalization =====
        descriptions = [item.get('description', '') for item in line_items_data]
        normalization_results = self._multi_pass_normalize(descriptions, file_context)

        # ===== PASS 4: Domain validation =====
        validation_results = None
        if self.domain_validator and settings.AI_DOMAIN_VALIDATION_ENABLED:
            try:
                validation_results = self.domain_validator.validate_batch(
                    normalization_results,
                    file_context
                )
            except Exception as e:
                logger.warning(f"Domain validation failed: {e}")

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

        for i, item_data in enumerate(line_items_data):
            # Apply normalization result
            if i < len(normalization_results):
                norm_result = normalization_results[i]
                item_data['normalized_description'] = norm_result.normalized
                item_data['work_category'] = norm_result.work_category
                item_data['normalization_confidence'] = norm_result.confidence

                # Apply domain validation correction if available
                if validation_results and i < len(validation_results):
                    val_result = validation_results[i]
                    if val_result.corrected_normalized:
                        item_data['normalized_description'] = val_result.corrected_normalized
                        logger.debug(
                            f"Applied validation correction: {norm_result.normalized[:30]}... -> "
                            f"{val_result.corrected_normalized[:30]}..."
                        )
            else:
                # Fallback to simple normalization
                original_description = item_data.get('description', '')
                if original_description:
                    item_data['normalized_description'] = self.normalizer.normalize(original_description)
                    item_data['work_category'] = self.normalizer.identify_work_category(original_description)
                    item_data['normalization_confidence'] = 50.0

            # FR-CL-01: Auto classification - use normalized description for better accuracy
            classification_text = item_data.get('normalized_description') or item_data.get('description')
            if classifier and classification_text:
                try:
                    # FR-CL-03: Get top 3 SEC codes
                    classification_results = classifier.classify(
                        classification_text,
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
        boq_file.status = FileStatus.draft

        # Commit all changes
        self.db.commit()

        # Calculate quality metrics
        quality_metrics = {}
        if self.domain_validator and validation_results:
            quality_metrics = self.domain_validator.get_quality_metrics(
                normalization_results,
                validation_results
            )

        logger.info(f"File processing complete: {processed_count} items, total amount: {total_amount}")

        return {
            'file_id': file_id,
            'processed_items': processed_count,
            'total_amount': float(total_amount),
            'status': 'success',
            'file_context': {
                'project_type': file_context.project_type if file_context else 'unknown',
                'sections': len(file_context.sections) if file_context else 0,
            } if file_context else None,
            'quality_metrics': quality_metrics
        }

    def _multi_pass_normalize(
        self,
        descriptions: List[str],
        file_context: Optional[FileContext]
    ) -> List:
        """
        Multi-pass normalization with context

        Pass 2: Rule-based with traffic equipment handling
        Pass 3: AI enhancement for complex items
        """
        from app.services.ai_normalizer import NormalizationResult

        results = []

        # Process each description
        for desc in descriptions:
            if not desc or not desc.strip():
                results.append(NormalizationResult(
                    original=desc,
                    normalized="",
                    work_category="general",
                    confidence=0,
                    components={},
                    ai_enhanced=False
                ))
                continue

            # Check if traffic equipment (specialized handling)
            if self.traffic_normalizer and self.traffic_normalizer.is_traffic_equipment(desc):
                traffic_result = self.traffic_normalizer.normalize(desc)
                results.append(NormalizationResult(
                    original=desc,
                    normalized=traffic_result.normalized,
                    work_category='road_infrastructure',
                    confidence=traffic_result.confidence * 100,
                    components=traffic_result.specs,
                    ai_enhanced=False,
                    pattern_used=traffic_result.equipment_type
                ))
            # Check if MEP equipment (specialized handling)
            elif self.mep_normalizer and self.mep_normalizer.is_mep_equipment(desc):
                mep_result = self.mep_normalizer.normalize(desc)
                results.append(NormalizationResult(
                    original=desc,
                    normalized=mep_result.normalized,
                    work_category='steel_mep',
                    confidence=mep_result.confidence * 100,
                    components=mep_result.specs,
                    ai_enhanced=False,
                    pattern_used=mep_result.equipment_type
                ))
            else:
                # Standard normalization
                if self.ai_normalizer:
                    result = self.ai_normalizer.normalize(desc, use_ai=False)
                    results.append(result)
                else:
                    normalized = self.normalizer.normalize(desc)
                    category = self.normalizer.identify_work_category(desc)
                    components = self.normalizer.parse_description(desc)

                    confidence = 100.0
                    if not components.get('verb'):
                        confidence -= 30
                    if not components.get('material'):
                        confidence -= 20
                    if not components.get('position'):
                        confidence -= 15
                    if not components.get('grade') and not components.get('specs'):
                        confidence -= 15

                    results.append(NormalizationResult(
                        original=desc,
                        normalized=normalized,
                        work_category=category,
                        confidence=max(0, confidence),
                        components=components,
                        ai_enhanced=False
                    ))

        # Pass 3: AI enhancement with file context
        if self.ai_normalizer and file_context:
            results = self.ai_normalizer.normalize_with_file_context(
                descriptions,
                file_context
            )

        return results

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
