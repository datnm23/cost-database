# BOQ SYSTEM - TECHNICAL DESIGN DOCUMENT

**Version:** 2.0  
**Created:** January 12, 2026  
**Last Updated:** January 12, 2026  
**Tech Stack:** Python FastAPI + React + TypeScript + MySQL

---

## TABLE OF CONTENTS

1. [System Architecture](#1-system-architecture)
2. [Database Design](#2-database-design)
3. [Backend Architecture (FastAPI)](#3-backend-architecture-fastapi)
4. [Frontend Architecture (React)](#4-frontend-architecture-react)
5. [ML Classification System](#5-ml-classification-system)
6. [API Design](#6-api-design)
7. [Security Design](#7-security-design)
8. [Performance Optimization](#8-performance-optimization)

---

## 1. SYSTEM ARCHITECTURE

### 1.1 High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         USERS                                     │
│                    (Web Browser)                                  │
└─────────────────────────┬────────────────────────────────────────┘
                          │ HTTPS
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│                    NGINX (Reverse Proxy)                          │
│                    - SSL Termination                              │
│                    - Load Balancing                               │
│                    - Static Files                                 │
└────────────┬────────────────────────────────────────┬────────────┘
             │ :80                                     │ :8000
             ▼                                         ▼
┌─────────────────────────┐         ┌─────────────────────────────┐
│   FRONTEND (React)       │         │   BACKEND (FastAPI)          │
│   - Vite Dev Server      │  REST   │   - Uvicorn ASGI Server      │
│   - SPA Application      │ ◄─────► │   - Business Logic           │
│   - TypeScript           │  JSON   │   - ML Classification        │
│   - Ant Design UI        │         │   - File Processing          │
│   Port: 5173 (dev)       │         │   Port: 8000                 │
└─────────────────────────┘         └──────────────┬──────────────┘
                                                    │
                                    ┌───────────────┼───────────────┐
                                    │               │               │
                                    ▼               ▼               ▼
                          ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
                          │  MySQL 8.0   │ │    Redis     │ │  File Store  │
                          │  (Primary)   │ │   (Cache)    │ │  (Uploads)   │
                          │  Port: 3306  │ │  Port: 6379  │ │              │
                          └──────────────┘ └──────────────┘ └──────────────┘
```

### 1.2 Container Architecture (Docker Compose)

```yaml
services:
  frontend:        # React + Vite (Port: 5173)
  backend:         # FastAPI + Uvicorn (Port: 8000)
  mysql:           # MySQL 8.0 (Port: 3306)
  redis:           # Redis Cache (Port: 6379, optional)
  nginx:           # Reverse proxy (production only)
```

### 1.3 Data Flow

```
User Action → React Component → API Call (Axios/TanStack Query) 
    → FastAPI Router → Service Layer → Repository Layer 
    → SQLAlchemy ORM → MySQL Database 
    → Response → React State Update → UI Render
```

---

## 2. DATABASE DESIGN

### 1.1 Complete Schema

```sql
-- ===========================================
-- BOQ STANDARDIZATION SYSTEM - MYSQL SCHEMA
-- Version: 1.0
-- Database: MySQL 8.0+
-- ===========================================

-- Create database
CREATE DATABASE IF NOT EXISTS boq_system
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE boq_system;

-- ===========================================
-- CORE TABLES
-- ===========================================

-- Projects table
CREATE TABLE projects (
    project_id INT AUTO_INCREMENT PRIMARY KEY,
    project_code VARCHAR(50) UNIQUE NOT NULL,
    project_name VARCHAR(255) NOT NULL,
    project_type ENUM('residential', 'commercial', 'industrial', 'infrastructure', 'other') DEFAULT 'other',
    location VARCHAR(255),
    client_name VARCHAR(255),
    contract_value DECIMAL(18,2) DEFAULT 0,
    start_date DATE,
    end_date DATE,
    status ENUM('active', 'completed', 'cancelled', 'on_hold') DEFAULT 'active',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    
    INDEX idx_project_code (project_code),
    INDEX idx_status (status),
    INDEX idx_created (created_at)
) ENGINE=InnoDB;

-- BOQ Files table
CREATE TABLE boq_files (
    file_id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    original_name VARCHAR(255),
    file_path VARCHAR(500),
    file_hash CHAR(64),
    file_size INT,
    total_rows INT DEFAULT 0,
    processed_rows INT DEFAULT 0,
    total_amount DECIMAL(18,2) DEFAULT 0,
    status ENUM('uploading', 'processing', 'completed', 'error', 'approved') DEFAULT 'uploading',
    error_message TEXT,
    uploaded_by VARCHAR(100),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    approved_at TIMESTAMP NULL,
    approved_by VARCHAR(100),
    
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    UNIQUE KEY uk_file_hash (file_hash),
    INDEX idx_project (project_id),
    INDEX idx_status (status)
) ENGINE=InnoDB;

-- Line Items table (main data table)
CREATE TABLE line_items (
    line_item_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    file_id INT NOT NULL,
    project_id INT NOT NULL,
    
    -- Original data
    row_number INT,
    original_description TEXT,
    original_unit VARCHAR(50),
    original_quantity VARCHAR(50),
    original_unit_price VARCHAR(50),
    original_amount VARCHAR(50),
    
    -- Cleaned data
    description TEXT NOT NULL,
    unit VARCHAR(20),
    quantity DECIMAL(18,4) DEFAULT 0,
    unit_price DECIMAL(18,2) DEFAULT 0,
    amount DECIMAL(18,2) DEFAULT 0,
    
    -- Classification
    sec_code VARCHAR(20),
    sec_code_suggestion VARCHAR(20),
    confidence_score DECIMAL(5,2) DEFAULT 0,
    classification_method ENUM('auto', 'manual', 'rule', 'pending') DEFAULT 'pending',
    
    -- Review status
    needs_review BOOLEAN DEFAULT TRUE,
    reviewed_at TIMESTAMP NULL,
    reviewed_by VARCHAR(100),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (file_id) REFERENCES boq_files(file_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (sec_code) REFERENCES sec_codes(sec_code) ON UPDATE CASCADE,
    
    INDEX idx_file (file_id),
    INDEX idx_project (project_id),
    INDEX idx_sec_code (sec_code),
    INDEX idx_needs_review (needs_review),
    INDEX idx_confidence (confidence_score),
    FULLTEXT idx_description (description)
) ENGINE=InnoDB;

-- SEC Codes table (reference data)
CREATE TABLE sec_codes (
    sec_code VARCHAR(20) PRIMARY KEY,
    sec_name_vi VARCHAR(255) NOT NULL,
    sec_name_en VARCHAR(255),
    description TEXT,
    parent_code VARCHAR(20),
    level TINYINT DEFAULT 1,
    sort_order INT DEFAULT 0,
    keywords JSON,
    synonyms JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_code) REFERENCES sec_codes(sec_code) ON UPDATE CASCADE,
    INDEX idx_parent (parent_code),
    INDEX idx_level (level),
    INDEX idx_active (is_active)
) ENGINE=InnoDB;

-- ===========================================
-- LOOKUP TABLES
-- ===========================================

-- Unit mapping table
CREATE TABLE unit_mappings (
    mapping_id INT AUTO_INCREMENT PRIMARY KEY,
    original_unit VARCHAR(50) NOT NULL,
    standard_unit VARCHAR(20) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    
    UNIQUE KEY uk_original (original_unit),
    INDEX idx_standard (standard_unit)
) ENGINE=InnoDB;

-- Classification rules table
CREATE TABLE classification_rules (
    rule_id INT AUTO_INCREMENT PRIMARY KEY,
    rule_name VARCHAR(100) NOT NULL,
    rule_type ENUM('keyword', 'regex', 'pattern') DEFAULT 'keyword',
    pattern VARCHAR(500) NOT NULL,
    sec_code VARCHAR(20) NOT NULL,
    priority INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (sec_code) REFERENCES sec_codes(sec_code) ON UPDATE CASCADE,
    INDEX idx_sec_code (sec_code),
    INDEX idx_priority (priority DESC)
) ENGINE=InnoDB;

-- ===========================================
-- LOGGING & AUDIT
-- ===========================================

-- Audit log table
CREATE TABLE audit_logs (
    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id BIGINT NOT NULL,
    action ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
    old_values JSON,
    new_values JSON,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    
    INDEX idx_table_record (table_name, record_id),
    INDEX idx_changed_at (changed_at)
) ENGINE=InnoDB;

-- Processing logs table
CREATE TABLE processing_logs (
    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    file_id INT,
    log_level ENUM('INFO', 'WARNING', 'ERROR', 'DEBUG') DEFAULT 'INFO',
    message TEXT,
    details JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (file_id) REFERENCES boq_files(file_id) ON DELETE SET NULL,
    INDEX idx_file (file_id),
    INDEX idx_level (log_level),
    INDEX idx_created (created_at)
) ENGINE=InnoDB;

-- ===========================================
-- VIEWS
-- ===========================================

-- Project summary view
CREATE OR REPLACE VIEW v_project_summary AS
SELECT 
    p.project_id,
    p.project_code,
    p.project_name,
    p.project_type,
    p.status,
    p.client_name,
    p.contract_value,
    p.created_at,
    COUNT(DISTINCT f.file_id) as file_count,
    COALESCE(SUM(f.total_rows), 0) as total_items,
    COALESCE(SUM(f.total_amount), 0) as total_value,
    (SELECT COUNT(*) FROM line_items li WHERE li.project_id = p.project_id AND li.needs_review = TRUE) as pending_review
FROM projects p
LEFT JOIN boq_files f ON p.project_id = f.project_id
WHERE p.is_deleted = FALSE
GROUP BY p.project_id;

-- Line items with SEC details view
CREATE OR REPLACE VIEW v_line_items_detail AS
SELECT 
    li.*,
    s.sec_name_vi,
    s.sec_name_en,
    s.level as sec_level,
    ps.sec_code as parent_sec_code,
    ps.sec_name_vi as parent_sec_name_vi,
    bf.file_name,
    p.project_code,
    p.project_name
FROM line_items li
LEFT JOIN sec_codes s ON li.sec_code = s.sec_code
LEFT JOIN sec_codes ps ON s.parent_code = ps.sec_code
LEFT JOIN boq_files bf ON li.file_id = bf.file_id
LEFT JOIN projects p ON li.project_id = p.project_id;

-- SEC code hierarchy view
CREATE OR REPLACE VIEW v_sec_hierarchy AS
SELECT 
    s.sec_code,
    s.sec_name_vi,
    s.sec_name_en,
    s.level,
    s.parent_code,
    (SELECT COUNT(*) FROM line_items li WHERE li.sec_code = s.sec_code) as usage_count,
    (SELECT COALESCE(SUM(li.amount), 0) FROM line_items li WHERE li.sec_code = s.sec_code) as total_amount
FROM sec_codes s
WHERE s.is_active = TRUE
ORDER BY s.sort_order, s.sec_code;

-- Classification accuracy view
CREATE OR REPLACE VIEW v_classification_stats AS
SELECT 
    classification_method,
    COUNT(*) as item_count,
    AVG(confidence_score) as avg_confidence,
    SUM(CASE WHEN needs_review = FALSE THEN 1 ELSE 0 END) as reviewed_count,
    SUM(CASE WHEN needs_review = TRUE THEN 1 ELSE 0 END) as pending_count
FROM line_items
GROUP BY classification_method;

-- ===========================================
-- STORED PROCEDURES
-- ===========================================

DELIMITER //

-- Get SEC code hierarchy
CREATE PROCEDURE sp_get_sec_tree(IN p_parent_code VARCHAR(20))
BEGIN
    WITH RECURSIVE sec_tree AS (
        SELECT sec_code, sec_name_vi, sec_name_en, parent_code, level, 0 as depth
        FROM sec_codes
        WHERE parent_code = p_parent_code OR (p_parent_code IS NULL AND parent_code IS NULL)
        
        UNION ALL
        
        SELECT s.sec_code, s.sec_name_vi, s.sec_name_en, s.parent_code, s.level, st.depth + 1
        FROM sec_codes s
        INNER JOIN sec_tree st ON s.parent_code = st.sec_code
        WHERE st.depth < 5
    )
    SELECT * FROM sec_tree ORDER BY sec_code;
END //

-- Update classification
CREATE PROCEDURE sp_update_classification(
    IN p_line_item_id BIGINT,
    IN p_sec_code VARCHAR(20),
    IN p_reviewed_by VARCHAR(100)
)
BEGIN
    UPDATE line_items 
    SET 
        sec_code = p_sec_code,
        classification_method = 'manual',
        confidence_score = 100,
        needs_review = FALSE,
        reviewed_at = NOW(),
        reviewed_by = p_reviewed_by
    WHERE line_item_id = p_line_item_id;
END //

-- Bulk update classification
CREATE PROCEDURE sp_bulk_update_classification(
    IN p_item_ids JSON,
    IN p_sec_code VARCHAR(20),
    IN p_reviewed_by VARCHAR(100)
)
BEGIN
    UPDATE line_items 
    SET 
        sec_code = p_sec_code,
        classification_method = 'manual',
        confidence_score = 100,
        needs_review = FALSE,
        reviewed_at = NOW(),
        reviewed_by = p_reviewed_by
    WHERE JSON_CONTAINS(p_item_ids, CAST(line_item_id AS JSON));
END //

-- Get project statistics
CREATE PROCEDURE sp_get_project_stats(IN p_project_id INT)
BEGIN
    SELECT 
        COUNT(*) as total_items,
        SUM(amount) as total_amount,
        AVG(confidence_score) as avg_confidence,
        SUM(CASE WHEN needs_review = TRUE THEN 1 ELSE 0 END) as pending_review,
        SUM(CASE WHEN classification_method = 'auto' THEN 1 ELSE 0 END) as auto_classified,
        SUM(CASE WHEN classification_method = 'manual' THEN 1 ELSE 0 END) as manual_classified,
        COUNT(DISTINCT sec_code) as unique_sec_codes
    FROM line_items
    WHERE project_id = p_project_id;
END //

DELIMITER ;

-- ===========================================
-- TRIGGERS
-- ===========================================

DELIMITER //

-- Update file totals after line item insert
CREATE TRIGGER tr_line_item_after_insert
AFTER INSERT ON line_items
FOR EACH ROW
BEGIN
    UPDATE boq_files 
    SET 
        total_rows = total_rows + 1,
        total_amount = total_amount + COALESCE(NEW.amount, 0)
    WHERE file_id = NEW.file_id;
END //

-- Update file totals after line item update
CREATE TRIGGER tr_line_item_after_update
AFTER UPDATE ON line_items
FOR EACH ROW
BEGIN
    IF OLD.amount != NEW.amount THEN
        UPDATE boq_files 
        SET total_amount = total_amount - COALESCE(OLD.amount, 0) + COALESCE(NEW.amount, 0)
        WHERE file_id = NEW.file_id;
    END IF;
END //

-- Update file totals after line item delete
CREATE TRIGGER tr_line_item_after_delete
AFTER DELETE ON line_items
FOR EACH ROW
BEGIN
    UPDATE boq_files 
    SET 
        total_rows = total_rows - 1,
        total_amount = total_amount - COALESCE(OLD.amount, 0)
    WHERE file_id = OLD.file_id;
END //

DELIMITER ;
```

### 1.2 Index Strategy

| Table | Index | Columns | Purpose |
|-------|-------|---------|---------|
| line_items | Primary | line_item_id | Primary key lookup |
| line_items | idx_project | project_id | Filter by project |
| line_items | idx_sec_code | sec_code | Join with sec_codes |
| line_items | idx_needs_review | needs_review | Filter pending items |
| line_items | FULLTEXT | description | Text search |
| projects | idx_project_code | project_code | Unique lookup |
| sec_codes | idx_parent | parent_code | Hierarchy traversal |

---

## 3. BACKEND ARCHITECTURE (FastAPI)

### 3.1 Project Structure

```
backend/
├── Dockerfile
├── pyproject.toml
├── requirements.txt
├── alembic/                    # Database migrations
│   ├── env.py
│   ├── alembic.ini
│   └── versions/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Settings management
│   ├── database.py             # Database connection
│   │
│   ├── api/                    # API Routes
│   │   ├── __init__.py
│   │   ├── deps.py             # Dependencies (auth, db session)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py       # Main router
│   │       ├── auth.py         # Authentication endpoints
│   │       ├── projects.py     # Project CRUD
│   │       ├── files.py        # File upload & processing
│   │       ├── items.py        # Line items management
│   │       ├── sec_codes.py    # SEC codes CRUD
│   │       ├── classify.py     # Classification endpoints
│   │       └── analytics.py    # Reports & dashboards
│   │
│   ├── models/                 # SQLAlchemy Models
│   │   ├── __init__.py
│   │   ├── base.py             # Base model class
│   │   ├── project.py
│   │   ├── boq_file.py
│   │   ├── line_item.py
│   │   ├── sec_code.py
│   │   └── user.py
│   │
│   ├── schemas/                # Pydantic Schemas
│   │   ├── __init__.py
│   │   ├── common.py           # Common response schemas
│   │   ├── project.py
│   │   ├── file.py
│   │   ├── item.py
│   │   ├── sec_code.py
│   │   └── auth.py
│   │
│   ├── services/               # Business Logic
│   │   ├── __init__.py
│   │   ├── project_service.py
│   │   ├── file_service.py
│   │   ├── item_service.py
│   │   ├── export_service.py
│   │   └── analytics_service.py
│   │
│   ├── ml/                     # ML Classification
│   │   ├── __init__.py
│   │   ├── classifier.py       # SECClassifier class
│   │   ├── preprocessor.py     # Text preprocessing
│   │   └── embeddings.py       # Embedding management
│   │
│   └── utils/                  # Utilities
│       ├── __init__.py
│       ├── logger.py
│       ├── validators.py
│       ├── file_processor.py   # Excel processing
│       └── unit_mapper.py      # Unit standardization
│
└── tests/
    ├── conftest.py
    ├── test_projects.py
    ├── test_files.py
    └── test_classifier.py
```

### 3.2 FastAPI Application (main.py)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base
from app.api.v1.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize ML model, database
    from app.ml.classifier import SECClassifier
    app.state.classifier = SECClassifier()
    yield
    # Shutdown: Cleanup

app = FastAPI(
    title="BOQ System API",
    description="BOQ Standardization System Backend",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### 3.3 SQLAlchemy Models

```python
# app/models/project.py
from sqlalchemy import Column, Integer, String, Enum, Date, Boolean, DECIMAL
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Project(BaseModel):
    __tablename__ = "projects"
    
    project_id = Column(Integer, primary_key=True, autoincrement=True)
    project_code = Column(String(50), unique=True, nullable=False, index=True)
    project_name = Column(String(255), nullable=False)
    project_type = Column(
        Enum('residential', 'commercial', 'industrial', 'infrastructure', 'other'),
        default='other'
    )
    location = Column(String(255))
    client_name = Column(String(255))
    contract_value = Column(DECIMAL(18, 2), default=0)
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(
        Enum('active', 'completed', 'cancelled', 'on_hold'),
        default='active'
    )
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    files = relationship("BOQFile", back_populates="project", cascade="all, delete-orphan")
    items = relationship("LineItem", back_populates="project")
```

### 3.4 Pydantic Schemas

```python
# app/schemas/project.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from enum import Enum

class ProjectType(str, Enum):
    residential = "residential"
    commercial = "commercial"
    industrial = "industrial"
    infrastructure = "infrastructure"
    other = "other"

class ProjectStatus(str, Enum):
    active = "active"
    completed = "completed"
    cancelled = "cancelled"
    on_hold = "on_hold"

class ProjectBase(BaseModel):
    project_code: str = Field(..., min_length=1, max_length=50)
    project_name: str = Field(..., min_length=1, max_length=255)
    project_type: ProjectType = ProjectType.other
    location: Optional[str] = None
    client_name: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    project_type: Optional[ProjectType] = None
    location: Optional[str] = None
    client_name: Optional[str] = None
    status: Optional[ProjectStatus] = None

class ProjectResponse(ProjectBase):
    project_id: int
    status: ProjectStatus
    file_count: int = 0
    total_items: int = 0
    
    class Config:
        from_attributes = True
```

### 3.5 Service Layer

```python
# app/services/project_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.models import Project, BOQFile
from app.schemas.project import ProjectCreate, ProjectUpdate

class ProjectService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> tuple[List[Project], int]:
        query = self.db.query(Project).filter(Project.is_deleted == False)
        
        if status:
            query = query.filter(Project.status == status)
        if search:
            query = query.filter(
                Project.project_name.ilike(f"%{search}%") |
                Project.project_code.ilike(f"%{search}%")
            )
        
        total = query.count()
        projects = query.offset(skip).limit(limit).all()
        return projects, total
    
    def create(self, data: ProjectCreate) -> Project:
        project = Project(**data.model_dump())
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project
    
    def update(self, project_id: int, data: ProjectUpdate) -> Optional[Project]:
        project = self.db.query(Project).filter(
            Project.project_id == project_id
        ).first()
        if not project:
            return None
        
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(project, key, value)
        
        self.db.commit()
        self.db.refresh(project)
        return project
```

---

## 4. FRONTEND ARCHITECTURE (React)

### 4.1 Project Structure

```
frontend/
├── Dockerfile
├── package.json
├── tsconfig.json
├── vite.config.ts
├── .env.example
│
├── public/
│   └── favicon.ico
│
└── src/
    ├── main.tsx                # Entry point
    ├── App.tsx                 # Root component
    ├── vite-env.d.ts
    │
    ├── api/                    # API Client
    │   ├── client.ts           # Axios instance
    │   ├── projects.ts         # Project API calls
    │   ├── files.ts            # File API calls
    │   ├── items.ts            # Items API calls
    │   └── types.ts            # API types
    │
    ├── components/             # Reusable Components
    │   ├── common/
    │   │   ├── PageHeader.tsx
    │   │   ├── DataTable.tsx
    │   │   ├── ConfirmModal.tsx
    │   │   └── LoadingSpinner.tsx
    │   ├── project/
    │   │   ├── ProjectCard.tsx
    │   │   ├── ProjectForm.tsx
    │   │   └── ProjectList.tsx
    │   ├── upload/
    │   │   ├── FileDropzone.tsx
    │   │   ├── ColumnMapper.tsx
    │   │   └── PreviewTable.tsx
    │   └── review/
    │       ├── ReviewTable.tsx
    │       ├── SecCodeSelect.tsx
    │       └── ConfidenceBadge.tsx
    │
    ├── pages/                  # Page Components
    │   ├── Dashboard.tsx
    │   ├── Projects.tsx
    │   ├── ProjectDetail.tsx
    │   ├── Upload.tsx
    │   ├── Review.tsx
    │   └── Analytics.tsx
    │
    ├── hooks/                  # Custom Hooks
    │   ├── useProjects.ts      # TanStack Query hooks
    │   ├── useFiles.ts
    │   ├── useItems.ts
    │   └── useDebounce.ts
    │
    ├── stores/                 # Zustand Stores
    │   ├── authStore.ts
    │   ├── uploadStore.ts
    │   └── uiStore.ts
    │
    ├── layouts/                # Layout Components
    │   ├── MainLayout.tsx
    │   └── AuthLayout.tsx
    │
    ├── types/                  # TypeScript Types
    │   ├── project.ts
    │   ├── file.ts
    │   ├── item.ts
    │   └── common.ts
    │
    ├── utils/                  # Utilities
    │   ├── formatters.ts
    │   ├── validators.ts
    │   └── constants.ts
    │
    └── styles/                 # Styles
        ├── global.css
        └── theme.ts            # Ant Design theme
```

### 4.2 API Client Setup

```typescript
// src/api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### 4.3 TanStack Query Hooks

```typescript
// src/hooks/useProjects.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/client';
import { Project, ProjectCreate, PaginatedResponse } from '../types';

export const useProjects = (params?: { page?: number; search?: string }) => {
  return useQuery({
    queryKey: ['projects', params],
    queryFn: async () => {
      const { data } = await apiClient.get<PaginatedResponse<Project>>('/projects', { params });
      return data;
    },
  });
};

export const useProject = (id: number) => {
  return useQuery({
    queryKey: ['project', id],
    queryFn: async () => {
      const { data } = await apiClient.get<Project>(`/projects/${id}`);
      return data;
    },
    enabled: !!id,
  });
};

export const useCreateProject = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (project: ProjectCreate) => {
      const { data } = await apiClient.post<Project>('/projects', project);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
};
```

### 4.4 Zustand Store

```typescript
// src/stores/uploadStore.ts
import { create } from 'zustand';

interface UploadState {
  file: File | null;
  preview: any[] | null;
  columnMapping: Record<string, string>;
  step: 'upload' | 'preview' | 'mapping' | 'processing' | 'complete';
  
  setFile: (file: File) => void;
  setPreview: (data: any[]) => void;
  setColumnMapping: (mapping: Record<string, string>) => void;
  setStep: (step: UploadState['step']) => void;
  reset: () => void;
}

export const useUploadStore = create<UploadState>((set) => ({
  file: null,
  preview: null,
  columnMapping: {},
  step: 'upload',
  
  setFile: (file) => set({ file }),
  setPreview: (preview) => set({ preview }),
  setColumnMapping: (mapping) => set({ columnMapping: mapping }),
  setStep: (step) => set({ step }),
  reset: () => set({ file: null, preview: null, columnMapping: {}, step: 'upload' }),
}));
```

### 4.5 Page Component Example

```tsx
// src/pages/Projects.tsx
import React, { useState } from 'react';
import { Table, Button, Input, Space, Card, Modal, message } from 'antd';
import { PlusOutlined, SearchOutlined } from '@ant-design/icons';
import { useProjects, useCreateProject, useDeleteProject } from '../hooks/useProjects';
import ProjectForm from '../components/project/ProjectForm';
import PageHeader from '../components/common/PageHeader';

const Projects: React.FC = () => {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  const { data, isLoading } = useProjects({ page, search });
  const createMutation = useCreateProject();
  
  const columns = [
    { title: 'Mã dự án', dataIndex: 'project_code', key: 'code' },
    { title: 'Tên dự án', dataIndex: 'project_name', key: 'name' },
    { title: 'Loại', dataIndex: 'project_type', key: 'type' },
    { title: 'Trạng thái', dataIndex: 'status', key: 'status' },
    { title: 'Số file', dataIndex: 'file_count', key: 'files' },
    {
      title: 'Thao tác',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button type="link" onClick={() => navigate(`/projects/${record.project_id}`)}>
            Xem
          </Button>
        </Space>
      ),
    },
  ];
  
  const handleCreate = async (values) => {
    try {
      await createMutation.mutateAsync(values);
      message.success('Tạo dự án thành công!');
      setIsModalOpen(false);
    } catch (error) {
      message.error('Có lỗi xảy ra');
    }
  };
  
  return (
    <>
      <PageHeader
        title="Quản lý dự án"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalOpen(true)}>
            Tạo dự án
          </Button>
        }
      />
      
      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Input
            placeholder="Tìm kiếm..."
            prefix={<SearchOutlined />}
            onChange={(e) => setSearch(e.target.value)}
          />
        </Space>
        
        <Table
          columns={columns}
          dataSource={data?.items}
          loading={isLoading}
          rowKey="project_id"
          pagination={{
            current: page,
            total: data?.total,
            pageSize: 20,
            onChange: setPage,
          }}
        />
      </Card>
      
      <Modal
        title="Tạo dự án mới"
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        footer={null}
      >
        <ProjectForm onSubmit={handleCreate} loading={createMutation.isPending} />
      </Modal>
    </>
  );
};

export default Projects;
```

---

## 5. ML CLASSIFICATION DESIGN

### 3.1 Algorithm Pipeline

```
┌─────────────────┐
│  Input Text     │
│  (Description)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Rule-Based     │  ←── Keywords, Regex patterns
│  Matching       │
└────────┬────────┘
         │ Match found?
    ┌────┴────┐
    │ YES     │ NO
    ▼         ▼
┌───────┐ ┌─────────────────┐
│Return │ │  Text Embedding │  ←── Vietnamese SBERT
│(95%)  │ │  (768-dim)      │
└───────┘ └────────┬────────┘
                   │
                   ▼
          ┌─────────────────┐
          │ Cosine          │  ←── Compare with SEC embeddings
          │ Similarity      │
          └────────┬────────┘
                   │
                   ▼
          ┌─────────────────┐
          │ Top-K Results   │
          │ (code, score)   │
          └─────────────────┘
```

### 3.2 Model Configuration

```python
MODEL_CONFIG = {
    'embedding_model': 'keepitreal/vietnamese-sbert',
    'embedding_dim': 768,
    'similarity_threshold': 0.5,
    'top_k': 3,
    'rule_confidence': 95.0,
    'min_confidence_for_auto': 80.0
}
```

### 3.3 Training Data Format

```json
{
    "sec_code": "SEC-01-01",
    "sec_name_vi": "Công tác đất",
    "sec_name_en": "Earthwork",
    "training_texts": [
        "đào đất móng",
        "đắp đất nền",
        "san lấp mặt bằng",
        "vận chuyển đất"
    ],
    "keywords": ["đào", "đắp", "san lấp", "đất"],
    "synonyms": ["earthwork", "excavation"]
}
```

---

## 4. API DESIGN

### 4.1 Internal API Methods

```python
# Project Operations
def create_project(project_code, project_name, project_type, **kwargs) -> int
def get_project(project_id) -> dict
def update_project(project_id, **kwargs) -> bool
def delete_project(project_id) -> bool
def list_projects(filters=None, page=1, limit=20) -> dict

# File Operations
def upload_file(project_id, file, user=None) -> int
def get_file(file_id) -> dict
def delete_file(file_id) -> bool
def get_files_by_project(project_id) -> list

# Line Item Operations
def get_line_items(project_id=None, file_id=None, filters=None, page=1, limit=100) -> dict
def update_line_item(line_item_id, **kwargs) -> bool
def bulk_update_items(item_ids, sec_code, user=None) -> int
def get_pending_review(project_id=None) -> list

# Classification
def classify_text(description, top_k=3) -> list
def classify_batch(descriptions) -> list
def retrain_model() -> bool

# Reports
def get_dashboard_stats() -> dict
def get_sec_distribution(project_id=None) -> dict
def export_report(project_id, format='xlsx') -> bytes
```

### 4.2 Response Format

```python
# Success Response
{
    "success": True,
    "data": {...},
    "message": "Operation successful",
    "timestamp": "2026-01-12T10:30:00Z"
}

# Error Response
{
    "success": False,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid project_code",
        "details": {...}
    },
    "timestamp": "2026-01-12T10:30:00Z"
}

# Paginated Response
{
    "success": True,
    "data": [...],
    "pagination": {
        "page": 1,
        "limit": 20,
        "total": 150,
        "pages": 8
    }
}
```

---

## 5. ERROR HANDLING

### 5.1 Error Codes

| Code | Category | Description |
|------|----------|-------------|
| E001 | Database | Connection failed |
| E002 | Database | Query execution error |
| E003 | Database | Duplicate entry |
| E010 | File | Invalid file format |
| E011 | File | File too large |
| E012 | File | Duplicate file |
| E020 | Validation | Required field missing |
| E021 | Validation | Invalid data type |
| E030 | ML | Model not loaded |
| E031 | ML | Classification failed |

### 5.2 Exception Classes

```python
class BOQException(Exception):
    """Base exception for BOQ system"""
    pass

class DatabaseException(BOQException):
    """Database related errors"""
    pass

class FileProcessingException(BOQException):
    """File processing errors"""
    pass

class ValidationException(BOQException):
    """Data validation errors"""
    pass

class ClassificationException(BOQException):
    """ML classification errors"""
    pass
```

---

## 6. LOGGING STRATEGY

### 6.1 Log Levels

| Level | Usage |
|-------|-------|
| DEBUG | Detailed debugging information |
| INFO | General operational events |
| WARNING | Warning conditions |
| ERROR | Error conditions |
| CRITICAL | Critical conditions |

### 6.2 Log Format

```python
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d | %(message)s"

# Example output:
# 2026-01-12 10:30:00 | INFO     | database:45 | Connected to MySQL
# 2026-01-12 10:30:01 | ERROR    | processor:123 | Failed to parse file: invalid format
```

### 6.3 Log Categories

```
logs/
├── app.log           # Main application log
├── database.log      # Database operations
├── processing.log    # File processing
├── classification.log # ML classification
└── error.log         # All errors (aggregated)
```

---

## 7. CONFIGURATION

### 7.1 Environment Variables

```bash
# .env.example

# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=boq_user
DB_PASSWORD=your_secure_password
DB_NAME=boq_system

# Application
APP_ENV=development
APP_DEBUG=true
APP_SECRET_KEY=your_secret_key

# ML
ML_MODEL_PATH=models/
ML_THRESHOLD=80

# Upload
UPLOAD_MAX_SIZE=52428800  # 50MB
UPLOAD_ALLOWED_EXTENSIONS=.xlsx,.xls

# Logging
LOG_LEVEL=INFO
LOG_PATH=logs/
```

### 7.2 Configuration Classes

```python
from dataclasses import dataclass
from pathlib import Path
import os

@dataclass
class AppConfig:
    ENV: str = os.getenv('APP_ENV', 'development')
    DEBUG: bool = os.getenv('APP_DEBUG', 'false').lower() == 'true'
    SECRET_KEY: str = os.getenv('APP_SECRET_KEY', 'dev-secret')

@dataclass
class DatabaseConfig:
    HOST: str = os.getenv('DB_HOST', 'localhost')
    PORT: int = int(os.getenv('DB_PORT', '3306'))
    USER: str = os.getenv('DB_USER', 'boq_user')
    PASSWORD: str = os.getenv('DB_PASSWORD', '')
    DATABASE: str = os.getenv('DB_NAME', 'boq_system')

@dataclass
class MLConfig:
    MODEL_PATH: Path = Path(os.getenv('ML_MODEL_PATH', 'models/'))
    THRESHOLD: float = float(os.getenv('ML_THRESHOLD', '80'))
    EMBEDDING_MODEL: str = 'keepitreal/vietnamese-sbert'
```

---

## 8. TESTING STRATEGY

### 8.1 Test Categories

| Type | Coverage | Tools |
|------|----------|-------|
| Unit Tests | Individual functions | pytest |
| Integration Tests | Module interactions | pytest + fixtures |
| E2E Tests | Full workflows | Selenium / Playwright |
| Performance Tests | Load testing | locust |

### 8.2 Test Structure

```
tests/
├── __init__.py
├── conftest.py           # Shared fixtures
├── unit/
│   ├── test_database.py
│   ├── test_processor.py
│   ├── test_classifier.py
│   └── test_validators.py
├── integration/
│   ├── test_upload_flow.py
│   ├── test_classification_flow.py
│   └── test_report_flow.py
├── fixtures/
│   ├── sample_boq.xlsx
│   └── test_data.json
└── performance/
    └── test_load.py
```

### 8.3 Test Examples

```python
# tests/unit/test_processor.py
import pytest
from modules.file_processor import FileProcessor

class TestFileProcessor:
    @pytest.fixture
    def processor(self):
        return FileProcessor()
    
    def test_standardize_unit_m2(self, processor):
        assert processor._standardize_unit('m2') == 'm2'
        assert processor._standardize_unit('m²') == 'm2'
        assert processor._standardize_unit('sqm') == 'm2'
    
    def test_clean_data_removes_empty_rows(self, processor, sample_df):
        cleaned = processor.clean_data(sample_df, {})
        assert cleaned['description'].isna().sum() == 0
```

---

## 📝 Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-12 | AI Assistant | Initial version |
