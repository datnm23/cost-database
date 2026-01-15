# BOQ SYSTEM - IMPROVEMENT PROPOSALS

**Version:** 1.0  
**Created:** January 12, 2026  
**Status:** Draft

---

## 📋 Executive Summary

Tài liệu này đề xuất các cải tiến cho hệ thống BOQ Standardization dựa trên phân tích tài liệu hướng dẫn triển khai hiện tại.

---

## 1. PHÂN TÍCH HIỆN TRẠNG

### 1.1 Điểm Mạnh ✅

| Khía cạnh | Đánh giá | Chi tiết |
|-----------|----------|----------|
| Kiến trúc | Tốt | Phân tách rõ ràng 3 layers |
| Tech Stack | Phù hợp | MySQL + Python + Streamlit |
| ML Integration | Xuất sắc | Sử dụng Vietnamese SBERT |
| Documentation | Khá | Có đầy đủ các phần cơ bản |
| Deployment | Tốt | Docker-based, dễ triển khai |

### 1.2 Điểm Yếu ⚠️

| Khía cạnh | Vấn đề | Mức độ |
|-----------|--------|--------|
| Security | Credentials hardcoded | High |
| Testing | Không có test cases | High |
| Error Handling | Quá đơn giản | Medium |
| Logging | Chưa structured | Medium |
| Validation | Thiếu input validation | Medium |
| Scalability | Single-user only | Low |
| Code Quality | Thiếu type hints | Low |

---

## 2. ĐỀ XUẤT CẢI TIẾN

### 2.1 Security Improvements (Priority: HIGH)

#### 2.1.1 Environment Variables

**Current Issue:** Passwords hardcoded trong docker-compose.yml

**Proposal:**
```yaml
# docker-compose.yml - BEFORE
environment:
  MYSQL_ROOT_PASSWORD: root_password_123

# docker-compose.yml - AFTER  
environment:
  MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
```

```bash
# .env file
DB_ROOT_PASSWORD=secure_random_password_here
DB_USER=boq_user
DB_PASSWORD=another_secure_password
```

**Benefits:**
- Không expose passwords trong code
- Dễ thay đổi credentials
- Tách biệt config giữa environments

#### 2.1.2 Input Validation

**Proposal:** Thêm module validation

```python
# utils/validators.py
from typing import Optional
import re

class Validators:
    @staticmethod
    def validate_project_code(code: str) -> tuple[bool, Optional[str]]:
        if not code:
            return False, "Project code is required"
        if len(code) > 50:
            return False, "Project code must be <= 50 characters"
        if not re.match(r'^[A-Z0-9_-]+$', code.upper()):
            return False, "Invalid characters in project code"
        return True, None
    
    @staticmethod
    def validate_file_upload(file) -> tuple[bool, Optional[str]]:
        allowed_extensions = ['.xlsx', '.xls']
        max_size = 50 * 1024 * 1024  # 50MB
        
        if not file:
            return False, "No file uploaded"
        
        ext = Path(file.name).suffix.lower()
        if ext not in allowed_extensions:
            return False, f"Invalid file type. Allowed: {allowed_extensions}"
        
        if file.size > max_size:
            return False, f"File too large. Max: {max_size // 1024 // 1024}MB"
        
        return True, None
```

#### 2.1.3 SQL Injection Prevention

**Current:** Sử dụng parameterized queries (tốt)

**Enhancement:** Thêm additional sanitization

```python
def sanitize_search_input(query: str) -> str:
    """Remove potentially dangerous characters from search queries"""
    # Remove SQL wildcards that could cause issues
    dangerous_chars = ['%', '_', ';', '--', '/*', '*/']
    for char in dangerous_chars:
        query = query.replace(char, '')
    return query.strip()
```

---

### 2.2 Error Handling (Priority: HIGH)

#### 2.2.1 Custom Exception Classes

```python
# utils/exceptions.py
class BOQException(Exception):
    """Base exception for BOQ system"""
    def __init__(self, message: str, code: str = None, details: dict = None):
        self.message = message
        self.code = code or "UNKNOWN_ERROR"
        self.details = details or {}
        super().__init__(self.message)

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

#### 2.2.2 Global Error Handler

```python
# utils/error_handler.py
import streamlit as st
import traceback
from utils.logger import get_logger

logger = get_logger(__name__)

def handle_error(func):
    """Decorator for handling errors gracefully"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationException as e:
            st.warning(f"⚠️ {e.message}")
            logger.warning(f"Validation error: {e.message}")
        except DatabaseException as e:
            st.error(f"❌ Database error: {e.message}")
            logger.error(f"Database error: {e.message}", exc_info=True)
        except Exception as e:
            st.error(f"❌ Unexpected error occurred")
            logger.critical(f"Unexpected error: {str(e)}", exc_info=True)
    return wrapper
```

---

### 2.3 Testing Infrastructure (Priority: HIGH)

#### 2.3.1 Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── unit/
│   ├── __init__.py
│   ├── test_database.py
│   ├── test_processor.py
│   ├── test_classifier.py
│   └── test_validators.py
├── integration/
│   ├── __init__.py
│   ├── test_upload_flow.py
│   └── test_classification_flow.py
└── fixtures/
    ├── sample_boq.xlsx
    └── test_sec_codes.json
```

#### 2.3.2 Sample Test Cases

```python
# tests/conftest.py
import pytest
import pandas as pd
from modules.database import Database

@pytest.fixture
def db():
    """Database fixture with test connection"""
    return Database(test_mode=True)

@pytest.fixture
def sample_df():
    """Sample DataFrame for testing"""
    return pd.DataFrame({
        'Description': ['Đào đất móng', 'Đổ bê tông', ''],
        'Unit': ['m3', 'm3', 'm2'],
        'Quantity': [100, 50, None],
        'Unit Price': [150000, 2500000, 0],
        'Amount': [15000000, 125000000, 0]
    })

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
        assert processor._standardize_unit('SQM') == 'm2'
    
    def test_standardize_unit_unknown(self, processor):
        assert processor._standardize_unit('unknown') == 'unknown'
        assert processor._standardize_unit(None) == 'pcs'
    
    def test_clean_data_removes_empty_descriptions(self, processor, sample_df):
        column_mapping = {'Description': 'description', 'Unit': 'unit'}
        cleaned = processor.clean_data(sample_df, column_mapping)
        assert '' not in cleaned['description'].values
        assert len(cleaned) == 2

# tests/unit/test_database.py
import pytest
from modules.database import Database

class TestDatabase:
    def test_connection(self, db):
        assert db.test_connection() == True
    
    def test_create_project(self, db):
        project_id = db.create_project(
            project_code='TEST-001',
            project_name='Test Project',
            project_type='residential'
        )
        assert project_id > 0
        
        # Cleanup
        db.execute_query("DELETE FROM projects WHERE project_id = %s", (project_id,), fetch=False)
```

#### 2.3.3 pytest Configuration

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
```

---

### 2.4 Logging System (Priority: MEDIUM)

#### 2.4.1 Structured Logging

```python
# utils/logger.py
import logging
import logging.handlers
import json
from datetime import datetime
from pathlib import Path

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    def format(self, record):
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage()
        }
        
        if hasattr(record, 'extra'):
            log_obj['extra'] = record.extra
        
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_obj)

def setup_logging(log_path: str = 'logs/', level: str = 'INFO'):
    """Setup application logging"""
    Path(log_path).mkdir(exist_ok=True)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
    ))
    root_logger.addHandler(console_handler)
    
    # File handler (JSON)
    file_handler = logging.handlers.RotatingFileHandler(
        f'{log_path}/app.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        f'{log_path}/error.log',
        maxBytes=10*1024*1024,
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(error_handler)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)
```

---

### 2.5 Code Quality Improvements (Priority: MEDIUM)

#### 2.5.1 Type Hints

```python
# BEFORE
def create_project(self, project_code, project_name, project_type, **kwargs):
    pass

# AFTER
from typing import Optional, Dict, Any

def create_project(
    self,
    project_code: str,
    project_name: str,
    project_type: str,
    location: Optional[str] = None,
    client_name: Optional[str] = None,
    contract_value: Optional[float] = None,
    **kwargs: Dict[str, Any]
) -> int:
    """
    Create a new project.
    
    Args:
        project_code: Unique project identifier
        project_name: Project display name
        project_type: Type of project (residential, commercial, etc.)
        location: Project location (optional)
        client_name: Client name (optional)
        contract_value: Contract value in VND (optional)
        **kwargs: Additional fields
    
    Returns:
        int: Created project ID
    
    Raises:
        ValidationException: If required fields are missing
        DatabaseException: If database operation fails
    """
    pass
```

#### 2.5.2 Code Organization

```python
# config.py - Improved structure
from dataclasses import dataclass, field
from typing import List
import os
from pathlib import Path

@dataclass
class AppConfig:
    ENV: str = field(default_factory=lambda: os.getenv('APP_ENV', 'development'))
    DEBUG: bool = field(default_factory=lambda: os.getenv('APP_DEBUG', 'false').lower() == 'true')
    SECRET_KEY: str = field(default_factory=lambda: os.getenv('APP_SECRET_KEY', 'dev-secret'))
    BASE_DIR: Path = field(default_factory=lambda: Path(__file__).parent)

@dataclass
class DatabaseConfig:
    HOST: str = field(default_factory=lambda: os.getenv('DB_HOST', 'localhost'))
    PORT: int = field(default_factory=lambda: int(os.getenv('DB_PORT', '3306')))
    USER: str = field(default_factory=lambda: os.getenv('DB_USER', 'boq_user'))
    PASSWORD: str = field(default_factory=lambda: os.getenv('DB_PASSWORD', ''))
    DATABASE: str = field(default_factory=lambda: os.getenv('DB_NAME', 'boq_system'))
    CHARSET: str = 'utf8mb4'
    POOL_SIZE: int = 5
    POOL_TIMEOUT: int = 30

@dataclass
class MLConfig:
    MODEL_PATH: Path = field(default_factory=lambda: Path(os.getenv('ML_MODEL_PATH', 'models/')))
    EMBEDDING_MODEL: str = 'keepitreal/vietnamese-sbert'
    THRESHOLD: float = field(default_factory=lambda: float(os.getenv('ML_THRESHOLD', '80')))
    TOP_K: int = 3

@dataclass
class UploadConfig:
    MAX_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: List[str] = field(default_factory=lambda: ['.xlsx', '.xls'])
    UPLOAD_DIR: Path = field(default_factory=lambda: Path('uploads/'))

@dataclass
class Config:
    app: AppConfig = field(default_factory=AppConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    ml: MLConfig = field(default_factory=MLConfig)
    upload: UploadConfig = field(default_factory=UploadConfig)

config = Config()
```

---

### 2.6 Performance Optimizations (Priority: MEDIUM)

#### 2.6.1 Database Connection Pool

```python
# modules/database.py - With connection pooling
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

class Database:
    _engine = None
    
    def __init__(self):
        if Database._engine is None:
            Database._engine = create_engine(
                f"mysql+pymysql://{config.database.USER}:{config.database.PASSWORD}@"
                f"{config.database.HOST}:{config.database.PORT}/{config.database.DATABASE}",
                poolclass=QueuePool,
                pool_size=config.database.POOL_SIZE,
                max_overflow=10,
                pool_timeout=config.database.POOL_TIMEOUT,
                pool_recycle=3600
            )
        self.engine = Database._engine
```

#### 2.6.2 Batch Processing

```python
# Batch insert for better performance
def save_line_items_batch(self, file_id: int, project_id: int, items: List[dict]) -> int:
    """Insert multiple line items in a single query"""
    if not items:
        return 0
    
    query = """
        INSERT INTO line_items 
        (file_id, project_id, row_number, description, unit, quantity, 
         unit_price, amount, sec_code, confidence_score)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    values = [
        (file_id, project_id, item['row_number'], item['description'],
         item['unit'], item['quantity'], item['unit_price'], item['amount'],
         item.get('sec_code'), item.get('confidence', 0))
        for item in items
    ]
    
    with self.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(query, values)
    
    return len(items)
```

#### 2.6.3 Caching

```python
# utils/cache.py
from functools import lru_cache
import streamlit as st

# In-memory cache for SEC codes
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_cached_sec_codes():
    db = Database()
    return db.get_all_sec_codes()

# Cache ML model
@st.cache_resource
def get_cached_classifier():
    db = Database()
    return SECClassifier(db)
```

---

### 2.7 UX Improvements (Priority: LOW)

#### 2.7.1 Progress Indicators

```python
# Better progress feedback
def process_file_with_progress(file, project_id):
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Step 1: Read file
    status_text.text("📖 Reading Excel file...")
    progress_bar.progress(10)
    df = processor.read_excel(file)
    
    # Step 2: Detect structure
    status_text.text("🔍 Detecting structure...")
    progress_bar.progress(20)
    structure = processor.detect_structure(df)
    
    # Step 3: Clean data
    status_text.text("🧹 Cleaning data...")
    progress_bar.progress(30)
    df_clean = processor.clean_data(df, structure['column_mapping'])
    
    # Step 4: Classify
    total = len(df_clean)
    for i, (idx, row) in enumerate(df_clean.iterrows()):
        progress = 30 + int(60 * (i + 1) / total)
        status_text.text(f"🤖 Classifying item {i+1}/{total}...")
        progress_bar.progress(progress)
        # ... classify logic
    
    # Step 5: Save
    status_text.text("💾 Saving to database...")
    progress_bar.progress(95)
    # ... save logic
    
    progress_bar.progress(100)
    status_text.text("✅ Complete!")
```

#### 2.7.2 Toast Notifications

```python
# utils/notifications.py
import streamlit as st

def show_success(message: str):
    st.toast(f"✅ {message}", icon="✅")

def show_error(message: str):
    st.toast(f"❌ {message}", icon="❌")

def show_warning(message: str):
    st.toast(f"⚠️ {message}", icon="⚠️")

def show_info(message: str):
    st.toast(f"ℹ️ {message}", icon="ℹ️")
```

---

## 3. IMPLEMENTATION ROADMAP

### Phase 1: Foundation (Week 1)

| Task | Priority | Effort |
|------|----------|--------|
| Setup .env configuration | High | 2h |
| Implement exception classes | High | 4h |
| Setup logging system | Medium | 4h |
| Create base validators | High | 4h |

### Phase 2: Quality (Week 2)

| Task | Priority | Effort |
|------|----------|--------|
| Setup pytest infrastructure | High | 4h |
| Write unit tests - database | High | 4h |
| Write unit tests - processor | High | 4h |
| Write unit tests - classifier | High | 4h |
| Add type hints | Medium | 4h |

### Phase 3: Performance (Week 3)

| Task | Priority | Effort |
|------|----------|--------|
| Implement connection pool | Medium | 4h |
| Add batch processing | Medium | 4h |
| Implement caching | Medium | 4h |
| Performance testing | Medium | 4h |

### Phase 4: Polish (Week 4)

| Task | Priority | Effort |
|------|----------|--------|
| UX improvements | Low | 8h |
| Documentation updates | Medium | 4h |
| Integration tests | Medium | 8h |
| Final review | High | 4h |

---

## 4. SUCCESS METRICS

| Metric | Current | Target |
|--------|---------|--------|
| Test Coverage | 0% | >70% |
| Response Time | Unknown | <3s |
| Error Rate | Unknown | <5% |
| Security Score | Low | High |
| Code Quality | Medium | High |

---

## 📝 Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-12 | AI Assistant | Initial version |
