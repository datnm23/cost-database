"""
Dictionary of construction materials.
Includes pipe materials, electrical materials, concrete types, finishes, etc.
"""

# Material mappings: Vietnamese variations -> Standard name
DICT_MATERIALS = {
    # Pipe materials - Compound (longest first)
    'thép mạ kẽm': 'Thép mạ kẽm',
    'thép đen': 'Thép đen',
    'thép không gỉ': 'Inox',
    'inox 304': 'Inox 304',
    'inox 316': 'Inox 316',
    'inox': 'Inox',
    'gang dẻo': 'Gang dẻo',
    'gang cầu': 'Gang cầu',
    'gang': 'Gang',

    # Plastic pipes
    'hdpe': 'HDPE',
    'pe100': 'PE100',
    'pe80': 'PE80',
    'ppr': 'PPR',
    'upvc': 'uPVC',
    'cpvc': 'CPVC',
    'pvc': 'PVC',
    'abs': 'ABS',
    'frp': 'FRP',
    'grp': 'GRP',

    # Electrical - Cable insulation (compound first)
    'cu/xlpe/pvc/dsta': 'Cu/XLPE/PVC/DSTA',
    'cu/xlpe/pvc': 'Cu/XLPE/PVC',
    'cu/xlpe': 'Cu/XLPE',
    'cu/pvc': 'Cu/PVC',
    'al/xlpe/pvc': 'Al/XLPE/PVC',
    'nhôm bọc': 'Nhôm bọc',
    'nhôm': 'Nhôm',
    'đồng trần': 'Đồng trần',
    'đồng': 'Đồng',
    'xlpe': 'XLPE',

    # Concrete types
    'bê tông cốt thép': 'BTCT',
    'btct': 'BTCT',
    'bê tông đúc sẵn': 'BT đúc sẵn',
    'bê tông tươi': 'BT tươi',
    'bê tông thương phẩm': 'BT thương phẩm',

    # Steel types
    'thép cb400v': 'CB400V',
    'thép cb300': 'CB300',
    'cb400v': 'CB400V',
    'cb300t': 'CB300T',
    'cb300': 'CB300',
    'cb240': 'CB240',
    'thép cuộn': 'Thép cuộn',
    'thép thanh': 'Thép thanh',

    # Formwork
    'ván ép phủ phim': 'Phủ phim',
    'phủ phim': 'Phủ phim',
    'ván ép': 'Ván ép',
    'cốp pha thép': 'Cốp pha thép',
    'cốp pha nhựa': 'Cốp pha nhựa',

    # Brick types
    'gạch đất nung': 'Gạch đất nung',
    'gạch không nung': 'Gạch không nung',
    'gạch block': 'Gạch block',
    'gạch bê tông': 'Gạch bê tông',
    'gạch aac': 'Gạch AAC',
    'aac': 'AAC',

    # Finishes
    'granite nhân tạo': 'Granite nhân tạo',
    'granite tự nhiên': 'Granite tự nhiên',
    'granite bóng kính': 'Granite bóng kính',
    'granite': 'Granite',
    'ceramic': 'Ceramic',
    'porcelain': 'Porcelain',
    'gạch men': 'Gạch men',
    'đá marble': 'Đá marble',
    'đá hoa cương': 'Đá hoa cương',

    # Wood types
    'gỗ mdf chống ẩm': 'Gỗ MDF chống ẩm',
    'gỗ mdf': 'Gỗ MDF',
    'mdf': 'MDF',
    'gỗ công nghiệp': 'Gỗ công nghiệp',
    'gỗ tự nhiên': 'Gỗ tự nhiên',
    'gỗ plywood': 'Gỗ plywood',
    'melamine': 'Melamine',
    'laminate': 'Laminate',
    'acrylic': 'Acrylic',

    # Glass types
    'kính cường lực': 'Kính cường lực',
    'kính dán an toàn': 'Kính dán an toàn',
    'kính low-e': 'Kính Low-E',
    'kính lowe': 'Kính Low-E',
    'kính phản quang': 'Kính phản quang',
    'kính trong': 'Kính trong',

    # Aluminum
    'nhôm xingfa': 'Nhôm Xingfa',
    'nhôm việt pháp': 'Nhôm Việt Pháp',
    'nhôm hệ': 'Nhôm hệ',

    # Paint types
    'sơn jotun': 'Jotun',
    'sơn dulux': 'Dulux',
    'sơn nippon': 'Nippon',
    'sơn nội thất': 'Nội thất',
    'sơn ngoại thất': 'Ngoại thất',
    'jotashield': 'Jotashield',
    'epoxy': 'Epoxy',
    'pu': 'PU',

    # Composite materials
    'composite': 'Composite',
    'nhựa composite': 'Composite',
    'fiberglass': 'Fiberglass',

    # Road materials
    'cấp phối đá dăm': 'CPĐD',
    'cpđd': 'CPĐD',
    'đá dăm': 'Đá dăm',
    'bê tông nhựa': 'BTN',
    'asphalt': 'Asphalt',
    'btn': 'BTN',
}

# Pressure ratings - separate for clarity
DICT_PRESSURE = {
    'pn6': 'PN6',
    'pn6.3': 'PN6.3',
    'pn8': 'PN8',
    'pn10': 'PN10',
    'pn12.5': 'PN12.5',
    'pn16': 'PN16',
    'pn20': 'PN20',
    'pn25': 'PN25',
}

# Sort by length descending for longest match first
DICT_MATERIALS_SORTED = dict(
    sorted(DICT_MATERIALS.items(), key=lambda x: len(x[0]), reverse=True)
)
