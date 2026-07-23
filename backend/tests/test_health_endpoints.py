from fastapi.testclient import TestClient

from main import app


def test_health_endpoint_is_available() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"


def test_models_endpoint_returns_models_list() -> None:
    client = TestClient(app)
    response = client.get("/api/models")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload.get("models"), list)
