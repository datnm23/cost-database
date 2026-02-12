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
from app.services.ai_structured_schema import (
    StructuredWorkItem, GEMINI_STRUCTURED_SCHEMA,
)

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


# System prompt for AI normalization - Standard Naming Strategy
SYSTEM_PROMPT = """Bạn là chuyên gia về định mức xây dựng Việt Nam. Nhiệm vụ của bạn là chuẩn hóa mô tả công việc xây dựng theo format chuẩn 3 thành phần.

## QUY TẮC BẮT BUỘC - 3 THÀNH PHẦN:

✓ Chỉ dùng ĐÚNG 2 dấu gạch ngang " - " (tạo 3 phần)
✓ Cấu trúc: [TÊN ĐỐI TƯỢNG] - [CHẤT LIỆU/BIẾN THỂ] - [THÔNG SỐ KỸ THUẬT]
✗ KHÔNG được dùng 3+ dấu gạch ngang
✗ KHÔNG tạo ra 4-5 components

**CÁCH GỘP COMPONENTS:**
- PHẦN 1: Tên đối tượng + Vị trí kết cấu (nếu cần)
- PHẦN 2: Chất liệu, loại, variant
- PHẦN 3: Grade, dimensions, specs

**VÍ DỤ ĐÚNG:**
✓ "Bê tông dầm sàn - M350 - đá 1x2"  (3 phần)
✓ "Ống cấp nước - PPR PN16 - D63"  (3 phần)
✓ "MCCB - 3P - 400A 50kA"  (3 phần)
✓ "Biển báo tam giác - A70 - 700x700"  (3 phần)

**VÍ DỤ SAI:**
✗ "Tủ gom công tơ - vỏ tủ điện - tôn - 500V - C1550"  (5 phần!)
✗ "Đèn báo pha - xanh - đỏ - vàng"  (4 phần!)

## QUY TẮC CẮT BỎ ĐỘNG TỪ PHỤ TRỢ:

**LOẠI BỎ:** Cung cấp, Lắp đặt, Thi công, Sản xuất, Gia công, Vận chuyển
**GIỮ LẠI:** Đào, Đắp, San, Lu, Đầm, Rải, Xây, Trát, Lát, Ốp, Sơn, Quét

## TEMPLATES THEO NHÓM:

**Đất & Cọc:**
- "Đào đất hố móng - máy đào 0.8 - đất cấp 3"
- "Đắp đất - K98 - đất mua mới"

**Bê tông & Cốt thép:**
- "Bê tông dầm sàn - M350 - đá 1x2"
- "Bê tông lót móng - M100 - đá 4x6"
- "Cốt thép - CB400V - D10-D18"

**Hoàn thiện:**
- "Xây tường - gạch đặc 6.5x10.5x22 - M75"
- "Lát sàn - gạch granite - 600x600"
- "Trát tường - dày 15mm - M75"

**MEP:**
- "Cáp điện ngầm - Cu/XLPE/PVC - 4x50mm2"
- "Ống cấp nước - PPR PN10 - D50"
- "MCCB - 3P - 400A 50kA"

**Hạ tầng đường:**
- "Biển báo tam giác - A70 - 700x700"
- "Cột đèn - Thép mạ kẽm - H=8m"
- "Vạch sơn liền - Trắng - 150mm"

## QUY TẮC CHỐNG HALLUCINATION:

1. CHỈ trích xuất thông tin CÓ TRONG bản gốc
2. KHÔNG tự thêm màu sắc, vật liệu, specs nếu không được nêu rõ
3. KHÔNG thêm "theo thiết kế" hoặc thông tin không có trong input
4. Nếu thiếu thông tin → giữ nguyên, KHÔNG bịa thêm

## Domain Knowledge Mapping:

- PC30/PC40 xi măng → M100-M150 (lót móng)
- Bê tông lót móng → M100
- Gạch 6.5x10.5x22 → gạch đặc
- D<10 hoặc D<=10 → thép đường kính nhỏ
- CB300, CB400 → mác thép cốt bê tông

Trả về JSON với format:
{
  "normalized": "Mô tả đã chuẩn hóa (ĐÚNG 3 THÀNH PHẦN)",
  "object": "tên đối tượng",
  "material": "chất liệu",
  "specs": ["spec1", "spec2"],
  "work_category": "earthworks_piling|concrete_rebar|finishing|steel_mep|road_infrastructure",
  "confidence": 0.95,
  "corrections": ["Sửa PC30 thành M100", "Gộp thành 3 phần"]
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
                result = json.loads(json_match.group())
                # Validate output format - enforce 3 components
                if 'normalized' in result:
                    result['normalized'] = self._validate_output_format(result['normalized'])
                return result
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI response as JSON: {e}")
            return None

    def _validate_output_format(self, normalized: str) -> str:
        """
        Ensure output has max 2 dashes (3 components).
        This enforces the Standard Naming Strategy 3-component structure.
        """
        if not normalized:
            return normalized

        dash_count = normalized.count(' - ')
        if dash_count > 2:
            # Merge excess components into 3 parts
            parts = normalized.split(' - ')
            if len(parts) > 3:
                return f"{parts[0]} - {' '.join(parts[1:-1])} - {parts[-1]}"
        return normalized

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

    # ── Structured Output Methods (WP4) ──

    STRUCTURED_SYSTEM_PROMPT = """Bạn là chuyên gia phân tích công việc xây dựng Việt Nam.

## NHIỆM VỤ:
Phân tích mỗi mô tả công việc và trả về cấu trúc JSON với các trường sau.

## QUY TẮC CHỐNG HALLUCINATION:
1. CHỈ trích xuất thông tin CÓ TRONG bản gốc
2. KHÔNG tự thêm grade, material, dimension nếu không có trong input
3. Nếu không xác định được → set null cho trường đó
4. Thêm tên trường vào ambiguous_fields nếu không chắc chắn
5. confidence < 0.7 nếu thiếu nhiều thông tin

## NHÓM CÔNG TÁC (group):
- CONC: Bê tông (đổ bê tông, bê tông lót, bê tông kết cấu)
- RBAR: Cốt thép (cốt thép, thép, sắt)
- FWRK: Ván khuôn (coffa, cốp pha)
- PIPE: Ống (cấp nước, thoát nước, ống HDPE/PVC/PPR)
- ELEC: Điện (cáp điện, tủ điện, aptomat, MCCB)
- HVAC: Điều hòa/thông gió
- ROAD: Đường (BTN, asphalt, vỉa hè)
- ERTH: Đất/cọc (đào, đắp, san, ép cọc)
- FNSH: Hoàn thiện (trát, lát, ốp, sơn, xây tường)
- MISC: Khác

## LOẠI CÔNG TÁC (type):
- STR: Kết cấu/cấu trúc
- LEA: Chống thấm
- SUP: Cung cấp vật tư
- INS: Lắp đặt
- EXC: Đào/đắp

## VỊ TRÍ (location):
- COL: Cột
- BEM: Dầm
- SLB: Sàn
- FND: Móng
- WAL: Tường

## WBS CONTEXT:
Nếu có WBS context, sử dụng thông tin section_path và parent_title để:
- Xác định chính xác group
- Cải thiện normalized_description
"""

    def _call_ai_structured(self, items_with_context: List[Dict]) -> Optional[List[Dict]]:
        """
        Call Gemini with structured JSON output using responseSchema.

        Args:
            items_with_context: List of dicts with 'description' and optional 'wbs_context'

        Returns:
            List of structured output dicts or None
        """
        if not items_with_context:
            return None

        client = self._get_client()
        if not client or self.provider != "gemini":
            # For non-Gemini providers, fall back to regular prompt
            return self._call_ai_structured_fallback(items_with_context)

        # Build prompt with WBS context
        items_text = ""
        for i, item in enumerate(items_with_context):
            desc = item.get('description', '')
            wbs = item.get('wbs_context')
            if wbs:
                items_text += f"\n{i+1}. \"{desc}\"\n   WBS: section={wbs.get('section_path', '')}, parent={wbs.get('parent_title', '')}\n"
            else:
                items_text += f"\n{i+1}. \"{desc}\"\n"

        prompt = f"Phân tích {len(items_with_context)} mô tả công việc sau:\n{items_text}"

        try:
            import requests
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            headers = {
                "Content-Type": "application/json",
                "X-goog-api-key": settings.GEMINI_API_KEY,
            }
            data = {
                "contents": [{
                    "parts": [{"text": f"{self.STRUCTURED_SYSTEM_PROMPT}\n\n{prompt}"}]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 2000,
                    "responseMimeType": "application/json",
                    "responseSchema": GEMINI_STRUCTURED_SCHEMA,
                },
            }
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()

            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    text = candidate["content"]["parts"][0].get("text", "")
                    return json.loads(text)
            return None
        except Exception as e:
            logger.error(f"Structured AI call failed: {e}")
            return None

    def _call_ai_structured_fallback(self, items_with_context: List[Dict]) -> Optional[List[Dict]]:
        """Fallback for non-Gemini providers: use regular prompt with JSON instruction."""
        items_text = ""
        for i, item in enumerate(items_with_context):
            desc = item.get('description', '')
            wbs = item.get('wbs_context')
            if wbs:
                items_text += f"\n{i+1}. \"{desc}\" (WBS: {wbs.get('section_path', '')})"
            else:
                items_text += f"\n{i+1}. \"{desc}\""

        prompt = (
            f"{self.STRUCTURED_SYSTEM_PROMPT}\n\n"
            f"Phân tích {len(items_with_context)} mô tả:\n{items_text}\n\n"
            "Trả về JSON array với format StructuredWorkItem cho mỗi item."
        )

        response = self._call_ai(prompt)
        if response:
            return self._parse_batch_response(response)
        return None

    def normalize_structured_batch(
        self,
        items: List[str],
        wbs_contexts: Optional[Dict[int, Dict]] = None,
        batch_size: int = 10,
    ) -> List[Optional[StructuredWorkItem]]:
        """
        Normalize a batch of items with structured LLM output.

        Args:
            items: List of description strings
            wbs_contexts: Optional dict mapping index -> WBS context dict
            batch_size: Number of items per LLM call

        Returns:
            List of StructuredWorkItem or None for failed items
        """
        results: List[Optional[StructuredWorkItem]] = [None] * len(items)

        for batch_start in range(0, len(items), batch_size):
            batch_end = min(batch_start + batch_size, len(items))
            batch_items = []

            for i in range(batch_start, batch_end):
                item_dict = {'description': items[i]}
                if wbs_contexts and i in wbs_contexts:
                    item_dict['wbs_context'] = wbs_contexts[i]
                batch_items.append(item_dict)

            structured_results = self._call_ai_structured(batch_items)
            if structured_results:
                for j, sr in enumerate(structured_results):
                    idx = batch_start + j
                    if idx < len(items):
                        try:
                            results[idx] = StructuredWorkItem(**sr)
                        except Exception as e:
                            logger.warning(f"Failed to parse structured result for item {idx}: {e}")

        return results


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
