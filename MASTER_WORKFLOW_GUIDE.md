# Quản Lý Mã Danh Mục Công Tác Chuẩn Hóa (Master Work Items)

## 🎯 Mục Đích

Master Work Items là **danh mục công tác chuẩn hóa** làm nền tảng cho:
1. ✅ Tham khảo giá (price benchmarking)
2. ✅ Matching công tác giữa các BOQ
3. ✅ Chuẩn hóa description
4. ✅ Quản lý mã công tác (work code)

---

## 📍 Vị Trí Lưu Trữ

### Database
**Bảng:** `master_work_items`

**Cấu trúc:**
```sql
master_work_items
├── master_id (PK)
├── work_code (UNIQUE) ← Mã công tác chuẩn
├── description ← Mô tả gốc
├── description_normalized ← Mô tả chuẩn hóa (lowercase, trim)
├── sec_code ← Phân loại SEC
├── unit_standard ← Đơn vị chuẩn
├── ref_unit_price_min/avg/max ← Giá tham khảo
├── occurrence_count ← Số lần xuất hiện
├── source_files ← Files nguồn (JSON array)
├── is_verified ← Đã verify chưa
└── created_at, updated_at
```

### Frontend
- **URL:** `/master-items`
- **Component:** `MasterItems.tsx`

---

## 🔄 Workflow: Từ BOQ → Master Database

### Luồng Tự Động

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Upload BOQ File                                          │
│    • User upload Excel file                                 │
│    • System lưu vào boq_files table                        │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Process File                                             │
│    • Parse Excel → Extract line items                       │
│    • Auto-classify với SEC codes                           │
│    • Lưu vào line_items table                              │
│    • Option: auto_build_master = true                      │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Build Master Database (Nếu auto_build_master = true)    │
│    Cho mỗi line item:                                       │
│    ┌────────────────────────────────────────────┐          │
│    │ a. Normalize description                   │          │
│    │    • Lowercase                             │          │
│    │    • Remove extra spaces                   │          │
│    │    • Unicode normalization                 │          │
│    └────────────────┬───────────────────────────┘          │
│                     ▼                                       │
│    ┌────────────────────────────────────────────┐          │
│    │ b. Check if exists in master              │          │
│    │    WHERE description_normalized = ?        │          │
│    │      AND sec_code = ?                     │          │
│    │      AND unit = ?                         │          │
│    └────────────────┬───────────────────────────┘          │
│                     │                                       │
│         ┌───────────┴───────────┐                          │
│         ▼                       ▼                          │
│    ┌─────────┐           ┌──────────┐                     │
│    │ Tồn tại │           │ Chưa có  │                     │
│    └────┬────┘           └─────┬────┘                     │
│         │                      │                           │
│         ▼                      ▼                           │
│    ┌─────────────────┐   ┌─────────────────────────────┐ │
│    │ UPDATE EXISTING │   │ CREATE NEW                   │ │
│    │                 │   │                               │ │
│    │ • occurrence++  │   │ • Generate work_code         │ │
│    │ • Update prices │   │ • Set description            │ │
│    │ • Add file_id   │   │ • Set sec_code, unit        │ │
│    │   to sources    │   │ • Set prices (min/avg/max)  │ │
│    │                 │   │ • occurrence_count = 1       │ │
│    │                 │   │ • source_files = [file_id]   │ │
│    └─────────────────┘   │ • is_verified = false        │ │
│                          └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Kết Quả                                                  │
│    • Master database được update                            │
│    • Work codes được generate tự động                       │
│    • Giá tham khảo được tính toán                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 Chi Tiết Logic

### 1. Normalize Description

**Input:** `"  Bê TÔNG  M200  dầm  "`

**Process:**
```python
def normalize_description(text: str) -> str:
    # Unicode normalization
    text = unicodedata.normalize('NFC', text)

    # Lowercase
    text = text.lower()

    # Remove extra spaces
    text = ' '.join(text.split())

    return text.strip()
```

**Output:** `"bê tông m200 dầm"`

### 2. Find Similar Master

**Matching Criteria:**
1. ✅ Description chuẩn hóa **giống hệt**
2. ✅ SEC code **giống nhau**
3. ✅ Unit **giống nhau**

```python
def _find_similar_master(
    description_normalized: str,
    sec_code: str,
    unit: str
) -> Optional[MasterWorkItem]:
    # Exact match
    return db.query(MasterWorkItem).filter(
        MasterWorkItem.description_normalized == description_normalized,
        MasterWorkItem.sec_code == sec_code,
        MasterWorkItem.unit_standard == unit
    ).first()
```

**Note:** Hiện tại là exact match. Có thể nâng cấp lên fuzzy matching sau.

### 3. Update Existing Master

**Khi tìm thấy master item tồn tại:**

```python
def _update_master_item(master: MasterWorkItem, item: LineItem):
    # 1. Tăng số lần xuất hiện
    master.occurrence_count += 1

    # 2. Update source files
    sources = json.loads(master.source_files)
    if item.file_id not in sources:
        sources.append(item.file_id)
        master.source_files = json.dumps(sources)

    # 3. Update giá tham khảo
    if item.unit_price > 0:
        # Update min price
        if master.ref_unit_price_min is None or item.unit_price < master.ref_unit_price_min:
            master.ref_unit_price_min = item.unit_price

        # Update max price
        if master.ref_unit_price_max is None or item.unit_price > master.ref_unit_price_max:
            master.ref_unit_price_max = item.unit_price

        # Recalculate average price
        count = master.occurrence_count
        master.ref_unit_price_avg = (
            (master.ref_unit_price_avg * (count - 1) + item.unit_price) / count
        )
```

**Kết quả:**
- ✅ Occurrence count tăng lên
- ✅ Source files được thêm vào
- ✅ Giá min/max/avg được update

### 4. Create New Master

**Khi chưa có trong master:**

```python
# Generate work code
work_code = code_generator.generate_work_code(
    description=item.description,
    sec_code=item.sec_code,
    unit=item.unit
)

# Create master item
master_item = MasterWorkItem(
    work_code=work_code,                    # S02-CONC-M200-0001
    description=item.description,           # "Bê tông M200 dầm"
    description_normalized=desc_normalized, # "bê tông m200 dầm"
    sec_code=item.sec_code,                # "SEC-02"
    unit_standard=item.unit,               # "m3"
    ref_unit_price_min=item.unit_price,    # 1,500,000
    ref_unit_price_max=item.unit_price,    # 1,500,000
    ref_unit_price_avg=item.unit_price,    # 1,500,000
    occurrence_count=1,                     # Lần đầu xuất hiện
    source_files=json.dumps([file_id]),    # [5]
    is_verified=False                       # Chưa verify
)
```

---

## 🎯 Các Trường Hợp Sử Dụng

### Case 1: Upload BOQ Đầu Tiên

**Input:** BOQ-001.xlsx với 100 công tác

**Process:**
```
1. Upload file → file_id = 1
2. Process file → 100 line items
3. Build master → Check master database
4. Result: Master database RỖNG
   → Tạo mới 100 master items
   → Generate 100 work codes
```

**Output:**
- 100 master items mới
- Occurrence count = 1 cho tất cả
- Source files = [1] cho tất cả

### Case 2: Upload BOQ Thứ 2 (Có Trùng)

**Input:** BOQ-002.xlsx với 120 công tác
- 80 công tác giống BOQ-001
- 40 công tác mới

**Process:**
```
1. Upload file → file_id = 2
2. Process file → 120 line items
3. Build master → Check từng item
   a. 80 items: Tìm thấy trong master
      → UPDATE: occurrence++, update prices, add file_id
   b. 40 items: Không tìm thấy
      → CREATE: 40 master items mới
```

**Output:**
- 80 master items: occurrence = 2, sources = [1, 2]
- 40 master items mới: occurrence = 1, sources = [2]
- Total: 140 master items

### Case 3: Upload BOQ Thứ 3 (Giá Khác Nhau)

**Input:** BOQ-003.xlsx
- "Bê tông M200 dầm": 1,650,000 VND (cao hơn)

**Existing Master:**
```
work_code: S02-CONC-M200-0001
description: "Bê tông M200 dầm"
ref_unit_price_min: 1,500,000
ref_unit_price_avg: 1,500,000
ref_unit_price_max: 1,500,000
occurrence_count: 2
```

**Process:**
```
1. Find existing: FOUND
2. Update prices:
   min = 1,500,000 (unchanged)
   max = 1,650,000 (new max!)
   avg = (1,500,000 * 2 + 1,650,000) / 3 = 1,550,000
3. Update occurrence: 3
```

**Result:**
```
work_code: S02-CONC-M200-0001
ref_unit_price_min: 1,500,000 ← min
ref_unit_price_avg: 1,550,000 ← avg
ref_unit_price_max: 1,650,000 ← max
occurrence_count: 3
source_files: [1, 2, 3]
```

---

## 🔧 Cách Sử Dụng

### Option 1: Auto-Build Khi Upload

**Frontend:**
```typescript
// File upload with auto-build
const result = await fileService.processFile(fileId, {
  column_mapping: {...},
  auto_build_master: true  // ← Enable auto-build
})

console.log(result.master_build)
// {
//   added: 45,
//   updated: 35,
//   skipped: 0
// }
```

**Backend API:**
```bash
curl -X POST "http://localhost:8000/api/v1/files/5/process" \
  -H "Content-Type: application/json" \
  -d '{
    "column_mapping": {...},
    "auto_build_master": true
  }'
```

### Option 2: Manual Build

**Frontend:**
```typescript
// Build from specific file
const result = await masterItemsService.buildFromFile({
  file_id: 5,
  min_confidence: 60.0,
  skip_unclassified: false
})

console.log(`Added: ${result.added}`)
console.log(`Updated: ${result.updated}`)
```

**Backend API:**
```bash
curl -X POST "http://localhost:8000/api/v1/master-items/build" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": 5,
    "min_confidence": 60.0,
    "skip_unclassified": false
  }'
```

### Option 3: CLI Script

**Run Script:**
```bash
docker compose exec backend python build_master_database.py
```

**Output:**
```
=== Building Master Database from 3 BOQ files ===

Processing: BOQ-001.xlsx (ID: 1)
  Total rows: 100
  ✓ Added: 85
  ✓ Updated: 0
  ✗ Skipped: 15

Processing: BOQ-002.xlsx (ID: 2)
  Total rows: 120
  ✓ Added: 40
  ✓ Updated: 80
  ✗ Skipped: 0

=== MASTER DATABASE STATISTICS ===
Total Master Items: 125
  - Verified: 0
  - Unverified: 125

Distribution by SEC Code:
  SEC-01: 25 items
  SEC-02: 30 items
  SEC-03: 35 items
  SEC-04: 15 items
  SEC-05: 20 items

✓ Master data exported to: /app/master_work_items.csv
```

---

## 📊 Quản Lý Master Items

### 1. Xem Danh Sách

**Frontend:** `/master-items`

**Features:**
- ✅ List tất cả master items
- ✅ Search theo description
- ✅ Filter theo SEC code
- ✅ Filter verified/unverified
- ✅ Xem occurrence count
- ✅ Xem giá min/avg/max

### 2. Verify Master Items

**Purpose:** Review và xác nhận master items đã chuẩn

**Process:**
```
1. Go to /master-items
2. Filter: Unverified items
3. Review description, work code, prices
4. Click Edit
5. Set is_verified = true
6. Save
```

**API:**
```bash
curl -X PUT "http://localhost:8000/api/v1/master-items/123" \
  -H "Content-Type: application/json" \
  -d '{
    "is_verified": true
  }'
```

### 3. Edit Master Items

**Khi nào cần edit:**
- ❌ Description sai chính tả
- ❌ SEC code không đúng
- ❌ Unit không chuẩn
- ❌ Work code cần regenerate

**Process:**
```
1. Find item cần edit
2. Click Edit button
3. Update fields
4. System tự động:
   - Re-normalize description
   - Có thể regenerate work code (option)
5. Save
```

### 4. Delete Master Items

**Khi nào cần delete:**
- ❌ Item bị duplicate
- ❌ Item không hợp lệ
- ❌ Test data cần xóa

**Process:**
```
1. Find item
2. Click Delete
3. Confirm
4. System: Soft delete (is_active = false)
```

**Note:** Không xóa hẳn khỏi database, chỉ đánh dấu inactive.

---

## 🔍 Tìm Kiếm & Matching

### Search by Description

```sql
SELECT * FROM master_work_items
WHERE description_normalized LIKE '%bê tông%'
  AND is_active = true;
```

### Search by Work Code Pattern

```sql
-- All concrete items
SELECT * FROM master_work_items
WHERE work_code LIKE 'S02-CONC-%';

-- All M200 materials
SELECT * FROM master_work_items
WHERE work_code LIKE '%-M200-%';
```

### Find by Price Range

```sql
SELECT * FROM master_work_items
WHERE ref_unit_price_avg BETWEEN 1000000 AND 2000000
  AND sec_code = 'SEC-02';
```

---

## 📈 Thống Kê

### Tổng Quan

**URL:** `/master-statistics`

**Metrics:**
- Total master items
- Verified vs Unverified
- Distribution by SEC code
- Distribution by material grade
- Verification rate

### By SEC Code

```sql
SELECT
  sec_code,
  COUNT(*) as count,
  AVG(ref_unit_price_avg) as avg_price,
  COUNT(CASE WHEN is_verified THEN 1 END) as verified_count
FROM master_work_items
WHERE is_active = true
GROUP BY sec_code
ORDER BY sec_code;
```

### Top Items by Occurrence

```sql
SELECT
  work_code,
  description,
  occurrence_count,
  ref_unit_price_avg
FROM master_work_items
WHERE is_active = true
ORDER BY occurrence_count DESC
LIMIT 20;
```

---

## 🎯 Best Practices

### 1. Upload BOQ Mới

✅ **DO:**
- Enable auto_build_master khi process file
- Review unverified items sau khi build
- Verify items có occurrence_count cao

❌ **DON'T:**
- Upload duplicate files
- Skip verification hoàn toàn
- Ignore items với confidence thấp

### 2. Maintain Master Database

**Weekly:**
- Review unverified items (occurrence_count > 5)
- Check for duplicates
- Verify top 20 items

**Monthly:**
- Export master database backup
- Review price trends
- Clean up inactive items

### 3. Data Quality

**Ensure:**
- Descriptions có mác vật liệu (M200, B25, etc.)
- SEC codes được classify đúng
- Units được chuẩn hóa (m3, m2, pcs)
- Prices hợp lý (không có outliers)

---

## 🔄 Future Enhancements

### Fuzzy Matching

Thay vì exact match, dùng similarity score:

```python
def _find_similar_master(description, sec_code, unit, threshold=0.85):
    # Use Levenshtein distance or cosine similarity
    candidates = db.query(MasterWorkItem).filter(
        MasterWorkItem.sec_code == sec_code,
        MasterWorkItem.unit_standard == unit
    ).all()

    for candidate in candidates:
        similarity = calculate_similarity(
            description,
            candidate.description_normalized
        )
        if similarity >= threshold:
            return candidate

    return None
```

### Auto-Merge Duplicates

Detect và merge các master items tương tự:

```python
def detect_duplicates():
    # Find items with high similarity
    # Suggest merge to user
    # Auto-merge if confidence > 95%
    pass
```

### Machine Learning Classification

Dùng ML để:
- Auto-classify SEC codes
- Suggest work code categories
- Detect anomalies in prices

---

## ✅ Summary

**Master Database Workflow:**

1. **Upload BOQ** → System lưu vào `boq_files`
2. **Process File** → Extract `line_items`
3. **Build Master** (auto hoặc manual):
   - Check existing: description + SEC + unit
   - **Tồn tại** → Update occurrence, prices, sources
   - **Chưa có** → Create new, generate work code
4. **Review** → Verify master items qua UI
5. **Use** → Reference cho BOQs tiếp theo

**Quản lý tại:**
- Frontend: `/master-items`
- API: `/api/v1/master-items`
- Database: `master_work_items` table

**Mọi thứ đã tự động!** ✅
