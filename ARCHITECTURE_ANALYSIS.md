# MULTIMAX AI HUB — Architecture Analysis & Implementation Roadmap

> **Document Version:** 1.0  
> **Date:** 2026-07-11  
> **Author:** Architecture Review  
> **Status:** Draft — Awaiting Approval

---

## TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [Current Codebase Overview](#2-current-codebase-overview)
3. [Architecture Deep Dive](#3-architecture-deep-dive)
4. [Critical Risks & Blockers](#4-critical-risks--blockers)
5. [Risk Remediation Plan](#5-risk-remediation-plan)
6. [Phase 0 Implementation Roadmap](#6-phase-0-implementation-roadmap)
7. [Phase 1–15 High-Level Strategy](#7-phase-1-15-high-level-strategy)
8. [Technology Stack Verification](#8-technology-stack-verification)
9. [Free Tier Compliance Audit](#9-free-tier-compliance-audit)
10. [Appendices](#10-appendices)

---

## 1. Executive Summary

Multimax AI Hub is an ambitious project to build the world's most powerful free AI Operating System. The project has a **strong architectural foundation** with clear ADRs, a domain-driven modular backend, and a modern React frontend. However, there are **3 critical risks** that must be resolved before Phase 0 can be considered production-ready, and several medium risks that should be addressed in Phase 0.

### Key Strengths
- ✅ Clean domain module structure (`app/auth/`, `app/workspace/`)
- ✅ Well-documented Architecture Decision Records (ADRs)
- ✅ Proper DI container pattern for service resolution
- ✅ JWT-based auth with refresh token rotation
- ✅ Event-driven communication between modules
- ✅ Docker Compose with PostgreSQL + ChromaDB
- ✅ GitHub Actions CI/CD pipeline
- ✅ Thoughtful zero-budget strategy (SQLite default, local models)

### Key Weaknesses
- ❌ **CRITICAL**: Backend startup may fail due to Python import path issues
- ❌ **CRITICAL**: Global exception handler references `request.app.state` before it's set
- ❌ **CRITICAL**: Frontend auth localStorage vs in-memory token race conditions
- ❌ **MEDIUM**: No test infrastructure exists
- ❌ **MEDIUM**: No rate limiting on auth endpoints
- ❌ **MEDIUM**: Frontend hardcodes localhost:5173 for Vite proxy

---

## 2. Current Codebase Overview

### 2.1 File Structure

```
multimax-ai-hub/
├── backend/
│   ├── main.py                          # Legacy entry point (WARNING: may crash)
│   ├── requirements.txt                 # Python deps
│   ├── app/
│   │   ├── main.py                      # FastAPI app factory (correct entry point)
│   │   ├── __init__.py
│   │   ├── core/
│   │   │   ├── config.py                # Pydantic Settings
│   │   │   ├── container.py             # DI container
│   │   │   ├── database.py              # Async SQLAlchemy manager
│   │   │   ├── events.py                # Event bus
│   │   │   ├── exceptions.py            # Global exception handler
│   │   │   ├── logger.py                # Structured logging
│   │   │   ├── module_loader.py         # Auto-discovery of domain modules
│   │   │   └── plugin_manager.py        # Plugin system skeleton
│   │   ├── shared/
│   │   │   ├── interfaces.py            # Abstract base classes
│   │   ├── auth/
│   │   │   ├── __init__.py              # Module registration
│   │   │   ├── api.py                   # Auth REST endpoints
│   │   │   ├── models.py                # User + RefreshToken ORM
│   │   │   ├── schemas.py               # Pydantic request/response
│   │   │   ├── service.py               # Auth business logic
│   │   │   └── dependencies.py          # FastAPI Depends (auth)
│   │   └── workspace/
│   │       ├── __init__.py              # Module registration
│   │       ├── api.py                   # Workspace endpoints
│   │       ├── models.py                # Workspace ORM
│   │       └── service.py               # Workspace business logic
│   ├── services/
│   │   └── rag_service.py               # RAG service (Phase 1+)
│   ├── legacy/                          # Marked as legacy/README.md
│   └── uploads/
│
├── frontend/
│   ├── src/
│   │   ├── lib/
│   │   │   ├── api-client.ts            # HTTP client w/ token refresh
│   │   │   ├── auth-api.ts              # Auth API wrappers
│   │   │   ├── api.ts                   # Old API client (redundant)
│   │   │   └── supabase.ts             # Removed (stub)
│   │   ├── contexts/
│   │   │   ├── AuthContext.tsx           # Auth state management
│   │   │   └── ThemeContext.tsx          # Theme state
│   │   ├── pages/
│   │   │   ├── AIChat.tsx               # Chat interface (Phase 1)
│   │   │   ├── Login.tsx                # Login page
│   │   │   ├── Signup.tsx               # Signup page
│   │   │   ├── Profile.tsx              # User profile page
│   │   │   └── ...                      # Other pages
│   │   ├── components/
│   │   │   └── Layout.tsx               # App shell w/ sidebar
│   │   └── types/
│   │       └── index.ts                 # Shared types
│   └── package.json                     # Frontend deps
│
├── docker/
│   ├── docker-compose.yml               # PostgreSQL + ChromaDB + Backend
│   └── Dockerfile.backend               # Backend container
│
├── .github/workflows/
│   ├── ci.yml                           # CI pipeline
│   └── deploy.yml                       # CD pipeline
│
├── .azure/architecture/
│   ├── ADR-001 to ADR-005               # Architecture Decision Records
│   ├── ARCHITECTURE_REVIEW.md           # Review notes
│   └── SOFTWARE_ARCHITECTURE_DOCUMENT.md # SAD
│
├── scripts/
│   └── audit_imports.py                 # Import audit tool
│
└── Makefile                             # Dev workflow commands
```

### 2.2 Technology Stack (Verified)

| Layer | Technology | Status |
|-------|-----------|--------|
| Frontend Framework | React 18 + TypeScript | ✅ |
| Build Tool | Vite 5 | ✅ |
| Styling | Tailwind CSS 3.4 | ✅ |
| Animation | Framer Motion 11 | ✅ |
| Routing | React Router 6 | ✅ |
| Icons | Lucide React | ✅ |
| Backend Framework | FastAPI (Python) | ✅ |
| ORM | SQLAlchemy 2.0 (async) | ✅ |
| Auth | Custom JWT (python-jose) | ✅ |
| Password Hashing | Argon2 (via passlib) | ✅ fallback to PBKDF2 |
| Validation | Pydantic v2 | ✅ |
| Database (dev) | SQLite + aiosqlite | ✅ |
| Database (prod) | PostgreSQL + asyncpg | ✅ |
| Vector DB | ChromaDB | ✅ (Docker) |
| Containerization | Docker Compose | ✅ |
| CI/CD | GitHub Actions | ✅ |
| DI Container | Custom (app.core.container) | ✅ |
| Events | Custom (app.core.events) | ✅ |

---

## 3. Architecture Deep Dive

### 3.1 Domain Module Architecture

The project follows a **domain-driven modular architecture** with auto-discovery:

```
backend/app/
├── core/           # Shared infrastructure (framework-agnostic)
│   ├── config.py   # Settings via environment variables
│   ├── container   # DI container for service resolution
│   ├── database    # Async SQLAlchemy engine + session
│   ├── events      # Event bus for cross-module communication
│   ├── logger      # Structured logging
│   └── exceptions  # Global FastAPI exception handlers
│
├── shared/         # Abstract interfaces shared across domains
│   └── interfaces  # Base classes for services, repositories
│
├── auth/           # Domain: Authentication & Users
│   ├── __init__    # Module registration (registers routes, handlers)
│   ├── api         # REST endpoints
│   ├── service     # Business logic
│   ├── models      # SQLAlchemy ORM models
│   ├── schemas     # Pydantic schemas (request/response)
│   └── dependencies # FastAPI dependency injection functions
│
└── workspace/      # Domain: Workspace Management
    ├── __init__    # Module registration
    ├── api         # REST endpoints
    ├── service     # Business logic
    └── models      # SQLAlchemy ORM models
```

**Module Discovery Flow:**
1. `app/main.py` creates the FastAPI app factory
2. `app/core/module_loader.py` scans `app/` for domain packages
3. Each domain's `__init__.py` exports a `register()` function
4. `module_loader` calls `register()` for each discovered module
5. `register()` injects routes, event handlers, and startup/shutdown callbacks into the app

**This is a clean, extensible pattern** — but the `__init__.py` key functions need proper import handling (risk #1).

### 3.2 Authentication Flow

```
Login:
  Client                    Server
    |                         |
    |-- POST /api/auth/login -->|  Validate credentials
    |                         |  Generate JWT access token (15 min)
    |                         |  Generate refresh token (7 days)
    |                         |  Store refresh token hash in DB
    |<-- {access, refresh, user} --|
    |                         |
    |  Store tokens in        |
    |  localStorage + memory  |
    |  Redirect to /          |

Token Refresh:
    |                         |
    |-- POST /api/auth/refresh -->|  Validate refresh token hash
    |                         |  Rotate: revoke old, issue new
    |<-- {new access, new refresh} --|
```

**Token storage concern:** The frontend stores tokens in both `localStorage` and an in-memory variable. On page load, it reads from `localStorage` into memory. A race condition exists between the `localStorage.getItem('access_token')` call and the `setTokens()` call during refresh.

### 3.3 DI Container Pattern

```python
# app/core/container.py
class Container:
    def __init__(self):
        self._services: dict[type, Any] = {}
        self._factories: dict[type, Callable] = {}

    def register(self, interface: type, implementation: type) -> None: ...
    def register_instance(self, interface: type, instance: Any) -> None: ...
    def register_factory(self, interface: type, factory: Callable) -> None: ...
    def resolve(self, interface: type) -> Any: ...

# Usage in API routes:
def _get_auth_service() -> AuthService:
    container = get_container()
    return container.resolve(AuthService)
```

**Observation:** The container uses `get_container()` which is a module-level function — this works but makes testing harder. A future improvement would be to use FastAPI's `app.state` or a request-scoped container.

### 3.4 Event System

```python
# app/core/events.py
event_bus = EventBus()

class EventBus:
    async def emit(self, event: str, data: dict = None): ...
    def on(self, event: str, handler: Callable): ...
    def off(self, event: str, handler: Callable): ...

# Emitted events during auth flow:
# - "auth.user.registered"  (after registration)
# - "auth.user.logged_in"   (after login)
# - "auth.user.logged_out"  (after logout)
```

Events are emitted but **no modules subscribe to them yet**. This is fine for Phase 0 but should be leveraged in Phase 1+ for cross-module communication (e.g., workspace creation on user registration).

---

## 4. Critical Risks & Blockers

### RISK-01: Backend Startup Import Error (CRITICAL)

**Issue:** `backend/main.py` (and potentially `backend/app/__init__.py`) may fail due to Python import path issues.

**Detail:** `backend/main.py` contains:

```python
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))
```

However, the **correct** `app/main.py` (the app factory) exists at `backend/app/main.py`. If `backend/` alone is added to `sys.path`, then imports like `from app.core.config import ...` work correctly. But if `backend/app/` is ever added instead, imports break.

**Impact:** Backend fails to start. All development blocked.

**Detection:** Run `python -m backend.app.main` or `python backend/app/main.py` to verify.

### RISK-02: Global Exception Handler Timing (CRITICAL)

**Issue in `app/core/exceptions.py`:**

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # ... logs error details ...
    # request.app.state may not be available during startup  
```

**Detail:** If an exception occurs **during app startup** (before `lifespan` completes), `request.app.state` may not be initialized. The handler tries to access `request.app.state.start_time` which can raise `AttributeError`.

**Impact:** If a startup error occurs, the error handler itself crashes, producing a 500 with no useful information.

### RISK-03: Auth Token Storage Race Condition (CRITICAL)

**Issue in `frontend/src/lib/api-client.ts`:**

```typescript
let accessToken: string | null = localStorage.getItem('access_token')
let refreshToken: string | null = localStorage.getItem('refresh_token')
```

These are initialized at module load time. But `setTokens()` writes to both localStorage and the in-memory variable. On page load, if the browser restores tab state, the in-memory variable could be stale.

**More critically:** The `getAccessToken()` function is used by `AuthContext.tsx` to check if a user is logged in:

```typescript
useEffect(() => {
    const token = getAccessToken()
    if (!token) {
      setLoading(false)
      return
    }
    // ... try to restore session
}, [])
```

Since the in-memory variable is initialized from `localStorage` at import time, this works. But there's a subtle race: if two tabs are open and one logs out (clearing localStorage), the other tab's in-memory variable still holds the old token. The next API call gets a 401, triggers refresh, which fails, then the user is logged out. This is functionally correct but **not reliable**.

**Real risk:** The `let` declarations at module level are not exported — only `getAccessToken()` is. If another module directly imports these during hot module reload in dev, they get the initial value, not the current value.

### RISK-04: No Test Infrastructure (HIGH)

**Issue:** Zero test files exist. No pytest configuration. No test database setup.

**Impact:** Impossible to verify regressions. Phase 0 changes must be manually tested.

### RISK-05: Auth Rate Limiting (MEDIUM)

**Issue:** Login/register endpoints have no rate limiting. A single client can brute-force passwords or spam registration.

**Impact:** Security vulnerability. Must be addressed before production.

### RISK-06: Frontend Hardcodes Backend URL (MEDIUM)

**Issue in `frontend/src/lib/api-client.ts`:**

```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
```

But in `pages/AIChat.tsx`:

```typescript
fetch('http://localhost:8000/api/chat/send', ...)
```

**Impact:** Hardcoded URLs break in Docker deployment and production.

### RISK-07: Login Redirect Uses Hardcoded Port (MEDIUM)

**Issue in Login.tsx:**

```typescript
window.location.href = 'http://localhost:5173/'
```

**Impact:** Fails in Docker where frontend runs on a different port. Should use relative URL or env variable.

### RISK-08: Missing Database Migration System (MEDIUM)

**Issue:** The app uses `Base.metadata.create_all()` for schema creation (called on startup). This works for development but has no migration path. Schema changes require recreating the database.

**Impact:** Breaking changes in production. No rollback capability.

### RISK-09: workspace module depends on auth model (LOW)

**Issue:** `workspace/service.py` imports from `app.auth.models` directly. While this works, it creates a tight coupling between domains. The workspace module should use the shared interfaces or event bus instead.

### RISK-10: Legacy Code Left in Place (LOW)

**Issue:** `backend/main.py` and `frontend/src/lib/api.ts` are old entry points that should be removed or clearly marked as deprecated. Confusion about which entry point to use.

---

## 5. Risk Remediation Plan

| Risk | Priority | Action | Effort |
|------|----------|--------|--------|
| RISK-01 | **CRITICAL** | Fix import paths, add startup validation | 30 min |
| RISK-02 | **CRITICAL** | Fix exception handler with defensive request.app.state check | 15 min |
| RISK-03 | **CRITICAL** | Centralize token storage, fix AuthContext initialization | 45 min |
| RISK-04 | **HIGH** | Add pytest setup, test database config, write auth unit tests | 2 hours |
| RISK-05 | **MEDIUM** | Add slowapi rate limiting to auth endpoints | 30 min |
| RISK-06 | **MEDIUM** | Replace hardcoded URLs with env variable / proxy config | 20 min |
| RISK-07 | **MEDIUM** | Use relative redirect after login | 10 min |
| RISK-08 | **MEDIUM** | Add Alembic migration setup | 1 hour |
| RISK-09 | **LOW** | Refactor workspace to use event-driven user creation | 30 min |
| RISK-10 | **LOW** | Remove/archive legacy code | 15 min |

---

## 6. Phase 0 Implementation Roadmap

Phase 0 is the **foundation** — it must be rock solid before building any features. The goal is a stable, authenticated, deployable base.

### Step 0: Fix Critical Risks (Day 1)
- [x] **0.1**: Fix RISK-01 — Add backend path to sys.path in `app/__init__.py`
- [ ] **0.2**: Fix RISK-02 — Defensive `request.app.state` in exception handler
- [ ] **0.3**: Fix RISK-03 — Consolidate token storage to localStorage-only with single-source-of-truth
- [ ] **0.4**: Verify backend starts successfully with `uvicorn app.main:create_app --factory`

### Step 1: Authentication Polish (Day 1-2)
- [ ] **1.1**: Add rate limiting to auth endpoints (slowapi)
- [ ] **1.2**: Fix login redirect to use relative path
- [ ] **1.3**: Add password strength validation
- [ ] **1.4**: Add proper frontend route protection (redirect to /login if unauthenticated)
- [ ] **1.5**: Test full auth flow: register → login → protected route → refresh → logout

### Step 2: Dashboard & Navigation (Day 2-3)
- [ ] **2.1**: Create Dashboard page with stats and quick actions
- [ ] **2.2**: Improve sidebar with all Phase 0 navigation items
- [ ] **2.3**: Add responsive mobile navigation
- [ ] **2.4**: Add page transition animations
- [ ] **2.5**: Add keyboard shortcuts (Cmd+K for search, etc.)

### Step 3: Theme & Settings (Day 3)
- [ ] **3.1**: Complete ThemeContext with system preference detection
- [ ] **3.2**: Persist theme preference to backend
- [ ] **3.3**: Create Settings page with tabs (Profile, Appearance, Notifications)
- [ ] **3.4**: Add avatar upload functionality

### Step 4: Profile Management (Day 3-4)
- [ ] **4.1**: Complete Profile page with edit functionality
- [ ] **4.2**: Add email verification flow
- [ ] **4.3**: Add password change flow
- [ ] **4.4**: Add user preferences storage and retrieval

### Step 5: Database Migrations (Day 4)
- [ ] **5.1**: Configure Alembic with async support
- [ ] **5.2**: Generate initial migration from current models
- [ ] **5.3**: Add migration scripts to Docker startup

### Step 6: Docker & Deployment (Day 4-5)
- [ ] **6.1**: Add frontend service to docker-compose.yml
- [ ] **6.2**: Add Nginx reverse proxy configuration
- [ ] **6.3**: Create Dockerfile.frontend
- [ ] **6.4**: Add proper health checks for all services
- [ ] **6.5**: Create .env.example files with all documented variables
- [ ] **6.6**: Test full `docker-compose up` flow

### Step 7: Logging & Error Handling (Day 5)
- [ ] **7.1**: Add structured logging with request IDs
- [ ] **7.2**: Add error reporting endpoints
- [ ] **7.3**: Create friendly error pages (404, 500)
- [ ] **7.4**: Add frontend error boundary components

### Step 8: Testing Infrastructure (Day 5-6)
- [ ] **8.1**: Configure pytest with async support
- [ ] **8.2**: Create test database fixture (SQLite in-memory)
- [ ] **8.3**: Write auth service unit tests
- [ ] **8.4**: Write auth API integration tests
- [ ] **8.5**: Write frontend component tests (Vitest + React Testing Library)
- [ ] **8.6**: Add CI test step to GitHub Actions

### Step 9: API Documentation & Health (Day 6)
- [ ] **9.1**: Verify Swagger UI at /docs is comprehensive
- [ ] **9.2**: Add health check endpoints (live + ready)
- [ ] **9.3**: Add API versioning prefix (/api/v1/...)
- [ ] **9.4**: Add OpenAPI metadata (title, version, description)

### Step 10: Code Quality & Cleanup (Day 6-7)
- [ ] **10.1**: Remove legacy files (backend/main.py, frontend/src/lib/api.ts)
- [ ] **10.2**: Add pre-commit hooks (linting, formatting)
- [ ] **10.3**: Add EditorConfig file (already exists)
- [ ] **10.4**: Verify all imports are correct
- [ ] **10.5**: Document remaining ADRs if needed
- [ ] **10.6**: Final smoke test of entire Phase 0

### Phase 0 Complete ✅ → Phase 1 Begins

---

## 7. Phase 1–15 High-Level Strategy

### Phase 1: AI Chat (Week 2–3)
- Implement Ollama integration for local models (Qwen, DeepSeek, Llama)
- Streaming chat via Server-Sent Events
- Markdown rendering + code highlighting (already partially done)
- Chat history CRUD in PostgreSQL
- Prompt library, custom personas
- Chat folders, search, export

### Phase 2: Coding Assistant (Week 3–4)
- Code generation with DeepSeek
- Git integration (clone, analyze repos)
- Terminal assistant
- Codebase search (ChromaDB for embeddings)

### Phase 3–15: Follow logically
- Research → Agents → Documents → Memory → Voice → Image → Video → Workflows → Marketplace → Team → Mobile → Enterprise

### Key Architectural Decision for Phases 1+
Each new feature should be a **domain module** following the same pattern as `auth/` and `workspace/`:
```
app/{feature}/
├── __init__.py     # module registration
├── api.py          # REST endpoints
├── service.py      # Business logic
├── models.py       # ORM models
└── schemas.py      # Pydantic schemas
```

---

## 8. Technology Stack Verification

### Check: Zero Budget (Free & Open Source)

| Technology | License | Cost | Status |
|-----------|---------|------|--------|
| React | MIT | Free | ✅ |
| Vite | MIT | Free | ✅ |
| Tailwind CSS | MIT | Free | ✅ |
| Framer Motion | MIT | Free | ✅ |
| FastAPI | MIT | Free | ✅ |
| SQLAlchemy | MIT | Free | ✅ |
| ChromaDB | Apache 2.0 | Free | ✅ |
| PostgreSQL | PostgreSQL | Free | ✅ |
| Docker | Apache 2.0 | Free | ✅ |
| Python | PSF | Free | ✅ |
| Node.js | MIT | Free | ✅ |
| TypeScript | Apache 2.0 | Free | ✅ |
| Lucide Icons | ISC | Free | ✅ |

### Check: Self-Hostable
- ✅ All components run locally via Docker Compose
- ✅ SQLite for development (no external DB required)
- ✅ Local AI models via Ollama (no cloud dependency)
- ✅ Vercel free tier for frontend hosting
- ✅ No paid API keys required for default experience

### Check: Modular Architecture
- ✅ Domain modules auto-discover and register
- ✅ Event bus for cross-module communication
- ✅ DI container for service abstraction
- ✅ Plugin manager skeleton (extensible)
- ✅ Docker microservice-friendly

---

## 9. Free Tier Compliance Audit

### Backend Requirements
| Resource | Current | Free Tier Compatible? |
|----------|---------|----------------------|
| Database | SQLite (dev) / PostgreSQL | ✅ SQLite is free. Supabase free tier (500MB) works. |
| Vector DB | ChromaDB | ✅ Self-hosted, free |
| AI Models | Ollama (local) | ✅ Free, runs on own hardware |
| Hosting | Docker (self-hosted) | ✅ Or Vercel free tier (serverless? No — use Railway/Render free) |

### Frontend Requirements
| Resource | Current | Free Tier Compatible? |
|----------|---------|----------------------|
| Hosting | Vite dev | ✅ Vercel free tier |
| Domain | localhost | ✅ Can use Vercel subdomain |
| Storage | Local + Supabase Storage | ✅ Supabase free tier (1GB) |

### Action Item
- The project spec mentions Supabase free tier but the current code uses **custom JWT auth**, not Supabase Auth. This is actually BETTER (no vendor lock-in). The Supabase reference can be removed entirely.
- For deployment, consider **Railway** or **Render** free tier instead of Vercel (since Vercel's free tier is optimized for serverless, and FastAPI is long-running).

---

## 10. Appendices

### A. ADR Summary

| ADR | Title | Status |
|-----|-------|--------|
| ADR-001 | Record Architecture Decisions | ✅ Final |
| ADR-002 | Domain Modules | ✅ Final |
| ADR-003 | AI Provider Abstraction | ✅ Final |
| ADR-004 | Event-Driven Communication | ✅ Final |
| ADR-005 | Zero Budget Stack | ✅ Final |

### B. Key Files Reference

| File | Purpose | Status |
|------|---------|--------|
| `backend/app/main.py` | FastAPI app factory (CORRECT entry point) | ✅ Active |
| `backend/main.py` | Legacy entry point | ⚠️ Deprecated |
| `backend/app/core/config.py` | Environment-based config | ✅ Active |
| `backend/app/auth/service.py` | Auth business logic | ✅ Active |
| `frontend/src/lib/api-client.ts` | HTTP client w/ auto-refresh | ✅ Active |
| `frontend/src/lib/auth-api.ts` | Auth API wrappers | ✅ Active |
| `frontend/src/contexts/AuthContext.tsx` | Auth state provider | ✅ Active |
| `docker/docker-compose.yml` | Infrastructure | ✅ Active |
| `frontend/src/lib/api.ts` | Old API client | ⚠️ Deprecated |

### C. Environment Variables Required

```bash
# Backend (.env)
DATABASE_URL=sqlite+aiosqlite:///./data/multimax.db
AUTH_SECRET_KEY=<generate-with: openssl rand -hex 32>
AUTH_ALGORITHM=HS256
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=15
AUTH_REFRESH_TOKEN_EXPIRE_DAYS=7

# Frontend (.env)
VITE_API_URL=http://localhost:8000
```

---

## APPROVAL CHECKLIST

Before Phase 1 begins, the following must be done:

- [ ] **Risks 1–3** are fixed and verified
- [ ] Backend starts cleanly with `uvicorn app.main:create_app --factory`
- [ ] Frontend starts cleanly with `npm run dev`
- [ ] Auth flow: Register → Login → Refresh → Logout works end-to-end
- [ ] Docker Compose starts all services
- [ ] Tests pass (once test infrastructure is built)
- [ ] Legacy code cleaned up

---

**Prepared for:** Raj (Founder)  
**Review status:** ⏳ Awaiting approval  
**Next action:** Upon approval, begin Step 0 (fix critical risks)