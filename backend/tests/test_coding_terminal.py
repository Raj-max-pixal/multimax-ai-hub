from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.auth.dependencies import get_current_user_id
from app.coding.api import _authorized_project, router
from app.coding.terminal_service import (
    MAX_OUTPUT_BYTES,
    ProcessResult,
    SandboxUnavailable,
    TerminalPolicyError,
    TerminalService,
    detect_test_command,
    parse_command_line,
    validate_argv,
)
from app.workspace.models import WorkspaceRole


class FakeIsolatedExecutor:
    available = True

    def __init__(self, result: ProcessResult | None = None, delay: float = 0):
        self.result = result or ProcessResult("ok", "", 0, 2)
        self.delay = delay
        self.argv: list[str] | None = None
        self.cancelled = False

    async def run(self, argv: list[str], project_root: Path, timeout_seconds: int) -> ProcessResult:
        self.argv = argv
        try:
            if self.delay:
                await asyncio.sleep(self.delay)
            return self.result
        except asyncio.CancelledError:
            self.cancelled = True
            raise


def test_command_allowlist_and_safe_parsing() -> None:
    assert parse_command_line("npm test") == ["npm", "test"]
    assert validate_argv(["python", "-m", "pytest", "-q"])[0] == "python"
    with pytest.raises(TerminalPolicyError, match="allowlisted"):
        validate_argv(["powershell", "-Command", "whoami"])


@pytest.mark.parametrize("command", [
    "npm test; whoami", "npm test && whoami", "npm test | more", "python -c print(1)",
    "node --eval alert(1)", "npm test %PATH%", "git push origin main", "pip install requests",
    "python -m pip install requests", "npx cowsay hi",
])
def test_shell_injection_and_unsafe_commands_are_rejected(command: str) -> None:
    with pytest.raises(TerminalPolicyError):
        parse_command_line(command)


@pytest.mark.parametrize("argv", [
    ["npm", "test", "../../outside"], ["pytest", "--confcutdir=../../outside"],
    ["node", "C:\\Windows\\system.ini"], ["python", ".env"],
    ["npm", "test", "config/.env.production"], ["git", "diff", "id_rsa"],
    ["pytest", "--config=.env"],
])
def test_path_traversal_absolute_paths_and_sensitive_paths_are_rejected(argv: list[str]) -> None:
    with pytest.raises(TerminalPolicyError):
        validate_argv(argv)


@pytest.mark.asyncio
async def test_successful_and_failed_processes_are_reported_with_bounded_output(tmp_path: Path) -> None:
    success_executor = FakeIsolatedExecutor(ProcessResult("x" * (MAX_OUTPUT_BYTES + 100), "", 0, 1))
    result = await TerminalService(tmp_path, success_executor).run(["npm", "test"])
    assert result["exit_code"] == 0
    assert len(result["stdout"].encode()) == MAX_OUTPUT_BYTES
    assert success_executor.argv == ["npm", "test"]

    failed = await TerminalService(tmp_path, FakeIsolatedExecutor(ProcessResult("", "assertion failed", 2, 1))).run(["pytest", "-q"])
    assert failed["exit_code"] == 2
    assert failed["stderr"] == "assertion failed"


@pytest.mark.asyncio
async def test_timeout_cancels_executor(tmp_path: Path) -> None:
    executor = FakeIsolatedExecutor(delay=2)
    result = await TerminalService(tmp_path, executor).run(["npm", "test"], timeout_seconds=1)
    assert executor.cancelled
    assert result["timed_out"] is True
    assert result["exit_code"] == 124


@pytest.mark.asyncio
async def test_execution_fails_closed_without_real_isolation(tmp_path: Path) -> None:
    service = TerminalService(tmp_path)
    assert service.capabilities()["available"] is False
    with pytest.raises(SandboxUnavailable):
        await service.run(["npm", "test"])


@pytest.mark.asyncio
@pytest.mark.parametrize("timeout", [0, 61, True, "5", 1.5])
async def test_timeout_value_is_strictly_validated(tmp_path: Path, timeout: object) -> None:
    with pytest.raises(TerminalPolicyError, match="Timeout"):
        await TerminalService(tmp_path, FakeIsolatedExecutor()).run(["npm", "test"], timeout)  # type: ignore[arg-type]


def test_test_command_detection_uses_project_configuration(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text('{"scripts":{"test":"vitest"}}', encoding="utf-8")
    assert detect_test_command(tmp_path) == ("node", ["npm", "test"])
    (tmp_path / "package.json").unlink()
    (tmp_path / "pytest.ini").touch()
    assert detect_test_command(tmp_path) == ("python", ["pytest", "-q"])
    (tmp_path / "pytest.ini").unlink()
    (tmp_path / "pubspec.yaml").touch()
    assert detect_test_command(tmp_path) == ("flutter", ["flutter", "test"])


@pytest.mark.asyncio
async def test_terminal_routes_require_authentication_and_project_membership() -> None:
    terminal_routes = [route for route in router.routes if "/terminal/" in route.path]
    assert {route.path.rsplit("/", 1)[-1] for route in terminal_routes} >= {"capabilities", "run", "tests"}
    assert all(any(dependency.call is get_current_user_id for dependency in route.dependant.dependencies) for route in terminal_routes)

    project = SimpleNamespace(id="project-id", workspace_id="workspace-id")
    session = AsyncMock()
    session.scalar.side_effect = [project, None]
    with pytest.raises(HTTPException) as error:
        await _authorized_project(session, project.id, "not-a-member", write=True)
    assert error.value.status_code == 404

    session.scalar.side_effect = [project, SimpleNamespace(role=WorkspaceRole.VIEWER)]
    with pytest.raises(HTTPException) as error:
        await _authorized_project(session, project.id, "viewer", write=True)
    assert error.value.status_code == 403
