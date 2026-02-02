"""
File Context Analyzer Service
Pass 1: Analyze BOQ file structure to detect project type and learn file-specific patterns

Features:
1. Detect project type (road_infrastructure, building, mep, mixed)
2. Identify sections and their row ranges
3. Learn common materials and verbs from file
4. Build project-specific terminology dictionary
"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import pandas as pd

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class Section:
    """Represents a section in the BOQ file"""
    name: str
    start_row: int
    end_row: int
    work_type: str  # earthworks, pavement, drainage, structure, mep, etc.
    item_count: int = 0


@dataclass
class FileContext:
    """Context extracted from BOQ file analysis"""
    project_type: str  # 'road_infrastructure', 'building', 'mep', 'mixed'
    sections: List[Section] = field(default_factory=list)
    common_materials: List[str] = field(default_factory=list)
    common_verbs: List[str] = field(default_factory=list)
    project_specific_terms: Dict[str, str] = field(default_factory=dict)
    dominant_work_types: List[str] = field(default_factory=list)
    confidence: float = 0.0
    total_items: int = 0


# Keywords for project type detection
PROJECT_TYPE_INDICATORS = {
    'road_infrastructure': {
        'strong': [
            'đường', 'mặt đường', 'nền đường', 'móng đường',
            'biển báo', 'vạch sơn', 'lan can', 'hộ lan',
            'btn', 'bê tông nhựa', 'cpđd', 'cấp phối đá dăm',
            'rải thảm', 'lớp thấm bám', 'nhựa pha dầu',
            'cống', 'thoát nước', 'hố ga',
            'trồng cây', 'trồng cỏ', 'cây xanh',
        ],
        'weak': ['đào', 'đắp', 'san', 'nền', 'móng'],
        'weight': 2.0
    },
    'building': {
        'strong': [
            'tầng', 'phòng', 'tường', 'sàn', 'trần',
            'móng đơn', 'móng băng', 'cột', 'dầm',
            'xây', 'trát', 'láng', 'sơn', 'ốp', 'lát',
            'thang máy', 'hành lang', 'ban công',
        ],
        'weak': ['bê tông', 'cốt thép', 'ván khuôn'],
        'weight': 1.5
    },
    'mep': {
        'strong': [
            'điện', 'cấp nước', 'thoát nước', 'thông gió',
            'điều hòa', 'phòng cháy', 'pccc',
            'ống ppr', 'ống pvc', 'ống hdpe',
            'cáp điện', 'dây điện', 'tủ điện',
            'máy bơm', 'quạt', 'van',
        ],
        'weak': ['lắp đặt', 'thi công', 'ống'],
        'weight': 1.5
    }
}

# Section detection patterns
SECTION_PATTERNS = {
    'earthworks': [
        r'công\s+tác\s+đất',
        r'đào\s+đắp',
        r'nền\s+đường',
        r'san\s+nền',
    ],
    'pavement': [
        r'mặt\s+đường',
        r'kết\s+cấu\s+mặt\s+đường',
        r'láng\s+nhựa',
        r'bê\s+tông\s+nhựa',
        r'btn',
    ],
    'drainage': [
        r'thoát\s+nước',
        r'cống',
        r'rãnh',
        r'hố\s+ga',
    ],
    'structure': [
        r'kết\s+cấu',
        r'bê\s+tông',
        r'cốt\s+thép',
        r'ván\s+khuôn',
    ],
    'finishing': [
        r'hoàn\s+thiện',
        r'xây\s+tường',
        r'trát',
        r'sơn',
        r'ốp\s+lát',
    ],
    'traffic_safety': [
        r'an\s+toàn\s+giao\s+thông',
        r'biển\s+báo',
        r'vạch\s+sơn',
        r'tín\s+hiệu',
    ],
    'landscaping': [
        r'cây\s+xanh',
        r'thảm\s+cỏ',
        r'trồng\s+cây',
        r'cảnh\s+quan',
    ],
    'mep': [
        r'điện',
        r'nước',
        r'm\s*&\s*e',
        r'mep',
        r'cơ\s+điện',
    ],
}

# Common abbreviations and their expansions
COMMON_ABBREVIATIONS = {
    'BTN': 'Bê tông nhựa',
    'BTXM': 'Bê tông xi măng',
    'CPĐD': 'Cấp phối đá dăm',
    'ĐKT': 'Địa kỹ thuật',
    'VKT': 'Vải kỹ thuật',
    'GCCT': 'Gia công cốt thép',
    'VK': 'Ván khuôn',
    'PPR': 'Polypropylene Random',
    'PVC': 'Polyvinyl Chloride',
    'HDPE': 'High Density Polyethylene',
    'PCCC': 'Phòng cháy chữa cháy',
}


class FileContextAnalyzer:
    """
    Analyzes BOQ file structure to extract context for improved normalization

    Pass 1 of multi-pass AI analysis strategy
    """

    def __init__(self):
        self._ai_client = None

    def analyze(self, df: pd.DataFrame, description_col: int = 1) -> FileContext:
        """
        Analyze file structure and extract context

        Args:
            df: DataFrame with BOQ data
            description_col: Column index containing descriptions

        Returns:
            FileContext with extracted information
        """
        logger.info("Starting file context analysis...")

        # Extract all descriptions
        descriptions = self._extract_descriptions(df, description_col)

        # Detect project type
        project_type, type_confidence = self._detect_project_type(descriptions)

        # Detect sections
        sections = self._detect_sections(df, description_col)

        # Extract common materials and verbs
        common_materials = self._extract_common_materials(descriptions)
        common_verbs = self._extract_common_verbs(descriptions)

        # Build project-specific terms
        project_terms = self._extract_project_terms(descriptions)

        # Determine dominant work types
        dominant_work_types = self._determine_dominant_work_types(descriptions)

        context = FileContext(
            project_type=project_type,
            sections=sections,
            common_materials=common_materials,
            common_verbs=common_verbs,
            project_specific_terms=project_terms,
            dominant_work_types=dominant_work_types,
            confidence=type_confidence,
            total_items=len(descriptions)
        )

        logger.info(
            f"File context analysis complete: project_type={project_type}, "
            f"sections={len(sections)}, items={len(descriptions)}"
        )

        return context

    def analyze_with_ai(self, df: pd.DataFrame, description_col: int = 1) -> FileContext:
        """
        Enhanced analysis using AI (for complex files)

        Samples 50 rows and uses AI to detect patterns
        """
        # First do rule-based analysis
        context = self.analyze(df, description_col)

        # If confidence is low, try AI enhancement
        if context.confidence < 0.7 and settings.AI_CONTEXT_ANALYSIS_ENABLED:
            try:
                context = self._ai_enhance_context(df, description_col, context)
            except Exception as e:
                logger.warning(f"AI context enhancement failed: {e}")

        return context

    def _extract_descriptions(self, df: pd.DataFrame, col: int) -> List[Tuple[int, str]]:
        """Extract all non-empty descriptions with row numbers"""
        descriptions = []
        for i in range(len(df)):
            if col < len(df.columns):
                val = df.iloc[i, col]
                if pd.notna(val) and isinstance(val, str):
                    val = val.strip()
                    if len(val) > 5:  # Skip very short strings
                        descriptions.append((i, val))
        return descriptions

    def _detect_project_type(self, descriptions: List[Tuple[int, str]]) -> Tuple[str, float]:
        """Detect project type from descriptions"""
        scores = {pt: 0.0 for pt in PROJECT_TYPE_INDICATORS.keys()}

        # Sample descriptions for analysis
        sample_size = min(100, len(descriptions))
        sample = descriptions[:sample_size]

        for _, desc in sample:
            desc_lower = desc.lower()
            for project_type, indicators in PROJECT_TYPE_INDICATORS.items():
                # Strong indicators
                for keyword in indicators['strong']:
                    if keyword in desc_lower:
                        scores[project_type] += indicators['weight']
                # Weak indicators
                for keyword in indicators['weak']:
                    if keyword in desc_lower:
                        scores[project_type] += 0.5

        # Normalize scores
        total = sum(scores.values())
        if total > 0:
            for pt in scores:
                scores[pt] /= total

        # Determine type
        max_score = max(scores.values())
        if max_score < 0.3:
            return 'mixed', max_score

        # Check if it's truly mixed
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_scores) >= 2:
            if sorted_scores[1][1] > 0.3:  # Second type is also significant
                return 'mixed', max_score

        for pt, score in sorted_scores:
            if score == max_score:
                return pt, score

        return 'mixed', 0.5

    def _detect_sections(self, df: pd.DataFrame, col: int) -> List[Section]:
        """Detect sections in the BOQ file"""
        sections = []
        current_section = None
        current_start = 0
        item_count = 0

        for i in range(len(df)):
            if col >= len(df.columns):
                continue

            val = df.iloc[i, col]
            if not pd.notna(val) or not isinstance(val, str):
                continue

            val_lower = val.lower().strip()

            # Check if this is a section header
            section_type = self._identify_section_type(val_lower)

            if section_type:
                # Save previous section
                if current_section:
                    sections.append(Section(
                        name=current_section,
                        start_row=current_start,
                        end_row=i - 1,
                        work_type=self._section_to_work_type(current_section),
                        item_count=item_count
                    ))

                current_section = val
                current_start = i
                item_count = 0
            else:
                item_count += 1

        # Save last section
        if current_section:
            sections.append(Section(
                name=current_section,
                start_row=current_start,
                end_row=len(df) - 1,
                work_type=self._section_to_work_type(current_section),
                item_count=item_count
            ))

        return sections

    def _identify_section_type(self, text: str) -> Optional[str]:
        """Check if text is a section header"""
        # Roman numeral sections
        if re.match(r'^[IVX]+\.\s+', text, re.IGNORECASE):
            return 'roman'
        # Numbered sections
        if re.match(r'^[A-Z]\.\s+', text):
            return 'letter'
        # All caps short headers
        if text.isupper() and len(text) < 50:
            return 'caps'
        # Contains "công tác"
        if 'công tác' in text and len(text) < 60:
            return 'work_category'

        return None

    def _section_to_work_type(self, section_name: str) -> str:
        """Map section name to work type"""
        section_lower = section_name.lower()
        for work_type, patterns in SECTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, section_lower):
                    return work_type
        return 'general'

    def _extract_common_materials(self, descriptions: List[Tuple[int, str]]) -> List[str]:
        """Extract commonly used materials from descriptions"""
        material_counts = {}
        material_keywords = [
            'bê tông', 'btn', 'btxm', 'cpđd', 'cấp phối',
            'đá', 'cát', 'xi măng', 'thép', 'gạch',
            'nhựa', 'nhựa đường', 'nhựa pha dầu',
            'vải đkt', 'nilon', 'ống pvc', 'ống hdpe',
        ]

        for _, desc in descriptions:
            desc_lower = desc.lower()
            for mat in material_keywords:
                if mat in desc_lower:
                    material_counts[mat] = material_counts.get(mat, 0) + 1

        # Return top materials
        sorted_mats = sorted(material_counts.items(), key=lambda x: x[1], reverse=True)
        return [mat for mat, _ in sorted_mats[:10]]

    def _extract_common_verbs(self, descriptions: List[Tuple[int, str]]) -> List[str]:
        """Extract commonly used verbs from descriptions"""
        verb_counts = {}
        verb_keywords = [
            'đào', 'đắp', 'san', 'lu', 'đầm',
            'rải', 'tưới', 'thi công', 'lắp đặt',
            'đổ', 'đúc', 'gia công', 'lắp dựng',
            'xây', 'trát', 'láng', 'sơn', 'ốp', 'lát',
            'cung cấp', 'vận chuyển', 'trồng',
        ]

        for _, desc in descriptions:
            desc_lower = desc.lower()
            for verb in verb_keywords:
                if desc_lower.startswith(verb) or f' {verb}' in desc_lower:
                    verb_counts[verb] = verb_counts.get(verb, 0) + 1

        # Return top verbs
        sorted_verbs = sorted(verb_counts.items(), key=lambda x: x[1], reverse=True)
        return [verb for verb, _ in sorted_verbs[:10]]

    def _extract_project_terms(self, descriptions: List[Tuple[int, str]]) -> Dict[str, str]:
        """Extract project-specific terms and their expansions"""
        terms = {}

        for _, desc in descriptions:
            desc_upper = desc.upper()
            # Find abbreviations
            for abbr, expansion in COMMON_ABBREVIATIONS.items():
                if abbr in desc_upper:
                    terms[abbr] = expansion

            # Find BTN grades (BTN C12.5, BTN C19)
            btn_match = re.search(r'BTN\s*C(\d+(?:\.\d+)?)', desc, re.IGNORECASE)
            if btn_match:
                grade = btn_match.group(1)
                terms[f'BTN C{grade}'] = f'Bê tông nhựa cấp {grade}'

            # Find K compaction grades
            k_match = re.search(r'\bK(9[0-8])\b', desc)
            if k_match:
                k_grade = k_match.group(1)
                terms[f'K{k_grade}'] = f'Độ đầm chặt {k_grade}%'

        return terms

    def _determine_dominant_work_types(self, descriptions: List[Tuple[int, str]]) -> List[str]:
        """Determine dominant work types in the file"""
        type_counts = {}

        for _, desc in descriptions:
            desc_lower = desc.lower()
            for work_type, patterns in SECTION_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, desc_lower):
                        type_counts[work_type] = type_counts.get(work_type, 0) + 1
                        break

        # Return top work types
        sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
        return [wt for wt, _ in sorted_types[:5]]

    def _ai_enhance_context(
        self,
        df: pd.DataFrame,
        col: int,
        base_context: FileContext
    ) -> FileContext:
        """Use AI to enhance context analysis"""
        # Sample 50 rows
        descriptions = self._extract_descriptions(df, col)
        sample_size = min(50, len(descriptions))
        sample = [desc for _, desc in descriptions[:sample_size]]

        prompt = self._build_ai_prompt(sample, base_context)

        # Call AI
        response = self._call_ai(prompt)
        if response:
            try:
                enhanced = self._parse_ai_response(response, base_context)
                return enhanced
            except Exception as e:
                logger.warning(f"Failed to parse AI response: {e}")

        return base_context

    def _build_ai_prompt(self, sample: List[str], context: FileContext) -> str:
        """Build AI prompt for context analysis"""
        sample_text = '\n'.join([f"{i+1}. {desc[:100]}" for i, desc in enumerate(sample[:30])])

        return f"""Phân tích file BOQ này và trả về JSON:

**Sample descriptions:**
{sample_text}

**Initial analysis:**
- Project type: {context.project_type}
- Dominant work types: {context.dominant_work_types}

Please analyze and return:
{{
  "project_type": "road_infrastructure|building|mep|mixed",
  "dominant_work_types": ["earthworks", "pavement", "drainage"],
  "common_materials": ["BTN C19", "CPĐD", "bê tông"],
  "common_verbs": ["Đào", "Đắp", "Rải", "Thi công"],
  "project_terms": {{
    "BTN C19": "Bê tông nhựa cấp 19",
    "CPĐD": "Cấp phối đá dăm"
  }},
  "confidence": 0.9
}}"""

    def _call_ai(self, prompt: str) -> Optional[str]:
        """Call AI API for analysis"""
        if not settings.AI_CONTEXT_ANALYSIS_ENABLED:
            return None

        try:
            if settings.AI_PROVIDER == "gemini":
                import requests
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.AI_MODEL}:generateContent"
                headers = {
                    "Content-Type": "application/json",
                    "X-goog-api-key": settings.GEMINI_API_KEY
                }
                data = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1000}
                }
                response = requests.post(url, headers=headers, json=data, timeout=30)
                response.raise_for_status()
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    return result["candidates"][0]["content"]["parts"][0].get("text", "")
            # Add other providers as needed
        except Exception as e:
            logger.warning(f"AI context analysis failed: {e}")

        return None

    def _parse_ai_response(self, response: str, base: FileContext) -> FileContext:
        """Parse AI response and update context"""
        import json

        # Extract JSON from response
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if not json_match:
            return base

        data = json.loads(json_match.group())

        return FileContext(
            project_type=data.get('project_type', base.project_type),
            sections=base.sections,
            common_materials=data.get('common_materials', base.common_materials),
            common_verbs=data.get('common_verbs', base.common_verbs),
            project_specific_terms=data.get('project_terms', base.project_specific_terms),
            dominant_work_types=data.get('dominant_work_types', base.dominant_work_types),
            confidence=data.get('confidence', base.confidence),
            total_items=base.total_items
        )


# Singleton instance
_file_context_analyzer = None


def get_file_context_analyzer() -> FileContextAnalyzer:
    """Get or create file context analyzer singleton"""
    global _file_context_analyzer
    if _file_context_analyzer is None:
        _file_context_analyzer = FileContextAnalyzer()
    return _file_context_analyzer


def analyze_file_context(df: pd.DataFrame, description_col: int = 1) -> FileContext:
    """Convenience function for file context analysis"""
    analyzer = get_file_context_analyzer()
    return analyzer.analyze(df, description_col)
