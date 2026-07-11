"""
Application Factory for Multimax AI Hub.

Creates and configures the FastAPI application instance with all
domain modules, middleware, and infrastructure services.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
        self.database = get_database()


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

    # Start event bus
    await app_state.event_bus.start()

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


def _load_domain_modules(app: FastAPI, app_state: AppState) -> None:
    """Import and register all domain modules."""
    domain_module_packages = ["app.auth", "app.workspace"]

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
    # CORS
    origins = settings.CORS_ORIGINS
    if isinstance(origins, str):
        origins = [o.strip() for o in origins.split(",") if o.strip()]

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
            "modules": list(app_state.module_loader.get_all_modules().keys())
            if hasattr(app_state.module_loader, "_modules")
            else [],
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
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Setup all application layers
    _setup_middleware(app, settings)
    _setup_health_endpoints(app)
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