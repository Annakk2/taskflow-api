import logging

from sqlalchemy.orm import Session

from app.models.project import Project
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectStatistics
from app.utils.exceptions import NotFoundError

logger = logging.getLogger(__name__)


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProjectRepository(db)

    def create_project(self, name: str, description: str | None) -> Project:
        project = self.repo.create(name=name, description=description)
        self.db.commit()
        logger.info("Created project id=%s name=%s", project.id, project.name)
        return project

    def get_project(self, project_id: int) -> Project:
        project = self.repo.get_by_id(project_id)
        if project is None:
            raise NotFoundError(f"Project {project_id} not found")
        return project

    def list_projects(self, limit: int = 50, offset: int = 0) -> list[Project]:
        return self.repo.list(limit=limit, offset=offset)

    def get_statistics(self, project_id: int) -> ProjectStatistics:
        # Ensures a 404 for a nonexistent project rather than a silently empty report.
        self.get_project(project_id)

        return ProjectStatistics(
            project_id=project_id,
            total_tasks=self.repo.count_total_tasks(project_id),
            by_status=self.repo.count_tasks_by_status(project_id),
            by_priority=self.repo.count_tasks_by_priority(project_id),
            unassigned_tasks=self.repo.count_unassigned_tasks(project_id),
        )
