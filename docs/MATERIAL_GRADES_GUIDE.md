# Hỗ Trợ Mác Vật Liệu (Material Grades) trong Work Code System

## Vấn Đề

Trong xây dựng, nhiều công tác có **nhiều loại mác khác nhau**:

### Bê Tông (Concrete)
- M100, M150, M200, M250, M300, M350, M400
- Mỗi mác có giá khác nhau
- Ứng dụng khác nhau (M200 cho móng, M300 cho cột/dầm, v.v.)

### Vữa (Mortar)
- M50 (xây tường)
- M75 (xây tường chịu lực, trát)
- M100 (trát tường ngoài, công trình đặc biệt)

**❌ Vấn đề cũ:** Không phân biệt được mác trong work code
```
S02-CONC-CONC-0001  → Bê tông M200? M250? M300?
S03-PLAST-0001      → Vữa trát M75? M100?
```

## Giải Pháp

Hệ thống tự động **nhận diện và tích hợp mác vật liệu vào work code**.

### ✅ Cấu Trúc Mới

```
S02-CONC-M200-0001
│   │    │    │
│   │    │    └─ Sequence
│   │    └────── Material Grade (M200)
│   └─────────── Category (CONC)
└─────────────── SEC Prefix (S02)
```

### So Sánh

| Description | Old Code | New Code (with grade) |
|-------------|----------|----------------------|
| Bê tông M200 dầm | S02-CONC-CONC-0001 | **S02-CONC-M200-0001** |
| Bê tông M250 cột | S02-CONC-CONC-0002 | **S02-CONC-M250-0001** |
| Bê tông M300 sàn | S02-CONC-CONC-0003 | **S02-CONC-M300-0001** |
| Vữa trát M75 | S03-PLAST-0001 | **S03-PLAST-M75-0001** |
| Vữa trát M100 | S03-PLAST-0002 | **S03-PLAST-M100-0001** |
| Tường gạch vữa M50 | S03-WALL-BRICK-0001 | **S03-WALL-M50-0001** |

## Tự Động Nhận Diện Mác

Hệ thống tự động nhận diện mác từ nhiều format:

| Description Input | Detected Grade |
|-------------------|----------------|
| "Bê tông M200" | M200 |
| "Bê tông M250" | M250 |
| "Bê tông mác 200" | M200 |
| "Bê tông mác 250" | M250 |
| "Concrete grade 300" | M300 |
| "Vữa trát M75" | M75 |
| "Vữa xây M50" | M50 |
| "Tường gạch vữa M75" | M75 |
| "Bê tông cột" | None (no grade) |

### Patterns Được Hỗ Trợ

1. **M + số:** `M200`, `M250`, `M300`, `M75`, `M100`
2. **"mác" + số:** `mác 200`, `mác 250`
3. **"grade" + số:** `grade 300`, `grade 250`
4. **"cấp" + số:** `cấp 200`, `cấp 250`

## Cách Sử Dụng

### 1. Auto-Generate với Material Grade

```python
from app.services.work_code_generator import WorkCodeGenerator

generator = WorkCodeGenerator(db)

# Tự động nhận diện và include grade
code = generator.generate_work_code(
    description="Bê tông M200 dầm",
    sec_code="SEC-02",
    include_grade=True  # Default = True
)
# Result: "S02-CONC-M200-0001"

# Không include grade (dùng sub-category)
code = generator.generate_work_code(
    description="Bê tông M200 dầm",
    sec_code="SEC-02",
    include_grade=False
)
# Result: "S02-CONC-CONC-0001"
```

### 2. Extract Material Grade

```python
# Chỉ extract grade từ description
grade = generator.extract_material_grade("Bê tông M200 dầm")
# Result: "M200"

grade = generator.extract_material_grade("Vữa trát M75")
# Result: "M75"

grade = generator.extract_material_grade("Tường gạch")
# Result: None
```

### 3. Validation

```python
# Work codes với material grade vẫn hợp lệ
is_valid = generator.validate_work_code("S02-CONC-M200-0001")
# Result: True

is_valid = generator.validate_work_code("S03-PLAST-M75-0001")
# Result: True
```

### 4. Parse Work Code

```python
# Parse để lấy components
parsed = generator.parse_work_code("S02-CONC-M200-0001")
# Result: {
#   'sec_prefix': 'S02',
#   'category': 'CONC',
#   'sub_category': 'M200',  # Material grade ở đây
#   'sequence': '0001'
# }
```

## Tìm Kiếm Theo Material Grade

### SQL Queries

```sql
-- Tất cả bê tông M200
SELECT * FROM master_work_items
WHERE work_code LIKE '%-M200-%';

-- Tất cả bê tông M250
SELECT * FROM master_work_items
WHERE work_code LIKE '%-M250-%';

-- Tất cả vữa M75
SELECT * FROM master_work_items
WHERE work_code LIKE '%-M75-%';

-- Tất cả bê tông (không phân biệt mác)
SELECT * FROM master_work_items
WHERE work_code LIKE 'S02-CONC-%';

-- Bê tông M200 trong SEC-02
SELECT * FROM master_work_items
WHERE work_code LIKE 'S02-CONC-M200-%';
```

### Python Queries

```python
from app.models.master_work_item import MasterWorkItem

# Tất cả bê tông M200
items = db.query(MasterWorkItem).filter(
    MasterWorkItem.work_code.like('%-M200-%')
).all()

# Bê tông M200 trong SEC-02
items = db.query(MasterWorkItem).filter(
    MasterWorkItem.work_code.like('S02-CONC-M200-%')
).all()
```

## Ví Dụ Thực Tế

### Bê Tông Các Loại Mác

| Work Code | Description | Unit | Reference Price |
|-----------|-------------|------|-----------------|
| S02-CONC-M200-0001 | Bê tông M200 dầm | m³ | 1,500,000 |
| S02-CONC-M250-0001 | Bê tông M250 cột | m³ | 1,650,000 |
| S02-CONC-M300-0001 | Bê tông M300 sàn | m³ | 1,800,000 |
| S01-FOUND-M200-0001 | Bê tông M200 móng | m³ | 1,450,000 |

### Vữa Các Loại Mác

| Work Code | Description | Unit | Reference Price |
|-----------|-------------|------|-----------------|
| S03-PLAST-M75-0001 | Vữa trát M75 trong nhà | m² | 35,000 |
| S03-PLAST-M100-0001 | Vữa trát M100 ngoài trời | m² | 42,000 |
| S03-WALL-M50-0001 | Tường gạch vữa M50 | m² | 180,000 |
| S03-WALL-M75-0001 | Tường gạch vữa M75 | m² | 195,000 |

## Ưu Điểm

### 1. Phân Biệt Rõ Ràng
- Mỗi mác có work code riêng
- Dễ dàng quản lý giá theo mác
- Tránh nhầm lẫn khi estimate

### 2. Tìm Kiếm Dễ Dàng
```sql
-- Tìm tất cả công tác dùng bê tông M200
WHERE work_code LIKE '%-M200-%'

-- So sánh giá giữa các mác
SELECT work_code, ref_unit_price_avg
FROM master_work_items
WHERE work_code LIKE 'S02-CONC-M%'
ORDER BY work_code;
```

### 3. Thống Kê Theo Mác
```sql
-- Thống kê số lượng công tác theo mác bê tông
SELECT
    SUBSTRING_INDEX(SUBSTRING_INDEX(work_code, '-', 3), '-', -1) AS grade,
    COUNT(*) as count,
    AVG(ref_unit_price_avg) as avg_price
FROM master_work_items
WHERE work_code LIKE 'S02-CONC-M%'
GROUP BY grade;

-- Result:
-- M200  | 25 items | 1,500,000 VND
-- M250  | 18 items | 1,650,000 VND
-- M300  | 12 items | 1,800,000 VND
```

### 4. Flexible Options
```python
# Option 1: Include grade (recommended for materials with grades)
code = generator.generate_work_code("Bê tông M200", "SEC-02", include_grade=True)
# → S02-CONC-M200-0001

# Option 2: Exclude grade (for generic items)
code = generator.generate_work_code("Bê tông M200", "SEC-02", include_grade=False)
# → S02-CONC-CONC-0001
```

## Best Practices

### 1. Luôn Ghi Rõ Mác

❌ **Không tốt:**
```
"Bê tông dầm"  → Không rõ mác
"Vữa trát"     → Không rõ mác
```

✅ **Tốt:**
```
"Bê tông M200 dầm"   → Rõ ràng
"Vữa trát M75"       → Rõ ràng
```

### 2. Consistent Naming

✅ **Format chuẩn:**
- `Bê tông M200`, `Bê tông M250`, `Bê tông M300`
- `Vữa M50`, `Vữa M75`, `Vữa M100`

❌ **Tránh:**
- `BT M200`, `BTM200` (viết tắt không chuẩn)
- `Bê tông 200`, `Bê tông mác200` (thiếu khoảng trắng)

### 3. Use include_grade=True for Materials

```python
# Với vật liệu có mác → include_grade=True
materials_with_grades = ["bê tông", "vữa", "gạch"]

if any(mat in description.lower() for mat in materials_with_grades):
    code = generator.generate_work_code(desc, sec, include_grade=True)
else:
    code = generator.generate_work_code(desc, sec, include_grade=False)
```

## Migration Guide

Nếu bạn đã có master items cũ không có mác trong code:

### Step 1: Update Descriptions

```sql
-- Đảm bảo descriptions có mác
UPDATE master_work_items
SET description = 'Bê tông M200 dầm'
WHERE description = 'Bê tông dầm' AND work_code LIKE 'S02-CONC-%';
```

### Step 2: Regenerate Codes

```bash
docker compose exec backend python regenerate_work_codes.py
```

### Step 3: Review Changes

Hệ thống sẽ preview:
```
Old Code: S02-CONC-CONC-0001
New Code: S02-CONC-M200-0001
Description: Bê tông M200 dầm
```

## Common Material Grades Reference

### Bê Tông (Concrete)
- **M100, M150:** Lót móng, công trình tạm
- **M200, M250:** Móng, dầm phụ, tường
- **M300, M350:** Cột, dầm chính, sàn
- **M400+:** Công trình đặc biệt

### Vữa (Mortar)
- **M50:** Xây tường ngăn, tường không chịu lực
- **M75:** Xây tường chịu lực, trát tường trong
- **M100:** Trát tường ngoài, công trình ẩm ướt

### Gạch (Brick)
- **M75, M100, M150:** Theo tiêu chuẩn TCVN

## Summary

✅ **Đã Implement:**
- Auto-detection của material grades từ description
- Include/exclude grade option
- Validation support cho codes with grades
- Parse support cho codes with grades

✅ **Benefits:**
- Phân biệt rõ ràng các mác vật liệu
- Dễ tìm kiếm và filter
- Quản lý giá chính xác hơn
- Thống kê theo mác

✅ **Usage:**
```python
# Simple usage
code = generator.generate_work_code("Bê tông M200 dầm", "SEC-02")
# → S02-CONC-M200-0001
```
