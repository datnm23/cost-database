# BOQ STANDARDIZATION SYSTEM - PROJECT OVERVIEW

**Version:** 2.0  
**Created:** January 12, 2026  
**Status:** Planning Phase  
**Tech Stack:** Python FastAPI + React + TypeScript + MySQL

---

## 📌 Executive Summary

Hệ thống BOQ (Bill of Quantities) Standardization là ứng dụng web giúp chuẩn hóa dữ liệu dự toán xây dựng, tự động phân loại theo mã SEC sử dụng AI/ML.

### Business Goals
- Giảm 70% thời gian xử lý BOQ thủ công
- Tăng độ chính xác phân loại lên 85%+
- Chuẩn hóa dữ liệu BOQ theo tiêu chuẩn SEC

### Key Features
| Feature | Priority | Status |
|---------|----------|--------|
| Upload & Parse Excel | P0 | Planned |
| Data Cleaning | P0 | Planned |
| Auto Classification (AI) | P0 | Planned |
| Manual Review | P1 | Planned |
| Reports & Analytics | P1 | Planned |
| Export Data | P2 | Planned |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND (React + TypeScript)                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Vite │ TanStack Query │ Zustand │ Ant Design           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │ REST API                            │
└────────────────────────────┼────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BACKEND (Python FastAPI)                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  API Layer (Routes)                                       │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │   │
│  │  │ Projects │ │ BOQ Files│ │ Classify │ │ Reports  │    │   │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘    │   │
│  └───────┼────────────┼────────────┼────────────┼───────────┘   │
│          ▼            ▼            ▼            ▼               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Service Layer (Business Logic)                           │   │
│  │  ├── ProjectService    ├── FileProcessor                 │   │
│  │  ├── ClassifierService └── ReportService                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│          │                                                       │
│  ┌───────▼──────────────────────────────────────────────────┐   │
│  │  Data Layer (SQLAlchemy ORM)                              │   │
│  │  ├── Project  ├── BOQFile  ├── LineItem  ├── SECCode     │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATABASE (MySQL 8.0+)                        │
│                     + Redis (Cache - Optional)                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow

```
Excel BOQ File
      │
      ▼
┌─────────────────┐
│  File Processor │ → Detect structure, extract data
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Data Cleaner   │ → Normalize units, clean text
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ML Classifier  │ → Auto-assign SEC codes
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Database     │ → Store with metadata
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Manual Review  │ → Human verification
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Reports/Export  │ → Analytics & Output
└─────────────────┘
```

---

## 🔧 Technology Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| Frontend | Streamlit | 1.31+ | Web UI framework |
| Backend | Python | 3.10+ | Business logic |
| Database | MySQL | 8.0+ | Data storage |
| ML | sentence-transformers | 2.3+ | Text classification |
| NLP | underthesea | 6.7+ | Vietnamese NLP |
| Container | Docker | Latest | MySQL deployment |

---

## 📁 Project Structure

```
boq_system/
├── docs/                       # Documentation
│   ├── PROJECT_OVERVIEW.md     # This file
│   ├── REQUIREMENTS.md         # Requirements specification
│   ├── TECHNICAL_DESIGN.md     # Technical design doc
│   ├── DEPLOYMENT_GUIDE.md     # Deployment instructions
│   └── implement_guide/        # Implementation guide
│
├── src/                        # Source code
│   ├── app.py                  # Main Streamlit app
│   ├── config.py               # Configuration
│   ├── modules/
│   │   ├── database.py         # Database handler
│   │   ├── file_processor.py   # Excel processing
│   │   ├── classifier.py       # ML classifier
│   │   └── reports.py          # Report generator
│   └── utils/
│       ├── logger.py           # Logging utility
│       └── validators.py       # Input validators
│
├── database/                   # Database files
│   ├── schema.sql              # Full schema
│   ├── seed_data.sql           # Initial data
│   └── migrations/             # Schema migrations
│
├── models/                     # ML models
│   └── .gitkeep
│
├── tests/                      # Test files
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── docker/
│   └── docker-compose.yml
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🎯 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Processing Time | <10s/1000 items | Timer in code |
| Classification Accuracy | >85% | Manual review ratio |
| User Adoption | 100% team | Usage analytics |
| Error Rate | <5% | Error logging |

---

## 📅 Project Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| 1. Setup | 1 week | Environment, Database |
| 2. Core Development | 2 weeks | Upload, Classification |
| 3. Review System | 1 week | Manual review UI |
| 4. Analytics | 1 week | Dashboard, Reports |
| 5. Testing | 1 week | Unit tests, UAT |
| 6. Deployment | 3 days | Production release |

---

## 🔒 Security Considerations

1. **Environment Variables**: All credentials in `.env` file
2. **Input Validation**: Sanitize all user inputs
3. **SQL Injection**: Use parameterized queries
4. **File Upload**: Validate file types and sizes
5. **Access Control**: Future multi-user support

---

## 📞 Contacts

| Role | Responsibility |
|------|----------------|
| Project Owner | Business requirements |
| Developer | Implementation |
| DBA | Database management |
| End Users | Testing & feedback |
