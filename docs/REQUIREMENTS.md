# BOQ SYSTEM - REQUIREMENTS SPECIFICATION

**Version:** 2.0  
**Created:** January 12, 2026  
**Last Updated:** January 12, 2026  
**Tech Stack:** Python FastAPI + React + TypeScript + MySQL

---

## 0. TECH STACK OVERVIEW

### 0.1 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + TypeScript)             │
│  ├── Vite 5+ (Build Tool)                                   │
│  ├── TanStack Query (Server State)                          │
│  ├── Zustand (Client State)                                 │
│  ├── Ant Design (UI Components)                             │
│  └── Recharts (Data Visualization)                          │
└─────────────────────────────────────────────────────────────┘
                            │ REST API (JSON)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (Python FastAPI)                  │
│  ├── FastAPI 0.109+ (Web Framework)                         │
│  ├── SQLAlchemy 2.0 (ORM)                                   │
│  ├── Pydantic v2 (Validation)                               │
│  ├── Alembic (Migrations)                                   │
│  └── sentence-transformers (ML Classification)              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATABASE (MySQL 8.0+)                     │
│                    + Redis (Cache/Queue)                     │
└─────────────────────────────────────────────────────────────┘
```

### 0.2 Technology Stack Details

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Frontend** ||||
| Framework | React | 18.2+ | UI Library |
| Language | TypeScript | 5.3+ | Type Safety |
| Build Tool | Vite | 5.0+ | Fast Dev Server |
| State (Server) | TanStack Query | 5.17+ | API State Management |
| State (Client) | Zustand | 4.5+ | Local State |
| UI Library | Ant Design | 5.13+ | Component Library |
| Routing | React Router | 6.21+ | Navigation |
| Forms | React Hook Form | 7.49+ | Form Handling |
| Validation | Zod | 3.22+ | Schema Validation |
| Charts | Recharts | 2.10+ | Visualization |
| HTTP Client | Axios | 1.6+ | API Requests |
| **Backend** ||||
| Framework | FastAPI | 0.109+ | REST API |
| Language | Python | 3.11+ | Backend Logic |
| ORM | SQLAlchemy | 2.0+ | Database ORM |
| Migrations | Alembic | 1.13+ | Schema Versioning |
| Validation | Pydantic | 2.5+ | Data Validation |
| Server | Uvicorn | 0.27+ | ASGI Server |
| Excel | Polars + openpyxl | Latest | Data Processing |
| ML | sentence-transformers | 2.3+ | Text Classification |
| NLP | underthesea | 6.8+ | Vietnamese NLP |
| **Database** ||||
| RDBMS | MySQL | 8.0+ | Primary Database |
| Cache | Redis | 7.0+ | Caching (Optional) |
| **DevOps** ||||
| Container | Docker | Latest | Containerization |
| Orchestration | Docker Compose | Latest | Local Development |

### 0.3 Project Structure

```
cost-database/
├── docker-compose.yml
├── .env.example
├── Makefile
│
├── backend/                    # FastAPI Backend
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic/               # Database migrations
│   ├── app/
│   │   ├── main.py            # FastAPI entry
│   │   ├── config.py          # Settings
│   │   ├── api/v1/            # API Routes
│   │   ├── models/            # SQLAlchemy Models
│   │   ├── schemas/           # Pydantic Schemas
│   │   ├── services/          # Business Logic
│   │   └── ml/                # ML Classification
│   └── tests/
│
├── frontend/                   # React Frontend
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── api/               # API Client
│   │   ├── components/        # React Components
│   │   ├── pages/             # Page Components
│   │   ├── hooks/             # Custom Hooks
│   │   ├── stores/            # Zustand Stores
│   │   └── types/             # TypeScript Types
│   └── tests/
│
└── docs/                       # Documentation
```

---

## 1. FUNCTIONAL REQUIREMENTS

### 1.1 Project Management (FR-PM)

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-PM-01 | Tạo mới project với thông tin: code, name, type, location, client | P0 | Required fields: code, name, type |
| FR-PM-02 | Xem danh sách tất cả projects | P0 | Pagination, sorting |
| FR-PM-03 | Sửa thông tin project | P1 | Except project_code |
| FR-PM-04 | Xóa project (soft delete) | P2 | Archive, not permanent delete |
| FR-PM-05 | Tìm kiếm project theo tên, mã, loại | P1 | Full-text search |
| FR-PM-06 | Lọc project theo status, type, date range | P1 | Multiple filters |

### 1.2 BOQ Upload & Processing (FR-UP)

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-UP-01 | Upload file Excel (.xlsx, .xls) | P0 | Max 50MB |
| FR-UP-02 | Tự động phát hiện cấu trúc file | P0 | Header row, columns |
| FR-UP-03 | Preview dữ liệu trước khi import | P0 | First 20 rows |
| FR-UP-04 | Mapping columns thủ công | P0 | Override auto-detect |
| FR-UP-05 | Validate dữ liệu trước import | P0 | Check required fields |
| FR-UP-06 | Phát hiện file trùng lặp | P1 | Hash-based |
| FR-UP-07 | Hỗ trợ nhiều sheets | P2 | Select target sheet |
| FR-UP-08 | Progress bar khi processing | P1 | Real-time update |

### 1.3 Data Cleaning (FR-DC)

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-DC-01 | Loại bỏ rows trống | P0 | Auto |
| FR-DC-02 | Chuẩn hóa đơn vị đo (m, m2, kg, ton...) | P0 | Mapping table |
| FR-DC-03 | Xử lý số lượng âm/không hợp lệ | P0 | Flag for review |
| FR-DC-04 | Trim whitespace | P0 | All text fields |
| FR-DC-05 | Tính toán amount = qty × unit_price | P0 | If missing |
| FR-DC-06 | Detect và xử lý tiếng Việt | P1 | Unicode normalization |

### 1.4 Auto Classification (FR-CL)

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-CL-01 | Phân loại tự động theo mã SEC | P0 | ML-based |
| FR-CL-02 | Trả về confidence score (0-100%) | P0 | Display to user |
| FR-CL-03 | Đề xuất top 3 SEC codes | P1 | For low confidence |
| FR-CL-04 | Rule-based matching (keywords) | P0 | First pass |
| FR-CL-05 | Học từ corrections của user | P2 | Active learning |
| FR-CL-06 | Threshold configuration | P1 | Admin setting |

### 1.5 Manual Review (FR-RV)

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-RV-01 | Xem danh sách items cần review | P0 | Confidence < threshold |
| FR-RV-02 | Sửa SEC code thủ công | P0 | Dropdown select |
| FR-RV-03 | Bulk edit nhiều items | P1 | Select & apply |
| FR-RV-04 | Filter items theo confidence | P0 | Slider |
| FR-RV-05 | Search items theo description | P1 | Full-text |
| FR-RV-06 | Mark as reviewed/approved | P1 | Status tracking |

### 1.6 Reports & Analytics (FR-RP)

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-RP-01 | Dashboard tổng quan | P0 | Key metrics |
| FR-RP-02 | Chart phân bố theo SEC | P0 | Pie/Bar chart |
| FR-RP-03 | Chart giá trị theo project | P1 | Line/Bar chart |
| FR-RP-04 | Export Excel report | P0 | Formatted |
| FR-RP-05 | Export PDF report | P2 | Summary |
| FR-RP-06 | Compare projects | P2 | Side by side |

---

## 2. NON-FUNCTIONAL REQUIREMENTS

### 2.1 Performance (NFR-PF)

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-PF-01 | Thời gian load trang | < 3 seconds |
| NFR-PF-02 | Thời gian xử lý 1000 items | < 10 seconds |
| NFR-PF-03 | Thời gian classify 1 item | < 100ms |
| NFR-PF-04 | Concurrent users | 5 users |
| NFR-PF-05 | Max file size | 50 MB |

### 2.2 Reliability (NFR-RL)

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-RL-01 | System uptime | 99% during work hours |
| NFR-RL-02 | Data backup | Daily |
| NFR-RL-03 | Error recovery | Auto-retry 3 times |
| NFR-RL-04 | Data consistency | ACID transactions |

### 2.3 Usability (NFR-US)

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-US-01 | Ngôn ngữ | Vietnamese + English |
| NFR-US-02 | Training time | < 2 hours |
| NFR-US-03 | Help documentation | Inline tooltips |
| NFR-US-04 | Error messages | Clear, actionable |

### 2.4 Security (NFR-SC)

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-SC-01 | SQL injection protection | Parameterized queries |
| NFR-SC-02 | File upload validation | Type & size check |
| NFR-SC-03 | Credential storage | Environment variables |
| NFR-SC-04 | Audit logging | All data changes |

### 2.5 Maintainability (NFR-MT)

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-MT-01 | Code documentation | Docstrings all functions |
| NFR-MT-02 | Test coverage | > 70% |
| NFR-MT-03 | Logging | Structured logging |
| NFR-MT-04 | Configuration | External config file |

---

## 3. DATA REQUIREMENTS

### 3.1 SEC Codes Master Data

```
Required fields:
- sec_code (VARCHAR 20): Mã SEC (e.g., SEC-01-01)
- sec_name_vi (VARCHAR 255): Tên tiếng Việt
- sec_name_en (VARCHAR 255): Tên tiếng Anh
- parent_code (VARCHAR 20): Mã cha (hierarchical)
- level (TINYINT): Cấp độ (1-5)
- keywords (JSON): Từ khóa matching
```

### 3.2 Standard SEC Hierarchy

```
Level 1: Main Categories
├── SEC-00: Chi phí chung & Chuẩn bị
├── SEC-01: Phần Ngầm (Substructure)
├── SEC-02: Phần Thân (Superstructure)
├── SEC-03: Kiến trúc & Hoàn thiện
├── SEC-04: Hệ thống MEP
└── SEC-05: Cảnh quan

Level 2: Sub-categories
├── SEC-01-01: Công tác đất
├── SEC-01-02: Cọc
├── SEC-01-03: Móng
...

Level 3: Detailed items
├── SEC-01-01-01: Đào đất móng
├── SEC-01-01-02: Đắp đất
...
```

### 3.3 Unit Standardization

| Standard | Variations to Accept |
|----------|---------------------|
| m | met, meter, mét |
| m2 | m², sqm, square meter |
| m3 | m³, cbm, cubic meter |
| kg | kilo, kilogram |
| ton | tấn, t, metric ton |
| pcs | cái, ea, each, piece |
| set | bộ, sets |
| ls | lump sum, trọn gói |

---

## 4. INTERFACE REQUIREMENTS

### 4.1 User Interface

```
Main Navigation:
├── 🏠 Home (Dashboard)
├── 📁 Projects
├── ⬆️ Upload BOQ
├── 📝 Review Items
├── 📊 Analytics
└── ⚙️ Settings

Color Scheme:
- Primary: #1E88E5 (Blue)
- Success: #4CAF50 (Green)
- Warning: #FF9800 (Orange)
- Error: #F44336 (Red)
- Background: #FAFAFA
```

### 4.2 Data Formats

| Type | Format |
|------|--------|
| Date | YYYY-MM-DD |
| DateTime | YYYY-MM-DD HH:MM:SS |
| Currency | #,##0.00 VND |
| Percentage | 0.00% |
| File size | KB/MB |

---

## 5. CONSTRAINTS

### 5.1 Technical Constraints

- **Backend:** Python 3.11+, FastAPI
- **Frontend:** Node.js 20+, React 18+
- **Database:** MySQL 8.0+ only
- **Browser:** Chrome, Firefox, Edge (latest 2 versions)
- **OS:** Windows 10+, macOS 11+, Linux (Ubuntu 20.04+)
- **Container:** Docker 24+, Docker Compose v2

### 5.2 Business Constraints

- Multi-user support (authentication required)
- Local/Cloud deployment options
- Vietnamese language primary, English secondary
- SEC code standard (company-specific, customizable)

---

## 6. ASSUMPTIONS

1. Users có kiến thức cơ bản về Excel và BOQ
2. File BOQ có cấu trúc tương đối chuẩn
3. Kết nối internet cho ML model (first run only)
4. Docker được cài đặt trên máy (development)
5. Node.js 20+ và Python 3.11+ được cài đặt

---

## 7. API DESIGN

### 7.1 RESTful Endpoints

```yaml
# Authentication
POST   /api/v1/auth/login           # Login
POST   /api/v1/auth/logout          # Logout
GET    /api/v1/auth/me              # Current user

# Projects
GET    /api/v1/projects             # List projects (paginated)
POST   /api/v1/projects             # Create project
GET    /api/v1/projects/{id}        # Get project details
PUT    /api/v1/projects/{id}        # Update project
DELETE /api/v1/projects/{id}        # Delete project (soft)

# BOQ Files
GET    /api/v1/projects/{id}/files  # List project files
POST   /api/v1/files/upload         # Upload BOQ file
GET    /api/v1/files/{id}           # Get file details
DELETE /api/v1/files/{id}           # Delete file
POST   /api/v1/files/{id}/process   # Process/classify file

# Line Items
GET    /api/v1/files/{id}/items     # List file items (paginated)
GET    /api/v1/items                # List all items (with filters)
PUT    /api/v1/items/{id}           # Update single item
POST   /api/v1/items/bulk-update    # Bulk update items
GET    /api/v1/items/review         # Items needing review

# SEC Codes
GET    /api/v1/sec-codes            # List all SEC codes
GET    /api/v1/sec-codes/tree       # Get hierarchy tree
POST   /api/v1/sec-codes            # Create SEC code
PUT    /api/v1/sec-codes/{code}     # Update SEC code

# Classification
POST   /api/v1/classify             # Classify single text
POST   /api/v1/classify/batch       # Batch classify

# Analytics & Reports
GET    /api/v1/analytics/dashboard  # Dashboard statistics
GET    /api/v1/analytics/sec-distribution/{project_id}
POST   /api/v1/reports/export       # Export report (Excel/PDF)
```

### 7.2 Response Format

```json
// Success Response
{
  "success": true,
  "data": { ... },
  "message": "Operation successful"
}

// Paginated Response
{
  "success": true,
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  }
}

// Error Response
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [
      {"field": "project_code", "message": "Already exists"}
    ]
  }
}
```

### 7.3 HTTP Status Codes

| Code | Description | Usage |
|------|-------------|-------|
| 200 | OK | Successful GET, PUT |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Validation error |
| 401 | Unauthorized | Not authenticated |
| 403 | Forbidden | Not authorized |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable | Business logic error |
| 500 | Server Error | Unexpected error |

---

## 8. ACCEPTANCE CRITERIA

### 8.1 Must Have (Phase 1 - MVP)

- [ ] **Backend API**
  - [ ] FastAPI server running with Swagger docs
  - [ ] CRUD operations for Projects, Files, Items
  - [ ] File upload and Excel parsing
  - [ ] ML classification endpoint
  - [ ] Export to Excel

- [ ] **Frontend React App**
  - [ ] Project list and detail pages
  - [ ] File upload with drag & drop
  - [ ] Preview and column mapping
  - [ ] Review table with inline edit
  - [ ] Dashboard with basic metrics

- [ ] **Core Features**
  - [ ] Upload Excel file và parse thành công
  - [ ] Auto-classify với accuracy > 80%
  - [ ] Manual review và correct SEC codes
  - [ ] Export cleaned data to Excel

### 8.2 Should Have (Phase 1)

- [ ] Dashboard với key metrics và charts
- [ ] Bulk edit multiple items
- [ ] Search and filter functionality
- [ ] Progress bar during processing
- [ ] Responsive design

### 8.3 Nice to Have (Phase 2)

- [ ] User authentication (JWT)
- [ ] Active learning from corrections
- [ ] Multi-user support with roles
- [ ] Advanced analytics
- [ ] PDF report generation
- [ ] Compare projects side-by-side
- [ ] Dark mode UI

---

## 9. DEVELOPMENT WORKFLOW

### 9.1 Getting Started

```bash
# Clone repository
git clone <repository-url>
cd cost-database

# Setup environment
cp .env.example .env

# Start all services with Docker
docker-compose up -d

# Or run separately:

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### 9.2 Development URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | React dev server |
| Backend API | http://localhost:8000 | FastAPI server |
| API Docs | http://localhost:8000/docs | Swagger UI |
| API ReDoc | http://localhost:8000/redoc | ReDoc UI |
| phpMyAdmin | http://localhost:8080 | Database admin |

### 9.3 Common Commands

```bash
# Docker
docker-compose up -d              # Start all services
docker-compose down               # Stop all services
docker-compose logs -f backend    # View backend logs

# Backend
cd backend
alembic upgrade head              # Run migrations
alembic revision --autogenerate -m "message"  # Create migration
pytest                            # Run tests
pytest --cov=app                  # Run tests with coverage

# Frontend
cd frontend
npm run dev                       # Development server
npm run build                     # Production build
npm run test                      # Run tests
npm run lint                      # Lint code
```

---

## 10. DEPLOYMENT

### 10.1 Environment Variables

```bash
# Backend (.env)
DEBUG=false
SECRET_KEY=your-production-secret-key
DB_HOST=mysql
DB_PORT=3306
DB_USER=boq_user
DB_PASSWORD=secure_password
DB_NAME=boq_system
CORS_ORIGINS=["https://your-domain.com"]

# Frontend (.env.production)
VITE_API_URL=https://api.your-domain.com/api/v1
```

### 10.2 Production Checklist

- [ ] Set DEBUG=false
- [ ] Use strong SECRET_KEY
- [ ] Configure CORS properly
- [ ] Setup SSL/HTTPS
- [ ] Configure database backups
- [ ] Setup monitoring & logging
- [ ] Load testing completed

---

## 📝 Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-12 | AI Assistant | Initial version |
| 2.0 | 2026-01-12 | AI Assistant | Updated to FastAPI + React stack |
