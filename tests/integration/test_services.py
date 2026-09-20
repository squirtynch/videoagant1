"""
AI Video Agent - Application Layer Tests
"""

import pytest
from pathlib import Path
import tempfile
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from video_agent.domain.models import Project, MediaAsset, Brief, EditingPlan, ExportProfile
from video_agent.storage.database import DatabaseManager
from video_agent.application.project_service import ProjectService
from video_agent.application.media_service import MediaService
from video_agent.application.brief_service import BriefService
from video_agent.application.export_service import ExportService, EXPORT_PROFILES


class TestProjectService:
    """Tests for ProjectService."""
    
    @pytest.fixture
    def project_service(self):
        """Create a test project service."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            projects_dir = Path(tmpdir) / "projects"
            
            db_manager = DatabaseManager(db_path)
            db_manager.initialize()
            
            service = ProjectService(db_manager, projects_dir)
            
            yield service
            
            db_manager.close()
    
    def test_create_project(self, project_service):
        """Test project creation."""
        project = project_service.create_project(
            name="Test Project",
            description="A test project"
        )
        
        assert isinstance(project, Project)
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.id is not None
    
    def test_create_project_directory(self, project_service):
        """Test that project directory is created."""
        project = project_service.create_project(name="Dir Test")
        
        project_dir = project_service.projects_dir / project.id
        assert project_dir.exists()
        assert project_dir.is_dir()


class TestMediaService:
    """Tests for MediaService."""
    
    @pytest.fixture
    def media_service(self):
        """Create a test media service."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            media_dir = Path(tmpdir) / "media"
            
            db_manager = DatabaseManager(db_path)
            db_manager.initialize()
            
            service = MediaService(db_manager, media_dir)
            
            yield service
            
            db_manager.close()
    
    def test_import_media_file_not_found(self, media_service):
        """Test importing non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            media_service.import_media("project-123", "/nonexistent/file.mp4")
    
    def test_import_media_success(self, media_service):
        """Test importing existing file."""
        # Create a test file
        test_file = Path(media_service.media_cache_dir) / "test.mp4"
        test_file.write_bytes(b"fake video content")
        
        asset = media_service.import_media("project-123", str(test_file))
        
        assert isinstance(asset, MediaAsset)
        assert asset.file_name == "test.mp4"
        assert asset.status == "IMPORTED"
        assert asset.project_id == "project-123"


class TestBriefService:
    """Tests for BriefService."""
    
    @pytest.fixture
    def brief_service(self):
        """Create a test brief service."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            
            db_manager = DatabaseManager(db_path)
            db_manager.initialize()
            
            service = BriefService(db_manager)
            
            yield service
            
            db_manager.close()
    
    def test_create_brief(self, brief_service):
        """Test brief creation."""
        brief = brief_service.create_brief(
            project_id="project-123",
            title="Test Brief",
            content="This is a test brief with requirements.",
            source_type="TEXT"
        )
        
        assert brief.title == "Test Brief"
        assert brief.content == "This is a test brief with requirements."
        assert brief.source_type == "TEXT"
        assert brief.project_id == "project-123"


class TestExportService:
    """Tests for ExportService."""
    
    @pytest.fixture
    def export_service(self):
        """Create a test export service."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            renders_dir = Path(tmpdir) / "renders"
            
            db_manager = DatabaseManager(db_path)
            db_manager.initialize()
            
            service = ExportService(db_manager, renders_dir)
            
            yield service
            
            db_manager.close()
    
    def test_export_profiles_exist(self):
        """Test that predefined export profiles exist."""
        assert "youtube_shorts" in EXPORT_PROFILES
        assert "instagram_reels" in EXPORT_PROFILES
        assert "tiktok" in EXPORT_PROFILES
        assert "youtube_landscape" in EXPORT_PROFILES
        assert "square" in EXPORT_PROFILES
    
    def test_get_profile(self, export_service):
        """Test getting export profile."""
        profile = export_service.get_profile("youtube_shorts")
        
        assert profile is not None
        assert profile.name == "YouTube Shorts"
        assert profile.resolution == [1080, 1920]
        assert profile.aspect_ratio == "9:16"
    
    def test_create_export(self, export_service):
        """Test creating an export job."""
        export = export_service.create_export(
            project_id="project-123",
            editing_plan_id="plan-456",
            profile_name="youtube_shorts"
        )
        
        assert export.project_id == "project-123"
        assert export.editing_plan_id == "plan-456"
        assert export.profile.name == "YouTube Shorts"
    
    def test_create_export_invalid_profile(self, export_service):
        """Test creating export with invalid profile."""
        with pytest.raises(ValueError, match="Unknown export profile"):
            export_service.create_export(
                project_id="project-123",
                editing_plan_id="plan-456",
                profile_name="invalid_profile"
            )
    
    def test_list_profiles(self, export_service):
        """Test listing all profiles."""
        profiles = export_service.list_profiles()
        
        assert len(profiles) >= 5  # At least our predefined profiles
        assert any(p.name == "YouTube Shorts" for p in profiles)
        assert any(p.name == "Instagram Reels" for p in profiles)
