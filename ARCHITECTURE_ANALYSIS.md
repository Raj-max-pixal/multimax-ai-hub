# MULTIMAX AI HUB — Architecture Analysis & Phase 0 Roadmap

> **Status**: Draft for review  
> **Date**: July 2026  
> **Reviewer**: Raj (Founder)

---

## 1. EXISTING PROJECT STRUCTURE

```
c:\Multimax AI Hub\
├── backend/
│   ├── app/
│   │   ├── auth/          # Custom JWT auth (FastAPI)
│   │   ├── core/          # Config, DB, logging, DI container, plugin loader
│   │   ├── shared/        # Base interfaces
│   │   ├── workspace/     # Workspace module
│   │   └── main.py        # create_app factory
│   ├── services/          # Legacy RAG service
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/    # Layout, ProtectedRoute
│   │   ├── contexts/      # AuthContext (Supabase), ThemeContext, ToastContext
│   │   ├── lib/           # API client, Supabase client, utils
│   │   ├── pages/         # Dashboard, Chat, PDFChat, Voice, Settings, Profile, Login, Signup
│   │   └── types/         # TypeScript interfaces
│   └── package.json       # Vite + React + Tailwind
├── docker/
│   └── docker-compose.yml
└── ARCHITECTURE_ANALYSIS.md (this file)
```

---

## 2. CRITICAL ARCHITECTURAL FINDINGS

### 🔴 RISK 1: Dual Auth Systems — Frontend ≠ Backend

| Layer | Auth Mechanism | Storage |
|-------|---------------|---------|
| **Frontend** | Supabase Auth (JWT from Supabase) | `localStorage` via `@supabase/supabase-js` |
| **Backend** | Custom JWT (`python-jose` + `passlib`) | SQLite via SQLAlchemy |

**Problem**: The frontend never sends its Supabase JWT to the backend. The backend has its own `/auth/login` endpoint generating its own tokens. When the frontend calls `/api/chat` via `api.ts`, **no auth header is sent at all** — the backend's `get_current_user` dependency is never invoked.

**Impact**: The backend's entire auth module is effectively dead code. Any authenticated backend endpoints are unprotected.

**Root Cause**: Two separate auth systems were built independently with no integration point.

### 🟡 RISK 2: No Auth on AI Endpoints

`frontend/src/lib/api.ts` sends requests to `/api/chat`, `/api/models`, `/api/pdf/upload`, `/api/transcribe` with **zero authentication headers**. These are public endpoints in practice.

### 🟡 RISK 3: Mixed Architecture Patterns

The `backend/app/` directory uses a modern DI container + module loader architecture, but:
- `backend/main.py` exists as a **legacy root entry point** (not using the factory pattern)
- `backend/services/rag_service.py` exists outside the module system
- The module loader (`core/module_loader.py`) and plugin manager (`core/plugin_manager.py`) are defined but **not actually used** to wire up the app

### 🟡 RISK 4: Demo Mode Bypasses Security

`AuthContext.tsx` always sets a demo user (`demo-user@multimax.ai`) when Supabase is not configured. This means:
- No real authentication barrier
- No user isolation
- Multi-tenant features impossible
- Data from all users stored in same DB

### 🟢 POSITIVE: Strong Foundation Elements

- **FastAPI app factory pattern** in `app/main.py` is correct
- **DI container** with `python-dependency-injector` is well-structured
- **Configuration management** via Pydantic settings is solid
- **Frontend UI** has polished auth pages (Login, Signup, ForgotPassword) with Zod validation
- **Tailwind CSS + dark mode** implementation is clean
- **Framer Motion** animations are production-quality

---

## 3. RECOMMENDED ARCHITECTURE DECISIONS

### Decision 1: Unify Auth — Use Backend JWT Only

**Chosen approach**: Backend issues JWTs. Frontend stores the token and sends it on every request.

**Why not Supabase-only?** 
- The backend needs to authenticate users for WebSocket connections (chat streaming)
- The backend manages AI model routing, user preferences, conversation storage
- A single token source avoids sync issues between Supabase and backend sessions

**How it works**:
```
Login/Signup → Backend POST /auth/login → Returns JWT
Frontend stores JWT in localStorage
Every API call includes Authorization: Bearer <token>
Backend validates JWT via get_current_user dependency
```

**Supabase role**: Frontend auth UI (OAuth providers) → backend validates the OAuth token and issues its own JWT.

### Decision 2: Real Auth First, Demo Mode Second

- Default to **real auth required**
- Demo mode only activates when `VITE_DEMO_MODE=true` is explicitly set
- Demo mode shows a banner: "⚠️ Demo Mode — Data is not persisted"

### Decision 3: Module Registration via Discovery

Instead of manually wiring modules, use the existing `module_loader.py` to auto-discover and register domain modules from `app/*/`.

### Decision 4: Decorator-based API Client

Replace the manual `fetch()` calls in `api.ts` with an Axios or fetch-based client that automatically:
- Attaches auth tokens
- Handles 401 → redirect to login
- Provides typed responses
- Supports request/response interceptors

---

## 4. PHASE 0 — DETAILED IMPLEMENTATION ROADMAP

### Goal
Build a functioning, secure foundation that connects the frontend and backend with real authentication, a working dashboard, theme support, notifications, Docker deployment, and proper error handling.

### Phased Steps

#### Step 1: Auth Unification (Highest Priority)
**Estimated effort**: 4-6 hours

1. Add a backend endpoint `/auth/supabase-callback` that accepts a Supabase OAuth token, validates it, and returns a backend JWT
2. Update `AuthContext.tsx` to:
   - Store the backend JWT alongside Supabase session
   - Send `Authorization: Bearer <jwt>` on all API calls
   - Handle 401 responses by redirecting to login
3. Add an axios/fetch wrapper in `frontend/src/lib/api-client.ts`:
   - Auto-inject auth header
   - Auto-refresh on 401
   - Typed responses
4. Remove the auto-demo-user fallback (make it opt-in via env var)

#### Step 2: API Client Overhaul
**Estimated effort**: 2-3 hours

1. Create `frontend/src/lib/api-client.ts` (fetch-based, no extra deps)
2. Define typed request/response interfaces
3. Add interceptors for auth, error handling, logging
4. Wire all existing API calls through the new client
5. Add backend health check on app startup

#### Step 3: Dashboard — Real Data from Backend
**Estimated effort**: 3-4 hours

1. Create backend `/dashboard/stats` endpoint returning:
   - Total conversations
   - Active models
   - Recent activity
   - Storage used
2. Update `Dashboard.tsx` to fetch and display real data instead of placeholder cards
3. Add loading skeletons and error states
4. Add quick-action buttons (New Chat, Upload PDF, Voice)

#### Step 4: Settings Page — Functional
**Estimated effort**: 3-4 hours

1. Create backend `/settings/*` endpoints:
   - GET/PUT `/settings/profile`
   - GET/PUT `/settings/notifications`
   - GET `/settings/models` (list available Ollama models)
2. Update `Settings.tsx` tabs to save/load from backend:
   - Profile tab: name, avatar, bio
   - Notifications tab: email, push preferences
   - Appearance tab: theme (already works locally)
   - Models tab: detect local Ollama models, set default
3. Add proper form validation and error handling

#### Step 5: Notifications System
**Estimated effort**: 2-3 hours

1. Create backend `/notifications` endpoints:
   - GET `/notifications` (list recent)
   - PUT `/notifications/{id}/read`
   - PUT `/notifications/read-all`
2. Add notification bell to Layout header
3. Implement notification dropdown with:
   - Unread count badge
   - Click-to-mark-read
   - Empty state
4. Toast system already exists in ToastContext — keep it

#### Step 6: Docker Compose — Working Stack
**Estimated effort**: 2-3 hours

1. Fix `docker-compose.yml` to include:
   - `backend` service (FastAPI + uvicorn)
   - `frontend` service (nginx serving built files, or vite dev mode)
   - `postgres` service (if using PostgreSQL; keep SQLite for now to stay zero-budget)
   - `ollama` service (optional, for local AI models)
2. Add health checks between services
3. Add `Dockerfile.frontend` for production builds
4. Add `.dockerignore` files

#### Step 7: Error Handling & Logging
**Estimated effort**: 2-3 hours

1. Backend:
   - Global exception handler returning structured `{error, detail, request_id}`
   - Request ID middleware for tracing
   - Logging middleware (existing `core/logger.py` needs wiring)
   - Rate limiting (slowapi — free, MIT)
2. Frontend:
   - Global error boundary component
   - API error interceptor → toast notifications
   - Offline detection and reconnection UI

#### Step 8: Profile Page — Functional
**Estimated effort**: 1-2 hours

1. Connect Profile.tsx to backend `/settings/profile` endpoint
2. Add avatar upload (Supabase storage or local filesystem)
3. Add email verification status display

#### Step 9: Deployment — GitHub Actions + Vercel/Cloudflare
**Estimated effort**: 2-3 hours

1. Fix `.github/workflows/ci.yml` to:
   - Run backend tests (pytest)
   - Run frontend build (vite build)
   - Lint both (ruff, eslint)
2. Fix `.github/workflows/deploy.yml` to:
   - Deploy frontend to Vercel (free)
   - Deploy backend instructions for Railway/Render (free tier)
3. Add health check endpoint (`/health/live`, `/health/ready`)

#### Step 10: Testing Foundation
**Estimated effort**: 3-4 hours

1. Backend:
   - pytest setup with `conftest.py` (test DB, test client)
   - Auth tests (signup, login, token refresh, protected routes)
   - Health endpoint tests
2. Frontend:
   - Vitest setup
   - Auth context tests
   - API client mock tests

---

## 5. IMPLEMENTATION ORDER & DEPENDENCIES

```
Step 1 (Auth Unification)
  └─▶ Step 2 (API Client)
       └─▶ Step 3 (Dashboard)
       └─▶ Step 4 (Settings)
       └─▶ Step 5 (Notifications)
       └─▶ Step 8 (Profile)
  ┌── Step 6 (Docker) ── can run in parallel with Steps 3-5
  │
  └── Step 7 (Error Handling) ── can run in parallel
  └── Step 9 (Deployment) ── after Steps 1 & 6
  └── Step 10 (Testing) ── after Steps 1-5
```

---

## 6. RISK MITIGATION SUMMARY

| Risk | Mitigation | Priority |
|------|-----------|----------|
| Dual auth systems dead code | Unify to backend JWT (Step 1) | 🔴 Critical |
| Public AI endpoints | Add auth middleware + token checks (Step 1) | 🔴 Critical |
| Dead module loader/plugin system | Wire into app factory (Step 2) | 🟡 Medium |
| Demo mode bypasses security | Make opt-in via env var (Step 1) | 🟡 Medium |
| No tests | pytest + vitest (Step 10) | 🟡 Medium |
| Docker stack incomplete | Fix compose + health checks (Step 6) | 🟢 Low |

---

## 7. QUESTIONS FOR APPROVAL

1. **Auth strategy**: Backend JWT as the single source of truth? (Recommended) Or keep Supabase as primary and proxy through backend?
2. **Database**: Stay with SQLite for Phase 0 (zero-budget, simple), or set up PostgreSQL in Docker?
3. **Demo mode**: Keep it as opt-in env var, or remove entirely and require real auth?
4. **Testing priority**: Blocking for Phase 0 completion, or can be a Phase 1 task?
5. **Deployment target**: Vercel (frontend) + Railway/Render (backend), or both on a single VPS with Docker?