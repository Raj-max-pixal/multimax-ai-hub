# Legacy Code Archive

## Purpose

This directory contains the **original legacy code** from before the Phase 0 modular migration. 
These files are preserved for reference only and are **NOT used** by the running application.

## Why Archived

The original monolithic `backend/main.py` and `backend/services/` were refactored into the modular 
`backend/app/` architecture during Phase 0. The legacy copies are kept here to:

1. Preserve original business logic for reference during future migrations
2. Serve as a fallback if bugs are found in the refactored implementation
3. Track the evolution of the codebase

## Legacy Files

| File | Original Purpose | Migrated To | Status |
|------|-----------------|-------------|--------|
| `main.py` | Single-file FastAPI app with all routes | `backend/app/main.py` + domain modules | ✅ Migrated |
| `services/__init__.py` | Services package init | `backend/app/` modules | ✅ Migrated |
| `services/rag_service.py` | RAG/embedding pipeline | Deferred to Phase 5 | ⏳ Deferred |
| `services/document_service.py` | Document processing | Deferred to Phase 5 | ⏳ Deferred |
| `services/embedding_service.py` | Embedding generation | Deferred to Phase 5 | ⏳ Deferred |
| `services/storage_service.py` | File storage | Deferred to Phase 5 | ⏳ Deferred |

## Note

**DO NOT MODIFY** files in this directory. They are read-only references.
If you need to restore any functionality, implement it in the appropriate 
`backend/app/` domain module instead.