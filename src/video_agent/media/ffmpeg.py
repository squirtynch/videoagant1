"""
AI Video Agent - FFmpeg Wrapper

Safe, controlled wrapper for FFmpeg operations.
Never constructs shell commands via string concatenation.
"""

import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import structlog

logger = structlog.get_logger(__name__)


class FFmpegError(Exception):
    """FFmpeg operation error."""
    def __init__(self, message: str, return_code: int = None, stderr: str = None):
        self.message = message
        self.return_code = return_code
        self.stderr = stderr
        super().__init__(message)


class FFmpegWrapper:
    """Controlled FFmpeg wrapper for media operations."""
    
    def __init__(self, ffmpeg_path: Optional[str] = None):
        self.ffmpeg_path = ffmpeg_path or "ffmpeg"
        self.ffprobe_path = ffmpeg_path.replace("ffmpeg", "ffprobe") if ffmpeg_path else "ffprobe"
    
    def _run_command(
        self, 
        args: List[str], 
        timeout: int = 300
    ) -> subprocess.CompletedProcess:
        """Run FFmpeg command safely.
        
        Args are passed as list, never as shell string.
        """
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,  # We handle errors ourselves
            )
            
            if result.returncode != 0:
                logger.error(
                    f"FFmpeg command failed with code {result.returncode}",
                    stderr=result.stderr
                )
                raise FFmpegError(
                    f"FFmpeg failed: {result.stderr[:500]}",
                    return_code=result.returncode,
                    stderr=result.stderr
                )
            
            return result
            
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg command timed out")
            raise FFmpegError("FFmpeg command timed out")
        except FileNotFoundError:
            logger.error(f"FFmpeg not found at {self.ffmpeg_path}")
            raise FFmpegError(f"FFmpeg not found: {self.ffmpeg_path}")
    
    def get_media_info(self, file_path: str) -> Dict[str, Any]:
        """Get media information using ffprobe."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Media file not found: {file_path}")
        
        args = [
            self.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(path),
        ]
        
        result = self._run_command(args)
        
        try:
            info = json.loads(result.stdout)
            return info
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse ffprobe output: {e}")
            raise FFmpegError(f"Failed to parse media info: {e}")
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract key metadata from media file."""
        info = self.get_media_info(file_path)
        
        format_info = info.get("format", {})
        streams = info.get("streams", [])
        
        video_stream = next(
            (s for s in streams if s.get("codec_type") == "video"), 
            None
        )
        audio_stream = next(
            (s for s in streams if s.get("codec_type") == "audio"), 
            None
        )
        
        metadata = {
            "duration": float(format_info.get("duration", 0)),
            "file_size": int(format_info.get("size", 0)),
            "bitrate": format_info.get("bit_rate"),
            "video": {
                "codec": video_stream.get("codec_name") if video_stream else None,
                "width": video_stream.get("width") if video_stream else None,
                "height": video_stream.get("height") if video_stream else None,
                "fps": self._parse_fps(video_stream.get("r_frame_rate")) if video_stream else None,
            },
            "audio": {
                "codec": audio_stream.get("codec_name") if audio_stream else None,
                "sample_rate": audio_stream.get("sample_rate") if audio_stream else None,
                "channels": audio_stream.get("channels") if audio_stream else None,
            },
            "has_audio": audio_stream is not None,
        }
        
        return metadata
    
    def _parse_fps(self, fps_str: Optional[str]) -> Optional[float]:
        """Parse FPS from fraction string (e.g., '30000/1001')."""
        if not fps_str:
            return None
        
        try:
            if "/" in fps_str:
                num, denom = map(int, fps_str.split("/"))
                return num / denom if denom != 0 else None
            return float(fps_str)
        except (ValueError, ZeroDivisionError):
            return None
    
    def extract_audio(
        self, 
        input_path: str, 
        output_path: str,
        audio_codec: str = "pcm_s16le",
        sample_rate: int = 16000
    ) -> str:
        """Extract audio from video file."""
        args = [
            self.ffmpeg_path,
            "-i", input_path,
            "-vn",  # No video
            "-acodec", audio_codec,
            "-ar", str(sample_rate),
            "-ac", "1",  # Mono
            "-y",  # Overwrite output
            output_path,
        ]
        
        self._run_command(args)
        
        return output_path
    
    def trim_video(
        self,
        input_path: str,
        output_path: str,
        start_time: float,
        end_time: float
    ) -> str:
        """Trim video to specified time range."""
        duration = end_time - start_time
        
        args = [
            self.ffmpeg_path,
            "-ss", str(start_time),
            "-t", str(duration),
            "-i", input_path,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-copyts",
            "-y",
            output_path,
        ]
        
        self._run_command(args)
        
        return output_path
    
    def crop_video(
        self,
        input_path: str,
        output_path: str,
        width: int,
        height: int,
        x: int,
        y: int
    ) -> str:
        """Crop video to specified dimensions."""
        args = [
            self.ffmpeg_path,
            "-i", input_path,
            "-vf", f"crop={width}:{height}:{x}:{y}",
            "-c:a", "copy",
            "-y",
            output_path,
        ]
        
        self._run_command(args)
        
        return output_path
    
    def reframe_to_vertical(
        self,
        input_path: str,
        output_path: str,
        output_width: int = 1080,
        output_height: int = 1920
    ) -> str:
        """Reframe video to vertical (9:16) aspect ratio."""
        # Use scale and crop filters for smart reframing
        # This is a simple center crop - could be enhanced with AI tracking
        args = [
            self.ffmpeg_path,
            "-i", input_path,
            "-vf", 
            f"scale={output_width}:-1,crop={output_width}:{output_height}:(ow-iw)/2:(oh-ih)/2",
            "-c:a", "copy",
            "-y",
            output_path,
        ]
        
        self._run_command(args)
        
        return output_path
    
    def concatenate_videos(
        self,
        input_paths: List[str],
        output_path: str
    ) -> str:
        """Concatenate multiple video files."""
        if not input_paths:
            raise ValueError("No input paths provided")
        
        # Create temporary file list for concat demuxer
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for path in input_paths:
                f.write(f"file '{path}'\n")
            list_file = f.name
        
        try:
            args = [
                self.ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", list_file,
                "-c", "copy",
                "-y",
                output_path,
            ]
            
            self._run_command(args)
            
        finally:
            # Clean up temp file
            Path(list_file).unlink(missing_ok=True)
        
        return output_path
    
    def add_subtitles(
        self,
        input_path: str,
        output_path: str,
        subtitle_file: str,
        subtitle_format: str = "srt"
    ) -> str:
        """Burn subtitles into video."""
        # Escape quotes in subtitle path for filter
        safe_path = subtitle_file.replace("'", "'\\''")
        
        args = [
            self.ffmpeg_path,
            "-i", input_path,
            "-vf", f"subtitles='{safe_path}'",
            "-c:a", "copy",
            "-y",
            output_path,
        ]
        
        self._run_command(args)
        
        return output_path
    
    def export_thumbnail(
        self,
        input_path: str,
        output_path: str,
        timestamp: float = 1.0
    ) -> str:
        """Export a thumbnail frame from video."""
        args = [
            self.ffmpeg_path,
            "-ss", str(timestamp),
            "-i", input_path,
            "-vframes", "1",
            "-q:v", "2",
            "-y",
            output_path,
        ]
        
        self._run_command(args)
        
        return output_path
    
    def validate_file(self, file_path: str) -> bool:
        """Validate that a file is a valid media file."""
        try:
            info = self.get_media_info(file_path)
            streams = info.get("streams", [])
            
            # Must have at least one video or audio stream
            has_video = any(s.get("codec_type") == "video" for s in streams)
            has_audio = any(s.get("codec_type") == "audio" for s in streams)
            
            return has_video or has_audio
            
        except Exception as e:
            logger.error(f"File validation failed: {e}")
            return False
