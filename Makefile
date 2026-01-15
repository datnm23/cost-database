.PHONY: help install dev build up down logs clean test migrate seed

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install all dependencies (backend + frontend)
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✅ Dependencies installed"

dev: ## Run development servers locally
	@echo "Starting development environment..."
	docker compose up mysql redis -d
	@echo "Waiting for services to be ready..."
	sleep 10
	@echo "Start backend with: cd backend && uvicorn app.main:app --reload"
	@echo "Start frontend with: cd frontend && npm run dev"

build: ## Build Docker images
	@echo "Building Docker images..."
	docker compose build
	@echo "✅ Build complete"

up: ## Start all services with Docker Compose
	@echo "Starting all services..."
	docker compose up -d
	@echo "✅ Services started"
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "API Docs: http://localhost:8000/docs"

down: ## Stop all services
	@echo "Stopping all services..."
	docker compose down
	@echo "✅ Services stopped"

logs: ## View logs from all services
	docker compose logs -f

logs-backend: ## View backend logs only
	docker compose logs -f backend

logs-frontend: ## View frontend logs only
	docker compose logs -f frontend

clean: ## Clean up containers, volumes, and generated files
	@echo "Cleaning up..."
	docker compose down -v
	rm -rf backend/__pycache__ backend/**/__pycache__
	rm -rf backend/.pytest_cache
	rm -rf frontend/node_modules frontend/dist
	@echo "✅ Cleanup complete"

test: ## Run tests
	@echo "Running backend tests..."
	cd backend && pytest
	@echo "Running frontend tests..."
	cd frontend && npm test
	@echo "✅ Tests complete"

test-backend: ## Run backend tests only
	cd backend && pytest -v

test-frontend: ## Run frontend tests only
	cd frontend && npm test

migrate: ## Run database migrations
	@echo "Running migrations..."
	docker compose exec backend alembic upgrade head
	@echo "✅ Migrations complete"

seed: ## Seed database with sample data
	@echo "Seeding database..."
	docker compose exec mysql mysql -u boq_user -pboq_password_456 boq_system < backend/database/seed.sql
	@echo "✅ Database seeded"

db-shell: ## Open MySQL shell
	docker compose exec mysql mysql -u boq_user -pboq_password_456 boq_system

backend-shell: ## Open backend container shell
	docker compose exec backend /bin/bash

frontend-shell: ## Open frontend container shell
	docker compose exec frontend /bin/sh

format: ## Format code
	@echo "Formatting backend code..."
	cd backend && black . && isort .
	@echo "Formatting frontend code..."
	cd frontend && npm run format
	@echo "✅ Code formatted"

lint: ## Lint code
	@echo "Linting backend..."
	cd backend && flake8 . && mypy .
	@echo "Linting frontend..."
	cd frontend && npm run lint
	@echo "✅ Linting complete"

backup: ## Backup database
	@echo "Backing up database..."
	docker compose exec mysql mysqldump -u boq_user -pboq_password_456 boq_system > backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup complete"

restore: ## Restore database from backup (usage: make restore FILE=backup.sql)
	@echo "Restoring database from $(FILE)..."
	docker compose exec -T mysql mysql -u boq_user -pboq_password_456 boq_system < $(FILE)
	@echo "✅ Database restored"
