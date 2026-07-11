# Multimax AI Hub — Architecture Analysis & Implementation Roadmap

> **Date:** 2026-07-12
> **Author:** Architecture Review
> **Status:** Analysis Complete — Awaiting Approval

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current Architecture Overview](#2-current-architecture-overview)
3. [Existing Codebase Analysis](#3-existing-codebase-analysis)
4. [Critical Risks Identified](#4-critical-risks-identified)
5. [Medium Risks Identified](#5-medium-risks-identified)
6. [Low Risks / Observations](#6-low-risks--observations)
7. [Architecture Recommendations](#7-architecture-recommendations)
8. [Phase 0 Detailed Implementation Roadmap](#8-phase-0-detailed-implementation-roadmap)
9. [Phase 1–15 High-Level Roadmap](#9-phase-1-15-high-level-roadmap)
10. [Technology Decisions & Justifications](#10-technology-decisions--justifications)
11. [Zero-Budget Validation](#11-zero-budget-validation)

---

## 1. Executive Summary

The Multimax AI Hub project aims to build a comprehensive AI Operating System that unifies chat, coding, research, agents, documents, voice, image generation, and workflow automation into a single self-hosted platform. The vision is ambitious—combining capabilities of 10+ AI tools into one application.

### Current State

The project already has significant foundational work:
- **Backend:** FastAPI application with modular architecture, DI container, event bus, module loader, database abstraction, and auth module
- **Frontend:** React + Vite + TypeScript with authentication UI, layout components, and API client
- **Core Infrastructure:** Docker setup, CI/CD pipelines, dev container configuration

### Key Findings

| Metric | Assessment |
|--------|-----------|
| **Architecture Quality** | Good - clean modular design with domain-driven patterns |
| **Code Organization** | Excellent - well-structured with clear separation of concerns |
| **Production Readiness** | Moderate - needs hardening for security, error handling, and testing |
| **Zero-Budget Compliance** | Good - SQLite default, in-memory event bus, local storage |
| **Scalability** | Moderate - modular design supports it but needs optimization |
| **Risk Level** | Medium - 3 critical issues need immediate attention |

---

## 2. Current Architecture Overview

### 2.1 Backend Architecture (FastAPI)

```
app/
├── __init__.py
├── main.py                    # Application factory, lifespan, health endpoints
├── core/                      # Core framework services
│   ├── config.py              # Pydantic Settings (env-based configuration)
│   ├── container.py           # DI container (singleton/factory/registry pattern)
│   ├── database.py            # Async SQLAlchemy + SQLite/PostgreSQL
│   ├── events.py              # Event bus (in-memory + PostgreSQL)
│   ├── exceptions.py          # Base exception hierarchy
│   ├── logger.py              # Structured logging (JSON + file rotation)
│   ├── module_loader.py       # Dynamic module discovery & registration
│   └── plugin_manager.py      # Plugin system for future marketplace
├── shared/                    # Shared interfaces & types
│   ├── interfaces.py          # Abstract base classes for domain modules
│   └── __init__.py
├── auth/                      # Domain module: Authentication
│   ├── __init__.py            # Module registration (ModuleInfo + register())
│   ├── api.py                 # REST routes (register, login, refresh, me)
│   ├── dependencies.py        # FastAPI dependency injection (get_current_user)
│   ├── models.py              # SQLAlchemy models (User, RefreshToken)
│   ├── schemas.py             # Pydantic request/response schemas
│   └── service.py             # Business logic (password hashing, JWT, etc.)
└── workspace/                 # Domain module: Workspace
    ├── __init__.py
    ├── api.py
    ├── models.py
    └── service.py
```

**Key Design Patterns:**
- **Application Factory:** `create_app()` in `main.py` returns configured FastAPI instance
- **Lifespan Manager:** Async context manager for startup/shutdown lifecycle
- **Module Discovery:** `ModuleLoader` scans packages and loads `module_info` + `register()` functions
- **DI Container:** Simple type-keyed registry for dependency injection
- **Event Bus:** Abstract base with in-memory and PostgreSQL implementations
- **Error Hierarchy:** `MultimaxError` base with typed subclasses

### 2.2 Frontend Architecture (React + Vite)

```
frontend/src/
├── main.tsx                   # React entry point
├── App.tsx                    # Root component with routing
├── lib/                       # API clients and utilities
│   ├── api.ts                 # Base API client
│   ├── api-client.ts          # Enhanced API client with auth
│   ├── auth-api.ts            # Auth-specific API calls
│   └── supabase.ts            # Supabase client (optional)
├── contexts/
│   └── AuthContext.tsx         # Auth state management (React Context)
├── components/
│   └── Layout.tsx              # App layout with sidebar/navigation
├── pages/
│   ├── AIChat.tsx              # AI Chat interface (Phase 1 backbone)
│   ├── Login.tsx               # Login page
│   ├── Signup.tsx              # Registration page
│   └── Profile.tsx             # User profile page
└── types/
    └── index.ts                # TypeScript type definitions
```

### 2.3 Data Flow

```
┌──────────┐     HTTP/JSON      ┌─────────────┐     SQL/ORM      ┌──────────┐
│  Browser  │ ◄──────────────► │   FastAPI    │ ◄──────────────► │  SQLite  │
│ (React)   │                  │  (Uvicorn)   │                  │ (Secure) │
└──────────┘                   └──────┬──────┘                  └──────────┘
                                      │
                             ┌────────┴────────┐
                             │   Event Bus     │
                             │  (In-Memory)    │
                             └─────────────────┘
```

---

## 3. Existing Codebase Analysis

### 3.1 Strengths

1. **Solid Modular Architecture:** The domain module pattern (`module_info` + `register()`) is clean and extensible. Adding new features requires creating a new package with a standard interface.

2. **Production-Quality Error Handling:** The exception hierarchy (`MultimaxError` → `NotFoundError`, `AuthenticationError`, etc.) is well-designed.

3. **Async-First Design:** Full async/await throughout the backend with proper async database sessions.

4. **Configuration Management:** Pydantic Settings with environment variable support is the right choice. Sensible defaults for development.

5. **Security Baseline:** Password hashing, JWT with refresh tokens, rate limiting configuration, and admin role checks are in place.

6. **Frontend Type Safety:** TypeScript throughout with shared type definitions.

### 3.2 Weaknesses

1. **Inconsistent Service Instantiation:** AuthService is created with `AuthService()` in route handlers instead of using the DI container. The container registers a singleton but routes bypass it.

2. **Supabase Auth Dependency:** The frontend has both custom JWT auth and Supabase auth configured simultaneously, creating confusion about which auth system is active.

3. **Legacy Backend Code:** `backend/services/rag_service.py` and `backend/app/core/plugin_manager.py` appear to be legacy/unused code that could cause confusion.

4. **Exception Handler Signature Mismatch:** `main.py` uses `error_code` and `detail` in exception responses, but `exceptions.py` uses `code` and `message`. This means the exception handler will produce `None` values for actual errors.

5. **Missing Tests:** No test files found for the core framework code (config, container, events, module_loader).

6. **No Migration System:** Alembic is referenced in config but not set up. Schema changes require manual intervention.

---

## 4. Critical Risks Identified

### 🔴 CRITICAL-1: Exception Handler/Exception Class Field Mismatch

**Location:** `backend/app/main.py` lines 183–191 vs `backend/app/core/exceptions.py` lines 20–34

**Problem:** The exception handler expects `exc.error_code`, `exc.detail`, and `exc.context`, but the `MultimaxError` base class defines `self.code`, `self.message`, and `self.details`. All error responses will return `null` for these fields:

```python
# main.py (line 189) — reads:
content = {"error": exc.error_code, "message": exc.detail, "context": exc.context}
# But exceptions.py defines:
self.message = message   # not "detail"
self.code = code         # not "error_code"
self.details = details or {}  # not "context"
```

**Impact:** All error responses from the API will be broken — returning `null` for error codes and messages. Frontend error handling will fail silently.

**Severity:** Critical — affects ALL API error responses

**Fix:** Standardize field names (either change the exception class or change the handler)

---

### 🔴 CRITICAL-2: AuthService Instantiation Bypasses DI Container

**Location:** `backend/app/auth/api.py` lines 59, 85, 116, 143, 175, 215, 245

**Problem:** Every route handler creates a new `AuthService()` instance directly instead of resolving from the DI container. The container registers a singleton (line 49 in `auth/__init__.py`) but no route ever uses it. This means:
- No shared state (e.g., database sessions are created fresh each time)
- No testability (can't mock AuthService in tests)
- Potential resource leaks from unmanaged database connections

**Impact:** Inconsistent database sessions, inability to unit test routes, wasted resources

**Severity:** Critical — undermines the entire DI pattern

**Fix:** Replace `Depends(lambda: AuthService())` with `Depends(get_auth_service)` where `get_auth_service` resolves from container

---

### 🔴 CRITICAL-3: Module Discovery Path Mismatch

**Location:** `backend/app/main.py` line 92

**Problem:** The module loader discovers modules in `"app"` as the base package, but it expects subpackages with `module_info`. The `auth` module is at `app.auth` (a subpackage), and `app.auth.__init__` has the proper `module_info` + `register()`. However, scanning `"app"` will also attempt to scan `app.core`, `app.shared`, etc., which are NOT modules and don't have `module_info`.

**Impact:** The `discover()` call on line 92 will either:
- Fail for non-module subpackages (generating warning logs)
- Miss modules if they're structured differently
- Load modules in unpredictable order

**Severity:** Critical — module discovery is the backbone of the plugin architecture

---

## 5. Medium Risks Identified

### 🟡 MEDIUM-1: Secret Key in Code Defaults

**Location:** `backend/app/core/config.py` lines 26, 101

**Problem:** Default values for `APP_SECRET_KEY` and `AUTH_SECRET_KEY` are "change-me-to-a-random-secret-key" and "change-me-to-another-random-secret". While documented as changeme values, there's no validation or warning if these defaults are used in production.

**Impact:** Critical security vulnerability if accidentally deployed with default keys

---

### 🟡 MEDIUM-2: Rate Limiting Configuration But No Implementation

**Location:** `backend/app/core/config.py` line 115

**Problem:** `API_RATE_LIMIT_PER_MINUTE` is defined but no rate-limiting middleware is installed or configured.

**Impact:** API is vulnerable to abuse and DoS attacks

---

### 🟡 MEDIUM-3: Legacy/Unused Code Files

**Location:** `backend/services/rag_service.py`, `backend/app/core/plugin_manager.py`

**Problem:** These files appear to be legacy or experimental. They import from modules that don't exist or reference outdated patterns. Could confuse developers and increase maintenance burden.

---

### 🟡 MEDIUM-4: No Database Migration System

**Problem:** The project creates tables via `Base.metadata.create_all()` on startup (development mode). This is not safe for production — schema changes require manual intervention and there's no version control for database changes.

**Impact:** Production deployment risk — schema changes are irreversible and unversioned

---

## 6. Low Risks / Observations

### 🟢 LOW-1: Health Readiness Probe Returns 200 Instead of 503

**Location:** `backend/app/main.py` lines 157–176

**Observation:** The readiness check returns `{"status": "unavailable"}` as a JSON response with default status code 200 when `app.state.multimax` is missing. It should return HTTP 503. The `JSONResponse(status_code=503, ...)` is only used for AttributeError, but the main try block returns a dict (which FastAPI converts to 200).

### 🟢 LOW-2: CORS Origins Hardcoded

**Location:** `backend/app/core/config.py` lines 116–119

**Observation:** CORS origins are hardcoded as a comma-separated string. For production, this should be `["*"]` temporarily or loaded from environment properly.

### 🟢 LOW-3: SQLite Concurrency

**Observation:** SQLite is the default database (zero-budget compliant), but SQLite has limited concurrent write support. For multi-user scenarios, PostgreSQL will be necessary.

### 🟢 LOW-4: No Input Sanitization on Frontend

**Observation:** Chat inputs and API request bodies don't show evidence of sanitization for XSS or injection attacks.

---

## 7. Architecture Recommendations

### 7.1 Critical Fixes (Must Do Before Phase 0 Completion)

1. **Fix exception handler/exceptions field mismatch** (CRITICAL-1)
2. **Fix AuthService DI container usage** (CRITICAL-2)
3. **Fix module discovery to scan specific module directories** (CRITICAL-3)

### 7.2 Recommended Improvements

1. **Add rate limiting middleware** (e.g., `slowapi` or custom middleware)
2. **Add production startup validation** — warn if default secrets are used
3. **Set up Alembic migrations** for production-safe schema management
4. **Clean up legacy code** — remove or archive `services/` and old files
5. **Add comprehensive tests** for core framework components
6. **Standardize API response format** (current is inconsistent between auth and health endpoints)

### 7.3 Architecture Decisions for Phase 1+

| Decision | Recommendation | Rationale |
|----------|---------------|-----------|
| AI Provider Abstraction | Build `AIModelProvider` abstract base with Ollama/LiteLLM implementations | Enables router to switch models dynamically |
| Chat Storage | SQLAlchemy model with async session | Reuses existing database layer |
| Streaming | Server-Sent Events (SSE) via FastAPI `StreamingResponse` | Native FastAPI support, no extra dependencies |
| Vector Database | ChromaDB (lightweight, self-hostable) | Zero-budget compliant, Python-native |
| Search | SearXNG (self-hosted meta search engine) | Free, privacy-respecting |
| Voice | Whisper (local) + Coqui TTS (local) | Both are MIT-licensed, run locally |
| Image Generation | Stable Diffusion via ComfyUI API | Free, self-hostable |

---

## 8. Phase 0 Detailed Implementation Roadmap

### 8.1 Overview

Phase 0 is the foundation — everything in Phase 1+ depends on it being solid. Current state is approximately 65% complete for Phase 0.

**Estimated Effort:** 2–3 weeks for a single developer
**Priority:** Security fixes → Core hardening → Tests → Documentation

### 8.2 Step-by-Step Tasks

#### Step 1: Fix Critical Security/Architecture Issues (Days 1–2)

| Task | File(s) | Description |
|------|---------|-------------|
| 1.1 Fix exception field mismatch | `core/exceptions.py` and/or `main.py` | Align field names between exception class and handler |
| 1.2 Fix AuthService DI | `auth/api.py` | Use container-resolved AuthService instead of direct instantiation |
| 1.3 Fix module discovery | `core/module_loader.py` and `main.py` | Limit discovery to `app.auth`, `app.workspace`, `app.chat` etc. |
| 1.4 Add secret key validation | `core/config.py` | Warn on startup if default secrets are used |
| 1.5 Add rate limiting | `main.py` + dependencies | Install and configure rate limiting middleware |

#### Step 2: Authentication Hardening (Days 2–3)

| Task | File(s) | Description |
|------|---------|-------------|
| 2.1 Review JWT implementation | `auth/service.py`, `auth/dependencies.py` | Verify token expiration, rotation, and revocation |
| 2.2 Add password policy | `auth/schemas.py`, `auth/service.py` | Minimum length, complexity requirements |
| 2.3 Fix readiness probe HTTP status | `main.py` | Return 503 when app state is uninitialized |
| 2.4 Clean up Supabase references | `frontend/src/lib/supabase.ts`, `frontend/src/contexts/AuthContext.tsx` | Clarify auth direction (remove or document Supabase usage) |

#### Step 3: Core Framework Hardening (Days 3–5)

| Task | File(s) | Description |
|------|---------|-------------|
| 3.1 Add comprehensive error handling | All route handlers | Ensure all exceptions are caught and returned consistently |
| 3.2 Add request/response logging middleware | `core/middleware.py` (new) | Log all API requests with timing |
| 3.3 Add database connection pooling config | `core/database.py` | Configure pool size, overflow, timeouts |
| 3.4 Add health check depth | `core/database.py`, `main.py` | Add database ping to readiness check |
| 3.5 Add graceful shutdown timeout | `main.py` | Configure graceful shutdown with timeout |

#### Step 4: Database & Migration Setup (Days 4–6)

| Task | File(s) | Description |
|------|---------|-------------|
| 4.1 Set up Alembic | `backend/alembic/` (new) | Initialize migration repository |
| 4.2 Create initial migration | Alembic | Auto-generate migration for existing models |
| 4.3 Add migration documentation | `README.md` | Document how to create and run migrations |
| 4.4 Add migration CI check | `.github/workflows/ci.yml` | Verify migrations are up to date in CI |

#### Step 5: Clean Up Legacy Code (Days 5–6)

| Task | File(s) | Description |
|------|---------|-------------|
| 5.1 Audit `backend/services/` | All files in directory | Remove or refactor legacy RAG service |
| 5.2 Audit `backend/app/core/plugin_manager.py` | `plugin_manager.py` | Determine if needed; remove if legacy |
| 5.3 Archive unused test files | `backend/test_*.py`, root `test_*.py` | Move to `backend/legacy/` |
| 5.4 Remove duplicate config files | `.env.example` files | Ensure single source of truth for env vars |

#### Step 6: Testing Infrastructure (Days 6–8)

| Task | File(s) | Description |
|------|---------|-------------|
| 6.1 Set up pytest with async support | `pyproject.toml` or `setup.cfg` | Configure pytest-asyncio |
| 6.2 Write core config tests | `tests/test_config.py` | Test settings loading, env override |
| 6.3 Write container tests | `tests/test_container.py` | Test registration, resolution, lifecycle |
| 6.4 Write event bus tests | `tests/test_events.py` | Test publish/subscribe, retry, dead letter |
| 6.5 Write module loader tests | `tests/test_module_loader.py` | Test discovery and loading |
| 6.6 Write auth tests | `tests/test_auth.py` | Test registration, login, token refresh |
| 6.7 Write API integration tests | `tests/test_api.py` | Test health endpoints, error responses |

#### Step 7: Frontend Foundation (Days 7–9)

| Task | File(s) | Description |
|------|---------|-------------|
| 7.1 Review auth flow | `AuthContext.tsx`, `Login.tsx`, `Signup.tsx` | Ensure consistent auth state management |
| 7.2 Add protected route component | `components/ProtectedRoute.tsx` (new) | Redirect unauthenticated users |
| 7.3 Add error boundary | `components/ErrorBoundary.tsx` (new) | Graceful error handling for React |
| 7.4 Add loading states | All pages | Skeleton loading components |
| 7.5 Standardize API client | `api-client.ts` | Consistent error handling, auth headers |
| 7.6 Add development proxy config | `vite.config.ts` | Proxy API calls to backend during dev |

#### Step 8: Docker & Deployment (Days 8–10)

| Task | File(s) | Description |
|------|---------|-------------|
| 8.1 Fix Dockerfile for production | `Dockerfile.backend` | Optimize for production (multi-stage build) |
| 8.2 Add frontend Dockerfile | `Dockerfile.frontend` (new) | Serve built frontend via Nginx |
| 8.3 Complete docker-compose | `docker-compose.yml` | Add frontend, ChromaDB, Ollama services |
| 8.4 Add health check to compose | `docker-compose.yml` | Docker health check for each service |
| 8.5 Add volume management | `docker-compose.yml` | Persistent volumes for SQLite, uploads |
| 8.6 Document deployment | `README.md`, deployment guide | Step-by-step deployment instructions |

#### Step 9: Documentation & Developer Experience (Days 9–11)

| Task | File(s) | Description |
|------|---------|-------------|
| 9.1 Complete README | `README.md` | Architecture overview, setup instructions |
| 9.2 Add API documentation | Auto-generated via FastAPI | Ensure all endpoints are documented |
| 9.3 Add contributing guide | `CONTRIBUTING.md` (new) | Development workflow, PR process |
| 9.4 Add code of conduct | `CODE_OF_CONDUCT.md` (new) | Community guidelines |
| 9.5 Add editor config | `.editorconfig` (exists) | Ensure consistency |
| 9.6 Add pre-commit hooks | `.pre-commit-config.yaml` (exists) | Lint, format, type-check |

#### Step 10: Hardening & Polish (Days 11–14)

| Task | File(s) | Description |
|------|---------|-------------|
| 10.1 Add input validation | All Pydantic schemas | Ensure strict validation on all inputs |
| 10.2 Add CORS hardening | `config.py` | Restrict origins in production |
| 10.3 Add security headers | `main.py` | Add helmet-like middleware |
| 10.4 Add logging rotation config | `logger.py` | Ensure logs don't fill disk |
| 10.5 Performance baseline | All | Profile and document baseline performance |
| 10.6 Security audit | All | Review for common vulnerabilities |

---

## 9. Phase 1–15 High-Level Roadmap

```
Phase 0: Foundation (Weeks 1-3)
├── Backend Framework [DONE ~65%]
├── Authentication [DONE ~80%]
├── Frontend Shell [DONE ~50%]
└── Infrastructure [DONE ~40%]

Phase 1: AI Chat (Weeks 3-6)
├── Ollama Integration
├── Chat UI with Streaming
├── Chat History & Management
├── Markdown Rendering
└── File Upload Support

Phase 2: Coding Assistant (Weeks 6-9)
├── Code Generation
├── Code Explanation & Refactoring
├── Git Integration
└── Repository Analysis

Phase 3: Research Engine (Weeks 9-11)
├── Web Search Integration (SearXNG)
├── Deep Search & Analysis
├── Citation Management
└── Research Reports

Phase 4: AI Agents (Weeks 11-14)
├── Browser Control Agent
├── Task Execution Engine
├── Multi-Step Planning
└── Data Collection

Phase 5: Document Intelligence (Weeks 14-17)
├── PDF Processing
├── Document OCR
├── Knowledge Extraction
└── Mind Maps

Phase 6: Memory System (Weeks 16-18)
├── Long-Term Memory
├── Knowledge Graph
├── User Preferences
└── Memory Search

Phase 7: Voice AI (Weeks 18-20)
├── Speech-to-Text (Whisper)
├── Text-to-Speech (Coqui)
├── Voice Chat Interface
└── Voice Commands

Phase 8: Image Studio (Weeks 20-23)
├── Image Generation
├── Logo & Thumbnail Creation
├── Photo Editing
└── Background Removal

Phase 9: Video Studio (Weeks 23-26)
├── Video Generation
├── Subtitle Generator
├── Avatar Videos
└── Shorts Generator

Phase 10: Workflow Automation (Weeks 26-30)
├── Visual Workflow Builder
├── Integration Connectors
├── Triggers & Schedules
└── AI Workflows

Phase 11: Plugin Marketplace (Weeks 30-33)
├── Plugin Installation System
├── MCP Server Support
├── Version Management
└── Community Plugin Support

Phase 12: Team Workspace (Weeks 33-36)
├── Organizations
├── Permissions & Roles
├── Shared Resources
└── Real-Time Collaboration

Phase 13: Marketplace (Weeks 36-39)
├── Publishing System
├── Agent Marketplace
├── Template Marketplace
└── Community Features

Phase 14: Mobile Apps (Weeks 39-44)
├── Android App
├── iOS App
├── Tablet Support
└── Mobile-First UI

Phase 15: Enterprise (Weeks 44-48+)
├── SSO & SAML
├── Audit Logs
├── Advanced RBAC
└── Enterprise APIs
```

---

## 10. Technology Decisions & Justifications

### Backend

| Technology | Status | Justification |
|------------|--------|---------------|
| **Python 3.11+** | ✅ Chosen | Best ecosystem for AI/ML, async support |
| **FastAPI** | ✅ Chosen | Async-native, auto-docs, fast performance |
| **SQLAlchemy 2.0** | ✅ Chosen | Mature async ORM, Alembic integration |
| **SQLite** | ✅ Default | Zero-budget, file-based, no server needed |
| **PostgreSQL** | ✅ Future | When scaling beyond single-user SQLite limits |
| **ChromaDB** | ✅ Chosen | Python-native vector DB, self-hostable |
| **Ollama** | ✅ Chosen | Run LLMs locally, no API costs |
| **LiteLLM** | ⚠️ Consider | For cloud API proxy (when user provides keys) |
| **Alembic** | ⚠️ Not set up | Needed for production migrations |

### Frontend

| Technology | Status | Justification |
|------------|--------|---------------|
| **React 18+** | ✅ Chosen | Mature ecosystem, hooks-based |
| **TypeScript** | ✅ Chosen | Type safety, better DX |
| **Vite** | ✅ Chosen | Fast HMR, modern bundler |
| **Tailwind CSS** | ✅ Chosen | Utility-first, fast UI development |
| **Shadcn UI** | ⚠️ Not installed | Excellent component library, radix-based |
| **React Router** | ⚠️ Not installed | Needed for proper routing |

### Infrastructure

| Technology | Status | Justification |
|------------|--------|---------------|
| **Docker** | ✅ Chosen | Portable deployment, dev/prod parity |
| **GitHub Actions** | ✅ Chosen | Free CI/CD for open-source projects |
| **Cloudflare** | ⚠️ Future | Free CDN, DDoS protection |
| **Dev Containers** | ✅ Chosen | Standardized development environment |

---

## 11. Zero-Budget Validation

Every technology choice has been validated against the zero-budget requirement:

| Component | Cost | Alternative if Paid |
|-----------|------|---------------------|
| **Database** | $0 (SQLite) | PostgreSQL (free self-hosted) |
| **Vector DB** | $0 (ChromaDB) | Pinecone (paid) |
| **LLM Inference** | $0 (Ollama) | OpenAI API (paid) |
| **Speech-to-Text** | $0 (Whisper) | Google STT (paid) |
| **Text-to-Speech** | $0 (Coqui TTS) | ElevenLabs (paid) |
| **Search** | $0 (SearXNG) | Google Search API (paid after 100 queries/day) |
| **Image Gen** | $0 (Stable Diffusion) | DALL-E 3 (paid) |
| **Object Storage** | $0 (Local + Supabase free tier) | AWS S3 (paid) |
| **CI/CD** | $0 (GitHub Actions free) | CircleCI (paid) |
| **Auth** | $0 (Custom JWT) | Auth0 (paid tier) |
| **Monitoring** | $0 (Structured logging) | Datadog (paid) |
| **OCR** | $0 (PaddleOCR/Tesseract) | Azure Document Intelligence (paid) |

**Total Monthly Cost for Self-Hosted Setup: $0–$5** (domain name + basic VPS if not self-hosted on existing hardware)

---

## Summary of Required Actions

### Immediate (Before Proceeding)
1. ✅ ~~Read and understand the project vision~~ (Completed)
2. ⬜ Fix exception handler mismatch (CRITICAL-1)
3. ⬜ Fix AuthService DI pattern (CRITICAL-2)
4. ⬜ Fix module discovery path (CRITICAL-3)

### Short-Term (Phase 0 Completion)
5. ⬜ Add rate limiting middleware
6. ⬜ Set up Alembic migrations
7. ⬜ Clean up legacy code files
8. ⬜ Add comprehensive test suite
9. ⬜ Complete Docker setup
10. ⬜ Complete documentation

### Medium-Term (Before Phase 1 Start)
11. ⬜ Implement AI provider abstraction
12. ⬜ Implement chat persistence
13. ⬜ Build streaming infrastructure
14. ⬜ Set up vector database integration

---

**Ready for your review and approval.** Once you approve this roadmap, I'll begin implementing Phase 0 step by step, fixing the critical issues first, then systematically building out the remaining foundation.

Would you like to proceed with the implementation?