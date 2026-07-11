.PHONY: help setup dev-backend dev-frontend dev-docker test-backend test-frontend test lint-backend lint-frontend lint clean build-backend build-frontend migrate db-shell check

help: ## Show this help message
	@echo "Multimax AI Hub - Development Makefile"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -Eh '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Install all dependencies
	@echo "📦 Installing Python dependencies..."
	cd backend && pip install -r requirements.txt && pip install ruff mypy pytest pytest-asyncio httpx pytest-cov
	@echo ""
	@echo "📦 Installing Node.js dependencies..."
	cd frontend && npm install
	@echo ""
	@echo "✅ Setup complete!"

dev-backend: ## Start the backend development server
	@echo "🚀 Starting backend server at http://localhost:8000"
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start the frontend development server
	@echo "🚀 Starting frontend at http://localhost:5173"
	cd frontend && npm run dev

dev-docker: ## Start all services via Docker Compose
	@echo "🐳 Starting Docker services..."
	docker compose -f docker/docker-compose.yml up -d
	@echo "✅ Docker services started!"
	@echo "   Backend: http://localhost:8000"
	@echo "   Docs:    http://localhost:8000/docs"
	@echo "   PGAdmin: http://localhost:5050"
	@echo ""
	@echo "To view logs: docker compose -f docker/docker-compose.yml logs -f"

test-backend: ## Run backend tests
	cd backend && python -m pytest tests/ -v --asyncio-mode=auto $(ARGS)

test-frontend: ## Run frontend tests
	cd frontend && npx vitest run $(ARGS)

test: test-backend test-frontend ## Run all tests

test-backend-coverage: ## Run backend tests with coverage
	cd backend && python -m pytest tests/ -v --asyncio-mode=auto --cov=app --cov-report=term --cov-report=html

lint-backend: ## Lint and format backend code
	cd backend && ruff check app/ && ruff format --check app/

lint-frontend: ## Lint and format frontend code
	cd frontend && npx tsc --noEmit && npx eslint src/ --ext .ts,.tsx

lint: lint-backend lint-frontend ## Run all linters

format-backend: ## Format backend code
	cd backend && ruff format app/ && ruff check --fix app/

format-frontend: ## Format frontend code
	cd frontend && npx prettier --write src/

format: format-backend format-frontend ## Format all code

build-backend: ## Build backend Docker image
	docker compose -f docker/docker-compose.yml build backend

build-frontend: ## Build frontend for production
	cd frontend && npm run build

build: build-backend build-frontend ## Build everything

migrate: ## Run database migrations
	cd backend && alembic upgrade head

migrate-new: ## Create a new migration (usage: make migrate-new msg="description")
	cd backend && alembic revision --autogenerate -m "$(msg)"

db-shell: ## Open database shell
	@echo "Opening database shell..."
	cd backend && python -c "from app.core.database import get_session; print('Database session available')"

clean: ## Clean build artifacts and caches
	@echo "🧹 Cleaning..."
	-rm -rf frontend/dist
	-rm -rf backend/.coverage
	-rm -rf backend/htmlcov
	-rm -rf backend/.pytest_cache
	-rm -rf backend/app/__pycache__
	-rm -rf backend/app/**/__pycache__
	-rm -rf .pytest_cache
	-rm -rf .mypy_cache
	-rm -rf .ruff_cache
	@echo "✅ Cleaned!"

check: lint test build ## Run all checks (lint + test + build)

docker-logs: ## View Docker logs
	docker compose -f docker/docker-compose.yml logs -f

docker-down: ## Stop Docker services
	docker compose -f docker/docker-compose.yml down

docker-restart: docker-down dev-docker ## Restart Docker services

pre-commit-install: ## Install pre-commit hooks
	pip install pre-commit
	pre-commit install

pre-commit-run: ## Run pre-commit on all files
	pre-commit run --all-files

.PHONY: help setup dev-backend dev-frontend dev-docker test-backend test-frontend test lint-backend lint-frontend lint format-backend format-frontend format build-backend build-frontend build migrate migrate-new db-shell clean check docker-logs docker-down docker-restart pre-commit-install pre-commit-run