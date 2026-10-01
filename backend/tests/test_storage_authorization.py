from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.dialects import sqlite

from app.storage.dependencies import get_current_user_id, get_optional_user_id
from app.storage.exceptions import FileNotFoundError_
from app.storage.repositories import StoredFileRepository
from app.storage.api import router

# Load the model graph before compiling ORM expressions with relationship mappings.
import app.auth.models  # noqa: F401, E402
import app.chat.models  # noqa: F401, E402
import app.document.models  # noqa: F401, E402
import app.settings.models  # noqa: F401, E402
import app.workspace.models  # noqa: F401, E402


@pytest.mark.asyncio
async def test_storage_user_id_uses_authenticated_user() -> None:
    assert await get_current_user_id(current_user={"id": "authenticated-user"}) == "authenticated-user"


@pytest.mark.asyncio
async def test_file_lookup_is_scoped_to_owner_and_hides_foreign_ids() -> None:
    session = AsyncMock()
    session.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: None)
    repository = StoredFileRepository(session)

    with pytest.raises(FileNotFoundError_):
        await repository.get_by_id_for_user_or_raise("other-users-file", "authenticated-user")

    statement = session.execute.await_args.args[0]
    compiled = statement.compile(dialect=sqlite.dialect())
    assert "stored_files.user_id" in str(compiled)
    assert set(compiled.params.values()) == {"other-users-file", "authenticated-user"}


@pytest.mark.asyncio
async def test_anonymous_download_lookup_only_allows_explicitly_public_files() -> None:
    session = AsyncMock()
    session.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: None)
    repository = StoredFileRepository(session)

    with pytest.raises(FileNotFoundError_):
        await repository.get_downloadable_file_or_raise("private-file", None)

    statement = session.execute.await_args.args[0]
    compiled = statement.compile(dialect=sqlite.dialect())
    assert "stored_files.is_public IS 1" in str(compiled)
    assert "private-file" in compiled.params.values()


def test_file_not_found_is_a_not_found_error_without_owner_details() -> None:
    error = FileNotFoundError_("other-users-file")

    assert error.code == "NOT_FOUND"
    assert error.status_code == 404
    assert error.details == {}
    assert error.message == "File not found"


@pytest.mark.parametrize(
    ("endpoint_name", "required_dependency"),
    [
        ("get_file", get_current_user_id),
        ("download_file", get_optional_user_id),
        ("delete_file", get_current_user_id),
    ],
)
def test_file_id_routes_use_the_correct_access_dependency(
    endpoint_name: str,
    required_dependency,
) -> None:
    route = next(route for route in router.routes if route.endpoint.__name__ == endpoint_name)

    assert any(
        dependency.call is required_dependency
        for dependency in route.dependant.dependencies
    )
