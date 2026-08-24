"""Integration tests for /users against a real PostgreSQL database."""


def test_create_and_get_user(client):
    resp = client.post("/users", json={"name": "Ana", "email": "ana@example.com"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Ana"
    assert body["email"] == "ana@example.com"
    assert "id" in body and "created_at" in body

    resp = client.get(f"/users/{body['id']}")
    assert resp.status_code == 200
    assert resp.json()["email"] == "ana@example.com"


def test_create_user_duplicate_email_returns_409(client):
    client.post("/users", json={"name": "Ana", "email": "dup@example.com"})
    resp = client.post("/users", json={"name": "Another", "email": "dup@example.com"})
    assert resp.status_code == 409


def test_create_user_invalid_email_returns_422(client):
    resp = client.post("/users", json={"name": "Ana", "email": "not-an-email"})
    assert resp.status_code == 422


def test_get_nonexistent_user_returns_404(client):
    resp = client.get("/users/999999")
    assert resp.status_code == 404


def test_list_users_returns_created_users(client):
    client.post("/users", json={"name": "A", "email": "a@example.com"})
    client.post("/users", json={"name": "B", "email": "b@example.com"})

    resp = client.get("/users")
    assert resp.status_code == 200
    emails = {u["email"] for u in resp.json()}
    assert {"a@example.com", "b@example.com"}.issubset(emails)
