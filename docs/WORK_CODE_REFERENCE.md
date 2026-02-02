# Work Code Quick Reference

## Cấu Trúc

### Format Cơ Bản
```
{SEC}-{CATEGORY}-{SUB}-{SEQ}
 S01   EARTH      EXCAV  0001

Ví dụ: S01-EARTH-EXCAV-0001 = Đào đất móng
```

### Format Với Material Grade (Mác Vật Liệu)
```
{SEC}-{CATEGORY}-{GRADE}-{SEQ}
 S02   CONC        M200    0001

Ví dụ: S02-CONC-M200-0001 = Bê tông M200
```

## SEC Codes

| Code | Meaning |
|------|---------|
| S00 | Preliminaries & General |
| S01 | Substructure |
| S02 | Superstructure |
| S03 | Architecture & Finishes |
| S04 | MEP Systems |
| S05 | Landscape & External |

## Common Categories

### S01 - Substructure
- EARTH = Đất (Earthworks)
- PILE = Cọc (Piling)
- FOUND = Móng (Foundation)
- FILL = Đắp đất (Fill)
- LEVEL = San lấp (Leveling)

**Sub-categories:**
- EXCAV = Excavation (Đào)
- BACKFILL = Backfill (Đắp)
- DPILE = Drilled Pile (Cọc khoan)
- BPILE = Bored Pile (Cọc nhồi)

### S02 - Superstructure
- CONC = Bê tông (Concrete)
- REBAR = Cốt thép (Rebar)
- STRUC = Kết cấu (Structure)
- BEAM = Dầm (Beam)
- COL = Cột (Column)
- SLAB = Sàn (Slab)
- WALL = Tường (Wall)

### S03 - Architecture
- WALL = Tường xây (Wall)
- BRICK = Gạch (Brick)
- BLOCK = Block
- PLAST = Trát (Plastering)
- PAINT = Sơn (Painting)
- TILE = Gạch lát (Tiling)
- FLOOR = Nền (Flooring)
- CEIL = Trần (Ceiling)
- DOOR = Cửa (Door)
- WIND = Cửa sổ (Window)

### S04 - MEP
- ELEC = Điện (Electrical)
- PLUMB = Nước (Plumbing)
- HVAC = Điều hòa (HVAC)
- VENT = Thông gió (Ventilation)
- FIRE = PCCC (Fire Protection)
- ELEV = Thang máy (Elevator)

### S05 - Landscape
- ROAD = Đường (Road)
- PAVE = Vỉa hè (Pavement)
- FENCE = Hàng rào (Fence)
- GATE = Cổng (Gate)
- TREE = Cây (Trees)
- PLANT = Cây trồng (Plants)
- POND = Hồ (Pond)
- PARK = Bãi đỗ (Parking)

## Examples

### Standard Work Items
| Code | Description |
|------|-------------|
| S01-EARTH-EXCAV-0001 | Đào đất móng |
| S01-PILE-DPILE-0001 | Cọc khoan nhồi |
| S03-WALL-BRICK-0001 | Tường gạch |
| S04-ELEC-0001 | Hệ thống điện |
| S05-ROAD-0001 | Đường nội bộ |

### Work Items With Material Grades
| Code | Description |
|------|-------------|
| S02-CONC-M200-0001 | Bê tông M200 dầm |
| S02-CONC-M250-0001 | Bê tông M250 cột |
| S02-CONC-M300-0001 | Bê tông M300 sàn |
| S03-PLAST-M75-0001 | Vữa trát M75 |
| S03-PLAST-M100-0001 | Vữa trát M100 |
| S03-WALL-M50-0001 | Tường gạch vữa M50 |

## Usage

### Generate Code
```python
from app.services.work_code_generator import WorkCodeGenerator

generator = WorkCodeGenerator(db)
code = generator.generate_work_code("Đào đất móng", "SEC-01-01")
# Returns: "S01-EARTH-EXCAV-0001"
```

### Validate Code
```python
is_valid = generator.validate_work_code("S01-EARTH-EXCAV-0001")
# Returns: True
```

### Parse Code
```python
parsed = generator.parse_work_code("S01-EARTH-EXCAV-0001")
# Returns: {
#   'sec_prefix': 'S01',
#   'category': 'EARTH',
#   'sub_category': 'EXCAV',
#   'sequence': '0001'
# }
```

### Search Examples
```sql
-- All SEC-01 items
WHERE work_code LIKE 'S01-%'

-- All concrete items
WHERE work_code LIKE '%-CONC-%'

-- All M200 concrete
WHERE work_code LIKE '%-M200-%'

-- All M75 mortar
WHERE work_code LIKE '%-M75-%'

-- Specific category
WHERE work_code LIKE 'S02-CONC-BEAM-%'

-- Specific grade in SEC-02
WHERE work_code LIKE 'S02-CONC-M200-%'
```

## Rules

1. ✅ Always use WorkCodeGenerator
2. ✅ Validate before saving
3. ✅ Use consistent format
4. ❌ Don't create manual codes
5. ❌ Don't modify existing codes
