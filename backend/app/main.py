"""
Application Factory for Multimax AI Hub.

Creates and configures the FastAPI application instance with all
domain modules, middleware, and infrastructure services.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from app.core.config import Settings, get_settings
from app.core.container import Container, get_container
from app.core.database import get_database
from app.core.events import create_event_bus
from app.core.exceptions import MultimaxError
from app.core.logger import get_logger, setup_logging
from app.core.module_loader import ModuleLoader

logger = get_logger("app.main")


# --------------------------------------------------------------------------- #
# Application State
# --------------------------------------------------------------------------- #


class AppState:
    """Holds global application state."""

    def __init__(self) -> None:
        self.settings: Settings = get_settings()
        self.container: Container = get_container()
        self.module_loader: ModuleLoader = ModuleLoader()
        self.event_bus = create_event_bus(self.settings)
        # Initialize database (must call init_database before get_database)
        from app.core.database import init_database
        self.database = init_database(self.settings)
        self.ai_manager: Optional[Any] = None


# --------------------------------------------------------------------------- #
# Lifespan Manager
# --------------------------------------------------------------------------- #


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown lifecycle."""
    # --- Startup ---
    settings = get_settings()
    setup_logging(settings)

    logger.info(f"Multimax AI Hub starting — environment: {settings.ENVIRONMENT}")

    # Initialize app state
    app_state = AppState()
    app.state.multimax = app_state

    # Initialize database
    await app_state.database.initialize()

    # Create all tables (development auto-migration)
    await app_state.database.create_all()

    # Start event bus
    await app_state.event_bus.start()

    # Initialize AI Manager
    app_state.ai_manager = _init_ai_manager(app_state)

    # Load domain modules
    _load_domain_modules(app, app_state)

    # Warn if default secret keys are used in production
    _warn_default_secrets(settings)

    logger.info("Startup complete")

    yield  # Application runs here

    # --- Shutdown ---
    logger.info("Shutting down...")
    await app_state.event_bus.stop()
    await app_state.database.close()
    logger.info("Shutdown complete")


def _init_ai_manager(app_state: AppState) -> Any:
    """Initialize the AI Manager with configured providers."""
    from app.ai.manager import AIManager
    from app.ai.providers.ollama import OllamaProvider
    from app.ai.providers.openai import OpenAIProvider
    from app.ai.provider_registry import ProviderRegistry

    registry = ProviderRegistry()

    # Register Ollama provider (always available)
    ollama_config = {
        "name": "ollama",
        "display_name": "Ollama",
        "base_url": app_state.settings.ollama_url,
        "default_model": app_state.settings.OLLAMA_DEFAULT_MODEL,
        "models": ["llama3.1", "mistral", "codellama", "phi3"],
        "timeout": 120,
    }

    from app.ai.base import ProviderConfig as ProviderConfigCls

    provider = OllamaProvider(ProviderConfigCls(**ollama_config))
    registry.register(provider)

    # Future: conditionally register OpenAI, Gemini, Qwen here

    return AIManager(registry=registry)


def _load_domain_modules(app: FastAPI, app_state: AppState) -> None:
    """Import and register all domain modules."""
    domain_module_packages = ["app.auth", "app.workspace", "app.chat", "app.document", "app.settings"]

    for package_name in domain_module_packages:
        try:
            import importlib
            module = importlib.import_module(package_name)

            # Each module exposes module_info and register()
            info = getattr(module, "module_info", None)
            if info:
                logger.info(f"Discovered module: {info.name} ({package_name})")

            register_func = getattr(module, "register", None)
            if register_func:
                register_func(app, app_state.container)
                logger.info(f"Module '{package_name}' loaded successfully")
            else:
                logger.warning(f"Module '{package_name}' has no register() function")
        except Exception as e:
            logger.error(f"Failed to load module '{package_name}': {e}", exc_info=True)


def _warn_default_secrets(settings: Settings) -> None:
    """Warn on startup if default secrets are being used."""
    defaults = {
        "APP_SECRET_KEY": "change-me-to-a-random-secret-key",
        "AUTH_SECRET_KEY": "change-me-to-another-random-secret",
    }
    for name, default in defaults.items():
        current = getattr(settings, name, None)
        if current == default:
            logger.warning(
                f"SECURITY: {name} is set to default value. "
                "Generate a random secret for production."
            )


# --------------------------------------------------------------------------- #
# Middleware
# --------------------------------------------------------------------------- #


def _setup_middleware(app: FastAPI, settings: Settings) -> None:
    """Configure application middleware."""
    # CORS — use the property which returns List[str]
    origins = settings.cors_origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next: Any) -> Any:
        logger.debug(f"{request.method} {request.url.path}")
        response = await call_next(request)
        logger.debug(f"{request.method} {request.url.path} → {response.status_code}")
        return response


# --------------------------------------------------------------------------- #
# Legacy-Compatible API Endpoints
# --------------------------------------------------------------------------- #


def _setup_legacy_endpoints(app: FastAPI) -> None:
    """Add backward-compatible endpoints matching the legacy backend/main.py API."""

    @app.get("/", tags=["legacy"])
    async def root():
        """Root endpoint — API information."""
        return {
            "message": "Multimax AI Hub API",
            "version": "0.4.0",
            "architecture": "modular",
            "status": "running",
        }

    @app.get("/api/models", tags=["legacy"])
    async def get_models():
        """List available models via AIManager (legacy-compatible response)."""
        app_state: AppState = getattr(app.state, "multimax", None)
        if app_state and app_state.ai_manager:
            try:
                models = await app_state.ai_manager.list_models()
                model_list = [
                    {"name": f"{m.name}:latest" if ":" not in m.name else m.name}
                    for m in models
                ]
                return {"models": model_list}
            except Exception as e:
                logger.warning(f"Failed to list models via AIManager: {e}")

        # Fallback default models
        return {
            "models": [
                {"name": "phi3:latest"},
                {"name": "llama3:latest"},
                {"name": "qwen3:4b"},
            ]
        }

    @app.post("/api/chat", tags=["legacy"])
    async def chat(request: Request):
        """Legacy-compatible chat endpoint — proxies to AIManager."""
        body = await request.json()
        model = body.get("model", "llama3.1")
        messages = body.get("messages", [])
        stream = body.get("stream", True)

        if not messages:
            raise HTTPException(status_code=422, detail="messages field is required")

        app_state: AppState = getattr(app.state, "multimax", None)

        if app_state and app_state.ai_manager:
            try:
                from app.ai.base import GenerationRequest

                gen_request = GenerationRequest(
                    model=model,
                    messages=[{"role": m["role"], "content": m["content"]} for m in messages],
                )

                if stream:
                    async def stream_response():
                        async for token in app_state.ai_manager.stream(gen_request):
                            yield token

                    return StreamingResponse(stream_response(), media_type="application/json")
                else:
                    response = await app_state.ai_manager.generate(gen_request)
                    return JSONResponse(content={"message": {"content": response.content}})

            except Exception as e:
                logger.error(f"AI Manager chat error: {e}")
                # Fall through to direct Ollama call

        # Fallback: direct Ollama call
        ollama_url = getattr(get_settings(), "ollama_url", "http://localhost:11434")
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                if stream:
                    async def proxy_stream():
                        async with client.stream(
                            "POST",
                            f"{ollama_url}/api/chat",
                            json={"model": model, "messages": messages, "stream": True},
                        ) as response:
                            response.raise_for_status()
                            async for chunk in response.aiter_bytes():
                                yield chunk

                    return StreamingResponse(proxy_stream(), media_type="application/json")
                else:
                    response = await client.post(
                        f"{ollama_url}/api/chat",
                        json={"model": model, "messages": messages, "stream": False},
                    )
                    response.raise_for_status()
                    return JSONResponse(content=response.json())
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Chat failed: {e}")

    @app.post("/api/documents/upload", tags=["legacy"])
    async def upload_documents(files: List[UploadFile] = File(...)):
        """Legacy-compatible document upload — redirects to v1."""
        # Forward to the v1 document API
        from app.document.api import router as document_router

        uploaded_docs = []
        for file in files:
            # Use the document service directly
            from app.document.service import DocumentService
            from app.document.repositories import DocumentRepository, StorageRepository, VectorRepository
            from app.core.database import get_database

            db = get_database()
            doc_repo = DocumentRepository(db)
            storage_repo = StorageRepository()
            vector_repo = VectorRepository()
            doc_service = DocumentService(doc_repo, storage_repo, vector_repo)

            try:
                doc = await doc_service.upload_document(file)
                uploaded_docs.append({
                    "id": doc.id,
                    "filename": doc.filename,
                    "file_type": doc.file_type,
                    "file_size": doc.file_size,
                    "chunk_count": doc.chunk_count,
                    "status": "processed",
                })
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to process {file.filename}: {e}")

        return {"documents": uploaded_docs, "message": "Documents uploaded and processed successfully"}

    @app.get("/api/documents", tags=["legacy"])
    async def get_documents_legacy():
        """Legacy-compatible document listing."""
        from app.document.service import DocumentService
        from app.document.repositories import DocumentRepository, StorageRepository, VectorRepository
        from app.core.database import get_database

        db = get_database()
        doc_repo = DocumentRepository(db)
        storage_repo = StorageRepository()
        vector_repo = VectorRepository()
        doc_service = DocumentService(doc_repo, storage_repo, vector_repo)

        docs = await doc_service.list_documents()
        return {"documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "file_type": d.file_type,
                "file_size": d.file_size,
                "chunk_count": d.chunk_count,
                "status": d.status,
            }
            for d in docs
        ]}

    @app.get("/api/documents/{document_id}", tags=["legacy"])
    async def get_document_legacy(document_id: str):
        """Legacy-compatible single document retrieval."""
        from app.document.service import DocumentService
        from app.document.repositories import DocumentRepository, StorageRepository, VectorRepository
        from app.core.database import get_database

        db = get_database()
        doc_repo = DocumentRepository(db)
        storage_repo = StorageRepository()
        vector_repo = VectorRepository()
        doc_service = DocumentService(doc_repo, storage_repo, vector_repo)

        doc = await doc_service.get_document(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return {
            "id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "chunk_count": doc.chunk_count,
            "status": doc.status,
        }

    @app.delete("/api/documents/{document_id}", tags=["legacy"])
    async def delete_document_legacy(document_id: str):
        """Legacy-compatible document deletion."""
        from app.document.service import DocumentService
        from app.document.repositories import DocumentRepository, StorageRepository, VectorRepository
        from app.core.database import get_database

        db = get_database()
        doc_repo = DocumentRepository(db)
        storage_repo = StorageRepository()
        vector_repo = VectorRepository()
        doc_service = DocumentService(doc_repo, storage_repo, vector_repo)

        deleted = await doc_service.delete_document(document_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": "Document deleted successfully"}

    @app.post("/api/documents/chat", tags=["legacy"])
    async def chat_with_documents_legacy(request: Request):
        """Legacy-compatible document chat — proxies to RAG service."""
        body = await request.json()
        query = body.get("query", "")
        document_ids = body.get("document_ids", [])
        model = body.get("model", "phi3:latest")

        if not query or not document_ids:
            raise HTTPException(status_code=422, detail="query and document_ids are required")

        from app.document.service import DocumentService
        from app.document.repositories import DocumentRepository, StorageRepository, VectorRepository
        from app.core.database import get_database

        db = get_database()
        doc_repo = DocumentRepository(db)
        storage_repo = StorageRepository()
        vector_repo = VectorRepository()
        doc_service = DocumentService(doc_repo, storage_repo, vector_repo)

        async def stream_response():
            async for chunk in doc_service.chat_with_documents(query, document_ids, model):
                yield chunk

        return StreamingResponse(stream_response(), media_type="application/json")

    @app.post("/api/transcribe", tags=["legacy"])
    async def transcribe_audio(file: UploadFile = File(...)):
        """Transcribe audio file (stub — Whisper integration placeholder)."""
        logger.info(f"Transcription requested for: {file.filename}")
        return {
            "transcript": "This is a sample transcript. Whisper integration will be added in the backend."
        }

    @app.get("/api/health", tags=["legacy"])
    async def health_legacy():
        """Legacy-compatible health check."""
        app_state: AppState = getattr(app.state, "multimax", None)
        ollama_status = "disconnected"
        if app_state and app_state.ai_manager:
            try:
                health = await app_state.ai_manager.health_check("ollama")
                ollama_status = "connected" if health.available else "disconnected"
            except Exception:
                pass
        return {"status": "healthy", "ollama": ollama_status}


# --------------------------------------------------------------------------- #
# Health Endpoints
# --------------------------------------------------------------------------- #


def _setup_health_endpoints(app: FastAPI) -> None:
    """Add health check endpoints."""

    @app.get("/health/live", tags=["health"])
    async def liveness():
        """Liveness probe — always returns 200 if the app is running."""
        return {"status": "alive", "service": "multimax-ai-hub"}

    @app.get("/health/ready", tags=["health"])
    async def readiness():
        """Readiness probe — returns 503 if the app hasn't initialized."""
        app_state: AppState = getattr(app.state, "multimax", None)
        if app_state is None:
            return JSONResponse(
                status_code=503,
                content={"status": "unavailable", "reason": "Application not initialized"},
            )

        # Check database connectivity
        try:
            await app_state.database.ping()
            db_ok = True
        except Exception as e:
            logger.warning(f"Database ping failed: {e}")
            db_ok = False

        if not db_ok:
            return JSONResponse(
                status_code=503,
                content={"status": "unavailable", "reason": "Database not reachable"},
            )

        return {
            "status": "ready",
            "modules": list(app_state.module_loader._modules.keys()),
        }


# --------------------------------------------------------------------------- #
# Exception Handlers
# --------------------------------------------------------------------------- #


def _setup_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers on the app instance."""

    @app.exception_handler(MultimaxError)
    async def multimax_error_handler(request: Request, exc: MultimaxError) -> JSONResponse:
        """Handle all MultimaxError exceptions with consistent JSON format."""
        status_map: Dict[str, int] = {
            "VALIDATION_ERROR": 422,
            "NOT_FOUND": 404,
            "AUTHENTICATION_ERROR": 401,
            "AUTHORIZATION_ERROR": 403,
            "DUPLICATE_ERROR": 409,
            "RATE_LIMIT_ERROR": 429,
            "CONFIGURATION_ERROR": 500,
            "EXTERNAL_SERVICE_ERROR": 502,
            "INTERNAL_ERROR": 500,
        }
        status_code = status_map.get(exc.code, 500)

        content = {
            "error": exc.code,
            "message": exc.message,
            "context": exc.details,
        }
        return JSONResponse(status_code=status_code, content=content)

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all for unhandled exceptions."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "context": {},
            },
        )


# --------------------------------------------------------------------------- #
# Application Factory
# --------------------------------------------------------------------------- #


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Fully configured FastAPI instance ready for uvicorn.
    """
    settings = get_settings()

    app = FastAPI(
        title="Multimax AI Hub",
        description="The AI Operating System — unified platform for chat, code, research, and automation",
        version="0.4.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Setup all application layers
    _setup_middleware(app, settings)
    _setup_health_endpoints(app)
    _setup_legacy_endpoints(app)
    _setup_exception_handlers(app)

    return app


# --------------------------------------------------------------------------- #
# Direct execution
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:create_app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        factory=True,
        log_level=settings.LOG_LEVEL.lower(),
    )