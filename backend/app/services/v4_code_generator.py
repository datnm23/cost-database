"""
V4 Code Generator — 3-Level Format

Generates v4.0 format codes: [PREFIX].[GROUP].[TYPE]
e.g. A.CONC.STR — Activity, Concrete, Structural

Key design decisions:
  - 3 levels only: PREFIX, GROUP (material/object), TYPE (sub-category)
  - Same GROUP.TYPE across all 4 prefixes = same work package
  - Discipline, location, grade → separate attributes on master_work_item
  - Code NEVER changes when spec changes → stable identity
"""
import re
import unicodedata
from typing import Optional, Tuple

from sqlalchemy.orm import Session


class V4CodeGenerator:
    """Generate v4.0 format codes: A.CONC.STR (3 levels)"""

    # ── SEC code → Discipline mapping (returned separately, not in code) ──
    SEC_TO_DISCIPLINE = {
        'SEC-00': 'PM',
        'SEC-01': 'CV',
        'SEC-01-01': 'CV',
        'SEC-01-02': 'CV',
        'SEC-01-03': 'CV',
        'SEC-02': 'CV',
        'SEC-02-01': 'CV',
        'SEC-02-02': 'CV',
        'SEC-02-03': 'CV',
        'SEC-02-04': 'CV',
        'SEC-02-05': 'CV',
        'SEC-02-06': 'CV',
        'SEC-03': 'AR',
        'SEC-03-01': 'AR',
        'SEC-03-02': 'AR',
        'SEC-03-03': 'AR',
        'SEC-03-04': 'AR',
        'SEC-03-05': 'AR',
        'SEC-03-06': 'AR',
        'SEC-04': 'EL',
        'SEC-04-01': 'EL',
        'SEC-04-02': 'PL',
        'SEC-04-03': 'ME',
        'SEC-04-04': 'FP',
        'SEC-05': 'EX',
        'SEC-05-01': 'EX',
        'SEC-05-02': 'EX',
        'SEC-05-03': 'LA',
    }

    # ── L1 (GROUP): Description keywords → Group code ──
    # GROUP represents the primary material/object being worked on
    CATEGORY_TO_GROUP = {
        # Concrete & Rebar & Formwork
        'bê tông': 'CONC', 'be tong': 'CONC', 'betong': 'CONC', 'bêtông': 'CONC',
        'cốt thép': 'RBAR', 'cot thep': 'RBAR',
        'thép hình': 'RBAR',
        'ván khuôn': 'FWRK', 'van khuon': 'FWRK', 'coppha': 'FWRK',
        # Earth & Piling
        'đào đất': 'SOIL', 'dao dat': 'SOIL', 'đắp đất': 'SOIL', 'dap dat': 'SOIL',
        'san lấp': 'SOIL', 'san nền': 'SOIL',
        'cấp phối': 'AGGT',
        'cọc': 'PILE', 'coc': 'PILE',
        # Finishing
        'gạch xây': 'BRCK', 'gạch đặc': 'BRCK', 'block': 'BRCK',
        'xây tường': 'BRCK', 'xây': 'BRCK',
        'trát': 'PLST', 'trat': 'PLST', 'bả matit': 'PLST', 'ba matit': 'PLST',
        'sơn': 'PANT', 'son': 'PANT',
        'lát gạch': 'TILE', 'lat gach': 'TILE', 'ốp gạch': 'TILE',
        'lát': 'TILE', 'ốp': 'TILE', 'sàn gỗ': 'TILE', 'vinyl': 'TILE',
        'trần': 'CLNG', 'tran': 'CLNG', 'thạch cao': 'CLNG',
        'cửa': 'DOOR', 'cua': 'DOOR',
        'chống thấm': 'WPRF', 'chong tham': 'WPRF',
        'bồn cầu': 'SANT', 'lavabo': 'SANT', 'thiết bị vệ sinh': 'SANT',
        'lan can': 'RLNG',
        # Envelope
        'vách kính': 'CWLL', 'mặt dựng': 'CWLL', 'curtain': 'CWLL',
        'aluminium': 'CLAD', 'lam chắn': 'CLAD',
        # Electrical
        'cáp': 'CABL', 'cap': 'CABL', 'dây điện': 'CABL',
        'đèn': 'LITE', 'den': 'LITE',
        'tủ điện': 'PANL', 'tu dien': 'PANL',
        'aptomat': 'BRKR', 'mccb': 'BRKR', 'mcb': 'BRKR',
        'ống luồn': 'COND',
        'máng cáp': 'TRAY',
        # Plumbing
        'ống': 'PIPE', 'ong': 'PIPE',
        'van': 'VALV',
        'cút': 'FITG', 'tê': 'FITG', 'côn thu': 'FITG', 'bích': 'FITG',
        'bơm': 'PUMP', 'bom': 'PUMP',
        'bể nước': 'TANK',
        # HVAC
        'điều hòa': 'HVAC', 'dieu hoa': 'HVAC',
        'ahu': 'HVAC', 'fcu': 'HVAC', 'vrf': 'HVAC',
        'ống gió': 'DUCT',
        'cách nhiệt': 'INSU',
        # Fire Protection
        'sprinkler': 'SPRK', 'đầu phun': 'SPRK',
        'báo cháy': 'FALM', 'báo khói': 'FALM', 'báo nhiệt': 'FALM',
        'pccc': 'FFGT', 'chữa cháy': 'FFGT', 'bình chữa cháy': 'FFGT',
        # Road & Landscape
        'đường': 'ROAD', 'duong': 'ROAD', 'bê tông nhựa': 'ROAD',
        'bó vỉa': 'ROAD',
        'cây': 'LAND', 'cay': 'LAND', 'cảnh quan': 'LAND', 'cỏ': 'LAND',
        # Generic
        'thang máy': 'ELVT',
        'hàng rào': 'FENC',
    }

    # ── L2 (TYPE): Description keywords → Type code ──
    # TYPE represents sub-category/characteristic of the GROUP
    CATEGORY_TO_TYPE = {
        # Concrete types
        'kết cấu': 'STR', 'ket cau': 'STR',
        'lót': 'LEA', 'lot': 'LEA',
        'móng': 'FND', 'mong': 'FND', 'đài': 'FND', 'giằng': 'FND',
        # Soil types
        'đào': 'EXC', 'dao': 'EXC',
        'đắp': 'FIL', 'dap': 'FIL', 'lấp': 'FIL', 'san lấp': 'FIL',
        'san nền': 'GRD', 'san nen': 'GRD',
        'vận chuyển': 'TRN',
        # Pile types
        'khoan': 'BOR', 'nhồi': 'BOR',
        'ép': 'DRV', 'đóng': 'DRV',
        'thí nghiệm': 'TST',
        # Rebar types
        'thép hình': 'STL',
        # Formwork types
        'gỗ': 'WOD', 'go': 'WOD',
        'thép': 'STL',
        # Brick types
        'đặc': 'SOL', 'dac': 'SOL',
        'aac': 'AAC',
        'block bê tông': 'CON',
        # Plaster types
        'xi măng': 'CEM', 'xi mang': 'CEM', 'vữa': 'CEM',
        'matit': 'PUT',
        # Paint types
        'nội thất': 'INT', 'trong nhà': 'INT', 'trong': 'INT',
        'ngoại thất': 'EXT', 'ngoài': 'EXT',
        'chống thấm': 'WPF',
        # Tile types
        'ceramic': 'CER',
        'granite': 'GRN', 'đá tự nhiên': 'STN',
        'vinyl': 'VYL', 'spc': 'VYL',
        'gỗ công nghiệp': 'LAM',
        # Ceiling types
        'thạch cao': 'GYP',
        'nhôm': 'ALU',
        # Door types
        'gỗ': 'WOD',
        'nhôm kính': 'ALU', 'nhôm': 'ALU',
        'chống cháy': 'FIR',
        # Waterproofing types
        'màng': 'MEM', 'membrane': 'MEM',
        'quét': 'COT', 'coating': 'COT',
        # Electrical cable types
        'động lực': 'PWR',
        'điều khiển': 'CTL',
        'thông tin': 'COM',
        # Light types
        'led': 'LED',
        'sự cố': 'EMG',
        # Panel types
        'chính': 'MSB', 'msb': 'MSB',
        'phân phối': 'DSB', 'db': 'DSB',
        # Pipe types
        'cấp nước': 'SUP', 'cap nuoc': 'SUP', 'cấp': 'SUP',
        'thoát nước': 'DRN', 'thoat nuoc': 'DRN', 'thoát': 'DRN',
        'pccc': 'FIR',
        # Valve types
        'cổng': 'GAT',
        'bướm': 'BFL',
        'bi': 'BAL',
        'một chiều': 'CHK',
        # Fitting types
        'cút': 'ELB',
        'tê': 'TEE',
        'côn thu': 'RED',
        'bích': 'FLG',
        # Pump types
        'chìm': 'SUB',
        'ly tâm': 'CEN',
        'tăng áp': 'BOS',
        # HVAC types
        'split': 'SPL',
        'vrf': 'VRF',
        'ahu': 'AHU',
        'fcu': 'FCU',
        # Duct types
        'mạ kẽm': 'GVN', 'tôn': 'GVN',
        'mềm': 'FLX',
        # Fire types
        'quay lên': 'UPR', 'upright': 'UPR',
        'quay xuống': 'PND', 'pendant': 'PND',
        'khói': 'SMK',
        'nhiệt': 'HET',
        # Road types
        'nhựa': 'ASP', 'asphalt': 'ASP',
        'vỉa': 'CRB',
        'vạch': 'MRK',
        # Landscape types
        'cây xanh': 'TRE', 'cây': 'TRE',
        'cỏ': 'TRF',
        'tưới': 'IRG',
    }

    # ── Location keywords (returned as attribute, not in code) ──
    LOCATION_KEYWORDS = {
        'móng': 'FND', 'mong': 'FND',
        'cột': 'COL', 'cot': 'COL',
        'dầm': 'BEM', 'dam': 'BEM',
        'sàn': 'SLB', 'san': 'SLB',
        'tường': 'WAL', 'tuong': 'WAL',
        'vách': 'SHW', 'vach': 'SHW',
        'cầu thang': 'STR',
        'mái': 'ROF', 'mai': 'ROF',
        'hầm': 'BSM', 'ham': 'BSM',
        'nền': 'GRD', 'nen': 'GRD',
        'hố': 'PIT', 'ho': 'PIT',
        'ban công': 'BLC',
        'hành lang': 'COR',
        'bể': 'TNK', 'be': 'TNK',
    }

    def _normalize(self, text: str) -> str:
        """Lowercase + NFC normalize."""
        if not text:
            return ''
        return unicodedata.normalize('NFC', text).lower().strip()

    def _remove_accents(self, text: str) -> str:
        """Remove Vietnamese diacritics for fallback matching."""
        vn_map = {
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
            'đ': 'd',
        }
        return ''.join(vn_map.get(c, c) for c in text)

    def generate(
        self,
        description: str,
        sec_code: str,
        specs: Optional[dict] = None,
        table_type: str = 'A',
    ) -> Tuple[str, str, Optional[str]]:
        """
        Generate a v4.0 3-level code + attributes from description.

        Args:
            description: Vietnamese work description
            sec_code: Legacy SEC code (SEC-01, SEC-02, etc.)
            specs: Dict with keys: category, material, grade, dimension
            table_type: 'A' (Activity), 'M' (Material), 'L' (Labour), 'E' (Equipment)

        Returns:
            Tuple of (ref_code, discipline, location):
              - ref_code: "A.CONC.STR"
              - discipline: "CV"
              - location: "COL" or None
        """
        if specs is None:
            specs = {}

        prefix = table_type
        discipline = self._resolve_discipline(sec_code, description)
        group = self._resolve_group(description, specs)
        type_code = self._resolve_type(description, specs, group)
        location = self._resolve_location(description)

        ref_code = f"{prefix}.{group}.{type_code}"

        return ref_code, discipline, location

    def _resolve_discipline(self, sec_code: str, description: str) -> str:
        """Resolve discipline from SEC code or description keywords."""
        if sec_code:
            if sec_code in self.SEC_TO_DISCIPLINE:
                return self.SEC_TO_DISCIPLINE[sec_code]
            for prefix_len in [10, 6, 3]:
                prefix = sec_code[:prefix_len]
                if prefix in self.SEC_TO_DISCIPLINE:
                    return self.SEC_TO_DISCIPLINE[prefix]

        desc = self._normalize(description)
        if any(kw in desc for kw in ['điện', 'cáp', 'dây điện', 'tủ điện', 'đèn']):
            return 'EL'
        if any(kw in desc for kw in ['ống', 'van', 'bơm', 'nước']):
            return 'PL'
        if any(kw in desc for kw in ['điều hòa', 'thông gió']):
            return 'ME'
        if any(kw in desc for kw in ['pccc', 'cháy', 'sprinkler']):
            return 'FP'
        return 'CV'

    def _resolve_group(self, description: str, specs: dict) -> str:
        """Resolve L1 GROUP from description keywords."""
        desc = self._normalize(description)

        # Try Vietnamese keywords — longest match first
        for keyword, group in sorted(
            self.CATEGORY_TO_GROUP.items(), key=lambda x: len(x[0]), reverse=True
        ):
            if keyword in desc:
                return group

        # Try without accents
        desc_no_accent = self._remove_accents(desc)
        for keyword, group in sorted(
            self.CATEGORY_TO_GROUP.items(), key=lambda x: len(x[0]), reverse=True
        ):
            kw_no_accent = self._remove_accents(keyword)
            if kw_no_accent in desc_no_accent:
                return group

        # Fallback from spec_category
        cat = (specs.get('category') or '').lower()
        for keyword, group in self.CATEGORY_TO_GROUP.items():
            if keyword in cat:
                return group

        return 'GENR'

    def _resolve_type(self, description: str, specs: dict, group: str) -> str:
        """Resolve L2 TYPE from description keywords based on GROUP context."""
        desc = self._normalize(description)

        # Group-specific defaults
        group_defaults = {
            'CONC': 'STR', 'RBAR': 'STR', 'FWRK': 'STL',
            'SOIL': 'EXC', 'PILE': 'DRV', 'AGGT': 'CMP',
            'BRCK': 'SOL', 'PLST': 'CEM', 'PANT': 'INT',
            'TILE': 'CER', 'CLNG': 'GYP', 'DOOR': 'ALU',
            'WPRF': 'MEM',
            'CABL': 'PWR', 'LITE': 'LED', 'PANL': 'MSB',
            'BRKR': 'MCB', 'COND': 'PVC', 'TRAY': 'GVN',
            'PIPE': 'SUP', 'VALV': 'GAT', 'FITG': 'ELB',
            'PUMP': 'CEN', 'TANK': 'WTR',
            'HVAC': 'SPL', 'DUCT': 'GVN', 'INSU': 'RBR',
            'SPRK': 'PND', 'FALM': 'SMK', 'FFGT': 'EXT',
            'ROAD': 'ASP', 'LAND': 'TRE',
            'SANT': 'TLT', 'RLNG': 'GLS',
            'CWLL': 'GLS', 'CLAD': 'ALU',
            'ELVT': 'GEN', 'FENC': 'GEN',
        }

        # Try TYPE keywords — longest match first
        for keyword, type_code in sorted(
            self.CATEGORY_TO_TYPE.items(), key=lambda x: len(x[0]), reverse=True
        ):
            if keyword in desc:
                return type_code

        # Try without accents
        desc_no_accent = self._remove_accents(desc)
        for keyword, type_code in sorted(
            self.CATEGORY_TO_TYPE.items(), key=lambda x: len(x[0]), reverse=True
        ):
            kw_no_accent = self._remove_accents(keyword)
            if kw_no_accent in desc_no_accent:
                return type_code

        # Use group-specific default
        return group_defaults.get(group, 'GEN')

    def _resolve_location(self, description: str) -> Optional[str]:
        """Resolve location from description (returned as attribute, not in code)."""
        desc = self._normalize(description)

        for keyword, loc in sorted(
            self.LOCATION_KEYWORDS.items(), key=lambda x: len(x[0]), reverse=True
        ):
            if keyword in desc:
                return loc

        desc_no_accent = self._remove_accents(desc)
        for keyword, loc in sorted(
            self.LOCATION_KEYWORDS.items(), key=lambda x: len(x[0]), reverse=True
        ):
            kw_no_accent = self._remove_accents(keyword)
            if kw_no_accent in desc_no_accent:
                return loc

        return None

    def validate_v4_code(self, code: str) -> bool:
        """Validate that a code matches the 3-level dot-separated v4 format."""
        pattern = r'^[AMLE]\.[A-Z]{2,5}\.[A-Z]{2,4}$'
        return bool(re.match(pattern, code))

    def parse_v4_code(self, code: str) -> Optional[dict]:
        """Parse a v4.0 code into its components."""
        if not self.validate_v4_code(code):
            return None

        parts = code.split('.')
        return {
            'table_type': parts[0],
            'group': parts[1],
            'type': parts[2],
        }

    def generate_instance_code(self, ref_code: str, db: Session) -> str:
        """
        Generate a unique instance code: {REF_CODE}-{SEQ:03d}
        e.g. A.CONC.STR-001, A.CONC.STR-002
        """
        from app.models.master_work_item import MasterWorkItem

        existing = db.query(MasterWorkItem.instance_code).filter(
            MasterWorkItem.instance_code.like(f"{ref_code}-%"),
        ).all()

        max_seq = 0
        for (inst_code,) in existing:
            if inst_code and '-' in inst_code:
                suffix = inst_code.rsplit('-', 1)[-1]
                try:
                    seq = int(suffix)
                    if seq > max_seq:
                        max_seq = seq
                except ValueError:
                    pass

        next_seq = max_seq + 1
        return f"{ref_code}-{next_seq:03d}"
