"""Integration tests for /health, /metrics, and generic error handling."""

from fastapi.testclient import TestClient

from app.main import app
from app.routers import users as users_router


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_metrics_endpoint_returns_snapshot(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.json()
    assert "request_count" in body
    assert "endpoints" in body


def test_unhandled_exception_returns_500_without_leaking_internals(client, monkeypatch):
    # `client` fixture already wires app.dependency_overrides[get_db] to the test
    # session; build a client here that does NOT re-raise server exceptions, so we
    # can assert on the JSON 500 response the exception handler produces.
    def _boom(*args, **kwargs):
        raise RuntimeError("db connection pool exhausted: password=hunter2")

    monkeypatch.setattr(users_router.UserService, "list_users", _boom)

    with TestClient(app, raise_server_exceptions=False) as non_raising_client:
        resp = non_raising_client.get("/users")

    assert resp.status_code == 500
    body = resp.json()
    assert body == {"detail": "Internal server error"}
    assert "hunter2" not in resp.text
    assert "RuntimeError" not in resp.text
