"""
Master Data Gatekeeper Service

Validates items before adding to Master DB to prevent data pollution.
- APPROVED (score >= 75): High quality → Add to Master
- PENDING_REVIEW (score 50-74): Medium quality → Staging area for human review
- REJECTED (score < 50): Low quality → Quarantine/discard

Default Settings System:
- When specs are insufficient, apply category-specific defaults
- Category-aware scoring: earthworks don't require specs, MEP requires equipment
- Material-only items can be approved with reasonable defaults
"""
import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Any, Optional
from enum import Enum

from app.core.config import settings

logger = logging.getLogger(__name__)


class WorkCategory(Enum):
    """Work categories for category-specific validation"""
    EARTHWORKS = 'earthworks_piling'
    CONCRETE = 'concrete_rebar'
    STEEL_MEP = 'steel_mep'
    ROAD = 'road_infrastructure'
    FINISHING = 'finishing'
    LANDSCAPING = 'landscaping'
    GENERAL = 'general'


# Default specifications by category when original specs are insufficient
CATEGORY_DEFAULTS = {
    WorkCategory.EARTHWORKS: {
        'default_grade': 'K95',
        'default_specs': [],
        'min_indicators': 1,  # Only verb required
        'bonus_score': 25,    # Earthworks are simple, give bonus
        'material_optional': True,
        'specs_optional': True,
    },
    WorkCategory.CONCRETE: {
        'default_grade': 'M250',
        'default_specs': ['đá 1x2'],
        'min_indicators': 2,  # Verb + material or location
        'bonus_score': 0,
        'material_optional': False,
        'specs_optional': False,
    },
    WorkCategory.STEEL_MEP: {
        'default_grade': None,
        'default_specs': [],
        'min_indicators': 1,  # Need material + something else
        'bonus_score': 25,    # MEP often lacks formal specs
        'material_optional': False,
        'specs_optional': True,
    },
    WorkCategory.ROAD: {
        'default_grade': None,
        'default_specs': [],
        'min_indicators': 1,  # Road work is often simple
        'bonus_score': 25,
        'material_optional': True,
        'specs_optional': True,
    },
    WorkCategory.FINISHING: {
        'default_grade': None,
        'default_specs': [],
        'min_indicators': 1,
        'bonus_score': 25,
        'material_optional': False,
        'specs_optional': True,
    },
    WorkCategory.LANDSCAPING: {
        'default_grade': None,
        'default_specs': [],
        'min_indicators': 1,
        'bonus_score': 25,
        'material_optional': True,
        'specs_optional': True,
    },
    WorkCategory.GENERAL: {
        'default_grade': None,
        'default_specs': [],
        'min_indicators': 1,  # Be lenient for general
        'bonus_score': 25,
        'material_optional': True,
        'specs_optional': True,
    },
}

# Known material-only items that are acceptable (auto-approve)
ACCEPTED_MATERIAL_ONLY = [
    # Construction materials
    (r'vải\s*(địa\s*kỹ\s*thuật|ĐKT)', 'Vải địa kỹ thuật'),
    (r'^nilon', 'Nilon'),
    (r'cáp\s*(điện|quang|thép|ngầm|treo)?', 'Cáp'),
    (r'dây\s*(điện|thép|đồng|dẫn)?', 'Dây'),
    (r'ống\s*(nhựa|thép|PVC|HDPE|UPVC|luồn|bảo vệ)?', 'Ống'),
    (r'tấm\s*(panel|thạch cao|nhôm|tôn)', 'Tấm'),
    (r'keo\s*(dán|chống thấm|silicone)', 'Keo'),
    (r'sơn\s*(chống|lót|phủ|epoxy)?', 'Sơn'),
    (r'gạch\s*(ceramic|granite|men|block|bê tông)?', 'Gạch'),
    (r'^đá\s*(granite|marble|hoa cương|dăm|1x2|0\.5x1)?', 'Đá'),
    (r'thép\s*(hình|ống|tấm|cuộn|tròn)?', 'Thép'),
    (r'biển\s*báo', 'Biển báo'),
    (r'bó\s*vỉa', 'Bó vỉa đá'),
    (r'tấm\s*đan', 'Tấm đan'),
    (r'CPĐD|cấp\s*phối', 'Cấp phối đá dăm'),
    # MEP/Plumbing items
    (r'van\s*(cổng|1 chiều|bi|bướm|an toàn|xả)?', 'Van'),
    (r'mối\s*nối', 'Mối nối'),
    (r'(tê|cút|co)\s*(đều|giảm)?', 'Phụ kiện ống'),
    (r'đinh\s*(phản quang|neo|vít)', 'Đinh'),
    (r'cửa\s*(xả|hút|thổi)', 'Cửa'),
    (r'đa\s*hộc', 'Đá hộc'),
    # Electrical items
    (r'đèn\s*(chiếu sáng|LED|cao áp|báo|tín hiệu|pha)?', 'Đèn'),
    (r'tủ\s*(điện|điều khiển|phân phối|gom|công tơ)?', 'Tủ điện'),
    (r'máy\s*(biến áp|phát điện|bơm)', 'Máy'),
    (r'cột\s*(điện|đèn|thép)', 'Cột'),
    # Electrical control items
    (r'biến\s*(dòng|áp)', 'Biến dòng/áp'),
    (r'khóa\s*chuyển', 'Khóa chuyển mạch'),
    (r'bộ\s*khởi\s*động', 'Bộ khởi động'),
    (r'rơ\s*le', 'Rơ le'),
    (r'contactor', 'Contactor'),
    (r'aptomat|MCB|MCCB|RCBO', 'Aptomat'),
    (r'đầu\s*(vào|ra|nối|cốt)', 'Đầu nối'),
    (r'mạch\s*điều\s*khiển', 'Mạch điều khiển'),
    (r'công\s*tác\s*phụ', 'Công tác phụ'),
    (r'vật\s*tư\s*phụ', 'Vật tư phụ'),
    # More electrical equipment
    (r'công\s*tơ', 'Công tơ điện'),
    (r'cầu\s*(chì|dao|đấu)', 'Cầu chì/dao'),
    (r'thanh\s*(cái|đồng|nhôm)', 'Thanh cái'),
    (r'tụ\s*(bù|điện)', 'Tụ điện'),
    (r'áp\s*tô\s*mát', 'Aptomat'),
    (r'cầu\s*chì', 'Cầu chì'),
    # Water/drainage items
    (r'bể\s*(nước|phốt|tự hoại)', 'Bể'),
    (r'hố\s*(ga|thu|thăm)', 'Hố ga'),
    (r'nắp\s*(gang|bê tông|nhựa)', 'Nắp hố ga'),
    (r'song\s*chắn', 'Song chắn rác'),
    # Additional electrical equipment
    (r'ổn\s*áp|AVR', 'Ổn áp'),
    (r'công\s*tắc', 'Công tắc'),
    (r'ổ\s*(cắm|điện)', 'Ổ cắm'),
    (r'hộp\s*(kiểm tra|nối|đấu|điện)', 'Hộp điện'),
    (r'bộ\s*đếm', 'Bộ đếm'),
    (r'gem|hóa\s*chất\s*giảm\s*điện\s*trở', 'Gem hóa chất'),
    (r'chi\s*phí\s*(kiểm định|thí nghiệm)', 'Chi phí kiểm định'),
    (r'tiếp\s*địa|nối\s*đất', 'Tiếp địa'),
    # Plumbing fittings
    (r'khớp\s*(nối|mềm)', 'Khớp nối'),
    (r'chếch', 'Chếch'),
    (r'kép\s*ren', 'Kép ren'),
    (r'bích\s*(rỗng|kín|nối)?', 'Bích'),
    (r'bình\s*(tích áp|chứa)', 'Bình tích áp'),
    (r'bệ\s*(bình|máy|bơm)', 'Bệ đỡ'),
    (r'trục\s*(ngang|đứng)', 'Trục'),
    (r'rắc\s*co', 'Rắc co'),
    (r'măng\s*xông', 'Măng xông'),
    (r'rọ\s*(hút|lọc)', 'Rọ hút'),
    (r'y\s*lọc', 'Y lọc'),
    # Fire protection / PCCC
    (r'alarm\s*valve', 'Van báo động'),
    (r'bình\s*chữa\s*cháy', 'Bình chữa cháy'),
    (r'hộp\s*đựng\s*bình', 'Hộp đựng bình chữa cháy'),
    (r'sprinkler', 'Đầu phun sprinkler'),
    # Electrical/MEP equipment
    (r'biến\s*tần|VSD|VFD', 'Biến tần'),
    (r'busbar', 'Busbar'),
    (r'inverter', 'Inverter'),
    (r'UPS', 'UPS'),
    (r'ATS', 'ATS'),
]

# Device/Equipment codes to SKIP (not work descriptions, just identifiers)
# These are proper names, not items to be processed
DEVICE_CODE_PATTERNS = [
    r'^[A-ZĐ]{1,4}-\d+.*TBA',           # TĐ-1-II-TBA, KK-1-II-TBA
    r'^TBA\s*\d+',                       # TBA 10, TBA-1
    r'^[A-ZĐ]{2,5}-\d+-[IVX]+',         # Equipment codes with Roman numerals
    r'^[A-ZĐ]{1,3}\d+-[A-ZĐ]+\d*$',     # Short codes like TC1-A, MĐ2-B1
    r'^\d+\.\d+\.\d+',                   # Section numbers like 1.2.3
    r'^[IVX]+\.\d+',                     # Roman numeral sections like I.1, II.3
]


@dataclass
class GatekeeperResult:
    """Result of gatekeeper validation for a single item"""
    status: str  # 'APPROVED', 'PENDING_REVIEW', 'REJECTED', 'SKIPPED'
    score: float  # 0-100 quality score
    reasons: List[str] = field(default_factory=list)  # Why this decision was made
    indicators: Dict[str, bool] = field(default_factory=dict)  # Breakdown of quality indicators
    defaults_applied: Dict[str, Any] = field(default_factory=dict)  # Default settings applied
    enhanced_description: Optional[str] = None  # Description with defaults applied
    # v4.0 spec lifecycle suggestions
    suggested_spec_status: str = 'draft'
    suggested_spec_source: str = 'default'
    suggested_spec_confidence: float = 0.3
    # Forbidden pattern match info (for routing decisions)
    is_forbidden_pattern: bool = False

    @property
    def gate_color(self) -> str:
        """Map status/score to traffic gate color (GREEN/YELLOW/RED)."""
        if self.status == 'APPROVED':
            return 'GREEN'
        elif self.status == 'PENDING_REVIEW':
            return 'YELLOW'
        else:
            return 'RED'


class MasterDataGatekeeper:
    """
    Validates items quality before adding to Master database.

    Scoring:
    - Each quality indicator is worth 25 points (max 100)
    - Category-specific bonuses can boost scores
    - Forbidden patterns result in immediate rejection
    - Minimum requirements must be met for any score
    - Default settings are applied when specs are insufficient
    """

    # Thresholds (from config)
    APPROVED_THRESHOLD = settings.GATEKEEPER_GREEN_THRESHOLD   # >= 90 → Auto add
    PENDING_THRESHOLD = settings.GATEKEEPER_YELLOW_THRESHOLD   # 60-89 → Need review
    # < 60 → Rejected

    # Minimum requirements (relaxed for Vietnamese)
    MIN_DESCRIPTION_LENGTH = 5   # Reduced from 10
    MIN_WORD_COUNT = 1           # Reduced from 2

    # Forbidden patterns (garbage detection) - immediate rejection
    FORBIDDEN_PATTERNS = [
        (r'^[\?\!\.\,\;\:]+$', 'only punctuation'),
        (r'^\d+$', 'only numbers'),
        (r'^[a-zA-Z]{1,2}$', 'too short meaningless'),
        (r'^(test|xxx|abc|xyz|asdf|qwerty)\b', 'common garbage pattern'),
        (r'^\s*$', 'empty or whitespace only'),
        (r'^[\?\!]{2,}', 'multiple question/exclamation marks'),
        (r'^n/a$', 'not applicable placeholder'),
        (r'^-+$', 'only dashes'),
        (r'^\.\.\.+$', 'only ellipsis'),
    ]

    # Quality indicators (each worth 25 points)
    # Pattern for Vietnamese construction work descriptions
    QUALITY_INDICATORS = {
        'has_verb': (
            r'(^|\s)(Đào|Đắp|Đổ|Xây|Trát|Lắp|Lát|Sơn|Phá|Cung cấp|Thi công|Gia công|'
            r'Vận chuyển|San|Đầm|Lấp|Bơm|Căng|Kéo|Uốn|Hàn|Cắt|Khoan|Đóng|Ép|'
            r'Rải|Trộn|Quét|Phun|Dán|Bọc|Chống thấm|Hoàn thiện|Tháo dỡ|Làm sạch|'
            r'Bó vỉa|Lắp đặt|Tưới|Rải thảm|Bê tông)',
            'has action verb'
        ),
        'has_material': (
            r'(bê tông|gạch|thép|đất|đá|ống|cáp|dây|gỗ|nhựa|kính|xi măng|cát|sỏi|'
            r'vữa|sơn|keo|nhôm|inox|thạch cao|gốm|sứ|bitum|asphalt|bọt xốp|'
            r'composite|pvc|hdpe|upvc|copper|đồng|chì|kẽm|tấm|thanh|cọc|'
            r'vải|nilon|CPĐD|cấp phối|BTN|biển báo|đan|ván khuôn|bó vỉa)',
            'has material keyword'
        ),
        'has_specs': (
            r'(M\d+|D\d+|K\d+|\d+x\d+|\d+mm|\d+cm|\d+m\b|PN\d+|CB\d+|'
            r'\d+MPa|C\d+|A\d+|S\d+|#\d+|Φ\d+|φ\d+|@\d+|\d+kg|Grade\s*\d+|'
            r'loại\s*[IV]+|lớp\s*(trên|dưới|thấm|bám)|KT\s*\d+|\d+kN)',
            'has specifications'
        ),
        'has_location': (
            r'(móng|cột|dầm|sàn|tường|mái|nền|hố|rãnh|mương|giằng|lanh tô|'
            r'ô văng|cầu thang|ban công|hành lang|mương|hầm|bể|tầng|lớp|'
            r'trần|vách|mặt bằng|kết cấu|phần thân|phần móng|vỉa hè|mặt đường|'
            r'đường|trong|ngoài)',
            'has location context'
        ),
    }

    def __init__(self):
        # Compile forbidden patterns for performance
        self._forbidden_compiled = [
            (re.compile(pattern, re.IGNORECASE), reason)
            for pattern, reason in self.FORBIDDEN_PATTERNS
        ]

        # Compile quality indicator patterns
        self._indicator_compiled = {
            name: (re.compile(pattern, re.IGNORECASE), desc)
            for name, (pattern, desc) in self.QUALITY_INDICATORS.items()
        }

        # Compile accepted material-only patterns
        self._material_only_compiled = [
            (re.compile(pattern, re.IGNORECASE), name)
            for pattern, name in ACCEPTED_MATERIAL_ONLY
        ]

        # Compile device code patterns (to skip)
        self._device_code_compiled = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in DEVICE_CODE_PATTERNS
        ]

    def validate(
        self,
        item: Any,
        category: Optional[str] = None,
        apply_defaults: bool = True
    ) -> GatekeeperResult:
        """
        Validate a single item's quality before adding to Master.

        Args:
            item: Object with 'normalized_description' attribute or dict with same key,
                  or just a string
            category: Optional work category for category-specific rules
            apply_defaults: Whether to apply default settings when specs insufficient

        Returns:
            GatekeeperResult with status, score, reasons, indicator breakdown,
            and any defaults applied
        """
        # Extract description and category from item
        if hasattr(item, 'normalized_description'):
            description = item.normalized_description or ''
            if hasattr(item, 'work_category') and not category:
                category = getattr(item.work_category, 'value', str(item.work_category))
        elif isinstance(item, dict):
            description = item.get('normalized_description', '') or item.get('description', '')
            if not category:
                category = item.get('category') or item.get('work_category')
        else:
            description = str(item)

        description = description.strip()
        reasons = []
        indicators = {}
        defaults_applied = {}
        enhanced_description = None

        # Step 0: Check if this is a device code (skip, not a work description)
        if self._is_device_code(description):
            return GatekeeperResult(
                status='SKIPPED',
                score=0,
                reasons=["Device/equipment code - not a work description"],
                indicators={'is_device_code': True}
            )

        # Step 1: Check forbidden patterns (immediate rejection)
        forbidden_match = self._check_forbidden_patterns(description)
        if forbidden_match:
            return GatekeeperResult(
                status='REJECTED',
                score=0,
                reasons=[f"Forbidden pattern: {forbidden_match}"],
                indicators={},
                is_forbidden_pattern=True,
            )

        # Step 2: Check if this is an accepted material-only item
        material_only_match = self._check_material_only(description)
        if material_only_match:
            return GatekeeperResult(
                status='APPROVED',
                score=75,
                reasons=[f"✓ Accepted material-only: {material_only_match}"],
                indicators={'has_material': True, 'material_only_accepted': True},
                defaults_applied={'material_type': material_only_match}
            )

        # Step 3: Check minimum requirements (relaxed)
        min_req_result = self._check_minimum_requirements(description)
        if not min_req_result['passed']:
            return GatekeeperResult(
                status='REJECTED',
                score=10,
                reasons=min_req_result['reasons'],
                indicators={}
            )

        # Step 4: Score quality indicators
        score = 0
        indicator_count = 0
        for name, (pattern, desc) in self._indicator_compiled.items():
            if pattern.search(description):
                indicators[name] = True
                score += 25
                indicator_count += 1
                reasons.append(f"✓ {desc}")
            else:
                indicators[name] = False

        # Step 5: Apply category-specific rules and bonuses
        work_category = self._parse_category(category)
        category_config = CATEGORY_DEFAULTS.get(work_category, CATEGORY_DEFAULTS[WorkCategory.GENERAL])

        # Check if minimum indicators are met for this category
        if indicator_count >= category_config['min_indicators']:
            # Apply category bonus
            bonus = category_config['bonus_score']
            if bonus > 0:
                score += bonus
                reasons.append(f"✓ Category bonus ({work_category.value}): +{bonus}")
                defaults_applied['category_bonus'] = bonus

        # Step 6: Apply default specs if needed and apply_defaults is True
        if apply_defaults and score < self.APPROVED_THRESHOLD:
            # Apply default grade if missing specs
            if not indicators.get('has_specs') and category_config.get('default_grade'):
                default_grade = category_config['default_grade']
                enhanced_description = f"{description} - {default_grade}"
                defaults_applied['default_grade'] = default_grade
                score += 25  # Now has specs
                reasons.append(f"✓ Applied default grade: {default_grade}")

            # Apply default specs
            if category_config.get('default_specs'):
                for spec in category_config['default_specs']:
                    if spec not in description:
                        defaults_applied.setdefault('default_specs', []).append(spec)

        # Step 7: Final score adjustments
        # Cap score at 100
        score = min(score, 100)

        # Step 8: Determine status based on score
        if score >= self.APPROVED_THRESHOLD:
            status = 'APPROVED'
        elif score >= self.PENDING_THRESHOLD:
            status = 'PENDING_REVIEW'
        else:
            status = 'REJECTED'
            if not reasons:
                reasons.append("Insufficient quality indicators")

        # Step 9: Determine spec lifecycle suggestions
        suggested_spec_status = 'draft'
        suggested_spec_source = 'default'
        suggested_spec_confidence = 0.3

        if indicators.get('has_specs'):
            # Has real specs from the description (likely from BOQ)
            suggested_spec_source = 'boq'
            suggested_spec_confidence = 0.5
            suggested_spec_status = 'detailed'
        elif defaults_applied.get('default_grade'):
            # Using system defaults
            suggested_spec_source = 'default'
            suggested_spec_confidence = 0.3
            suggested_spec_status = 'draft'

        return GatekeeperResult(
            status=status,
            score=score,
            reasons=reasons,
            indicators=indicators,
            defaults_applied=defaults_applied if defaults_applied else {},
            enhanced_description=enhanced_description,
            suggested_spec_status=suggested_spec_status,
            suggested_spec_source=suggested_spec_source,
            suggested_spec_confidence=suggested_spec_confidence,
        )

    def validate_batch(
        self,
        items: List[Any],
        apply_defaults: bool = True
    ) -> Dict[str, List]:
        """
        Validate multiple items and categorize by result.

        Args:
            items: List of items to validate
            apply_defaults: Whether to apply default settings

        Returns:
            Dict with keys 'approved', 'pending', 'rejected', 'skipped', each containing
            list of tuples (item, GatekeeperResult)
        """
        results = {
            'approved': [],
            'pending': [],
            'rejected': [],
            'skipped': []
        }

        for item in items:
            result = self.validate(item, apply_defaults=apply_defaults)

            if result.status == 'APPROVED':
                results['approved'].append((item, result))
            elif result.status == 'PENDING_REVIEW':
                results['pending'].append((item, result))
            elif result.status == 'SKIPPED':
                results['skipped'].append((item, result))
            else:
                results['rejected'].append((item, result))

        logger.info(
            f"Gatekeeper validation: {len(results['approved'])} approved, "
            f"{len(results['pending'])} pending, {len(results['rejected'])} rejected, "
            f"{len(results['skipped'])} skipped"
        )

        return results

    def _check_forbidden_patterns(self, description: str) -> Optional[str]:
        """
        Check if description matches any forbidden pattern.

        Returns:
            Matched pattern reason or None if no match
        """
        for pattern, reason in self._forbidden_compiled:
            if pattern.search(description):
                return reason
        return None

    def _check_material_only(self, description: str) -> Optional[str]:
        """
        Check if description is an accepted material-only item.

        Returns:
            Material name if matched, None otherwise
        """
        for pattern, name in self._material_only_compiled:
            if pattern.search(description):
                return name
        return None

    def _is_device_code(self, description: str) -> bool:
        """
        Check if description is a device/equipment code (not a work description).

        These are identifiers like "TĐ-1-II-TBA 10" that should be skipped.

        Returns:
            True if it's a device code, False otherwise
        """
        for pattern in self._device_code_compiled:
            if pattern.match(description):
                return True
        return False

    def _check_minimum_requirements(self, description: str) -> Dict:
        """
        Check if description meets minimum requirements.

        Returns:
            Dict with 'passed' bool and 'reasons' list
        """
        reasons = []

        # Check length
        if len(description) < self.MIN_DESCRIPTION_LENGTH:
            reasons.append(f"Description too short ({len(description)} < {self.MIN_DESCRIPTION_LENGTH} chars)")

        # Check word count
        words = description.split()
        if len(words) < self.MIN_WORD_COUNT:
            reasons.append(f"Too few words ({len(words)} < {self.MIN_WORD_COUNT})")

        return {
            'passed': len(reasons) == 0,
            'reasons': reasons
        }

    def _parse_category(self, category: Optional[str]) -> WorkCategory:
        """Parse category string to WorkCategory enum."""
        if not category:
            return WorkCategory.GENERAL

        category_lower = category.lower() if isinstance(category, str) else str(category).lower()

        for wc in WorkCategory:
            if wc.value == category_lower or wc.name.lower() == category_lower:
                return wc

        # Fuzzy matching
        if 'earth' in category_lower or 'đào' in category_lower or 'đắp' in category_lower:
            return WorkCategory.EARTHWORKS
        if 'concrete' in category_lower or 'bê tông' in category_lower:
            return WorkCategory.CONCRETE
        if 'steel' in category_lower or 'mep' in category_lower or 'thép' in category_lower:
            return WorkCategory.STEEL_MEP
        if 'road' in category_lower or 'đường' in category_lower:
            return WorkCategory.ROAD
        if 'finish' in category_lower or 'hoàn thiện' in category_lower:
            return WorkCategory.FINISHING
        if 'landscape' in category_lower or 'cây' in category_lower:
            return WorkCategory.LANDSCAPING

        return WorkCategory.GENERAL


def get_gatekeeper() -> MasterDataGatekeeper:
    """Factory function to get gatekeeper instance"""
    return MasterDataGatekeeper()
