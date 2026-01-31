# Quy Trình Xây Dựng Master Database

## Mục Đích

Giai đoạn này tập trung vào việc **xây dựng cơ sở dữ liệu công tác chuẩn (Master Database)** để làm nền tảng cho:

1. ✅ **Làm sạch và chuẩn hóa** dữ liệu từ nhiều BOQ files
2. ✅ **Chuẩn hóa đơn vị** (unit standardization)
3. ✅ **Phân loại nhóm** theo SEC codes
4. ✅ **Tạo nền tảng** cho matching và pricing BOQ tương lai

## Cấu Trúc Master Database

### Bảng: `master_work_items`

| Field | Type | Description |
|-------|------|-------------|
| `master_id` | Integer | ID duy nhất |
| `work_code` | String(50) | **Mã công tác chuẩn** (VD: DAO-DAT-MONG-0001) |
| `description` | Text | Mô tả công tác gốc |
| `description_normalized` | String(500) | Mô tả đã chuẩn hóa (lowercase, trim) |
| `sec_code` | String(20) | **Mã phân loại SEC** (VD: SEC-01-01) |
| `category` | String(100) | Danh mục chi tiết |
| `unit_standard` | String(20) | **Đơn vị chuẩn** (m, m2, m3, kg, ton, pcs, etc.) |
| `unit_variants` | Text | JSON array các biến thể đơn vị |
| `ref_unit_price_min` | Decimal | Giá tham khảo thấp nhất |
| `ref_unit_price_avg` | Decimal | **Giá trung bình** |
| `ref_unit_price_max` | Decimal | Giá tham khảo cao nhất |
| `occurrence_count` | Integer | Số lần xuất hiện |
| `source_files` | Text | JSON array các file_id nguồn |
| `is_verified` | Boolean | Đã được verify bởi user |

## Quy Trình

### 1️⃣ Upload BOQ Files

```bash
# Frontend: http://localhost:3000/upload
1. Select project
2. Upload Excel file
3. Verify column mapping
4. Process file
```

Kết quả:
- Line items được import vào `line_items` table
- Tự động phân loại SEC code (confidence >= 60%)
- Đánh dấu items cần review

### 2️⃣ Build Master Database

```bash
# Chạy script build master database
docker compose exec backend python build_master_database.py
```

Script sẽ:
- ✅ Đọc tất cả line items từ BOQ files đã upload
- ✅ Chuẩn hóa description (lowercase, trim, unicode normalization)
- ✅ Loại bỏ trùng lặp (deduplication dựa trên description + SEC code + unit)
- ✅ Tính giá tham khảo (min/avg/max)
- ✅ Đếm số lần xuất hiện
- ✅ Export CSV file

### 3️⃣ Kết Quả

**Database:**
- Bảng `master_work_items` chứa công tác chuẩn đã làm sạch
- Có thể query để tìm kiếm, filter, so sánh

**CSV Export:**
```
/app/master_work_items.csv
```

Ví dụ:
```csv
Work Code,Description,SEC Code,Unit,Min Price,Avg Price,Max Price,Occurrences
DAO-DAT-MONG-0001,Đào đất móng,SEC-01-01,m3,50000,75000,100000,5
TONG-COT-THEP-0002,Tường bê tông cốt thép,SEC-02,m2,1200000,1500000,1800000,3
```

## Tình Huống Sử Dụng

### A. Matching BOQ Mới

Khi upload BOQ mới:
1. System tìm kiếm trong master database
2. Match dựa trên description similarity + SEC code
3. Gợi ý công tác tương tự
4. Áp dụng giá tham khảo

### B. Price Benchmarking

So sánh giá:
```sql
SELECT
  work_code,
  description,
  ref_unit_price_avg,
  occurrence_count
FROM master_work_items
WHERE sec_code = 'SEC-01-01'
ORDER BY ref_unit_price_avg DESC;
```

### C. Quality Control

Verify master data:
1. Review items với `is_verified = false`
2. Chuẩn hóa thủ công nếu cần
3. Đánh dấu `is_verified = true`

## Thống Kê Hiện Tại

**Từ test run:**
```
Total Master Items: 20
  - SEC-00 (Preliminaries): 4 items
  - SEC-01-01 (Earthworks): 1 item
  - SEC-01-03 (Foundation): 1 item
  - SEC-03 (Finishes): 1 item
  - SEC-04 (MEP): 1 item
  - SEC-05 (Landscape): 12 items

Build Summary:
  Files processed: 3
  New items added: 20
  Items updated: 0
```

## Next Steps

### 1. Upload Real BOQ Files

Upload các file BOQ thực tế để build master database lớn hơn:
- BOQ-Semitech.xlsx (đã fix header detection)
- Các BOQ khác từ projects

### 2. Review & Verify

Kiểm tra và verify master data:
```bash
# Query unverified items
SELECT * FROM master_work_items
WHERE is_verified = false
ORDER BY occurrence_count DESC;
```

### 3. Enhance Classification

Cải thiện keywords cho SEC codes:
- Bổ sung keywords cho items chưa phân loại
- Tăng accuracy của auto-classification

### 4. Build Matching Algorithm

Tạo algorithm để:
- Match line items mới với master database
- Calculate similarity score
- Suggest best matches

## API Endpoints (Future)

```
GET  /api/v1/master-items/          # List master items
GET  /api/v1/master-items/{id}      # Get detail
POST /api/v1/master-items/search    # Search & match
PUT  /api/v1/master-items/{id}      # Update & verify
GET  /api/v1/master-items/stats     # Statistics
```

## File Locations

```
backend/app/models/master_work_item.py       # Model definition
backend/app/services/master_data_service.py  # Service logic
backend/build_master_database.py             # Build script
/app/master_work_items.csv                   # Exported data
```
