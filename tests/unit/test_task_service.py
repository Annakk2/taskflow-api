"""Unit tests for TaskService business logic, isolated from the database via mocks."""

from unittest.mock import MagicMock

import pytest

from app.models.project import Project
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User
from app.services.task_service import TaskService
from app.utils.exceptions import NotFoundError


def make_service() -> tuple[TaskService, MagicMock, MagicMock, MagicMock]:
    db = MagicMock()
    service = TaskService(db)
    service.repo = MagicMock()
    service.project_repo = MagicMock()
    service.user_repo = MagicMock()
    return service, service.repo, service.project_repo, service.user_repo


def test_create_task_success():
    service, repo, project_repo, user_repo = make_service()
    project_repo.get_by_id.return_value = Project(id=1, name="P")
    user_repo.get_by_id.return_value = User(id=2, name="U", email="u@example.com")
    created = Task(id=10, title="Write tests", project_id=1, assigned_user_id=2)
    repo.create.return_value = created

    result = service.create_task(
        title="Write tests",
        description=None,
        status=TaskStatus.TODO,
        priority=TaskPriority.HIGH,
        project_id=1,
        assigned_user_id=2,
    )

    assert result is created
    repo.create.assert_called_once_with(
        title="Write tests",
        description=None,
        status=TaskStatus.TODO,
        priority=TaskPriority.HIGH,
        project_id=1,
        assigned_user_id=2,
    )
    service.db.commit.assert_called_once()


def test_create_task_nonexistent_project_raises_not_found():
    service, repo, project_repo, user_repo = make_service()
    project_repo.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.create_task(
            title="X",
            description=None,
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            project_id=999,
            assigned_user_id=None,
        )

    repo.create.assert_not_called()
    service.db.commit.assert_not_called()


def test_create_task_nonexistent_assigned_user_raises_not_found():
    service, repo, project_repo, user_repo = make_service()
    project_repo.get_by_id.return_value = Project(id=1, name="P")
    user_repo.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.create_task(
            title="X",
            description=None,
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            project_id=1,
            assigned_user_id=999,
        )

    repo.create.assert_not_called()


def test_get_task_not_found_raises():
    service, repo, _, _ = make_service()
    repo.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.get_task(123)


def test_update_task_applies_partial_fields():
    service, repo, project_repo, user_repo = make_service()
    task = Task(id=5, title="Old", status=TaskStatus.TODO, priority=TaskPriority.LOW, project_id=1)
    repo.get_by_id.return_value = task

    result = service.update_task(5, {"status": TaskStatus.DONE})

    assert result.status == TaskStatus.DONE
    assert result.title == "Old"  # untouched field stays as-is
    service.db.commit.assert_called_once()


def test_update_task_validates_new_project_id():
    service, repo, project_repo, user_repo = make_service()
    task = Task(id=5, title="Old", project_id=1)
    repo.get_by_id.return_value = task
    project_repo.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.update_task(5, {"project_id": 999})

    service.db.commit.assert_not_called()


def test_update_task_validates_new_assigned_user():
    service, repo, project_repo, user_repo = make_service()
    task = Task(id=5, title="Old", project_id=1)
    repo.get_by_id.return_value = task
    user_repo.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.update_task(5, {"assigned_user_id": 999})


def test_update_task_allows_unassigning_with_none():
    service, repo, project_repo, user_repo = make_service()
    task = Task(id=5, title="Old", project_id=1, assigned_user_id=2)
    repo.get_by_id.return_value = task

    result = service.update_task(5, {"assigned_user_id": None})

    assert result.assigned_user_id is None
    user_repo.get_by_id.assert_not_called()


def test_delete_task_not_found_raises():
    service, repo, _, _ = make_service()
    repo.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.delete_task(42)

    repo.delete.assert_not_called()


def test_delete_task_success():
    service, repo, _, _ = make_service()
    task = Task(id=7, title="Gone", project_id=1)
    repo.get_by_id.return_value = task

    service.delete_task(7)

    repo.delete.assert_called_once_with(task)
    service.db.commit.assert_called_once()


def test_list_tasks_delegates_filters_to_repository():
    service, repo, _, _ = make_service()
    repo.list_filtered.return_value = ([], 0)

    service.list_tasks(status=TaskStatus.DONE, priority=TaskPriority.HIGH, project_id=3, limit=10, offset=20)

    repo.list_filtered.assert_called_once_with(
        status=TaskStatus.DONE,
        priority=TaskPriority.HIGH,
        project_id=3,
        assigned_user_id=None,
        sort_by="created_at",
        order="desc",
        limit=10,
        offset=20,
    )
