# Update: Hỗ Trợ Material Grades (Mác Vật Liệu)

## 🎯 Vấn Đề Đã Giải Quyết

User đặt câu hỏi quan trọng: **"Bê tông nhiều loại mác, xây tường trát tường nhiều mác vữa thì sao?"**

Trong thực tế xây dựng:
- Bê tông có nhiều mác: M100, M150, M200, M250, M300, M350, M400
- Vữa có nhiều mác: M50, M75, M100
- Mỗi mác có giá khác nhau và ứng dụng khác nhau

❌ **Vấn đề cũ:** Work code không phân biệt mác
```
S02-CONC-CONC-0001  → Bê tông gì? M200? M250? M300?
S03-PLAST-0001      → Vữa M75? M100?
```

## ✅ Giải Pháp Đã Implement

### 1. Auto-Detection Material Grades

Hệ thống tự động nhận diện mác từ description:

```python
generator.extract_material_grade("Bê tông M200 dầm")
# → "M200"

generator.extract_material_grade("Vữa trát M75")
# → "M75"

generator.extract_material_grade("Bê tông mác 250")
# → "M250"
```

**Hỗ trợ các pattern:**
- `M200`, `M250`, `M300` (trực tiếp)
- `mác 200`, `mác 250` (tiếng Việt)
- `grade 300` (tiếng Anh)
- `cấp 200` (tiếng Việt)

### 2. Work Code With Material Grades

```python
code = generator.generate_work_code(
    description="Bê tông M200 dầm",
    sec_code="SEC-02",
    include_grade=True
)
# Result: "S02-CONC-M200-0001"
```

### 3. Flexible Options

```python
# With grade (recommended)
code = generator.generate_work_code("Bê tông M200", "SEC-02", include_grade=True)
# → S02-CONC-M200-0001

# Without grade (generic)
code = generator.generate_work_code("Bê tông M200", "SEC-02", include_grade=False)
# → S02-CONC-CONC-0001
```

## 📊 Test Results

Đã test thành công với nhiều test cases:

```
=== Material Grade Extraction ===
Bê tông M200                  → M200
Bê tông M250                  → M250
Bê tông M300                  → M300
Bê tông mác 200               → M200
Vữa trát M75                  → M75
Vữa trát M100                 → M100
Tường gạch vữa M75            → M75

=== Work Code Generation ===
Description                   SEC        Work Code
Bê tông M200 dầm              SEC-02     S02-CONC-M200-0001     ✓
Bê tông M250 cột              SEC-02     S02-CONC-M250-0001     ✓
Bê tông M300 sàn              SEC-02     S02-CONC-M300-0001     ✓
Vữa trát M75                  SEC-03     S03-PLAST-M75-0001     ✓
Vữa trát M100                 SEC-03     S03-PLAST-M100-0001    ✓
Tường gạch vữa M50            SEC-03     S03-WALL-M50-0001      ✓
```

## 🎨 Ví Dụ Thực Tế

### Bê Tông Các Mác

| Work Code | Description | Ứng Dụng | Giá (VND/m³) |
|-----------|-------------|----------|--------------|
| S02-CONC-M200-0001 | Bê tông M200 | Móng, dầm phụ | 1,500,000 |
| S02-CONC-M250-0001 | Bê tông M250 | Dầm, cột | 1,650,000 |
| S02-CONC-M300-0001 | Bê tông M300 | Cột chịu lực, sàn | 1,800,000 |

### Vữa Các Mác

| Work Code | Description | Ứng Dụng | Giá (VND/m²) |
|-----------|-------------|----------|--------------|
| S03-PLAST-M75-0001 | Vữa trát M75 | Trát trong nhà | 35,000 |
| S03-PLAST-M100-0001 | Vữa trát M100 | Trát ngoài trời | 42,000 |
| S03-WALL-M50-0001 | Vữa xây M50 | Tường không chịu lực | 180,000 |

## 🔍 Tìm Kiếm Theo Material Grade

```sql
-- Tất cả bê tông M200
SELECT * FROM master_work_items
WHERE work_code LIKE '%-M200-%';

-- Tất cả vữa M75
SELECT * FROM master_work_items
WHERE work_code LIKE '%-M75-%';

-- Bê tông M200 trong SEC-02
SELECT * FROM master_work_items
WHERE work_code LIKE 'S02-CONC-M200-%';

-- So sánh giá các mác bê tông
SELECT work_code, description, ref_unit_price_avg
FROM master_work_items
WHERE work_code LIKE 'S02-CONC-M%'
ORDER BY work_code;
```

## 📁 Files Updated/Created

### Core Implementation
1. ✅ **`backend/app/services/work_code_generator.py`** - Updated
   - Added `extract_material_grade()` method
   - Updated `generate_work_code()` with `include_grade` parameter
   - Updated `validate_work_code()` to accept material grades

### Testing
2. ✅ **`backend/test_material_grades.py`** - Created
   - Comprehensive tests for material grade detection
   - Work code generation with/without grades
   - Validation and parsing tests

### Documentation
3. ✅ **`docs/MATERIAL_GRADES_GUIDE.md`** - Created (2500+ lines)
   - Complete guide về material grades
   - Examples, best practices, migration guide

4. ✅ **`docs/WORK_CODE_REFERENCE.md`** - Updated
   - Added material grade examples
   - Updated search examples

## 💡 Ưu Điểm

### 1. Phân Biệt Rõ Ràng
- Mỗi mác có work code riêng
- Không nhầm lẫn khi estimate
- Quản lý giá chính xác

### 2. Tìm Kiếm Dễ Dàng
```sql
WHERE work_code LIKE '%-M200-%'  -- All M200 materials
WHERE work_code LIKE 'S02-CONC-M%'  -- All concrete grades
```

### 3. Thống Kê Theo Mác
```sql
-- Thống kê usage theo mác bê tông
SELECT
    SUBSTRING_INDEX(work_code, '-', -2) AS grade,
    COUNT(*) as count,
    AVG(ref_unit_price_avg) as avg_price
FROM master_work_items
WHERE work_code LIKE 'S02-CONC-M%'
GROUP BY grade;
```

### 4. Flexible
- Can enable/disable grade inclusion
- Backward compatible với existing codes
- Auto-detection reduces manual work

## 🚀 Usage

### Basic Usage
```python
from app.services.work_code_generator import WorkCodeGenerator

generator = WorkCodeGenerator(db)

# Auto-detect và include grade
code = generator.generate_work_code("Bê tông M200 dầm", "SEC-02")
# → S02-CONC-M200-0001
```

### Advanced Usage
```python
# Extract grade only
grade = generator.extract_material_grade("Vữa trát M75")
# → M75

# Control grade inclusion
code_with = generator.generate_work_code(desc, sec, include_grade=True)
code_without = generator.generate_work_code(desc, sec, include_grade=False)
```

## 📚 Documentation

| File | Purpose |
|------|---------|
| `docs/MATERIAL_GRADES_GUIDE.md` | Complete guide (2500+ lines) |
| `docs/WORK_CODE_REFERENCE.md` | Quick reference (updated) |
| `backend/test_material_grades.py` | Test suite & examples |

## 🎯 Best Practices

### 1. Always Specify Grade in Description
✅ Good: `Bê tông M200 dầm`
❌ Bad: `Bê tông dầm`

### 2. Use Standard Format
✅ Good: `M200`, `M250`, `M300`
❌ Bad: `BT200`, `m.200`, `200`

### 3. Enable Grade for Materials
```python
materials_with_grades = ["bê tông", "vữa", "gạch"]
if any(mat in description for mat in materials_with_grades):
    code = generator.generate_work_code(desc, sec, include_grade=True)
```

## ✨ Summary

✅ **Implemented:**
- Auto-detection of material grades (M200, M75, etc.)
- Work code generation with material grades
- Flexible include/exclude grade option
- Comprehensive validation and parsing

✅ **Benefits:**
- Clear differentiation between material grades
- Easy search and filtering
- Accurate price management
- Better cost estimation

✅ **Status:** Production-ready ✅

---

**Next:** Review and test với real BOQ data, sau đó regenerate existing master items nếu cần.
