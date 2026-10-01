# Multimax AI Hub V2 Architecture Assessment

**Assessment date:** 2026-09-20  
**Scope:** Current executable repository, not phase-completion claims in historical Markdown files  
**Decision:** Preserve the modular foundation and working UI/provider code; replace broken persistence boundaries incrementally.

## 1. Executive assessment

Multimax AI Hub is a broad prototype with a useful React workspace UI, a FastAPI application factory, domain-oriented packages, JWT authentication, asynchronous SQLAlchemy infrastructure, a provider registry, Ollama/Gemini streaming, and initial Docker/CI files. These are good foundations and should be preserved.

It is not yet a production-grade AI platform. The main issue is not missing pages; it is that the product has three overlapping implementation layers:

1. modular domain packages under `backend/app/*`;
2. backward-compatible endpoints embedded in `backend/app/main.py`;
3. legacy and root services under `backend/legacy`, `backend/services`, and `backend/main.py`.

Several Phase 1-15 features exist only as screens, in-memory endpoints, local browser state, stubs, or code that cannot configure its ORM mappers. The safest path is to make the modular application the single system of record, retain compatibility routes as thin adapters while clients migrate, and complete one infrastructure milestone at a time.

## 2. Verified baseline

### Working and worth preserving

| Area | Verified implementation | Decision |
|---|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind, protected route shell, lazy-loaded pages | Preserve; progressively split large pages into feature components |
| Authentication | JWT access/refresh flow, password hashing, refresh-token persistence, frontend refresh handling | Preserve core service; harden sessions, cookies/token storage, rate limits, and authorization |
| Backend composition | FastAPI app factory, lifespan management, domain packages, common error types | Preserve; remove silent module-load failure and reduce `main.py` responsibilities |
| Database access | SQLAlchemy 2 async manager and request-scoped sessions | Preserve interface; correct pooling, migrations, models, and environment policy |
| AI providers | Provider interface/registry/manager, functional Ollama and Gemini implementations, streaming | Preserve and extend in Milestone 5 |
| Chat validation | Empty and whitespace-only messages are filtered before provider calls | Preserve; add endpoint regression coverage |
| File metadata | Initial stored-file, quota, document, and chunk models/repositories | Refactor into one coherent file/document model rather than duplicate it |
| Delivery assets | Backend/frontend Dockerfiles, Compose skeleton, Nginx configuration, GitHub Actions skeleton | Preserve intent; repair and make checks blocking |
| Tests | Three Gemini provider tests currently pass | Preserve; expand because coverage is currently very small |

### Reproduced blockers

| Blocker | Evidence | Impact |
|---|---|---|
| ORM mapping is invalid | `configure_mappers()` fails because `Document` references nonexistent `WorkspaceRecord` and `UserRecord` classes | Document/storage operations can fail at runtime |
| Foreign-key types disagree | Core user/workspace IDs are `String(36)` while document/storage foreign keys use `Integer` | PostgreSQL migration/table creation cannot be trusted |
| Alembic is nonfunctional | `alembic current` fails importing nonexistent `app.core.database.get_database_url` | No controlled schema lifecycle or rollback path |
| No migration history | There is no `backend/migrations/versions` baseline | Existing databases have no versioned upgrade path |
| Startup mutates schema | The lifespan always calls `Base.metadata.create_all()` | Production schema can drift outside migrations |
| PostgreSQL is not actually selected in Compose | Compose sets `POSTGRES_HOST` but does not set `DATABASE_URL`; application therefore falls back to SQLite | The declared production database is bypassed |
| Required driver missing from runtime requirements | `backend/requirements.txt` omits `asyncpg` | Container/CI PostgreSQL startup fails even with a correct URL |
| CI overstates protection | frontend test/security/lint failures are allowed or tests are missing | Regressions can merge while CI remains green |
| Domain module failures are swallowed | `_load_domain_modules()` logs exceptions and continues startup | Readiness can report healthy with core APIs absent |

## 3. Current architecture inventory

### Frontend

The frontend is a single React SPA. `App.tsx` protects the main layout and lazy-loads pages. API access is split between:

- `src/lib/api-client.ts`: authenticated requests and refresh handling;
- `src/lib/auth-api.ts`: authentication operations;
- `src/lib/api.ts`: feature endpoints, mostly unauthenticated `fetch` calls;
- direct `fetch` calls inside pages such as PDF Chat.

Chat, coding, research, and image histories are partly stored in `localStorage`. Many screens are functional prototypes against endpoints in the monolithic compatibility backend. The UI therefore looks complete but does not prove durable, tenant-scoped backend behavior.

### Backend

`backend/app/main.py` is the intended production entry point and currently performs four jobs: infrastructure startup, module registration, compatibility APIs, and several feature APIs. Domain packages exist for auth, workspace, chat, document, storage, settings, and AI. `backend/main.py`, `backend/services`, and `backend/legacy` are duplicate generations of implementation and should not receive new feature work.

The custom dependency container is serviceable for process-wide stateless services, but database-backed services should remain request-scoped through FastAPI dependencies. The in-process event bus is suitable for local events only; it cannot guarantee delivery across replicas.

### Existing API groups

- Modular: `/api/auth`, `/api/v1/workspaces`, `/api/v1/chat`, `/api/v1/documents`, `/api/v1/settings`, `/api/v1/storage`.
- Compatibility: `/api/chat`, `/api/models`, `/api/documents/*`, `/api/health`.
- Prototype feature routes: coding, research, agents, memory, automation, voice, images, video, plugins, team, marketplace, mobile, and enterprise.
- Health: `/health/live`, `/health/ready`.

The API surface lacks one versioning/auth/pagination/error policy. Compatibility endpoints should remain temporarily but delegate to modular services and be marked for measured deprecation.

### Persistence and storage

SQLite is the effective default everywhere. PostgreSQL configuration exists but is not wired end-to-end. Document embeddings are JSON text and similarity search is Python-side. Local file paths are stored directly and uploads use blocking filesystem operations inside async request handlers. There are overlapping `ProjectFile`, `StoredFile`, and `Document` concepts without a single metadata/storage ownership boundary.

### AI, RAG, memory, agents, tools, and workflows

- AI provider abstraction exists and Gemini/Ollama are usable.
- Automatic routing, fallback policy, retries, capability-based selection, usage persistence, and orchestration do not yet exist as a coherent runtime.
- Document extraction/chunk records exist, but vector search is not production RAG: no pgvector index, tenant-aware SQL retrieval, reranker, citation contract, or asynchronous ingestion pipeline.
- Memory, agents, workflows, marketplace/team/mobile/enterprise endpoints are primarily prototype persistence or in-memory behavior rather than production domain modules.
- Plugin management is an in-process registry with discovery explicitly stubbed; tool permissions and sandboxing are not implemented.
- Voice transcription is explicitly a sample response.

## 4. What should be preserved, replaced, and refactored

### Preserve

- React/TypeScript/Tailwind/Vite stack and current navigation while backend capabilities mature.
- FastAPI app factory and lifespan pattern.
- SQLAlchemy async repository/service approach.
- Auth hashing/JWT service as an incremental base.
- AI provider protocol, registry, manager, Gemini provider, Ollama provider, and streaming response compatibility.
- Existing public endpoint shapes where practical, via adapters.
- Local SQLite mode for lightweight development and unit tests.

### Replace

- `create_all()` as the production schema mechanism with Alembic migrations.
- Chroma/Python-side JSON-vector retrieval with PostgreSQL plus pgvector in Milestone 7.
- Direct local-path storage assumptions with an object-storage interface in Milestone 2.
- Process-memory state for durable user features with PostgreSQL repositories.
- Sample/stub responses with explicit capability-disabled errors until real integrations exist.
- Silent startup degradation with fail-fast checks for required modules and migrations.

### Refactor incrementally

- Normalize all identity and foreign-key columns to UUID-compatible strings first; changing every existing SQLite primary key to PostgreSQL-native UUID in one migration would add unnecessary conversion risk.
- Unify `ProjectFile`, `StoredFile`, and `Document` around one file metadata record plus optional document-processing state.
- Move compatibility endpoint logic out of `app/main.py` into adapter routers.
- Route all frontend feature calls through the authenticated API client.
- Add ownership/workspace authorization at service/repository boundaries, not only in UI routes.
- Separate long-running ingestion, research, and agent work from request processes once Redis/jobs arrive.

## 5. Production risk register

| Priority | Risk | Why it matters | Best implementation | Effort | Dependencies |
|---|---|---|---|---|---|
| P0 | Broken ORM and migrations | Data features cannot be safely deployed | Normalize model references/types, establish Alembic baseline, test SQLite and PostgreSQL | 3-5 days | Milestone 1 |
| P0 | Unauthenticated compatibility/feature routes | Cross-user data exposure and abuse | Require identity and workspace authorization; temporary adapters call secured services | 4-7 days | Milestones 1 and 4 |
| P0 | Local/in-memory feature state | Data disappears and cannot scale across replicas | PostgreSQL repositories and object storage | 1-3 weeks | Milestones 1-3 |
| P0 | File security/ownership gaps | Upload abuse, path exposure, tenant leakage | Object keys, MIME/signature checks, quotas, permission queries, signed downloads | 1-2 weeks | Milestones 2-4 |
| P0 | No reliable background execution | Large uploads and agents block requests and lose progress | Redis-backed jobs with idempotency, retries, status, and cancellation | 1-2 weeks | Milestone 13 |
| P1 | Fragmented APIs and duplicate implementations | Fixes diverge and clients behave inconsistently | Modular service ownership plus compatibility adapters | 1 week staged | Milestones 1-6 |
| P1 | Incomplete AI routing/orchestration | Provider choice is manual and failures are brittle | Capability metadata, policy router, fallback/retry budgets, central orchestrator | 2-3 weeks | Milestones 5-6 |
| P1 | Prototype RAG | Retrieval is slow, unscoped, and difficult to cite | pgvector, filtered retrieval, ingestion jobs, citation schema, evaluation set | 2-3 weeks | Milestones 1, 3, 7, 13 |
| P1 | Minimal observability | Failures, cost, latency, and model quality cannot be improved | Request IDs, structured traces, usage/run tables, metrics exporters | 1-2 weeks | Milestone 14 |
| P1 | Weak test gates | Broad regressions are likely during refactoring | Unit, API integration, PostgreSQL migration, storage, browser E2E; blocking CI | 2-3 weeks ongoing | Every milestone |
| P2 | Large page components and local state | UX code becomes difficult to test and optimize | Feature hooks/components and server-backed caches, introduced per screen | Ongoing | Backend APIs |
| P2 | Accessibility gaps | Keyboard/screen-reader users receive inconsistent behavior | Automated axe checks plus manual keyboard/focus review | 3-5 days | Stable components |

## 6. Milestone readiness and sequence

| Milestone | Current state | Exit condition before claiming complete |
|---|---|---|
| 1. PostgreSQL + migrations | **Blocked/broken** | Alembic baseline upgrades clean DBs on SQLite and PostgreSQL; startup does not create production schema; migration CI passes |
| 2. Object storage + file service | Partial local disk service | S3-compatible interface, local adapter, secure keys, checksums, streamed I/O, tests |
| 3. Persistent files/folders | Partial overlapping models | Durable folders/files, rename/move/search/soft delete, exact rename persistence integration test |
| 4. Authentication + RBAC | Partial auth, incomplete authorization | All private APIs require identity; workspace role matrix and tenant-isolation tests |
| 5. Provider abstraction | Strong partial | Configured model registry, capability metadata, retry/fallback/timeout policy, provider contract tests |
| 6. AI orchestrator | Not implemented as central runtime | Intent/context/tool plan execution with bounded, observable state machine |
| 7. RAG + pgvector | Prototype | Async ingestion, pgvector indexes, permission filters, citations, retrieval evaluation |
| 8. Persistent memory | Prototype | Explicit long-term records, scoped retrieval, inspect/delete controls, retention rules |
| 9. Agent runtime | Prototype endpoints | Persisted definitions/runs/steps, limits, permissions, cancellation, resumability |
| 10. Coding agent | Assistant screen only | Sandboxed repository tools, patch/test loop, approvals, artifacts |
| 11. Research agent | Prototype endpoint | Source collection, deduplication, claim citations, persisted report/run |
| 12. Tool/MCP | Registry skeleton | Typed tool protocol, grants, secret handling, timeouts, audit trail, MCP lifecycle |
| 13. Redis + jobs | Not implemented | Durable queue, worker, retries, idempotency, progress/cancel APIs |
| 14. Observability + usage | Minimal logs | Correlation IDs, model/tool/job metrics, usage records, admin queries |
| 15. Security | Partial | Threat model, upload/SSRF/tool controls, secret validation, rate limits, audit logs |
| 16. Testing + CI/CD | Minimal and non-blocking | Representative unit/integration/E2E/load tests; blocking lint, migration, security, and build gates |

## 7. Immediate implementation decision

The first implementation increment is Milestone 1 only:

1. repair ORM relationships and foreign-key type consistency without changing API shapes;
2. make PostgreSQL configuration explicit and validated;
3. repair Alembic and add a reviewed initial migration;
4. disable automatic schema creation outside local/test mode;
5. update Compose and runtime dependencies;
6. add migration/database tests and rerun backend/frontend verification.

Object storage, folders, RBAC, RAG, agents, Redis, and other milestones should not be mixed into this database change. They depend on a trustworthy schema baseline.
