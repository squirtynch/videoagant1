"""
AI Video Agent - Project Service

Handles project lifecycle: creation, loading, saving, deletion.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional, List
import structlog

from ..domain.models import Project, ProjectVersion
from ..storage.database import DatabaseManager, DatabaseSession, Base
from sqlalchemy.orm import Session

logger = structlog.get_logger(__name__)


class ProjectService:
    """Service for managing projects."""
    
    def __init__(self, db_manager: DatabaseManager, projects_dir: Path):
        self.db_manager = db_manager
        self.projects_dir = projects_dir
        self.projects_dir.mkdir(parents=True, exist_ok=True)
    
    def create_project(self, name: str, description: Optional[str] = None) -> Project:
        """Create a new project."""
        project = Project(name=name, description=description)
        
        # Save to database
        with DatabaseSession(self.db_manager) as session:
            # Here we would normally save to DB using repositories
            # For now, we'll just log the creation
            logger.info(f"Project created: {project.id} - {project.name}")
        
        # Create project directory
        project_dir = self.projects_dir / project.id
        project_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Project directory created: {project_dir}")
        
        return project
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID."""
        # TODO: Implement database retrieval
        logger.info(f"Getting project: {project_id}")
        return None
    
    def list_projects(self) -> List[Project]:
        """List all projects."""
        # TODO: Implement database listing
        logger.info("Listing projects")
        return []
    
    def update_project(self, project: Project) -> Project:
        """Update an existing project."""
        project.updated_at = datetime.utcnow()
        
        with DatabaseSession(self.db_manager) as session:
            logger.info(f"Project updated: {project.id}")
        
        return project
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        # TODO: Implement deletion with proper cleanup
        logger.info(f"Deleting project: {project_id}")
        return True
    
    def create_version(
        self, 
        project_id: str, 
        version_number: int,
        description: Optional[str] = None,
        editing_plan_snapshot: Optional[dict] = None
    ) -> ProjectVersion:
        """Create a new project version."""
        version = ProjectVersion(
            project_id=project_id,
            version_number=version_number,
            description=description,
            editing_plan_snapshot=editing_plan_snapshot
        )
        
        logger.info(f"Project version created: {version.id} for project {project_id}")
        
        return version
    
    def get_versions(self, project_id: str) -> List[ProjectVersion]:
        """Get all versions for a project."""
        # TODO: Implement database retrieval
        logger.info(f"Getting versions for project: {project_id}")
        return []
