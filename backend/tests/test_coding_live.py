"""Opt-in Gemini smoke test using a disposable database, user, and repository.

Run from backend with MULTIMAX_LIVE_CODING=1. Uses the existing server-side
Gemini configuration; never prints keys, passwords, or access tokens.
"""
import os
import secrets

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


@pytest.mark.ai
@pytest.mark.skipif(os.getenv("MULTIMAX_LIVE_CODING") != "1", reason="Explicit live Gemini test opt-in required")
def test_live_coding_workflow(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{(tmp_path / 'coding.db').as_posix()}")
    monkeypatch.setenv("DATABASE_AUTO_CREATE", "true")
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("LOG_FILE", str(tmp_path / "smoke.log"))
    monkeypatch.setenv("APP_DEBUG", "false")
    get_settings.cache_clear()
    try:
        with TestClient(create_app()) as client:
            assert get_settings().GEMINI_API_KEY, "Server-side Gemini configuration is required"

            def checked(method, path, expected=200, **kwargs):
                if (path.endswith('/assist') or path.endswith('/commit-message')) and 'json' in kwargs and os.getenv('MULTIMAX_LIVE_MODEL'):
                    kwargs['json']['model'] = os.environ['MULTIMAX_LIVE_MODEL']
                response = getattr(client, method)(path, **kwargs)
                assert response.status_code == expected, (path, response.status_code, response.json().get("detail"))
                return response.json()

            password = "SmokeA1-" + secrets.token_urlsafe(20)
            checked("post", "/api/auth/register", 201, json={
                "username": "coding_smoke", "email": "coding-smoke@example.com", "password": password,
            })
            login = checked("post", "/api/auth/login", json={"username": "coding_smoke", "password": password})
            client.headers["Authorization"] = f"Bearer {login['access_token']}"
            prompts = {
                "generate": "Write a Python add(a,b) function.",
                "fix": "Correct the subtraction in this addition function.",
                "explain": "Explain what this function actually does.",
                "refactor": "Refactor with type hints, preserving behavior.",
                "tests": "Write two pytest tests for addition; identify the failing case.",
                "readme": "Write a tiny README for this Python arithmetic utility.",
                "api": "Write a tiny FastAPI addition endpoint.",
                "project": "Outline a tiny Python addition project with file contents.",
                "review": "Review this addition function for correctness.",
            }
            for task, prompt in prompts.items():
                selected = os.getenv("MULTIMAX_LIVE_TASKS", "").split(",")
                if selected != [""] and task not in selected:
                    continue
                result = checked("post", "/api/v1/coding/assist", json={
                    "task": task, "prompt": prompt + " Keep your answer under 100 words.",
                    "code": "def add(a, b): return a - b", "language": "Python",
                })
                assert result["answer"].strip()
                assert result["model"].startswith("gemini-")
                print(f"Live {task}: OK", flush=True)

            workspace = checked("post", "/api/v1/workspaces", 201, json={"name": "Coding smoke"})
            project = checked("post", f"/api/v1/workspaces/{workspace['id']}/projects", 201, json={"name": "Arithmetic"})
            prefix = f"/api/v1/coding/projects/{project['id']}"
            assert checked("get", "/api/v1/coding/workspaces")["items"]
            checked("post", prefix + "/files", 201, files={"file": ("add.py", b"def add(a, b): return a - b\n", "text/plain")}, data={"path": "add.py"})
            assert checked("get", prefix + "/files?q=add")["items"][0]["path"] == "add.py"
            assert "a - b" in checked("get", prefix + "/file?path=add.py")["content"]
            assert checked("get", prefix + "/search?q=add")["items"]
            for mode in ("explain", "suggest"):
                assert checked("post", prefix + "/assist", json={"mode": mode, "prompt": "Describe the addition bug in one sentence.", "path": "add.py"})["answer"].strip()
            proposal = checked("post", prefix + "/assist", json={"mode": "patch", "prompt": "Fix addition to return a + b. Keep the same function name and arguments.", "path": "add.py"})
            assert proposal["diff"]
            assert "a - b" in checked("get", prefix + "/file?path=add.py")["content"]
            checked("post", prefix + "/apply", json={"path": "add.py", "content": proposal["proposed_content"], "original_sha256": proposal["original_sha256"]})
            assert "a + b" in checked("get", prefix + "/file?path=add.py")["content"]
            checked("post", prefix + "/git/connect", json={"repository_url": "https://github.com/example/coding-smoke.git", "default_branch": "main"})
            assert checked("get", prefix + "/git/status")["is_git_repository"]
            assert checked("get", prefix + "/git/diff")["diff"]
            subject = checked("post", prefix + "/git/commit-message", json={})["message"]
            assert subject
            checked("post", prefix + "/git/commit", json={"message": subject, "confirmed": True})
            assert checked("get", prefix + "/git/status")["state"] == "clean"
            capabilities = checked("get", prefix + "/terminal/capabilities")
            assert not capabilities["available"]  # Host execution must remain disabled.
            print("Live project files, explain/suggest, patch/apply, and local Git commit: OK", flush=True)
    finally:
        get_settings.cache_clear()
