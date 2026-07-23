# PHASE 0 — Foundation Implementation Plan

## Architecture
```
Core Platform          Modules           Shared Services
├── Authentication      ├── Chat         ├── Storage Service
├── AI Router           ├── Coding      ├── Vector Service
├── Plugin Manager      ├── Research    ├── Search Service
├── Agent Engine        ├── Documents   ├── Document Parser
├── Memory Engine       ├── Voice       ├── Cache Service
├── Workflow Engine     ├── Images
├── Search Engine       ├── Video
├── Model Manager       ├── Automation
├── Settings            ├── Knowledge Base
├── API Gateway         ├── Marketplace
├── Event Bus           └── Teams
└── (Phase 0 builds Core Platform shell + infrastructure)
```

## Phase 0 Checklist

### Step 1: Project Structure & Monorepo Setup
- [x] Create project directory structure
- [ ] Set up Python virtual environment
- [ ] Install FastAPI, SQLAlchemy, Alembic, Pydantic, Uvicorn
- [ ] Set up Next.js/React frontend scaffold
- [ ] Create Docker Compose configuration
- [ ] Create .env files

### Step 2: Database Foundation
- [ ] PostgreSQL schema setup with SQLAlchemy models
- [ ] Alembic migrations configuration
- [ ] Core models: User, Session, ApiKey, Settings
- [ ] Database connection pool configuration
- [ ] Repository pattern implementation

### Step 3: Authentication System
- [ ] User registration endpoint
- [ ] User login with JWT tokens
- [ ] Token refresh mechanism
- [ ] API key authentication
- [ ] RBAC permission system
- [ ] Better Auth integration (frontend)
- [ ] Auth middleware on all protected routes

### Step 4: Core Kernel — Event Bus
- [ ] In-process event bus (asyncio-based)
- [ ] Event registry with typed events
- [ ] Publisher/Subscriber pattern
- [ ] Event logging for audit
- [ ] Dead letter queue for failed handlers

### Step 5: Core Kernel — Settings & Configuration
- [ ] System settings model (key-value)
- [ ] User settings model
- [ ] Settings CRUD API
- [ ] Environment variable validation
- [ ] Configuration loading on startup

### Step 6: Core Kernel — API Gateway
- [ ] Request validation middleware
- [ ] Rate limiting middleware
- [ ] CORS middleware
- [ ] Request ID tracing
- [ ] Error handler with consistent response format
- [ ] Health check endpoint
- [ ] API version prefix (/api/v1/)

### Step 7: Core Kernel — Logging & Error Handling
- [ ] Structured JSON logging (loguru)
- [ ] Error tracking middleware
- [ ] Auditing system
- [ ] Graceful shutdown handling

### Step 8: AI Router — Provider Abstraction
- [ ] AIProvider abstract base class
- [ ] Ollama provider implementation
- [ ] Model capability registry
- [ ] Default routing strategy (task → model)
- [ ] Chat completion endpoint
- [ ] Streaming chat endpoint (SSE)
- [ ] Model listing endpoint

### Step 9: Storage Service
- [ ] StorageBackend interface
- [ ] Local storage implementation
- [ ] File upload endpoint
- [ ] File download/retrieval endpoint
- [ ] File type validation
- [ ] File size limits

### Step 10: Frontend — Layout & Navigation
- [ ] App shell with sidebar
- [ ] Core Platform navigation (11 items)
- [ ] Module navigation (11 items)
- [ ] Theme system (light/dark)
- [ ] Responsive layout
- [ ] Keyboard shortcuts
- [ ] User menu (profile, settings, logout)

### Step 11: Frontend — Authentication UI
- [ ] Login page
- [ ] Register page
- [ ] Password reset flow
- [ ] Auth state management (Zustand)
- [ ] Protected route wrapper
- [ ] Token management (interceptor)

### Step 12: Frontend — Dashboard
- [ ] Dashboard page with summary cards
- [ ] Recent conversations widget
- [ ] Quick action buttons
- [ ] System status indicators
- [ ] Welcome guide for new users

### Step 13: Frontend — Settings Page
- [ ] Profile settings (name, email, avatar)
- [ ] Appearance settings (theme, font size)
- [ ] API key management
- [ ] AI model preferences
- [ ] Notification preferences

### Step 14: Docker & Deployment
- [ ] Dockerfile for backend (multi-stage)
- [ ] Dockerfile for frontend (nginx serve)
- [ ] Docker Compose with all services
- [ ] Health check endpoints
- [ ] Docker volume configuration
- [ ] Production checklist documentation

### Step 15: Testing Infrastructure
- [ ] pytest configuration
- [ ] Test database setup (SQLite in-memory)
- [ ] Auth endpoint tests
- [ ] Chat endpoint tests
- [ ] Settings endpoint tests
- [ ] Frontend component tests (vitest)

---

## Build Order

I will build in this exact order, one step at a time, getting confirmation before proceeding:

```
1.  Project Structure & Monorepo Setup
2.  Database Foundation (models + migrations)
3.  Authentication System
4.  Event Bus
5.  Settings & Config
6.  API Gateway (middleware + error handling)
7.  Logging & Error Handling
8.  AI Router (provider abstraction + Ollama)
9.  Storage Service
10. Frontend — Layout & Navigation
11. Frontend — Authentication UI
12. Frontend — Dashboard
13. Frontend — Settings Page
14. Docker & Deployment
15. Testing Infrastructure
```

## 2026-07-23 Audit Update

### Completed in this audit pass
- Restored frontend shared `lib` layer (`api`, `api-client`, `auth-api`, `utils`) so Phase 1/2/3/4/7/8/9/10/11/12/13/14/15 pages compile again.
- Fixed backend modular app runtime entrypoint (`app = create_app()` in `backend/app/main.py`) for dev startup compatibility.
- Added backend test suite folder (`backend/tests`) and baseline health/models tests.
- Re-ran validation:
  - Backend tests (`pytest`) ✅
  - Frontend typecheck (`tsc --noEmit`) ✅
  - Frontend production build (`npm run build`) ✅

### Remaining for full Phase 0 completion
- Expand backend test coverage beyond health/models.
- Resolve pre-existing backend lint backlog (Ruff).
- Finish production hardening tasks (auth completeness, monitoring depth, deployment automation).