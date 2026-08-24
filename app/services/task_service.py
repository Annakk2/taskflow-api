import logging

from sqlalchemy.orm import Session

from app.metrics import metrics
from app.models.task import Task, TaskPriority, TaskStatus
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.utils.exceptions import NotFoundError

logger = logging.getLogger(__name__)


class TaskService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = TaskRepository(db)
        self.project_repo = ProjectRepository(db)
        self.user_repo = UserRepository(db)

    def _validate_project(self, project_id: int) -> None:
        if self.project_repo.get_by_id(project_id) is None:
            raise NotFoundError(f"Project {project_id} not found")

    def _validate_assigned_user(self, assigned_user_id: int | None) -> None:
        if assigned_user_id is not None and self.user_repo.get_by_id(assigned_user_id) is None:
            raise NotFoundError(f"User {assigned_user_id} not found")

    def create_task(
        self,
        title: str,
        description: str | None,
        status: TaskStatus,
        priority: TaskPriority,
        project_id: int,
        assigned_user_id: int | None,
    ) -> Task:
        self._validate_project(project_id)
        self._validate_assigned_user(assigned_user_id)

        task = self.repo.create(
            title=title,
            description=description,
            status=status,
            priority=priority,
            project_id=project_id,
            assigned_user_id=assigned_user_id,
        )
        self.db.commit()
        metrics.record_task_created()
        logger.info("Created task id=%s project_id=%s", task.id, task.project_id)
        return task

    def get_task(self, task_id: int) -> Task:
        task = self.repo.get_by_id(task_id)
        if task is None:
            raise NotFoundError(f"Task {task_id} not found")
        return task

    def update_task(self, task_id: int, updates: dict) -> Task:
        task = self.get_task(task_id)

        if "project_id" in updates and updates["project_id"] is not None:
            self._validate_project(updates["project_id"])
        if "assigned_user_id" in updates:
            self._validate_assigned_user(updates["assigned_user_id"])

        for field, value in updates.items():
            setattr(task, field, value)

        self.db.commit()
        self.db.refresh(task)
        logger.info("Updated task id=%s fields=%s", task.id, list(updates.keys()))
        return task

    def delete_task(self, task_id: int) -> None:
        task = self.get_task(task_id)
        self.repo.delete(task)
        self.db.commit()
        logger.info("Deleted task id=%s", task_id)

    def list_tasks(
        self,
        *,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        project_id: int | None = None,
        assigned_user_id: int | None = None,
        sort_by: str = "created_at",
        order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Task], int]:
        return self.repo.list_filtered(
            status=status,
            priority=priority,
            project_id=project_id,
            assigned_user_id=assigned_user_id,
            sort_by=sort_by,
            order=order,
            limit=limit,
            offset=offset,
        )
