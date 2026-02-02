"""
AI-Enhanced Description Normalizer
Sử dụng LLM để chuẩn hóa và làm sạch description với độ chính xác cao hơn

Hybrid Approach:
1. Rule-based parsing để extract components cơ bản
2. AI để enhance và correct các trường hợp phức tạp:
   - Domain knowledge mapping (PC30 → M100)
   - Infer missing info từ context (gạch đặc)
   - Chuẩn hóa format output

Multi-Pass Analysis:
- Pass 1: File context analysis
- Pass 2: Rule-based with context
- Pass 3: AI enhancement for complex items
- Pass 4: Domain validation

Supports: OpenAI (GPT-4o-mini, GPT-4), Anthropic (Claude), and Gemini
"""
import json
import logging
import re
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field

from app.core.config import settings
from app.services.description_normalizer import DescriptionNormalizer

if TYPE_CHECKING:
    from app.services.file_context_analyzer import FileContext

logger = logging.getLogger(__name__)


@dataclass
class NormalizationResult:
    """Result of AI-enhanced normalization"""
    original: str
    normalized: str
    work_category: str
    confidence: float
    components: Dict
    ai_enhanced: bool
    ai_corrections: List[str] = None
    pattern_used: str = None  # Template pattern name used


# Road infrastructure specific keywords for AI trigger
ROAD_INFRASTRUCTURE_KEYWORDS = [
    'biển báo', 'bản quan trắc', 'quan trắc', 'vạch sơn', 'sơn vạch',
    'lan can', 'hộ lan', 'tôn sóng', 'cọc tiêu', 'cọc km',
    'cột đèn', 'đèn chiếu sáng', 'trồng cây', 'trồng cỏ', 'đất màu',
    'rải thảm', 'btn c', 'lớp thấm bám', 'nhựa pha dầu',
]


# System prompt for AI normalization
SYSTEM_PROMPT = """Bạn là chuyên gia về định mức xây dựng Việt Nam. Nhiệm vụ của bạn là chuẩn hóa mô tả công việc xây dựng theo format chuẩn.

## Quy tắc chuẩn hóa:

### 1. Format output:
[Động từ] [Vật liệu] [Vị trí] - [Thông số kỹ thuật] - [Chi tiết bổ sung]

### 2. Nhóm công tác và template:

**Đất & Cọc (earthworks_piling):**
- Template: [Hành động] [Đối tượng] [vị trí] - [Thiết bị/Kích thước] - [Cấp đất]
- VD: "Đào đất hố móng - máy đào 1.25m3 - đất cấp 3"
- VD: "Ép cọc - PHC D300 - 200 tấn - đất cấp 2"

**Bê tông & Cốt thép (concrete_rebar):**
- Template: [Hành động] [Vật liệu] [vị trí] - [Mác/Đường kính] - [Đặc tính]
- VD: "Đổ bê tông dầm sàn - M350 - thương phẩm"
- VD: "Bê tông lót móng - M100 - thương phẩm"
- VD: "Gia công cốt thép móng - D<=10 - CB300"

**Hoàn thiện (finishing):**
- Template: [Động từ] [vị trí] - [Vật liệu chi tiết] - [Kích thước/Mác]
- VD: "Lát sàn - gạch granite - 600x600"
- VD: "Xây tường - gạch đặc 6.5x10.5x22 - M75"
- VD: "Trát tường trong nhà - dày 15mm - M75"
- VD: "Sơn tường trong nhà - 1 lót 2 phủ"

**MEP (steel_mep):**
- Template: [Động từ] [Vật liệu] [vị trí] - [Loại] - [Quy cách] - [Áp suất]
- VD: "Lắp đặt ống cấp nước - PPR - D63 - PN16"

**Hạ tầng đường (road_infrastructure):**
- Template cho biển báo: "Biển báo [loại] - [kích thước]"
  - VD: "Biển báo tam giác - A70"
  - VD: "Biển báo tròn - B40"
- Template cho bản quan trắc: "Lắp đặt bản quan trắc [loại]"
  - VD: "Lắp đặt bản quan trắc lún"
- Template cho vạch sơn: "Sơn vạch [loại] - [màu]"
  - VD: "Sơn vạch kẻ đường - trắng"
- Template cho BTN: "Rải thảm BTN mặt đường - [grade]"
  - VD: "Rải thảm BTN mặt đường - C19"
- Template cho tưới nhựa: "Tưới mặt đường - [vật liệu]"
  - VD: "Tưới mặt đường - nhựa pha dầu - lớp thấm bám"
- Template cho cây xanh: "Trồng [cây/cỏ] - [location]"
  - VD: "Trồng cây xanh hố móng - đất màu"
- Template cho lan can: "Lắp đặt [loại lan can] - [vật liệu]"
  - VD: "Lắp đặt hộ lan tôn sóng - mạ kẽm"

### 3. Domain Knowledge - Mapping quan trọng:

**Bê tông:**
- PC30/PC40 xi măng → thường dùng cho M100-M150 (lót móng)
- Bê tông lót móng thường là M100
- "vữa bê tông" = bê tông trộn tại chỗ hoặc thương phẩm

**Gạch xây:**
- Kích thước 6.5x10.5x22 hoặc tương tự → gạch đặc
- Kích thước 8x8x19 hoặc 10x10x20 → gạch ống/gạch block

**Cốt thép:**
- D<10 hoặc D<=10 → thép có đường kính nhỏ hơn hoặc bằng 10mm
- CB300, CB400 → loại thép (Cốt Bê tông)

**Bê tông nhựa (BTN):**
- BTN C12.5, C19 → grade của bê tông nhựa
- "thảm" = lớp BTN mặt đường
- "lớp thấm bám" = tack coat

**Biển báo:**
- Tam giác = Biển cảnh báo (A-series)
- Tròn = Biển cấm (B-series)
- Chữ nhật = Biển chỉ dẫn (C-series)
- Số sau chữ = kích thước (70cm, 40cm)

**Quan trắc:**
- "bản quan trắc lún" = thiết bị đo độ lún
- KHÔNG phải công tác đá nền

**Đất màu:**
- "đất màu" = topsoil cho trồng cây
- KHÔNG phải đất có màu sắc

### 4. Quy tắc viết:
- Động từ viết hoa chữ cái đầu: Đào, Đổ, Xây, Lát, Trát, Sơn, Lắp đặt
- Vị trí viết thường: móng, tường, sàn, trong nhà
- Phân cách bằng " - " (có space 2 bên)
- Không dùng dấu ngoặc [], ()

Trả về JSON với format:
{
  "normalized": "Mô tả đã chuẩn hóa",
  "work_category": "earthworks_piling|concrete_rebar|finishing|steel_mep|road_infrastructure",
  "confidence": 0.95,
  "corrections": ["Sửa PC30 thành M100", "Thêm 'gạch đặc'"]
}
"""

# Batch context prompt template
BATCH_CONTEXT_PROMPT = """File Context:
- Project type: {project_type}
- Common materials: {common_materials}
- Current section: {section_name}

Batch of {n} items to normalize:
{items}

For each item, return JSON array:
[
  {{"id": 1, "normalized": "...", "work_category": "...", "confidence": 0.95, "pattern": "template_name"}},
  ...
]

Apply consistent patterns across batch. Ensure similar items get similar normalization.
"""


class AINormalizer:
    """AI-Enhanced Description Normalizer using LLM"""

    def __init__(self):
        self.rule_based = DescriptionNormalizer()
        self.ai_enabled = settings.AI_NORMALIZATION_ENABLED
        self.provider = settings.AI_PROVIDER
        self.model = settings.AI_MODEL
        self._client = None

    def _get_client(self):
        """Lazy load AI client"""
        if self._client is not None:
            return self._client

        if self.provider == "openai":
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("OpenAI client initialized")
            except ImportError:
                logger.warning("OpenAI package not installed")
                self._client = None
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self._client = None

        elif self.provider == "anthropic":
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                logger.info("Anthropic client initialized")
            except ImportError:
                logger.warning("Anthropic package not installed")
                self._client = None
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
                self._client = None

        elif self.provider == "gemini":
            # For Gemini, we use requests directly to call the REST API
            self._client = "gemini"  # Marker to indicate Gemini is enabled
            logger.info("Gemini client initialized (REST API)")

        return self._client

    def _call_ai(self, prompt: str) -> Optional[str]:
        """Call AI API"""
        client = self._get_client()
        if not client:
            return None

        try:
            if self.provider == "openai":
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=500
                )
                return response.choices[0].message.content

            elif self.provider == "anthropic":
                response = client.messages.create(
                    model=self.model,
                    system=SYSTEM_PROMPT,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=500
                )
                return response.content[0].text

            elif self.provider == "gemini":
                import requests
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
                headers = {
                    "Content-Type": "application/json",
                    "X-goog-api-key": settings.GEMINI_API_KEY
                }
                data = {
                    "contents": [
                        {
                            "parts": [
                                {"text": f"{SYSTEM_PROMPT}\n\n{prompt}"}
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 500
                    }
                }
                response = requests.post(url, headers=headers, json=data, timeout=30)
                response.raise_for_status()
                result = response.json()
                # Extract text from Gemini response
                if "candidates" in result and len(result["candidates"]) > 0:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        return candidate["content"]["parts"][0].get("text", "")
                return None

        except Exception as e:
            logger.error(f"AI API call failed: {e}")
            return None

    def _parse_ai_response(self, response: str) -> Optional[Dict]:
        """Parse AI JSON response"""
        if not response:
            return None

        try:
            # Extract JSON from response (may be wrapped in markdown)
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI response as JSON: {e}")
            return None

    def normalize(self, description: str, use_ai: bool = True) -> NormalizationResult:
        """
        Normalize description with optional AI enhancement

        Args:
            description: Original description
            use_ai: Whether to use AI for enhancement (default True)

        Returns:
            NormalizationResult with normalized description and metadata
        """
        if not description or not description.strip():
            return NormalizationResult(
                original=description,
                normalized="",
                work_category="general",
                confidence=0,
                components={},
                ai_enhanced=False
            )

        # Step 1: Rule-based parsing
        category = self.rule_based.identify_work_category(description)
        components = self.rule_based.parse_description(description)
        rule_based_result = self.rule_based.normalize(description)

        # Step 2: AI enhancement (if enabled)
        ai_enhanced = False
        ai_corrections = []
        final_result = rule_based_result
        confidence = self._calculate_confidence(components)

        if use_ai and self.ai_enabled and self._should_use_ai(components, confidence):
            ai_result = self._ai_enhance(description, rule_based_result, components, category)
            if ai_result:
                final_result = ai_result.get("normalized", rule_based_result)
                category = ai_result.get("work_category", category)
                confidence = ai_result.get("confidence", confidence)
                ai_corrections = ai_result.get("corrections", [])
                ai_enhanced = True

        return NormalizationResult(
            original=description,
            normalized=final_result,
            work_category=category,
            confidence=confidence,
            components=components,
            ai_enhanced=ai_enhanced,
            ai_corrections=ai_corrections
        )

    def _should_use_ai(
        self,
        components: Dict,
        confidence: float,
        file_context: Optional['FileContext'] = None,
        original_desc: str = ""
    ) -> bool:
        """
        Decide whether to use AI for this description

        Use AI when:
        - Confidence is low (< 80%)
        - Missing key components
        - Potential domain mapping needed
        - Road infrastructure specific items
        """
        # Low confidence
        if confidence < 80:
            return True

        # Missing verb or material
        if not components.get('verb') or not components.get('material'):
            return True

        # Has PC grade (needs mapping to M grade)
        grade = components.get('grade', '')
        if grade and grade.startswith('PC'):
            return True

        # Has brick dimensions but no type
        if components.get('material') == 'gạch' and not components.get('material_detail'):
            return True

        # Road infrastructure specific triggers
        desc_lower = original_desc.lower() if original_desc else ""
        if any(kw in desc_lower for kw in ROAD_INFRASTRUCTURE_KEYWORDS):
            return True

        # BTN without grade
        if 'btn' in desc_lower and not re.search(r'c\d+', desc_lower):
            return True

        # Multi-material complex items
        if '(bao gồm' in desc_lower or '(kể cả' in desc_lower:
            return True

        # File context specific triggers
        if file_context and file_context.project_type == 'road_infrastructure':
            # For road projects, be more aggressive with AI
            if confidence < 85:
                return True

        return False

    def _calculate_confidence(self, components: Dict) -> float:
        """Calculate confidence based on parsed components"""
        confidence = 100.0

        if not components.get('verb'):
            confidence -= 30
        if not components.get('material'):
            confidence -= 20
        if not components.get('position'):
            confidence -= 15
        if not components.get('grade') and not components.get('specs'):
            confidence -= 15

        return max(0, confidence)

    def _ai_enhance(
        self,
        original: str,
        rule_based: str,
        components: Dict,
        category: str
    ) -> Optional[Dict]:
        """Use AI to enhance normalization"""
        prompt = f"""Chuẩn hóa mô tả công việc xây dựng sau:

**Mô tả gốc:** {original}

**Kết quả rule-based:** {rule_based}

**Components đã parse:**
- Động từ: {components.get('verb', 'N/A')}
- Vật liệu: {components.get('material', 'N/A')}
- Vị trí: {components.get('position', 'N/A')}
- Mác/Grade: {components.get('grade', 'N/A')}
- Thông số: {components.get('specs', [])}
- Chi tiết: {components.get('details', [])}
- Thiết bị: {components.get('equipment', 'N/A')}

**Nhóm công tác:** {category}

Hãy chuẩn hóa lại theo format chuẩn, sửa các lỗi nếu có (mapping PC→M, thêm loại gạch, etc.)

Trả về JSON:
{{"normalized": "...", "work_category": "...", "confidence": 0.95, "corrections": ["..."]}}"""

        response = self._call_ai(prompt)
        return self._parse_ai_response(response)

    def normalize_batch(
        self,
        descriptions: List[str],
        use_ai: bool = True,
        file_context: Optional['FileContext'] = None
    ) -> List[NormalizationResult]:
        """
        Normalize batch of descriptions

        Args:
            descriptions: List of descriptions
            use_ai: Whether to use AI enhancement
            file_context: Optional file context for enhanced normalization

        Returns:
            List of NormalizationResult
        """
        results = []

        # First pass: Rule-based for all
        for desc in descriptions:
            result = self.normalize(desc, use_ai=False)
            results.append(result)

        # Second pass: AI enhancement for low-confidence items
        if use_ai and self.ai_enabled:
            batch_size = settings.AI_NORMALIZATION_BATCH_SIZE
            items_to_enhance = [
                (i, r) for i, r in enumerate(results)
                if self._should_use_ai(
                    r.components,
                    r.confidence,
                    file_context,
                    r.original
                )
            ]

            # Process in batches with context
            if file_context and len(items_to_enhance) >= 3:
                # Use batch AI call for efficiency
                self._batch_ai_normalize(items_to_enhance, results, file_context)
            else:
                # Process individually
                for idx, result in items_to_enhance:
                    enhanced = self.normalize(result.original, use_ai=True)
                    if enhanced.ai_enhanced:
                        results[idx] = enhanced

        return results

    def normalize_with_file_context(
        self,
        descriptions: List[str],
        file_context: 'FileContext'
    ) -> List[NormalizationResult]:
        """
        Normalize with file context for improved accuracy

        Pass 2+3: Uses file context to improve normalization

        Args:
            descriptions: List of descriptions to normalize
            file_context: FileContext from Pass 1 analysis

        Returns:
            List of NormalizationResult
        """
        logger.info(
            f"Normalizing {len(descriptions)} items with context: "
            f"project_type={file_context.project_type}"
        )

        # Step 1: Rule-based first pass
        results = []
        for desc in descriptions:
            result = self.normalize(desc, use_ai=False)
            results.append(result)

        # Step 2: Identify items needing AI
        items_needing_ai = []
        for i, result in enumerate(results):
            if self._should_use_ai(
                result.components,
                result.confidence,
                file_context,
                result.original
            ):
                items_needing_ai.append((i, result))

        logger.info(f"Items needing AI enhancement: {len(items_needing_ai)}/{len(results)}")

        # Step 3: Batch AI call with context
        if items_needing_ai and self.ai_enabled:
            self._batch_ai_normalize(items_needing_ai, results, file_context)

        return results

    def _batch_ai_normalize(
        self,
        items: List[Tuple[int, NormalizationResult]],
        results: List[NormalizationResult],
        file_context: 'FileContext'
    ) -> None:
        """
        Batch AI normalization with file context

        Updates results in place
        """
        batch_size = settings.AI_NORMALIZATION_BATCH_SIZE

        for batch_start in range(0, len(items), batch_size):
            batch = items[batch_start:batch_start + batch_size]

            # Build batch prompt
            items_text = '\n'.join([
                f"{i+1}. \"{item.original}\""
                for i, (_, item) in enumerate(batch)
            ])

            # Determine current section
            section_name = "general"
            if file_context.sections:
                section_name = file_context.sections[0].name if file_context.sections else "general"

            prompt = BATCH_CONTEXT_PROMPT.format(
                project_type=file_context.project_type,
                common_materials=', '.join(file_context.common_materials[:5]),
                section_name=section_name,
                n=len(batch),
                items=items_text
            )

            # Call AI
            response = self._call_ai(prompt)
            if response:
                try:
                    # Parse batch response
                    batch_results = self._parse_batch_response(response)
                    if batch_results:
                        for i, (idx, original_result) in enumerate(batch):
                            if i < len(batch_results):
                                ai_result = batch_results[i]
                                results[idx] = NormalizationResult(
                                    original=original_result.original,
                                    normalized=ai_result.get('normalized', original_result.normalized),
                                    work_category=ai_result.get('work_category', original_result.work_category),
                                    confidence=ai_result.get('confidence', 0.9) * 100,
                                    components=original_result.components,
                                    ai_enhanced=True,
                                    ai_corrections=[],
                                    pattern_used=ai_result.get('pattern')
                                )
                except Exception as e:
                    logger.warning(f"Failed to parse batch AI response: {e}")
                    # Fall back to individual processing
                    for idx, result in batch:
                        enhanced = self.normalize(result.original, use_ai=True)
                        if enhanced.ai_enhanced:
                            results[idx] = enhanced

    def _parse_batch_response(self, response: str) -> Optional[List[Dict]]:
        """Parse batch AI JSON response"""
        if not response:
            return None

        try:
            # Extract JSON array from response
            array_match = re.search(r'\[[\s\S]*\]', response)
            if array_match:
                return json.loads(array_match.group())
            return None
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse batch AI response as JSON: {e}")
            return None


# Singleton instance
_ai_normalizer = None


def get_ai_normalizer() -> AINormalizer:
    """Get or create AI normalizer singleton"""
    global _ai_normalizer
    if _ai_normalizer is None:
        _ai_normalizer = AINormalizer()
    return _ai_normalizer


def normalize_with_ai(description: str, use_ai: bool = True) -> NormalizationResult:
    """Convenience function for single normalization"""
    normalizer = get_ai_normalizer()
    return normalizer.normalize(description, use_ai=use_ai)


def normalize_batch_with_ai(
    descriptions: List[str],
    use_ai: bool = True,
    file_context: Optional['FileContext'] = None
) -> List[NormalizationResult]:
    """Convenience function for batch normalization"""
    normalizer = get_ai_normalizer()
    if file_context:
        return normalizer.normalize_with_file_context(descriptions, file_context)
    return normalizer.normalize_batch(descriptions, use_ai=use_ai)


def normalize_with_context(
    descriptions: List[str],
    file_context: 'FileContext'
) -> List[NormalizationResult]:
    """Convenience function for context-aware normalization"""
    normalizer = get_ai_normalizer()
    return normalizer.normalize_with_file_context(descriptions, file_context)
