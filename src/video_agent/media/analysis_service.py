"""
AI Video Agent - Media Analysis Service

Analyzes media files to extract:
- Metadata (duration, resolution, codec, etc.)
- Audio extraction for transcription
- Scene detection
- Key moments identification
- Thumbnail generation
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import structlog

from ..media.ffmpeg import FFmpegWrapper
from ..storage.filesystem import FileSystemManager
from ..transcription.interfaces import Transcript
from ..domain.models import MediaAsset, MediaAnalysis

logger = structlog.get_logger(__name__)


class MediaAnalysisError(Exception):
    """Media analysis operation error."""
    def __init__(self, message: str, asset_id: str = None):
        self.message = message
        self.asset_id = asset_id
        super().__init__(message)


class MediaAnalysisService:
    """Service for analyzing media files."""
    
    def __init__(
        self,
        ffmpeg: FFmpegWrapper,
        filesystem: FileSystemManager
    ):
        self.ffmpeg = ffmpeg
        self.filesystem = filesystem
    
    async def analyze_video(
        self,
        video_path: str,
        asset_id: str,
        project_id: str,
        generate_thumbnail: bool = True
    ) -> MediaAnalysis:
        """
        Perform comprehensive analysis of a video file.
        
        Args:
            video_path: Path to video file
            asset_id: Unique asset identifier
            project_id: Project identifier
            generate_thumbnail: Whether to generate thumbnail
            
        Returns:
            MediaAnalysis object with all extracted metadata
        """
        path = Path(video_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        logger.info(
            f"Starting media analysis",
            asset_id=asset_id,
            path=video_path
        )
        
        # Extract metadata using FFmpeg
        metadata = await asyncio.to_thread(
            self.ffmpeg.extract_metadata,
            str(path)
        )
        
        # Generate thumbnail if requested
        thumbnail_path = None
        if generate_thumbnail and metadata.get("duration", 0) > 0:
            try:
                thumbnail_path = await self._generate_thumbnail(
                    str(path),
                    asset_id,
                    project_id
                )
            except Exception as e:
                logger.warning(f"Failed to generate thumbnail: {e}")
        
        # Create analysis result
        analysis = MediaAnalysis(
            id=f"analysis-{asset_id}",
            asset_id=asset_id,
            duration=metadata.get("duration", 0),
            resolution=[
                metadata.get("video", {}).get("width", 0),
                metadata.get("video", {}).get("height", 0)
            ],
            fps=metadata.get("video", {}).get("fps"),
            codec=metadata.get("video", {}).get("codec"),
            has_audio=metadata.get("has_audio", False),
            audio_codec=metadata.get("audio", {}).get("codec") if metadata.get("has_audio") else None,
            file_size=metadata.get("file_size", 0),
            thumbnail_path=thumbnail_path,
            metadata={
                "source_path": str(path),
                "analyzed_at": datetime.utcnow().isoformat(),
                "ffmpeg_metadata": metadata,
            }
        )
        
        logger.info(
            f"Media analysis completed",
            asset_id=asset_id,
            duration=analysis.duration,
            resolution=analysis.resolution,
            has_audio=analysis.has_audio
        )
        
        return analysis
    
    async def _generate_thumbnail(
        self,
        video_path: str,
        asset_id: str,
        project_id: str
    ) -> str:
        """Generate thumbnail from video."""
        # Get thumbnail directory for project
        thumb_dir = self.filesystem.get_thumbnails_directory() / project_id
        thumb_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate thumbnail filename
        thumb_filename = f"{asset_id}_thumb.jpg"
        thumb_path = thumb_dir / thumb_filename
        
        # Extract thumbnail at 10% of duration or 1 second
        metadata = self.ffmpeg.get_media_info(video_path)
        duration = float(metadata.get("format", {}).get("duration", 1))
        timestamp = max(1.0, duration * 0.1)
        
        await asyncio.to_thread(
            self.ffmpeg.export_thumbnail,
            video_path,
            str(thumb_path),
            timestamp
        )
        
        return str(thumb_path)
    
    async def detect_scenes(
        self,
        video_path: str,
        min_scene_length: float = 2.0
    ) -> List[Dict[str, float]]:
        """
        Detect scene changes in video.
        
        Uses FFmpeg's scene detection filter to find cuts.
        
        Args:
            video_path: Path to video file
            min_scene_length: Minimum scene length in seconds
            
        Returns:
            List of scenes with start, end, and duration
        """
        logger.info(f"Detecting scenes in {video_path}")
        
        # This is a simplified implementation
        # A full implementation would use FFmpeg's select filter
        # with scene change detection
        
        try:
            # Get video duration
            metadata = self.ffmpeg.get_media_info(video_path)
            duration = float(metadata.get("format", {}).get("duration", 0))
            
            if duration == 0:
                return []
            
            # For now, return single scene
            # TODO: Implement actual scene detection with FFmpeg
            return [
                {
                    "start": 0.0,
                    "end": duration,
                    "duration": duration,
                    "confidence": 1.0,
                }
            ]
            
        except Exception as e:
            logger.error(f"Scene detection failed: {e}")
            return []
    
    async def find_silent_segments(
        self,
        audio_path: str,
        threshold_db: float = -50.0,
        min_duration: float = 1.0
    ) -> List[Dict[str, float]]:
        """
        Find silent segments in audio.
        
        Args:
            audio_path: Path to audio file
            threshold_db: Silence threshold in dB
            min_duration: Minimum silence duration in seconds
            
        Returns:
            List of silent segments with start, end, duration
        """
        logger.info(f"Finding silent segments in {audio_path}")
        
        # This would use FFmpeg's silencedetect filter
        # For now, return empty list
        # TODO: Implement actual silence detection
        
        return []
    
    async def extract_key_moments(
        self,
        video_path: str,
        transcript: Optional[Transcript] = None,
        max_moments: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Identify potentially interesting moments in video.
        
        Combines visual and audio cues to find highlights.
        
        Args:
            video_path: Path to video file
            transcript: Optional transcript for text-based analysis
            max_moments: Maximum number of moments to return
            
        Returns:
            List of key moments with timestamps and rationale
        """
        logger.info(f"Extracting key moments from {video_path}")
        
        moments = []
        
        # If we have a transcript, look for emotional/important phrases
        if transcript:
            # Simple heuristic: look for exclamation marks, questions, etc.
            for segment in transcript.segments:
                text = segment.text
                
                score = 0.0
                
                # Exclamation indicates emphasis
                if "!" in text:
                    score += 0.3
                
                # Question might indicate important point
                if "?" in text:
                    score += 0.2
                
                # Short segments might be punchy
                if len(text.split()) < 10:
                    score += 0.1
                
                if score > 0.2:
                    moments.append({
                        "start": segment.start,
                        "end": segment.end,
                        "type": "transcript_based",
                        "text": text,
                        "confidence": min(score, 1.0),
                        "rationale": self._get_rationale(text, score),
                    })
        
        # Sort by confidence and take top N
        moments.sort(key=lambda m: m["confidence"], reverse=True)
        return moments[:max_moments]
    
    def _get_rationale(self, text: str, score: float) -> str:
        """Generate human-readable rationale for moment selection."""
        reasons = []
        
        if "!" in text:
            reasons.append("emphatic statement")
        
        if "?" in text:
            reasons.append("question posed")
        
        if len(text.split()) < 10:
            reasons.append("concise statement")
        
        if score > 0.7:
            reasons.append("high confidence highlight")
        
        return f"Selected because: {', '.join(reasons) or 'general interest'}"
    
    async def validate_media_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate that a file is a valid, processable media file.
        
        Args:
            file_path: Path to media file
            
        Returns:
            Validation result with status and details
        """
        result = {
            "valid": False,
            "path": file_path,
            "errors": [],
            "warnings": [],
            "metadata": None,
        }
        
        # Check file exists
        path = Path(file_path)
        if not path.exists():
            result["errors"].append("File does not exist")
            return result
        
        # Check file is readable
        if not path.is_file():
            result["errors"].append("Not a file")
            return result
        
        try:
            # Try to get metadata
            metadata = await asyncio.to_thread(
                self.ffmpeg.get_media_info,
                str(path)
            )
            
            # Check for video or audio streams
            streams = metadata.get("streams", [])
            has_video = any(s.get("codec_type") == "video" for s in streams)
            has_audio = any(s.get("codec_type") == "audio" for s in streams)
            
            if not has_video and not has_audio:
                result["errors"].append("No video or audio streams found")
                return result
            
            # Add warnings for potential issues
            duration = float(metadata.get("format", {}).get("duration", 0))
            
            if duration == 0:
                result["warnings"].append("Duration is zero")
            elif duration < 1:
                result["warnings"].append("Very short duration (< 1s)")
            
            file_size = int(metadata.get("format", {}).get("size", 0))
            if file_size == 0:
                result["warnings"].append("File size is zero")
            
            result["valid"] = True
            result["metadata"] = metadata
            
        except Exception as e:
            result["errors"].append(f"Failed to read media info: {str(e)}")
        
        return result
