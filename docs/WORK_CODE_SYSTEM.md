# Hệ Thống Đặt Tên Công Tác (Work Code System)

## Tổng Quan

Hệ thống đặt tên công tác được thiết kế để:
- ✅ **Nhất quán**: Tất cả mã công tác tuân theo cùng một format
- ✅ **Dễ đọc**: Có thể hiểu ngay ý nghĩa từ mã code
- ✅ **Dễ tìm kiếm**: Tìm kiếm theo SEC, category, hoặc sequence
- ✅ **Có cấu trúc**: Sắp xếp logic theo nhóm công việc
- ✅ **Mở rộng được**: Dễ dàng thêm categories mới

---

## Cấu Trúc Work Code

### Format Chuẩn

```
{SEC_PREFIX}-{CATEGORY}-{SUB_CATEGORY}-{SEQUENCE}
   (2-3 ký tự)  (3-6 ký tự)  (3-8 ký tự)    (4 số)
```

**Hoặc đơn giản hơn:**

```
{SEC_PREFIX}-{CATEGORY}-{SEQUENCE}
```

### Các Thành Phần

#### 1. SEC_PREFIX (Mã Phân Loại)

Mapping từ SEC codes sang prefix ngắn gọn:

| SEC Code | Prefix | Ý Nghĩa |
|----------|--------|---------|
| SEC-00 | S00 | Preliminaries & General |
| SEC-01 | S01 | Substructure (Earthworks, Piling, Foundation) |
| SEC-02 | S02 | Superstructure (Concrete, Steel) |
| SEC-03 | S03 | Architecture & Finishes |
| SEC-04 | S04 | MEP Systems |
| SEC-05 | S05 | Landscape & External Works |

**Tại sao dùng S01 thay vì SEC-01?**
- Ngắn gọn hơn (3 ký tự vs 6 ký tự)
- Dễ gõ, dễ đọc
- Vẫn giữ được ý nghĩa

#### 2. CATEGORY (Nhóm Công Tác Chính)

Danh mục các categories thông dụng:

**SEC-01 (Substructure):**
- `EARTH` - Công tác đất (Earthworks)
- `PILE` - Cọc (Piling)
- `FOUND` - Móng (Foundation)
- `FILL` - Đắp đất (Backfill)
- `LEVEL` - San lấp (Leveling)

**SEC-02 (Superstructure):**
- `CONC` - Bê tông (Concrete)
- `REBAR` - Cốt thép (Reinforcement)
- `FORM` - Ván khuôn (Formwork)
- `STRUC` - Kết cấu (Structure)
- `BEAM` - Dầm (Beam)
- `COL` - Cột (Column)
- `SLAB` - Sàn (Slab)
- `WALL` - Tường (Wall)

**SEC-03 (Architecture & Finishes):**
- `WALL` - Tường xây (Masonry Wall)
- `BRICK` - Gạch (Brick)
- `BLOCK` - Block
- `PLAST` - Trát (Plastering)
- `PAINT` - Sơn (Painting)
- `TILE` - Lát gạch (Tiling)
- `FLOOR` - Sàn/Nền (Flooring)
- `CEIL` - Trần (Ceiling)
- `ROOF` - Mái (Roofing)
- `DOOR` - Cửa (Door)
- `WIND` - Cửa sổ (Window)

**SEC-04 (MEP):**
- `ELEC` - Điện (Electrical)
- `PLUMB` - Nước (Plumbing)
- `WATER` - Cấp thoát nước (Water Supply)
- `HVAC` - Điều hòa (HVAC)
- `VENT` - Thông gió (Ventilation)
- `FIRE` - Phòng cháy chữa cháy (Fire Protection)
- `ELEV` - Thang máy (Elevator)

**SEC-05 (Landscape):**
- `LAND` - Cảnh quan (Landscape)
- `ROAD` - Đường (Road)
- `PAVE` - Vỉa hè (Pavement)
- `FENCE` - Hàng rào (Fence)
- `GATE` - Cổng (Gate)
- `TREE` - Cây xanh (Trees/Plants)
- `PLANT` - Cây trồng (Planting)
- `POND` - Hồ (Pond/Lake)
- `PARK` - Bãi đỗ (Parking)

#### 3. SUB_CATEGORY (Chi Tiết - Tùy Chọn)

Mô tả chi tiết hơn về loại công tác:

| Sub-Category | Ý Nghĩa |
|--------------|---------|
| EXCAV | Excavation (Đào) |
| BACKFILL | Backfill (Đắp đất) |
| DPILE | Drilled Pile (Cọc khoan) |
| BPILE | Bored Pile (Cọc nhồi) |
| STRIP | Strip Foundation (Móng băng) |
| RAFT | Raft Foundation (Móng bè) |
| MASON | Masonry (Xây) |
| SIDE | Sidewalk (Vỉa hè) |

#### 4. SEQUENCE (Số Thứ Tự)

- Luôn là **4 chữ số**: `0001`, `0002`, ..., `9999`
- Tự động tăng trong mỗi nhóm (SEC + CATEGORY)
- Reset khi chuyển sang nhóm mới

---

## Ví Dụ Thực Tế

### Ví Dụ 1: Công Tác Đất

| Work Code | Description | Phân Tích |
|-----------|-------------|-----------|
| S01-EARTH-EXCAV-0001 | Đào đất móng | SEC-01, Earthworks, Excavation, #1 |
| S01-EARTH-EXCAV-0002 | Đào đất hố móng | SEC-01, Earthworks, Excavation, #2 |
| S01-EARTH-BACKFILL-0001 | Đắp đất nền | SEC-01, Earthworks, Backfill, #1 |
| S01-FILL-0001 | San lấp mặt bằng | SEC-01, Fill, #1 |

### Ví Dụ 2: Bê Tông

| Work Code | Description | Phân Tích |
|-----------|-------------|-----------|
| S02-CONC-BEAM-0001 | Bê tông dầm | SEC-02, Concrete, Beam, #1 |
| S02-CONC-COL-0001 | Bê tông cột | SEC-02, Concrete, Column, #1 |
| S02-CONC-SLAB-0001 | Bê tông sàn | SEC-02, Concrete, Slab, #1 |
| S02-REBAR-0001 | Cốt thép dầm | SEC-02, Rebar, #1 |

### Ví Dụ 3: Kiến Trúc

| Work Code | Description | Phân Tích |
|-----------|-------------|-----------|
| S03-WALL-BRICK-0001 | Tường gạch | SEC-03, Wall, Brick, #1 |
| S03-WALL-BLOCK-0001 | Tường block | SEC-03, Wall, Block, #1 |
| S03-PLAST-0001 | Trát tường trong | SEC-03, Plastering, #1 |
| S03-PAINT-0001 | Sơn tường | SEC-03, Painting, #1 |
| S03-TILE-FLOOR-0001 | Lát gạch nền | SEC-03, Tile, Floor, #1 |

### Ví Dụ 4: MEP

| Work Code | Description | Phân Tích |
|-----------|-------------|-----------|
| S04-ELEC-0001 | Hệ thống điện | SEC-04, Electrical, #1 |
| S04-PLUMB-0001 | Hệ thống nước | SEC-04, Plumbing, #1 |
| S04-ELEV-0001 | Thang máy 8 người | SEC-04, Elevator, #1 |
| S04-FIRE-0001 | Hệ thống PCCC | SEC-04, Fire Protection, #1 |

### Ví Dụ 5: Cảnh Quan

| Work Code | Description | Phân Tích |
|-----------|-------------|-----------|
| S05-ROAD-0001 | Đường nội bộ bê tông | SEC-05, Road, #1 |
| S05-PAVE-SIDE-0001 | Vỉa hè lát gạch | SEC-05, Pavement, Sidewalk, #1 |
| S05-FENCE-0001 | Hàng rào bảo vệ | SEC-05, Fence, #1 |
| S05-GATE-0001 | Cổng chính | SEC-05, Gate, #1 |
| S05-TREE-PLANT-0001 | Cây xanh công viên | SEC-05, Tree, Planting, #1 |

---

## So Sánh Hệ Thống Cũ vs Mới

### Hệ Thống Cũ (Không Nhất Quán)

```
DAO-DAT-MONG-0001       # Dựa vào từ trong description
TONG-COT-THEP-0002      # Thiếu chữ đầu, khó hiểu
BAO-HIEM-CONG-0001      # Không rõ SEC code
NHA-VAN-PHONG-0001      # Không nhất quán
CANH-QUAN--0002         # Có "--" lỗi format
```

**Vấn đề:**
- ❌ Không nhất quán format
- ❌ Khó tìm kiếm theo nhóm
- ❌ Không rõ SEC code
- ❌ Sequence không logic
- ❌ Có lỗi kỹ thuật (ký tự trùng)

### Hệ Thống Mới (Chuẩn)

```
S01-EARTH-EXCAV-0001    # Rõ ràng: SEC-01, Earthworks, Excavation
S02-CONC-COL-0002       # Rõ ràng: SEC-02, Concrete, Column
S00-PRELIM-0001         # Rõ ràng: SEC-00, Preliminaries
S00-OFFICE-0001         # Rõ ràng: SEC-00, Office/Building
S05-LAND-POND-0002      # Rõ ràng: SEC-05, Landscape, Pond
```

**Ưu điểm:**
- ✅ Format nhất quán
- ✅ Dễ tìm kiếm: `S01-*`, `*-CONC-*`, `*-0001`
- ✅ Rõ ràng SEC code
- ✅ Sequence logic theo nhóm
- ✅ Không có lỗi kỹ thuật

---

## Cách Sử Dụng

### 1. Tự Động Generate (Recommended)

```python
from app.services.work_code_generator import WorkCodeGenerator

generator = WorkCodeGenerator(db)

# Generate work code từ description
code = generator.generate_work_code(
    description="Đào đất móng",
    sec_code="SEC-01-01",
    unit="m3"
)
# Result: "S01-EARTH-EXCAV-0001"
```

### 2. Validate Work Code

```python
# Check if valid
is_valid = generator.validate_work_code("S01-EARTH-EXCAV-0001")
# Result: True

is_valid = generator.validate_work_code("INVALID-CODE-123")
# Result: False
```

### 3. Parse Work Code

```python
# Parse components
parsed = generator.parse_work_code("S01-EARTH-EXCAV-0001")
# Result:
# {
#     'sec_prefix': 'S01',
#     'category': 'EARTH',
#     'sub_category': 'EXCAV',
#     'sequence': '0001'
# }
```

### 4. Regenerate All Codes

```bash
# Preview changes
docker compose exec backend python regenerate_work_codes.py

# Output:
# PREVIEW: Work Code Changes
# Total items: 20
# Will update: 18
# Unchanged: 2
#
# Old Code                  New Code                  Description
# DAO-DAT-MONG-0001        S01-EARTH-EXCAV-0001     Đào đất móng
# TONG-COT-THEP-0002       S02-CONC-WALL-0001       Tường bê tông cốt thép
# ...
#
# Do you want to apply these changes? (yes/no):
```

---

## Tìm Kiếm và Query

### Tìm tất cả công tác trong SEC-01

```sql
SELECT * FROM master_work_items
WHERE work_code LIKE 'S01-%'
ORDER BY work_code;
```

### Tìm tất cả công tác bê tông

```sql
SELECT * FROM master_work_items
WHERE work_code LIKE '%-CONC-%'
ORDER BY work_code;
```

### Tìm công tác theo sequence

```sql
SELECT * FROM master_work_items
WHERE work_code LIKE '%-0001'
ORDER BY work_code;
```

### Tìm công tác theo category cụ thể

```sql
SELECT * FROM master_work_items
WHERE work_code LIKE 'S02-CONC-BEAM-%'
ORDER BY work_code;
```

---

## Mở Rộng Hệ Thống

### Thêm Category Mới

Edit file `backend/app/services/work_code_generator.py`:

```python
CATEGORY_KEYWORDS = {
    # ... existing keywords ...

    # Thêm category mới
    'thép': 'STEEL',
    'gỗ': 'WOOD',
    'kính': 'GLASS',
}
```

### Thêm Sub-Category Mới

```python
SUB_KEYWORDS = {
    # ... existing keywords ...

    # Thêm sub-category mới
    'thép hình': 'SECTION',
    'thép tấm': 'PLATE',
}
```

---

## Best Practices

### 1. Luôn Dùng Auto-Generate

❌ **Không nên:**
```python
work_code = "CUSTOM-CODE-001"  # Manual, không nhất quán
```

✅ **Nên:**
```python
work_code = generator.generate_work_code(description, sec_code, unit)
```

### 2. Validate Trước Khi Lưu

```python
if not generator.validate_work_code(work_code):
    raise ValueError(f"Invalid work code: {work_code}")
```

### 3. Review Generated Codes

Sau khi generate, luôn review một số samples:
```bash
docker compose exec backend python regenerate_work_codes.py
```

### 4. Backup Trước Khi Regenerate

```bash
# Export current codes
docker compose exec backend python -c "
from app.services.master_data_service import MasterDataService
from app.core.database import SessionLocal
service = MasterDataService(SessionLocal())
service.export_master_csv('/app/backup_master_codes.csv')
"
```

---

## Troubleshooting

### Lỗi: Duplicate Work Code

**Nguyên nhân:** Sequence number không đồng bộ

**Giải pháp:**
```python
# Regenerate all codes để sync sequence
generator.regenerate_all_codes(dry_run=False)
```

### Lỗi: Invalid Work Code Format

**Nguyên nhân:** Code không match pattern

**Kiểm tra:**
```python
is_valid = generator.validate_work_code(code)
parsed = generator.parse_work_code(code)  # Returns None if invalid
```

### Không Nhận Diện Được Category

**Nguyên nhân:** Thiếu keyword trong dictionary

**Giải pháp:** Thêm keyword vào `CATEGORY_KEYWORDS` hoặc `SUB_KEYWORDS`

---

## Kết Luận

Hệ thống đặt tên mới mang lại:
- ✅ **Tính nhất quán** cao
- ✅ **Dễ đọc, dễ hiểu** cho mọi người
- ✅ **Dễ tìm kiếm** và filter
- ✅ **Có cấu trúc** logic
- ✅ **Dễ mở rộng** với categories mới

**Next Steps:**
1. Review và test generator với data hiện tại
2. Regenerate tất cả codes
3. Update documentation cho team
4. Train users về hệ thống mới
