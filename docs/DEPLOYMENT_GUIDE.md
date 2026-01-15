# BOQ SYSTEM - DEPLOYMENT GUIDE

**Version:** 2.0  
**Created:** January 12, 2026  
**Last Updated:** January 12, 2026  
**Tech Stack:** Python FastAPI + React + TypeScript + MySQL

---

## 📋 Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Environment Setup](#2-environment-setup)
3. [Development Setup](#3-development-setup)
4. [Docker Deployment](#4-docker-deployment)
5. [Backend Configuration](#5-backend-configuration)
6. [Frontend Configuration](#6-frontend-configuration)
7. [Database Setup](#7-database-setup)
8. [Verification](#8-verification)
9. [Production Deployment](#9-production-deployment)
10. [Maintenance](#10-maintenance)

---

## 1. PREREQUISITES

### 1.1 Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 4 GB | 8 GB |
| Storage | 20 GB | 50 GB SSD |
| Network | 10 Mbps | 100 Mbps |

### 1.2 Software Requirements

| Software | Version | Download Link |
|----------|---------|---------------|
| Python | 3.11+ | https://python.org |
| Node.js | 20+ | https://nodejs.org |
| Docker Desktop | Latest | https://docker.com |
| Git | Latest | https://git-scm.com |
| VS Code (optional) | Latest | https://code.visualstudio.com |

### 1.3 Verify Prerequisites

```bash
# Check Python version
python --version
# Expected: Python 3.11.x or higher

# Check Node.js version
node --version
# Expected: v20.x or higher

# Check npm version
npm --version

# Check Docker
docker --version
docker compose version

# Check Git
git --version
```

---

## 2. ENVIRONMENT SETUP

### 2.1 Clone Repository

```bash
# Clone the repository
git clone <repository-url> cost-database
cd cost-database
```

### 2.2 Project Structure

```
cost-database/
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── Makefile
│
├── backend/                # FastAPI Backend
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── alembic/           # Database migrations
│   └── app/               # Application code
│
├── frontend/              # React Frontend
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   └── src/               # React source code
│
└── docs/                  # Documentation
```

### 2.3 Create Environment Files

```bash
# Copy example environment files
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit configurations as needed
nano .env
```

---

## 3. DEVELOPMENT SETUP

### 3.1 Backend Setup (FastAPI)

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at:
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3.2 Frontend Setup (React)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: http://localhost:5173

### 3.3 Database Setup (MySQL via Docker)

```bash
# Start MySQL container only
docker compose up -d mysql

# Wait for MySQL to be ready
docker compose logs -f mysql

# Access MySQL CLI (optional)
docker exec -it boq_mysql mysql -u boq_user -p
```

---

## 4. DOCKER DEPLOYMENT

### 4.1 Docker Compose Configuration

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  # MySQL Database
  mysql:
    image: mysql:8.0
    container_name: boq_mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD:-rootpassword}
      MYSQL_DATABASE: ${DB_NAME:-boq_system}
      MYSQL_USER: ${DB_USER:-boq_user}
      MYSQL_PASSWORD: ${DB_PASSWORD:-boq_password}
    ports:
      - "${DB_PORT:-3306}:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./database/init:/docker-entrypoint-initdb.d
    command: >
      --character-set-server=utf8mb4
      --collation-server=utf8mb4_unicode_ci
      --max_allowed_packet=256M
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      timeout: 5s
      retries: 10
    networks:
      - boq_network

  # FastAPI Backend
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: boq_backend
    restart: unless-stopped
    environment:
      - DB_HOST=mysql
      - DB_PORT=3306
      - DB_USER=${DB_USER:-boq_user}
      - DB_PASSWORD=${DB_PASSWORD:-boq_password}
      - DB_NAME=${DB_NAME:-boq_system}
      - SECRET_KEY=${SECRET_KEY:-dev-secret-key}
      - DEBUG=${DEBUG:-true}
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - ./uploads:/app/uploads
      - ./models:/app/models
    depends_on:
      mysql:
        condition: service_healthy
    networks:
      - boq_network

  # React Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: development
    container_name: boq_frontend
    restart: unless-stopped
    environment:
      - VITE_API_URL=http://localhost:8000/api/v1
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend
    networks:
      - boq_network

  # phpMyAdmin (optional, for development)
  phpmyadmin:
    image: phpmyadmin:latest
    container_name: boq_phpmyadmin
    restart: unless-stopped
    environment:
      PMA_HOST: mysql
      PMA_USER: ${DB_USER:-boq_user}
      PMA_PASSWORD: ${DB_PASSWORD:-boq_password}
    ports:
      - "8080:80"
    depends_on:
      mysql:
        condition: service_healthy
    networks:
      - boq_network
    profiles:
      - dev

volumes:
  mysql_data:
    name: boq_mysql_data

networks:
  boq_network:
    name: boq_network
```

### 4.2 Backend Dockerfile

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download ML model on build
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('keepitreal/vietnamese-sbert')"

# Copy application code
COPY . .

# Create directories
RUN mkdir -p uploads logs models

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4.3 Frontend Dockerfile

Create `frontend/Dockerfile`:

```dockerfile
# Development stage
FROM node:20-alpine AS development

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# Build stage
FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Production stage
FROM nginx:alpine AS production

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 4.4 Start All Services

```bash
# Start all services
docker compose up -d

# Start with dev profile (includes phpMyAdmin)
docker compose --profile dev up -d

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f backend
docker compose logs -f frontend

# Stop all services
docker compose down

# Stop and remove volumes
docker compose down -v
```

---

## 5. BACKEND CONFIGURATION

### 5.1 Environment Variables

Create `backend/.env`:

```bash
# Application
DEBUG=true
SECRET_KEY=your-secret-key-change-in-production
APP_ENV=development

# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=boq_user
DB_PASSWORD=boq_password
DB_NAME=boq_system

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# JWT (if using authentication)
JWT_SECRET_KEY=jwt-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# ML
ML_MODEL_PATH=models/
ML_CONFIDENCE_THRESHOLD=80
ML_EMBEDDING_MODEL=keepitreal/vietnamese-sbert

# Upload
UPLOAD_MAX_SIZE=52428800
UPLOAD_DIR=uploads/
ALLOWED_EXTENSIONS=.xlsx,.xls

# Logging
LOG_LEVEL=INFO
LOG_PATH=logs/
```

### 5.2 Database Migrations

```bash
cd backend

# Create new migration
alembic revision --autogenerate -m "Add new table"

# Run migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1

# View migration history
alembic history
```

### 5.3 Download ML Model

```bash
# Download Vietnamese SBERT model (first run)
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('keepitreal/vietnamese-sbert')
print('Model downloaded successfully!')
"
```

---

## 6. FRONTEND CONFIGURATION

### 6.1 Environment Variables

Create `frontend/.env`:

```bash
# API URL
VITE_API_URL=http://localhost:8000/api/v1

# App Config
VITE_APP_NAME=BOQ System
VITE_APP_VERSION=2.0.0
```

### 6.2 Production Build

```bash
cd frontend

# Build for production
npm run build

# Preview production build
npm run preview
```

### 6.3 Nginx Configuration

Create `frontend/nginx.conf`:

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    # SPA routing - redirect all to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy (optional, if backend on same domain)
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Static assets caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## 8. VERIFICATION

### 8.1 Health Checks

```bash
# Check backend API
curl -s http://localhost:8000/health
# Expected: {"status":"healthy"}

# Check API documentation
curl -s http://localhost:8000/docs
# Should return Swagger UI HTML

# Check frontend
curl -s http://localhost:5173
# Should return React app HTML

# Check database connection via API
curl -s http://localhost:8000/api/v1/projects
# Should return JSON response
```

### 8.2 Run Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html

# Frontend tests
cd frontend
npm run test

# E2E tests (if using Playwright/Cypress)
npm run test:e2e
```

### 8.3 Verification Checklist

- [ ] MySQL container running (`docker compose ps`)
- [ ] Database tables created (`SHOW TABLES;`)
- [ ] SEC codes loaded (50+ records)
- [ ] Backend API accessible at http://localhost:8000
- [ ] API docs accessible at http://localhost:8000/docs
- [ ] Frontend accessible at http://localhost:5173
- [ ] Can create a project via UI
- [ ] Can upload Excel file
- [ ] Classification working
- [ ] Export working

---

## 9. PRODUCTION DEPLOYMENT

### 9.1 Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    container_name: boq_mysql
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
      MYSQL_DATABASE: ${DB_NAME}
      MYSQL_USER: ${DB_USER}
      MYSQL_PASSWORD: ${DB_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
    command: >
      --character-set-server=utf8mb4
      --collation-server=utf8mb4_unicode_ci
      --max_allowed_packet=256M
      --innodb_buffer_pool_size=1G
      --innodb_log_file_size=256M
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      timeout: 5s
      retries: 10
    networks:
      - boq_network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: boq_backend
    restart: always
    environment:
      - DB_HOST=mysql
      - DB_PORT=3306
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_NAME=${DB_NAME}
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=false
    volumes:
      - uploads_data:/app/uploads
      - models_data:/app/models
    depends_on:
      mysql:
        condition: service_healthy
    networks:
      - boq_network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: production
      args:
        - VITE_API_URL=${VITE_API_URL}
    container_name: boq_frontend
    restart: always
    networks:
      - boq_network

  nginx:
    image: nginx:alpine
    container_name: boq_nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
    networks:
      - boq_network

volumes:
  mysql_data:
  uploads_data:
  models_data:

networks:
  boq_network:
```

### 9.2 Production Nginx Configuration

Create `nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Gzip
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:80;
    }

    server {
        listen 80;
        server_name your-domain.com;

        # Redirect to HTTPS (uncomment for production)
        # return 301 https://$host$request_uri;

        # API requests
        location /api {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # File upload settings
            client_max_body_size 50M;
        }

        # OpenAPI docs
        location /docs {
            proxy_pass http://backend;
            proxy_set_header Host $host;
        }

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }

    # HTTPS server (uncomment for production)
    # server {
    #     listen 443 ssl;
    #     server_name your-domain.com;
    #
    #     ssl_certificate /etc/nginx/ssl/cert.pem;
    #     ssl_certificate_key /etc/nginx/ssl/key.pem;
    #
    #     # ... same location blocks as above
    # }
}
```

### 9.3 Security Checklist

- [ ] Change all default passwords
- [ ] Use strong `SECRET_KEY`
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Configure firewall (UFW/iptables)
- [ ] Restrict database access
- [ ] Regular security updates
- [ ] Set up fail2ban
- [ ] Enable rate limiting

### 9.4 Backup Configuration

Create `scripts/backup.sh`:

```bash
#!/bin/bash
set -e

BACKUP_DIR=/path/to/backups
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE=${BACKUP_DIR}/boq_backup_${DATE}.sql

# Create backup directory
mkdir -p ${BACKUP_DIR}

# Database backup
docker exec boq_mysql mysqldump -u ${DB_USER} -p${DB_PASSWORD} ${DB_NAME} > ${BACKUP_FILE}

# Compress
gzip ${BACKUP_FILE}

# Backup uploads
tar -czf ${BACKUP_DIR}/uploads_${DATE}.tar.gz ./uploads/

# Keep only last 7 days
find ${BACKUP_DIR} -name "*.gz" -mtime +7 -delete

echo "✅ Backup completed: ${BACKUP_FILE}.gz"
```

---

## 10. MAINTENANCE

### 10.1 Common Commands

```bash
# View all container status
docker compose ps

# View logs
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f mysql

# Restart services
docker compose restart backend
docker compose restart frontend

# Rebuild and restart
docker compose up -d --build backend

# Shell access
docker exec -it boq_backend /bin/bash
docker exec -it boq_mysql mysql -u boq_user -p
```

### 10.2 Daily Tasks

```bash
# Check services
docker compose ps

# Check disk space
df -h

# Check container logs for errors
docker compose logs --tail=100 backend | grep -i error
```

### 10.3 Weekly Tasks

```bash
# Database optimization
docker exec boq_mysql mysql -u root -p -e "
ANALYZE TABLE boq_system.line_items;
ANALYZE TABLE boq_system.projects;
"

# Clear old logs
docker system prune -f

# Check for updates
git fetch origin
```

### 10.4 Rollback Procedures

```bash
# Stop current version
docker compose down

# Checkout previous version
git checkout v1.0.0

# Restore database from backup
docker compose up -d mysql
docker exec -i boq_mysql mysql -u boq_user -p boq_system < /path/to/backup.sql

# Rebuild and start
docker compose up -d --build
```

---

## 📞 Support

### Error Reporting

When reporting issues, include:
1. Error message from logs
2. Steps to reproduce
3. System information (OS, Docker version)
4. Screenshots (if UI issue)

### Log Locations

| Log | Access | Description |
|-----|--------|-------------|
| Backend | `docker compose logs backend` | FastAPI logs |
| Frontend | `docker compose logs frontend` | React build/serve logs |
| MySQL | `docker compose logs mysql` | Database logs |
| Nginx | `docker compose logs nginx` | Proxy logs |

---

## 📝 Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-12 | AI Assistant | Initial version (Streamlit) |
| 2.0 | 2026-01-12 | AI Assistant | Updated to FastAPI + React stack |
