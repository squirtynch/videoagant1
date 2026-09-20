"""
AI Video Agent - Transcription Provider Interface

Abstract base class for transcription providers.
Supports local Whisper, Whisper-compatible APIs, and other providers.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from pathlib import Path


class TranscriptSegment(BaseModel):
    """A segment of transcribed text with timing."""
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    text: str = Field(..., description="Transcribed text")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score")


class Transcript(BaseModel):
    """Complete transcription result."""
    language: str = Field(..., description="Detected language code")
    duration: float = Field(..., ge=0, description="Total duration in seconds")
    segments: List[TranscriptSegment] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def full_text(self) -> str:
        """Get full transcription as continuous text."""
        return " ".join(seg.text for seg in self.segments)
    
    def get_segment_at(self, timestamp: float) -> Optional[TranscriptSegment]:
        """Get the segment containing the specified timestamp."""
        for segment in self.segments:
            if segment.start <= timestamp <= segment.end:
                return segment
        return None
    
    def get_segments_in_range(
        self, 
        start: float, 
        end: float
    ) -> List[TranscriptSegment]:
        """Get all segments within a time range."""
        return [
            seg for seg in self.segments 
            if seg.start < end and seg.end > start
        ]


class TranscriptionProvider(ABC):
    """Abstract base class for transcription providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return provider name."""
        pass
    
    @property
    @abstractmethod
    def supports_languages(self) -> List[str]:
        """Return list of supported language codes."""
        pass
    
    @abstractmethod
    async def transcribe(
        self, 
        audio_path: str, 
        language: Optional[str] = None
    ) -> Transcript:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file (WAV, MP3, etc.)
            language: Optional language code (auto-detect if None)
            
        Returns:
            Transcript object with segments and metadata
            
        Raises:
            TranscriptionError: If transcription fails
        """
        pass
    
    @abstractmethod
    async def check_health(self) -> bool:
        """Check if provider is available and healthy."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Return provider capabilities."""
        pass


class TranscriptionError(Exception):
    """Transcription operation error."""
    def __init__(self, message: str, provider: str = None):
        self.message = message
        self.provider = provider
        super().__init__(message)
