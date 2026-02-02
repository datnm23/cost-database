# Integration Guide: Work Code System

## 🎯 Tổng Quan

Work Code System đã được tích hợp hoàn chỉnh vào hệ thống BOQ của bạn.

---

## ✅ Những Gì Đã Tích Hợp

### 1. Backend API Endpoints

**Base URL:** `/api/v1/master-items`

#### ✅ Endpoints Available:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | List master items (with filters) |
| GET | `/statistics` | Get master database statistics |
| GET | `/{master_id}` | Get specific master item |
| POST | `/` | Create new master item |
| PUT | `/{master_id}` | Update master item |
| DELETE | `/{master_id}` | Soft delete master item |
| POST | `/generate-code` | Generate work code (preview) |
| POST | `/build` | Build master from BOQ file |
| POST | `/rebuild-all` | Regenerate all work codes |
| GET | `/search/by-code` | Search by work code pattern |
| GET | `/export/csv` | Export to CSV |

### 2. Auto-Build Integration

File processing endpoint đã được update:

**`POST /api/v1/files/{file_id}/process`**

Thêm parameter:
```json
{
  "column_mapping": {...},
  "auto_build_master": true  // ← NEW!
}
```

Khi `auto_build_master = true`, hệ thống sẽ tự động:
1. Process BOQ file
2. Build master database từ line items
3. Generate work codes cho tất cả items

### 3. Services Integration

- ✅ `WorkCodeGenerator` - Generate và validate work codes
- ✅ `MasterDataService` - Build và manage master database
- ✅ Auto-integration vào file processing workflow

---

## 📖 API Usage Examples

### 1. Generate Work Code (Preview)

```bash
curl -X POST "http://localhost:8000/api/v1/master-items/generate-code" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Bê tông M200 dầm",
    "sec_code": "SEC-02",
    "unit": "m3",
    "include_grade": true
  }'
```

**Response:**
```json
{
  "work_code": "S02-CONC-M200-0001",
  "description": "Bê tông M200 dầm",
  "sec_code": "SEC-02",
  "material_grade": "M200",
  "is_valid": true,
  "parsed": {
    "sec_prefix": "S02",
    "category": "CONC",
    "sub_category": "M200",
    "sequence": "0001"
  }
}
```

### 2. List Master Items

```bash
curl "http://localhost:8000/api/v1/master-items/?limit=10&sec_code=SEC-02"
```

**Response:**
```json
[
  {
    "master_id": 15,
    "work_code": "S02-CONC-M200-0001",
    "description": "Bê tông M200 dầm",
    "sec_code": "SEC-02",
    "unit_standard": "m3",
    "ref_unit_price_avg": 1500000,
    "occurrence_count": 5,
    "is_verified": false,
    "created_at": "2026-02-02T10:00:00",
    "updated_at": "2026-02-02T10:00:00"
  }
]
```

### 3. Get Statistics

```bash
curl "http://localhost:8000/api/v1/master-items/statistics"
```

**Response:**
```json
{
  "total_master_items": 150,
  "verified_items": 45,
  "unverified_items": 105,
  "by_sec_code": {
    "SEC-01": 25,
    "SEC-02": 30,
    "SEC-03": 40,
    "SEC-04": 20,
    "SEC-05": 35
  },
  "by_material_grade": {
    "M200": 15,
    "M250": 10,
    "M300": 5
  }
}
```

### 4. Search by Work Code Pattern

```bash
# All SEC-01 items
curl "http://localhost:8000/api/v1/master-items/search/by-code?code_pattern=S01-*"

# All M200 concrete
curl "http://localhost:8000/api/v1/master-items/search/by-code?code_pattern=*-M200-*"

# All concrete items
curl "http://localhost:8000/api/v1/master-items/search/by-code?code_pattern=S02-CONC-*"
```

### 5. Build Master from File

```bash
curl -X POST "http://localhost:8000/api/v1/master-items/build" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": 5,
    "min_confidence": 60.0,
    "skip_unclassified": false
  }'
```

**Response:**
```json
{
  "total_items": 120,
  "added": 85,
  "updated": 35,
  "skipped": 0,
  "by_sec_code": {
    "SEC-01": 20,
    "SEC-02": 30,
    "SEC-03": 25,
    "SEC-04": 15,
    "SEC-05": 30
  }
}
```

### 6. Process File with Auto-Build

```bash
curl -X POST "http://localhost:8000/api/v1/files/5/process" \
  -H "Content-Type: application/json" \
  -d '{
    "column_mapping": {
      "description": "Mô tả",
      "unit": "Đơn vị",
      "quantity": "Số lượng",
      "unit_price": "Đơn giá",
      "amount": "Thành tiền"
    },
    "auto_build_master": true
  }'
```

**Response includes master build stats:**
```json
{
  "message": "File processed successfully",
  "total_rows": 120,
  "processed_rows": 115,
  "master_build": {
    "added": 85,
    "updated": 30,
    "skipped": 0
  }
}
```

### 7. Regenerate All Work Codes

```bash
# Preview changes (dry run)
curl -X POST "http://localhost:8000/api/v1/master-items/rebuild-all?dry_run=true"

# Apply changes
curl -X POST "http://localhost:8000/api/v1/master-items/rebuild-all?dry_run=false"
```

---

## 🔧 Frontend Integration

### React/TypeScript Example

```typescript
// api/masterItems.ts
import axios from 'axios';

const API_BASE = '/api/v1/master-items';

export const masterItemsAPI = {
  // List items
  list: async (params?: {
    skip?: number;
    limit?: number;
    sec_code?: string;
    search?: string;
    verified_only?: boolean;
  }) => {
    const response = await axios.get(API_BASE, { params });
    return response.data;
  },

  // Get statistics
  getStatistics: async () => {
    const response = await axios.get(`${API_BASE}/statistics`);
    return response.data;
  },

  // Generate work code
  generateCode: async (data: {
    description: string;
    sec_code: string;
    unit?: string;
    include_grade?: boolean;
  }) => {
    const response = await axios.post(`${API_BASE}/generate-code`, data);
    return response.data;
  },

  // Search by pattern
  searchByCode: async (pattern: string) => {
    const response = await axios.get(`${API_BASE}/search/by-code`, {
      params: { code_pattern: pattern }
    });
    return response.data;
  },

  // Build from file
  buildFromFile: async (fileId: number, options?: {
    min_confidence?: number;
    skip_unclassified?: boolean;
  }) => {
    const response = await axios.post(`${API_BASE}/build`, {
      file_id: fileId,
      ...options
    });
    return response.data;
  }
};
```

### React Component Example

```tsx
import React, { useState } from 'react';
import { masterItemsAPI } from './api/masterItems';

export const WorkCodeGenerator: React.FC = () => {
  const [description, setDescription] = useState('');
  const [secCode, setSecCode] = useState('SEC-02');
  const [result, setResult] = useState<any>(null);

  const handleGenerate = async () => {
    try {
      const data = await masterItemsAPI.generateCode({
        description,
        sec_code: secCode,
        include_grade: true
      });
      setResult(data);
    } catch (error) {
      console.error('Error generating code:', error);
    }
  };

  return (
    <div>
      <h2>Generate Work Code</h2>
      <input
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="Description (e.g., Bê tông M200 dầm)"
      />
      <select value={secCode} onChange={(e) => setSecCode(e.target.value)}>
        <option value="SEC-01">SEC-01 - Substructure</option>
        <option value="SEC-02">SEC-02 - Superstructure</option>
        <option value="SEC-03">SEC-03 - Architecture</option>
      </select>
      <button onClick={handleGenerate}>Generate</button>

      {result && (
        <div>
          <h3>Result:</h3>
          <p>Work Code: <strong>{result.work_code}</strong></p>
          <p>Material Grade: {result.material_grade || 'N/A'}</p>
          <p>Valid: {result.is_valid ? '✓' : '✗'}</p>
        </div>
      )}
    </div>
  );
};
```

---

## 🚀 Deployment Checklist

### 1. Database Migration

Ensure `master_work_items` table exists:

```bash
docker compose exec backend python -c "
from app.models.master_work_item import MasterWorkItem
from app.core.database import engine
MasterWorkItem.__table__.create(engine, checkfirst=True)
print('✓ Master work items table created')
"
```

### 2. Build Initial Master Database

```bash
# Option 1: Build from specific file
docker compose exec backend python -c "
from app.core.database import SessionLocal
from app.services.master_data_service import MasterDataService

db = SessionLocal()
service = MasterDataService(db)
stats = service.build_master_from_file(file_id=5, min_confidence=60.0)
print(f'Added: {stats[\"added\"]}, Updated: {stats[\"updated\"]}')
db.close()
"

# Option 2: Use the build script
docker compose exec backend python build_master_database.py
```

### 3. Verify API Endpoints

```bash
curl http://localhost:8000/api/v1/master-items/statistics
```

### 4. Test Work Code Generation

```bash
curl -X POST http://localhost:8000/api/v1/master-items/generate-code \
  -H "Content-Type: application/json" \
  -d '{"description":"Bê tông M200","sec_code":"SEC-02"}'
```

---

## 📊 Monitoring & Maintenance

### Check Master Database Health

```python
# Get statistics
GET /api/v1/master-items/statistics

# Check unverified items
GET /api/v1/master-items/?verified_only=false&limit=100

# Export for review
GET /api/v1/master-items/export/csv
```

### Regular Maintenance Tasks

1. **Weekly:** Review unverified items
2. **Monthly:** Regenerate work codes if needed
3. **Quarterly:** Export and backup master database

---

## 🔍 Troubleshooting

### Issue: Work codes not generating

**Solution:** Check that WorkCodeGenerator is properly initialized
```bash
docker compose logs backend | grep "WorkCodeGenerator"
```

### Issue: Master items not building

**Solution:** Verify line items have SEC codes
```bash
docker compose exec backend python -c "
from app.core.database import SessionLocal
from app.models.line_item import LineItem
db = SessionLocal()
items_with_sec = db.query(LineItem).filter(LineItem.sec_code.isnot(None)).count()
print(f'Items with SEC codes: {items_with_sec}')
"
```

### Issue: API returns 500 error

**Solution:** Check backend logs
```bash
docker compose logs backend --tail=50
```

---

## 📚 Related Documentation

- **Work Code System:** `docs/WORK_CODE_SYSTEM.md`
- **Material Grades:** `docs/MATERIAL_GRADES_GUIDE.md`
- **API Reference:** `http://localhost:8000/docs` (Swagger UI)
- **Test Results:** `REAL_BOQ_TEST_RESULTS.md`

---

## ✅ Integration Status

| Component | Status |
|-----------|--------|
| Backend API Endpoints | ✅ Complete |
| Work Code Generator | ✅ Complete |
| Master Data Service | ✅ Complete |
| Auto-Build Integration | ✅ Complete |
| API Documentation | ✅ Available at `/docs` |
| Material Grade Support | ✅ B-grade & M-grade |
| Search & Filter | ✅ Complete |
| Statistics API | ✅ Complete |

**System Ready for Production!** 🚀
