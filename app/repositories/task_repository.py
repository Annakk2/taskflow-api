from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.models.task import Task, TaskPriority, TaskStatus

_SORTABLE_FIELDS = {
    "created_at": Task.created_at,
    "updated_at": Task.updated_at,
    "priority": Task.priority,
    "status": Task.status,
    "title": Task.title,
}


class TaskRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, **fields) -> Task:
        task = Task(**fields)
        self.db.add(task)
        self.db.flush()
        self.db.refresh(task)
        return task

    def get_by_id(self, task_id: int) -> Task | None:
        return self.db.get(Task, task_id)

    def delete(self, task: Task) -> None:
        self.db.delete(task)
        self.db.flush()

    def list_filtered(
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
        conditions = []
        if status is not None:
            conditions.append(Task.status == status)
        if priority is not None:
            conditions.append(Task.priority == priority)
        if project_id is not None:
            conditions.append(Task.project_id == project_id)
        if assigned_user_id is not None:
            conditions.append(Task.assigned_user_id == assigned_user_id)

        count_stmt = select(func.count(Task.id))
        for condition in conditions:
            count_stmt = count_stmt.where(condition)
        total = self.db.execute(count_stmt).scalar_one()

        sort_column = _SORTABLE_FIELDS.get(sort_by, Task.created_at)
        direction = desc if order == "desc" else asc

        stmt = select(Task)
        for condition in conditions:
            stmt = stmt.where(condition)
        stmt = stmt.order_by(direction(sort_column)).limit(limit).offset(offset)

        items = list(self.db.execute(stmt).scalars().all())
        return items, total
