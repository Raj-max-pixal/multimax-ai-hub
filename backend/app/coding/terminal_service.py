"""Policy and adapter boundary for isolated project command execution.

No host-process executor is provided intentionally: a project directory alone
is not a security sandbox. Deployments must inject a hardened executor (for
example, a locked-down container runtime) before commands can run.
"""

from __future__ import annotations

import asyncio
import re
import shlex
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

MAX_ARGUMENTS = 64
MAX_ARGUMENT_LENGTH = 500
MAX_OUTPUT_BYTES = 64 * 1024
DEFAULT_TIMEOUT_SECONDS = 60
ALLOWED_BINARIES = {"npm", "pnpm", "yarn", "python", "pytest", "pip", "node", "git", "flutter"}
SHELL_META = re.compile(r"[;&|<>`$()%!\r\n\x00]")
SECRET_REFERENCE = re.compile(r"(?i)(?:^|[/\\=])(?:\.env(?:\.[^/\\]*)?|credentials?[^/\\]*|secrets?[^/\\]*|id_rsa|id_ed25519)(?:$|[/\\\s,])|\.(?:pem|key|p12|pfx|keystore)(?:$|[/\\\s,])")


class TerminalPolicyError(ValueError):
    pass


class SandboxUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class ProcessResult:
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int


class IsolatedProcessExecutor(Protocol):
    """Hardened runtime contract required before any command can be enabled.

    Implementations must use an unprivileged disposable container/VM with
    networking disabled, a fresh allowlisted environment, a filtered project
    copy (no secrets or symlinks), no other host mounts, CPU/memory/process
    limits, bounded streaming output, and kill the full process tree on timeout
    or cancellation. They must never invoke a shell.
    """

    @property
    def available(self) -> bool: ...

    async def run(self, argv: list[str], project_root: Path, timeout_seconds: int) -> ProcessResult: ...


class UnavailableExecutor:
    """Fail-closed until a real process sandbox is configured by the host."""

    @property
    def available(self) -> bool:
        return False

    async def run(self, argv: list[str], project_root: Path, timeout_seconds: int) -> ProcessResult:
        raise SandboxUnavailable("Secure command execution is unavailable: no isolated process runtime is configured.")


def parse_command_line(command: str) -> list[str]:
    """Parse a simple command line without invoking a shell."""
    if not isinstance(command, str) or not command.strip() or len(command) > 2000:
        raise TerminalPolicyError("Enter a command up to 2,000 characters")
    if SHELL_META.search(command):
        raise TerminalPolicyError("Shell operators and expansions are not supported")
    try:
        argv = shlex.split(command, posix=False)
    except ValueError as exc:
        raise TerminalPolicyError("Command quoting is invalid") from exc
    # Windows shlex preserves quote characters; remove only a balanced outer pair.
    argv = [arg[1:-1] if len(arg) >= 2 and arg[0] == arg[-1] and arg[0] in "\"'" else arg for arg in argv]
    validate_argv(argv)
    return argv


def validate_argv(argv: list[str]) -> list[str]:
    if not isinstance(argv, list) or not argv or len(argv) > MAX_ARGUMENTS:
        raise TerminalPolicyError("A command and at most 63 arguments are required")
    if any(not isinstance(arg, str) or not arg or len(arg) > MAX_ARGUMENT_LENGTH for arg in argv):
        raise TerminalPolicyError("Command arguments must be non-empty and at most 500 characters")
    if any(SHELL_META.search(arg) for arg in argv):
        raise TerminalPolicyError("Shell operators and expansions are not supported")
    executable = Path(argv[0].replace("\\", "/")).name.lower()
    if executable not in ALLOWED_BINARIES or "/" in argv[0].replace("\\", "/"):
        raise TerminalPolicyError("This executable is not allowlisted")
    if any(SECRET_REFERENCE.search(arg) for arg in argv[1:]):
        raise TerminalPolicyError("Secret and environment-file paths are not accessible")
    if any(".." in arg.replace("\\", "/").split("/") for arg in argv[1:]):
        raise TerminalPolicyError("Path traversal is not allowed")
    if any(re.match(r"^(?:[A-Za-z]:|/|\\\\)", arg) for arg in argv[1:] if not arg.startswith("-")):
        raise TerminalPolicyError("Absolute paths outside the selected project are not allowed")
    lower_args = [arg.lower() for arg in argv[1:]]
    if executable in {"python", "python.exe"} and any(arg in {"-c", "--command"} for arg in lower_args):
        raise TerminalPolicyError("Inline Python execution is not allowed")
    if executable in {"node", "node.exe"} and any(arg in {"-e", "--eval", "-p", "--print", "--require", "--import"} for arg in lower_args):
        raise TerminalPolicyError("Inline or injected Node execution is not allowed")
    if executable in {"npm", "pnpm", "yarn"} and (not lower_args or lower_args[0] not in {"run", "test", "build", "lint"}):
        raise TerminalPolicyError("Only configured run, test, build, and lint scripts are allowed")
    if executable == "pip" and (not lower_args or lower_args[0] not in {"list", "show", "check"}):
        raise TerminalPolicyError("Package installation and network-capable pip commands are not allowed")
    if executable == "python" and "-m" in lower_args:
        module_index = lower_args.index("-m") + 1
        if module_index >= len(lower_args) or lower_args[module_index] not in {"pytest", "unittest"}:
            raise TerminalPolicyError("Only Python pytest and unittest modules are allowed")
    if executable == "git" and (not lower_args or lower_args[0] not in {"status", "diff", "log", "rev-parse"}):
        raise TerminalPolicyError("Only read-only Git inspection commands are allowed")
    return argv


def detect_test_command(project_root: Path) -> tuple[str, list[str]] | None:
    """Choose a test command only from checked-in project configuration."""
    package_json = project_root / "package.json"
    if package_json.is_file():
        import json
        try:
            data = json.loads(package_json.read_text(encoding="utf-8"))
            scripts = data.get("scripts", {})
            if isinstance(scripts, dict) and isinstance(scripts.get("test"), str):
                return "node", ["npm", "test"]
        except (OSError, ValueError):
            return None
    if (project_root / "pytest.ini").exists() or (project_root / "pyproject.toml").exists() or any(project_root.glob("test_*.py")):
        return "python", ["pytest", "-q"]
    if (project_root / "pubspec.yaml").exists():
        return "flutter", ["flutter", "test"]
    return None


class TerminalService:
    def __init__(self, project_root: Path, executor: IsolatedProcessExecutor | None = None):
        self.project_root = project_root.resolve()
        self.executor = executor or UnavailableExecutor()

    def capabilities(self) -> dict[str, object]:
        return {
            "available": self.executor.available,
            "reason": None if self.executor.available else "A hardened OS-level process sandbox is not configured on this server.",
            "allowed_commands": sorted(ALLOWED_BINARIES),
        }

    async def run(self, argv: list[str], timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> dict[str, object]:
        validate_argv(argv)
        if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= DEFAULT_TIMEOUT_SECONDS:
            raise TerminalPolicyError(f"Timeout must be between 1 and {DEFAULT_TIMEOUT_SECONDS} seconds")
        if not self.project_root.is_dir():
            raise FileNotFoundError("Selected project directory is unavailable")
        if not self.executor.available:
            raise SandboxUnavailable("Secure command execution is unavailable: no isolated process runtime is configured.")
        started = time.monotonic()
        try:
            result = await asyncio.wait_for(self.executor.run(argv, self.project_root, timeout_seconds), timeout_seconds)
        except asyncio.TimeoutError:
            return {
                "command": shlex.join(argv), "stdout": "", "stderr": f"Process exceeded the {timeout_seconds}-second timeout and was cancelled.",
                "exit_code": 124, "duration_ms": timeout_seconds * 1000, "timed_out": True,
            }
        except asyncio.CancelledError:
            # Executor implementations must terminate the isolated process on cancellation.
            raise
        elapsed = max(0, int((time.monotonic() - started) * 1000))
        return {
            "command": shlex.join(argv), "stdout": result.stdout.encode("utf-8", "replace")[:MAX_OUTPUT_BYTES].decode("utf-8", "ignore"),
            "stderr": result.stderr.encode("utf-8", "replace")[:MAX_OUTPUT_BYTES].decode("utf-8", "ignore"),
            "exit_code": result.exit_code, "duration_ms": max(result.duration_ms, elapsed), "timed_out": False,
        }
