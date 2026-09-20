# Build Instructions

## Development Setup

### Prerequisites

- Python 3.12 or higher
- Git
- FFmpeg (optional for media processing)
- DaVinci Resolve Studio 18+ (optional for timeline integration)

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/ai-video-agent.git
cd ai-video-agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install in development mode
pip install -e .[dev]
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=video_agent --cov-report=html

# Run specific test types
pytest tests/unit
pytest tests/integration
pytest tests/e2e

# View coverage report
# Open htmlcov/index.html in browser
```

### Running Application

```bash
# From source
python -m video_agent.main

# Or after installation
ai-video-agent
```

## Production Build

### PyInstaller Build

```bash
# Install PyInstaller
pip install pyinstaller>=6.0.0

# Create spec file if not exists
pyi-makespec --windowed --name AI-Video-Agent src/video_agent/main.py

# Build executable
pyinstaller build/app.spec

# Output will be in dist/AI-Video-Agent.exe
```

### Inno Setup Installer

1. Download and install [Inno Setup](https://jrsoftware.org/isdl.php)

2. Create installer script (`installer/setup.iss`):

```iss
[Setup]
AppName=AI Video Agent
AppVersion=0.1.0
DefaultDirName={autopf}\AI Video Agent
DefaultGroupName=AI Video Agent
OutputDir=output
OutputBaseFilename=AI-Video-Agent-Setup-0.1.0

[Files]
Source: "dist\AI-Video-Agent.exe"; DestDir: "{app}"

[Icons]
Name: "{group}\AI Video Agent"; Filename: "{app}\AI-Video-Agent.exe"
Name: "{autodesktop}\AI Video Agent"; Filename: "{app}\AI-Video-Agent.exe"

[Run]
Filename: "{app}\AI-Video-Agent.exe"; Description: "Launch AI Video Agent"; Flags: nowait postinstall skipifsilent
```

3. Compile installer:

```bash
iscc installer/setup.iss
```

4. Output will be in `installer/output/AI-Video-Agent-Setup-0.1.0.exe`

## GitHub Actions Build

The project includes workflows for automated builds:

### CI Workflow (`.github/workflows/ci.yml`)

Runs on every push/PR:
- Lint code
- Run unit tests
- Upload coverage report

### Build Windows Workflow (`.github/workflows/build-windows.yml`)

Runs on main branch:
- Setup Python 3.12
- Install dependencies
- Run tests
- Build PyInstaller executable
- Upload artifact

### Release Workflow (`.github/workflows/release.yml`)

Runs on version tags (`v*.*.*`):
- Full build process
- Create installer
- Generate checksums
- Create GitHub Release with artifacts

## Build Artifacts

After successful build:

```
dist/
├── AI-Video-Agent.exe          # Portable executable
└── AI-Video-Agent-Windows.zip  # Packaged executable

installer/output/
└── AI-Video-Agent-Setup-v0.1.0.exe  # Installer
```

## Configuration

### Environment Variables

Create `.env` file:

```env
# AI Providers
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
LOCAL_AI_URL=http://localhost:8080/v1

# Transcription
WHISPER_MODEL=base
WHISPER_DEVICE=cpu

# Paths (optional, defaults used if not specified)
FFMPEG_PATH=C:\Program Files\ffmpeg\bin\ffmpeg.exe
RESOLVE_INSTALLATION_PATH=C:\Program Files\Blackmagic Design\DaVinci Resolve
STORAGE_BASE_PATH=C:\Users\YourName\AppData\Local\AIVideoAgent
```

### Database Location

Default database location:
- Windows: `%LOCALAPPDATA%\AIVideoAgent\database\video_agent.db`
- Linux: `~/.local/share/AIVideoAgent/database/video_agent.db`
- Mac: `~/Library/Application Support/AIVideoAgent/database/video_agent.db`

### Log Files

Logs stored in:
- Windows: `%LOCALAPPDATA%\AIVideoAgent\logs\`
- Linux: `~/.local/share/AIVideoAgent/logs/`
- Mac: `~/Library/Application Support/AIVideoAgent/logs/`

## Troubleshooting

### PyInstaller Build Issues

**Missing modules:**
```bash
# Add hidden imports to spec file
hiddenimports=[
    'video_agent.domain.models',
    'video_agent.application.services',
    # ... other modules
]
```

**Large executable size:**
```bash
# Use UPX compression
pyinstaller --upx-dir=upx app.spec
```

### Inno Setup Issues

**Compiler not found:**
- Ensure Inno Setup is installed
- Add to PATH: `C:\Program Files (x86)\Inno Setup 6`

**File not found:**
- Verify PyInstaller build completed successfully
- Check paths in `.iss` file

### Test Failures

**Import errors:**
```bash
# Ensure running from project root
# Set PYTHONPATH
set PYTHONPATH=src  # Windows
export PYTHONPATH=src  # Linux/Mac

# Run tests
pytest tests/unit
```

**Fixture issues:**
- Check test fixtures in `tests/fixtures/`
- Ensure pytest-asyncio is installed

## Performance Optimization

### Build Optimization

```bash
# One-file mode (smaller download, slower startup)
pyinstaller --onefile app.spec

# One-directory mode (faster startup, larger download)
pyinstaller --onedir app.spec

# Exclude unnecessary modules
pyinstaller --exclude-module tkinter app.spec
```

### Runtime Optimization

- Enable multiprocessing for video processing
- Use GPU acceleration for transcription (if available)
- Configure appropriate cache sizes

## Release Checklist

Before creating a release:

- [ ] All tests passing
- [ ] Documentation updated
- [ ] Version number updated in:
  - `pyproject.toml`
  - `src/video_agent/__init__.py`
  - `installer/setup.iss`
- [ ] CHANGELOG.md updated
- [ ] Build tested on clean Windows VM
- [ ] Installer tested
- [ ] Smoke tests passed

## Creating a Release

```bash
# Update version
# Edit pyproject.toml, __init__.py, setup.iss

# Commit changes
git add .
git commit -m "Release v0.1.0"

# Tag release
git tag v0.1.0

# Push tag (triggers release workflow)
git push origin v0.1.0
```

GitHub Actions will automatically:
1. Build executable
2. Create installer
3. Generate checksums
4. Create GitHub Release
5. Attach artifacts
