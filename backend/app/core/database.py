"""
Database Management.

Provides async SQLAlchemy engine, session factory, and base model.
Supports PostgreSQL via asyncpg driver for high-concurrency workloads.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
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
        """Create the database engine and session factory."""
        if self._initialized:
            return

        self._engine = create_async_engine(
            self._settings.database_url,
            echo=self._settings.APP_DEBUG,
            poolclass=NullPool,  # Disable pooling for serverless compatibility
            pool_pre_ping=True,
        )

        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        self._initialized = True
        logger.info(
            "Database engine initialized",
            extra={"host": self._settings.POSTGRES_HOST, "db": self._settings.POSTGRES_DB},
        )

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
        logger.info("All database tables created")

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