from __future__ import annotations

import sqlite3
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.orm import configure_mappers

from app.core.config import Settings, get_settings
from app.core.database import Base

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
