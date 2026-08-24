"""Unit tests for ProjectService business logic, isolated from the database via mocks."""

from unittest.mock import MagicMock

import pytest

from app.models.project import Project
from app.services.project_service import ProjectService
from app.utils.exceptions import NotFoundError


def make_service() -> tuple[ProjectService, MagicMock]:
    db = MagicMock()
    service = ProjectService(db)
    service.repo = MagicMock()
    return service, service.repo


def test_get_project_not_found_raises():
    service, repo = make_service()
    repo.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.get_project(404)


def test_get_statistics_not_found_raises_before_querying_counts():
    service, repo = make_service()
    repo.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.get_statistics(404)

    repo.count_total_tasks.assert_not_called()


def test_get_statistics_success_aggregates_repository_data():
    service, repo = make_service()
    repo.get_by_id.return_value = Project(id=1, name="P")
    repo.count_total_tasks.return_value = 5
    repo.count_tasks_by_status.return_value = {"todo": 3, "done": 2}
    repo.count_tasks_by_priority.return_value = {"high": 1, "medium": 4}
    repo.count_unassigned_tasks.return_value = 2

    stats = service.get_statistics(1)

    assert stats.project_id == 1
    assert stats.total_tasks == 5
    assert stats.by_status == {"todo": 3, "done": 2}
    assert stats.by_priority == {"high": 1, "medium": 4}
    assert stats.unassigned_tasks == 2
