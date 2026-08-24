"""Unit tests for UserService business logic, isolated from the database via mocks."""

from unittest.mock import MagicMock

import pytest

from app.models.user import User
from app.services.user_service import UserService
from app.utils.exceptions import DuplicateError, NotFoundError


def make_service() -> tuple[UserService, MagicMock]:
    db = MagicMock()
    service = UserService(db)
    service.repo = MagicMock()
    return service, service.repo


def test_create_user_success():
    service, repo = make_service()
    repo.get_by_email.return_value = None
    created = User(id=1, name="Ana", email="ana@example.com")
    repo.create.return_value = created

    result = service.create_user("Ana", "ana@example.com")

    assert result is created
    service.db.commit.assert_called_once()


def test_create_user_duplicate_email_raises():
    service, repo = make_service()
    repo.get_by_email.return_value = User(id=1, name="Existing", email="ana@example.com")

    with pytest.raises(DuplicateError):
        service.create_user("Ana", "ana@example.com")

    repo.create.assert_not_called()
    service.db.commit.assert_not_called()


def test_get_user_not_found_raises():
    service, repo = make_service()
    repo.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.get_user(999)


def test_list_users_delegates_to_repository():
    service, repo = make_service()
    repo.list.return_value = []

    service.list_users(limit=25, offset=5)

    repo.list.assert_called_once_with(limit=25, offset=5)
