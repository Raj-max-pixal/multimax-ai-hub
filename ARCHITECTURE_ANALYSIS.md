# Multimax AI Hub — Architecture Analysis & Implementation Roadmap

> **Date:** 2026-07-12  
> **Analyst:** Multimax Dev  
> **Status:** Draft for Founder Approval

---

## 1. Current State Summary

### Backend (FastAPI – `backend/app/`)
| Component | Status | Notes |
|-----------|--------|-------|
| `app/main.py` (factory) | ✅ Solid | Lifespan mgmt, health checks, exception handlers |
| `app/core/config.py` | ✅ Solid | Pydantic Settings, zero-budget defaults (SQLite) |
| `app/core/database.py` | ✅ Solid | Async SQLAlchemy, connection pooling |
| `app/core/logger.py` | ✅ Solid | JSON + console logging |
| `app/core/container.py` | ✅ Solid | Simple DI container |
| `app/core/events.py` | ✅ Solid | In-memory event bus with DLQ |
| `app/core/exceptions.py` | ✅ Solid | Structured error handling |
| `app/core/module_loader.py` | ✅ Good | Auto-discovers domain modules |
| `app/core/plugin_manager.py` | 🟡 Stub | Needs Phase 1+ implementation |
| `app/auth/` | ✅ Solid | JWT with refresh tokens, lockout, admin |
| `app/workspace/` | 🟡 Partial | Models exist, API incomplete |
| `backend/services/rag_service.py` | 🟡 Partial | RAG service exists but not integrated |

### Frontend (React + Vite – `frontend/src/`)
| Component | Status | Notes |
|-----------|--------|-------|
| `App.tsx` (routing) | ✅ Good | React Router, protected routes |
| `contexts/AuthContext.tsx` | 🟡 Mixed | Custom JWT backend + Supabase hybrid — **critical risk** |
| `lib/api.ts` | 🟡 Minimal | Only 4 endpoints (chat, models, PDF upload, transcribe) |
| `lib/supabase.ts` | 🟡 Mixed | Falls back to `null` if no env vars — causes demo mode |
| `pages/AIChat.tsx` | 🟡 Partial | Chat UI exists |
| `pages/PDFChat.tsx` | 🟡 Partial | PDF upload UI |
| `pages/VoiceAssistant.tsx` | 🟡 Partial | Voice UI |
| `pages/Settings.tsx` | 🟡 Partial | Settings UI |
| `pages/Dashboard.tsx` | 🟡 Partial | Dashboard |
| `components/Layout.tsx` | ✅ Good | Sidebar + layout |

### DevOps
| Component | Status | Notes |
|-----------|--------|-------|
| Docker (Compose) | ✅ Exists | Backend + frontend |
| `.github/workflows/` | ✅ Exists | CI + deploy |
| `.devcontainer/` | ✅ Exists | Dev container |
| `Makefile` | ✅ Exists | Build commands |
| `.pre-commit-config.yaml` | ✅ Exists | Code quality |

---

## 2. Critical Architecture Risks

### 🔴 RISK #1: Auth Dualism (Frontend Supabase vs Backend JWT)
**Severity: HIGH**
- **Backend** uses custom JWT auth (`/api/auth/login` → returns `access_token` + `refresh_token`)
- **Frontend** `AuthContext.tsx` is written for **Supabase Auth** (tries `supabase.auth.getSession()`, `supabase.auth.onAuthStateChange()`)
- **Fallback behavior**: If Supabase env vars are missing, the context falls into a **"demo mode"** where it creates a fake user `{ id: 'demo-user', email: 'demo@multimax.ai' }`
- **Consequence**: The frontend NEVER authenticates against the backend API. Every API call from the frontend is unauthenticated. The backend auth module is fully built but completely unused by the frontend.
- **Fix**: Rewrite `AuthContext.tsx` to call the backend's `/api/auth/login`, `/api/auth/register`, `/api/auth/refresh`, and store the JWT token (not Supabase session).

### 🟡 RISK #2: API Client (`api.ts`) Has No Auth Integration
**Severity: HIGH**
- `api.ts` sends no `Authorization: Bearer <token>` header
- All API calls are anonymous
- When Supabase is not configured, the app silently operates in unauthenticated mode
- **Fix**: Create an authenticated API client that reads JWT from AuthContext and attaches it to every request

### 🟡 RISK #3: Backend Auth Is Not Registered as a Module
**Severity: MEDIUM**
- The `app/auth/` module defines its own APIRouter but **it is not imported or included** in `app/main.py`'s `create_app()` or in the module loader
- Looking at the code: `main.py` uses `module_loader.discover("app")` + `module_loader.load_all(app, container)` — this may not include routers unless they are properly structured
- **Fix**: Verify that `app/auth/api.py`'s router is registered. Add explicit router inclusion if needed.

### 🟡 RISK #4: Hardcoded Default Secrets in Production
**Severity: MEDIUM**
- `APP_SECRET_KEY: str = "change-me-to-a-random-secret-key"`
- `AUTH_SECRET_KEY: str = "change-me-to-another-random-secret"`
- If deployed without setting env vars, all JWT tokens can be forged
- **Fix**: Generate random keys on first launch if none set, or fail loudly with a startup validation check

### 🟢 RISK #5: No Rate Limiting Actual Implementation
**Severity: LOW-MEDIUM**
- `API_RATE_LIMIT_PER_MINUTE: int = 60` is defined in config
- But there's no middleware or dependency that enforces it
- **Fix**: Add a simple in-memory rate limiter (or use slowapi)

### 🟢 RISK #6: SQLite for Production
**Severity: LOW (by design)**
- Zero-budget means SQLite is acceptable for MVP
- But SQLite has concurrency limits: only one writer at a time
- **Mitigation**: Document this clearly. Provide easy switch to PostgreSQL.

### 🟢 RISK #7: No Graceful Database Degradation
**Severity: LOW**
- `database.initialize()` failure is caught and logged, allowing health checks to respond
- But subsequent DB queries (e.g., login) will fail with opaque errors
- **Fix**: Add a health-check-aware database proxy that returns degraded responses

---

## 3. Architectural Strengths

| Strength | Details |
|----------|---------|
| ✅ Clean module structure | `app/core/`, `app/auth/`, `app/workspace/` — well-separated |
| ✅ Application factory pattern | `create_app()` with lifespan — follows FastAPI best practices |
| ✅ Event bus abstraction | `EventBus` ABC with in-memory + PostgreSQL backends, DLQ, retry |
| ✅ DI container | Simple but functional — `Container` class with lazy resolution |
| ✅ Config management | Pydantic Settings with env file support |
| ✅ Comprehensive health checks | `/health/live` (liveness) + `/health/ready` (readiness) |
| ✅ Graceful startup degradation | App starts even if DB is unavailable |
| ✅ Type hints everywhere | Full Python type annotations |
| ✅ Docker support | Both backend + frontend Dockerfiles, docker-compose.yml |
| ✅ CI/CD | GitHub Actions workflows |

---

## 4. Improvement Recommendations

### Immediate (Phase 0 Fixes)
1. **Unify auth**: Rewrite `AuthContext.tsx` to use backend JWT auth. Remove Supabase dependency from the auth flow.
2. **Create authenticated API client**: Wrap `fetch` with token management, auto-refresh, and retry.
3. **Register auth router**: Ensure `app/auth/api.py` is included in the FastAPI app.
4. **Add startup secret validation**: Reject startup with hardcoded secrets in production.
5. **Add rate limiting middleware**: Simple in-memory rate limiter.
6. **Create API error handling in frontend**: Intercept 401 responses → redirect to login.

### Short-term (Phase 1)
7. **Implement PostgreSQL event bus**: The `PostgresEventBus` class is a stub — implement it.
8. **Add Alembic migrations**: Required for PostgreSQL in production.
9. **Merge `backend/services/` into module structure**: `rag_service.py` should become `app/rag/`.
10. **Add frontend state management**: Zustand or Jotai for global state.

### Medium-term (Phase 2+)
11. **Implement plugin manager**: The `plugin_manager.py` stub needs real implementation.
12. **Add WebSocket support**: For streaming AI responses.
13. **Implement rate limiting with Redis** (or keep in-memory for zero-budget).
14. **Add comprehensive test suite**: Unit + integration + E2E.

---

## 5. Detailed Implementation Roadmap

### Phase 0 — Foundation (Current Focus)

**Goal:** Production-ready foundation with working auth, settings, dashboard, and deployment.

```
Week 1: Auth Unification
  ├── Rewrite frontend AuthContext → Backend JWT
  ├── Create authenticated API client
  ├── Add token storage (localStorage/HttpOnly cookies)
  ├── Add 401 interceptor → redirect to login
  └── Test full auth flow: register → login → refresh → protected API

Week 2: Dashboard & Settings
  ├── Build real dashboard (stats, model status, recent activity)
  ├── Build settings page (profile, theme, notifications, API keys)
  ├── Add user preferences API
  └── Responsive sidebar navigation

Week 3: Backend Hardening
  ├── Rate limiting (in-memory)
  ├── Startup validation (no default secrets in production)
  ├── Merge services/ → modules/
  ├── Verify auth router registration
  └── Add request logging middleware

Week 4: Docker & Deployment
  ├── Optimize Docker images (multi-stage)
  ├── Docker Compose with all services
  ├── GitHub Actions: test → build → deploy
  ├── Environment variable documentation
  └── Production deployment guide
```

### Phase 1 — AI Chat
```
├── Streaming chat API (SSE)
├── Chat UI with Markdown rendering + code highlighting
├── Chat history (CRUD)
├── Folders + pinned chats
├── Chat search
├── Export chats (JSON/MD/PDF)
├── Prompt library
├── Custom personas
├── Model selection (Ollama + cloud)
└── Basic AI router (task → model mapping)
```

### Phase 2 — Coding Assistant
```
├── Code generation
├── Bug fixing / explanation
├── Refactoring
├── API generation
├── Test generation
├── README generation
├── Git integration (commit messages, PR reviews)
├── Repository analysis (file tree, symbols)
└── Terminal assistant
```

### Phase 3 — Research Engine
```
├── Web search integration (SearXNG / DuckDuckGo)
├── Deep search (multi-query)
├── Website summarization
├── Research reports
├── Citation support
├── Academic search (arXiv, Semantic Scholar)
├── News search
└── Fact checking
```

### Phase 4 — AI Agents
```
├── Browser Use integration
├── Task execution engine
├── Shopping / Booking automation
├── Research agents
├── Data collection agents
├── Multi-step planning
└── Agent monitoring dashboard
```

### Phase 5 — Document Intelligence
```
├── PDF chat (RAG with ChromaDB)
├── Word / Excel / PPT support (Apache Tika)
├── OCR (PaddleOCR)
├── Document summaries
├── Flashcards
├── Q&A extraction
├── Mind maps
└── Knowledge extraction
```

### Phase 6+ — (See original spec for full roadmap)

---

## 6. Architectural Decisions (ADRs)

### ADR-001: Auth Backend — Custom JWT over Supabase Auth
- **Decision**: Use the existing `app/auth/` custom JWT implementation with bcrypt password hashing
- **Rationale**: 
  - Fully self-hosted, zero dependency on external services
  - Complete control over token lifecycle, lockout policies
  - No API rate limits or pricing tiers
- **Consequence**: Frontend must be rewritten to use backend auth endpoints

### ADR-002: Database — SQLite for MVP, PostgreSQL for scale
- **Decision**: Default to SQLite (aiosqlite), provide smooth migration path to PostgreSQL
- **Rationale**:
  - Zero-cost, zero-config for development
  - Easy to containerize
  - SQLAlchemy abstracts the differences
- **Trade-off**: SQLite concurrency is limited; acceptable for single-user / small team use

### ADR-003: AI Model Abstraction — Provider Pattern
- **Decision**: Create an `AIProvider` abstract base class. Implementations: `OllamaProvider`, `OpenAIProvider`, `ClaudeProvider`, etc.
- **Rationale**:
  - New models can be added without changing router or chat logic
  - Users bring their own API keys
  - Local models work out of the box

### ADR-004: State Management — React Context + Zustand
- **Decision**: Use React Context for auth (lightweight), Zustand for complex UI state
- **Rationale**:
  - Zustand is minimal (~1KB), TypeScript-first
  - No boilerplate compared to Redux
  - Works well with the modular architecture

### ADR-005: Event Bus — Adapter Pattern
- **Decision**: Keep the `EventBus` ABC. In-memory for development, PostgreSQL for production.
- **Rationale**:
  - Decouples modules without direct imports
  - Enables future microservice migration
  - DLQ provides resilience

---

## 7. File Structure Plan (After Phase 0)

```
Multimax AI Hub/
├── .github/workflows/
│   ├── ci.yml
│   └── deploy.yml
├── .azure/architecture/        # ADRs + architecture docs
├── .devcontainer/
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── core/               # Foundation layer
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── logger.py
│   │   │   ├── container.py
│   │   │   ├── events.py
│   │   │   ├── exceptions.py
│   │   │   ├── module_loader.py
│   │   │   └── plugin_manager.py
│   │   ├── auth/               # Domain: Auth
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   ├── api.py
│   │   │   └── dependencies.py
│   │   ├── workspace/          # Domain: Workspace (Phase 0)
│   │   │   ├── models.py
│   │   │   ├── service.py
│   │   │   └── api.py
│   │   ├── chat/               # Domain: AI Chat (Phase 1)
│   │   │   ├── models.py
│   │   │   ├── service.py
│   │   │   └── api.py
│   │   ├── documents/          # Domain: Document (Phase 5)
│   │   ├── agents/             # Domain: Agents (Phase 4)
│   │   ├── research/           # Domain: Research (Phase 3)
│   │   ├── voice/              # Domain: Voice (Phase 7)
│   │   ├── images/             # Domain: Images (Phase 8)
│   │   ├── workflows/          # Domain: Workflows (Phase 10)
│   │   └── shared/             # Shared interfaces
│   │       └── interfaces.py
│   ├── services/               # TO BE MERGED into app/
│   ├── data/                   # SQLite database files (gitignored)
│   ├── uploads/                # User uploads (gitignored)
│   ├── .env.example
│   ├── requirements.txt
│   ├── alembic.ini             # (Phase 1)
│   └── alembic/                # (Phase 1)
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── contexts/
│   │   │   ├── AuthContext.tsx  # REWRITTEN: uses backend JWT
│   │   │   └── ThemeContext.tsx
│   │   ├── lib/
│   │   │   ├── api.ts          # REWRITTEN: authenticated client
│   │   │   └── supabase.ts     # REMOVED or kept for storage only
│   │   ├── hooks/
│   │   │   └── useApi.ts       # NEW: hook for API calls
│   │   ├── components/
│   │   │   ├── Layout.tsx
│   │   │   ├── ProtectedRoute.tsx
│   │   │   └── Sidebar.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── AIChat.tsx
│   │   │   ├── PDFChat.tsx
│   │   │   ├── VoiceAssistant.tsx
│   │   │   ├── Login.tsx       # REWRITTEN: uses backend auth
│   │   │   ├── Signup.tsx      # REWRITTEN: uses backend auth
│   │   │   ├── Settings.tsx
│   │   │   └── Profile.tsx
│   │   └── types/
│   │       └── index.ts
│   ├── .env.example
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── postcss.config.js
├── ARCHITECTURE_ANALYSIS.md    # THIS FILE
├── Makefile
├── README.md
├── .env.example
├── .gitignore
└── .editorconfig
```

---

## 8. Technology Decisions for Phase 0

| Concern | Decision | Rationale |
|---------|----------|-----------|
| **Auth tokens** | `localStorage` with auto-refresh | HttpOnly cookies require same-domain, localStorage is simplest for SPA |
| **API client** | Custom `fetch` wrapper with interceptors | No extra dependency, full control |
| **State management** | React Context (auth) + Zustand (UI) | Minimal, no boilerplate |
| **Rate limiting** | In-memory dict with timestamps | Zero dependency, sufficient for MVP |
| **Password hashing** | bcrypt (already in `auth/service.py`) | Industry standard |
| **CSS framework** | Tailwind (already configured) | Zero-cost, highly customizable |
| **UI components** | Custom + Shadcn (to add) | Clean, accessible, MIT licensed |

---

## 9. Success Criteria for Phase 0

1. ✅ User can register → login → see dashboard → logout (full auth cycle)
2. ✅ All API calls include valid JWT tokens
3. ✅ 401 responses redirect to login page
4. ✅ Dashboard shows meaningful data (model status, recent activity)
5. ✅ Settings page allows profile updates + preferences
6. ✅ Backend starts without errors when PostgreSQL is unavailable (uses SQLite)
7. ✅ Rate limiting prevents abuse
8. ✅ App runs in Docker with `docker-compose up`
9. ✅ CI pipeline passes (lint → test → build)
10. ✅ No hardcoded secrets in production mode

---

## 10. Immediate Next Steps (Need Your Approval)

Before writing any code, I need your go-ahead on:

1. **Auth unification approach**: Remove Supabase auth from the frontend entirely? Or keep it as an optional provider alongside custom JWT?
2. **Supabase usage**: Do you want to keep Supabase for storage/database only, or remove it entirely? Zero-budget means self-hosted is preferred.
3. **Module structure**: The current `backend/services/rag_service.py` lives outside the `app/` module structure. Should I merge it into `app/chat/` or `app/documents/`?
4. **Phase 0 scope**: Do you want me to implement ALL items in the Phase 0 section above, or start with just Auth + Dashboard?

**My recommendation:**
- **Start with Auth Unification** (most critical risk)
- **Then Dashboard + Settings** (visible progress)
- **Then Backend Hardening** (rate limiting, validation)
- **Then Docker polish** (deployment-ready)

This gives you working software after each mini-milestone.

---

*Ready for your approval to begin implementation.*