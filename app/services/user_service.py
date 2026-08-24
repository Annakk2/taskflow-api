import logging

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.utils.exceptions import DuplicateError, NotFoundError

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = UserRepository(db)

    def create_user(self, name: str, email: str) -> User:
        if self.repo.get_by_email(email) is not None:
            raise DuplicateError(f"A user with email '{email}' already exists")

        user = self.repo.create(name=name, email=email)
        self.db.commit()
        logger.info("Created user id=%s email=%s", user.id, user.email)
        return user

    def get_user(self, user_id: int) -> User:
        user = self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found")
        return user

    def list_users(self, limit: int = 50, offset: int = 0) -> list[User]:
        return self.repo.list(limit=limit, offset=offset)
