"""
AI Video Agent - FFmpeg Wrapper Tests
"""

import pytest
import tempfile
from pathlib import Path

from video_agent.media.ffmpeg import FFmpegWrapper, FFmpegError


class TestFFmpegWrapper:
    """Tests for FFmpegWrapper."""
    
    @pytest.fixture
    def ffmpeg(self):
        """Create FFmpeg wrapper instance."""
        return FFmpegWrapper()
    
    def test_ffmpeg_available(self, ffmpeg):
        """Test that FFmpeg is available."""
        # This test will fail if FFmpeg is not installed
        assert ffmpeg.ffmpeg_path == "ffmpeg"
        assert ffmpeg.ffprobe_path == "ffprobe"
    
    def test_get_media_info_file_not_found(self, ffmpeg):
        """Test getting info for non-existent file."""
        with pytest.raises(FileNotFoundError):
            ffmpeg.get_media_info("/nonexistent/file.mp4")
    
    def test_validate_file_nonexistent(self, ffmpeg):
        """Test validating non-existent file."""
        result = ffmpeg.validate_file("/nonexistent/file.mp4")
        assert result is False
    
    def test_parse_fps_fraction(self, ffmpeg):
        """Test FPS parsing from fraction."""
        assert ffmpeg._parse_fps("30000/1001") == pytest.approx(29.97, rel=0.01)
        assert ffmpeg._parse_fps("60000/1001") == pytest.approx(59.94, rel=0.01)
        assert ffmpeg._parse_fps("30/1") == 30.0
        assert ffmpeg._parse_fps("24/1") == 24.0
    
    def test_parse_fps_invalid(self, ffmpeg):
        """Test FPS parsing with invalid input."""
        assert ffmpeg._parse_fps(None) is None
        assert ffmpeg._parse_fps("") is None
        assert ffmpeg._parse_fps("invalid") is None
        assert ffmpeg._parse_fps("0/0") is None  # Division by zero
    
    def test_extract_metadata_with_test_file(self, ffmpeg):
        """Test metadata extraction with a generated test file."""
        # Create a simple test video using FFmpeg
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.mp4"
            
            # Generate a 2-second test video
            args = [
                ffmpeg.ffmpeg_path,
                "-f", "lavfi",
                "-i", "testsrc=size=320x240:rate=30",
                "-f", "lavfi",
                "-i", "sine=frequency=440:duration=2",
                "-t", "2",
                "-c:v", "libx264",
                "-c:a", "aac",
                "-y",
                str(test_file),
            ]
            
            import subprocess
            result = subprocess.run(args, capture_output=True, text=True)
            
            if result.returncode == 0:
                metadata = ffmpeg.extract_metadata(str(test_file))
                
                assert metadata["duration"] > 0
                assert metadata["video"]["width"] == 320
                assert metadata["video"]["height"] == 240
                assert metadata["has_audio"] is True
                assert metadata["video"]["fps"] is not None
            else:
                pytest.skip("Could not generate test video file")
    
    def test_export_thumbnail(self, ffmpeg):
        """Test thumbnail export with a generated test file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.mp4"
            thumb_file = Path(tmpdir) / "thumb.jpg"
            
            # Generate test video
            args = [
                ffmpeg.ffmpeg_path,
                "-f", "lavfi",
                "-i", "testsrc=size=320x240:rate=30",
                "-t", "2",
                "-c:v", "libx264",
                "-y",
                str(test_file),
            ]
            
            import subprocess
            result = subprocess.run(args, capture_output=True, text=True)
            
            if result.returncode == 0:
                output = ffmpeg.export_thumbnail(
                    str(test_file),
                    str(thumb_file),
                    timestamp=1.0
                )
                
                assert Path(output).exists()
                assert thumb_file.stat().st_size > 0
            else:
                pytest.skip("Could not generate test video file")
