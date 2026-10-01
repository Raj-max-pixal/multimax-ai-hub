from __future__ import annotations

import pytest
from fastapi import HTTPException
from types import SimpleNamespace

from app.auth.dependencies import get_current_user, get_current_user_id
from app.coding.api import redact_secrets, router as coding_router, validate_project_path
from app.workspace.api import get_workspace, get_workspace_service, router as workspace_router
from app.coding.api import _search_project_files


@pytest.mark.parametrize("path", ["../outside.py", "src/../../outside.py", "C:\\temp\\file.py", "/etc/passwd"])
def test_project_paths_reject_absolute_and_traversal(path: str) -> None:
    with pytest.raises(HTTPException) as error:
        validate_project_path(path)
    assert error.value.status_code == 400


@pytest.mark.parametrize("path", [".env", "config/.env.production", "keys/server.pem", "node_modules/pkg/index.js"])
def test_project_paths_exclude_secrets_and_generated_directories(path: str) -> None:
    with pytest.raises(HTTPException) as error:
        validate_project_path(path)
    assert error.value.status_code == 404


def test_project_path_is_normalized_and_secret_values_are_redacted() -> None:
    assert validate_project_path("src\\components\\App.tsx") == "src/components/App.tsx"
    assert redact_secrets('API_KEY="do-not-show"\nDATABASE_URL=postgres://private\nport = 3000') == 'API_KEY="[REDACTED]"\nDATABASE_URL=[REDACTED]\nport = 3000'


def test_redacts_well_known_tokens_and_private_keys() -> None:
    private_key_start = "-----BEGIN " + "PRIVATE KEY-----"
    content = "key=ghp_" + "A" * 30 + f"\n{private_key_start}\nsecret material\n-----END PRIVATE KEY-----"
    redacted = redact_secrets(content)
    assert "ghp_" not in redacted
    assert "secret material" not in redacted


def test_repository_search_returns_relevant_redacted_snippets_and_skips_unsafe_files(tmp_path, monkeypatch) -> None:
    (tmp_path / "auth.py").write_text('def refresh_session():\n    access_token = "sensitive-value"\n', encoding="utf-8")
    (tmp_path / ".env").write_text("refresh session secrets\n", encoding="utf-8")
    monkeypatch.setattr("app.coding.api._file_path", lambda project_id, path: tmp_path / path)
    records = [
        SimpleNamespace(path="auth.py", size_bytes=72),
        SimpleNamespace(path=".env", size_bytes=24),
        SimpleNamespace(path="../outside.py", size_bytes=10),
    ]
    results = _search_project_files(records, "project-id", "refresh_session")
    assert len(results) == 1
    assert results[0]["path"] == "auth.py"
    assert results[0]["line"] == 1
    assert "sensitive-value" not in results[0]["snippet"]


def test_coding_file_routes_require_authenticated_identity() -> None:
    assert coding_router.routes
    assert all(any(dependency.call in {get_current_user_id, get_current_user} for dependency in route.dependant.dependencies) for route in coding_router.routes)


def test_workspace_detail_uses_member_scoped_lookup_and_authenticated_user() -> None:
    detail_route = next(route for route in workspace_router.routes if route.endpoint is get_workspace)
    assert any(dependency.call is get_current_user_id for dependency in detail_route.dependant.dependencies)
    assert any(dependency.call is get_workspace_service for dependency in detail_route.dependant.dependencies)
