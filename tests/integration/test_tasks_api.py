"""Integration tests for /tasks against a real PostgreSQL database."""

import pytest


@pytest.fixture
def project(client):
    return client.post("/projects", json={"name": "Task Project"}).json()


@pytest.fixture
def user(client):
    return client.post("/users", json={"name": "Assignee", "email": "assignee@example.com"}).json()


def test_create_task_success(client, project, user):
    resp = client.post(
        "/tasks",
        json={
            "title": "Build API",
            "description": "Implement endpoints",
            "project_id": project["id"],
            "assigned_user_id": user["id"],
            "priority": "high",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Build API"
    assert body["status"] == "todo"  # default
    assert body["priority"] == "high"
    assert body["project_id"] == project["id"]
    assert body["assigned_user_id"] == user["id"]


def test_create_task_nonexistent_project_returns_404(client):
    resp = client.post("/tasks", json={"title": "X", "project_id": 999999})
    assert resp.status_code == 404


def test_create_task_nonexistent_assigned_user_returns_404(client, project):
    resp = client.post(
        "/tasks", json={"title": "X", "project_id": project["id"], "assigned_user_id": 999999}
    )
    assert resp.status_code == 404


def test_create_task_invalid_status_returns_422(client, project):
    resp = client.post(
        "/tasks", json={"title": "X", "project_id": project["id"], "status": "not-a-status"}
    )
    assert resp.status_code == 422


def test_create_task_invalid_priority_returns_422(client, project):
    resp = client.post(
        "/tasks", json={"title": "X", "project_id": project["id"], "priority": "urgent"}
    )
    assert resp.status_code == 422


def test_create_task_missing_title_returns_422(client, project):
    resp = client.post("/tasks", json={"project_id": project["id"]})
    assert resp.status_code == 422


def test_get_nonexistent_task_returns_404(client):
    resp = client.get("/tasks/999999")
    assert resp.status_code == 404


def test_patch_task_partial_update(client, project):
    task = client.post("/tasks", json={"title": "Old title", "project_id": project["id"]}).json()

    resp = client.patch(f"/tasks/{task['id']}", json={"status": "in_progress"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "in_progress"
    assert body["title"] == "Old title"  # unaffected by partial update


def test_patch_task_reassign_to_nonexistent_user_returns_404(client, project):
    task = client.post("/tasks", json={"title": "T", "project_id": project["id"]}).json()

    resp = client.patch(f"/tasks/{task['id']}", json={"assigned_user_id": 999999})
    assert resp.status_code == 404


def test_patch_task_move_to_nonexistent_project_returns_404(client, project):
    task = client.post("/tasks", json={"title": "T", "project_id": project["id"]}).json()

    resp = client.patch(f"/tasks/{task['id']}", json={"project_id": 999999})
    assert resp.status_code == 404


def test_patch_nonexistent_task_returns_404(client):
    resp = client.patch("/tasks/999999", json={"status": "done"})
    assert resp.status_code == 404


def test_delete_task_removes_it(client, project):
    task = client.post("/tasks", json={"title": "Delete me", "project_id": project["id"]}).json()

    resp = client.delete(f"/tasks/{task['id']}")
    assert resp.status_code == 204

    resp = client.get(f"/tasks/{task['id']}")
    assert resp.status_code == 404


def test_delete_nonexistent_task_returns_404(client):
    resp = client.delete("/tasks/999999")
    assert resp.status_code == 404


def test_filter_tasks_by_status(client, project):
    client.post("/tasks", json={"title": "A", "project_id": project["id"], "status": "todo"})
    client.post("/tasks", json={"title": "B", "project_id": project["id"], "status": "done"})

    resp = client.get("/tasks", params={"status": "done", "project_id": project["id"]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert all(t["status"] == "done" for t in body["items"])


def test_filter_tasks_by_priority(client, project):
    client.post("/tasks", json={"title": "Urgent", "project_id": project["id"], "priority": "high"})
    client.post("/tasks", json={"title": "Later", "project_id": project["id"], "priority": "low"})

    resp = client.get("/tasks", params={"priority": "high", "project_id": project["id"]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Urgent"


def test_filter_tasks_by_assigned_user(client, project, user):
    client.post(
        "/tasks",
        json={"title": "Assigned", "project_id": project["id"], "assigned_user_id": user["id"]},
    )
    client.post("/tasks", json={"title": "Unassigned", "project_id": project["id"]})

    resp = client.get("/tasks", params={"assigned_user_id": user["id"]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Assigned"


def test_sort_tasks_by_priority(client, project):
    client.post("/tasks", json={"title": "Low", "project_id": project["id"], "priority": "low"})
    client.post("/tasks", json={"title": "High", "project_id": project["id"], "priority": "high"})
    client.post("/tasks", json={"title": "Medium", "project_id": project["id"], "priority": "medium"})

    resp = client.get(
        "/tasks", params={"project_id": project["id"], "sort_by": "title", "order": "asc"}
    )
    assert resp.status_code == 200
    titles = [t["title"] for t in resp.json()["items"]]
    assert titles == sorted(titles)


def test_pagination_limits_and_offsets_results(client, project):
    for i in range(5):
        client.post("/tasks", json={"title": f"Task {i}", "project_id": project["id"]})

    resp = client.get("/tasks", params={"project_id": project["id"], "limit": 2, "offset": 0})
    body = resp.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2
    assert body["limit"] == 2
    assert body["offset"] == 0

    resp2 = client.get("/tasks", params={"project_id": project["id"], "limit": 2, "offset": 2})
    body2 = resp2.json()
    assert len(body2["items"]) == 2
    assert {t["id"] for t in body["items"]}.isdisjoint({t["id"] for t in body2["items"]})


def test_metrics_endpoint_tracks_task_creation(client, project):
    before = client.get("/metrics").json()["tasks_created"]
    client.post("/tasks", json={"title": "Tracked", "project_id": project["id"]})
    after = client.get("/metrics").json()["tasks_created"]
    assert after == before + 1
