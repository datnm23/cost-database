"""
Legal Code Service - Xử lý mã định mức theo Thông tư 12/2021/TT-BXD
Hỗ trợ tạo, phân tích, và ánh xạ legal codes
"""
import re
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func


class LegalCodeService:
    """
    Service xử lý Legal Codes theo Thông tư 12/2021
    
    Legal Code Format: {PREFIX}{NUMBER}{SUFFIX}
    - PREFIX: 2-3 ký tự (AA, AB, AF, BA, CA, etc.)
    - NUMBER: 3-4 chữ số (1111, 2345)
    - SUFFIX: a, b, +, -, hoặc NULL
    
    Examples:
    - AA.1111: Công tác đất
    - AF.1201a: Bê tông biến thể a
    - BA.5678+: Công tác thiết kế mở rộng
    """
    
    # Prefix mapping theo Thông tư 12/2021
    PREFIX_CATEGORIES = {
        # Phụ lục I - Định mức Xây dựng
        'AA': {
            'name_vn': 'Công tác đất',
            'name_en': 'Earthworks',
            'appendix': 'I',
            'sec_codes': ['SEC-01-01']
        },
        'AB': {
            'name_vn': 'Công tác đào đắp đất bằng máy',
            'name_en': 'Machine earthworks',
            'appendix': 'I',
            'sec_codes': ['SEC-01-01']
        },
        'AC': {
            'name_vn': 'Công tác cọc',
            'name_en': 'Piling works',
            'appendix': 'I',
            'sec_codes': ['SEC-01-02']
        },
        'AD': {
            'name_vn': 'Công tác đá xây',
            'name_en': 'Stone masonry',
            'appendix': 'I',
            'sec_codes': ['SEC-02', 'SEC-03']
        },
        'AE': {
            'name_vn': 'Công tác xây',
            'name_en': 'Brickwork',
            'appendix': 'I',
            'sec_codes': ['SEC-03']
        },
        'AF': {
            'name_vn': 'Công tác bê tông',
            'name_en': 'Concrete works',
            'appendix': 'I',
            'sec_codes': ['SEC-02']
        },
        'AG': {
            'name_vn': 'Công tác cốt thép',
            'name_en': 'Rebar works',
            'appendix': 'I',
            'sec_codes': ['SEC-02']
        },
        'AH': {
            'name_vn': 'Công tác ván khuôn',
            'name_en': 'Formwork',
            'appendix': 'I',
            'sec_codes': ['SEC-02']
        },
        'AI': {
            'name_vn': 'Công tác lắp dựng kết cấu thép',
            'name_en': 'Steel structure installation',
            'appendix': 'I',
            'sec_codes': ['SEC-02']
        },
        'AJ': {
            'name_vn': 'Công tác hoàn thiện',
            'name_en': 'Finishing works',
            'appendix': 'I',
            'sec_codes': ['SEC-03']
        },
        'AK': {
            'name_vn': 'Công tác lợp mái',
            'name_en': 'Roofing works',
            'appendix': 'I',
            'sec_codes': ['SEC-03']
        },
        
        # Phụ lục II - Định mức Thiết kế
        'BA': {
            'name_vn': 'Thiết kế kiến trúc',
            'name_en': 'Architectural design',
            'appendix': 'II',
            'sec_codes': ['SEC-00']
        },
        'BB': {
            'name_vn': 'Thiết kế kết cấu',
            'name_en': 'Structural design',
            'appendix': 'II',
            'sec_codes': ['SEC-00']
        },
        'BC': {
            'name_vn': 'Thiết kế hệ thống MEP',
            'name_en': 'MEP design',
            'appendix': 'II',
            'sec_codes': ['SEC-00']
        },
        
        # Phụ lục III - Định mức Khảo sát
        'CA': {
            'name_vn': 'Khảo sát địa hình',
            'name_en': 'Topographic survey',
            'appendix': 'III',
            'sec_codes': ['SEC-00']
        },
        'CB': {
            'name_vn': 'Khảo sát địa chất',
            'name_en': 'Geological survey',
            'appendix': 'III',
            'sec_codes': ['SEC-00']
        },
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def parse_legal_code(self, legal_code: str) -> Optional[Dict]:
        """
        Phân tích legal code thành các thành phần
        
        Args:
            legal_code: Mã định mức (VD: AA.1111, AF.2345a, BA.5678+)
        
        Returns:
            Dict chứa: prefix, number, suffix, category_info
            hoặc None nếu không hợp lệ
        """
        # Pattern: {2-3 chữ cái}.{3-4 số}{suffix tùy chọn}
        pattern = r'^([A-Z]{2,3})\.(\d{3,4})([a-z+\-]?)$'
        match = re.match(pattern, legal_code.upper())
        
        if not match:
            return None
        
        prefix, number, suffix = match.groups()
        
        category_info = self.PREFIX_CATEGORIES.get(prefix, {
            'name_vn': 'Chưa xác định',
            'name_en': 'Undefined',
            'appendix': 'Unknown',
            'sec_codes': []
        })
        
        return {
            'legal_code': legal_code.upper(),
            'prefix': prefix,
            'number': number,
            'suffix': suffix if suffix else None,
            'category_vn': category_info['name_vn'],
            'category_en': category_info['name_en'],
            'appendix': category_info['appendix'],
            'suggested_sec_codes': category_info['sec_codes']
        }
    
    def validate_legal_code(self, legal_code: str) -> bool:
        """Kiểm tra legal code có hợp lệ không"""
        return self.parse_legal_code(legal_code) is not None
    
    def generate_legal_code_from_description(
        self, 
        description: str,
        sec_code: str = None,
        category_hint: str = None
    ) -> str:
        """
        Đề xuất legal code từ description
        
        Strategy:
        1. Phân tích từ khóa trong description
        2. Map với category
        3. Gợi ý prefix phù hợp
        4. Tạo số sequence
        """
        desc_lower = description.lower()
        
        # Detect prefix based on keywords
        prefix = 'ZZ'  # Default unknown
        
        # Earthworks
        if any(kw in desc_lower for kw in ['đào', 'đắp', 'san', 'nền']):
            if 'máy' in desc_lower:
                prefix = 'AB'
            else:
                prefix = 'AA'
        
        # Piling
        elif any(kw in desc_lower for kw in ['cọc', 'khoan', 'nhồi', 'ép']):
            prefix = 'AC'
        
        # Concrete
        elif any(kw in desc_lower for kw in ['bê tông', 'betong', 'concrete']):
            prefix = 'AF'
        
        # Rebar
        elif any(kw in desc_lower for kw in ['cốt thép', 'thép', 'rebar']):
            prefix = 'AG'
        
        # Formwork
        elif any(kw in desc_lower for kw in ['ván khuôn', 'formwork', 'khuôn']):
            prefix = 'AH'
        
        # Masonry
        elif any(kw in desc_lower for kw in ['xây', 'gạch', 'block', 'brick']):
            prefix = 'AE'
        
        # Steel structure
        elif any(kw in desc_lower for kw in ['lắp dựng', 'kết cấu thép', 'steel']):
            prefix = 'AI'
        
        # Finishing
        elif any(kw in desc_lower for kw in ['trát', 'sơn', 'lát', 'ốp', 'finishing']):
            prefix = 'AJ'
        
        # Roofing
        elif any(kw in desc_lower for kw in ['mái', 'lợp', 'roof']):
            prefix = 'AK'
        
        # Design (if sec_code suggests)
        elif sec_code == 'SEC-00' or 'thiết kế' in desc_lower:
            if 'kiến trúc' in desc_lower:
                prefix = 'BA'
            elif 'kết cấu' in desc_lower:
                prefix = 'BB'
            elif any(kw in desc_lower for kw in ['mep', 'điện', 'nước']):
                prefix = 'BC'
        
        # Survey
        elif 'khảo sát' in desc_lower:
            if 'địa hình' in desc_lower:
                prefix = 'CA'
            elif 'địa chất' in desc_lower:
                prefix = 'CB'
        
        # Generate number (simplified - should query DB for next sequence)
        # For now, use placeholder
        number = '9999'
        
        return f"{prefix}.{number}"
    
    def convert_to_natural_name(
        self,
        official_name: str,
        material_grade: str = None
    ) -> str:
        """
        Chuyển đổi tên định mức chính thức sang tên tự nhiên
        
        Rules (theo tài liệu):
        1. Viết thường vị trí (móng, sàn, tường)
        2. Dùng dấu gạch ngang (-) phân tách
        3. Loại bỏ ký tự toán học (<, >, <=, >=)
        4. Đưa thông số quan trọng lên đầu
        5. Ngắn gọn hơn 30%
        
        Examples:
        - "Bê tông lót móng, chiều rộng <= 250cm, vữa bê tông PC30"
          → "Đổ bê tông lót móng - M100 đá 4x6"
        
        - "Xây tường thẳng, chiều dày > 33cm, gạch 6.5x10.5x22"
          → "Xây tường gạch ống - dày 330mm - vữa M75"
        """
        name = official_name.lower()
        
        # Remove mathematical operators
        name = re.sub(r'[<>=]+', '', name)
        
        # Remove dimension descriptors
        name = re.sub(r'chiều (rộng|dày|cao|sâu)\s*', '', name)
        
        # Simplify "vữa bê tông" to grade
        if material_grade:
            name = re.sub(r'vữa bê tông \w+', material_grade, name)
        
        # Remove excessive commas
        name = re.sub(r'\s*,\s*', ' - ', name)
        
        # Capitalize first word (action verb)
        parts = name.split(' - ')
        if parts:
            parts[0] = parts[0].capitalize()
        
        return ' - '.join(parts)
    
    def search_legal_codes(
        self,
        query: str = None,
        prefix: str = None,
        appendix: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Tìm kiếm legal codes
        
        Args:
            query: Tìm theo tên
            prefix: Filter theo prefix (AA, AF, etc.)
            appendix: Filter theo phụ lục (I, II, III)
            limit: Số kết quả
        """
        # This would query the legal_work_codes table
        # Placeholder implementation
        results = []
        
        for code_prefix, info in self.PREFIX_CATEGORIES.items():
            if prefix and code_prefix != prefix:
                continue
            if appendix and info['appendix'] != appendix:
                continue
            
            results.append({
                'prefix': code_prefix,
                'category_vn': info['name_vn'],
                'category_en': info['name_en'],
                'appendix': info['appendix'],
                'sec_codes': info['sec_codes']
            })
        
        return results[:limit]
    
    def get_prefix_statistics(self) -> Dict:
        """
        Thống kê legal codes theo prefix
        
        Returns:
            {
                'AA': {'count': 150, 'name': 'Công tác đất'},
                'AF': {'count': 320, 'name': 'Công tác bê tông'},
                ...
            }
        """
        # Would query database
        # Placeholder
        stats = {}
        for prefix, info in self.PREFIX_CATEGORIES.items():
            stats[prefix] = {
                'name_vn': info['name_vn'],
                'name_en': info['name_en'],
                'appendix': info['appendix'],
                'count': 0  # Would count from DB
            }
        return stats
    
    def suggest_suffix(
        self,
        base_code: str,
        variation_type: str
    ) -> str:
        """
        Đề xuất suffix cho biến thể
        
        Args:
            base_code: Mã gốc (VD: AA.1111)
            variation_type: Loại biến thể
                - 'variant': Biến thể kỹ thuật → a, b, c
                - 'extended': Mở rộng → +
                - 'reduced': Thu gọn → -
        """
        if variation_type == 'variant':
            # Check existing variants in DB
            # Return next letter (a, b, c, ...)
            return base_code + 'a'
        elif variation_type == 'extended':
            return base_code + '+'
        elif variation_type == 'reduced':
            return base_code + '-'
        
        return base_code


def test_legal_code_service():
    """Test function"""
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    service = LegalCodeService(db)
    
    print("=== LEGAL CODE SERVICE TEST ===\n")
    
    # Test parsing
    test_codes = [
        "AA.1111",
        "AF.2345a",
        "BA.5678+",
        "CA.1001-",
        "INVALID.123",
    ]
    
    print("1. Parsing Legal Codes:")
    for code in test_codes:
        result = service.parse_legal_code(code)
        if result:
            print(f"✓ {code:15} → {result['category_vn']:30} (Phụ lục {result['appendix']})")
        else:
            print(f"✗ {code:15} → INVALID")
    
    print("\n2. Generate from Description:")
    descriptions = [
        "Đào đất hố móng bằng máy",
        "Đổ bê tông dầm",
        "Gia công cốt thép",
        "Xây tường gạch",
        "Thiết kế kiến trúc",
    ]
    
    for desc in descriptions:
        code = service.generate_legal_code_from_description(desc)
        print(f"{desc:40} → {code}")
    
    print("\n3. Convert to Natural Name:")
    official_names = [
        "Bê tông lót móng, chiều rộng <= 250cm, vữa bê tông PC30",
        "Xây tường thẳng, chiều dày > 33cm, gạch 6.5x10.5x22",
    ]
    
    for name in official_names:
        natural = service.convert_to_natural_name(name, "M100")
        print(f"Official: {name}")
        print(f"Natural:  {natural}\n")
    
    db.close()


if __name__ == "__main__":
    test_legal_code_service()
