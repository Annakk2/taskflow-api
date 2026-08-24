from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.task import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    project_id: int
    assigned_user_id: int | None = None


class TaskUpdate(BaseModel):
    """All fields optional — PATCH applies only the fields provided."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    project_id: int | None = None
    assigned_user_id: int | None = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    project_id: int
    assigned_user_id: int | None
    created_at: datetime
    updated_at: datetime


class PaginatedTasks(BaseModel):
    items: list[TaskRead]
    total: int
    limit: int
    offset: int
