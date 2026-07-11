# Backend Migration Checklist

## Phase 0 – Modular Architecture Foundation

This checklist tracks the migration from the legacy monolithic `backend/main.py` + `backend/services/` 
to the modular `backend/app/` architecture.

### Legend
- ✅ Complete
- 🔄 In Progress
- ⏳ Deferred to Later Phase
- ❌ Not Started

---

### 1. Core Infrastructure (`backend/app/core/`)

| Component | Status | Notes |
|-----------|--------|-------|
| Config (`config.py`) | ✅ | Pydantic Settings, env-aware, secrets manager |
| Container (`container.py`) | ✅ | Dependency Injection with lazy singletons |
| Logger (`logger.py`) | ✅ | JSON + console logging, structured fields |
| Event Bus (`events.py`) | ✅ | In-memory + Postgres backends, retry, DLQ |
| Database (`database.py`) | ✅ | Async SQLAlchemy, session management, migrations |
| Exceptions (`exceptions.py`) | ✅ | Hierarchy: MultimaxError → domain errors |
| Module Loader (`module_loader.py`) | ✅ | Dynamic module discovery |
| Plugin Manager (`plugin_manager.py`) | ✅ | Interface + scaffolding (Full impl → Phase 11) |

### 2. Shared Interfaces (`backend/app/shared/`)

| Component | Status | Notes |
|-----------|--------|-------|
| Repository Interface | ✅ | Generic CRUD with pagination |
| Service Interface | ✅ | Base service contract |
| AI Provider Interface | ✅ | Chat, streaming, model listing |
| Vector Store Interface | ✅ | Embeddings, search, collections |
| Storage Interface | ✅ | File upload/download/delete |
| Cache Interface | ✅ | TTL-based caching |
| Search Interface | ✅ | Full-text search |
| Task Queue Interface | ✅ | Async task processing |

### 3. Workspace Module (`backend/app/workspace/`)

| Component | Status | Notes |
|-----------|--------|-------|
| Models (`models.py`) | ✅ | Workspace, WorkspaceMember, Project (SQLAlchemy) |
| Service (`service.py`) | ✅ | Business logic with event bus integration |
| API (`api.py`) | ✅ | REST endpoints under `/api/v1/workspaces/` |
| Tests | ❌ | Need to create |

### 4. Application Entry Point

| Component | Status | Notes |
|-----------|--------|-------|
| App Factory (`main.py`) | ❌ | Need to create FastAPI app with wire-up |
| Health Endpoint | ❌ | Needed for Docker/K8s health checks |
| Root Router | ❌ | Need to aggregate all domain routers |

### 5. Testing

| Component | Status | Notes |
|-----------|--------|-------|
| Core Tests | ❌ | Config, Container, Logger, Events, DB |
| Workspace Tests | ❌ | API, Service, Models |
| Integration Tests | ❌ | Full app startup |
| Legacy Functionality Tests | ❌ | Verify RAG/chat/document endpoints still work |

### 6. Legacy Code (`backend/legacy/`)

| Component | Status | Notes |
|-----------|--------|-------|
| `main.py` | ✅ | Archived with READ_ONLY marker |
| `services/rag_service.py` | ⏳ | Deferred to Phase 5 (Document Intelligence) |
| `services/document_service.py` | ⏳ | Deferred to Phase 5 |
| `services/embedding_service.py` | ⏳ | Deferred to Phase 5 |
| `services/storage_service.py` | ⏳ | Deferred to Phase 5 |

### 7. Documentation

| Component | Status | Notes |
|-----------|--------|-------|
| CHANGELOG.md | ❌ | Need to create |
| ADR-001 | ✅ | Architecture Decision Records |
| ADR-002 | ✅ | Domain Modules |
| ADR-003 | ✅ | AI Provider Abstraction |
| ADR-004 | ✅ | Event-Driven Communication |
| ADR-005 | ✅ | Zero-Budget Stack |
| README.md | ✅ | Root project README |

---

## Deferred to Future Phases

| Feature | Target Phase | Legacy File |
|---------|-------------|-------------|
| RAG / Document Q&A | Phase 5 | `services/rag_service.py` |
| Document Processing (PDF, Word, Excel) | Phase 5 | `services/document_service.py` |
| Embedding Generation | Phase 5 | `services/embedding_service.py` |
| File Storage | Phase 5 | `services/storage_service.py` |
| Plugin Marketplace | Phase 11 | `core/plugin_manager.py` (scaffold exists) |

---

## How to Verify

```bash
# 1. Check Python imports resolve
python -c "from app.core.config import Settings; print('Config OK')"
python -c "from app.core.container import Container; print('Container OK')"
python -c "from app.workspace.service import WorkspaceService; print('Workspace OK')"

# 2. Start the app
uvicorn app.main:create_app --factory --port 8000

# 3. Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/workspaces/

# 4. Run tests
pytest -v