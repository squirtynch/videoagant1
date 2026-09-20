"""
AI Video Agent - Transcription Service

Orchestrates transcription workflow:
1. Extract audio from video (if needed)
2. Select appropriate transcription provider
3. Execute transcription
4. Store results
"""

import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
import structlog

from .interfaces import (
    TranscriptionProvider, 
    Transcript, 
    TranscriptSegment,
    TranscriptionError
)
from ..media.ffmpeg import FFmpegWrapper
from ..storage.filesystem import FileSystemManager

logger = structlog.get_logger(__name__)


class TranscriptionService:
    """Service for managing transcription operations."""
    
    def __init__(
        self,
        ffmpeg_wrapper: FFmpegWrapper,
        filesystem: FileSystemManager,
        providers: Optional[List[TranscriptionProvider]] = None
    ):
        self.ffmpeg = ffmpeg_wrapper
        self.filesystem = filesystem
        self.providers: Dict[str, TranscriptionProvider] = {}
        
        if providers:
            for provider in providers:
                self.register_provider(provider)
    
    def register_provider(self, provider: TranscriptionProvider):
        """Register a transcription provider."""
        self.providers[provider.name] = provider
        logger.info(f"Registered transcription provider: {provider.name}")
    
    def get_provider(self, name: str) -> Optional[TranscriptionProvider]:
        """Get provider by name."""
        return self.providers.get(name)
    
    def list_providers(self) -> List[str]:
        """List available provider names."""
        return list(self.providers.keys())
    
    async def transcribe_video(
        self,
        video_path: str,
        provider_name: Optional[str] = None,
        language: Optional[str] = None,
        keep_audio: bool = False
    ) -> Transcript:
        """
        Transcribe audio from a video file.
        
        Args:
            video_path: Path to video file
            provider_name: Specific provider to use (auto-select if None)
            language: Target language code (auto-detect if None)
            keep_audio: Keep extracted audio file after transcription
            
        Returns:
            Transcript object with segments and metadata
        """
        path = Path(video_path)
        if not path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Validate video file
        if not self.ffmpeg.validate_file(str(path)):
            raise ValueError(f"Invalid or corrupted video file: {video_path}")
        
        # Extract audio
        audio_path = await self._extract_audio(path)
        
        try:
            # Select provider
            provider = self._select_provider(provider_name)
            
            logger.info(
                f"Starting video transcription",
                video=video_path,
                audio=audio_path,
                provider=provider.name,
                language=language or "auto"
            )
            
            # Transcribe
            transcript = await provider.transcribe(audio_path, language)
            
            logger.info(
                f"Transcription completed",
                segments=len(transcript.segments),
                duration=transcript.duration,
                language=transcript.language
            )
            
            return transcript
            
        finally:
            # Clean up audio file unless requested to keep
            if not keep_audio and Path(audio_path).exists():
                try:
                    Path(audio_path).unlink()
                    logger.debug(f"Cleaned up temporary audio file: {audio_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up audio file: {e}")
    
    async def transcribe_audio(
        self,
        audio_path: str,
        provider_name: Optional[str] = None,
        language: Optional[str] = None
    ) -> Transcript:
        """
        Transcribe an audio file.
        
        Args:
            audio_path: Path to audio file
            provider_name: Specific provider to use
            language: Target language code
            
        Returns:
            Transcript object
        """
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        provider = self._select_provider(provider_name)
        
        logger.info(
            f"Starting audio transcription",
            audio=audio_path,
            provider=provider.name
        )
        
        return await provider.transcribe(audio_path, language)
    
    async def _extract_audio(self, video_path: Path) -> str:
        """Extract audio from video file."""
        # Create temp directory for audio
        temp_dir = self.filesystem.get_temp_directory()
        
        # Generate unique audio filename
        audio_filename = f"{video_path.stem}_audio.wav"
        audio_path = temp_dir / audio_filename
        
        logger.debug(f"Extracting audio to: {audio_path}")
        
        # Extract using FFmpeg
        await asyncio.to_thread(
            self.ffmpeg.extract_audio,
            str(video_path),
            str(audio_path),
            audio_codec="pcm_s16le",
            sample_rate=16000
        )
        
        return str(audio_path)
    
    def _select_provider(self, preferred_name: Optional[str]) -> TranscriptionProvider:
        """Select best available provider."""
        if not self.providers:
            raise TranscriptionError("No transcription providers registered")
        
        # If preferred provider specified, use it
        if preferred_name:
            if preferred_name in self.providers:
                return self.providers[preferred_name]
            else:
                logger.warning(
                    f"Preferred provider '{preferred_name}' not found, using default"
                )
        
        # Priority order: Whisper local > Whisper API > others
        priority_order = [
            lambda p: "Whisper (" in p.name and "API" not in p.name,  # Local Whisper
            lambda p: "Whisper API" in p.name,  # Whisper API
            lambda p: True,  # Any other
        ]
        
        for priority_check in priority_order:
            matches = [p for p in self.providers.values() if priority_check(p)]
            if matches:
                # Check health of candidates
                for provider in matches:
                    # Non-blocking health check
                    try:
                        is_healthy = asyncio.run(provider.check_health())
                        if is_healthy:
                            return provider
                    except Exception:
                        continue
                
                # If no healthy providers, return first match anyway
                return matches[0]
        
        # Fallback to first provider
        return next(iter(self.providers.values()))
    
    async def check_all_providers(self) -> Dict[str, bool]:
        """Check health of all registered providers."""
        results = {}
        
        for name, provider in self.providers.items():
            try:
                is_healthy = await provider.check_health()
                results[name] = is_healthy
                
                if not is_healthy:
                    logger.warning(f"Provider health check failed: {name}")
                    
            except Exception as e:
                logger.error(f"Provider health check error: {name} - {e}")
                results[name] = False
        
        return results
    
    def get_capabilities_summary(self) -> Dict[str, Any]:
        """Get summary of all provider capabilities."""
        return {
            name: provider.get_capabilities()
            for name, provider in self.providers.items()
        }
