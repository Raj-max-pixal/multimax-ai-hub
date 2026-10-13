from contextlib import asynccontextmanager

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.mark.parametrize("fail", [False, True])
def test_fallback_stream_keeps_client_open_and_reports_failure(monkeypatch, fail):
    clients = []

    class Client:
        def __init__(self, **kwargs):
            self.open = False
            clients.append(self)

        async def __aenter__(self):
            self.open = True
            return self

        async def __aexit__(self, *args):
            self.open = False

        @asynccontextmanager
        async def stream(self, *args, **kwargs):
            assert self.open, "HTTP client was closed before streaming started"
            assert kwargs["json"]["messages"] == [{"role": "user", "content": "hello"}]
            if fail:
                raise httpx.ConnectError("private provider diagnostic")
            yield self

        def raise_for_status(self):
            pass

        async def aiter_bytes(self):
            assert self.open
            yield b'{"message":{"content":"hello"},"done":false}\n'
            assert self.open
            yield b'{"done":true}\n'

    monkeypatch.setattr("app.main.httpx.AsyncClient", Client)
    response = TestClient(create_app()).post("/api/chat", json={
        "model": "test-local", "stream": True,
        "messages": [{"role": "user", "content": "hello"}, {"role": "assistant", "content": " "}],
    })
    assert response.status_code == 200
    assert "application/x-ndjson" in response.headers["content-type"]
    assert not clients[0].open
    if fail:
        assert "Local AI service is unavailable" in response.text
        assert "private provider diagnostic" not in response.text
    else:
        assert '"content":"hello"' in response.text
        assert '"done":true' in response.text
