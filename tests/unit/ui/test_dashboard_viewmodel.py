"""Tests for Dashboard ViewModel"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from video_agent.ui.viewmodels.dashboard_viewmodel import (
    DashboardViewModel,
    SystemStatus,
    RecentProject,
    ActiveJob,
)


class TestSystemStatus:
    """Test SystemStatus dataclass."""
    
    def test_create_system_status_minimal(self):
        """Test creating SystemStatus with minimal fields."""
        status = SystemStatus(name="Test", status="OK")
        
        assert status.name == "Test"
        assert status.status == "OK"
        assert status.details is None
        assert status.last_checked is None
    
    def test_create_system_status_full(self):
        """Test creating SystemStatus with all fields."""
        now = datetime.now()
        status = SystemStatus(
            name="Database",
            status="OK",
            details="SQLite connection successful",
            last_checked=now
        )
        
        assert status.name == "Database"
        assert status.status == "OK"
        assert status.details == "SQLite connection successful"
        assert status.last_checked == now


class TestRecentProject:
    """Test RecentProject dataclass."""
    
    def test_create_recent_project(self):
        """Test creating RecentProject."""
        now = datetime.now()
        project = RecentProject(
            id=1,
            name="Test Project",
            created_at=now,
            modified_at=now,
            media_count=5,
            status="DRAFT"
        )
        
        assert project.id == 1
        assert project.name == "Test Project"
        assert project.media_count == 5
        assert project.status == "DRAFT"
        assert project.thumbnail_path is None


class TestActiveJob:
    """Test ActiveJob dataclass."""
    
    def test_create_active_job(self):
        """Test creating ActiveJob."""
        job = ActiveJob(
            id=1,
            project_id=10,
            project_name="Test Project",
            job_type="TRANSCRIBE",
            status="PROCESSING",
            progress=45.5
        )
        
        assert job.id == 1
        assert job.project_id == 10
        assert job.job_type == "TRANSCRIBE"
        assert job.status == "PROCESSING"
        assert job.progress == 45.5
        assert job.started_at is None
        assert job.estimated_remaining is None


class TestDashboardViewModel:
    """Test DashboardViewModel functionality."""
    
    @pytest.fixture
    def mock_container(self):
        """Create a mock container."""
        container = Mock()
        container.settings = Mock()
        container.settings.get_storage_base = "/tmp/test_storage"
        container.settings.get_database_path = "/tmp/test.db"
        container.db_manager = Mock()
        container.logger = Mock()
        return container
    
    def test_init(self, mock_container):
        """Test ViewModel initialization."""
        vm = DashboardViewModel(mock_container)
        
        assert vm.container == mock_container
        assert vm.logger is not None
    
    def test_get_system_status_database_ok(self, mock_container):
        """Test getting system status when database is OK."""
        # Mock database connection test
        mock_connection = Mock()
        mock_container.db_manager.engine.connect.return_value = mock_connection
        
        vm = DashboardViewModel(mock_container)
        statuses = vm.get_system_status()
        
        # Should have at least database status
        db_status = next((s for s in statuses if s.name == "Database"), None)
        assert db_status is not None
        assert db_status.status == "OK"
    
    def test_get_system_status_database_error(self, mock_container):
        """Test getting system status when database has error."""
        # Mock database connection failure
        mock_container.db_manager.engine.connect.side_effect = Exception("Connection failed")
        
        vm = DashboardViewModel(mock_container)
        statuses = vm.get_system_status()
        
        db_status = next((s for s in statuses if s.name == "Database"), None)
        assert db_status is not None
        assert db_status.status == "ERROR"
    
    def test_check_disk_space_ok(self, mock_container):
        """Test disk space check when space is sufficient."""
        with patch('shutil.disk_usage') as mock_disk:
            # Mock 100 GB total, 50 GB used, 50 GB free
            mock_disk.return_value = (100 * 1024**3, 50 * 1024**3, 50 * 1024**3)
            
            vm = DashboardViewModel(mock_container)
            statuses = vm.get_system_status()
            
            disk_status = next((s for s in statuses if s.name == "Disk Space"), None)
            assert disk_status is not None
            assert disk_status.status == "OK"
            assert "GB free" in disk_status.details
    
    def test_check_disk_space_warning(self, mock_container):
        """Test disk space check when space is low."""
        with patch('shutil.disk_usage') as mock_disk:
            # Mock 100 GB total, 99.5 GB used, 0.5 GB free
            mock_disk.return_value = (100 * 1024**3, 99.5 * 1024**3, 0.5 * 1024**3)
            
            vm = DashboardViewModel(mock_container)
            statuses = vm.get_system_status()
            
            disk_status = next((s for s in statuses if s.name == "Disk Space"), None)
            assert disk_status is not None
            assert disk_status.status == "WARNING"
    
    def test_get_recent_projects_empty(self, mock_container):
        """Test getting recent projects when none exist."""
        vm = DashboardViewModel(mock_container)
        projects = vm.get_recent_projects()
        
        assert projects == []
    
    def test_get_active_jobs_empty(self, mock_container):
        """Test getting active jobs when none exist."""
        vm = DashboardViewModel(mock_container)
        jobs = vm.get_active_jobs()
        
        assert jobs == []
    
    def test_create_new_project_success(self, mock_container):
        """Test creating a new project successfully."""
        with patch.object(mock_container.db_manager, 'session_scope') as mock_scope:
            mock_session = Mock()
            mock_scope.return_value.__enter__ = Mock(return_value=mock_session)
            mock_scope.return_value.__exit__ = Mock(return_value=None)
            
            # Mock the flush to set an ID
            def set_id():
                pass
            
            mock_session.flush = Mock(side_effect=set_id)
            
            vm = DashboardViewModel(mock_container)
            project_id = vm.create_new_project("Test Project", "Test Description")
            
            # Should return a UUID string (project.id is a UUID)
            assert project_id is not None
            assert isinstance(project_id, str)
    
    def test_create_new_project_empty_name(self, mock_container):
        """Test creating a project with empty name."""
        vm = DashboardViewModel(mock_container)
        project_id = vm.create_new_project("", "")
        
        # Empty name should be handled gracefully
        assert project_id is None or isinstance(project_id, int)
    
    def test_create_new_project_error(self, mock_container):
        """Test creating a project when error occurs."""
        with patch.object(mock_container.db_manager, 'session_scope') as mock_scope:
            mock_scope.side_effect = Exception("Database error")
            
            vm = DashboardViewModel(mock_container)
            project_id = vm.create_new_project("Test Project")
            
            assert project_id is None
