from fastapi.testclient import TestClient

from src.app import app


client = TestClient(app)


def test_liveness_and_security_headers():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-request-id"]


def test_login_rate_limit_returns_retry_after(monkeypatch):
    from src.middlewares.production import ProductionMiddleware

    ProductionMiddleware._requests.clear()
    monkeypatch.setattr("src.middlewares.production.get_settings", lambda: type("S", (), {
        "RATE_LIMIT_ENABLED": True, "RATE_LIMIT_LOGIN": 1,
        "RATE_LIMIT_REGISTER": 1, "RATE_LIMIT_TRACK_ORDER": 1,
        "ENVIRONMENT": "test",
    })())
    first = client.post("/auth/login", json={"email": "nobody@example.com", "senha": "wrong"})
    second = client.post("/auth/login", json={"email": "nobody@example.com", "senha": "wrong"})
    assert first.status_code != 429
    assert second.status_code == 429
    assert second.headers["retry-after"] == "60"
    ProductionMiddleware._requests.clear()
