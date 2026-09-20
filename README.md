# AI VIDEO AGENT

AI-powered video editing automation desktop application for Windows with DaVinci Resolve Studio integration.

## Features

- **Import & Analyze**: Import long-form videos and analyze content
- **AI Transcription**: Automatic speech-to-text with timestamp accuracy
- **Short Maker**: Automatically create Shorts/Reels/TikTok from long videos
- **Brief-to-Edit**: Convert text briefs into structured editing plans
- **AI Assistant**: Natural language commands for video editing
- **DaVinci Resolve Integration**: Seamlessly transfer timelines to Resolve
- **Local-First**: Projects stored locally with optional cloud AI providers

## Requirements

- Windows 10/11
- Python 3.12+ (for development)
- FFmpeg (for media processing)
- DaVinci Resolve Studio 18+ (optional, for timeline integration)

## Installation

### From Installer (Recommended)

Download the latest installer from [GitHub Releases](https://github.com/your-org/ai-video-agent/releases) and run `AI-Video-Agent-Setup.exe`.

### From Source (Development)

```bash
# Clone repository
git clone https://github.com/your-org/ai-video-agent.git
cd ai-video-agent

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -e .

# Run application
python -m video_agent.main
```

## Configuration

### AI Providers

Create a `.env` file in the application directory:

```env
# OpenAI-compatible API
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# Local AI endpoint (optional)
LOCAL_AI_URL=http://localhost:8080/v1

# Transcription provider
WHISPER_MODEL=base
```

### FFmpeg

FFmpeg should be available in your PATH or specify location in Settings.

### DaVinci Resolve

The application will auto-detect DaVinci Resolve installation. Ensure:
- DaVinci Resolve Studio 18+ is installed
- Remote scripting is enabled in Resolve preferences

## Usage

### Creating Shorts

1. Launch AI Video Agent
2. Click "Create Shorts"
3. Import your source video
4. Configure settings (duration, format, style, etc.)
5. Review AI-generated candidates
6. Approve and export

### Brief-to-Edit

1. Click "Edit from Brief"
2. Upload or paste your brief (TXT, MD, DOCX, PDF)
3. Import media assets
4. Review AI-generated editing plan
5. Execute and review compliance report

### AI Assistant

Use natural language commands:
- "Make 5 shorts from this interview"
- "Find the best hook moment"
- "Create a vertical version"
- "Check edit against brief"

## Architecture

```
src/video_agent/
├── app/              # Application bootstrap & config
├── domain/           # Domain models & business logic
├── application/      # Application services
├── ai/               # AI providers & routing
├── media/            # FFmpeg wrapper & media processing
├── editing/          # Editing plan schema & execution
├── resolve/          # DaVinci Resolve integration
├── jobs/             # Background job management
├── storage/          # Database & filesystem
├── security/         # Secrets & validation
├── ui/               # PySide6 UI components
└── diagnostics/      # Logging & health checks
```

## Building

### Development Build

```bash
python scripts/build.py
```

### Production Build (GitHub Actions)

The application builds automatically on push/tag via GitHub Actions:
- `ci.yml`: Continuous integration tests
- `build-windows.yml`: Windows executable & installer
- `release.yml`: GitHub Release with artifacts

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=video_agent --cov-report=html

# Run specific test type
pytest tests/unit
pytest tests/integration
pytest tests/e2e
```

## Documentation

- [Architecture](docs/architecture.md)
- [Build Instructions](docs/build.md)
- [Resolve Integration](docs/resolve-integration.md)
- [Provider Development](docs/provider-development.md)
- [Troubleshooting](docs/troubleshooting.md)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## Support

For issues and feature requests, use [GitHub Issues](https://github.com/your-org/ai-video-agent/issues).
