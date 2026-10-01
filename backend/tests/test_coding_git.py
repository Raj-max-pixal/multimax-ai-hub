from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.auth.dependencies import get_current_user_id
from app.coding.api import _authorized_project, router
from app.coding.git_service import (
    GitOperationError,
    GitService,
    _looks_like_secret,
    parse_porcelain_status,
    validate_branch_name,
    validate_repository_url,
)
from app.workspace.models import WorkspaceRole


def test_repository_url_is_canonical_and_provider_is_detected() -> None:
    url, provider = validate_repository_url("https://GitHub.com/Owner/Repo.git")
    assert url == "https://github.com/Owner/Repo.git"
    assert provider == "github"


@pytest.mark.parametrize("url", [
    "https://user:token@github.com/owner/repo.git",
    "https://github.com/owner/repo.git?token=private",
    "http://github.com/owner/repo.git",
])
def test_repository_url_rejects_embedded_credentials_and_unsafe_schemes(url: str) -> None:
    with pytest.raises(ValueError):
        validate_repository_url(url)


@pytest.mark.parametrize("branch", ["../main", "-option", "release..candidate", "main/", "main name"])
def test_branch_validation_rejects_unsafe_names(branch: str) -> None:
    with pytest.raises(ValueError):
        validate_branch_name(branch)


def test_porcelain_status_parser_categorizes_git_changes() -> None:
    states = parse_porcelain_status(" M src/changed.py\0?? notes.md\0A  staged.py\0 D removed.py\0")
    assert [(state.index_status, state.worktree_status, state.path) for state in states] == [
        (" ", "M", "src/changed.py"), ("?", "?", "notes.md"),
        ("A", " ", "staged.py"), (" ", "D", "removed.py"),
    ]


def test_non_git_project_returns_clean_not_connected_status(tmp_path: Path) -> None:
    status = GitService(tmp_path / "not-created").status()
    assert status["is_git_repository"] is False
    assert status["state"] == "not_connected"


def test_git_status_diff_and_commit_are_project_scoped(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    (root / "main.py").write_text("print('before')\n", encoding="utf-8")
    service = GitService(root)
    connected = service.connect("https://github.com/example/project.git", "main")
    assert connected["provider"] == "github"
    assert service.status()["untracked_files"] == ["main.py"]

    first_commit = service.commit("Add initial source", "user-id")
    assert first_commit["message"] == "Add initial source"
    (root / "main.py").write_text("print('after')\n", encoding="utf-8")
    (root / "new.py").write_text("print('new')\n", encoding="utf-8")
    status = service.status()
    assert status["state"] == "dirty"
    assert status["modified_files"] == ["main.py"]
    assert status["untracked_files"] == ["new.py"]
    diff = service.diff()["diff"]
    assert "print('after')" in diff and "print('new')" in diff


def test_commit_blocks_credential_files_and_tokens(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    service = GitService(root)
    service.connect("https://github.com/example/project.git", "main")
    (root / ".env").write_text("DATABASE_URL=private", encoding="utf-8")
    with pytest.raises(GitOperationError, match="sensitive files"):
        service.commit("Add configuration", "user-id")
    assert _looks_like_secret(("token=ghp_" + "A" * 30).encode())


@pytest.mark.asyncio
async def test_project_membership_is_required_for_git_operations() -> None:
    project = SimpleNamespace(id="project-id", workspace_id="workspace-id")
    session = AsyncMock()
    session.scalar.side_effect = [project, None]
    with pytest.raises(HTTPException) as error:
        await _authorized_project(session, project.id, "not-a-member")
    assert error.value.status_code == 404

    session.scalar.side_effect = [project, SimpleNamespace(role=WorkspaceRole.VIEWER)]
    with pytest.raises(HTTPException) as error:
        await _authorized_project(session, project.id, "viewer", write=True)
    assert error.value.status_code == 403


def test_git_routes_require_authenticated_project_identity() -> None:
    route_names = {route.endpoint.__name__ for route in router.routes}
    git_routes = [route for route in router.routes if "/git/" in route.path]
    assert {"connect_project_repository", "get_project_git_status", "get_project_git_diff",
            "suggest_project_commit_message", "create_project_commit"}.issubset(route_names)
    assert len(git_routes) == 5
    assert all(any(dependency.call is get_current_user_id for dependency in route.dependant.dependencies) for route in git_routes)
