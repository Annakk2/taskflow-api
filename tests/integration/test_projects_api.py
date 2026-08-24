"""Integration tests for /projects against a real PostgreSQL database."""


def test_create_and_get_project(client):
    resp = client.post("/projects", json={"name": "TaskFlow", "description": "demo"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "TaskFlow"

    resp = client.get(f"/projects/{body['id']}")
    assert resp.status_code == 200
    assert resp.json()["description"] == "demo"


def test_create_project_without_description(client):
    resp = client.post("/projects", json={"name": "No Description"})
    assert resp.status_code == 201
    assert resp.json()["description"] is None


def test_list_projects_returns_created_projects(client):
    client.post("/projects", json={"name": "Alpha"})
    client.post("/projects", json={"name": "Beta"})

    resp = client.get("/projects")
    assert resp.status_code == 200
    names = {p["name"] for p in resp.json()}
    assert {"Alpha", "Beta"}.issubset(names)


def test_get_nonexistent_project_returns_404(client):
    resp = client.get("/projects/999999")
    assert resp.status_code == 404


def test_project_statistics_nonexistent_returns_404(client):
    resp = client.get("/projects/999999/statistics")
    assert resp.status_code == 404


def test_project_statistics_aggregates_tasks(client):
    project = client.post("/projects", json={"name": "Stats Project"}).json()
    pid = project["id"]

    client.post("/tasks", json={"title": "T1", "project_id": pid, "status": "todo", "priority": "high"})
    client.post("/tasks", json={"title": "T2", "project_id": pid, "status": "todo", "priority": "low"})
    client.post("/tasks", json={"title": "T3", "project_id": pid, "status": "done", "priority": "high"})

    resp = client.get(f"/projects/{pid}/statistics")
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["total_tasks"] == 3
    assert stats["by_status"]["todo"] == 2
    assert stats["by_status"]["done"] == 1
    assert stats["by_priority"]["high"] == 2
    assert stats["unassigned_tasks"] == 3
