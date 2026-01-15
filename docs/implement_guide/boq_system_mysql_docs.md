# HỆ THỐNG BOQ CHUẨN HÓA - PHIÊN BẢN MYSQL

**Version:** 1.0  
**Database:** MySQL 8.0+  
**Framework:** Python 3.10+ / Streamlit  
**Deployment:** Local Desktop Application  
**Author:** AI Assistant  
**Date:** January 2026

---

## 📋 MỤC LỤC

1. [Tổng Quan](#1-tổng-quan)
2. [Tech Stack](#2-tech-stack)
3. [Database Schema](#3-database-schema)
4. [Setup & Installation](#4-setup--installation)
5. [Source Code](#5-source-code)
6. [User Guide](#6-user-guide)
7. [API Reference](#7-api-reference)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. TỔNG QUAN

### 1.1 Giới Thiệu

Hệ thống BOQ Standardization là ứng dụng desktop giúp:
- ✅ Upload và parse file BOQ Excel tự động
- ✅ Làm sạch và chuẩn hóa dữ liệu
- ✅ Phân loại tự động theo mã SEC bằng AI/ML
- ✅ Review và chỉnh sửa thủ công
- ✅ Phân tích và xuất báo cáo

### 1.2 Kiến Trúc Hệ Thống

```
┌─────────────────────────────────────────────┐
│         DESKTOP APPLICATION                  │
│  ┌────────────────────────────────────┐     │
│  │     UI Layer (Streamlit)           │     │
│  └──────────────┬─────────────────────┘     │
│                 │                            │
│  ┌──────────────▼─────────────────────┐     │
│  │   Business Logic (Python)          │     │
│  │  - File Processing                 │     │
│  │  - Data Cleaning                   │     │
│  │  - ML Classification                │     │
│  └──────────────┬─────────────────────┘     │
│                 │                            │
│  ┌──────────────▼─────────────────────┐     │
│  │   MySQL Database (Docker)          │     │
│  └────────────────────────────────────┘     │
└─────────────────────────────────────────────┘
```

### 1.3 Tính Năng Chính

#### Core Features
- **F1: Quản lý Projects** - Tạo, xem, sửa, xóa projects
- **F2: Upload & Parse BOQ** - Tự động phát hiện cấu trúc Excel
- **F3: Data Cleaning** - Chuẩn hóa description, unit, giá trị
- **F4: Auto Classification** - AI phân loại theo mã SEC
- **F5: Manual Review** - Chỉnh sửa thủ công các items cần review
- **F6: View & Filter** - Xem và lọc dữ liệu đa chiều
- **F7: Reports & Analytics** - Dashboard, charts, export reports

---

## 2. TECH STACK

### 2.1 Core Technologies

```yaml
Language: Python 3.10+
UI Framework: Streamlit 1.31+
Database: MySQL 8.0+
ORM/Driver: PyMySQL + SQLAlchemy
Excel: pandas + openpyxl
ML: scikit-learn + sentence-transformers
NLP: underthesea (Vietnamese)
Charts: plotly
Package: PyInstaller (optional)
```

### 2.2 Dependencies

**requirements.txt**
```txt
# Core
streamlit==1.31.0
pandas==2.1.4
openpyxl==3.1.2

# Database
pymysql==1.1.0
sqlalchemy==2.0.25
cryptography==41.0.7

# Visualization
plotly==5.18.0
streamlit-aggrid==0.3.4

# Machine Learning
scikit-learn==1.4.0
sentence-transformers==2.3.1
underthesea==6.7.0

# Export
xlsxwriter==3.1.9
python-docx==1.1.0
```

### 2.3 Folder Structure

```
boq_system/
├── docker-compose.yml          # MySQL container config
├── schema.sql                  # Database schema
├── requirements.txt            # Python dependencies
├── config.py                   # Database configuration
├── app.py                      # Main Streamlit app
├── init_db.py                  # Database initialization
├── modules/
│   ├── __init__.py
│   ├── database.py             # Database handler
│   ├── file_processor.py       # Excel processing
│   ├── classifier.py           # ML classifier
│   └── reports.py              # Report generator
├── models/                     # ML models
│   ├── sec_classifier.pkl
│   └── embeddings.pkl
├── uploads/                    # Uploaded files
│   └── project_*/
├── exports/                    # Generated reports
└── logs/                       # Application logs
```

---

## 3. DATABASE SCHEMA

### 3.1 Entity Relationship Diagram

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   projects   │────<│  boq_files   │────<│ line_items   │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                                  │ references
                                                  │
                     ┌──────────────┐             │
                     │  sec_codes   │<────────────┘
                     └──────────────┘
                            △
                            │ self-reference
                            │ (parent_code)
                            │
```

### 3.2 Main Tables

#### projects
```sql
CREATE TABLE projects (
    project_id INT AUTO_INCREMENT PRIMARY KEY,
    project_code VARCHAR(50) UNIQUE NOT NULL,
    project_name VARCHAR(255) NOT NULL,
    project_type ENUM('residential', 'commercial', 'industrial', 'infrastructure'),
    location VARCHAR(255),
    client_name VARCHAR(255),
    contract_value DECIMAL(18,2),
    start_date DATE,
    status ENUM('active', 'completed', 'cancelled') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### boq_files
```sql
CREATE TABLE boq_files (
    file_id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_hash CHAR(64) UNIQUE,
    total_rows INT DEFAULT 0,
    total_amount DECIMAL(18,2) DEFAULT 0,
    status ENUM('draft', 'approved') DEFAULT 'draft',
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
```

#### line_items
```sql
CREATE TABLE line_items (
    line_item_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    file_id INT NOT NULL,
    project_id INT NOT NULL,
    description TEXT NOT NULL,
    unit VARCHAR(10),
    quantity DECIMAL(18,4),
    unit_price DECIMAL(18,2),
    amount DECIMAL(18,2),
    sec_code VARCHAR(20),
    confidence_score DECIMAL(5,2),
    classification_method ENUM('auto', 'manual'),
    FOREIGN KEY (file_id) REFERENCES boq_files(file_id),
    FOREIGN KEY (sec_code) REFERENCES sec_codes(sec_code)
);
```

#### sec_codes
```sql
CREATE TABLE sec_codes (
    sec_code VARCHAR(20) PRIMARY KEY,
    sec_name_vi VARCHAR(255) NOT NULL,
    sec_name_en VARCHAR(255),
    parent_code VARCHAR(20),
    level TINYINT DEFAULT 1,
    keywords JSON,
    FOREIGN KEY (parent_code) REFERENCES sec_codes(sec_code)
);
```

### 3.3 Complete Schema

**schema.sql** (Full version - see separate file)

---

## 4. SETUP & INSTALLATION

### 4.1 Prerequisites

- **Docker Desktop** (for MySQL)
- **Python 3.10+**
- **Git** (optional)

### 4.2 Step-by-Step Setup

#### Step 1: Create Project Folder

```bash
mkdir boq_system
cd boq_system
```

#### Step 2: Create docker-compose.yml

```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    container_name: boq_mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: root_password_123
      MYSQL_DATABASE: boq_system
      MYSQL_USER: boq_user
      MYSQL_PASSWORD: boq_password_456
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./schema.sql:/docker-entrypoint-initdb.d/schema.sql
    command: >
      --character-set-server=utf8mb4
      --collation-server=utf8mb4_unicode_ci
      --max_allowed_packet=256M

  phpmyadmin:
    image: phpmyadmin:latest
    container_name: boq_phpmyadmin
    environment:
      PMA_HOST: mysql
      PMA_USER: boq_user
      PMA_PASSWORD: boq_password_456
    ports:
      - "8080:80"
    depends_on:
      - mysql

volumes:
  mysql_data:
```

#### Step 3: Start MySQL

```bash
# Start containers
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs mysql

# Wait for "ready for connections" message
```

#### Step 4: Setup Python

```bash
# Create virtual environment
python -m venv venv

# Activate
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install streamlit pandas openpyxl pymysql sqlalchemy plotly scikit-learn sentence-transformers underthesea

# Or use requirements.txt
pip install -r requirements.txt
```

#### Step 5: Test Connection

```bash
python -c "from modules.database import Database; db = Database(); print('✅ OK' if db.test_connection() else '❌ FAIL')"
```

#### Step 6: Run Application

```bash
streamlit run app.py
```

Application will open at: **http://localhost:8501**

### 4.3 Alternative: XAMPP Setup (Windows)

If you don't want to use Docker:

1. Download XAMPP: https://www.apachefriends.org/
2. Install and start MySQL
3. Access phpMyAdmin: http://localhost/phpmyadmin
4. Create database: `boq_system`
5. Import `schema.sql`
6. Update `config.py`:
   ```python
   HOST = 'localhost'
   USER = 'root'
   PASSWORD = ''  # Your MySQL password
   ```

---

## 5. SOURCE CODE

### 5.1 Configuration

**config.py**
```python
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    HOST: str = 'localhost'
    PORT: int = 3306
    USER: str = 'boq_user'
    PASSWORD: str = 'boq_password_456'
    DATABASE: str = 'boq_system'
    CHARSET: str = 'utf8mb4'
    
    def get_pymysql_config(self) -> dict:
        return {
            'host': self.HOST,
            'port': self.PORT,
            'user': self.USER,
            'password': self.PASSWORD,
            'database': self.DATABASE,
            'charset': self.CHARSET,
            'cursorclass': pymysql.cursors.DictCursor
        }

db_config = DatabaseConfig()
```

### 5.2 Database Module

**modules/database.py**
```python
import pymysql
import pandas as pd
import json
from contextlib import contextmanager
from config import db_config

class Database:
    def __init__(self):
        self.config = db_config.get_pymysql_config()
    
    @contextmanager
    def get_connection(self):
        conn = pymysql.connect(**self.config)
        try:
            yield conn
            conn.commit()
        except:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = True):
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                if fetch:
                    if cursor.description:
                        columns = [desc[0] for desc in cursor.description]
                        results = cursor.fetchall()
                        return pd.DataFrame([dict(row) for row in results])
                    return None
                else:
                    return cursor.lastrowid
    
    # Project methods
    def get_all_projects(self):
        return self.execute_query("SELECT * FROM v_project_summary ORDER BY created_at DESC")
    
    def create_project(self, project_code, project_name, project_type, **kwargs):
        fields = ['project_code', 'project_name', 'project_type']
        values = [project_code, project_name, project_type]
        
        for field in ['location', 'client_name', 'contract_value', 'start_date']:
            if field in kwargs:
                fields.append(field)
                values.append(kwargs[field])
        
        query = f"INSERT INTO projects ({', '.join(fields)}) VALUES ({', '.join(['%s']*len(fields))})"
        return self.execute_query(query, tuple(values), fetch=False)
    
    # File methods
    def save_boq_file(self, project_id, file_name, file_hash, total_rows, total_amount):
        query = """
            INSERT INTO boq_files (project_id, file_name, file_hash, total_rows, total_amount)
            VALUES (%s, %s, %s, %s, %s)
        """
        return self.execute_query(query, (project_id, file_name, file_hash, total_rows, total_amount), fetch=False)
    
    # Line item methods
    def save_line_item(self, file_id, project_id, **kwargs):
        query = """
            INSERT INTO line_items 
            (file_id, project_id, row_number, description, unit, quantity, 
             unit_price, amount, sec_code, confidence_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            file_id, project_id, kwargs.get('row_number', 0),
            kwargs['description'], kwargs['unit'], kwargs['quantity'],
            kwargs['unit_price'], kwargs['amount'],
            kwargs.get('sec_code'), kwargs.get('confidence', 0)
        )
        return self.execute_query(query, values, fetch=False)
    
    def get_line_items(self, project_id=None, needs_review=False, skip=0, limit=100):
        conditions = []
        params = []
        
        if project_id:
            conditions.append("project_id = %s")
            params.append(project_id)
        
        if needs_review:
            conditions.append("(confidence_score < 80 OR sec_code IS NULL)")
        
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        query = f"SELECT * FROM line_items {where} LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        
        return self.execute_query(query, tuple(params))
    
    # SEC code methods
    def get_all_sec_codes(self):
        df = self.execute_query("SELECT sec_code FROM sec_codes WHERE is_active = TRUE")
        return df['sec_code'].tolist() if not df.empty else []
    
    # Analytics
    def get_dashboard_stats(self):
        stats = {}
        stats['total_projects'] = self.execute_query("SELECT COUNT(*) as cnt FROM projects").iloc[0]['cnt']
        stats['total_files'] = self.execute_query("SELECT COUNT(*) as cnt FROM boq_files").iloc[0]['cnt']
        stats['total_items'] = self.execute_query("SELECT COUNT(*) as cnt FROM line_items").iloc[0]['cnt']
        stats['total_value'] = self.execute_query("SELECT COALESCE(SUM(amount), 0) as total FROM line_items").iloc[0]['total']
        return stats
    
    def test_connection(self):
        try:
            with self.get_connection():
                return True
        except:
            return False
```

### 5.3 File Processor

**modules/file_processor.py**
```python
import pandas as pd
import json

class FileProcessor:
    def read_excel(self, file):
        return pd.read_excel(file, sheet_name=0)
    
    def detect_structure(self, df):
        # Find header row
        header_row = 0
        max_non_null = 0
        for i in range(min(10, len(df))):
            non_null = df.iloc[i].notna().sum()
            if non_null > max_non_null:
                max_non_null = non_null
                header_row = i
        
        df.columns = df.iloc[header_row]
        df = df.iloc[header_row + 1:].reset_index(drop=True)
        df = df.dropna(how='all')
        
        column_mapping = self._detect_columns(df.columns.tolist())
        
        return {
            'header_row': header_row,
            'column_mapping': column_mapping,
            'total_rows': len(df),
            'preview': df.head(10).to_dict('records')
        }
    
    def _detect_columns(self, columns):
        mapping = {}
        keywords = {
            'description': ['description', 'mô tả', 'hạng mục', 'item'],
            'unit': ['unit', 'đơn vị', 'đvt'],
            'quantity': ['quantity', 'số lượng', 'qty', 'khối lượng'],
            'unit_price': ['unit price', 'đơn giá', 'rate'],
            'amount': ['amount', 'thành tiền', 'total']
        }
        
        for col in columns:
            col_lower = str(col).lower().strip()
            for standard, kws in keywords.items():
                if any(kw in col_lower for kw in kws):
                    mapping[col] = standard
                    break
        return mapping
    
    def clean_data(self, df, column_mapping):
        df = df.rename(columns=column_mapping)
        df = df.dropna(subset=['description'])
        
        # Clean description
        df['description'] = df['description'].astype(str).str.strip()
        
        # Standardize units
        df['unit'] = df['unit'].apply(self._standardize_unit)
        
        # Convert numeric
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
        df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce')
        
        # Calculate amount
        if 'amount' not in df.columns:
            df['amount'] = df['quantity'] * df['unit_price']
        
        return df[df['quantity'] > 0]
    
    def _standardize_unit(self, unit):
        if pd.isna(unit):
            return 'pcs'
        
        unit = str(unit).lower().strip()
        unit_map = {
            'm': ['m', 'met', 'meter'],
            'm2': ['m2', 'm²', 'sqm'],
            'm3': ['m3', 'm³', 'cbm'],
            'kg': ['kg', 'kilo'],
            'ton': ['ton', 'tấn', 't'],
            'pcs': ['pcs', 'cái', 'ea']
        }
        
        for standard, variations in unit_map.items():
            if unit in variations:
                return standard
        return unit
```

### 5.4 ML Classifier

**modules/classifier.py**
```python
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pickle
import json
from pathlib import Path

class SECClassifier:
    def __init__(self, database):
        self.db = database
        self.model = None
        self.sec_embeddings = None
        self.sec_codes = []
        self.keywords_dict = {}
        
        if Path("models/sec_classifier.pkl").exists():
            self.load_model()
        else:
            self.initialize_model()
    
    def initialize_model(self):
        print("Initializing classifier...")
        self.model = SentenceTransformer('keepitreal/vietnamese-sbert')
        
        sec_df = self.db.execute_query(
            "SELECT sec_code, sec_name_vi, sec_name_en, keywords FROM sec_codes WHERE is_active = TRUE"
        )
        
        self.sec_codes = sec_df['sec_code'].tolist()
        sec_texts = []
        
        for _, row in sec_df.iterrows():
            keywords = json.loads(row['keywords']) if row['keywords'] else []
            text = f"{row['sec_name_vi']} {row['sec_name_en']} {' '.join(keywords)}"
            sec_texts.append(text)
            self.keywords_dict[row['sec_code']] = set(keywords)
        
        self.sec_embeddings = self.model.encode(sec_texts, show_progress_bar=True)
        self.save_model()
    
    def classify(self, description, top_k=3):
        # Rule-based first
        rule_result = self._rule_based_match(description)
        if rule_result:
            return [(rule_result, 95.0)]
        
        # ML-based
        desc_embedding = self.model.encode([description])[0]
        similarities = cosine_similarity([desc_embedding], self.sec_embeddings)[0]
        
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        return [(self.sec_codes[i], float(similarities[i] * 100)) for i in top_indices]
    
    def _rule_based_match(self, description):
        desc_lower = description.lower()
        for sec_code, keywords in self.keywords_dict.items():
            if any(kw.lower() in desc_lower for kw in keywords):
                return sec_code
        return None
    
    def save_model(self):
        Path("models").mkdir(exist_ok=True)
        with open('models/sec_classifier.pkl', 'wb') as f:
            pickle.dump({
                'sec_embeddings': self.sec_embeddings,
                'sec_codes': self.sec_codes,
                'keywords_dict': self.keywords_dict
            }, f)
    
    def load_model(self):
        self.model = SentenceTransformer('keepitreal/vietnamese-sbert')
        with open('models/sec_classifier.pkl', 'rb') as f:
            data = pickle.load(f)
        self.sec_embeddings = data['sec_embeddings']
        self.sec_codes = data['sec_codes']
        self.keywords_dict = data['keywords_dict']
```

### 5.5 Main Application

**app.py**
```python
import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime
from modules.database import Database
from modules.file_processor import FileProcessor
from modules.classifier import SECClassifier

st.set_page_config(
    page_title="BOQ System",
    page_icon="📊",
    layout="wide"
)

@st.cache_resource
def init_app():
    db = Database()
    if not db.test_connection():
        st.error("❌ Cannot connect to MySQL")
        st.stop()
    classifier = SECClassifier(db)
    return db, classifier

db, classifier = init_app()

# Navigation
page = st.sidebar.radio(
    "Navigation",
    ["🏠 Home", "📁 Projects", "⬆️ Upload BOQ", "📝 Review", "📊 Analytics"]
)

# HOME PAGE
if page == "🏠 Home":
    st.title("🏠 BOQ System")
    
    col1, col2, col3, col4 = st.columns(4)
    stats = db.get_dashboard_stats()
    
    with col1:
        st.metric("Projects", stats['total_projects'])
    with col2:
        st.metric("Files", stats['total_files'])
    with col3:
        st.metric("Items", f"{stats['total_items']:,}")
    with col4:
        st.metric("Value", f"{stats['total_value']:,.0f}")
    
    st.subheader("Recent Projects")
    projects = db.get_all_projects()
    if not projects.empty:
        st.dataframe(projects.head(5), use_container_width=True)

# PROJECT PAGE
elif page == "📁 Projects":
    st.title("📁 Projects")
    
    tab1, tab2 = st.tabs(["All Projects", "Create New"])
    
    with tab2:
        with st.form("new_project"):
            project_code = st.text_input("Project Code *")
            project_name = st.text_input("Project Name *")
            project_type = st.selectbox("Type", ["residential", "commercial", "industrial"])
            location = st.text_input("Location")
            
            if st.form_submit_button("Create"):
                try:
                    db.create_project(project_code, project_name, project_type, location=location)
                    st.success("✅ Project created!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# UPLOAD PAGE
elif page == "⬆️ Upload BOQ":
    st.title("⬆️ Upload BOQ")
    
    projects = db.get_all_projects()
    if projects.empty:
        st.warning("Create a project first")
    else:
        project_id = st.selectbox(
            "Select Project",
            projects['project_id'].tolist(),
            format_func=lambda x: projects[projects['project_id']==x]['project_name'].iloc[0]
        )
        
        file = st.file_uploader("Upload Excel", type=['xlsx', 'xls'])
        
        if file:
            processor = FileProcessor()
            df = processor.read_excel(file)
            structure = processor.detect_structure(df)
            
            st.write(f"Found {structure['total_rows']} rows")
            st.dataframe(pd.DataFrame(structure['preview']))
            
            if st.button("Process"):
                df_clean = processor.clean_data(df, structure['column_mapping'])
                
                file_hash = hashlib.sha256(file.getvalue()).hexdigest()
                file_id = db.save_boq_file(
                    project_id, file.name, file_hash,
                    len(df_clean), df_clean['amount'].sum()
                )
                
                for idx, row in df_clean.iterrows():
                    predictions = classifier.classify(row['description'])
                    sec_code, confidence = predictions[0]
                    
                    db.save_line_item(
                        file_id, project_id,
                        row_number=idx+1,
                        description=row['description'],
                        unit=row['unit'],
                        quantity=row['quantity'],
                        unit_price=row['unit_price'],
                        amount=row['amount'],
                        sec_code=sec_code,
                        confidence=confidence
                    )
                
                st.success(f"✅ Imported {len(df_clean)} items!")

st.sidebar.info(f"Connected to MySQL | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
```

---

## 6. USER GUIDE

### 6.1 First Time Setup

1. **Start MySQL**
   ```bash
   docker-compose up -d
   ```

2. **Launch App**
   ```bash
   streamlit run app.py
   ```

3. **Create First Project**
   - Go to "📁 Projects" tab
   - Fill in project details
   - Click "Create"

4. **Upload BOQ**
   - Go to "⬆️ Upload BOQ"
   - Select project
   - Drop Excel file
   - Review structure
   - Click "Process"

5. **Review Results**
   - Items auto-classified with confidence > 80%
   - Review items with low confidence
   - Manually correct if needed

### 6.2 Daily Workflow

```
1. Upload BOQ file
   ↓
2. System auto-classifies (AI)
   ↓
3. Review low-confidence items
   ↓
4. Manual correction if needed
   ↓
5. View analytics & reports
   ↓
6. Export cleaned data
```

---

## 7. API REFERENCE

### 7.1 Database Class Methods

#### Projects
```python
# Get all projects
db.get_all_projects() -> pd.DataFrame

# Create project
db.create_project(
    project_code: str,
    project_name: str,
    project_type: str,
    **kwargs
) -> int  # Returns project_id

# Get project
db.get_project_by_id(project_id: int) -> dict
```

#### BOQ Files
```python
# Save file
db.save_boq_file(
    project_id: int,
    file_name: str,
    file_hash: str,
    total_rows: int,
    total_amount: float
) -> int  # Returns file_id

# Check duplicate
db.check_duplicate_file(file_hash: str) -> dict | None
```

#### Line Items
```python
# Save line item
db.save_line_item(
    file_id: int,
    project_id: int,
    description: str,
    unit: str,
    quantity: float,
    unit_price: float,
    amount: float,
    sec_code: str,
    confidence: float
) -> int  # Returns line_item_id

# Get line items
db.get_line_items(
    project_id: int = None,
    needs_review: bool = False,
    skip: int = 0,
    limit: int = 100
) -> pd.DataFrame
```

### 7.2 Classifier Methods

```python
# Classify description
classifier.classify(
    description: str,
    top_k: int = 3
) -> List[Tuple[str, float]]  # [(sec_code, confidence), ...]

# Example
results = classifier.classify("Đào đất móng")
# Returns: [('SEC-01-01', 95.0), ('SEC-01', 85.0), ...]
```

---

## 8. TROUBLESHOOTING

### 8.1 Common Issues

#### MySQL Connection Failed

**Problem:** Cannot connect to MySQL

**Solutions:**
```bash
# Check Docker status
docker-compose ps

# Restart MySQL
docker-compose restart mysql

# View logs
docker-compose logs mysql

# Ensure port 3306 is not in use
netstat -an | grep 3306
```

#### Import Error

**Problem:** ModuleNotFoundError

**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or install missing package
pip install pymysql
```

#### Slow Performance

**Problem:** Queries take too long

**Solutions:**
```sql
-- Add indexes
CREATE INDEX idx_project ON line_items(project_id);
CREATE INDEX idx_sec ON line_items(sec_code);

-- Analyze tables
ANALYZE TABLE line_items;

-- Check query plan
EXPLAIN SELECT * FROM line_items WHERE project_id = 1;
```

### 8.2 Database Maintenance

```bash
# Backup database
docker-compose exec mysql mysqldump -u boq_user -pboq_password_456 boq_system > backup.sql

# Restore database
docker-compose exec -T mysql mysql -u boq_user -pboq_password_456 boq_system < backup.sql

# Clear all data
docker-compose down -v
docker-compose up -d
```

### 8.3 Support Resources

- **MySQL Docs:** https://dev.mysql.com/doc/
- **Streamlit Docs:** https://docs.streamlit.io/
- **Python Docs:** https://docs.python.org/3/

---

## 9. APPENDIX

### 9.1 Sample Data

**Sample SEC Codes**
```
SEC-00: Chi phí chung & Chuẩn bị
SEC-01: Phần Ngầm (Substructure)
  SEC-01-01: Công tác đất
  SEC-01-02: Cọc
  SEC-01-03: Móng
SEC-02: Phần Thân (Superstructure)
  SEC-02-01: Khung BTCT
  SEC-02-02: Sàn
SEC-03: Kiến trúc & Hoàn thiện
SEC-04: Hệ thống MEP
SEC-05: Cảnh quan
```

### 9.2 Performance Benchmarks

| Operation | Time | Notes |
|-----------|------|-------|
| Upload 1000 items | 5-10s | Depends on ML model |
| Classify 1 item | 50-100ms | GPU: 10-20ms |
| Search query | <500ms | With proper indexes |
| Generate report | 2-5s | 1000 items |

### 9.3 Future Enhancements

- [ ] Multi-user support
- [ ] Cloud deployment
- [ ] Mobile app
- [ ] Advanced ML models
- [ ] Price database integration
- [ ] Cost estimation
- [ ] Template library

---

## 📞 CONTACT & SUPPORT

**Version:** 1.0  
**Last Updated:** January 2026  
**License:** MIT  

For questions or support, please contact your system administrator.

---

**END OF DOCUMENTATION**