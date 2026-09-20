"""
AI Video Agent - File System Manager

Safe, controlled file system operations for media handling.
"""

import shutil
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
import structlog

logger = structlog.get_logger(__name__)


class FileSystemError(Exception):
    """File system operation error."""
    def __init__(self, message: str, path: str = None):
        self.message = message
        self.path = path
        super().__init__(message)


class FileSystemManager:
    """Managed file system operations for the application."""
    
    def __init__(self, base_directory: Optional[Path] = None):
        """
        Initialize file system manager.
        
        Args:
            base_directory: Base directory for app data. 
                           Uses AppData/Local/AIVideoAgent on Windows,
                           ~/.local/share/ai-video-agent on Linux/Mac if not specified.
        """
        if base_directory:
            self.base_dir = Path(base_directory)
        else:
            # Default platform-specific location
            import platform
            system = platform.system()
            
            if system == "Windows":
                appdata = Path.home() / "AppData" / "Local" / "AIVideoAgent"
            elif system == "Darwin":
                appdata = Path.home() / "Library" / "Application Support" / "AIVideoAgent"
            else:  # Linux
                appdata = Path.home() / ".local" / "share" / "ai-video-agent"
            
            self.base_dir = appdata
        
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create all required directories."""
        directories = [
            self.base_dir,
            self.get_config_directory(),
            self.get_database_directory(),
            self.get_projects_directory(),
            self.get_media_cache_directory(),
            self.get_thumbnails_directory(),
            self.get_renders_directory(),
            self.get_temp_directory(),
            self.get_logs_directory(),
            self.get_backups_directory(),
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized file system at {self.base_dir}")
    
    def get_config_directory(self) -> Path:
        """Get configuration directory."""
        return self.base_dir / "config"
    
    def get_database_directory(self) -> Path:
        """Get database directory."""
        return self.base_dir / "database"
    
    def get_projects_directory(self) -> Path:
        """Get projects directory."""
        return self.base_dir / "projects"
    
    def get_media_cache_directory(self) -> Path:
        """Get media cache directory."""
        return self.base_dir / "media_cache"
    
    def get_thumbnails_directory(self) -> Path:
        """Get thumbnails directory."""
        return self.base_dir / "thumbnails"
    
    def get_renders_directory(self) -> Path:
        """Get renders directory."""
        return self.base_dir / "renders"
    
    def get_temp_directory(self) -> Path:
        """Get temporary files directory."""
        return self.base_dir / "temp"
    
    def get_logs_directory(self) -> Path:
        """Get logs directory."""
        return self.base_dir / "logs"
    
    def get_backups_directory(self) -> Path:
        """Get backups directory."""
        return self.base_dir / "backups"
    
    def get_project_directory(self, project_id: str) -> Path:
        """Get directory for specific project."""
        project_dir = self.get_projects_directory() / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir
    
    def get_safe_path(
        self, 
        filename: str, 
        directory: Path,
        allow_subdirs: bool = False
    ) -> Path:
        """
        Get a safe path within a directory, preventing directory traversal.
        
        Args:
            filename: Requested filename
            directory: Base directory
            allow_subdirs: Whether to allow subdirectories in filename
            
        Returns:
            Safe absolute path within directory
            
        Raises:
            FileSystemError: If path is unsafe
        """
        # Resolve to absolute path
        base = directory.resolve()
        
        if allow_subdirs:
            # Allow subdirectories but prevent traversal
            requested = (base / filename).resolve()
        else:
            # Only allow filename, no path components
            requested = (base / Path(filename).name).resolve()
        
        # Ensure resolved path is within base directory
        try:
            requested.relative_to(base)
        except ValueError:
            raise FileSystemError(
                f"Unsafe path detected: {filename}",
                path=str(requested)
            )
        
        return requested
    
    def validate_file_access(self, file_path: str) -> bool:
        """
        Validate that a file path is accessible and safe.
        
        Args:
            file_path: Path to validate
            
        Returns:
            True if file is accessible and safe
        """
        try:
            path = Path(file_path)
            
            # Check existence
            if not path.exists():
                logger.warning(f"File does not exist: {file_path}")
                return False
            
            # Check readability
            if not path.is_file():
                logger.warning(f"Not a file: {file_path}")
                return False
            
            # Try to open for reading
            with open(path, 'rb') as f:
                f.read(1)
            
            return True
            
        except PermissionError:
            logger.error(f"Permission denied: {file_path}")
            return False
        except Exception as e:
            logger.error(f"File validation failed: {e}")
            return False
    
    def ensure_space_available(
        self, 
        required_bytes: int, 
        directory: Optional[Path] = None
    ) -> bool:
        """
        Check if sufficient disk space is available.
        
        Args:
            required_bytes: Required space in bytes
            directory: Directory to check (uses temp dir if None)
            
        Returns:
            True if space is available
        """
        import shutil
        
        check_dir = directory or self.get_temp_directory()
        
        try:
            usage = shutil.disk_usage(check_dir)
            available = usage.free
            
            if available < required_bytes:
                logger.warning(
                    f"Insufficient disk space",
                    required=required_bytes,
                    available=available,
                    directory=str(check_dir)
                )
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to check disk space: {e}")
            return False
    
    def get_directory_info(self, directory: Optional[Path] = None) -> Dict[str, Any]:
        """
        Get information about a directory.
        
        Args:
            directory: Directory to inspect (uses base dir if None)
            
        Returns:
            Dictionary with directory information
        """
        import shutil
        
        check_dir = directory or self.base_dir
        
        try:
            usage = shutil.disk_usage(check_dir)
            
            return {
                "path": str(check_dir),
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
                "percent_used": (usage.used / usage.total) * 100 if usage.total > 0 else 0,
            }
            
        except Exception as e:
            logger.error(f"Failed to get directory info: {e}")
            return {
                "path": str(check_dir),
                "error": str(e),
            }
    
    def cleanup_temp_directory(self, max_age_hours: int = 24):
        """
        Clean up old temporary files.
        
        Args:
            max_age_hours: Maximum age of files to keep in hours
        """
        import time
        
        temp_dir = self.get_temp_directory()
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        cleaned_count = 0
        
        try:
            for item in temp_dir.iterdir():
                try:
                    # Check modification time
                    mtime = item.stat().st_mtime
                    
                    if current_time - mtime > max_age_seconds:
                        if item.is_file():
                            item.unlink()
                            cleaned_count += 1
                            logger.debug(f"Cleaned up old temp file: {item.name}")
                        elif item.is_dir():
                            shutil.rmtree(item)
                            cleaned_count += 1
                            logger.debug(f"Cleaned up old temp directory: {item.name}")
                            
                except Exception as e:
                    logger.warning(f"Failed to clean up {item}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup temp directory: {e}")
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old temp items")
    
    def copy_file_safely(
        self, 
        source: str, 
        destination: str,
        overwrite: bool = False
    ) -> str:
        """
        Safely copy a file with validation.
        
        Args:
            source: Source file path
            destination: Destination file path
            overwrite: Whether to overwrite existing file
            
        Returns:
            Destination path
            
        Raises:
            FileSystemError: If copy fails
        """
        src_path = Path(source)
        dst_path = Path(destination)
        
        # Validate source
        if not src_path.exists():
            raise FileSystemError(f"Source file not found", path=str(source))
        
        if not src_path.is_file():
            raise FileSystemError(f"Source is not a file", path=str(source))
        
        # Check if destination exists
        if dst_path.exists() and not overwrite:
            raise FileSystemError(
                f"Destination already exists and overwrite=False", 
                path=str(destination)
            )
        
        # Ensure destination directory exists
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            shutil.copy2(src_path, dst_path)
            logger.debug(f"Copied file from {source} to {destination}")
            return str(dst_path)
            
        except Exception as e:
            logger.error(f"Failed to copy file: {e}")
            raise FileSystemError(f"Copy failed: {e}", path=str(destination))
    
    def delete_file_safely(self, file_path: str) -> bool:
        """
        Safely delete a file.
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if deleted successfully
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.warning(f"File not found for deletion: {file_path}")
            return False
        
        try:
            path.unlink()
            logger.debug(f"Deleted file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            raise FileSystemError(f"Delete failed: {e}", path=file_path)
