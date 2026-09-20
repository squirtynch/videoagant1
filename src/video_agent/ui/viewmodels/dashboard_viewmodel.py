"""Dashboard View Model"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class SystemStatus:
    """System component status."""
    name: str
    status: str  # OK, WARNING, ERROR, NOT_DETECTED, NOT_CONFIGURED
    details: Optional[str] = None
    last_checked: Optional[datetime] = None


@dataclass
class RecentProject:
    """Recent project information for dashboard."""
    id: int
    name: str
    created_at: datetime
    modified_at: datetime
    media_count: int
    status: str  # DRAFT, PROCESSING, COMPLETED
    thumbnail_path: Optional[str] = None


@dataclass
class ActiveJob:
    """Active job information for dashboard."""
    id: int
    project_id: int
    project_name: str
    job_type: str
    status: str  # QUEUED, PROCESSING, VALIDATING, etc.
    progress: float  # 0.0 to 100.0
    started_at: Optional[datetime] = None
    estimated_remaining: Optional[int] = None  # seconds


class DashboardViewModel:
    """View model for Dashboard page."""
    
    def __init__(self, container):
        self.container = container
        self.logger = structlog.get_logger(__name__)
    
    def get_system_status(self) -> List[SystemStatus]:
        """Get status of all system components."""
        statuses = []
        
        # Database status
        try:
            if self.container.db_manager:
                # Test database connection
                self.container.db_manager.engine.connect().close()
                statuses.append(SystemStatus(
                    name="Database",
                    status="OK",
                    details=f"SQLite: {self.container.settings.get_database_path}",
                    last_checked=datetime.now()
                ))
            else:
                statuses.append(SystemStatus(
                    name="Database",
                    status="ERROR",
                    details="Database not initialized",
                    last_checked=datetime.now()
                ))
        except Exception as e:
            self.logger.error(f"Database status check failed: {e}")
            statuses.append(SystemStatus(
                name="Database",
                status="ERROR",
                details=str(e),
                last_checked=datetime.now()
            ))
        
        # FFmpeg status
        ffmpeg_status = self._check_ffmpeg()
        statuses.append(ffmpeg_status)
        
        # DaVinci Resolve status
        resolve_status = self._check_resolve()
        statuses.append(resolve_status)
        
        # AI Providers status
        ai_status = self._check_ai_providers()
        statuses.append(ai_status)
        
        # Disk space status
        disk_status = self._check_disk_space()
        statuses.append(disk_status)
        
        return statuses
    
    def _check_ffmpeg(self) -> SystemStatus:
        """Check FFmpeg availability."""
        try:
            from video_agent.media.ffmpeg import FFmpegWrapper
            ffmpeg = FFmpegWrapper()
            
            if ffmpeg.is_available():
                version = ffmpeg.get_version()
                return SystemStatus(
                    name="FFmpeg",
                    status="OK",
                    details=f"Version: {version}",
                    last_checked=datetime.now()
                )
            else:
                return SystemStatus(
                    name="FFmpeg",
                    status="NOT_DETECTED",
                    details="FFmpeg executable not found",
                    last_checked=datetime.now()
                )
        except Exception as e:
            self.logger.error(f"FFmpeg check failed: {e}")
            return SystemStatus(
                name="FFmpeg",
                status="ERROR",
                details=str(e),
                last_checked=datetime.now()
            )
    
    def _check_resolve(self) -> SystemStatus:
        """Check DaVinci Resolve availability."""
        try:
            # TODO: Implement actual Resolve detection
            # For now, return NOT_DETECTED
            return SystemStatus(
                name="DaVinci Resolve",
                status="NOT_DETECTED",
                details="Resolve integration not yet implemented",
                last_checked=datetime.now()
            )
        except Exception as e:
            self.logger.error(f"Resolve check failed: {e}")
            return SystemStatus(
                name="DaVinci Resolve",
                status="ERROR",
                details=str(e),
                last_checked=datetime.now()
            )
    
    def _check_ai_providers(self) -> SystemStatus:
        """Check AI providers configuration."""
        try:
            # Check if any providers are configured
            # TODO: Implement actual provider health checks
            return SystemStatus(
                name="AI Providers",
                status="NOT_CONFIGURED",
                details="No AI providers configured yet",
                last_checked=datetime.now()
            )
        except Exception as e:
            self.logger.error(f"AI providers check failed: {e}")
            return SystemStatus(
                name="AI Providers",
                status="ERROR",
                details=str(e),
                last_checked=datetime.now()
            )
    
    def _check_disk_space(self) -> SystemStatus:
        """Check available disk space."""
        try:
            import shutil
            
            storage_path = self.container.settings.get_storage_base
            total, used, free = shutil.disk_usage(str(storage_path))
            free_gb = free / (1024 ** 3)
            
            if free_gb < 1:
                status = "WARNING"
                details = f"Low disk space: {free_gb:.1f} GB free"
            elif free_gb < 5:
                status = "WARNING"
                details = f"Moderate disk space: {free_gb:.1f} GB free"
            else:
                status = "OK"
                details = f"{free_gb:.1f} GB free"
            
            return SystemStatus(
                name="Disk Space",
                status=status,
                details=details,
                last_checked=datetime.now()
            )
        except Exception as e:
            self.logger.error(f"Disk space check failed: {e}")
            return SystemStatus(
                name="Disk Space",
                status="ERROR",
                details=str(e),
                last_checked=datetime.now()
            )
    
    def get_recent_projects(self, limit: int = 5) -> List[RecentProject]:
        """Get recent projects for dashboard."""
        try:
            # TODO: Implement actual project retrieval from database
            # For now, return empty list
            return []
        except Exception as e:
            self.logger.error(f"Failed to get recent projects: {e}")
            return []
    
    def get_active_jobs(self) -> List[ActiveJob]:
        """Get active jobs for dashboard."""
        try:
            # TODO: Implement actual job retrieval
            # For now, return empty list
            return []
        except Exception as e:
            self.logger.error(f"Failed to get active jobs: {e}")
            return []
    
    def create_new_project(self, name: str, description: str = "") -> Optional[int]:
        """Create a new project and return its ID."""
        try:
            # TODO: Use ProjectService when implemented
            from video_agent.domain.models import Project
            
            with self.container.db_manager.session_scope() as session:
                project = Project(
                    name=name,
                    description=description,
                    status="DRAFT"
                )
                session.add(project)
                session.flush()  # Get the ID
                
                self.logger.info(f"Created new project: {name} (ID: {project.id})")
                return project.id
        except Exception as e:
            self.logger.error(f"Failed to create project: {e}")
            return None
