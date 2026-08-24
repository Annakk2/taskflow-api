from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.project import ProjectCreate, ProjectRead, ProjectStatistics
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> ProjectRead:
    service = ProjectService(db)
    project = service.create_project(name=payload.name, description=payload.description)
    return ProjectRead.model_validate(project)


@router.get("", response_model=list[ProjectRead])
def list_projects(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[ProjectRead]:
    service = ProjectService(db)
    projects = service.list_projects(limit=limit, offset=offset)
    return [ProjectRead.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, db: Session = Depends(get_db)) -> ProjectRead:
    service = ProjectService(db)
    project = service.get_project(project_id)
    return ProjectRead.model_validate(project)


@router.get("/{project_id}/statistics", response_model=ProjectStatistics)
def get_project_statistics(project_id: int, db: Session = Depends(get_db)) -> ProjectStatistics:
    service = ProjectService(db)
    return service.get_statistics(project_id)
