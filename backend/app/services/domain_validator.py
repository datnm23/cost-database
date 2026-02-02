"""
Domain Validator Service
Pass 4: Validate normalized descriptions against domain-specific rules

Features:
1. Validate normalization results against domain rules
2. Trigger AI correction for failed validations
3. Provide quality metrics for normalized batch
"""
import re
import logging
from typing import Dict, List, Optional, Callable, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field

from app.core.config import settings

if TYPE_CHECKING:
    from app.services.ai_normalizer import NormalizationResult
    from app.services.file_context_analyzer import FileContext

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """Represents a validation issue"""
    rule_name: str
    description: str
    severity: str  # 'error', 'warning', 'info'
    fix_suggestion: str


@dataclass
class ValidationResult:
    """Result of domain validation"""
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    corrected_normalized: Optional[str] = None
    ai_correction_applied: bool = False


# Domain rules organized by project type
DOMAIN_RULES = {
    'road_infrastructure': {
        'btn_grade_required': {
            'condition': lambda item: 'btn' in item.normalized.lower(),
            'check': lambda item: bool(re.search(r'BTN\s*C\d+', item.normalized, re.IGNORECASE)),
            'severity': 'warning',
            'description': 'BTN thiếu grade (C12.5, C19, etc.)',
            'fix_suggestion': 'Thêm grade BTN (ví dụ: BTN C19)'
        },
        'compaction_k_grade': {
            'condition': lambda item: item.work_category == 'earthworks_piling' and 'đắp' in item.normalized.lower(),
            'check': lambda item: bool(re.search(r'K9[0-8]', item.normalized)),
            'severity': 'info',
            'description': 'Công tác đầm nén thiếu K grade',
            'fix_suggestion': 'Thêm K grade (K90, K95, K98)'
        },
        'traffic_sign_complete': {
            'condition': lambda item: 'biển báo' in item.normalized.lower(),
            'check': lambda item: bool(re.search(r'(tam giác|tròn|chữ nhật|vuông).*\d+|[ABCR]\d+', item.normalized, re.IGNORECASE)),
            'severity': 'warning',
            'description': 'Biển báo thiếu loại hoặc kích thước',
            'fix_suggestion': 'Thêm loại biển (tam giác/tròn) và kích thước (A70, B40)'
        },
        'monitoring_type': {
            'condition': lambda item: 'quan trắc' in item.normalized.lower(),
            'check': lambda item: bool(re.search(r'quan trắc\s+(lún|nghiêng|chuyển vị|nứt)', item.normalized, re.IGNORECASE)),
            'severity': 'warning',
            'description': 'Bản quan trắc thiếu loại',
            'fix_suggestion': 'Thêm loại quan trắc (lún, nghiêng, chuyển vị)'
        },
        'tack_coat_material': {
            'condition': lambda item: 'thấm bám' in item.normalized.lower() or 'tưới' in item.normalized.lower(),
            'check': lambda item: bool(re.search(r'nhựa|bitum|dầu', item.normalized, re.IGNORECASE)),
            'severity': 'info',
            'description': 'Lớp thấm bám thiếu vật liệu',
            'fix_suggestion': 'Thêm vật liệu (nhựa pha dầu)'
        },
        'topsoil_context': {
            'condition': lambda item: 'đất màu' in item.normalized.lower(),
            'check': lambda item: bool(re.search(r'trồng|cây|cỏ|hố móng', item.normalized, re.IGNORECASE)),
            'severity': 'info',
            'description': 'Đất màu thiếu context (trồng cây)',
            'fix_suggestion': 'Thêm mục đích sử dụng (hố móng trồng cây)'
        },
    },
    'building': {
        'concrete_grade': {
            'condition': lambda item: 'bê tông' in item.normalized.lower() and 'lót' not in item.normalized.lower(),
            'check': lambda item: bool(re.search(r'M\d{2,3}', item.normalized)),
            'severity': 'warning',
            'description': 'Bê tông thiếu mác',
            'fix_suggestion': 'Thêm mác bê tông (M200, M250, M300)'
        },
        'rebar_grade': {
            'condition': lambda item: 'cốt thép' in item.normalized.lower(),
            'check': lambda item: bool(re.search(r'CB\d{3}|D[<>=]*\d+', item.normalized)),
            'severity': 'warning',
            'description': 'Cốt thép thiếu loại hoặc đường kính',
            'fix_suggestion': 'Thêm loại thép (CB300, CB400) hoặc đường kính'
        },
        'brick_type': {
            'condition': lambda item: 'gạch' in item.normalized.lower() and 'xây' in item.normalized.lower(),
            'check': lambda item: bool(re.search(r'gạch\s+(đặc|ống|block)', item.normalized, re.IGNORECASE)),
            'severity': 'info',
            'description': 'Gạch xây thiếu loại',
            'fix_suggestion': 'Thêm loại gạch (đặc, ống)'
        },
        'plaster_thickness': {
            'condition': lambda item: 'trát' in item.normalized.lower(),
            'check': lambda item: bool(re.search(r'dày\s*\d+', item.normalized, re.IGNORECASE)),
            'severity': 'info',
            'description': 'Trát thiếu chiều dày',
            'fix_suggestion': 'Thêm chiều dày (dày 15mm)'
        },
    },
    'mep': {
        'pipe_material': {
            'condition': lambda item: 'ống' in item.normalized.lower(),
            'check': lambda item: bool(re.search(r'(PPR|PVC|HDPE|thép)', item.normalized, re.IGNORECASE)),
            'severity': 'warning',
            'description': 'Ống thiếu vật liệu',
            'fix_suggestion': 'Thêm vật liệu ống (PPR, PVC, HDPE)'
        },
        'pipe_diameter': {
            'condition': lambda item: 'ống' in item.normalized.lower(),
            'check': lambda item: bool(re.search(r'D\d+|Ø\d+|phi\s*\d+', item.normalized, re.IGNORECASE)),
            'severity': 'warning',
            'description': 'Ống thiếu đường kính',
            'fix_suggestion': 'Thêm đường kính (D50, D110)'
        },
    },
    'general': {
        'has_verb': {
            'condition': lambda item: True,
            'check': lambda item: bool(re.match(r'^[A-ZĐỐỤẮẾÀẢẤ]', item.normalized)),
            'severity': 'error',
            'description': 'Thiếu động từ hoặc động từ không viết hoa',
            'fix_suggestion': 'Bắt đầu bằng động từ viết hoa (Đào, Đổ, Xây, Lắp đặt)'
        },
        'reasonable_length': {
            'condition': lambda item: True,
            'check': lambda item: 10 <= len(item.normalized) <= 100,
            'severity': 'warning',
            'description': 'Độ dài không phù hợp (khuyến nghị 10-100 ký tự)',
            'fix_suggestion': 'Điều chỉnh độ dài mô tả'
        },
        'no_brackets': {
            'condition': lambda item: True,
            'check': lambda item: '[' not in item.normalized and ']' not in item.normalized,
            'severity': 'info',
            'description': 'Không nên dùng dấu ngoặc vuông',
            'fix_suggestion': 'Loại bỏ dấu ngoặc vuông'
        },
    },
}


class DomainValidator:
    """
    Validates normalized descriptions against domain-specific rules

    Pass 4 of multi-pass AI analysis strategy
    """

    def __init__(self):
        self._ai_normalizer = None

    def _get_ai_normalizer(self):
        """Lazy load AI normalizer to avoid circular import"""
        if self._ai_normalizer is None:
            from app.services.ai_normalizer import get_ai_normalizer
            self._ai_normalizer = get_ai_normalizer()
        return self._ai_normalizer

    def validate(
        self,
        item: 'NormalizationResult',
        file_context: Optional['FileContext'] = None
    ) -> ValidationResult:
        """
        Validate a single normalization result

        Args:
            item: NormalizationResult to validate
            file_context: Optional file context for project-specific rules

        Returns:
            ValidationResult with issues and optional correction
        """
        issues = []

        # Determine which rule sets to apply
        rule_sets = ['general']
        if file_context:
            rule_sets.insert(0, file_context.project_type)
        elif item.work_category == 'road_infrastructure':
            rule_sets.insert(0, 'road_infrastructure')

        # Apply rules
        for rule_set_name in rule_sets:
            if rule_set_name not in DOMAIN_RULES:
                continue

            rule_set = DOMAIN_RULES[rule_set_name]
            for rule_name, rule in rule_set.items():
                try:
                    # Check if rule applies
                    if rule['condition'](item):
                        # Run validation check
                        if not rule['check'](item):
                            issues.append(ValidationIssue(
                                rule_name=rule_name,
                                description=rule['description'],
                                severity=rule['severity'],
                                fix_suggestion=rule['fix_suggestion']
                            ))
                except Exception as e:
                    logger.warning(f"Rule {rule_name} failed: {e}")

        # Determine if valid
        has_errors = any(i.severity == 'error' for i in issues)
        is_valid = not has_errors

        result = ValidationResult(
            is_valid=is_valid,
            issues=issues
        )

        # Try AI correction for items with warnings/errors
        if issues and settings.AI_DOMAIN_VALIDATION_ENABLED:
            error_count = sum(1 for i in issues if i.severity == 'error')
            warning_count = sum(1 for i in issues if i.severity == 'warning')

            # Only use AI for significant issues
            if error_count > 0 or warning_count >= 2:
                corrected = self._ai_correct(item, issues, file_context)
                if corrected:
                    result.corrected_normalized = corrected
                    result.ai_correction_applied = True

        return result

    def validate_batch(
        self,
        items: List['NormalizationResult'],
        file_context: Optional['FileContext'] = None
    ) -> List[ValidationResult]:
        """
        Validate a batch of normalization results

        Args:
            items: List of NormalizationResult to validate
            file_context: Optional file context

        Returns:
            List of ValidationResult
        """
        results = []
        for item in items:
            result = self.validate(item, file_context)
            results.append(result)

        # Log summary
        valid_count = sum(1 for r in results if r.is_valid)
        error_count = sum(
            sum(1 for i in r.issues if i.severity == 'error')
            for r in results
        )
        warning_count = sum(
            sum(1 for i in r.issues if i.severity == 'warning')
            for r in results
        )

        logger.info(
            f"Validation complete: {valid_count}/{len(items)} valid, "
            f"{error_count} errors, {warning_count} warnings"
        )

        return results

    def get_quality_metrics(
        self,
        items: List['NormalizationResult'],
        validation_results: List[ValidationResult]
    ) -> Dict:
        """
        Calculate quality metrics for a normalized batch

        Returns:
            Dict with quality metrics
        """
        total = len(items)
        if total == 0:
            return {
                'total_items': 0,
                'valid_rate': 0,
                'ai_enhanced_rate': 0,
                'average_confidence': 0,
                'error_count': 0,
                'warning_count': 0,
            }

        valid_count = sum(1 for r in validation_results if r.is_valid)
        ai_enhanced = sum(1 for i in items if i.ai_enhanced)
        avg_confidence = sum(i.confidence for i in items) / total

        error_count = sum(
            sum(1 for i in r.issues if i.severity == 'error')
            for r in validation_results
        )
        warning_count = sum(
            sum(1 for i in r.issues if i.severity == 'warning')
            for r in validation_results
        )

        return {
            'total_items': total,
            'valid_rate': valid_count / total * 100,
            'ai_enhanced_rate': ai_enhanced / total * 100,
            'average_confidence': avg_confidence,
            'error_count': error_count,
            'warning_count': warning_count,
        }

    def _ai_correct(
        self,
        item: 'NormalizationResult',
        issues: List[ValidationIssue],
        file_context: Optional['FileContext']
    ) -> Optional[str]:
        """
        Use AI to correct validation issues

        Args:
            item: Original normalization result
            issues: List of validation issues
            file_context: Optional file context

        Returns:
            Corrected normalized string or None
        """
        try:
            ai_normalizer = self._get_ai_normalizer()

            issues_text = '\n'.join([
                f"- {i.description}: {i.fix_suggestion}"
                for i in issues
            ])

            context_text = ""
            if file_context:
                context_text = f"\nProject type: {file_context.project_type}"

            prompt = f"""Sửa lỗi cho mô tả đã chuẩn hóa sau:

**Mô tả gốc:** {item.original}
**Đã chuẩn hóa:** {item.normalized}
**Nhóm công tác:** {item.work_category}
{context_text}

**Các lỗi cần sửa:**
{issues_text}

Trả về JSON:
{{"corrected": "Mô tả đã sửa"}}"""

            response = ai_normalizer._call_ai(prompt)
            if response:
                import json
                import re
                json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    return data.get('corrected')

        except Exception as e:
            logger.warning(f"AI correction failed: {e}")

        return None


# Singleton instance
_domain_validator = None


def get_domain_validator() -> DomainValidator:
    """Get or create domain validator singleton"""
    global _domain_validator
    if _domain_validator is None:
        _domain_validator = DomainValidator()
    return _domain_validator


def validate_normalization(
    item: 'NormalizationResult',
    file_context: Optional['FileContext'] = None
) -> ValidationResult:
    """Convenience function for single validation"""
    validator = get_domain_validator()
    return validator.validate(item, file_context)


def validate_batch(
    items: List['NormalizationResult'],
    file_context: Optional['FileContext'] = None
) -> List[ValidationResult]:
    """Convenience function for batch validation"""
    validator = get_domain_validator()
    return validator.validate_batch(items, file_context)
