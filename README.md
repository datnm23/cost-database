# BOQ Cost Database System

Modern web application for managing and standardizing Bill of Quantities (BOQ) data with AI-powered classification and normalization.

## Features

### Core Features
- **BOQ File Upload**: Upload Excel BOQ files with automatic structure detection
- **Multi-Pass AI Processing**: 5-pass analysis for comprehensive data processing
- **Description Normalization**: Natural syntax normalization for Vietnamese construction terms
- **SEC Classification**: Machine learning-based Standard Estimating Code classification
- **Master Database**: Centralized work item database with fuzzy matching

### BOQ Processing Flow
```
Upload BOQ → Extract Items → Dedupe Raw → Normalize → Match with Master
    ↓
├─ Exact Match (≥95%) → Auto assign work code
├─ Fuzzy Match (80-95%) → Needs review
└─ New Item (<80%) → Add to Master
```

### Export & Reporting
- Excel export with 7 structured sheets
- Color-coded match types (green/yellow/red)
- Master database reference
- Line items with SEC classification

## Tech Stack

### Backend
- **Python 3.11+** with FastAPI
- **SQLAlchemy** ORM
- **MySQL 8.0+** database
- **Sentence Transformers** for ML classification
- **OpenPyXL** for Excel processing

### Frontend
- **React 18** with TypeScript
- **Vite** build tool
- **Ant Design** UI components
- **React Query** for data fetching

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 20+

### Using Docker
```bash
# Clone and start
git clone <repo-url>
cd cost-database
cp .env.example .env
docker-compose up -d

# Access
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Local Development
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Project Structure

```
cost-database/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # API endpoints
│   │   ├── models/              # SQLAlchemy models
│   │   ├── services/            # Business logic
│   │   │   ├── boq_processing_service.py    # BOQ processing flow
│   │   │   ├── boq_export_service.py        # Excel export
│   │   │   ├── description_normalizer.py    # Natural syntax normalization
│   │   │   ├── mep_equipment_normalizer.py  # MEP equipment handling
│   │   │   ├── master_data_service.py       # Master DB with fuzzy matching
│   │   │   └── classifier_service.py        # SEC classification
│   │   └── utils/
│   ├── TEMPLATE_BOQ_Result_After_Processing.xlsx
│   └── requirements.txt
├── frontend/
│   └── src/
├── docs/
│   ├── PROJECT_OVERVIEW.md
│   ├── REQUIREMENTS.md
│   ├── TECHNICAL_DESIGN.md
│   └── DEPLOYMENT_GUIDE.md
└── docker-compose.yml
```

## API Endpoints

### BOQ Processing
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/files/upload` | POST | Upload BOQ Excel file |
| `/api/v1/files/{id}/process` | POST | Process uploaded file |
| `/api/v1/master_items/process-boq` | POST | Process with new flow |
| `/api/v1/master_items/process-boq/{id}/details` | GET | Get match details |
| `/api/v1/master_items/process-boq/{id}/export` | GET | Export to Excel |
| `/api/v1/master_items/match-description` | POST | Test single match |

### Master Database
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/master_items` | GET | List master items |
| `/api/v1/master_items/build` | POST | Build from BOQ file |
| `/api/v1/master_items/search/by-code` | GET | Search by work code |
| `/api/v1/master_items/export/csv` | GET | Export to CSV |

## Normalization Categories

| Category | Examples |
|----------|----------|
| **Earthworks** | Đào đất, Đắp đất K95, San nền |
| **Concrete** | Bê tông móng M300, Ván khuôn |
| **Finishing** | Xây tường gạch, Trát tường, Lát gạch |
| **MEP** | Cáp Cu/XLPE/PVC, Ống HDPE D110, MCCB 3P 400A |
| **Road Infrastructure** | Biển báo, Vạch sơn, Lan can |
| **Landscaping** | Trồng cây Bàng, Cỏ lạc, Đất màu |

## Export Template

The system generates Excel files with 7 sheets:

1. **Summary** - Processing statistics
2. **All Items** - Complete list with match types
3. **Exact Matches** - Auto-approved items (≥95%)
4. **Needs Review** - Items requiring review (80-95%)
5. **New Items** - New work items (<80%)
6. **Master Reference** - Top master items
7. **Line Items Detail** - Full classification data

See `backend/TEMPLATE_BOQ_Result_After_Processing.xlsx` for sample format.

## Documentation

| Document | Description |
|----------|-------------|
| [Đặt tên chuẩn công tác xây dựng.md](Đặt tên chuẩn công tác xây dựng.md) | Naming conventions for construction work |
| [docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md) | System architecture |
| [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) | Functional requirements |
| [docs/TECHNICAL_DESIGN.md](docs/TECHNICAL_DESIGN.md) | Technical specifications |
| [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) | Deployment instructions |

## Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Test with real BOQ files
python test_boq_processing.py
python test_mep_improvements.py

# Test normalization
python test_real_boq.py
```

## License

MIT License

---

**Built for construction cost management in Vietnam**
