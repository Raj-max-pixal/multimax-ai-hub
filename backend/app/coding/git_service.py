"""Safe, project-scoped Git operations for the coding agent."""

from __future__ import annotations

import difflib
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse


class GitOperationError(Exception):
    """A sanitized Git operation failure suitable for an API response."""


@dataclass(frozen=True)
class GitFileState:
    path: str
    index_status: str
    worktree_status: str


def validate_branch_name(branch: str) -> str:
    if (not branch or len(branch) > 200 or branch.startswith(("-", "."))
            or branch.endswith(("/", ".", ".lock")) or ".." in branch
            or "@{" in branch or any(ord(char) < 32 for char in branch)
            or re.search(r"[ ~^:?*\[\\]", branch)
            or any(part in {"", "."} for part in branch.split("/"))):
        raise ValueError("Invalid default branch name")
    return branch


def validate_repository_url(value: str) -> tuple[str, str]:
    parsed = urlparse(value.strip())
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or "@" in parsed.netloc):
        raise ValueError("Use a public HTTPS repository URL without embedded credentials")
    if parsed.port not in (None, 443):
        raise ValueError("Custom repository URL ports are not supported")
    host = parsed.hostname.lower()
    if host == "github.com":
        provider = "github"
    elif host in {"gitlab.com", "www.gitlab.com"}:
        provider = "gitlab"
    elif host in {"bitbucket.org", "www.bitbucket.org"}:
        provider = "bitbucket"
    else:
        provider = "generic"
    # Store a canonical credential-free URL; query and fragment were rejected above.
    safe_url = urlunparse(("https", parsed.netloc.lower(), parsed.path.rstrip("/"), "", "", ""))
    if not parsed.path.strip("/"):
        raise ValueError("Repository URL must include an owner and repository")
    return safe_url, provider


def parse_porcelain_status(raw: str) -> list[GitFileState]:
    entries = raw.split("\0")
    states: list[GitFileState] = []
    index = 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if len(entry) < 4:
            continue
        x, y, path = entry[0], entry[1], entry[3:]
        if x in {"R", "C"} or y in {"R", "C"}:
            index += 1  # -z format emits the source path as a second NUL record.
        states.append(GitFileState(path=path, index_status=x, worktree_status=y))
    return states


def _secret_path(path: str) -> bool:
    parts = path.replace("\\", "/").lower().split("/")
    name = parts[-1] if parts else ""
    return (
        any(part in {".git", "node_modules", ".venv", "venv"} for part in parts)
        or name in {".env", "credentials.json", "service-account.json", "id_rsa", "id_ed25519"}
        or name.startswith((".env.", "credentials.", "secrets."))
        or Path(name).suffix in {".pem", ".key", ".p12", ".pfx", ".keystore"}
    )


class GitService:
    def __init__(self, project_root: Path) -> None:
        self.root = project_root.resolve()

    def _run(self, args: list[str], *, timeout: int = 15, check: bool = True) -> subprocess.CompletedProcess[str]:
        executable = shutil.which("git")
        if not executable:
            raise GitOperationError("Git is not installed on the application server")
        try:
            result = subprocess.run(
                [executable, "-C", str(self.root), *args],
                cwd=self.root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_NOSYSTEM": "1"},
            )
        except subprocess.TimeoutExpired as exc:
            raise GitOperationError("Git operation timed out") from exc
        except OSError as exc:
            raise GitOperationError("Git could not access the selected project") from exc
        if check and result.returncode:
            raise GitOperationError("Git operation failed; verify the repository and try again")
        return result

    def is_repository(self) -> bool:
        if not self.root.is_dir():
            return False
        result = self._run(["rev-parse", "--show-toplevel"], check=False)
        if result.returncode:
            return False
        try:
            return Path(result.stdout.strip()).resolve() == self.root
        except OSError:
            return False

    def connect(self, repository_url: str, default_branch: str) -> dict[str, str]:
        safe_url, provider = validate_repository_url(repository_url)
        branch = validate_branch_name(default_branch)
        self.root.mkdir(parents=True, exist_ok=True)
        if not self.is_repository():
            # Initialize over the project's managed files; never clone, fetch, or overwrite them.
            self._run(["init"], timeout=30)
            self._run(["symbolic-ref", "HEAD", f"refs/heads/{branch}"])
        existing = self._run(["remote", "get-url", "origin"], check=False)
        if existing.returncode:
            self._run(["remote", "add", "origin", safe_url])
        else:
            self._run(["remote", "set-url", "origin", safe_url])
        return {"repository_url": safe_url, "provider": provider, "default_branch": branch}

    def status(self) -> dict[str, Any]:
        if not self.is_repository():
            return {"is_git_repository": False, "state": "not_connected", "branch": None,
                    "modified_files": [], "untracked_files": [], "staged_files": [], "deleted_files": []}
        branch_result = self._run(["branch", "--show-current"], check=False)
        branch = branch_result.stdout.strip() or "DETACHED"
        raw = self._run(["status", "--porcelain=v1", "-z", "--untracked-files=all"]).stdout
        states = [state for state in parse_porcelain_status(raw) if not _secret_path(state.path)]
        modified = sorted({s.path for s in states if any(code in {s.index_status, s.worktree_status} for code in {"M", "T", "R", "C"})})
        untracked = sorted({s.path for s in states if s.index_status == "?" and s.worktree_status == "?"})
        staged = sorted({s.path for s in states if s.index_status not in {" ", "?"}})
        deleted = sorted({s.path for s in states if "D" in (s.index_status, s.worktree_status)})
        return {"is_git_repository": True, "state": "dirty" if states else "clean", "branch": branch,
                "modified_files": modified, "untracked_files": untracked,
                "staged_files": staged, "deleted_files": deleted}

    def diff(self, *, limit: int = 120_000) -> dict[str, Any]:
        status = self.status()
        if not status["is_git_repository"]:
            return {"is_git_repository": False, "diff": "", "truncated": False}
        pieces = []
        raw_states = parse_porcelain_status(
            self._run(["status", "--porcelain=v1", "-z", "--untracked-files=all"]).stdout
        )
        paths = sorted({state.path for state in raw_states if not _secret_path(state.path)})
        literal_paths = [f":(literal){path}" for path in paths]
        for args in (["diff", "--no-ext-diff", "--no-textconv", "--", *literal_paths],
                     ["diff", "--cached", "--no-ext-diff", "--no-textconv", "--", *literal_paths]):
            if not literal_paths:
                continue
            result = self._run(args)
            if result.stdout:
                pieces.append(result.stdout)
        for path in status["untracked_files"]:
            safe_path = Path(path)
            target = (self.root / safe_path).resolve()
            if self.root not in target.parents or _secret_path(path) or not target.is_file():
                continue
            try:
                data = target.read_bytes()
                if len(data) > 2 * 1024 * 1024 or b"\0" in data:
                    pieces.append(f"Binary or oversized untracked file omitted: {path}\n")
                    continue
                text = data.decode("utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            lines = difflib.unified_diff([], text.splitlines(keepends=True), fromfile="/dev/null", tofile=f"b/{path}")
            pieces.append("".join(lines))
        content = "\n".join(pieces)
        truncated = len(content) > limit
        return {"is_git_repository": True, "diff": content[:limit], "truncated": truncated}

    def commit(self, message: str, user_id: str) -> dict[str, str]:
        clean_message = message.strip()
        if not clean_message or len(clean_message) > 200:
            raise ValueError("Commit message must be between 1 and 200 characters")
        if _looks_like_secret(clean_message.encode("utf-8")):
            raise ValueError("Commit messages must not contain credentials")
        status = self.status()
        if not status["is_git_repository"]:
            raise GitOperationError("This project is not connected to a Git repository")
        all_states = parse_porcelain_status(
            self._run(["status", "--porcelain=v1", "-z", "--untracked-files=all"]).stdout
        )
        if any(_secret_path(state.path) for state in all_states):
            raise GitOperationError("Commit blocked because sensitive files are present in the changes")
        if not all_states:
            raise GitOperationError("There are no changes to commit")
        for state in all_states:
            target = (self.root / state.path).resolve()
            if self.root not in target.parents or not target.is_file():
                continue  # deleted paths have no current contents
            try:
                data = target.read_bytes()
            except OSError as exc:
                raise GitOperationError("Unable to validate changed files for credentials") from exc
            if _looks_like_secret(data):
                raise GitOperationError("Commit blocked because a changed file appears to contain credentials")
        self._run(["add", "-A", "--", "."], timeout=30)
        # Disable local hooks and signing: project hooks are untrusted and must not execute on the server.
        with tempfile.TemporaryDirectory(prefix="multimax-git-hooks-") as hooks_dir:
            self._run([
                "-c", f"core.hooksPath={hooks_dir}", "-c", "commit.gpgsign=false",
                "-c", "user.name=Multimax AI Hub User",
                "-c", f"user.email={user_id}@users.noreply.multimax.local",
                "commit", "-m", clean_message,
            ], timeout=60)
        commit_id = self._run(["rev-parse", "--short", "HEAD"]).stdout.strip()
        return {"commit": commit_id, "message": clean_message}


def _looks_like_secret(data: bytes) -> bool:
    text = data.decode("utf-8", errors="ignore")
    markers = (
        re.compile(r"(?i)\b(?:AIza[0-9A-Za-z_-]{20,}|(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16})\b"),
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        re.compile(r"(?im)^\s*(?:api[_-]?key|token|credential|private[_-]?key|client[_-]?secret|password|database[_-]?url)\s*[:=]\s*(['\"]?)(?!\$\{|\[REDACTED\]|YOUR_|CHANGEME|process\.env|os\.getenv)[^\s'\";,]{12,}"),
    )
    return any(pattern.search(text) for pattern in markers)
