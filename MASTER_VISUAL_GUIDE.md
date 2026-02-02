# Master Database Workflow - Visual Guide

## 🎯 Quy Trình Tổng Quan

```
┌─────────────────────────────────────────────────────────────┐
│                    UPLOAD BOQ FILE                          │
│                    (Excel/CSV)                              │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │  boq_files     │  ← Lưu metadata file
         │  - file_id     │
         │  - file_name   │
         │  - file_hash   │
         └────────┬───────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              PROCESS & EXTRACT LINE ITEMS                   │
│  • Parse Excel                                              │
│  • Clean data                                               │
│  • Auto-classify SEC codes                                  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │  line_items    │  ← Raw data từ BOQ
         │  - description │
         │  - unit        │
         │  - unit_price  │
         │  - sec_code    │
         └────────┬───────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│           BUILD MASTER DATABASE                             │
│  (auto_build_master = true)                                │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │  FOR EACH LINE ITEM         │
    └─────────────┬───────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │  1. NORMALIZE DESCRIPTION   │
    │  "  Bê TÔNG M200  "        │
    │         ↓                   │
    │  "bê tông m200"            │
    └─────────────┬───────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │  2. CHECK IF EXISTS         │
    │  WHERE:                     │
    │  - description_normalized   │
    │  - sec_code                │
    │  - unit                    │
    └─────────────┬───────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
   ┌─────────┐         ┌─────────┐
   │  FOUND  │         │ NOT FOUND│
   └────┬────┘         └────┬────┘
        │                   │
        ▼                   ▼
┌───────────────┐    ┌──────────────────┐
│ UPDATE        │    │ CREATE NEW       │
│               │    │                  │
│ occurrence++  │    │ Generate code    │
│ Update prices │    │ S02-CONC-M200-.. │
│ Add file_id   │    │                  │
│ source_files  │    │ Set description  │
│               │    │ Set prices       │
│               │    │ occurrence = 1   │
└───────┬───────┘    └────────┬─────────┘
        │                     │
        └──────────┬──────────┘
                   ▼
         ┌──────────────────┐
         │ master_work_items│  ← DANH MỤC CHUẨN
         │                  │
         │ - work_code      │  ← MÃ CÔNG TÁC
         │ - description    │
         │ - sec_code       │
         │ - unit_standard  │
         │ - price_min/avg  │
         │ - occurrence     │
         │ - source_files   │
         │ - is_verified    │
         └──────────────────┘
```

---

## 📊 Example Flow: 3 BOQ Files

### BOQ #1: First Upload

```
INPUT: BOQ-Project-A.xlsx
├── "Bê tông M200 dầm" | SEC-02 | m3 | 1,500,000
├── "Tường gạch"       | SEC-03 | m2 | 180,000
└── "Đào đất móng"     | SEC-01 | m3 | 75,000

PROCESS:
1. Parse → 3 line items
2. Check master → EMPTY
3. Create 3 new masters

RESULT: master_work_items
┌──────────────────────┬─────────┬────┬───────────┬─────┬──────────┐
│ Work Code            │ Desc    │ SEC│ Price Avg │ Occ │ Sources  │
├──────────────────────┼─────────┼────┼───────────┼─────┼──────────┤
│ S02-CONC-M200-0001  │ BT M200 │ 02 │ 1,500,000 │  1  │ [1]      │
│ S03-WALL-BRICK-0001 │ T.gạch  │ 03 │   180,000 │  1  │ [1]      │
│ S01-EARTH-EXCAV-0001│ Đào đất │ 01 │    75,000 │  1  │ [1]      │
└──────────────────────┴─────────┴────┴───────────┴─────┴──────────┘
```

### BOQ #2: Second Upload (Có Trùng)

```
INPUT: BOQ-Project-B.xlsx
├── "Bê tông M200 dầm" | SEC-02 | m3 | 1,550,000  ← Trùng (giá khác)
├── "Tường gạch"       | SEC-03 | m2 | 175,000    ← Trùng (giá khác)
├── "Cột bê tông B25"  | SEC-02 | m3 | 1,650,000  ← MỚI
└── "Sơn tường"        | SEC-03 | m2 | 35,000     ← MỚI

PROCESS:
1. Parse → 4 line items
2. Check master:
   a. "Bê tông M200" → FOUND (S02-CONC-M200-0001)
      → UPDATE: occurrence=2, avg=(1,500,000+1,550,000)/2=1,525,000
   b. "Tường gạch" → FOUND (S03-WALL-BRICK-0001)
      → UPDATE: occurrence=2, avg=177,500
   c. "Cột bê tông B25" → NOT FOUND
      → CREATE: S02-CONC-M250-0001
   d. "Sơn tường" → NOT FOUND
      → CREATE: S03-PAINT-0001

RESULT: master_work_items
┌──────────────────────┬─────────┬────┬───────────┬─────┬──────────┐
│ Work Code            │ Desc    │ SEC│ Price Avg │ Occ │ Sources  │
├──────────────────────┼─────────┼────┼───────────┼─────┼──────────┤
│ S02-CONC-M200-0001  │ BT M200 │ 02 │ 1,525,000 │  2  │ [1,2]    │ ← UPDATED
│ S03-WALL-BRICK-0001 │ T.gạch  │ 03 │   177,500 │  2  │ [1,2]    │ ← UPDATED
│ S01-EARTH-EXCAV-0001│ Đào đất │ 01 │    75,000 │  1  │ [1]      │
│ S02-CONC-M250-0001  │ Cột B25 │ 02 │ 1,650,000 │  1  │ [2]      │ ← NEW
│ S03-PAINT-0001      │ Sơn     │ 03 │    35,000 │  1  │ [2]      │ ← NEW
└──────────────────────┴─────────┴────┴───────────┴─────┴──────────┘
```

### BOQ #3: Third Upload

```
INPUT: BOQ-Project-C.xlsx
├── "Bê tông M200 dầm" | SEC-02 | m3 | 1,600,000  ← Trùng (lần 3)
├── "Đào đất móng"     | SEC-01 | m3 | 80,000     ← Trùng (giá cao hơn)
└── "Lát gạch nền"     | SEC-03 | m2 | 120,000    ← MỚI

PROCESS:
1. "Bê tông M200" → FOUND
   → UPDATE:
      occurrence = 3
      min = 1,500,000 (unchanged)
      avg = (1,500,000 + 1,550,000 + 1,600,000) / 3 = 1,550,000
      max = 1,600,000 (new max)
      sources = [1, 2, 3]

2. "Đào đất" → FOUND
   → UPDATE:
      occurrence = 2
      min = 75,000
      avg = (75,000 + 80,000) / 2 = 77,500
      max = 80,000

3. "Lát gạch" → NOT FOUND
   → CREATE: S03-TILE-FLOOR-0001

RESULT: master_work_items
┌──────────────────────┬─────────┬────┬─────────────────────────────┬─────┬──────────┐
│ Work Code            │ Desc    │ SEC│ Min    │ Avg       │ Max   │ Occ │ Sources  │
├──────────────────────┼─────────┼────┼────────┼───────────┼───────┼─────┼──────────┤
│ S02-CONC-M200-0001  │ BT M200 │ 02 │1,500K  │ 1,550,000 │1,600K │  3  │ [1,2,3]  │
│ S03-WALL-BRICK-0001 │ T.gạch  │ 03 │  175K  │   177,500 │  180K │  2  │ [1,2]    │
│ S01-EARTH-EXCAV-0001│ Đào đất │ 01 │   75K  │    77,500 │   80K │  2  │ [1,3]    │
│ S02-CONC-M250-0001  │ Cột B25 │ 02 │1,650K  │ 1,650,000 │1,650K │  1  │ [2]      │
│ S03-PAINT-0001      │ Sơn     │ 03 │   35K  │    35,000 │   35K │  1  │ [2]      │
│ S03-TILE-FLOOR-0001 │ Lát g   │ 03 │  120K  │   120,000 │  120K │  1  │ [3]      │
└──────────────────────┴─────────┴────┴────────┴───────────┴───────┴─────┴──────────┘

INSIGHTS:
✅ "Bê tông M200" xuất hiện 3 lần → Công tác phổ biến
✅ Giá dao động 1,500K-1,600K → Tham khảo: 1,550K
✅ "Lát gạch" chỉ 1 lần → Cần thêm data
```

---

## 🎯 Các Tình Huống Thực Tế

### Scenario 1: Description Khác Nhau Một Chút

```
Line Item 1: "Bê tông M200 dầm"
Line Item 2: "Bê  tông   M200  dầm  "  ← Extra spaces

Normalize:
  "bê tông m200 dầm"
  "bê tông m200 dầm"  ← SAME!

Result: MATCH → Update existing master
```

### Scenario 2: Description Giống Nhưng Unit Khác

```
Line Item 1: "Tường gạch" | unit: m2
Line Item 2: "Tường gạch" | unit: m3  ← Different unit

Check:
  description_normalized: "tường gạch" ← SAME
  sec_code: SEC-03 ← SAME
  unit: m2 vs m3 ← DIFFERENT!

Result: NO MATCH → Create 2 separate masters
  - S03-WALL-BRICK-0001 (m2)
  - S03-WALL-BRICK-0002 (m3)
```

### Scenario 3: Description Giống Nhưng SEC Khác

```
Line Item 1: "Đào đất" | SEC-01-01 (Earthworks)
Line Item 2: "Đào đất" | SEC-01-03 (Foundation excavation)

Check:
  description_normalized: "đào đất" ← SAME
  sec_code: SEC-01-01 vs SEC-01-03 ← DIFFERENT!

Result: NO MATCH → Create 2 separate masters
  - S01-EARTH-EXCAV-0001 (SEC-01-01)
  - S01-FOUND-EXCAV-0001 (SEC-01-03)
```

### Scenario 4: Duplicate Trong Cùng File

```
BOQ-001.xlsx:
  Row 10: "Bê tông M200 dầm" | 1,500,000
  Row 50: "Bê tông M200 dầm" | 1,500,000  ← Duplicate

Process:
1. Row 10 → Check master → NOT FOUND
   → CREATE: S02-CONC-M200-0001 (occurrence=1)

2. Row 50 → Check master → FOUND!
   → UPDATE: S02-CONC-M200-0001 (occurrence=2)

Result: 1 master item, occurrence = 2
```

---

## 📍 Vị Trí Quản Lý

### 1. Database

```sql
-- View all masters
SELECT * FROM master_work_items WHERE is_active = true;

-- Most common items
SELECT work_code, description, occurrence_count
FROM master_work_items
ORDER BY occurrence_count DESC
LIMIT 10;

-- Items needing verification
SELECT * FROM master_work_items
WHERE is_verified = false
  AND occurrence_count >= 3
ORDER BY occurrence_count DESC;
```

### 2. Frontend UI

**URL:** `/master-items`

```
┌─────────────────────────────────────────────────────────┐
│ [Total: 150] [Verified: 45] [Unverified: 105]         │
├─────────────────────────────────────────────────────────┤
│ Master Work Items Database      [Export CSV] [Refresh] │
├─────────────────────────────────────────────────────────┤
│ Search: [_____________] SEC: [All ▼] Status: [All ▼]  │
├──────┬───────────────┬──────┬────┬──────────┬──────────┤
│ Code │ Description   │ SEC  │ Un │ Avg Price│ Occur    │
├──────┼───────────────┼──────┼────┼──────────┼──────────┤
│ S02..│ Bê tông M200  │ 02   │ m3 │1,550,000 │ 3 ⭐     │
│ S03..│ Tường gạch    │ 03   │ m2 │  177,500 │ 2        │
│ S01..│ Đào đất       │ 01   │ m3 │   77,500 │ 2        │
└──────┴───────────────┴──────┴────┴──────────┴──────────┘

⭐ = High occurrence (commonly used)
```

### 3. API

```bash
# List all masters
GET /api/v1/master-items/

# Get statistics
GET /api/v1/master-items/statistics

# Build from file
POST /api/v1/master-items/build
{
  "file_id": 5,
  "min_confidence": 60.0
}

# Search by pattern
GET /api/v1/master-items/search/by-code?code_pattern=S02-*
```

---

## ✅ Summary

**Câu trả lời cho câu hỏi:**

> "Quản lý các mã danh mục công tác chuẩn hóa ở đâu?"

**📍 Vị trí:**
- **Database:** Bảng `master_work_items`
- **Frontend:** `/master-items` (UI quản lý)
- **API:** `/api/v1/master-items/*`

**🔄 Logic:**
1. ✅ **Nếu tồn tại:** Update occurrence, prices, sources
2. ✅ **Nếu chưa có:** Tạo mới + generate work code

**🎯 Matching Criteria:**
- Description chuẩn hóa (normalized)
- SEC code
- Unit

**Mọi thứ tự động khi upload BOQ!** 🚀
