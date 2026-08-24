from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.task import Task


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, name: str, description: str | None) -> Project:
        project = Project(name=name, description=description)
        self.db.add(project)
        self.db.flush()
        self.db.refresh(project)
        return project

    def get_by_id(self, project_id: int) -> Project | None:
        return self.db.get(Project, project_id)

    def list(self, limit: int = 50, offset: int = 0) -> list[Project]:
        stmt = select(Project).order_by(Project.id).limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars().all())

    def count_tasks_by_status(self, project_id: int) -> dict[str, int]:
        stmt = (
            select(Task.status, func.count(Task.id))
            .where(Task.project_id == project_id)
            .group_by(Task.status)
        )
        return {status.value: count for status, count in self.db.execute(stmt).all()}

    def count_tasks_by_priority(self, project_id: int) -> dict[str, int]:
        stmt = (
            select(Task.priority, func.count(Task.id))
            .where(Task.project_id == project_id)
            .group_by(Task.priority)
        )
        return {priority.value: count for priority, count in self.db.execute(stmt).all()}

    def count_total_tasks(self, project_id: int) -> int:
        stmt = select(func.count(Task.id)).where(Task.project_id == project_id)
        return self.db.execute(stmt).scalar_one()

    def count_unassigned_tasks(self, project_id: int) -> int:
        stmt = select(func.count(Task.id)).where(
            Task.project_id == project_id, Task.assigned_user_id.is_(None)
        )
        return self.db.execute(stmt).scalar_one()
