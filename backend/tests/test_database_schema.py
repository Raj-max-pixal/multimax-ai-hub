from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.orm import configure_mappers

from app.core.config import Settings, get_settings
from app.core.database import Base, DatabaseManager

# Register the complete model graph for mapper and metadata assertions.
import app.auth.models  # noqa: F401, E402
import app.chat.models  # noqa: F401, E402
import app.document.models  # noqa: F401, E402
import app.settings.models  # noqa: F401, E402
import app.storage.models  # noqa: F401, E402
import app.workspace.models  # noqa: F401, E402


def test_model_graph_and_foreign_key_types_are_consistent() -> None:
    configure_mappers()

    assert len(Base.metadata.tables) == 17
    for table in Base.metadata.tables.values():
        for foreign_key in table.foreign_keys:
            local_type = foreign_key.parent.type
            remote_type = foreign_key.column.type
            assert local_type._type_affinity is remote_type._type_affinity, (
                f"{table.name}.{foreign_key.parent.name} has type {local_type}, "
                f"but references {foreign_key.target_fullname} with type {remote_type}"
            )


def test_database_url_normalization_and_auto_create_policy() -> None:
    postgres = Settings(
        _env_file=None,
        DATABASE_URL="postgresql://user:password@db:5432/multimax",
        APP_ENV="production",
    )
    assert postgres.database_url.startswith("postgresql+asyncpg://")
    assert postgres.database_auto_create is False

    sqlite = Settings(
        _env_file=None,
        DATABASE_URL="sqlite:///./data/test.db",
        APP_ENV="test",
    )
    assert sqlite.database_url.startswith("sqlite+aiosqlite://")
    assert sqlite.database_auto_create is True


def test_initial_migration_round_trip(tmp_path: Path, monkeypatch) -> None:
    database_path = tmp_path / "migration.db"
    database_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("APP_ENV", "test")
    get_settings.cache_clear()

    backend_root = Path(__file__).resolve().parents[1]
    config = Config(str(backend_root / "migrations" / "alembic.ini"))

    try:
        command.upgrade(config, "head")
        with sqlite3.connect(database_path) as connection:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
        assert "alembic_version" in tables
        assert set(Base.metadata.tables).issubset(tables)

        command.downgrade(config, "base")
        command.upgrade(config, "head")
    finally:
        get_settings.cache_clear()


def test_legacy_sqlite_profile_repair_preserves_login(tmp_path, monkeypatch):
    from app.auth.service import AuthService, _hash_password

    database_path = tmp_path / "legacy.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{database_path.as_posix()}")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_DEBUG", "false")
    get_settings.cache_clear()
    config = Config(str(Path(__file__).resolve().parents[1] / "migrations" / "alembic.ini"))
    try:
        command.upgrade(config, "3ff0865da455")
        with sqlite3.connect(database_path) as connection:
            connection.execute("DROP TABLE alembic_version")
            connection.execute(
                "INSERT INTO users (id, email, username, hashed_password, role, is_active) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                ("legacy-user", "legacy@example.com", "legacy", _hash_password("Test-password-123!"), "USER", 1),
            )
        manager = DatabaseManager(get_settings())
        monkeypatch.setattr("app.auth.service.get_database", lambda: manager)

        async def verify():
            await manager.initialize()
            try:
                await manager.create_all()
                await manager.create_all()  # Repair must be idempotent.
                result = await AuthService().login("legacy", "Test-password-123!")
                assert result["user"]["id"] == "legacy-user"
                assert result["user"]["bio"] == ""
                assert result["access_token"]
                import pytest
                with pytest.raises(ValueError):
                    await AuthService().login("legacy", "wrong-password")
            finally:
                await manager.close()

        asyncio.run(verify())
    finally:
        get_settings.cache_clear()
