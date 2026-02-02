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
        ROAD_INFRASTRUCTURE = "road_infrastructure"  # Hạ tầng đường
        GENERAL = "general"                          # Chung

    # Keywords để phân loại nhóm công tác
    CATEGORY_KEYWORDS = {
        WorkCategory.ROAD_INFRASTRUCTURE: [
            'biển báo', 'cọc tiêu', 'cọc km', 'lan can',
            'vạch sơn', 'vạch kẻ', 'sơn vạch',
            'bản quan trắc', 'quan trắc lún',
            'cột đèn', 'đèn chiếu sáng',
            'rải thảm', 'btn c', 'bê tông nhựa',
            'lớp thấm bám', 'tưới nhựa', 'nhựa pha dầu',
            'trồng cây', 'trồng cỏ', 'cây xanh', 'đất màu',
            'tôn sóng', 'hộ lan',
        ],
        WorkCategory.EARTHWORKS_PILING: [
            'đào', 'đắp', 'san', 'ép', 'khoan', 'đóng',
            'cọc', 'đất', 'hố móng', 'móng', 'nền',
            'đầm chặt', 'k95', 'k98', 'k90',  # Compaction
            'cpđd', 'cấp phối', 'đá dăm',  # Aggregate
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
        'lu lèn': 'Lu lèn',
        'đầm': 'Đầm',
        'rải': 'Rải',
        'tưới': 'Tưới',
        'tấm đan': 'Tấm đan',  # Slab/cover
        'bó vỉa': 'Bó vỉa',  # Curb

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
        'bó vỉa': 'Bó vỉa',

        # MEP
        'lắp đặt': 'Lắp đặt',
        'thi công': 'Thi công',

        # Road Infrastructure - Paving
        'rải thảm': 'Rải thảm',
        'lu': 'Lu',
        'đầm nén': 'Đầm nén',
        'tưới nhựa': 'Tưới nhựa',
        'sơn vạch': 'Sơn vạch',
        'kẻ vạch': 'Kẻ vạch',

        # Road Infrastructure - Equipment
        'lắp biển báo': 'Lắp đặt biển báo',
        'lắp đặt biển báo': 'Lắp đặt biển báo',
        'lắp đặt cột': 'Lắp đặt cột',
        'lắp đặt bản quan trắc': 'Lắp đặt bản quan trắc',
        'lắp đặt lan can': 'Lắp đặt lan can',
        'trồng cây': 'Trồng cây',
        'trồng cỏ': 'Trồng cỏ',
    }

    # Vật liệu chuẩn
    STANDARD_MATERIALS = {
        'bê tông': 'bê tông',
        'betong': 'bê tông',
        'bêtông': 'bê tông',
        'btxm': 'BTXM',  # Bê tông xi măng
        'btn': 'BTN',    # Bê tông nhựa (asphalt)
        'cốt thép': 'cốt thép',
        'thép': 'thép',
        'gạch': 'gạch',
        'đất': 'đất',
        'đá': 'đá',
        'đá dăm': 'đá dăm',
        'cấp phối đá dăm': 'CPĐD',
        'cọc': 'cọc',
        'ván khuôn': 'ván khuôn',
        'vải địa kỹ thuật': 'vải ĐKT',
        'nhựa đường': 'nhựa đường',
        'nilon': 'nilon',
        'ni lông': 'nilon',
        'tấm đan': 'tấm đan',
        # MEP materials
        'ống': 'ống',
        'ống ppr': 'ống PPR',
        'ống pvc': 'ống PVC',
        'ống hdpe': 'ống HDPE',
        'ppr': 'PPR',
        'pvc': 'PVC',
        'hdpe': 'HDPE',
        'cáp điện': 'cáp điện',
        'dây điện': 'dây điện',
        'ống gió': 'ống gió',

        # Road Infrastructure Materials
        'nhựa pha dầu': 'nhựa pha dầu',
        'đất màu': 'đất màu',  # Topsoil
        'bản quan trắc': 'bản quan trắc',
        'biển báo': 'biển báo',
        'vạch sơn': 'vạch sơn',
        'cột đèn': 'cột đèn',
        'lan can': 'lan can',
        'tôn sóng': 'tôn sóng',
        'cọc tiêu': 'cọc tiêu',
        'cọc km': 'cọc km',
        'cỏ': 'cỏ',
        'cây xanh': 'cây xanh',
    }

    # Vị trí công tác (luôn viết thường)
    POSITION_KEYWORDS = [
        # Extended positions first (longer patterns)
        'tường trong nhà', 'tường ngoài nhà', 'tường ngoài trời',
        'tường ngoài', 'tường trong',
        'trong nhà', 'ngoài nhà', 'ngoài trời',
        # Foundation/structure positions
        'lót móng', 'đế móng', 'bệ móng', 'hố móng',
        'đài, giằng móng', 'đài móng', 'giằng móng',
        'móng',
        'cột', 'dầm', 'sàn', 'tường', 'vách',
        'dầm sàn', 'dầm trần', 'dầm chính', 'dầm phụ',
        'trần', 'mái', 'nền', 'ngoài', 'trong',
        'hố thang máy', 'hố thu',
        'tầng hầm', 'tầng trệt', 'tầng mái',
        # Road/infrastructure positions
        'mặt đường', 'lề đường', 'vỉa hè', 'hè đường',
        'nền đường', 'móng đường', 'đường',
        'mương', 'rãnh', 'cống', 'hố ga',
        'taluy', 'ta luy', 'bờ kè',
        # MEP positions
        'cấp nước', 'thoát nước', 'trục đứng', 'trục ngang',
        'âm tường', 'âm sàn', 'nổi', 'ngầm',
    ]

    # Equipment/method keywords
    EQUIPMENT_KEYWORDS = {
        'máy đào': 'máy đào',
        'máy xúc': 'máy xúc',
        'máy ép': 'máy ép',
        'robot': 'robot',
        'thủ công': 'thủ công',
        'bằng máy': 'máy đào',
        'bằng thủ công': 'thủ công',
    }

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

        # Strong indicators for road infrastructure (highest priority)
        road_indicators = [
            'biển báo', 'cọc tiêu', 'cọc km', 'bản quan trắc', 'quan trắc',
            'vạch sơn', 'sơn vạch', 'vạch kẻ', 'lan can', 'hộ lan', 'tôn sóng',
            'rải thảm', 'lớp thấm bám', 'nhựa pha dầu', 'btn c',
            'trồng cây', 'trồng cỏ', 'cây xanh', 'đất màu',
        ]
        for indicator in road_indicators:
            if indicator in text_lower:
                return self.WorkCategory.ROAD_INFRASTRUCTURE

        # Strong indicators for specific categories (override scoring)
        # "Bê tông" + position (not cọc/đất) -> concrete_rebar
        if ('bê tông' in text_lower or 'betong' in text_lower or text_lower.startswith('vữa bê tông')):
            if 'cọc' not in text_lower:
                return self.WorkCategory.CONCRETE_REBAR

        # Count matches for each category
        scores = {category: 0 for category in [
            self.WorkCategory.ROAD_INFRASTRUCTURE,
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
        # Skip if it looks like pipe diameter (D63 with PPR/PVC context)
        if not re.search(r'\b(ppr|pvc|hdpe|ống)\b', text_lower):
            match = re.search(r'\bd(\d{1,2})\b', text_lower)
            if match:
                return f"D{match.group(1)}"

        # Pattern 6: Thickness (dày XXXmm, chiều dày XXX)
        match = re.search(r'dày\s*(\d+)\s*mm', text_lower)
        if match:
            return f"dày {match.group(1)}mm"

        # Pattern 7: PC + số (PC30, PC40 - xi măng) -> Domain knowledge mapping
        # PC30 cement for foundation concrete typically means M100
        # PC40 cement typically means M150-M200
        match = re.search(r'\bpc(\d{2})\b', text_lower)
        if match:
            pc_grade = int(match.group(1))
            # Map PC cement grades to concrete M grades (domain knowledge)
            if 'lót móng' in text_lower or 'lót' in text_lower:
                # Foundation lót móng with PC30 -> M100
                pc_to_m = {30: 100, 40: 150}
                if pc_grade in pc_to_m:
                    return f"M{pc_to_m[pc_grade]}"
            # Otherwise just return PC grade
            return f"PC{match.group(1)}"

        # Pattern 8: SS + số (SS400, SS490 - thép kết cấu)
        match = re.search(r'\bss(\d{3})\b', text_lower)
        if match:
            return f"SS{match.group(1)}"

        # Pattern 9: PN + số (PN16, PN10 - áp suất ống)
        match = re.search(r'\bpn\s*(\d+)\b', text_lower)
        if match:
            return f"PN{match.group(1)}"

        # Pattern 10: K + số (K90, K95, K98 - độ đầm chặt/compaction)
        match = re.search(r'\bk\s*(9[0-8])\b', text_lower)
        if match:
            return f"K{match.group(1)}"

        # Pattern 11: BTN Cxx (BTN C12.5, BTN C19 - bê tông nhựa)
        match = re.search(r'\bbtn\s*c(\d+(?:\.\d+)?)\b', text_lower)
        if match:
            return f"BTN C{match.group(1)}"

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

        # Pattern 5b: Stone/curb dimensions (230x260x1000mm or 230x260x1000)
        # Format: WxHxL in mm
        match = re.search(r'(\d{2,3})x(\d{2,3})x(\d{3,4})\s*(?:mm)?', text_lower)
        if match:
            dim_str = f"{match.group(1)}x{match.group(2)}x{match.group(3)}"
            if dim_str not in dimensions:
                dimensions.append(dim_str)

        # Pattern 6: số x số (600x600, 400x200) - không phải H-section
        matches = re.findall(r'(?<!h)(\d+)\s*x\s*(\d+)(?!\s*x)', text_lower)
        for match in matches:
            dim_str = f"{match[0]}x{match[1]}"
            if dim_str not in dimensions:  # Avoid duplicates
                dimensions.append(dim_str)

        # Pattern 7: Plastering thickness only (NOT wall thickness)
        # Skip "chiều dày > X cm" which indicates wall thickness classification
        if not any('dày' in d for d in dimensions):
            has_wall_thickness = re.search(r'chiều\s+dày\s*[><]=?\s*\d+\s*cm', text_lower)
            if not has_wall_thickness:
                size_patterns = [
                    (r'dày\s+(\d+)\s*mm', 'dày', 'mm'),
                    (r'dày\s+(\d+)(?!\s*cm)', 'dày', 'mm'),
                ]
                for pattern, name, unit in size_patterns:
                    match = re.search(pattern, text_lower)
                    if match:
                        dimensions.append(f"{name} {match.group(1)}{unit}")
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
            'details': [],
            'equipment': None,
            'material_detail': None,  # e.g., "gạch granite", "gạch đặc 5x10.5x22"
        }

        text_lower = text_cleaned.lower()

        # Special case: "Vữa bê tông" should be treated as "Bê tông"
        if text_lower.startswith('vữa bê tông') or text_lower.startswith('vữa betong'):
            components['verb'] = 'Bê tông'
            text_lower = re.sub(r'^vữa\s+(bê tông|betong)', '', text_lower).strip()
        else:
            # Extract verb - tìm động từ dài nhất match (ưu tiên cụm động từ)
            sorted_verbs = sorted(self.STANDARD_VERBS.items(), key=lambda x: len(x[0]), reverse=True)
            for vn_verb, standard in sorted_verbs:
                if text_lower.startswith(vn_verb):
                    components['verb'] = standard
                    # Remove verb khỏi text để parse tiếp
                    text_lower = text_lower[len(vn_verb):].strip()
                    break

        # Extract material - tìm vật liệu dài nhất match
        # For earthworks, prioritize "cọc" over "đất" when both are present
        sorted_materials = sorted(self.STANDARD_MATERIALS.items(), key=lambda x: len(x[0]), reverse=True)

        # Special handling: check for "cọc" first in earthworks context
        if 'cọc' in text_lower:
            components['material'] = 'cọc'
        else:
            for vn_material, standard in sorted_materials:
                if vn_material in text_lower:
                    # Skip "đất" if it's part of "đất cấp X" (soil classification, not material)
                    if vn_material == 'đất' and re.search(r'đất\s+cấp\s+\d+', text_lower):
                        # Check if there's another primary material
                        other_materials = [m for m, s in sorted_materials if m != 'đất' and m in text_lower]
                        if other_materials:
                            components['material'] = self.STANDARD_MATERIALS[other_materials[0]]
                            break
                    components['material'] = standard
                    break

        # Extract position
        components['position'] = self.identify_position(text_cleaned)

        # Extract equipment/method
        for equip_key, equip_value in self.EQUIPMENT_KEYWORDS.items():
            if equip_key in text_lower:
                components['equipment'] = equip_value
                break

        # Extract grade
        components['grade'] = self.extract_material_grade(text_cleaned)

        # Extract rebar diameter with comparison (D<10, D<=10, D>18, etc.)
        rebar_match = re.search(r'd\s*([<>=]+)\s*(\d+)', text_lower)
        if rebar_match:
            components['specs'].append(f"D{rebar_match.group(1)}{rebar_match.group(2)}")

        # Extract dimensions
        dimensions = self.extract_dimensions(text_cleaned)
        if dimensions:
            components['specs'].extend(dimensions)

        # Extract brick/tile dimensions with decimal (e.g., 6.5x10.5x22, 6,5x10,5x22)
        # Handle both dot and comma as decimal separator
        text_for_brick = text_lower.replace(',', '.')
        brick_match = re.search(r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*x\s*(\d+)', text_for_brick)
        brick_dim = None
        if brick_match:
            brick_dim = f"{brick_match.group(1)}x{brick_match.group(2)}x{brick_match.group(3)}"

        # Extract material detail for finishing (gạch granite, gạch đặc, etc.)
        if components['material'] == 'gạch':
            if 'granite' in text_lower:
                components['material_detail'] = 'gạch granite'
            elif 'ceramic' in text_lower:
                components['material_detail'] = 'gạch ceramic'
            elif brick_dim:
                # Has brick dimensions - check if "đặc" or "ống"
                # Domain knowledge: dimensions like 6.5x10.5x22 are typically solid bricks (gạch đặc)
                # Dimensions like 8x8x19 or 10x10x20 are typically hollow bricks (gạch ống/block)
                if 'đặc' in text_lower:
                    components['material_detail'] = f"gạch đặc {brick_dim}"
                elif 'ống' in text_lower or 'block' in text_lower:
                    components['material_detail'] = f"gạch ống {brick_dim}"
                else:
                    # Infer type based on typical dimensions (domain knowledge)
                    # Solid bricks: ~6.5x10.5x22 (thickness < 10cm)
                    # Hollow blocks: ~8x8x19, 10x10x20 (more cube-like)
                    first_dim = float(brick_match.group(1)) if brick_match else 0
                    if first_dim > 0 and first_dim < 8:
                        # Small first dimension suggests solid brick
                        components['material_detail'] = f"gạch đặc {brick_dim}"
                    else:
                        components['material_detail'] = f"gạch {brick_dim}"
            elif 'đặc' in text_lower:
                components['material_detail'] = 'gạch đặc'
            elif 'ống' in text_lower:
                components['material_detail'] = 'gạch ống'

        # Extract MEP material types (PPR, PVC, HDPE)
        for mat_type in ['ppr', 'pvc', 'hdpe', 'xlpe', 'phc']:
            if mat_type in text_lower:
                components['material_type'] = mat_type.upper()
                break

        # Extract MEP pipe diameter (D63, D50, D110, etc.) - add to specs
        pipe_diameter = re.search(r'\bd(\d{2,3})\b', text_lower)
        if pipe_diameter and components.get('material_type'):
            components['specs'].append(f"D{pipe_diameter.group(1)}")

        # Extract additional details (thương phẩm, đá 1x2, cấp đất, vữa, etc.)
        detail_patterns = [
            (r'thương\s+phẩm', 'thương phẩm'),
            (r'trộn\s+tại\s+chỗ', 'trộn tại chỗ'),
            (r'đá\s+(\d+)x(\d+)', lambda m: f"đá {m.group(1)}x{m.group(2)}"),
            (r'vữa\s+(M\d+)', lambda m: f"vữa {m.group(1)}"),
            (r'đất\s+cấp\s+(\d+)', lambda m: f"đất cấp {m.group(1)}"),  # Keep "đất cấp X"
            (r'đất\s+mua\s+mới', 'đất mua mới'),  # New soil source
            (r'đất\s+tận\s+dụng', 'đất tận dụng'),  # Reused soil
            (r'nội\s+bộ\s+(?:công\s+trường|dự\s+án)', 'nội bộ dự án'),  # Internal transport
            (r'lớp\s+dưới', 'loại II'),  # Lower layer → Type II
            (r'lớp\s+trên', 'loại I'),  # Upper layer → Type I
            (r'lớp\s+thấm\s+bám', 'lớp thấm bám'),  # Tack coat
            (r'\bkt\s*(\d+)x(\d+)x(\d+)\s*(?:mm|cm)?', lambda m: f"KT {m.group(1)}x{m.group(2)}x{m.group(3)}"),  # Stone/slab dimensions
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
            # MEP details - only add PN if not already in grade
            (r'\bpn\s*(\d+)\b', lambda m: f"PN{m.group(1)}"),
            # Thickness pattern for plastering (dày 15, dày 220) - NOT for wall thickness (chiều dày > 33 cm)
            # Only match "dày X" not "chiều dày > X"
            (r'dày\s+(\d+)(?!\s*mm)', lambda m: f"dày {m.group(1)}"),
        ]

        # Track what's already extracted to avoid duplicates
        extracted_position = components.get('position', '')
        extracted_grade = components.get('grade', '')

        for pattern_def in detail_patterns:
            if len(pattern_def) == 2:
                pattern, replacement = pattern_def
                if callable(replacement):
                    match = re.search(pattern, text_lower)
                    if match:
                        detail_value = replacement(match)
                        # Avoid duplicates with position or already extracted details
                        if detail_value not in components['details']:
                            if extracted_position and detail_value.lower() in extracted_position.lower():
                                continue  # Skip if already in position
                            if extracted_grade and detail_value == extracted_grade:
                                continue  # Skip if already in grade
                            components['details'].append(detail_value)
                else:
                    match = re.search(pattern, text_lower)
                    if match:
                        # Avoid duplicates with position or already extracted details
                        if replacement not in components['details']:
                            if extracted_position and replacement.lower() in extracted_position.lower():
                                continue  # Skip if already in position
                            components['details'].append(replacement)

        return components

    def build_natural_syntax(self, components: Dict, category: str = None) -> str:
        """
        Xây dựng description theo Natural Syntax (Phương án 5)
        Áp dụng template đúng cho từng nhóm công tác

        Templates:
        - Earthworks & Piling: [Hành động][Đối tượng][vị trí] - [Thiết bị/Kích thước] - [Cấp đất/Ghi chú]
        - Concrete & Rebar: [Hành động][Vật liệu][vị trí] - [Mác/Kích thước] - [Đặc tính]
        - Finishing: [Động từ][vị trí] - [Vật liệu chi tiết] - [Kích thước]
        - Steel & MEP: [Động từ][Vật liệu/Hệ thống][vị trí] - [Loại] - [Quy cách]

        Quy tắc:
        1. Headline: Viết hoa chữ cái đầu
        2. Position: Viết thường toàn bộ
        3. Primary specs: Sau dấu - đầu tiên
        4. Details: Sau dấu - thứ hai
        """
        parts = []
        verb = components.get('verb')
        material = components.get('material')
        position = components.get('position')
        equipment = components.get('equipment')
        material_detail = components.get('material_detail')
        grade = components.get('grade')
        specs = components.get('specs', [])
        details = components.get('details', [])

        if category == self.WorkCategory.ROAD_INFRASTRUCTURE:
            # Template varies by work type:
            # Traffic signs: [Lắp đặt] [biển báo] [type] - [size]
            # Monitoring: [Lắp đặt] [bản quan trắc] [type]
            # Paving: [Rải thảm/Tưới] [mặt đường] - [material] - [grade]
            # Landscaping: [Trồng] [cây/cỏ] [location] - [details]
            headline = []
            if verb:
                headline.append(verb)
            if material:
                verb_lower = verb.lower() if verb else ''
                material_lower = material.lower()
                if material_lower not in verb_lower:
                    headline.append(material)
            if position:
                headline.append(position)
            if headline:
                parts.append(' '.join(headline))

            # Add specs and grade
            spec_parts = []
            if specs:
                spec_parts.extend(specs[:2])
            if grade:
                spec_parts.append(grade)
            if spec_parts:
                parts.append(' - ')
                parts.append(' - '.join(spec_parts))

            # Add details
            if details:
                parts.append(' - ')
                parts.append(' '.join(details))

        elif category == self.WorkCategory.FINISHING:
            # Template: [Động từ][vị trí] - [Vật liệu chi tiết] - [Kích thước/Mác]
            # e.g., "Lát sàn - gạch granite - 600x600"
            # e.g., "Trát tường ngoài - dày 15mm - M75"
            # e.g., "Xây tường - gạch đặc 6.5x10.5x22 - M75 - dày 220"
            headline = []
            if verb:
                headline.append(verb)

            # For Xây/Trát/Sơn - include tường/position
            if verb and verb.lower() in ['xây', 'trát', 'sơn']:
                if position:
                    headline.append(position)
                elif verb.lower() == 'xây':
                    # Default: Xây tường gạch
                    headline.append('tường gạch')
                elif verb.lower() == 'trát':
                    # Default: Trát tường
                    headline.append('tường')
            else:
                # For Lát/Ốp - just use simple position
                if position:
                    simple_pos = position.split()[0] if position else None  # Get first word
                    if simple_pos:
                        headline.append(simple_pos)

            if headline:
                parts.append(' '.join(headline))

            # Material detail (gạch granite, gạch đặc 5x10.5x22)
            if material_detail:
                parts.append(' - ')
                parts.append(material_detail)
            elif material and verb and verb.lower() not in ['trát', 'sơn']:
                parts.append(' - ')
                parts.append(material)

            # For masonry (Xây): grade first, then thickness
            if verb and verb.lower() == 'xây':
                # Grade (M75 for mortar)
                if grade:
                    parts.append(' - ')
                    parts.append(grade)
                # Then thickness
                thickness_specs = [s for s in specs if 'dày' in s]
                thickness_details = [d for d in details if d.startswith('dày')]
                if thickness_specs:
                    parts.append(' - ')
                    parts.append(thickness_specs[0])
                elif thickness_details:
                    for td in thickness_details:
                        parts.append(' - ')
                        parts.append(td if 'mm' in td else td)  # Keep as-is (dày 220)
            else:
                # For plastering/painting: specs first, then grade
                spec_parts = []
                # First add thickness from specs
                thickness_specs = [s for s in specs if 'dày' in s]
                if thickness_specs:
                    spec_parts.extend(thickness_specs)
                # Also check thickness from details
                thickness_details = [d for d in details if d.startswith('dày')]
                if thickness_details and not thickness_specs:
                    # Format as "dày Xmm"
                    for td in thickness_details:
                        if 'mm' not in td:
                            spec_parts.append(f"{td}mm")
                        else:
                            spec_parts.append(td)
                # Default thickness for plastering
                if verb and verb.lower() == 'trát' and not spec_parts:
                    spec_parts.append('dày 15mm')

                # Then tile dimensions (NxN format for tiles)
                tile_specs = [s for s in specs if re.match(r'^\d+x\d+$', s)]
                if tile_specs and not material_detail:  # Only if not already in material_detail
                    spec_parts.extend(tile_specs[:1])
                # Add tile dimensions even if material_detail exists (for tiles like granite)
                if tile_specs and material_detail and 'granite' in material_detail.lower():
                    spec_parts.extend(tile_specs[:1])
                if spec_parts:
                    parts.append(' - ')
                    parts.append(' - '.join(spec_parts))

                # Grade (M75 for mortar) - only for plastering, default if not specified
                if verb and verb.lower() == 'trát':
                    if grade:
                        parts.append(' - ')
                        parts.append(grade)
                    else:
                        # Default M75 for plastering
                        parts.append(' - ')
                        parts.append('M75')

            # Details (1 lót 2 phủ for painting) - but not for tiling/masonry
            if details and verb and verb.lower() in ['sơn']:
                # Filter out thickness from details since it's already handled
                paint_details = [d for d in details if not d.startswith('dày')]
                if paint_details:
                    parts.append(' - ')
                    parts.append(' '.join(paint_details))

        elif category == self.WorkCategory.STEEL_MEP:
            # Template: [Động từ][Vật liệu][vị trí] - [Loại] - [Đường kính] - [Áp suất]
            # e.g., "Lắp đặt ống cấp nước - PPR - D63 - PN16"
            headline = []
            if verb:
                headline.append(verb)
            if material:
                # For MEP, don't include material type (PPR/PVC) in headline if it will be added separately
                material_type = components.get('material_type')
                if material_type and material_type in material.upper():
                    # Material includes the type (e.g., "ống PPR") - just use "ống"
                    simple_material = material.split()[0] if ' ' in material else material
                    headline.append(simple_material)
                else:
                    headline.append(material)
            if position:
                headline.append(position)
            if headline:
                parts.append(' '.join(headline))

            # Material type (PPR, PVC, HDPE)
            material_type = components.get('material_type')
            if material_type:
                parts.append(' - ')
                parts.append(material_type)

            # Specs (D63, etc.) - filter out rebar comparison specs
            other_specs = [s for s in specs if not (s.startswith('D') and any(c in s for c in '<>='))]
            if other_specs:
                for spec in other_specs[:2]:
                    parts.append(' - ')
                    parts.append(spec)

            # Grade (PN16, etc.) - always add if present
            if grade:
                parts.append(' - ')
                parts.append(grade)

        elif category == self.WorkCategory.EARTHWORKS_PILING:
            # Template varies by work type:
            # Excavation: [Hành động][Đối tượng][vị trí] - [Thiết bị Kích thước] - [Cấp đất]
            # Piling: [Hành động][Đối tượng] - [Tải trọng] - [Cấp đất]
            # Compaction: [Hành động][Đối tượng] - [Nguồn đất] - [Kxx]
            headline = []
            if verb:
                headline.append(verb)
            # Only add material if it's not already contained in the verb
            if material:
                verb_lower = verb.lower() if verb else ''
                material_lower = material.lower()
                if material_lower not in verb_lower:
                    headline.append(material)
            if position:
                headline.append(position)
            if headline:
                parts.append(' '.join(headline))

            # Check if this is piling work (Ép cọc, đóng cọc)
            is_piling = verb and verb.lower() in ['ép', 'đóng', 'khoan']
            # Check if this is compaction work (Đắp đất)
            is_compaction = verb and verb.lower() == 'đắp' and grade and grade.startswith('K')

            # Equipment + specs (different handling for piling vs excavation)
            equip_specs = []
            if is_piling:
                # For piling: only include specs (load capacity), skip equipment (robot/máy ép)
                if specs:
                    equip_specs.extend(specs[:2])
            elif not is_compaction:
                # For excavation: include equipment + specs
                if equipment:
                    equip_specs.append(equipment)
                if specs:
                    equip_specs.extend(specs[:2])

            if grade and not details and not is_compaction:  # Include grade if no details (not for compaction)
                equip_specs.append(grade)
            if equip_specs:
                parts.append(' - ')
                parts.append(' '.join(equip_specs))

            # Details (đất mua mới, đất tận dụng, đất cấp X, loại I/II)
            if details:
                # Filter details - remove "đầm chặt" (implied for compaction)
                filtered_details = [d for d in details if d != 'đầm chặt']
                if filtered_details:
                    parts.append(' - ')
                    parts.append(' '.join(filtered_details))

            # K grade at the end for compaction work
            if is_compaction and grade:
                parts.append(' - ')
                parts.append(grade)

        elif category == self.WorkCategory.CONCRETE_REBAR:
            # Template: [Hành động][Vật liệu][vị trí] - [Đường kính/Mác] - [Loại thép/Đặc tính]
            # e.g., "Bê tông lót móng - M100 - thương phẩm"
            # e.g., "Gia công cốt thép móng - D<=10 - CB300"
            headline = []
            if verb:
                headline.append(verb)
            if material:
                verb_lower = verb.lower() if verb else ''
                material_lower = material.lower()
                if material_lower not in verb_lower:
                    headline.append(material)
            if position:
                headline.append(position)
            if headline:
                parts.append(' '.join(headline))

            # Specs (D<=10, etc.) and grade
            primary_specs = []
            rebar_specs = [s for s in specs if s.startswith('D') and any(c in s for c in '<>=')]
            if rebar_specs:
                primary_specs.extend(rebar_specs)

            # Default M100 for "lót móng" when no grade specified (but not for ván khuôn)
            effective_grade = grade
            is_formwork = (material and 'ván khuôn' in material.lower()) or (verb and 'ván khuôn' in verb.lower())
            if not effective_grade and position and 'lót móng' in position and not is_formwork:
                effective_grade = 'M100'

            if effective_grade:
                primary_specs.append(effective_grade)
            if primary_specs:
                parts.append(' - ')
                parts.append(' - '.join(primary_specs))

            # Details (thương phẩm)
            if details:
                parts.append(' - ')
                parts.append(' '.join(details))

        else:
            # General fallback
            headline = []
            if verb:
                headline.append(verb)
            if material:
                verb_lower = verb.lower() if verb else ''
                material_lower = material.lower()
                if material_lower not in verb_lower:
                    headline.append(material)
            if position:
                headline.append(position)

            # Special case: nilon without verb -> add "Rải"
            if not verb and material and 'nilon' in material.lower():
                headline = ['Rải', material]

            if headline:
                parts.append(' '.join(headline))

            # Specs and grade
            all_specs = []
            if specs:
                all_specs.extend(specs[:2])
            if grade:
                all_specs.append(grade)

            # Default thickness for nilon: 0.3mm
            if material and 'nilon' in material.lower() and not all_specs:
                all_specs.append('0.3mm')

            if all_specs:
                parts.append(' - ')
                parts.append(' '.join(all_specs))

            # Details
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
