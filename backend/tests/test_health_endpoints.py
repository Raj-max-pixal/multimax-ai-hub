from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint_is_available() -> None:
    client = TestClient(create_app())
    response = client.get("/health/live")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "alive"


def test_models_endpoint_returns_models_list() -> None:
    client = TestClient(create_app())
    response = client.get("/api/models")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload.get("models"), list)


def test_readiness_is_not_reported_before_initialization() -> None:
    response = TestClient(create_app()).get("/health/ready")
    assert response.status_code == 503
