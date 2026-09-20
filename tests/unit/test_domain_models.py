"""Unit tests for domain models"""

import pytest
from datetime import datetime
from uuid import UUID

from video_agent.domain.models import (
    JobStatus, QCStatus, RequirementStatus, OperationType, Capability,
    Project, MediaAsset, Transcript, TranscriptSegment,
    EditingPlan, EditingOperation, TimelineConfig,
    ShortCandidate, Job, Brief, BriefRequirement
)


class TestEnums:
    """Test enumeration definitions."""
    
    def test_job_status_values(self):
        """Test JobStatus enum has required values."""
        assert JobStatus.CREATED == "CREATED"
        assert JobStatus.COMPLETED == "COMPLETED"
        assert JobStatus.FAILED == "FAILED"
    
    def test_qc_status_values(self):
        """Test QCStatus enum has required values."""
        assert QCStatus.PASS == "PASS"
        assert QCStatus.FAIL == "FAIL"
        assert QCStatus.WARN == "WARN"
        assert QCStatus.UNKNOWN == "UNKNOWN"
    
    def test_operation_type_values(self):
        """Test OperationType enum has basic operations."""
        assert OperationType.TRIM == "TRIM"
        assert OperationType.CUT == "CUT"
        assert OperationType.ADD_SUBTITLES == "ADD_SUBTITLES"
        assert OperationType.EXPORT == "EXPORT"
    
    def test_capability_values(self):
        """Test Capability enum has required capabilities."""
        assert Capability.TEXT_GENERATION == "TEXT_GENERATION"
        assert Capability.STRUCTURED_OUTPUT == "STRUCTURED_OUTPUT"
        assert Capability.AUDIO_TRANSCRIPTION == "AUDIO_TRANSCRIPTION"


class TestProject:
    """Test Project model."""
    
    def test_create_project_minimal(self):
        """Test creating project with minimal fields."""
        project = Project(name="Test Project")
        
        assert project.name == "Test Project"
        assert project.id is not None
        assert project.version == 1
        assert project.status == "ACTIVE"
        assert isinstance(project.created_at, datetime)
    
    def test_create_project_full(self):
        """Test creating project with all fields."""
        project = Project(
            name="Full Project",
            description="A test project",
            version=2,
            status="ACTIVE"
        )
        
        assert project.name == "Full Project"
        assert project.description == "A test project"
        assert project.version == 2
    
    def test_project_id_is_uuid(self):
        """Test that project ID is a valid UUID."""
        project = Project(name="UUID Test")
        UUID(project.id)  # Should not raise


class TestMediaAsset:
    """Test MediaAsset model."""
    
    def test_create_media_asset(self):
        """Test creating media asset."""
        asset = MediaAsset(
            project_id="proj-123",
            file_path="/path/to/video.mp4",
            file_name="video.mp4",
            file_size=1024000
        )
        
        assert asset.file_path == "/path/to/video.mp4"
        assert asset.file_name == "video.mp4"
        assert asset.file_size == 1024000
        assert asset.has_audio == False
        assert asset.status == "IMPORTED"
    
    def test_media_asset_with_metadata(self):
        """Test media asset with metadata."""
        asset = MediaAsset(
            project_id="proj-123",
            file_path="/path/to/video.mp4",
            file_name="video.mp4",
            file_size=1024000,
            duration=120.5,
            width=1920,
            height=1080,
            fps=30.0,
            codec="h264",
            has_audio=True
        )
        
        assert asset.duration == 120.5
        assert asset.width == 1920
        assert asset.height == 1080
        assert asset.fps == 30.0
        assert asset.has_audio == True


class TestTranscript:
    """Test Transcript model."""
    
    def test_create_transcript(self):
        """Test creating transcript."""
        transcript = Transcript(
            media_asset_id="asset-123",
            duration=60.0,
            language="en"
        )
        
        assert transcript.media_asset_id == "asset-123"
        assert transcript.duration == 60.0
        assert transcript.language == "en"
    
    def test_transcript_with_segments(self):
        """Test transcript with segments."""
        segment = TranscriptSegment(
            start=0.0,
            end=5.0,
            text="Hello world",
            confidence=0.95
        )
        
        transcript = Transcript(
            media_asset_id="asset-123",
            duration=60.0,
            segments=[segment]
        )
        
        assert len(transcript.segments) == 1
        assert transcript.segments[0].text == "Hello world"
        assert transcript.segments[0].start == 0.0
        assert transcript.segments[0].end == 5.0


class TestEditingPlan:
    """Test EditingPlan model."""
    
    def test_create_editing_plan(self):
        """Test creating editing plan."""
        plan = EditingPlan(project_id="proj-123")
        
        assert plan.project_id == "proj-123"
        assert plan.schema_version == "1.0"
        assert plan.status == "DRAFT"
        assert plan.version == 1
        assert len(plan.operations) == 0
    
    def test_editing_plan_with_operations(self):
        """Test editing plan with operations."""
        op1 = EditingOperation(
            operation_type=OperationType.TRIM,
            source_asset="asset-123",
            start=10.0,
            end=20.0
        )
        
        plan = EditingPlan(
            project_id="proj-123",
            operations=[op1]
        )
        
        assert len(plan.operations) == 1
        assert plan.operations[0].operation_type == OperationType.TRIM
        assert plan.operations[0].start == 10.0
        assert plan.operations[0].end == 20.0
    
    def test_timeline_config(self):
        """Test timeline configuration."""
        plan = EditingPlan(
            project_id="proj-123",
            timeline=TimelineConfig(
                fps=60.0,
                resolution=[1080, 1920],
                aspect_ratio="9:16"
            )
        )
        
        assert plan.timeline.fps == 60.0
        assert plan.timeline.resolution == [1080, 1920]
        assert plan.timeline.aspect_ratio == "9:16"


class TestShortCandidate:
    """Test ShortCandidate model."""
    
    def test_create_candidate(self):
        """Test creating short candidate."""
        candidate = ShortCandidate(
            source_asset="asset-123",
            start=30.0,
            end=60.0,
            confidence=0.85
        )
        
        assert candidate.source_asset == "asset-123"
        assert candidate.start == 30.0
        assert candidate.end == 60.0
        assert candidate.confidence == 0.85
    
    def test_candidate_with_rationale(self):
        """Test candidate with selection rationale."""
        candidate = ShortCandidate(
            source_asset="asset-123",
            start=30.0,
            end=60.0,
            hook="Strong opening statement",
            selection_rationale="High engagement potential",
            confidence=0.85
        )
        
        assert candidate.hook == "Strong opening statement"
        assert candidate.selection_rationale == "High engagement potential"


class TestJob:
    """Test Job model."""
    
    def test_create_job(self):
        """Test creating job."""
        job = Job(
            project_id="proj-123",
            job_type="TRANSCRIBE"
        )
        
        assert job.project_id == "proj-123"
        assert job.job_type == "TRANSCRIBE"
        assert job.status == JobStatus.CREATED
        assert job.progress == 0.0
        assert job.retry_count == 0
        assert job.max_retries == 3
    
    def test_job_status_transitions(self):
        """Test job status transitions."""
        job = Job(
            project_id="proj-123",
            job_type="RENDER"
        )
        
        assert job.status == JobStatus.CREATED
        
        job.status = JobStatus.PROCESSING
        assert job.status == JobStatus.PROCESSING
        
        job.status = JobStatus.COMPLETED
        assert job.status == JobStatus.COMPLETED


class TestBrief:
    """Test Brief model."""
    
    def test_create_brief(self):
        """Test creating brief."""
        brief = Brief(
            project_id="proj-123",
            title="Test Brief",
            content="This is a test brief"
        )
        
        assert brief.title == "Test Brief"
        assert brief.content == "This is a test brief"
        assert brief.source_type == "TEXT"
        assert len(brief.requirements) == 0
    
    def test_brief_with_requirements(self):
        """Test brief with requirements."""
        req = BriefRequirement(
            brief_id="brief-123",
            description="Must include intro",
            category="STRUCTURE"
        )
        
        brief = Brief(
            project_id="proj-123",
            title="Brief with Requirements",
            content="Content here",
            requirements=[req]
        )
        
        assert len(brief.requirements) == 1
        assert brief.requirements[0].description == "Must include intro"
        assert brief.requirements[0].status == RequirementStatus.REQUIRES_HUMAN_REVIEW
