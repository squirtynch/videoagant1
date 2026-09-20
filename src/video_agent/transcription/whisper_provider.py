"""
AI Video Agent - Whisper Transcription Provider

Local Whisper transcription using OpenAI's Whisper model.
Supports both CPU and GPU execution.
"""

import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
import structlog

from .interfaces import (
    TranscriptionProvider, 
    Transcript, 
    TranscriptSegment,
    TranscriptionError
)

logger = structlog.get_logger(__name__)


class WhisperProvider(TranscriptionProvider):
    """Local Whisper transcription provider."""
    
    def __init__(
        self, 
        model_size: str = "base",
        device: Optional[str] = None,
        compute_type: str = "default"
    ):
        """
        Initialize Whisper provider.
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to run on (cpu, cuda, mps). None for auto-detect.
            compute_type: Compute type for GPU acceleration
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None
        self._available_languages = None
    
    @property
    def name(self) -> str:
        return f"Whisper ({self.model_size})"
    
    @property
    def supports_languages(self) -> List[str]:
        """Whisper supports 99+ languages."""
        # Common languages - full list is extensive
        return [
            "en", "zh", "de", "es", "ru", "ko", "fr", "ja", "pt", "tr",
            "pl", "ca", "nl", "ar", "sv", "it", "id", "hi", "fi", "vi",
            "he", "uk", "el", "ms", "cs", "ro", "da", "hu", "ta", "no",
            "th", "ur", "hr", "bg", "lt", "la", "mi", "ml", "cy", "sk",
            "te", "fa", "lv", "bn", "sr", "az", "sl", "kn", "et", "mk",
            "br", "eu", "is", "hy", "ne", "mn", "bs", "kk", "sq", "sw",
            "gl", "mr", "pa", "si", "km", "sn", "yo", "so", "af", "oc",
            "ka", "be", "tg", "sd", "gu", "am", "yi", "lo", "uz", "fo",
            "ht", "ps", "tk", "nn", "mt", "sa", "lb", "my", "bo", "tl",
            "mg", "as", "tt", "haw", "ln", "ha", "ba", "jw", "su"
        ]
    
    def _load_model(self):
        """Lazy-load Whisper model."""
        if self._model is not None:
            return
        
        try:
            import whisper
            
            logger.info(
                f"Loading Whisper model: {self.model_size}",
                device=self.device
            )
            
            if self.device:
                self._model = whisper.load_model(
                    self.model_size, 
                    device=self.device
                )
            else:
                self._model = whisper.load_model(self.model_size)
            
            logger.info("Whisper model loaded successfully")
            
        except ImportError:
            logger.error("Whisper package not installed. Run: pip install openai-whisper")
            raise TranscriptionError(
                "Whisper not installed. Install with: pip install openai-whisper",
                provider=self.name
            )
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise TranscriptionError(
                f"Failed to load Whisper model: {e}",
                provider=self.name
            )
    
    async def transcribe(
        self, 
        audio_path: str, 
        language: Optional[str] = None
    ) -> Transcript:
        """Transcribe audio file using Whisper."""
        
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Load model if not already loaded
        await asyncio.to_thread(self._load_model)
        
        try:
            logger.info(
                f"Starting transcription",
                file=audio_path,
                language=language or "auto"
            )
            
            # Run Whisper in thread pool (it's blocking)
            result = await asyncio.to_thread(
                self._transcribe_sync,
                audio_path,
                language
            )
            
            # Convert to our Transcript format
            segments = []
            for seg in result.get("segments", []):
                segments.append(
                    TranscriptSegment(
                        start=seg["start"],
                        end=seg["end"],
                        text=seg["text"].strip(),
                        confidence=seg.get("confidence") or seg.get("avg_logprob")
                    )
                )
            
            transcript = Transcript(
                language=result.get("language", "unknown"),
                duration=result.get("duration") or len(segments) > 0 and segments[-1].end or 0,
                segments=segments,
                metadata={
                    "model": self.model_size,
                    "device": self.device,
                    "source_file": str(path),
                }
            )
            
            logger.info(
                f"Transcription completed",
                segments=len(segments),
                duration=transcript.duration
            )
            
            return transcript
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise TranscriptionError(
                f"Transcription failed: {e}",
                provider=self.name
            )
    
    def _transcribe_sync(
        self, 
        audio_path: str, 
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synchronous Whisper transcription."""
        options = {
            "word_timestamps": False,  # Can enable for word-level timing
        }
        
        if language:
            options["language"] = language
        
        result = self._model.transcribe(audio_path, **options)
        return result
    
    async def check_health(self) -> bool:
        """Check if Whisper is available and can load models."""
        try:
            await asyncio.to_thread(self._load_model)
            return True
        except Exception as e:
            logger.warning(f"Whisper health check failed: {e}")
            return False
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return Whisper capabilities."""
        return {
            "provider_type": "local",
            "model_size": self.model_size,
            "device": self.device or "auto",
            "supports_languages": self.supports_languages,
            "auto_language_detection": True,
            "word_timestamps": True,
            "speaker_diarization": False,  # Not built-in
            "max_audio_duration": None,  # No hard limit
            "requires_internet": False,
        }
