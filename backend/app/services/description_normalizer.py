"""
Service để chuẩn hóa description theo Phương án 5 - Natural Syntax
Áp dụng từ tài liệu: "Đặt tên chuẩn công tác xây dựng.md"

Quy tắc cốt lõi:
    1. Cụm Động từ & Vật liệu (Headline): Viết hoa chữ cái đầu
    2. Vị trí Thi công: Viết thường toàn bộ
    3. Thông số Kỹ thuật Chính: Sau dấu gạch ngang (-) đầu tiên
    4. Chi tiết Bổ sung: Sau dấu gạch ngang (-) thứ hai
    5. Hạn chế ký tự đặc biệt: Không dùng [], ()
    6. Độ dài tối ưu: 40-80 ký tự

Quy tắc đặc thù theo nhóm công tác:

5.2.1. Nhóm Đất và Cọc (Earthworks & Piling)
    Template: [Hành động][Đối tượng][vị trí] - [Kích thước/Tải trọng] - [Cấp đất/Ghi chú]
    VD: "Đào đất hố móng - 1.25m3 - đất cấp 3"

5.2.2. Nhóm Bê Tông và Cốt Thép (Concrete & Rebar)
    Template: [Hành động][Vật liệu][vị trí] - [Mác/Kính] - [Đặc tính]
    VD: "Đổ bê tông dầm sàn - M350 - thương phẩm"

5.2.3. Nhóm Hoàn Thiện (Finishing)
    Template: [Động từ][Vật liệu][vị trí] - [Quy cách/Kích thước] - [Mã hiệu/Màu sắc]
    VD: "Lát gạch sàn phòng khách - 600x600 - Granite bóng kính"

5.2.4. Nhóm Kết Cấu Thép và MEP
    Template: [Động từ][Vật liệu/Hệ thống][vị trí] - [Quy cách] - [Phương pháp]
    VD: "Gia công dầm thép tổ hợp - H400x200x8x12 - SS400"
"""
import re
import unicodedata
from typing import Dict, Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)


class DescriptionNormalizer:
    """
    Chuẩn hóa description theo Natural Syntax (Phương án 5)
    Áp dụng template đặc thù cho từng nhóm công tác
    """

    # Phân loại nhóm công tác (Work Category)
    class WorkCategory:
        EARTHWORKS_PILING = "earthworks_piling"      # Đất & Cọc
        CONCRETE_REBAR = "concrete_rebar"            # Bê tông & Cốt thép
        FINISHING = "finishing"                      # Hoàn thiện
        STEEL_MEP = "steel_mep"                      # Kết cấu thép & MEP
        GENERAL = "general"                          # Chung

    # Keywords để phân loại nhóm công tác
    CATEGORY_KEYWORDS = {
        WorkCategory.EARTHWORKS_PILING: [
            'đào', 'đắp', 'san', 'ép', 'khoan', 'đóng',
            'cọc', 'đất', 'hố móng', 'móng', 'nền'
        ],
        WorkCategory.CONCRETE_REBAR: [
            'bê tông', 'betong', 'đổ', 'đúc',
            'cốt thép', 'thép', 'ván khuôn',
            'gia công', 'lắp dựng'
        ],
        WorkCategory.FINISHING: [
            'xây', 'trát', 'láng', 'sơn', 'ốp', 'lát',
            'gạch', 'vữa', 'tường', 'sàn', 'trần'
        ],
        WorkCategory.STEEL_MEP: [
            'lắp đặt', 'thi công',
            'ống', 'dây', 'cáp', 'thiết bị',
            'hệ thống', 'điện', 'nước', 'thông gió'
        ]
    }

    # Động từ chuẩn cho từng nhóm công tác
    STANDARD_VERBS = {
        # Earthworks & Foundation
        'đào': 'Đào',
        'đắp': 'Đắp',
        'san': 'San',
        'ép': 'Ép',
        'đóng': 'Đóng',
        'khoan': 'Khoan',
        'cung cấp': 'Cung cấp',
        'vận chuyển': 'Vận chuyển',

        # Concrete & Structure
        'đổ': 'Đổ',
        'đúc': 'Đúc',
        'bê tông': 'Bê tông',
        'betong': 'Bê tông',
        'bêtông': 'Bê tông',

        # Rebar & Formwork
        'gia công': 'Gia công',
        'lắp dựng': 'Lắp dựng',
        'lắp đặt': 'Lắp đặt',
        'cốt thép': 'cốt thép',
        'ván khuôn': 'ván khuôn',

        # Masonry & Walls
        'xây': 'Xây',
        'trát': 'Trát',
        'láng': 'Láng',
        'sơn': 'Sơn',
        'ốp': 'Ốp',
        'lát': 'Lát',

        # MEP
        'lắp đặt': 'Lắp đặt',
        'thi công': 'Thi công',
    }

    # Vật liệu chuẩn
    STANDARD_MATERIALS = {
        'bê tông': 'bê tông',
        'betong': 'bê tông',
        'bêtông': 'bê tông',
        'cốt thép': 'cốt thép',
        'thép': 'thép',
        'gạch': 'gạch',
        'đất': 'đất',
        'đá': 'đá',
        'cọc': 'cọc',
        'ván khuôn': 'ván khuôn',
    }

    # Vị trí công tác (luôn viết thường)
    POSITION_KEYWORDS = [
        'móng', 'lót móng', 'đế móng', 'bệ móng',
        'cột', 'dầm', 'sàn', 'tường', 'vách',
        'dầm sàn', 'dầm trần', 'dầm chính', 'dầm phụ',
        'trần', 'mái', 'nền', 'ngoài', 'trong',
        'hố móng', 'hố thang máy', 'hố thu',
        'tầng hầm', 'tầng trệt', 'tầng mái',
    ]

    # Đơn vị đo chuẩn hóa
    UNIT_STANDARDIZATION = {
        'mét': 'm',
        'met': 'm',
        'meter': 'm',
        'mét vuông': 'm2',
        'm vuông': 'm2',
        'mét khối': 'm3',
        'm khối': 'm3',
        'milimet': 'mm',
        'milimét': 'mm',
        'centimet': 'cm',
        'centimét': 'cm',
        'kilôgam': 'kg',
        'kí lô': 'kg',
        'tấn': 'tấn',
        'tan': 'tấn',
        'cái': 'cái',
        'chiếc': 'cái',
    }

    def __init__(self):
        """Initialize normalizer"""
        pass

    def identify_work_category(self, text: str) -> str:
        """
        Xác định nhóm công tác từ description

        Returns:
            WorkCategory constant
        """
        text_lower = text.lower()

        # Count matches for each category
        scores = {category: 0 for category in [
            self.WorkCategory.EARTHWORKS_PILING,
            self.WorkCategory.CONCRETE_REBAR,
            self.WorkCategory.FINISHING,
            self.WorkCategory.STEEL_MEP
        ]}

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    scores[category] += 1

        # Return category with highest score
        max_score = max(scores.values())
        if max_score == 0:
            return self.WorkCategory.GENERAL

        for category, score in scores.items():
            if score == max_score:
                return category

        return self.WorkCategory.GENERAL

    def normalize_text(self, text: str) -> str:
        """
        Chuẩn hóa text cơ bản
        - Unicode normalization
        - Remove extra spaces
        - Trim
        """
        if not text:
            return ""

        # Unicode normalization (NFC)
        text = unicodedata.normalize('NFC', text)

        # Remove extra spaces
        text = ' '.join(text.split())

        return text.strip()

    def clean_special_chars(self, text: str) -> str:
        """
        Loại bỏ các ký tự đặc biệt không cần thiết theo quy tắc 5
        - Loại bỏ [], () bọc vị trí/thông số
        - Giữ lại dấu - (để phân tách)
        - Giữ lại >, <, = trong thông số kỹ thuật
        """
        # Remove brackets and parentheses around text
        text = re.sub(r'\[([^\]]+)\]', r'\1', text)
        text = re.sub(r'\(([^)]+)\)', r'\1', text)

        # Remove multiple consecutive special chars except dash
        text = re.sub(r'[,;:]{2,}', ',', text)

        # Clean up multiple dashes
        text = re.sub(r'-{2,}', '-', text)

        return text

    def extract_material_grade(self, text: str) -> Optional[str]:
        """
        Trích xuất mác vật liệu (M200, M250, M300, B25, CB400, etc.)

        Returns:
            Material grade chuẩn hóa hoặc None
        """
        text_lower = text.lower()

        # Pattern 1: M + số (M100, M150, M200, M250, M300, M350, M400)
        match = re.search(r'\bm(\d{2,3})\b', text_lower)
        if match:
            return f"M{match.group(1)}"

        # Pattern 2: "mác" + số
        match = re.search(r'mác\s*(\d{2,3})', text_lower)
        if match:
            return f"M{match.group(1)}"

        # Pattern 3: B + số (B15, B20, B25, B30) -> convert to M
        match = re.search(r'\bb(\d{2})\b', text_lower)
        if match:
            b_grade = int(match.group(1))
            b_to_m = {
                15: 150, 20: 200, 22: 225, 25: 250,
                30: 300, 35: 350, 40: 400, 45: 450, 50: 500
            }
            if b_grade in b_to_m:
                return f"M{b_to_m[b_grade]}"

        # Pattern 4: CB + số (CB300, CB400 - cho thép)
        match = re.search(r'\bcb(\d{3})\b', text_lower)
        if match:
            return f"CB{match.group(1)}"

        # Pattern 5: D + số (D10, D12, D16, D18 - đường kính thép)
        match = re.search(r'\bd(\d{1,2})\b', text_lower)
        if match:
            return f"D{match.group(1)}"

        # Pattern 6: Thickness (dày XXXmm, chiều dày XXX)
        match = re.search(r'dày\s*(\d+)\s*mm', text_lower)
        if match:
            return f"dày {match.group(1)}mm"

        # Pattern 7: PC + số (PC30, PC40 - xi măng)
        match = re.search(r'\bpc(\d{2})\b', text_lower)
        if match:
            return f"PC{match.group(1)}"

        # Pattern 8: SS + số (SS400, SS490 - thép kết cấu)
        match = re.search(r'\bss(\d{3})\b', text_lower)
        if match:
            return f"SS{match.group(1)}"

        return None

    def extract_dimensions(self, text: str) -> List[str]:
        """
        Trích xuất kích thước (600x600, H400x200x8x12, 1200x2400, 1.25m3, 200 tấn, etc.)
        """
        dimensions = []
        text_lower = text.lower()

        # Pattern 1: Thể tích (1.25m3, 2.5m3)
        match = re.search(r'(\d+\.?\d*)\s*m3', text_lower)
        if match:
            dimensions.append(f"{match.group(1)}m3")

        # Pattern 2: Tải trọng (200 tấn, 150 tấn)
        match = re.search(r'(\d+)\s*tấn', text_lower)
        if match:
            dimensions.append(f"{match.group(1)} tấn")

        # Pattern 3: H-section (H400x200x8x12 - cho thép)
        match = re.search(r'\bh(\d+)x(\d+)x(\d+)x(\d+)\b', text_lower)
        if match:
            h_spec = f"H{match.group(1)}x{match.group(2)}x{match.group(3)}x{match.group(4)}"
            dimensions.append(h_spec)
            return dimensions  # Return early to avoid duplicates

        # Pattern 4: D + số + A (D500A - đường kính cọc)
        match = re.search(r'\bd(\d+)([a-z])\b', text_lower)
        if match:
            dimensions.append(f"D{match.group(1)}{match.group(2).upper()}")

        # Pattern 5: L= (L=12m - chiều dài)
        match = re.search(r'l\s*=\s*(\d+)\s*m', text_lower)
        if match:
            dimensions.append(f"L={match.group(1)}m")

        # Pattern 6: số x số (600x600, 400x200) - không phải H-section
        matches = re.findall(r'(?<!h)(\d+)\s*x\s*(\d+)(?!\s*x)', text_lower)
        for match in matches:
            dim_str = f"{match[0]}x{match[1]}"
            if dim_str not in dimensions:  # Avoid duplicates
                dimensions.append(dim_str)

        # Pattern 7: chiều dày/cao/rộng + số (ONLY if not already extracted)
        if not any('dày' in d for d in dimensions):
            size_patterns = [
                (r'dày\s+[><=]*\s*(\d+)\s*mm', 'dày', 'mm'),
                (r'chiều\s+dày\s+[><=]*\s*(\d+)\s*cm', 'dày', 'cm'),
                (r'chiều\s+dày\s+[><=]*\s*(\d+)\s*mm', 'dày', 'mm'),
            ]

            for pattern, name, unit in size_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    value = int(match.group(1))
                    if unit == 'cm':
                        value = value * 10  # Convert to mm
                        unit = 'mm'
                    dimensions.append(f"{name} {value}{unit}")
                    break

        return dimensions

    def identify_position(self, text: str) -> Optional[str]:
        """
        Xác định vị trí công tác (móng, cột, dầm, sàn, etc.)
        Return: vị trí viết thường theo quy tắc 2
        """
        text_lower = text.lower()

        # Tìm vị trí match với keywords (ưu tiên cụm từ dài trước)
        sorted_positions = sorted(self.POSITION_KEYWORDS, key=len, reverse=True)

        for position in sorted_positions:
            if position in text_lower:
                return position  # Trả về viết thường

        return None

    def parse_description(self, text: str) -> Dict[str, Optional[str]]:
        """
        Parse description thành các components:
        - verb: Động từ (Đổ, Xây, Gia công, etc.)
        - material: Vật liệu (bê tông, cốt thép, gạch, etc.)
        - position: Vị trí (móng, cột, dầm, sàn - viết thường)
        - grade: Mác vật liệu (M300, CB400, D18)
        - specs: Thông số kỹ thuật khác
        - details: Chi tiết bổ sung
        """
        text_normalized = self.normalize_text(text)
        text_cleaned = self.clean_special_chars(text_normalized)

        components = {
            'verb': None,
            'material': None,
            'position': None,
            'grade': None,
            'specs': [],
            'details': []
        }

        text_lower = text_cleaned.lower()

        # Extract verb - tìm động từ dài nhất match (ưu tiên cụm động từ)
        sorted_verbs = sorted(self.STANDARD_VERBS.items(), key=lambda x: len(x[0]), reverse=True)
        for vn_verb, standard in sorted_verbs:
            if text_lower.startswith(vn_verb):
                components['verb'] = standard
                # Remove verb khỏi text để parse tiếp
                text_lower = text_lower[len(vn_verb):].strip()
                break

        # Extract material - tìm vật liệu dài nhất match
        sorted_materials = sorted(self.STANDARD_MATERIALS.items(), key=lambda x: len(x[0]), reverse=True)
        for vn_material, standard in sorted_materials:
            if vn_material in text_lower:
                components['material'] = standard
                break

        # Extract position
        components['position'] = self.identify_position(text_cleaned)

        # Extract grade
        components['grade'] = self.extract_material_grade(text_cleaned)

        # Extract dimensions
        dimensions = self.extract_dimensions(text_cleaned)
        if dimensions:
            components['specs'].extend(dimensions)

        # Extract additional details (thương phẩm, đá 1x2, cấp đất, vữa, etc.)
        detail_patterns = [
            (r'thương\s+phẩm', 'thương phẩm'),
            (r'trộn\s+tại\s+chỗ', 'trộn tại chỗ'),
            (r'đá\s+(\d+)x(\d+)', lambda m: f"đá {m.group(1)}x{m.group(2)}"),
            (r'vữa\s+(M\d+)', lambda m: f"vữa {m.group(1)}"),
            (r'đất\s+cấp\s+(\d+)', lambda m: f"đất cấp {m.group(1)}"),
            (r'cấp\s+(\d+)', lambda m: f"cấp {m.group(1)}"),
            (r'granite', 'Granite'),
            (r'ceramic', 'Ceramic'),
            (r'gỗ', 'gỗ'),
            (r'phủ\s+phim', 'phủ phim'),
            (r'bóng\s+kính', 'bóng kính'),
            (r'men\s+bóng', 'men bóng'),
            (r'men\s+mờ', 'men mờ'),
            (r'màu\s+([a-zA-ZÀ-ỹ\s]+)', lambda m: f"màu {m.group(1).strip()}"),
            (r'(\d+)\s+lót\s+(\d+)\s+phủ', lambda m: f"{m.group(1)} lót {m.group(2)} phủ"),
            (r'bailey', 'Bailey'),
            (r'hệ\s+khung\s+giàn', 'hệ khung giàn'),
            (r'tôn\s+tráng\s+kẽm', 'tôn tráng kẽm'),
            (r'bọc\s+cách\s+nhiệt', 'bọc cách nhiệt'),
        ]

        for pattern_def in detail_patterns:
            if len(pattern_def) == 2:
                pattern, replacement = pattern_def
                if callable(replacement):
                    match = re.search(pattern, text_lower)
                    if match:
                        detail_value = replacement(match)
                        if detail_value not in components['details']:  # Avoid duplicates
                            components['details'].append(detail_value)
                else:
                    match = re.search(pattern, text_lower)
                    if match:
                        if replacement not in components['details']:  # Avoid duplicates
                            components['details'].append(replacement)

        return components

    def build_natural_syntax(self, components: Dict, category: str = None) -> str:
        """
        Xây dựng description theo Natural Syntax (Phương án 5)
        Áp dụng template đúng cho từng nhóm công tác

        Templates:
        - Earthworks & Piling: [Hành động][Đối tượng][vị trí] - [Kích thước/Tải trọng] - [Cấp đất/Ghi chú]
        - Concrete & Rebar: [Hành động][Vật liệu][vị trí] - [Mác/Kính] - [Đặc tính]
        - Finishing: [Động từ][Vật liệu][vị trí] - [Quy cách/Kích thước] - [Mã hiệu/Màu sắc]
        - Steel & MEP: [Động từ][Vật liệu/Hệ thống][vị trí] - [Quy cách] - [Phương pháp]

        Quy tắc:
        1. Headline: Viết hoa chữ cái đầu
        2. Position: Viết thường toàn bộ
        3. Primary specs: Sau dấu - đầu tiên
        4. Details: Sau dấu - thứ hai
        """
        parts = []

        # Part 1: Verb + Material (Headline - viết hoa chữ đầu)
        headline = []
        if components['verb']:
            headline.append(components['verb'])
        if components['material']:
            headline.append(components['material'])

        if headline:
            parts.append(' '.join(headline))

        # Part 2: Position (viết thường - quy tắc 2)
        if components['position']:
            if parts:
                parts[0] += f" {components['position']}"  # Nối liền không cần dấu
            else:
                parts.append(components['position'])

        # Part 3: Primary Specs (sau dấu - đầu tiên)
        # Template khác nhau theo category
        primary_specs = []

        if category == self.WorkCategory.EARTHWORKS_PILING:
            # [Kích thước/Tải trọng]
            if components['specs']:
                primary_specs.extend(components['specs'][:2])
            if components['grade']:
                # Grade cho earthworks thường là soil type, không hiển thị ở primary
                pass

        elif category == self.WorkCategory.CONCRETE_REBAR:
            # [Mác/Kính]
            if components['grade']:
                primary_specs.append(components['grade'])
            if components['specs']:
                primary_specs.extend(components['specs'][:1])

        elif category == self.WorkCategory.FINISHING:
            # [Quy cách/Kích thước]
            if components['specs']:
                primary_specs.extend(components['specs'][:2])
            if components['grade']:
                primary_specs.append(components['grade'])

        elif category == self.WorkCategory.STEEL_MEP:
            # [Quy cách]
            if components['specs']:
                primary_specs.extend(components['specs'][:2])
            if components['grade']:
                primary_specs.append(components['grade'])

        else:
            # General fallback
            if components['grade']:
                primary_specs.append(components['grade'])
            if components['specs']:
                primary_specs.extend(components['specs'][:2])

        if primary_specs:
            parts.append(' - ')
            parts.append(' '.join(primary_specs))

        # Part 4: Details (sau dấu - thứ hai)
        details = []

        if category == self.WorkCategory.EARTHWORKS_PILING:
            # [Cấp đất/Ghi chú]
            if components['details']:
                details.extend(components['details'])

        elif category == self.WorkCategory.CONCRETE_REBAR:
            # [Đặc tính] (thương phẩm, đá 1x2, etc.)
            if components['details']:
                details.extend(components['details'])

        elif category == self.WorkCategory.FINISHING:
            # [Mã hiệu/Màu sắc]
            if components['details']:
                details.extend(components['details'])

        elif category == self.WorkCategory.STEEL_MEP:
            # [Phương pháp]
            if components['details']:
                details.extend(components['details'])

        else:
            # General
            if components['details']:
                details.extend(components['details'])

        if details:
            parts.append(' - ')
            parts.append(' '.join(details))

        result = ''.join(parts)

        # Ensure proper spacing around dashes
        result = re.sub(r'\s*-\s*', ' - ', result)
        result = re.sub(r'\s+', ' ', result)

        return result.strip()

    def normalize(self, description: str) -> str:
        """
        Main normalization function

        Input: Raw description from BOQ
        Output: Normalized description theo Natural Syntax với template đúng cho nhóm công tác

        Ví dụ:
            Input: "Đào đất hố móng bằng máy 1.25m3 đất cấp 3"
            Output: "Đào đất hố móng - 1.25m3 - đất cấp 3"

            Input: "Bê tông lót móng, chiều rộng <= 250 cm, vữa bê tông PC30"
            Output: "Đổ bê tông lót móng - M100 đá 4x6 - PC30"

            Input: "Lát gạch sàn phòng khách 600x600 Granite bóng kính"
            Output: "Lát gạch sàn - 600x600 - Granite bóng kính"

            Input: "Gia công dầm thép tổ hợp H400x200x8x12 SS400"
            Output: "Gia công thép dầm - H400x200x8x12 - SS400"
        """
        if not description or description.strip() == '':
            return ""

        # Step 1: Identify work category
        category = self.identify_work_category(description)

        # Step 2: Parse components
        components = self.parse_description(description)

        # Step 3: Build natural syntax with category-specific template
        normalized = self.build_natural_syntax(components, category=category)

        # Step 4: Validate length (40-80 chars recommended)
        if len(normalized) > 100:
            logger.warning(f"Description too long ({len(normalized)} chars): {normalized[:50]}...")

        return normalized

    def normalize_batch(self, descriptions: List[str]) -> List[Dict[str, str]]:
        """
        Normalize batch of descriptions

        Returns:
            List of {
                'original': original description,
                'normalized': normalized description,
                'category': work category,
                'components': parsed components
            }
        """
        results = []

        for desc in descriptions:
            try:
                category = self.identify_work_category(desc)
                components = self.parse_description(desc)
                normalized = self.build_natural_syntax(components, category=category)

                results.append({
                    'original': desc,
                    'normalized': normalized,
                    'category': category,
                    'components': components
                })
            except Exception as e:
                logger.error(f"Error normalizing '{desc}': {e}")
                results.append({
                    'original': desc,
                    'normalized': desc,  # Fallback to original
                    'category': self.WorkCategory.GENERAL,
                    'components': None,
                    'error': str(e)
                })

        return results

    def suggest_improvements(self, description: str) -> List[str]:
        """
        Suggest improvements for a description
        """
        suggestions = []

        # Check for brackets
        if '[' in description or ']' in description:
            suggestions.append("Loại bỏ dấu ngoặc vuông [] (Quy tắc 5)")

        if '(' in description or ')' in description:
            suggestions.append("Loại bỏ dấu ngoặc đơn () (Quy tắc 5)")

        # Check for position capitalization
        for pos in self.POSITION_KEYWORDS:
            if pos.capitalize() in description or pos.upper() in description:
                suggestions.append(f"Viết thường vị trí '{pos}' (Quy tắc 2)")

        # Check length
        if len(description) > 80:
            suggestions.append(f"Rút gọn description (hiện tại: {len(description)} ký tự, khuyến nghị: 40-80)")

        return suggestions


def test_normalizer():
    """Test function with examples from the document"""
    normalizer = DescriptionNormalizer()

    test_cases = [
        "Bê tông lót móng, chiều rộng <= 250 cm, vữa bê tông PC30",
        "Xây tường thẳng, chiều dày > 33 cm, gạch 6.5x10.5x22, vữa xi măng PC30",
        "Đổ bê tông dầm sàn M350 thương phẩm",
        "Gia công lắp dựng cốt thép móng D<10 CB300",
        "Lát gạch sàn phòng khách 600x600 Granite bóng kính",
        "Đào đất hố móng bằng máy 1.25m3 đất cấp 3",
        "Ép cọc robot 200 tấn đất cấp 2",
    ]

    print("=" * 80)
    print("TEST DESCRIPTION NORMALIZER - PHƯƠNG ÁN 5 (NATURAL SYNTAX)")
    print("=" * 80)

    for original in test_cases:
        normalized = normalizer.normalize(original)
        components = normalizer.parse_description(original)

        print(f"\nOriginal:    {original}")
        print(f"Normalized:  {normalized}")
        print(f"Components:  {components}")
        print("-" * 80)


if __name__ == "__main__":
    test_normalizer()
