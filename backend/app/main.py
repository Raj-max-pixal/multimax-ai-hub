"""
Application Factory.
============================================================

Creates and configures the FastAPI application for Multimax AI Hub.
Handles lifespan events (startup/shutdown), dependency injection,
middleware, exception handlers, and module registration.

Usage:
    uvicorn app.main:create_app --factory --port 8000
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import Settings, get_settings
from app.core.container import Container, get_container
from app.core.database import DatabaseManager, init_database, get_database
from app.core.events import EventBus, create_event_bus
from app.core.exceptions import MultimaxError
from app.core.logger import get_logger
from app.core.module_loader import ModuleLoader

logger = get_logger("app.main")


# --------------------------------------------------------------------------- #
# Application State (accessible via app.state or request.app.state)
# --------------------------------------------------------------------------- #

class AppState:
    """Holds references to core services for the app lifetime."""

    def __init__(self) -> None:
        self.settings: Settings | None = None
        self.container: Container | None = None
        self.database: DatabaseManager | None = None
        self.event_bus: EventBus | None = None
        self.module_loader: ModuleLoader | None = None


# --------------------------------------------------------------------------- #
# Lifecycle Manager
# --------------------------------------------------------------------------- #

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler (startup → serve → shutdown).

    Startup sequence:
        1. Load settings
        2. Initialize the DI container
        3. Initialize the database engine
        4. Create & start the event bus
        5. Create tables (dev-only, safe to run repeatedly)
        6. Discover & load domain modules
        7. Set up app state references
    """
    # --- Startup ---
    logger.info("=" * 60)
    logger.info("  Multimax AI Hub – Starting up")
    logger.info("=" * 60)

    settings = get_settings()
    container = get_container()
    state = AppState()

    try:
        # Database – gracefully handle failure so app can serve health checks
        database = init_database(settings)
        try:
            await database.initialize()
            logger.info("Database engine initialized")
        except Exception as db_err:
            logger.warning(f"Database initialization skipped: {db_err}. App running in degraded mode.")
            database = None  # Allow the app to start without database

        # Event bus
        event_bus = create_event_bus(settings)
        await event_bus.start()
        logger.info(f"Event bus started (backend={settings.EVENT_BUS_BACKEND})")

        # Module loader – discover and load all domain modules
        module_loader = ModuleLoader()
        discovered = module_loader.discover("app")
        logger.info(f"Module discovery complete: {len(discovered)} module(s) found")

        # Load discovered modules (this registers all models with Base.metadata)
        results = module_loader.load_all(app, container)
        loaded = [name for name, ok in results.items() if ok]
        failed = [name for name, ok in results.items() if not ok]
        if loaded:
            logger.info(f"Modules loaded: {', '.join(loaded)}")
        if failed:
            logger.warning(f"Modules failed to load: {', '.join(failed)}")

        # Create tables in dev AFTER module discovery so all models are registered
        if settings.APP_ENV in ("development", "test") and database is not None:
            try:
                await database.create_all()
                logger.info("Database tables created/verified")
            except Exception as db_err:
                logger.warning(f"Could not create tables: {db_err} (database may not be available yet)")

        # Store state on the app
        state.settings = settings
        state.container = container
        state.database = database
        state.event_bus = event_bus
        state.module_loader = module_loader
        app.state.multimax = state

        logger.info("Multimax AI Hub startup complete")
        yield  # <-- Application serves requests here

    except Exception as exc:
        logger.critical(f"Startup failed: {exc}", exc_info=True)
        # Still yield so health checks can respond even on partial startup
        app.state.multimax = state
        yield

    finally:
        # --- Shutdown ---
        logger.info("Shutting down Multimax AI Hub…")

        if state.event_bus:
            await state.event_bus.stop()
            logger.info("Event bus stopped")

        if state.database:
            await state.database.close()
            logger.info("Database connections closed")

        logger.info("Shutdown complete. Goodbye.")


# --------------------------------------------------------------------------- #
# Health Endpoints
# --------------------------------------------------------------------------- #

async def health_live() -> Dict[str, Any]:
    """Liveness probe – lightweight check that the process is alive."""
    return {
        "status": "ok",
        "app": "Multimax AI Hub",
        "version": get_settings().APP_VERSION,
    }


async def health_ready(request: Request) -> Dict[str, Any]:
    """Readiness probe – verifies core services are operational."""
    try:
        state: AppState = request.app.state.multimax
        checks = {
            "settings": state.settings is not None,
            "container": state.container is not None,
            "database": state.database is not None,
            "event_bus": state.event_bus is not None,
        }
        all_ok = all(checks.values())
        return {
            "status": "ok" if all_ok else "degraded",
            "checks": checks,
        }
    except AttributeError:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "message": "App state not initialized"},
        )


# --------------------------------------------------------------------------- #
# Exception Handlers
# --------------------------------------------------------------------------- #

async def multimax_error_handler(request: Request, exc: MultimaxError) -> JSONResponse:
    """Handle known application exceptions with appropriate status codes."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.detail,
            "context": exc.context,
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred."},
    )


# --------------------------------------------------------------------------- #
# Factory
# --------------------------------------------------------------------------- #

def create_app() -> FastAPI:
    """Application factory – creates and returns a configured FastAPI instance.

    This is the entry point called by uvicorn:
        uvicorn app.main:create_app --factory
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Multimax AI Hub – AI Operating System Backend",
        lifespan=lifespan,
        docs_url="/docs" if settings.APP_DEBUG else None,
        redoc_url="/redoc" if settings.APP_DEBUG else None,
    )

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Health routes ---
    app.add_api_route("/health/live", health_live, tags=["health"])
    app.add_api_route("/health/ready", health_ready, tags=["health"])
    app.add_api_route("/health", health_live, tags=["health"])  # alias

    # --- Exception handlers ---
    app.add_exception_handler(MultimaxError, multimax_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info(
        "FastAPI application created",
        extra={
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "env": settings.APP_ENV,
        },
    )

    return app