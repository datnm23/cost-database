"""
Enhanced Naming Template Service
Tích hợp quy chuẩn 4-part syntax vào Natural Name generation
"""
import re
from typing import Dict, List, Optional
from sqlalchemy.orm import Session


class EnhancedNamingService:
    """
    Service tạo tên công tác theo quy chuẩn 4-part syntax:
    [Động từ + Đối tượng][Môi trường] - [Định tính] - [Định lượng] - [Đặc tính]
    """
    
    # Từ điển động từ chuẩn (EXPANDED)
    STANDARD_VERBS = {
        # Earthworks & Foundation
        'excavate': 'Đào', 'backfill': 'Đắp', 'compact': 'Đầm', 'level': 'San',
        'grade': 'San nền', 'remove': 'Dọn', 'transport': 'Vận chuyển',
        
        # Piling
        'drive': 'Ép', 'drill': 'Khoan', 'bore': 'Khoan', 'auger': 'Khoan xoắn',
        'install_pile': 'Thi công cọc', 'extract': 'Nhổ cọc',
        
        # Concrete & Formwork
        'cast': 'Đổ', 'pour': 'Đổ', 'place': 'Đổ', 'pump': 'Bơm bê tông',
        'vibrate': 'Đầm bê tông', 'cure': 'Dưỡng hộ',
        'erect_formwork': 'Lắp ván khuôn', 'strip_formwork': 'Tháo ván khuôn',
        
        # Rebar & Steel
        'fabricate': 'Gia công', 'bend': 'Uốn thép', 'tie': 'Buộc thép',
        'weld': 'Hàn', 'bolt': 'Bắt bu lông', 'erect': 'Dựng',
        
        # Masonry
        'build': 'Xây', 'lay_brick': 'Xây gạch', 'lay_block': 'Xây block',
        'point': 'Chít mạch', 'grout': 'Trét vữa',
        
        # Finishing - Floor
        'lay': 'Lát', 'tile': 'Lát gạch', 'pave': 'Thảm', 'screed': 'Chà nhám',
        'polish': 'Đánh bóng', 'seal': 'Phủ bóng', 'waterproof': 'Chống thấm',
        
        # Finishing - Wall
        'coat': 'Ốp', 'clad': 'Ốp', 'plaster': 'Trát', 'render': 'Trát',
        'skim': 'Trát nhẵn', 'paint': 'Sơn', 'spray': 'Phun sơn',
        
        # Finishing - Ceiling
        'install_ceiling': 'Làm trần', 'suspend': 'Treo trần', 
        
        # Doors & Windows
        'install': 'Lắp', 'hang': 'Treo', 'fix': 'Lắp', 'glaze': 'Lắp kính',
        'seal_joint': 'Chống thấm mối nối',
        
        # MEP - Piping
        'lay_pipe': 'Lắp ống', 'route_pipe': 'Rải ống', 'connect': 'Nối',
        'thread': 'Ren ống', 'solder': 'Hàn thiếc', 'flange': 'Mặt bích',
        
        # MEP - Electrical
        'pull': 'Kéo', 'lay_cable': 'Rải', 'route': 'Rải', 'terminate': 'Ép cos',
        'wire': 'Đấu dây', 'crimp': 'Ép cáp', 'splice': 'Nối cáp',
        
        # MEP - Equipment
        'mount': 'Lắp', 'install_equip': 'Lắp đặt', 'position': 'Bố trí',
        'anchor': 'Neo', 'suspend_equip': 'Treo', 'support': 'Đỡ',
        
        # MEP - Ducting & Insulation
        'install_duct': 'Lắp ống gió', 'fabricate_duct': 'Chế tạo ống gió',
        'insulate': 'Bảo ôn', 'wrap': 'Bọc cách nhiệt',
        
        # Infrastructure
        'pave_road': 'Thảm', 'spread': 'Rải', 'roll': 'Lu', 
        'mark': 'Kẻ vạch', 'drain': 'Thoát nước',
        
        # Landscape
        'plant': 'Trồng', 'sod': 'Trải cỏ', 'irrigate': 'Tưới',
        
        # Testing & Commissioning
        'test': 'Chạy thử', 'commission': 'Nghiệm thu', 'calibrate': 'Hiệu chuẩn',
        'train': 'Đào tạo', 'document': 'Lập hồ sơ', 'handover': 'Bàn giao',
        
        # Demolition & Removal
        'demolish': 'Phá dỡ', 'break': 'Đập', 'cut': 'Cắt', 'saw': 'Cưa',
        'dismantle': 'Tháo dỡ', 'strip': 'Bóc', 'clean': 'Dọn dẹp'
    }
    
    # Từ điển vị trí/môi trường chuẩn
    STANDARD_LOCATIONS = {
        # Structural
        'foundation': 'móng', 'pile': 'cọc', 'column': 'cột',
        'beam': 'dầm', 'slab': 'sàn', 'wall': 'tường', 'roof': 'mái',
        
        # MEP environments
        'underground': 'ngầm', 'in_wall': 'âm tường', 'in_slab': 'âm sàn',
        'above_ceiling': 'treo trần', 'vertical_shaft': 'trục đứng',
        'exposed': 'lộ thiên',
        
        # Zones
        'external': 'ngoài', 'internal': 'trong', 'basement': 'tầng hầm'
    }
    
    # Template patterns theo nhóm công tác
    TEMPLATES = {
        # SEC-01: Earthworks & Piling
        'SEC-01-01': {
            'pattern': '{verb} {material} {location} - {method} - {classification}',
            'example': 'Đào đất hố móng - Máy đào 0.8m3 - Đất cấp 3',
            'required': ['verb', 'material', 'location'],
            'optional': ['method', 'classification']
        },
        
        # SEC-02: Concrete & Structure
        'SEC-02': {
            'pattern': '{verb} {material} {element} - {grade} - {aggregate}',
            'example': 'Đổ bê tông dầm sàn - M350 - Đá 1x2',
            'required': ['verb', 'material', 'element', 'grade'],
            'optional': ['aggregate', 'slump']
        },
        
        # SEC-03: Architecture
        'SEC-03': {
            'pattern': '{verb} {element} {location} - {material_type} - {dimension}',
            'example': 'Xây tường ngoài - Gạch đặc - Dày 220',
            'required': ['verb', 'element', 'material_type'],
            'optional': ['location', 'dimension']
        },
        
        # SEC-04: MEP (Chi tiết nhất)
        'SEC-04': {
            'water': {
                'pattern': '{verb} {pipe_type} {environment} - {material} - {diameter} - {pressure}',
                'example': 'Lắp ống cấp nước trục đứng - PPR - D63 - PN16',
                'required': ['verb', 'pipe_type', 'material', 'diameter'],
                'optional': ['environment', 'pressure']
            },
            'electrical': {
                'pattern': '{verb} {cable_type} {environment} - {conductor} - {size}',
                'example': 'Rải dây cáp điện ngầm - Cu/XLPE/PVC - 4x50',
                'required': ['verb', 'cable_type', 'conductor', 'size'],
                'optional': ['environment']
            },
            'hvac': {
                'pattern': '{verb} {duct_type} {system} - {material} - {dimension} - {thickness}',
                'example': 'Lắp ống gió cấp - Tôn tráng kẽm - 1200x400 - 0.75mm',
                'required': ['verb', 'duct_type', 'material', 'dimension'],
                'optional': ['system', 'thickness']
            }
        }
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def detect_verb(self, description: str) -> Optional[str]:
        """
        Phát hiện động từ từ description
        """
        desc_lower = description.lower()
        
        # Priority order (specific first)
        verb_patterns = [
            ('chạy thử', 'test'),
            ('đào tạo', 'train'),
            ('lập hồ sơ', 'document'),
            ('ép cọc', 'drive'),
            ('khoan cọc', 'drill'),
            ('đổ bê tông', 'cast'),
            ('xây tường', 'build'),
            ('lát gạch', 'tile'),
            ('ốp', 'coat'),
            ('sơn', 'paint'),
            ('trát', 'plaster'),
            ('lắp', 'install'),
            ('kéo dây', 'pull'),
            ('rải', 'lay_cable'),
            ('thảm', 'pave'),
            ('đào', 'excavate'),
            ('đắp', 'backfill'),
        ]
        
        for vn_verb, en_key in verb_patterns:
            if vn_verb in desc_lower:
                return self.STANDARD_VERBS[en_key]
        
        return None
    
    def detect_location(self, description: str) -> Optional[str]:
        """
        Phát hiện vị trí/môi trường từ description
        """
        desc_lower = description.lower()
        
        location_patterns = [
            ('treo trần', 'above_ceiling'),
            ('âm tường', 'in_wall'),
            ('âm sàn', 'in_slab'),
            ('trục đứng', 'vertical_shaft'),
            ('lộ thiên', 'exposed'),
            ('ngầm', 'underground'),
            ('móng', 'foundation'),
            ('cọc', 'pile'),
            ('dầm', 'beam'),
            ('sàn', 'slab'),
            ('cột', 'column'),
            ('tường', 'wall'),
            ('mái', 'roof'),
        ]
        
        for vn_loc, en_key in location_patterns:
            if vn_loc in desc_lower:
                return self.STANDARD_LOCATIONS[en_key]
        
        return None
    
    def build_material_spec_json(
        self,
        material: str = None,
        diameter: str = None,
        pressure: str = None,
        conductor: str = None,
        size: str = None,
        dimension: str = None,
        thickness: str = None,
        **kwargs
    ) -> dict:
        """
        Tạo material_spec JSON object chuẩn
        
        Returns:
            JSON object để lưu vào database
        """
        spec = {}
        
        if material:
            spec['material'] = material
        if diameter:
            spec['diameter'] = diameter
        if pressure:
            spec['pressure'] = pressure
        if conductor:
            spec['conductor'] = conductor
        if size:
            spec['size'] = size
        if dimension:
            spec['dimension'] = dimension
        if thickness:
            spec['thickness'] = thickness
        
        # Additional specs from kwargs
        for key, value in kwargs.items():
            if value is not None:
                spec[key] = value
        
        return spec
    
    def extract_mep_specs(self, description: str) -> Dict[str, str]:
        """
        Trích xuất specs MEP chi tiết (PPR, D63, PN16)
        
        Returns:
            {
                'material': 'PPR',
                'diameter': 'D63',
                'pressure': 'PN16',
                'conductor': 'Cu/XLPE/PVC',
                'size': '4x50'
            }
        """
        specs = {}
        desc = description.upper()
        
        # Pipe material
        pipe_materials = ['PPR', 'UPVC', 'HDPE', 'CPVC', 'PEX']
        for mat in pipe_materials:
            if mat in desc:
                specs['material'] = mat
                break
        
        # Diameter (D50, DN100, etc.)
        diameter_match = re.search(r'(D|DN)(\d+)', desc)
        if diameter_match:
            specs['diameter'] = diameter_match.group(0)
        
        # Pressure rating (PN10, PN16, etc.)
        pressure_match = re.search(r'PN(\d+)', desc)
        if pressure_match:
            specs['pressure'] = pressure_match.group(0)
        
        # Conductor type (Cu/XLPE/PVC)
        if 'CU/' in desc or 'XLPE' in desc:
            # Extract full conductor spec
            conductor_match = re.search(r'(CU|AL)/[A-Z/]+', desc)
            if conductor_match:
                specs['conductor'] = conductor_match.group(0)
        
        # Cable size (4x50, 3x2.5, etc.)
        size_match = re.search(r'(\d+X\d+\.?\d*)', desc)
        if size_match:
            specs['size'] = size_match.group(0)
        
        # Duct dimension (1200x400)
        duct_match = re.search(r'(\d{3,4}X\d{3,4})', desc)
        if duct_match:
            specs['dimension'] = duct_match.group(0)
        
        # Thickness (0.75mm, Dày 220)
        thickness_match = re.search(r'(DÀY|THICKNESS)\s*(\d+\.?\d*)\s*(MM)?', desc)
        if thickness_match:
            specs['thickness'] = thickness_match.group(2) + 'mm'
        
        return specs
    
    def generate_natural_name(
        self,
        description: str,
        sec_code: str,
        material_grade: str = None,
        **kwargs
    ) -> str:
        """
        Tạo tên tự nhiên theo quy chuẩn 4-part syntax
        
        Args:
            description: Mô tả gốc
            sec_code: Mã SEC (để chọn template)
            material_grade: M200, CB300, etc.
            **kwargs: Các thông số bổ sung
        
        Returns:
            Tên tự nhiên chuẩn hóa
        """
        # Detect components
        verb = self.detect_verb(description) or kwargs.get('verb', '')
        location = self.detect_location(description) or kwargs.get('location', '')
        mep_specs = self.extract_mep_specs(description)
        
        # Get template for SEC code
        template = self.TEMPLATES.get(sec_code, {})
        
        # Build parts
        parts = []
        
        # Part 1: Verb + Object + Location
        part1_components = [verb] if verb else []
        
        # Add object (extracted from description)
        if 'bê tông' in description.lower():
            part1_components.append('bê tông')
        elif 'ống' in description.lower():
            part1_components.append('ống')
        elif 'dây' in description.lower() or 'cáp' in description.lower():
            part1_components.append('dây cáp')
        elif 'tường' in description.lower():
            part1_components.append('tường')
        elif 'gạch' in description.lower():
            part1_components.append('gạch')
        
        if location:
            part1_components.append(location)
        
        part1 = ' '.join(part1_components)
        if part1:
            parts.append(part1)
        
        # Part 2: Định tính (Material type)
        if mep_specs.get('material'):
            parts.append(mep_specs['material'])
        elif mep_specs.get('conductor'):
            parts.append(mep_specs['conductor'])
        elif 'gạch đặc' in description.lower():
            parts.append('Gạch đặc')
        elif 'gạch ống' in description.lower():
            parts.append('Gạch ống')
        
        # Part 3: Định lượng (Size/Dimension)
        if mep_specs.get('diameter'):
            parts.append(mep_specs['diameter'])
        elif mep_specs.get('dimension'):
            parts.append(mep_specs['dimension'])
        elif mep_specs.get('size'):
            parts.append(mep_specs['size'])
        elif mep_specs.get('thickness'):
            parts.append(f"Dày {mep_specs['thickness']}")
        elif material_grade:
            parts.append(material_grade)
        
        # Part 4: Đặc tính (Specs)
        if mep_specs.get('pressure'):
            parts.append(mep_specs['pressure'])
        
        # Join with dash separator
        natural_name = ' - '.join(parts)
        
        # Fallback: if no parts extracted, clean up original
        if not natural_name.strip():
            natural_name = self._clean_description(description)
        
        return natural_name
    
    def _clean_description(self, description: str) -> str:
        """
        Làm sạch description gốc theo 6 nguyên tắc
        """
        name = description.lower()
        
        # 1. Remove mathematical operators
        name = re.sub(r'[<>=]+', '', name)
        
        # 2. Remove dimension descriptors
        name = re.sub(r'chiều (rộng|dày|cao|sâu)\s*', '', name)
        
        # 3. Replace commas with dashes
        name = re.sub(r'\s*,\s*', ' - ', name)
        
        # 4. Remove extra spaces
        name = ' '.join(name.split())
        
        # 5. Capitalize first word (verb)
        parts = name.split(' - ')
        if parts:
            words = parts[0].split()
            if words:
                words[0] = words[0].capitalize()
                parts[0] = ' '.join(words)
        
        return ' - '.join(parts)
    
    def validate_natural_name(self, name: str) -> Dict[str, any]:
        """
        Validate tên tự nhiên theo quy chuẩn
        
        Returns:
            {
                'is_valid': bool,
                'has_verb': bool,
                'has_specs': bool,
                'length': int,
                'issues': List[str]
            }
        """
        issues = []
        parts = name.split(' - ')
        
        # Check verb
        has_verb = False
        for vn_verb in self.STANDARD_VERBS.values():
            if vn_verb in name:
                has_verb = True
                break
        
        if not has_verb:
            issues.append('Thiếu động từ chuẩn (Đào, Lắp, Rải, etc.)')
        
        # Check length (40-80 chars optimal)
        length = len(name)
        if length < 20:
            issues.append(f'Tên quá ngắn ({length} ký tự < 20)')
        elif length > 100:
            issues.append(f'Tên quá dài ({length} ký tự > 100)')
        
        # Check structure (should have 2-4 parts)
        if len(parts) < 2:
            issues.append('Thiếu phân tách bằng dấu gạch ngang (-)')
        
        # Check specs
        has_specs = any([
            re.search(r'D\d+', name),  # Diameter
            re.search(r'M\d+', name),  # Grade
            re.search(r'\d+x\d+', name),  # Dimension
            re.search(r'PN\d+', name),  # Pressure
        ])
        
        return {
            'is_valid': len(issues) == 0,
            'has_verb': has_verb,
            'has_specs': has_specs,
            'length': length,
            'parts_count': len(parts),
            'issues': issues
        }


def test_enhanced_naming():
    """Test function"""
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    service = EnhancedNamingService(db)
    
    test_cases = [
        {
            'desc': 'Đào đất hố móng bằng máy, sâu <= 1.25m, đất cấp 3',
            'sec': 'SEC-01-01',
            'grade': None
        },
        {
            'desc': 'Lắp ống cấp nước trục đứng PPR D63 PN16',
            'sec': 'SEC-04',
            'grade': None
        },
        {
            'desc': 'Rải dây cáp điện ngầm Cu/XLPE/PVC 4x50',
            'sec': 'SEC-04',
            'grade': None
        },
        {
            'desc': 'Xây tường ngoài gạch đặc dày 220mm',
            'sec': 'SEC-03',
            'grade': None
        },
        {
            'desc': 'Đổ bê tông dầm sàn M350 đá 1x2',
            'sec': 'SEC-02',
            'grade': 'M350'
        },
    ]
    
    print("=== ENHANCED NAMING SERVICE TEST ===\n")
    
    for idx, case in enumerate(test_cases, 1):
        print(f"Test {idx}:")
        print(f"  Original: {case['desc']}")
        
        natural = service.generate_natural_name(
            case['desc'],
            case['sec'],
            case['grade']
        )
        print(f"  Natural:  {natural}")
        
        validation = service.validate_natural_name(natural)
        print(f"  Valid:    {validation['is_valid']}")
        if validation['issues']:
            print(f"  Issues:   {', '.join(validation['issues'])}")
        print()
    
    db.close()


if __name__ == "__main__":
    test_enhanced_naming()
