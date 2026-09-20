# AI Video Agent Architecture

## Overview

AI Video Agent is a Windows desktop application for AI-powered video editing automation with DaVinci Resolve Studio integration.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     UI Layer (PySide6)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │Dashboard │ │ Projects │ │ShortMaker│ │ Assistant│       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Application Services                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Project  │ │  Media   │ │ Editing  │ │  Export  │       │
│  │ Service  │ │ Service  │ │ Service  │ │ Service  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │  Brief   │ │  Short   │ │   Job    │                    │
│  │ Service  │ │ Service  │ │ Manager  │                    │
│  └──────────┘ └──────────┘ └──────────┘                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Domain Layer                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Project  │ │  Media   │ │  Brief   │ │  Editing │       │
│  │          │ │  Asset   │ │          │ │   Plan   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │   Job    │ │ Transcript│ │Candidate │ │  Export  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ SQLite   │ │  FFmpeg  │ │AI Provider│ │ Resolve  │       │
│  │ Database │ │ Wrapper  │ │ Registry │ │ Adapter  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │Filesystem│ │Transcrip-│ │  Secrets │                    │
│  │          │ │ tion     │ │ Storage  │                    │
│  └──────────┘ └──────────┘ └──────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Principles

### 1. Separation of Concerns

- **UI Layer**: PySide6 widgets and views, no business logic
- **Application Layer**: Use cases and orchestration
- **Domain Layer**: Business entities and rules
- **Infrastructure Layer**: External system integrations

### 2. AI Safety

AI models NEVER directly execute:
- Shell commands
- File system operations
- FFmpeg calls
- DaVinci Resolve scripting

Instead, AI produces structured `EditingPlan` objects that are:
1. Validated against schema
2. Checked for security constraints
3. Verified for capability availability
4. Executed by controlled infrastructure layer

### 3. Local-First Design

All data stored locally:
- SQLite database for metadata
- Filesystem for media and renders
- Optional cloud sync (future)

### 4. Job-Based Processing

Long-running operations use job queue:
- Non-blocking UI
- Progress tracking
- Cancellation support
- Error recovery
- Retry logic

## Core Components

### Domain Models

Located in `src/video_agent/domain/`:

- `Project`: Top-level container
- `MediaAsset`: Imported video/audio files
- `Transcript`: Speech-to-text results with timestamps
- `Brief`: User requirements document
- `EditingPlan`: Structured edit instructions
- `ShortCandidate`: Potential short-form content
- `Job`: Background processing task
- `Export`: Rendered output

### Application Services

Located in `src/video_agent/application/`:

- `ProjectService`: CRUD operations for projects
- `MediaService`: Import, analyze, manage media
- `BriefService`: Parse and extract requirements
- `ShortService`: Generate short-form candidates
- `EditingService`: Execute editing plans
- `ExportService`: Render and export videos

### AI Provider System

Located in `src/video_agent/ai/`:

**Provider Types:**
- OpenAI-compatible HTTP API
- Local HTTP endpoint (Ollama, LM Studio, etc.)
- Mock provider for testing

**Capabilities:**
- `TEXT_GENERATION`: General text output
- `STRUCTURED_OUTPUT`: JSON/schema-constrained output
- `TOOL_CALLING`: Function/tool invocation
- `VISION_ANALYSIS`: Image understanding
- `VIDEO_ANALYSIS`: Video content analysis
- `AUDIO_TRANSCRIPTION`: Speech-to-text

**Safety Features:**
- Whitelisted tools only
- No arbitrary code execution
- Structured output validation
- Capability health checks

### Media Engine

Located in `src/video_agent/media/`:

**FFmpeg Wrapper:**
- Safe argument passing (no shell injection)
- Progress monitoring
- Error handling
- Resource cleanup

**Operations:**
- Metadata extraction
- Transcoding
- Trimming/cutting
- Concatenation
- Audio processing
- Subtitle rendering
- Thumbnail generation

### DaVinci Resolve Integration

Located in `src/video_agent/resolve/`:

**Components:**
- `ResolveAdapter`: Main interface
- `ResolveConnection`: Connection management
- `ResolveCapabilityProbe`: Feature detection
- `ResolveTimeline`: Timeline operations

**Supported Operations (verified):**
- Detect Resolve installation
- Connect to running instance
- Get project information
- Create/get timeline
- Import media
- Basic clip placement

**Not Promised Until Tested:**
- Advanced transitions
- Color grading
- Audio mixing
- Effects

## Data Flow Examples

### Short Creation Flow

```
User Input (video + settings)
    ↓
Media Analysis (FFmpeg)
    ↓
Transcription (AI Provider)
    ↓
Segmentation (Domain Logic)
    ↓
Candidate Generation (AI)
    ↓
Candidate Scoring (Algorithm)
    ↓
User Review (UI)
    ↓
Editing Plan Creation (AI)
    ↓
Plan Validation (Validator)
    ↓
Execution (FFmpeg/Resolve)
    ↓
QC Check (QC Layer)
    ↓
Export (Media Engine)
```

### Brief-to-Edit Flow

```
User Input (brief + media)
    ↓
Requirement Extraction (AI)
    ↓
Requirement Classification (Domain)
    ↓
Media Analysis (FFmpeg + AI)
    ↓
Editing Plan Generation (AI)
    ↓
Plan Validation (Validator)
    ↓
User Approval (UI)
    ↓
Execution (Editing Engine)
    ↓
Compliance Report (QC)
    ↓
Export or Send to Resolve
```

## Security Model

### Credential Storage

- Windows Credential Manager (primary)
- DPAPI fallback
- Never in plaintext config files

### File Security

- Path validation
- Existence checks
- Format verification
- No arbitrary filesystem access from AI

### AI Tool Restrictions

Whitelisted tools only:
- `list_project_media`
- `get_media_metadata`
- `get_transcript`
- `search_transcript`
- `find_scenes`
- `create_editing_plan`
- `validate_editing_plan`
- `render_preview`
- `export_video`
- `check_resolve`
- `create_resolve_timeline`
- `check_brief_compliance`

## Testing Strategy

### Unit Tests

- Domain model validation
- Schema validation
- Timecode calculations
- Parsing logic
- Routing decisions

### Integration Tests

- FFmpeg wrapper
- SQLite operations
- AI endpoint communication
- Transcription pipeline
- Resolve connection (when available)

### E2E Tests

Full workflow tests:
```
Import → Analyze → Transcribe → Candidate → Plan → Render → Export
```

### Failure Tests

- API unavailable
- Malformed responses
- Invalid plans
- Corrupted media
- Insufficient disk space
- Cancellation
- Timeout
- Network loss
- Application restart

## Build & Deployment

### Development

```bash
pip install -e .
python -m video_agent.main
```

### Production Build

GitHub Actions on Windows runner:
1. Install Python 3.12
2. Install dependencies
3. Run tests
4. PyInstaller build
5. Inno Setup installer
6. GitHub Release

### Artifacts

- `AI-Video-Agent.exe` (portable)
- `AI-Video-Agent-Setup-vX.Y.Z.exe` (installer)
- `checksums.txt` (SHA256 hashes)

## Versioning

Semantic Versioning: `MAJOR.MINOR.PATCH`

- `MAJOR`: Breaking changes
- `MINOR`: New features (backward compatible)
- `PATCH`: Bug fixes

## Future Extensions

### Planned Features

- Multi-cam editing
- Color adjustment
- Audio ducking
- B-roll insertion
- Transition library
- Custom effects
- Cloud storage sync
- Collaboration features

### Provider Extensions

- Additional AI providers
- Local Whisper transcription
- Embedding models
- RAG integration

### Resolve Integration

- Advanced timeline operations
- Fairlight audio
- Color page integration
- Fusion effects
