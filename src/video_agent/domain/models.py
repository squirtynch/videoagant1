"""
AI Video Agent - Domain Models

Core business entities that represent the problem domain.
These models are independent of frameworks and external concerns.
"""

from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    PREPARING = "PREPARING"
    PROCESSING = "PROCESSING"
    VALIDATING = "VALIDATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    CANCELLED = "CANCELLED"
    RECOVERABLE = "RECOVERABLE"


class QCStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class RequirementStatus(str, Enum):
    AUTOMATICALLY_VERIFIABLE = "AUTOMATICALLY_VERIFIABLE"
    PARTIALLY_VERIFIABLE = "PARTIALLY_VERIFIABLE"
    REQUIRES_HUMAN_REVIEW = "REQUIRES_HUMAN_REVIEW"
    NOT_SUPPORTED = "NOT_SUPPORTED"


class OperationType(str, Enum):
    CUT = "CUT"
    TRIM = "TRIM"
    SPLIT = "SPLIT"
    REMOVE_SEGMENT = "REMOVE_SEGMENT"
    REORDER = "REORDER"
    CROP = "CROP"
    REFRAME = "REFRAME"
    ADD_SUBTITLES = "ADD_SUBTITLES"
    ADD_AUDIO = "ADD_AUDIO"
    EXPORT = "EXPORT"
    # Future operations
    ADD_BROLL = "ADD_BROLL"
    ZOOM = "ZOOM"
    TRANSITION = "TRANSITION"
    AUDIO_DUCKING = "AUDIO_DUCKING"
    NORMALIZE_AUDIO = "NORMALIZE_AUDIO"
    SILENCE_REMOVAL = "SILENCE_REMOVAL"
    MULTICAM = "MULTICAM"
    COLOR_ADJUSTMENT = "COLOR_ADJUSTMENT"


class Capability(str, Enum):
    TEXT_GENERATION = "TEXT_GENERATION"
    STRUCTURED_OUTPUT = "STRUCTURED_OUTPUT"
    TOOL_CALLING = "TOOL_CALLING"
    VISION_ANALYSIS = "VISION_ANALYSIS"
    VIDEO_ANALYSIS = "VIDEO_ANALYSIS"
    AUDIO_ANALYSIS = "AUDIO_ANALYSIS"
    AUDIO_TRANSCRIPTION = "AUDIO_TRANSCRIPTION"
    EMBEDDINGS = "EMBEDDINGS"


# ============================================================================
# Project Domain
# ============================================================================

class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1
    status: str = "ACTIVE"
    
    class Config:
        arbitrary_types_allowed = True


class ProjectVersion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    version_number: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    description: Optional[str] = None
    editing_plan_snapshot: Optional[Dict[str, Any]] = None


# ============================================================================
# Media Domain
# ============================================================================

class MediaAsset(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    file_path: str
    file_name: str
    file_size: int
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    codec: Optional[str] = None
    audio_codec: Optional[str] = None
    has_audio: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "IMPORTED"
    
    class Config:
        arbitrary_types_allowed = True


class MediaAnalysis(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    media_asset_id: str
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    scenes: List[Dict[str, Any]] = Field(default_factory=list)
    keyframes: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str
    confidence: Optional[float] = None


class Transcript(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    media_asset_id: str
    language: str = "en"
    duration: float
    segments: List[TranscriptSegment] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    provider: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True


# ============================================================================
# Brief Domain
# ============================================================================

class BriefRequirement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    brief_id: str
    description: str
    category: str
    status: RequirementStatus = RequirementStatus.REQUIRES_HUMAN_REVIEW
    verified: bool = False
    verification_notes: Optional[str] = None


class Brief(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    title: str
    content: str
    source_type: str = "TEXT"  # TEXT, MARKDOWN, DOCX, PDF
    created_at: datetime = Field(default_factory=datetime.utcnow)
    requirements: List[BriefRequirement] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True


# ============================================================================
# Editing Plan Domain
# ============================================================================

class EditingOperation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    operation_type: OperationType
    source_asset: Optional[str] = None
    source_operation: Optional[str] = None
    start: Optional[float] = None
    end: Optional[float] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    status: str = "PENDING"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TimelineConfig(BaseModel):
    fps: float = 30.0
    resolution: List[int] = [1080, 1920]
    aspect_ratio: str = "9:16"


class EditingPlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    schema_version: str = "1.0"
    project_id: str
    name: Optional[str] = None
    timeline: TimelineConfig = Field(default_factory=TimelineConfig)
    operations: List[EditingOperation] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "DRAFT"
    version: int = 1
    
    class Config:
        arbitrary_types_allowed = True


# ============================================================================
# Short Maker Domain
# ============================================================================

class ShortCandidate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    source_asset: str
    start: float
    end: float
    transcript: Optional[str] = None
    hook: Optional[str] = None
    selection_rationale: Optional[str] = None
    confidence: float = 0.0
    editing_plan: Optional[EditingPlan] = None
    subtitle_plan: Optional[Dict[str, Any]] = None
    crop_plan: Optional[Dict[str, Any]] = None
    export_settings: Optional[Dict[str, Any]] = None
    
    class Config:
        arbitrary_types_allowed = True


# ============================================================================
# Job Domain
# ============================================================================

class JobEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    job_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str
    message: str
    details: Optional[Dict[str, Any]] = None


class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    job_type: str
    status: JobStatus = JobStatus.CREATED
    progress: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    events: List[JobEvent] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True


# ============================================================================
# Export Domain
# ============================================================================

class ExportProfile(BaseModel):
    name: str
    resolution: List[int]
    aspect_ratio: str
    codec: str
    bitrate: Optional[str] = None
    fps: float
    audio_codec: str = "aac"
    audio_bitrate: str = "192k"
    duration_constraints: Optional[Dict[str, Any]] = None
    filename_rules: Optional[Dict[str, Any]] = None


class Export(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    editing_plan_id: str
    profile: ExportProfile
    output_path: Optional[str] = None
    status: str = "PENDING"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    qc_status: Optional[QCStatus] = None
    qc_report: Optional[Dict[str, Any]] = None
    
    class Config:
        arbitrary_types_allowed = True


# ============================================================================
# AI Provider Domain
# ============================================================================

class ModelProvider(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    provider_type: str  # OPENAI, LOCAL, MOCK
    endpoint: Optional[str] = None
    api_key_ref: Optional[str] = None
    enabled: bool = True
    health_status: str = "UNKNOWN"
    last_checked: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True


class ModelConfiguration(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    provider_id: str
    model_identifier: str
    name: str
    capabilities: List[Capability] = Field(default_factory=list)
    context_limit: int = 4096
    enabled: bool = True
    
    class Config:
        arbitrary_types_allowed = True
