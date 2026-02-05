"""
Template Service for Column Mapping Templates

Handles CRUD operations, template matching, and usage tracking.
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.models.column_mapping_template import ColumnMappingTemplate, TemplateVisibility
from app.models.template_usage_log import TemplateUsageLog, MatchType, UsageAction
from app.services.fingerprint_generator import (
    FingerprintGenerator,
    FingerprintResult,
    FingerprintComponents,
    get_fingerprint_generator
)
from app.schemas.template import (
    TemplateMatchResult,
    MatchType as SchemaMatchType
)

logger = logging.getLogger(__name__)


class TemplateService:
    """Service for managing column mapping templates."""

    def __init__(self, db: Session):
        self.db = db
        self.fingerprint_generator = get_fingerprint_generator()

    # CRUD Operations

    def create_template(
        self,
        name: str,
        column_mapping: Dict[str, str],
        description: Optional[str] = None,
        header_row_hint: int = 0,
        sheet_name_pattern: Optional[str] = None,
        visibility: TemplateVisibility = TemplateVisibility.private,
        created_by: Optional[int] = None,
        is_system: bool = False
    ) -> ColumnMappingTemplate:
        """
        Create a new column mapping template.

        Args:
            name: Template name
            column_mapping: Mapping of original columns to standard columns
            description: Optional description
            header_row_hint: Hint for header row location
            sheet_name_pattern: Optional regex pattern for sheet name matching
            visibility: Template visibility (private, team, public)
            created_by: User ID of creator
            is_system: Whether this is a system template

        Returns:
            Created ColumnMappingTemplate instance
        """
        # Generate fingerprint from column names
        column_names = list(column_mapping.keys())
        fingerprint_result = self.fingerprint_generator.generate(column_names)

        template = ColumnMappingTemplate(
            name=name,
            description=description,
            column_mapping=column_mapping,
            header_row_hint=header_row_hint,
            sheet_name_pattern=sheet_name_pattern,
            fingerprint=fingerprint_result.fingerprint,
            fingerprint_components=fingerprint_result.components.to_dict(),
            visibility=visibility,
            created_by=created_by,
            is_system=is_system
        )

        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)

        logger.info(f"Created template '{name}' (id={template.template_id}) with fingerprint {fingerprint_result.fingerprint[:16]}...")

        return template

    def get_template(self, template_id: int) -> Optional[ColumnMappingTemplate]:
        """Get a template by ID."""
        return self.db.query(ColumnMappingTemplate).filter(
            ColumnMappingTemplate.template_id == template_id
        ).first()

    def get_templates(
        self,
        user_id: Optional[int] = None,
        visibility: Optional[TemplateVisibility] = None,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[ColumnMappingTemplate], int]:
        """
        Get templates with filtering and pagination.

        Args:
            user_id: Filter by owner
            visibility: Filter by visibility
            include_inactive: Include soft-deleted templates
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            Tuple of (templates list, total count)
        """
        query = self.db.query(ColumnMappingTemplate)

        # Filter by active status
        if not include_inactive:
            query = query.filter(ColumnMappingTemplate.is_active == True)

        # Filter by visibility
        if visibility:
            query = query.filter(ColumnMappingTemplate.visibility == visibility)
        elif user_id:
            # Show user's own templates + team/public templates
            query = query.filter(
                (ColumnMappingTemplate.created_by == user_id) |
                (ColumnMappingTemplate.visibility.in_([
                    TemplateVisibility.team,
                    TemplateVisibility.public
                ]))
            )

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        templates = query.order_by(
            desc(ColumnMappingTemplate.use_count),
            desc(ColumnMappingTemplate.created_at)
        ).offset(skip).limit(limit).all()

        return templates, total

    def update_template(
        self,
        template_id: int,
        **kwargs
    ) -> Optional[ColumnMappingTemplate]:
        """
        Update an existing template.

        Args:
            template_id: Template ID to update
            **kwargs: Fields to update

        Returns:
            Updated template or None if not found
        """
        template = self.get_template(template_id)
        if not template:
            return None

        # If column_mapping changes, regenerate fingerprint
        if 'column_mapping' in kwargs and kwargs['column_mapping']:
            column_names = list(kwargs['column_mapping'].keys())
            fingerprint_result = self.fingerprint_generator.generate(column_names)
            kwargs['fingerprint'] = fingerprint_result.fingerprint
            kwargs['fingerprint_components'] = fingerprint_result.components.to_dict()

        # Update fields
        for key, value in kwargs.items():
            if hasattr(template, key) and value is not None:
                setattr(template, key, value)

        self.db.commit()
        self.db.refresh(template)

        logger.info(f"Updated template id={template_id}")

        return template

    def delete_template(self, template_id: int, soft: bool = True) -> bool:
        """
        Delete a template.

        Args:
            template_id: Template ID to delete
            soft: If True, soft delete (mark as inactive)

        Returns:
            True if deleted, False if not found
        """
        template = self.get_template(template_id)
        if not template:
            return False

        if soft:
            template.is_active = False
            self.db.commit()
            logger.info(f"Soft deleted template id={template_id}")
        else:
            self.db.delete(template)
            self.db.commit()
            logger.info(f"Hard deleted template id={template_id}")

        return True

    # Template Matching

    def find_matching_templates(
        self,
        column_names: List[str],
        sheet_name: Optional[str] = None,
        min_similarity: float = 75.0,
        limit: int = 5,
        user_id: Optional[int] = None
    ) -> Tuple[Optional[TemplateMatchResult], List[TemplateMatchResult], str]:
        """
        Find templates that match the given column structure.

        Args:
            column_names: List of column names from uploaded file
            sheet_name: Optional sheet name for additional matching
            min_similarity: Minimum similarity threshold (0-100)
            limit: Maximum alternatives to return
            user_id: User ID for visibility filtering

        Returns:
            Tuple of (best_match, alternatives, input_fingerprint)
        """
        # Generate fingerprint for input columns
        input_fp = self.fingerprint_generator.generate(column_names)

        # Try exact match first
        exact_match = self.db.query(ColumnMappingTemplate).filter(
            ColumnMappingTemplate.fingerprint == input_fp.fingerprint,
            ColumnMappingTemplate.is_active == True
        ).first()

        if exact_match:
            best = self._template_to_match_result(
                exact_match,
                100.0,
                SchemaMatchType.exact,
                len(column_names)
            )
            logger.info(f"Found exact match: template id={exact_match.template_id}")
            return best, [], input_fp.fingerprint

        # Get all active templates for fuzzy matching
        query = self.db.query(ColumnMappingTemplate).filter(
            ColumnMappingTemplate.is_active == True
        )

        # Apply visibility filter
        if user_id:
            query = query.filter(
                (ColumnMappingTemplate.created_by == user_id) |
                (ColumnMappingTemplate.visibility.in_([
                    TemplateVisibility.team,
                    TemplateVisibility.public
                ])) |
                (ColumnMappingTemplate.is_system == True)
            )

        templates = query.all()

        # Calculate similarity for each template
        matches = []
        for template in templates:
            if not template.fingerprint_components:
                continue

            # Reconstruct FingerprintComponents from stored dict
            stored_components = FingerprintComponents(
                column_count=template.fingerprint_components.get('column_count', 0),
                column_keywords=template.fingerprint_components.get('column_keywords', []),
                column_order_hash=template.fingerprint_components.get('column_order_hash', ''),
                data_type_signature=template.fingerprint_components.get('data_type_signature')
            )

            similarity = self.fingerprint_generator.calculate_similarity(
                input_fp.components,
                stored_components
            )

            if similarity >= min_similarity:
                result = self._template_to_match_result(
                    template,
                    similarity,
                    SchemaMatchType.fuzzy,
                    len(column_names)
                )
                matches.append((similarity, result))

        # Sort by similarity (descending)
        matches.sort(key=lambda x: x[0], reverse=True)

        if not matches:
            logger.info(f"No matching templates found above {min_similarity}% threshold")
            return None, [], input_fp.fingerprint

        # Best match and alternatives
        best_match = matches[0][1]
        alternatives = [m[1] for m in matches[1:limit+1]]

        logger.info(
            f"Found {len(matches)} matching templates. "
            f"Best: id={best_match.template_id} ({best_match.similarity_score}%)"
        )

        return best_match, alternatives, input_fp.fingerprint

    def _template_to_match_result(
        self,
        template: ColumnMappingTemplate,
        similarity: float,
        match_type: SchemaMatchType,
        total_columns: int
    ) -> TemplateMatchResult:
        """Convert a template to a match result."""
        return TemplateMatchResult(
            template_id=template.template_id,
            template_name=template.name,
            similarity_score=similarity,
            match_type=match_type,
            column_mapping=template.column_mapping,
            matched_columns=len(template.column_mapping),
            total_columns=total_columns,
            fingerprint=template.fingerprint
        )

    # Usage Tracking

    def log_usage(
        self,
        template_id: int,
        action: UsageAction,
        match_type: MatchType,
        file_id: Optional[int] = None,
        match_score: Optional[float] = None,
        was_successful: bool = True,
        columns_mapped: Optional[int] = None,
        columns_total: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> TemplateUsageLog:
        """
        Log template usage.

        Args:
            template_id: ID of the template used
            action: How the template was applied
            match_type: Type of match (exact, fuzzy, manual)
            file_id: Optional file ID
            match_score: Optional match score
            was_successful: Whether the mapping was successful
            columns_mapped: Number of columns mapped
            columns_total: Total number of columns
            user_id: User who applied the template

        Returns:
            Created TemplateUsageLog instance
        """
        usage_log = TemplateUsageLog(
            template_id=template_id,
            file_id=file_id,
            match_score=match_score,
            match_type=match_type,
            was_successful=was_successful,
            columns_mapped=columns_mapped,
            columns_total=columns_total,
            user_id=user_id,
            action=action
        )

        self.db.add(usage_log)

        # Update template usage stats
        template = self.get_template(template_id)
        if template:
            template.use_count = (template.use_count or 0) + 1
            template.last_used_at = datetime.utcnow()

            # Recalculate success rate
            if not was_successful:
                total_uses = self.db.query(TemplateUsageLog).filter(
                    TemplateUsageLog.template_id == template_id
                ).count()
                successful_uses = self.db.query(TemplateUsageLog).filter(
                    TemplateUsageLog.template_id == template_id,
                    TemplateUsageLog.was_successful == True
                ).count()
                if total_uses > 0:
                    template.match_success_rate = (successful_uses / total_uses) * 100

        self.db.commit()
        self.db.refresh(usage_log)

        logger.info(f"Logged usage for template id={template_id}, action={action}")

        return usage_log

    def get_statistics(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get template usage statistics.

        Args:
            user_id: Optional user ID to filter by

        Returns:
            Dictionary of statistics
        """
        # Template counts
        total_templates = self.db.query(ColumnMappingTemplate).count()
        active_templates = self.db.query(ColumnMappingTemplate).filter(
            ColumnMappingTemplate.is_active == True
        ).count()
        system_templates = self.db.query(ColumnMappingTemplate).filter(
            ColumnMappingTemplate.is_system == True,
            ColumnMappingTemplate.is_active == True
        ).count()

        # User templates
        user_templates_query = self.db.query(ColumnMappingTemplate).filter(
            ColumnMappingTemplate.is_system == False,
            ColumnMappingTemplate.is_active == True
        )
        if user_id:
            user_templates_query = user_templates_query.filter(
                ColumnMappingTemplate.created_by == user_id
            )
        user_templates = user_templates_query.count()

        # Usage stats
        total_uses = self.db.query(TemplateUsageLog).count()
        successful_uses = self.db.query(TemplateUsageLog).filter(
            TemplateUsageLog.was_successful == True
        ).count()

        avg_success_rate = (successful_uses / total_uses * 100) if total_uses > 0 else 100.0

        # Most used templates
        most_used = self.db.query(ColumnMappingTemplate).filter(
            ColumnMappingTemplate.is_active == True
        ).order_by(desc(ColumnMappingTemplate.use_count)).limit(5).all()

        most_used_list = [
            {
                "template_id": t.template_id,
                "name": t.name,
                "use_count": t.use_count,
                "success_rate": float(t.match_success_rate or 100)
            }
            for t in most_used
        ]

        # Recent usage
        recent_logs = self.db.query(TemplateUsageLog).order_by(
            desc(TemplateUsageLog.created_at)
        ).limit(10).all()

        return {
            "total_templates": total_templates,
            "active_templates": active_templates,
            "system_templates": system_templates,
            "user_templates": user_templates,
            "total_uses": total_uses,
            "successful_uses": successful_uses,
            "average_success_rate": round(avg_success_rate, 2),
            "most_used_templates": most_used_list,
            "recent_uses": recent_logs
        }


def get_template_service(db: Session) -> TemplateService:
    """Get a TemplateService instance."""
    return TemplateService(db)
