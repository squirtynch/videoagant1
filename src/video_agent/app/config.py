"""Application Configuration and Settings"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path
from typing import Optional


class AppSettings(BaseSettings):
    """Application settings loaded from environment and config files."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = "AI Video Agent"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Database
    database_path: Optional[Path] = None
    
    # AI Providers
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    local_ai_url: Optional[str] = Field(default=None, alias="LOCAL_AI_URL")
    
    # Transcription
    whisper_model: str = "base"
    whisper_device: str = "cpu"
    
    # FFmpeg
    ffmpeg_path: Optional[Path] = None
    
    # DaVinci Resolve
    resolve_installation_path: Optional[Path] = None
    
    # Storage
    storage_base_path: Optional[Path] = None
    
    # Security
    secrets_backend: str = "windows_credential_manager"  # windows_credential_manager, dpapi, file
    
    @property
    def get_database_path(self) -> Path:
        """Get database path, using default if not configured."""
        if self.database_path:
            return self.database_path
        
        base = self.get_storage_base()
        db_dir = base / "database"
        db_dir.mkdir(parents=True, exist_ok=True)
        return db_dir / "video_agent.db"
    
    @property
    def get_storage_base(self) -> Path:
        """Get base storage directory."""
        if self.storage_base_path:
            return self.storage_base_path
        
        # Default to AppData on Windows, ~/.local/share on Linux/Mac
        import sys
        if sys.platform == "win32":
            from pathlib import Path
            appdata = Path.home() / "AppData" / "Local" / "AIVideoAgent"
        else:
            appdata = Path.home() / ".local" / "share" / "AIVideoAgent"
        
        appdata.mkdir(parents=True, exist_ok=True)
        return appdata
    
    def ensure_directories(self):
        """Ensure all required directories exist."""
        base = self.get_storage_base
        
        dirs = [
            base / "config",
            base / "database",
            base / "projects",
            base / "media_cache",
            base / "thumbnails",
            base / "renders",
            base / "temp",
            base / "logs",
            base / "backups",
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)


def load_settings() -> AppSettings:
    """Load application settings."""
    return AppSettings()
