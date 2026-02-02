# HƯỚNG DẪN TOÀN DIỆN: HỆ THỐNG ĐA MÃ (MULTI-CODE SYSTEM)

## I. TỔNG QUAN KIẾN TRÚC

Hệ thống Cost Database sử dụng **kiến trúc 3 lớp mã hóa song song** để đảm bảo:
- ✅ Tương thích với pháp luật Việt Nam (Thông tư 12/2021/TT-BXD)
- ✅ Tương thích với chuẩn quốc tế (ISO 12006-2)
- ✅ Tích hợp liền mạch với BIM (Revit, ArchiCAD, etc.)
- ✅ Tra cứu linh hoạt, mở rộng dễ dàng

### Kiến trúc 3 lớp:

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: WORK CODE (Internal)                              │
│  Format: S01-EARTH-EXCAV-0001                               │
│  Purpose: Quản lý nội bộ, search, grouping                  │
└─────────────────────────────────────────────────────────────┘
                            ↕ (Mapping)
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2: LEGAL CODE (Thông tư 12/2021)                     │
│  Format: AA.1111a, AF.2345+, BA.5678-                       │
│  Purpose: Tuân thủ pháp lý, pricing, tender                 │
└─────────────────────────────────────────────────────────────┘
                            ↕ (Mapping)
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3: ISO CODE (ISO 12006-2)                            │
│  Format: Pr_21_31_13                                        │
│  Purpose: BIM integration, international compatibility      │
└─────────────────────────────────────────────────────────────┘
```

---

## II. CHI TIẾT TỪNG LỚP MÃ

### 1. WORK CODE (Mã Công Tác Nội Bộ)

**Format:** `{SEC_PREFIX}-{CATEGORY}-{SUB/GRADE}-{SEQUENCE}`

**Ví dụ:**
- `S01-EARTH-EXCAV-0001` - Đào đất
- `S02-CONC-M200-0015` - Bê tông M200
- `S03-WALL-BRICK-0008` - Tường gạch

**Nguyên tắc:**
1. **SEC_PREFIX**: 3 ký tự (S01, S02, S03...)
   - S00: Preliminaries
   - S01: Substructure
   - S02: Superstructure
   - S03: Architecture
   - S04: MEP
   - S05: Landscape

2. **CATEGORY**: Từ khóa chính (EARTH, CONC, WALL, TILE...)
   - Tối đa 6 ký tự
   - Viết hoa toàn bộ
   - Dễ nhận biết

3. **SUB/GRADE**: Sub-category hoặc Material Grade
   - EXCAV (Excavation), M200 (Grade), BRICK...
   - Optional nếu không có

4. **SEQUENCE**: 4 chữ số (0001-9999)
   - Auto-increment theo nhóm

**Ưu điểm:**
- ✅ Dễ đọc, dễ nhớ
- ✅ Tìm kiếm nhanh
- ✅ Sắp xếp logic
- ✅ Mở rộng không giới hạn

---

### 2. LEGAL CODE (Mã Định Mức Pháp Lý)

**Format:** `{PREFIX}.{NUMBER}{SUFFIX}`

**Ví dụ:**
- `AA.1111` - Công tác đất cơ bản
- `AF.2101a` - Bê tông biến thể a
- `BA.5678+` - Thiết kế mở rộng

**Cấu trúc PREFIX:**

| Prefix | Tên Công Tác | Phụ Lục | SEC Code |
|--------|--------------|---------|----------|
| **AA** | Công tác đất | I | SEC-01-01 |
| **AB** | Đào đắp đất máy | I | SEC-01-01 |
| **AC** | Công tác cọc | I | SEC-01-02 |
| **AE** | Công tác xây | I | SEC-03 |
| **AF** | Công tác bê tông | I | SEC-02 |
| **AG** | Công tác cốt thép | I | SEC-02 |
| **AH** | Ván khuôn | I | SEC-02 |
| **AI** | Kết cấu thép | I | SEC-02 |
| **AJ** | Hoàn thiện | I | SEC-03 |
| **AK** | Lợp mái | I | SEC-03 |
| **BA** | Thiết kế KT | II | SEC-00 |
| **BB** | Thiết kế KC | II | SEC-00 |
| **BC** | Thiết kế MEP | II | SEC-00 |
| **CA** | Khảo sát địa hình | III | SEC-00 |
| **CB** | Khảo sát địa chất | III | SEC-00 |

**SUFFIX:**
- `a, b, c...`: Biến thể kỹ thuật (variant)
- `+`: Mở rộng (extended)
- `-`: Thu gọn (reduced)
- `NULL`: Phiên bản gốc

**Quy tắc đặt tên tự nhiên (Natural Name):**

Theo nghiên cứu từ tài liệu, tên định mức chính thức cần chuyển sang tên "tự nhiên":

| Tên Chính Thức (Official) | Tên Tự Nhiên (Natural) |
|---------------------------|------------------------|
| Bê tông lót móng, chiều rộng <= 250cm, vữa PC30 | **Đổ bê tông lót móng - M100 đá 4x6** |
| Xây tường thẳng, dày > 33cm, gạch 6.5x10.5x22 | **Xây tường gạch ống - dày 330mm - vữa M75** |
| Đào đất hố móng bằng máy, sâu <= 1.25m | **Đào đất hố móng - 1.25m - đất cấp 3** |

**Nguyên tắc 6 ĐIỂM:**
1. ✅ Viết thường vị trí (móng, sàn, tường)
2. ✅ Dùng dấu gạch ngang (-) phân tách
3. ✅ Loại bỏ ký tự toán học (<, >, <=, >=)
4. ✅ Đưa thông số quan trọng (mác, quy cách) lên đầu
5. ✅ Ngắn gọn hơn 30%
6. ✅ Độ dài tối ưu: 40-80 ký tự

---

### 3. ISO CODE (Mã Phân Loại Quốc Tế)

**Format:** `{ENTITY}_{SYSTEM}_{ELEMENT}_{PRODUCT}`

**Ví dụ:**
- `Pr_21` - Công việc - Tường
- `Pr_21_31` - Công việc - Tường - Bê tông
- `Pr_21_31_20` - Công việc - Tường - Bê tông - M200

**Entity Types (Facet 1):**
- **Ss**: Spaces (Không gian)
- **Pr**: Processes (Công việc) ← Phổ biến nhất
- **El**: Elements (Bộ phận)
- **Ac**: Agents (Tác nhân)
- **Re**: Resources (Tài nguyên)

**System Codes (Facet 2):**

| Code | Hệ Thống | SEC Code |
|------|----------|----------|
| **01** | Móng | SEC-01-03 |
| **02** | Cọc | SEC-01-02 |
| **20** | Khung kết cấu | SEC-02 |
| **21** | Hệ thống tường | SEC-02 |
| **22** | Hệ thống sàn | SEC-02 |
| **23** | Hệ thống cột | SEC-02 |
| **24** | Hệ thống dầm | SEC-02 |
| **30** | Hoàn thiện tường | SEC-03 |
| **31** | Hoàn thiện sàn | SEC-03 |
| **32** | Hoàn thiện trần | SEC-03 |
| **40** | Điện | SEC-04 |
| **41** | Nước | SEC-04 |
| **42** | HVAC | SEC-04 |
| **60** | Cảnh quan | SEC-05 |

**Element Codes (Facet 3):**
- **30**: Bê tông
- **31**: Bê tông thương phẩm
- **21**: Thép
- **40**: Gạch
- **51**: Sơn
- **52**: Gạch lát

**Product Codes (Facet 4):**
- **10**: M100, **20**: M200, **30**: M300
- **50**: CB300, **51**: CB400

---

## III. DATABASE SCHEMA

### Bảng chính:

```sql
-- 1. master_work_items (Bảng công tác chuẩn)
CREATE TABLE master_work_items (
    master_id INT PRIMARY KEY,
    work_code VARCHAR(50) UNIQUE,      -- S01-EARTH-EXCAV-0001
    legal_code VARCHAR(30),             -- AA.1111
    iso_code VARCHAR(50),               -- Pr_21_31_13
    name_natural VARCHAR(500),          -- Tên tự nhiên
    description TEXT,                   -- Mô tả gốc
    sec_code VARCHAR(20),               -- SEC-01-01
    material_grade VARCHAR(20),         -- M200, CB300
    ...
);

-- 2. legal_work_codes (Mã định mức pháp lý)
CREATE TABLE legal_work_codes (
    legal_code VARCHAR(30) PRIMARY KEY,
    legal_code_prefix VARCHAR(5),       -- AA, AF, BA
    legal_code_number VARCHAR(10),      -- 1234
    legal_code_suffix VARCHAR(5),       -- a, +, -
    name_official_vn TEXT,              -- Tên chính thức
    name_natural_vn TEXT,               -- Tên tự nhiên
    ...
);

-- 3. iso_classification_codes (Mã ISO)
CREATE TABLE iso_classification_codes (
    iso_code VARCHAR(50) PRIMARY KEY,
    entity_code VARCHAR(10),            -- Pr, Ss, El
    system_code VARCHAR(10),            -- 21, 22
    element_code VARCHAR(10),           -- 31, 40
    product_code VARCHAR(10),           -- 13, 20
    ...
);

-- 4. work_code_mapping (Bảng ánh xạ 3 chiều)
CREATE TABLE work_code_mapping (
    mapping_id INT PRIMARY KEY,
    work_code VARCHAR(50),              -- Internal
    legal_code VARCHAR(30),             -- Legal
    iso_code VARCHAR(50),               -- ISO
    sec_code VARCHAR(20),               -- SEC
    confidence_score DECIMAL(5,2),      -- 0-100
    ...
);
```

---

## IV. API USAGE

### 1. Parse Legal Code

```bash
GET /api/v1/codes/legal/parse/AA.1111

Response:
{
  "legal_code": "AA.1111",
  "prefix": "AA",
  "number": "1111",
  "suffix": null,
  "category_vn": "Công tác đất",
  "appendix": "I",
  "suggested_sec_codes": ["SEC-01-01"]
}
```

### 2. Generate All Codes

```bash
POST /api/v1/codes/map/auto
{
  "description": "Đào đất hố móng bằng máy - 1.25m - đất cấp 3",
  "sec_code": "SEC-01-01",
  "unit": "m3"
}

Response:
{
  "work_code": "S01-EARTH-EXCAV-0001",
  "legal_code": "AB.1111",
  "iso_code": "Pr_01_10_01",
  "material_grade": null,
  "confidence_score": 85.0
}
```

### 3. Batch Mapping

```bash
POST /api/v1/codes/map/batch
[
  {"description": "Đào đất móng", "sec_code": "SEC-01-01"},
  {"description": "Đổ bê tông M200", "sec_code": "SEC-02"}
]
```

---

## V. MIGRATION GUIDE

### Bước 1: Thêm columns vào DB

```bash
cd backend
python migrate_to_multi_code_system.py --step 1
```

### Bước 2: Generate codes (DRY RUN)

```bash
python migrate_to_multi_code_system.py --step 2
```

### Bước 3: Apply changes (LIVE)

```bash
python migrate_to_multi_code_system.py --step 2 --live
```

---

## VI. USE CASES

### Use Case 1: Import BOQ từ Excel
```python
# 1. Classify line item
item = "Đào đất hố móng bằng máy"

# 2. Auto-generate all codes
codes = auto_map_codes(item)
# → work_code: S01-EARTH-EXCAV-0001
# → legal_code: AB.1111
# → iso_code: Pr_01_10_01

# 3. Save to database
save_to_master(codes)
```

### Use Case 2: Export to Tender
```python
# 1. Get all items
items = get_master_items()

# 2. Group by legal code prefix
grouped = group_by_legal_prefix(items)
# AA: Công tác đất
# AF: Công tác bê tông
# AG: Cốt thép

# 3. Export with legal names
export_with_legal_codes(grouped)
```

### Use Case 3: BIM Integration
```python
# 1. Extract from Revit
revit_objects = extract_from_revit()

# 2. Map to ISO codes
for obj in revit_objects:
    iso_code = generate_iso_code(obj)
    
# 3. Link to Legal codes
legal_code = map_iso_to_legal(iso_code)

# 4. Calculate pricing
price = get_unit_price(legal_code)
```

---

## VII. BEST PRACTICES

### 1. Naming Convention
- ✅ **Work Code**: Dùng cho quản lý nội bộ, search
- ✅ **Legal Code**: Dùng cho tender, pricing, official docs
- ✅ **ISO Code**: Dùng cho BIM, international collaboration

### 2. Search Strategy
```python
# Multi-code search
results = search_multi({
    "work_code": "S01-EARTH",    # Tìm theo internal code
    "legal_code": "AA",          # Tìm theo prefix
    "iso_code": "Pr_01",         # Tìm theo entity+system
    "keyword": "đào đất"         # Tìm theo description
})
```

### 3. Extension Strategy
```python
# Thêm prefix mới (VD: MEP chi tiết)
add_legal_prefix({
    "prefix": "AM",
    "name": "Công tác MEP đặc biệt",
    "appendix": "I",
    "sec_codes": ["SEC-04"]
})
```

---

## VIII. TROUBLESHOOTING

### Q1: Legal code trùng lặp?
**A:** Dùng suffix (a, b, c) để phân biệt biến thể

### Q2: ISO code quá dài?
**A:** Chỉ cần 2-3 levels (Pr_21_31 thay vì Pr_21_31_13)

### Q3: Migrate data cũ?
**A:** Chạy migration script với `--dry-run` trước

---

## IX. KẾT LUẬN

Hệ thống Multi-Code Architecture cung cấp:

1. ✅ **Tính linh hoạt**: 3 lớp mã độc lập, có thể extend
2. ✅ **Tương thích pháp lý**: Tuân thủ Thông tư 12/2021
3. ✅ **Tích hợp BIM**: Hỗ trợ ISO 12006-2
4. ✅ **Hiệu suất cao**: Index tối ưu, search nhanh
5. ✅ **Mở rộng dễ**: Thêm prefix/code mới không ảnh hưởng cũ

**Liên hệ:** Technical Support Team
**Version:** 1.0.0
**Last Updated:** 2026-02-02
