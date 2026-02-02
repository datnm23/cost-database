"""
ISO Classification Service - ISO 12006-2
Hỗ trợ phân loại công tác theo tiêu chuẩn quốc tế
"""
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session


class ISOClassificationService:
    """
    Service xử lý ISO 12006-2 Classification
    
    ISO Code Format: {ENTITY}_{SYSTEM}_{ELEMENT}_{PRODUCT}
    
    Entities (Facets):
    - Ss: Spaces (Không gian)
    - Pr: Processes/Activities (Công việc)
    - El: Elements (Bộ phận)
    - Ac: Agents (Tác nhân)
    - Re: Resources (Tài nguyên)
    
    Example: Pr_21_31_13
    - Pr: Process (Công việc)
    - 21: Wall system (Hệ thống tường)
    - 31: Concrete (Bê tông)
    - 13: Grade M200 (Mác 200)
    """
    
    # Entity types (Facet 1)
    ENTITIES = {
        'Ss': {
            'name_vn': 'Không gian',
            'name_en': 'Spaces',
            'description': 'Phân loại theo không gian vật lý'
        },
        'Pr': {
            'name_vn': 'Công việc/Hoạt động',
            'name_en': 'Processes/Activities',
            'description': 'Phân loại theo công tác thực hiện'
        },
        'El': {
            'name_vn': 'Bộ phận/Cấu kiện',
            'name_en': 'Elements/Components',
            'description': 'Phân loại theo bộ phận kết cấu'
        },
        'Pr': {
            'name_vn': 'Sản phẩm',
            'name_en': 'Products',
            'description': 'Phân loại theo sản phẩm/vật liệu'
        },
        'Ac': {
            'name_vn': 'Tác nhân',
            'name_en': 'Agents',
            'description': 'Phân loại theo người/tổ chức thực hiện'
        },
    }
    
    # System codes (Facet 2) - Simplified
    SYSTEMS = {
        # Substructure (01-19)
        '01': {'name_vn': 'Móng', 'name_en': 'Foundations', 'sec': 'SEC-01-03'},
        '02': {'name_vn': 'Cọc', 'name_en': 'Piles', 'sec': 'SEC-01-02'},
        '03': {'name_vn': 'Tầng hầm', 'name_en': 'Basement', 'sec': 'SEC-01'},
        
        # Superstructure (20-29)
        '20': {'name_vn': 'Khung kết cấu', 'name_en': 'Structural frame', 'sec': 'SEC-02'},
        '21': {'name_vn': 'Hệ thống tường', 'name_en': 'Wall systems', 'sec': 'SEC-02'},
        '22': {'name_vn': 'Hệ thống sàn', 'name_en': 'Floor systems', 'sec': 'SEC-02'},
        '23': {'name_vn': 'Hệ thống cột', 'name_en': 'Column systems', 'sec': 'SEC-02'},
        '24': {'name_vn': 'Hệ thống dầm', 'name_en': 'Beam systems', 'sec': 'SEC-02'},
        '25': {'name_vn': 'Hệ thống mái', 'name_en': 'Roof systems', 'sec': 'SEC-02'},
        
        # Finishes (30-39)
        '30': {'name_vn': 'Hoàn thiện tường', 'name_en': 'Wall finishes', 'sec': 'SEC-03'},
        '31': {'name_vn': 'Hoàn thiện sàn', 'name_en': 'Floor finishes', 'sec': 'SEC-03'},
        '32': {'name_vn': 'Hoàn thiện trần', 'name_en': 'Ceiling finishes', 'sec': 'SEC-03'},
        
        # MEP (40-59)
        '40': {'name_vn': 'Hệ thống điện', 'name_en': 'Electrical', 'sec': 'SEC-04'},
        '41': {'name_vn': 'Hệ thống nước', 'name_en': 'Plumbing', 'sec': 'SEC-04'},
        '42': {'name_vn': 'HVAC', 'name_en': 'HVAC', 'sec': 'SEC-04'},
        '43': {'name_vn': 'PCCC', 'name_en': 'Fire protection', 'sec': 'SEC-04'},
        '44': {'name_vn': 'Thang máy', 'name_en': 'Elevators', 'sec': 'SEC-04'},
        
        # External (60-69)
        '60': {'name_vn': 'Cảnh quan', 'name_en': 'Landscape', 'sec': 'SEC-05'},
        '61': {'name_vn': 'Đường nội bộ', 'name_en': 'Internal roads', 'sec': 'SEC-05'},
        '62': {'name_vn': 'Hàng rào', 'name_en': 'Fencing', 'sec': 'SEC-05'},
    }
    
    # Element codes (Facet 3)
    ELEMENTS = {
        # Materials
        '10': {'name_vn': 'Đất đá', 'name_en': 'Soil/Rock'},
        '20': {'name_vn': 'Kim loại', 'name_en': 'Metals'},
        '21': {'name_vn': 'Thép', 'name_en': 'Steel'},
        '30': {'name_vn': 'Bê tông', 'name_en': 'Concrete'},
        '31': {'name_vn': 'Bê tông thương phẩm', 'name_en': 'Ready-mix concrete'},
        '32': {'name_vn': 'Bê tông đổ tại chỗ', 'name_en': 'In-situ concrete'},
        '40': {'name_vn': 'Gạch', 'name_en': 'Bricks'},
        '41': {'name_vn': 'Gạch ống', 'name_en': 'Hollow bricks'},
        '42': {'name_vn': 'Gạch đặc', 'name_en': 'Solid bricks'},
        '50': {'name_vn': 'Vật liệu hoàn thiện', 'name_en': 'Finishing materials'},
        '51': {'name_vn': 'Sơn', 'name_en': 'Paint'},
        '52': {'name_vn': 'Gạch ốp lát', 'name_en': 'Tiles'},
    }
    
    # Product codes (Facet 4) - Grades/Specifications
    PRODUCTS = {
        # Concrete grades
        '10': {'name_vn': 'Mác 100', 'name_en': 'Grade M100'},
        '15': {'name_vn': 'Mác 150', 'name_en': 'Grade M150'},
        '20': {'name_vn': 'Mác 200', 'name_en': 'Grade M200'},
        '25': {'name_vn': 'Mác 250', 'name_en': 'Grade M250'},
        '30': {'name_vn': 'Mác 300', 'name_en': 'Grade M300'},
        '35': {'name_vn': 'Mác 350', 'name_en': 'Grade M350'},
        '40': {'name_vn': 'Mác 400', 'name_en': 'Grade M400'},
        
        # Steel grades
        '50': {'name_vn': 'CB300', 'name_en': 'CB300'},
        '51': {'name_vn': 'CB400', 'name_en': 'CB400'},
        '52': {'name_vn': 'CB500', 'name_en': 'CB500'},
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def parse_iso_code(self, iso_code: str) -> Optional[Dict]:
        """
        Phân tích ISO code thành các thành phần
        
        Args:
            iso_code: Mã ISO (VD: Pr_21_31_13)
        
        Returns:
            Dict chứa thông tin từng level
        """
        parts = iso_code.split('_')
        
        if len(parts) < 2 or len(parts) > 4:
            return None
        
        result = {
            'iso_code': iso_code,
            'entity': parts[0] if len(parts) >= 1 else None,
            'system': parts[1] if len(parts) >= 2 else None,
            'element': parts[2] if len(parts) >= 3 else None,
            'product': parts[3] if len(parts) >= 4 else None,
            'level': len(parts)
        }
        
        # Lookup names
        if result['entity']:
            entity_info = self.ENTITIES.get(result['entity'], {})
            result['entity_name_vn'] = entity_info.get('name_vn')
            result['entity_name_en'] = entity_info.get('name_en')
        
        if result['system']:
            system_info = self.SYSTEMS.get(result['system'], {})
            result['system_name_vn'] = system_info.get('name_vn')
            result['system_name_en'] = system_info.get('name_en')
            result['suggested_sec'] = system_info.get('sec')
        
        if result['element']:
            element_info = self.ELEMENTS.get(result['element'], {})
            result['element_name_vn'] = element_info.get('name_vn')
            result['element_name_en'] = element_info.get('name_en')
        
        if result['product']:
            product_info = self.PRODUCTS.get(result['product'], {})
            result['product_name_vn'] = product_info.get('name_vn')
            result['product_name_en'] = product_info.get('name_en')
        
        return result
    
    def generate_iso_code(
        self,
        description: str,
        sec_code: str = None,
        legal_code: str = None,
        material_grade: str = None
    ) -> str:
        """
        Tạo ISO code từ description
        
        Strategy:
        1. Xác định entity (thường là 'Pr' - Process)
        2. Map system từ SEC code hoặc keywords
        3. Xác định element (material type)
        4. Xác định product (grade/spec)
        """
        desc_lower = description.lower()
        
        # Default entity is Process
        entity = 'Pr'
        
        # Detect system
        system = '99'  # Default unknown
        
        # Foundation/Substructure
        if any(kw in desc_lower for kw in ['móng', 'foundation']):
            system = '01'
        elif any(kw in desc_lower for kw in ['cọc', 'pile']):
            system = '02'
        
        # Superstructure
        elif any(kw in desc_lower for kw in ['tường', 'wall']):
            system = '21'
        elif any(kw in desc_lower for kw in ['sàn', 'floor', 'slab']):
            system = '22'
        elif any(kw in desc_lower for kw in ['cột', 'column']):
            system = '23'
        elif any(kw in desc_lower for kw in ['dầm', 'beam']):
            system = '24'
        elif any(kw in desc_lower for kw in ['mái', 'roof']):
            system = '25'
        
        # Finishes
        elif 'hoàn thiện' in desc_lower or 'finishing' in desc_lower:
            if 'tường' in desc_lower:
                system = '30'
            elif 'sàn' in desc_lower:
                system = '31'
            elif 'trần' in desc_lower:
                system = '32'
        
        # MEP
        elif any(kw in desc_lower for kw in ['điện', 'electrical']):
            system = '40'
        elif any(kw in desc_lower for kw in ['nước', 'plumbing', 'water']):
            system = '41'
        elif 'hvac' in desc_lower or 'điều hòa' in desc_lower:
            system = '42'
        
        # External
        elif any(kw in desc_lower for kw in ['cảnh quan', 'landscape']):
            system = '60'
        elif any(kw in desc_lower for kw in ['đường', 'road']):
            system = '61'
        
        # Detect element (material)
        element = None
        
        if any(kw in desc_lower for kw in ['bê tông', 'concrete']):
            if 'thương phẩm' in desc_lower or 'ready-mix' in desc_lower:
                element = '31'
            elif 'tại chỗ' in desc_lower or 'in-situ' in desc_lower:
                element = '32'
            else:
                element = '30'
        elif any(kw in desc_lower for kw in ['thép', 'steel', 'cốt thép']):
            element = '21'
        elif any(kw in desc_lower for kw in ['gạch', 'brick']):
            if 'ống' in desc_lower or 'hollow' in desc_lower:
                element = '41'
            elif 'đặc' in desc_lower or 'solid' in desc_lower:
                element = '42'
            else:
                element = '40'
        elif any(kw in desc_lower for kw in ['sơn', 'paint']):
            element = '51'
        elif any(kw in desc_lower for kw in ['gạch lát', 'gạch ốp', 'tile']):
            element = '52'
        
        # Detect product (grade)
        product = None
        
        if material_grade:
            # Map grade to code
            grade_map = {
                'M100': '10', 'M150': '15', 'M200': '20',
                'M250': '25', 'M300': '30', 'M350': '35',
                'M400': '40',
                'CB300': '50', 'CB400': '51', 'CB500': '52'
            }
            product = grade_map.get(material_grade.upper())
        
        # Build ISO code
        parts = [entity, system]
        if element:
            parts.append(element)
        if product:
            parts.append(product)
        
        return '_'.join(parts)
    
    def get_hierarchy_path(self, iso_code: str) -> List[Dict]:
        """
        Lấy đường dẫn phân cấp của ISO code
        
        Returns:
            List các level từ cao đến thấp
        """
        parsed = self.parse_iso_code(iso_code)
        if not parsed:
            return []
        
        path = []
        
        # Level 1: Entity
        if parsed.get('entity'):
            path.append({
                'level': 1,
                'code': parsed['entity'],
                'name_vn': parsed.get('entity_name_vn'),
                'name_en': parsed.get('entity_name_en')
            })
        
        # Level 2: System
        if parsed.get('system'):
            path.append({
                'level': 2,
                'code': f"{parsed['entity']}_{parsed['system']}",
                'name_vn': parsed.get('system_name_vn'),
                'name_en': parsed.get('system_name_en')
            })
        
        # Level 3: Element
        if parsed.get('element'):
            path.append({
                'level': 3,
                'code': f"{parsed['entity']}_{parsed['system']}_{parsed['element']}",
                'name_vn': parsed.get('element_name_vn'),
                'name_en': parsed.get('element_name_en')
            })
        
        # Level 4: Product
        if parsed.get('product'):
            path.append({
                'level': 4,
                'code': iso_code,
                'name_vn': parsed.get('product_name_vn'),
                'name_en': parsed.get('product_name_en')
            })
        
        return path
    
    def search_iso_codes(
        self,
        entity: str = None,
        system: str = None,
        element: str = None,
        query: str = None
    ) -> List[Dict]:
        """
        Tìm kiếm ISO codes
        """
        results = []
        
        # Would query database
        # Placeholder
        
        return results


def test_iso_service():
    """Test function"""
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    service = ISOClassificationService(db)
    
    print("=== ISO CLASSIFICATION SERVICE TEST ===\n")
    
    # Test parsing
    test_codes = [
        "Pr_21",
        "Pr_21_31",
        "Pr_21_31_20",
        "El_22_30",
    ]
    
    print("1. Parsing ISO Codes:")
    for code in test_codes:
        result = service.parse_iso_code(code)
        if result:
            print(f"✓ {code:20} → Level {result['level']}")
            if result.get('system_name_vn'):
                print(f"  System: {result['system_name_vn']}")
            if result.get('element_name_vn'):
                print(f"  Element: {result['element_name_vn']}")
            if result.get('product_name_vn'):
                print(f"  Product: {result['product_name_vn']}")
        print()
    
    print("\n2. Generate from Description:")
    test_items = [
        ("Đổ bê tông dầm", None, "M200"),
        ("Xây tường gạch ống", None, None),
        ("Lát gạch sàn", None, None),
        ("Lắp đặt hệ thống điện", None, None),
    ]
    
    for desc, sec, grade in test_items:
        code = service.generate_iso_code(desc, sec, None, grade)
        print(f"{desc:40} → {code}")
    
    print("\n3. Hierarchy Path:")
    code = "Pr_21_31_20"
    path = service.get_hierarchy_path(code)
    for item in path:
        indent = "  " * (item['level'] - 1)
        print(f"{indent}L{item['level']}: {item['code']:20} - {item['name_vn']}")
    
    db.close()


if __name__ == "__main__":
    test_iso_service()
