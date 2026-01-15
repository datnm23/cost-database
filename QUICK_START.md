# 🚀 Quick Start Guide

This guide will help you get the BOQ System up and running quickly.

## Prerequisites

- **Docker** and **Docker Compose** installed
- OR manually:
  - Python 3.11+
  - Node.js 18+
  - MySQL 8.0+
  - Redis 7.0+

## Option 1: Docker (Recommended)

### 1. Clone and Setup
```bash
cd /home/datnm/projects/cost-database

# Copy environment file
cp .env.example .env

# Edit .env with your configuration (optional for local dev)
nano .env
```

### 2. Start All Services
```bash
# Build and start all containers
make up

# OR using docker compose directly (V2)
docker compose up -d --build

# Legacy docker-compose (V1) - if you have it installed
# docker-compose up -d --build
```

This will start:
- **Backend API** on http://localhost:8000
- **Frontend** on http://localhost:3000
- **MySQL** on internal network only (no host port exposure to avoid conflicts)
- **Redis** on internal network only (no host port exposure to avoid conflicts)

> **Note:** MySQL and Redis are only accessible from within the Docker network.
> If you need direct access from your host, uncomment the port mappings in `docker-compose.yml`.

### 3. Initialize Database
```bash
# Run database migrations
make db-init

# OR manually
docker compose exec backend python -m app.core.database
```

### 4. Access the Application
- **Frontend UI**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **API Alternative**: http://localhost:8000/redoc

### 5. Default Credentials
```
Username: admin
Password: admin123
```

## Option 2: Manual Setup (Development)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp ../.env.example .env
nano .env  # Configure your settings

# Run database setup
python -c "from app.core.database import init_db; init_db()"

# Run migrations (if using Alembic)
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at http://localhost:8000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
echo "VITE_API_BASE_URL=http://localhost:8000" > .env

# Start development server
npm run dev
```

Frontend will be available at http://localhost:3000

### Database Setup (MySQL)

```bash
# Connect to MySQL
mysql -u root -p

# Create database
CREATE DATABASE boq_system;

# Create user
CREATE USER 'boq_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON boq_system.* TO 'boq_user'@'localhost';
FLUSH PRIVILEGES;

# Import schema
mysql -u boq_user -p boq_system < backend/database/schema.sql

# Import seed data
mysql -u boq_user -p boq_system < backend/database/seed.sql
```

### Redis Setup

```bash
# Install Redis (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install redis-server

# Start Redis
sudo systemctl start redis
sudo systemctl enable redis

# Verify Redis is running
redis-cli ping  # Should return "PONG"
```

## Common Commands (Docker)

```bash
# View logs
make logs
# OR: docker compose logs -f

# Stop all services
make down
# OR: docker compose down

# Restart services
make restart
# OR: docker compose restart

# View running containers
docker compose ps

# Access backend shell
docker compose exec backend bash

# Access frontend shell
docker compose exec frontend sh

# Access MySQL
docker compose exec mysql mysql -u boq_user -p
# OR from backend container:
# docker compose exec backend mysql -h mysql -u boq_user -p

# Access Redis CLI
docker compose exec redis redis-cli

# View backend logs
docker compose logs -f backend

# View frontend logs
docker compose logs -f frontend
```

## Testing the Application

### 1. Login
- Navigate to http://localhost:3000
- Login with default credentials (admin/admin123)

### 2. Create a Project
- Go to "Projects" page
- Click "Create Project"
- Fill in project details
- Save

### 3. Upload BOQ File
- Go to "Upload BOQ" page
- Select the project you created
- Upload an Excel file with BOQ data
- Map columns (auto-detection will help)
- Process the file

### 4. Review Line Items
- Go to "Line Items" page
- Review imported data
- Use auto-classification feature
- Verify items
- Bulk edit if needed

### 5. View Analytics
- Go to "Analytics" page
- Select your project
- View charts and distributions
- Check classification accuracy

## Troubleshooting

### Port Already in Use Error
```bash
# Error: "address already in use" for ports 3306, 6379, 8000, or 3000

# Solution 1: Use the minimal port configuration (recommended)
# MySQL and Redis ports are already commented out in docker-compose.yml
# This avoids conflicts with local MySQL/Redis installations

# Solution 2: Stop local services
sudo systemctl stop redis redis-server mysql mysqld 2>/dev/null

# Solution 3: Check what's using the port
sudo lsof -i :6379  # or :3306, :8000, :3000
# Then kill the process or change the port in docker-compose.yml

# For detailed solutions, see PORT_CONFLICT_SOLUTION.md
```

### Backend won't start
```bash
# Check logs
docker compose logs backend

# Common issues:
# 1. Database not ready - wait 30 seconds and try again
# 2. Port 8000 already in use - change in docker-compose.yml
# 3. Environment variables - check .env file
```

### Frontend won't start
```bash
# Check logs
docker compose logs frontend

# Common issues:
# 1. Node modules not installed - run: docker compose exec frontend npm install
# 2. Port 3000 already in use - change in docker-compose.yml
# 3. API connection issues - check VITE_API_BASE_URL in frontend/.env
```

### Database connection issues
```bash
# Test database connection from backend container
docker compose exec backend python -c "from app.core.database import engine; print(engine.connect())"

# Check MySQL is running
docker compose ps mysql

# Access MySQL from backend container
docker compose exec backend mysql -h mysql -u boq_user -p

# OR access MySQL directly
docker compose exec mysql mysql -u boq_user -p

# Reset database
docker compose down -v  # Warning: This deletes all data!
docker compose up -d
```

### Redis connection issues
```bash
# Test Redis connection from backend container
docker compose exec backend python -c "from app.core.redis import redis_client; print(redis_client.ping())"

# Check Redis is running
docker compose ps redis

# Access Redis CLI
docker compose exec redis redis-cli

# Restart Redis
docker compose restart redis
```

## Environment Variables

Key environment variables in `.env`:

### Database
```bash
DATABASE_URL=mysql+pymysql://boq_user:password@mysql:3306/boq_system
```

### Redis
```bash
REDIS_URL=redis://redis:6379/0
```

### Security
```bash
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Application
```bash
ENVIRONMENT=development
DEBUG=True
ALLOWED_ORIGINS=http://localhost:3000
```

### Frontend
```bash
VITE_API_BASE_URL=http://localhost:8000
```

## Next Steps

1. **Explore the Application**
   - Create projects
   - Upload BOQ files
   - Review and classify line items
   - View analytics

2. **Customize Configuration**
   - Update `.env` with your settings
   - Configure email notifications (future feature)
   - Set up authentication providers

3. **Development**
   - Read `FRONTEND_IMPLEMENTATION.md` for frontend details
   - Check `docs/TECHNICAL_DESIGN.md` for architecture
   - Review API docs at http://localhost:8000/docs

4. **Production Deployment**
   - See `docs/DEPLOYMENT_GUIDE.md`
   - Set up proper SSL/TLS
   - Configure production database
   - Set up backup strategy

## Support

For issues or questions:
1. Check the logs: `make logs` or `docker compose logs`
2. Review documentation in `/docs`
3. Check API documentation at http://localhost:8000/docs
4. Review `FRONTEND_IMPLEMENTATION.md` for frontend issues

## Useful Resources

- **API Documentation**: http://localhost:8000/docs
- **Technical Design**: `docs/TECHNICAL_DESIGN.md`
- **Frontend Guide**: `FRONTEND_IMPLEMENTATION.md`
- **Deployment Guide**: `docs/DEPLOYMENT_GUIDE.md`
- **Project Overview**: `docs/PROJECT_OVERVIEW.md`

---

**Happy BOQ Managing! 🎉**
