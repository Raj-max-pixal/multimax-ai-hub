"""
Database Management.

Provides async SQLAlchemy engine, session factory, and base model.
Supports both SQLite (local/dev) and PostgreSQL (production) backends.

SQLite is the DEFAULT for zero-budget local development.
PostgreSQL via asyncpg is used when DATABASE_URL is explicitly set.

Database URL formats:
  - SQLite (default): sqlite+aiosqlite:///./data/multimax.db
  - PostgreSQL:       postgresql+asyncpg://user:pass@host:5432/multimax
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, AsyncIterator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import Settings
from app.core.logger import get_logger

logger = get_logger("app.core.database")


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


class DatabaseManager:
    """Manages database engine and session lifecycle.

    Usage:
        db = DatabaseManager(settings)
        await db.initialize()
        async with db.session() as session:
            result = await session.execute(...)
        await db.close()
    """

    def __init__(self, settings: Settings):
        self._settings = settings
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Create the database engine and session factory.

        Automatically detects the backend from the database_url setting.
        Falls back to SQLite if no PostgreSQL connection is configured.
        """
        if self._initialized:
            return

        db_url = self._settings.database_url

        # Auto-detect whether we're using PostgreSQL or SQLite
        is_postgres = db_url.startswith("postgresql")

        # For SQLite, ensure the parent directory exists
        if not is_postgres and db_url.startswith("sqlite"):
            # Extract path from sqlite+aiosqlite:///./path
            db_path_str = db_url.replace("sqlite+aiosqlite:///", "")
            db_path = Path(db_path_str)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"SQLite database path: {db_path.absolute()}")

        try:
            self._engine = create_async_engine(
                db_url,
                echo=self._settings.APP_DEBUG,
                poolclass=NullPool,
                pool_pre_ping=is_postgres,
            )

            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )

            self._initialized = True

            # Log connection info (sanitized for security)
            if is_postgres:
                db_host = self._settings.POSTGRES_HOST or "localhost"
                db_name = self._settings.POSTGRES_DB or "multimax"
                logger.info(
                    "PostgreSQL engine initialized",
                    extra={"host": db_host, "db": db_name},
                )
            else:
                logger.info("SQLite engine initialized (local development mode)")

        except ImportError as e:
            # Handle missing driver gracefully
            missing_driver = str(e).split("'")[1] if "'" in str(e) else "unknown"
            alternative = "aiosqlite" if "asyncpg" in str(e) else "asyncpg"
            logger.error(
                f"Database driver '{missing_driver}' not installed. "
                f"Install with: pip install {alternative}"
            )
            raise

        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise

    async def close(self) -> None:
        """Dispose of the database engine."""
        if self._engine:
            await self._engine.dispose()
            self._initialized = False
            logger.info("Database engine disposed")

    async def create_all(self) -> None:
        """Create all tables defined in models (useful for development)."""
        if not self._engine:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("All database tables created/verified")

    async def drop_all(self) -> None:
        """Drop all tables (useful for testing)."""
        if not self._engine:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("All database tables dropped")

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Provide an async context manager for database sessions.

        Usage:
            async with db.session() as session:
                user = await session.get(User, user_id)
        """
        if not self._session_factory:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides a database session.

    Usage in FastAPI:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db_session)):
            ...
    """
    if _db_manager is None:
        raise RuntimeError("Database not initialized")

    async with _db_manager.session() as session:
        yield session


def init_database(settings: Settings) -> DatabaseManager:
    """Initialize the global database manager.

    Args:
        settings: Application settings.

    Returns:
        Configured DatabaseManager instance.
    """
    global _db_manager
    _db_manager = DatabaseManager(settings)
    return _db_manager


def get_database() -> DatabaseManager:
    """Get the global database manager instance."""
    if _db_manager is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _db_manager