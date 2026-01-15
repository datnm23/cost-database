# Port Conflict Resolution Guide

## Issue
Docker containers fail to start because ports are already in use on the host system.

## Common Port Conflicts

### Redis (Port 6379)
**Error:** `failed to bind host port 0.0.0.0:6379/tcp: address already in use`

**Solutions:**

#### Option 1: Stop Local Redis Service (Recommended if you don't need it)
```bash
# Check if Redis is running as a service
sudo systemctl status redis
# OR
sudo systemctl status redis-server

# Stop Redis service
sudo systemctl stop redis
# OR
sudo systemctl stop redis-server

# Disable Redis from auto-starting
sudo systemctl disable redis
# OR
sudo systemctl disable redis-server
```

#### Option 2: Use Different Port for Docker Redis
Edit `docker-compose.yml` and change Redis port mapping:
```yaml
redis:
  ports:
    - "6380:6379"  # Map host port 6380 to container port 6379
```

Then update `.env`:
```bash
REDIS_URL=redis://localhost:6380/0
```

#### Option 3: Don't Expose Redis Port (Best for Development)
If you only need Redis for backend container, remove the port mapping:
```yaml
redis:
  # Remove or comment out the ports section
  # ports:
  #   - "6379:6379"
```
The backend container can still access Redis via the internal network.

### MySQL (Port 3306)

**Solutions:**

#### Option 1: Stop Local MySQL
```bash
sudo systemctl stop mysql
sudo systemctl disable mysql
```

#### Option 2: Use Different Port
```yaml
mysql:
  ports:
    - "3307:3306"  # Use port 3307 on host
```

Update `.env`:
```bash
DATABASE_URL=mysql+pymysql://boq_user:password@localhost:3307/boq_system
```

#### Option 3: Don't Expose MySQL Port
```yaml
mysql:
  # Remove ports if you don't need direct host access
  # ports:
  #   - "3306:3306"
```

### Backend (Port 8000)

**Check what's using it:**
```bash
sudo lsof -i :8000
# OR
sudo netstat -tlnp | grep 8000
```

**Solutions:**
- Kill the process using port 8000
- Or change port in `docker-compose.yml`:
```yaml
backend:
  ports:
    - "8001:8000"  # Use port 8001 on host
```

### Frontend (Port 3000)

**Solutions:**
- Kill any Node.js process using port 3000
- Or change port in `docker-compose.yml`:
```yaml
frontend:
  ports:
    - "3001:3000"  # Use port 3001 on host
```

## Quick Fix Script

Create a file `scripts/stop-conflicting-services.sh`:

```bash
#!/bin/bash

echo "Stopping services that might conflict with Docker containers..."

# Stop Redis
sudo systemctl stop redis 2>/dev/null || sudo systemctl stop redis-server 2>/dev/null
echo "✓ Redis stopped (if it was running)"

# Stop MySQL
sudo systemctl stop mysql 2>/dev/null || sudo systemctl stop mysqld 2>/dev/null
echo "✓ MySQL stopped (if it was running)"

# Check for processes on ports
echo ""
echo "Checking for remaining port conflicts..."
for port in 3000 3306 6379 8000; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "⚠ Port $port is still in use"
        lsof -i :$port
    else
        echo "✓ Port $port is available"
    fi
done
```

Make it executable:
```bash
chmod +x scripts/stop-conflicting-services.sh
./scripts/stop-conflicting-services.sh
```

## Recommended Approach

For development, the cleanest approach is:

1. **Remove external port mappings** for services you don't need to access directly from the host
2. **Keep only essential ports** exposed (frontend on 3000, backend on 8000)
3. **Use internal Docker networking** for service-to-service communication

### Minimal Port Exposure Configuration

Edit `docker-compose.yml`:

```yaml
services:
  mysql:
    # ... existing config ...
    # Don't expose port - only accessible from backend container
    # ports:
    #   - "3306:3306"
    
  redis:
    # ... existing config ...
    # Don't expose port - only accessible from backend container
    # ports:
    #   - "6379:6379"
    
  backend:
    # ... existing config ...
    ports:
      - "8000:8000"  # Keep this - you need API access
    
  frontend:
    # ... existing config ...
    ports:
      - "3000:3000"  # Keep this - you need UI access
```

This way:
- Frontend runs on http://localhost:3000
- Backend API on http://localhost:8000
- MySQL and Redis are only accessible internally (no conflicts!)

## After Making Changes

```bash
# Stop all containers
docker compose down

# Remove all containers and volumes (fresh start)
docker compose down -v

# Rebuild and start
docker compose up -d --build

# Check status
docker compose ps

# View logs
docker compose logs -f
```

## Verify Everything Works

```bash
# Check all containers are running
docker compose ps

# Test backend
curl http://localhost:8000/api/v1/health

# Test frontend
curl http://localhost:3000

# Test internal connectivity (from backend to MySQL)
docker compose exec backend python -c "from app.core.database import engine; print(engine.connect())"

# Test internal connectivity (from backend to Redis)
docker compose exec backend python -c "from app.core.redis import redis_client; print(redis_client.ping())"
```

## Common Commands Reference

```bash
# See what's using a specific port
sudo lsof -i :PORT_NUMBER
sudo netstat -tlnp | grep PORT_NUMBER
sudo ss -tlnp | grep PORT_NUMBER

# Kill process by PID
sudo kill -9 PID

# Check Docker logs
docker compose logs SERVICE_NAME
docker compose logs -f  # Follow mode

# Restart a specific service
docker compose restart SERVICE_NAME

# Rebuild a specific service
docker compose up -d --build SERVICE_NAME
```
