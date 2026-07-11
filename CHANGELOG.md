# Changelog

All notable changes to the Multimax AI Hub will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.4.0] - 2026-07-11 — Phase 0: Modular Architecture Foundation

### Added
- **Application Factory** (`backend/app/main.py`)
  - FastAPI app with lifespan-based startup/shutdown
  - Liveness + readiness health endpoints (`/health/live`, `/health/ready`)
  - CORS middleware from Settings
  - Exception handlers for `MultimaxError` + general exceptions
- **Domain Module System** (`backend/app/core/module_loader.py`)
  - `ModuleLoader` — dynamic discovery and loading of domain modules
  - `ModuleInterface` — contract that each module must follow
  - `ModuleInfo` — metadata class for module registration
- **Workspace Module** (`backend/app/workspace/`)
  - `register()` function for Module Loader integration
  - Full CRUD for workspaces, members, and projects
  - DI container registration of WorkspaceService
- **Configuration** (`backend/app/core/config.py`)
  - Pydantic-v2 `Settings` with env-file support
  - Comprehensive settings for DB, AI providers, auth, storage, event bus
- **Dependency Injection Container** (`backend/app/core/container.py`)
  - Type-safe generic DI with singletons, factories, and transient registrations
  - Global singleton container with auto-initialization
- **Event Bus** (`backend/app/core/events.py`)
  - In-memory and PostgreSQL backends
  - Event priority, retry with exponential backoff, dead-letter queue
- **Database Layer** (`backend/app/core/database.py`)
  - Async SQLAlchemy with asyncpg driver
  - Session context manager with auto-commit/rollback
  - `Base` ORM model for all domain models
- **Structured Logging** (`backend/app/core/logger.py`)
  - JSON and console output formats
  - Correlation ID support
  - File rotation and structured fields
- **Exception Hierarchy** (`backend/app/core/exceptions.py`)
  - `MultimaxError` → domain-specific subclasses
  - Standardized error codes and HTTP status mapping
- **Shared Interfaces** (`backend/app/shared/interfaces.py`)
  - Repository, Service, AI Provider, Vector Store, Storage, Cache, Search, Task Queue
- **Plugin Manager Scaffold** (`backend/app/core/plugin_manager.py`)
  - Interface for future Plugin Marketplace (Phase 11)
- **Legacy Code Archive** (`backend/legacy/`)
  - Original monolithic `main.py` and `services/` preserved as read-only reference
- **Migration Checklist** (`backend/app/MIGRATION_CHECKLIST.md`)
  - Tracks migration status of all components from legacy to modular architecture

### Changed
- Workspace `__init__.py` now exports `module_info` as `ModuleInfo` object + `register()` function
- Workspace `__init__.py` uses `from __future__ import annotations` for type safety

### Removed
- Workspace `__init__.py` no longer exports plain dict as `module_info`

### Technical Debt / Known Issues
- Authentication is still a stub (`get_current_user_id` returns `"system"`)
- Workspace service uses in-memory storage; database integration pending
- Full RAG, document processing, and file storage deferred to Phase 5
- Plugin Manager is scaffold only; full implementation in Phase 11
- Module Loader `discover("app")` scans the `app` package for subpackages;
  currently only `app.workspace` is a valid domain module.
- Tests not yet created for core infrastructure or workspace module
- Database migrations not yet implemented (Alembic setup deferred)

---

## [0.3.0] - 2025-09-21 — Legacy Monolithic Backend

### Changed
- The original monolithic `backend/main.py` with all routes in a single file
- `backend/services/` with RAG, document, embedding, and storage services
- Basic FastAPI server with CORS, static file serving, and health check
- Ollama integration for local AI model inference
- ChromaDB integration for vector search
- File upload and document parsing (PDF, DOCX)
- Frontend Vite + React + TypeScript setup with Tailwind and Shadcn UI
- Initial Docker configuration

### Legacy Notice
Starting from 0.4.0, the codebase has been refactored into a modular
domain-driven architecture. The original monolithic code is preserved
in `backend/legacy/` for reference only.

---

## [0.2.0] - 2025-07-15

### Added
- Basic project scaffolding
- Frontend setup with Vite + React + TypeScript
- Backend setup with FastAPI + Python
- Initial Docker Compose configuration

---

## [0.1.0] - 2025-06-01

### Added
- Project initialization
- README with project vision and mission
- MIT License
- Initial Git repository setup