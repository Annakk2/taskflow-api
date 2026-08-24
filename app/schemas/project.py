from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    created_at: datetime


class ProjectStatistics(BaseModel):
    project_id: int
    total_tasks: int
    by_status: dict[str, int]
    by_priority: dict[str, int]
    unassigned_tasks: int
