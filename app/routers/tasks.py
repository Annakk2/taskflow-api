from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.task import TaskPriority, TaskStatus
from app.schemas.task import PaginatedTasks, TaskCreate, TaskRead, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])

SortField = Literal["created_at", "updated_at", "priority", "status", "title"]
SortOrder = Literal["asc", "desc"]


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)) -> TaskRead:
    service = TaskService(db)
    task = service.create_task(
        title=payload.title,
        description=payload.description,
        status=payload.status,
        priority=payload.priority,
        project_id=payload.project_id,
        assigned_user_id=payload.assigned_user_id,
    )
    return TaskRead.model_validate(task)


@router.get("", response_model=PaginatedTasks)
def list_tasks(
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    priority: TaskPriority | None = Query(default=None),
    project_id: int | None = Query(default=None),
    assigned_user_id: int | None = Query(default=None),
    sort_by: SortField = Query(default="created_at"),
    order: SortOrder = Query(default="desc"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> PaginatedTasks:
    service = TaskService(db)
    items, total = service.list_tasks(
        status=status_filter,
        priority=priority,
        project_id=project_id,
        assigned_user_id=assigned_user_id,
        sort_by=sort_by,
        order=order,
        limit=limit,
        offset=offset,
    )
    return PaginatedTasks(
        items=[TaskRead.model_validate(t) for t in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: int, db: Session = Depends(get_db)) -> TaskRead:
    service = TaskService(db)
    task = service.get_task(task_id)
    return TaskRead.model_validate(task)


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)) -> TaskRead:
    service = TaskService(db)
    updates = payload.model_dump(exclude_unset=True)
    task = service.update_task(task_id, updates)
    return TaskRead.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)) -> None:
    service = TaskService(db)
    service.delete_task(task_id)
