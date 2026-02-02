"""
Hệ thống tạo mã công tác (Work Code) nhất quán và có ý nghĩa

Cấu trúc Work Code:
    Format: {SEC_PREFIX}-{CATEGORY}-{SEQUENCE}

    Ví dụ:
    - S01-EARTH-EXCAV-0001: Đào đất (SEC-01, Earthworks, Excavation)
    - S02-CONC-BEAM-0015: Dầm bê tông (SEC-02, Concrete, Beam)
    - S03-WALL-BRICK-0008: Tường gạch (SEC-03, Wall, Brick)

Nguyên tắc:
    1. Dễ đọc, dễ hiểu ngay ý nghĩa công tác
    2. Có thể tìm kiếm theo từng phần (SEC, category, type)
    3. Sắp xếp logic theo nhóm
    4. Tránh trùng lặp
    5. Có thể mở rộng
"""
import re
import unicodedata
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.master_work_item import MasterWorkItem


class WorkCodeGenerator:
    """
    Generator để tạo mã công tác nhất quán
    """

    # Mapping SEC codes to short prefixes
    SEC_PREFIX_MAP = {
        'SEC-00': 'S00',
        'SEC-01': 'S01',
        'SEC-01-01': 'S01',  # Earthworks
        'SEC-01-02': 'S01',  # Piling
        'SEC-01-03': 'S01',  # Foundation
        'SEC-02': 'S02',     # Superstructure
        'SEC-03': 'S03',     # Architecture & Finishes
        'SEC-04': 'S04',     # MEP
        'SEC-05': 'S05',     # Landscape
    }

    # Từ khóa chính cho categories (Vietnamese -> English code)
    CATEGORY_KEYWORDS = {
        # Earthworks (SEC-01)
        'đào': 'EARTH',
        'đắp': 'FILL',
        'san': 'LEVEL',
        'nền': 'GROUND',
        'cọc': 'PILE',
        'khoan': 'DRILL',
        'móng': 'FOUND',

        # Concrete & Structure (SEC-02)
        'bê tông': 'CONC',
        'bêtông': 'CONC',
        'be tong': 'CONC',
        'betong': 'CONC',
        'cốt thép': 'REBAR',
        'sàn': 'SLAB',
        'dầm': 'BEAM',
        'cột': 'COL',
        'tường': 'WALL',
        'kết cấu': 'STRUC',

        # Architecture (SEC-03)
        'tường': 'WALL',
        'gạch': 'BRICK',
        'vữa': 'MORT',
        'trát': 'PLAST',
        'sơn': 'PAINT',
        'lát': 'TILE',
        'trần': 'CEIL',
        'mái': 'ROOF',
        'cửa': 'DOOR',
        'cửa sổ': 'WIND',

        # MEP (SEC-04)
        'điện': 'ELEC',
        'nước': 'WATER',
        'thang máy': 'ELEV',
        'thông gió': 'VENT',
        'điều hòa': 'HVAC',
        'pccc': 'FIRE',
        'cháy': 'FIRE',

        # Landscape (SEC-05)
        'cảnh quan': 'LAND',
        'đường': 'ROAD',
        'vỉa': 'PAVE',
        'cây': 'TREE',
        'hàng rào': 'FENCE',
        'cổng': 'GATE',
        'hồ': 'POND',
        'bãi': 'PARK',
    }

    # Sub-categories (chi tiết hơn)
    SUB_KEYWORDS = {
        'đào đất': 'EXCAV',
        'đắp đất': 'BACKFILL',
        'san lấp': 'LEVEL',
        'cọc khoan': 'DPILE',
        'cọc nhồi': 'BPILE',
        'móng băng': 'STRIP',
        'móng bè': 'RAFT',

        'bê tông': 'CONC',
        'cốt thép': 'REBAR',
        'ván khuôn': 'FORM',

        'gạch': 'BRICK',
        'block': 'BLOCK',
        'tường xây': 'MASON',
        'trát tường': 'PLAST',
        'sơn tường': 'PAINT',
        'lát nền': 'FLOOR',
        'lát gạch': 'TILE',

        'điện': 'ELEC',
        'nước': 'PLUMB',
        'thang máy': 'ELEV',
        'thông gió': 'VENT',

        'đường': 'ROAD',
        'vỉa hè': 'SIDE',
        'cây xanh': 'PLANT',
        'hàng rào': 'FENCE',
        'cổng': 'GATE',
    }

    def __init__(self, db: Session):
        self.db = db

    def normalize_text(self, text: str) -> str:
        """Chuẩn hóa text: lowercase, remove accents, extra spaces"""
        if not text:
            return ""

        # Unicode normalization
        text = unicodedata.normalize('NFC', text)
        text = text.lower().strip()

        # Remove extra spaces
        text = ' '.join(text.split())

        return text

    def remove_accents(self, text: str) -> str:
        """Remove Vietnamese accents for ASCII codes"""
        # Mapping Vietnamese characters to ASCII
        vietnamese_map = {
            'à': 'a', 'á': 'a', 'ạ': 'a', 'ả': 'a', 'ã': 'a',
            'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ậ': 'a', 'ẩ': 'a', 'ẫ': 'a',
            'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ặ': 'a', 'ẳ': 'a', 'ẵ': 'a',
            'è': 'e', 'é': 'e', 'ẹ': 'e', 'ẻ': 'e', 'ẽ': 'e',
            'ê': 'e', 'ề': 'e', 'ế': 'e', 'ệ': 'e', 'ể': 'e', 'ễ': 'e',
            'ì': 'i', 'í': 'i', 'ị': 'i', 'ỉ': 'i', 'ĩ': 'i',
            'ò': 'o', 'ó': 'o', 'ọ': 'o', 'ỏ': 'o', 'õ': 'o',
            'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ộ': 'o', 'ổ': 'o', 'ỗ': 'o',
            'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ợ': 'o', 'ở': 'o', 'ỡ': 'o',
            'ù': 'u', 'ú': 'u', 'ụ': 'u', 'ủ': 'u', 'ũ': 'u',
            'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ự': 'u', 'ử': 'u', 'ữ': 'u',
            'ỳ': 'y', 'ý': 'y', 'ỵ': 'y', 'ỷ': 'y', 'ỹ': 'y',
            'đ': 'd', 'Đ': 'D'
        }

        result = []
        for char in text:
            result.append(vietnamese_map.get(char, char))

        return ''.join(result)

    def extract_material_grade(self, description: str) -> Optional[str]:
        """
        Trích xuất mác vật liệu từ description

        Ví dụ:
        - "Bê tông M200" -> "M200"
        - "Vữa trát M75" -> "M75"
        - "Bê tông mác 250" -> "M250"
        - "Concrete grade 300" -> "M300"
        - "Bê tông B25" -> "M250" (B25 = M250)
        - "Bê tông B30" -> "M300" (B30 = M300)

        Returns:
            Material grade code (e.g., "M200") hoặc None
        """
        desc_normalized = self.normalize_text(description)

        # Pattern 1: M + số (M200, M250, M300, etc.)
        match = re.search(r'\bm(\d{2,3})\b', desc_normalized)
        if match:
            return f"M{match.group(1)}"

        # Pattern 2: "mác" + số
        match = re.search(r'mác\s*(\d{2,3})', desc_normalized)
        if match:
            return f"M{match.group(1)}"

        # Pattern 3: "grade" + số
        match = re.search(r'grade\s*(\d{2,3})', desc_normalized)
        if match:
            return f"M{match.group(1)}"

        # Pattern 4: "cấp" + số
        match = re.search(r'cấp\s*(\d{2,3})', desc_normalized)
        if match:
            return f"M{match.group(1)}"

        # Pattern 5: B + số (Vietnamese concrete standard B15, B20, B25, B30, B35, B40)
        # B15 = M150, B20 = M200, B25 = M250, B30 = M300, B35 = M350, B40 = M400
        match = re.search(r'\bb(\d{2})\b', desc_normalized)
        if match:
            b_grade = int(match.group(1))
            # Convert B-grade to M-grade
            b_to_m = {
                15: 150,
                20: 200,
                22.5: 225,
                25: 250,
                30: 300,
                35: 350,
                40: 400,
                45: 450,
                50: 500
            }
            m_grade = b_to_m.get(b_grade)
            if m_grade:
                return f"M{m_grade}"

        return None

    def extract_category(self, description: str, sec_code: str) -> Tuple[str, str]:
        """
        Trích xuất category và sub-category từ description

        Returns:
            (category_code, sub_code)
        """
        desc_normalized = self.normalize_text(description)

        # Try to find sub-category first (more specific)
        for keyword, code in self.SUB_KEYWORDS.items():
            if keyword in desc_normalized:
                # Also find main category
                for cat_keyword, cat_code in self.CATEGORY_KEYWORDS.items():
                    if cat_keyword in desc_normalized:
                        return (cat_code, code)
                return ('MISC', code)

        # Find main category only
        for keyword, code in self.CATEGORY_KEYWORDS.items():
            if keyword in desc_normalized:
                return (code, '')

        # Default based on SEC code
        sec_defaults = {
            'SEC-00': ('PRELIM', ''),
            'SEC-01': ('EARTH', ''),
            'SEC-02': ('STRUC', ''),
            'SEC-03': ('ARCH', ''),
            'SEC-04': ('MEP', ''),
            'SEC-05': ('LAND', ''),
        }

        for sec_prefix, (cat, sub) in sec_defaults.items():
            if sec_code and sec_code.startswith(sec_prefix):
                return (cat, sub)

        return ('MISC', '')

    def get_next_sequence(self, sec_code: str, category: str) -> int:
        """
        Lấy sequence number tiếp theo cho một nhóm
        """
        sec_prefix = self.SEC_PREFIX_MAP.get(sec_code, 'S99')
        pattern = f"{sec_prefix}-{category}-%"

        # Find max sequence in this group
        result = self.db.query(
            func.max(MasterWorkItem.work_code)
        ).filter(
            MasterWorkItem.work_code.like(pattern)
        ).scalar()

        if not result:
            return 1

        # Extract sequence number from code like "S01-EARTH-EXCAV-0025"
        match = re.search(r'-(\d+)$', result)
        if match:
            return int(match.group(1)) + 1

        return 1

    def generate_work_code(
        self,
        description: str,
        sec_code: str,
        unit: str = None,
        include_grade: bool = True
    ) -> str:
        """
        Tạo work code từ description và SEC code

        Args:
            description: Mô tả công tác (Vietnamese)
            sec_code: Mã phân loại SEC
            unit: Đơn vị (optional, để phân biệt thêm)
            include_grade: Có thêm material grade vào code không

        Returns:
            Work code dạng:
            - Không có grade: S01-EARTH-EXCAV-0001
            - Có grade: S02-CONC-M200-0001
        """
        # Get SEC prefix
        sec_prefix = self.SEC_PREFIX_MAP.get(sec_code, 'S99')

        # Extract category and sub-category
        category, sub_category = self.extract_category(description, sec_code)

        # Extract material grade if requested
        material_grade = None
        if include_grade:
            material_grade = self.extract_material_grade(description)

        # Build category part
        parts = [category]

        if material_grade:
            # If has material grade, use it instead of sub-category
            parts.append(material_grade)
        elif sub_category:
            # If no grade but has sub-category, use sub-category
            parts.append(sub_category)

        category_part = '-'.join(parts)

        # Get next sequence number
        sequence = self.get_next_sequence(sec_code, category_part)

        # Generate final code
        work_code = f"{sec_prefix}-{category_part}-{sequence:04d}"

        return work_code

    def validate_work_code(self, work_code: str) -> bool:
        """
        Kiểm tra work code có hợp lệ không

        Valid formats:
        - S01-EARTH-EXCAV-0001 (with sub-category)
        - S01-EARTH-0001 (without sub-category)
        - S02-CONC-M200-0001 (with material grade)
        """
        # Pattern: S{2digits}-{WORD}-({WORD|M\d+}-)?{4digits}
        pattern = r'^S\d{2}-[A-Z]+-(([A-Z]+|M\d{2,3})-)?[0-9]{4}$'
        return bool(re.match(pattern, work_code))

    def parse_work_code(self, work_code: str) -> Dict[str, str]:
        """
        Parse work code thành các components

        Returns:
            {
                'sec_prefix': 'S01',
                'category': 'EARTH',
                'sub_category': 'EXCAV',
                'sequence': '0001'
            }
        """
        if not self.validate_work_code(work_code):
            return None

        parts = work_code.split('-')

        result = {
            'sec_prefix': parts[0],
            'category': parts[1],
            'sequence': parts[-1]
        }

        # Check if has sub-category
        if len(parts) == 4:
            result['sub_category'] = parts[2]
        else:
            result['sub_category'] = None

        return result

    def get_category_description(self, category_code: str) -> str:
        """
        Lấy mô tả của category code
        """
        # Reverse lookup
        for keyword, code in self.CATEGORY_KEYWORDS.items():
            if code == category_code:
                return keyword.title()

        for keyword, code in self.SUB_KEYWORDS.items():
            if code == category_code:
                return keyword.title()

        return category_code

    def regenerate_all_codes(self, dry_run: bool = True) -> Dict:
        """
        Tạo lại tất cả work codes trong database

        Args:
            dry_run: Nếu True, chỉ preview không update

        Returns:
            Statistics
        """
        items = self.db.query(MasterWorkItem).filter(
            MasterWorkItem.is_active == True
        ).order_by(
            MasterWorkItem.sec_code,
            MasterWorkItem.description
        ).all()

        stats = {
            'total': len(items),
            'updated': 0,
            'skipped': 0,
            'previews': []
        }

        # Reset sequence tracking
        sequence_tracker = {}

        for item in items:
            try:
                # Generate new code
                new_code = self.generate_work_code(
                    description=item.description,
                    sec_code=item.sec_code,
                    unit=item.unit_standard
                )

                old_code = item.work_code

                if old_code != new_code:
                    stats['previews'].append({
                        'old': old_code,
                        'new': new_code,
                        'description': item.description[:50]
                    })

                    if not dry_run:
                        item.work_code = new_code
                        stats['updated'] += 1
                else:
                    stats['skipped'] += 1

            except Exception as e:
                print(f"Error processing item {item.master_id}: {e}")
                stats['skipped'] += 1

        if not dry_run:
            self.db.commit()

        return stats


def test_generator():
    """Test function"""
    from app.core.database import SessionLocal

    db = SessionLocal()
    generator = WorkCodeGenerator(db)

    # Test cases
    test_cases = [
        ("Đào đất móng", "SEC-01-01"),
        ("Đắp đất nền", "SEC-01-01"),
        ("Bê tông cột", "SEC-02"),
        ("Bê tông dầm", "SEC-02"),
        ("Tường gạch", "SEC-03"),
        ("Lát gạch nền", "SEC-03"),
        ("Sơn tường", "SEC-03"),
        ("Hệ thống điện", "SEC-04"),
        ("Thang máy", "SEC-04"),
        ("Đường nội bộ", "SEC-05"),
        ("Cây xanh", "SEC-05"),
        ("Hàng rào", "SEC-05"),
    ]

    print("=== TESTING WORK CODE GENERATOR ===\n")

    for desc, sec in test_cases:
        code = generator.generate_work_code(desc, sec)
        parsed = generator.parse_work_code(code)
        print(f"{desc:25} | {sec:12} | {code:25} | Valid: {generator.validate_work_code(code)}")

    db.close()


if __name__ == "__main__":
    test_generator()
