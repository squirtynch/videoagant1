"""
AI Video Agent - AI Provider Interfaces

Abstract base classes for AI providers.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class Message(BaseModel):
    """Chat message."""
    role: str  # "system", "user", "assistant"
    content: str


class ModelInfo(BaseModel):
    """Information about an AI model."""
    id: str
    name: str
    provider_type: str
    endpoint: Optional[str] = None
    model_identifier: str
    capabilities: List[str] = []
    context_limit: int = 4096
    enabled: bool = True
    health_status: str = "UNKNOWN"


class AIResponse(BaseModel):
    """Response from AI provider."""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    raw_response: Optional[Dict[str, Any]] = None


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return provider name."""
        pass
    
    @property
    @abstractmethod
    def provider_type(self) -> str:
        """Return provider type (OPENAI, LOCAL, MOCK)."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is healthy and accessible."""
        pass
    
    @abstractmethod
    async def list_models(self) -> List[ModelInfo]:
        """List available models from this provider."""
        pass
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AIResponse:
        """Send chat completion request."""
        pass
    
    @abstractmethod
    async def structured_output(
        self,
        messages: List[Message],
        model: str,
        response_schema: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Request structured JSON output from model."""
        pass


class TranscriptionResult(BaseModel):
    """Result of transcription."""
    language: str
    duration: float
    segments: List[Dict[str, Any]]
    text: str


class TranscriptionProvider(ABC):
    """Abstract base class for transcription providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return provider name."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is healthy."""
        pass
    
    @abstractmethod
    async def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """Transcribe audio file."""
        pass


class VisionProvider(ABC):
    """Abstract base class for vision/video analysis providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return provider name."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is healthy."""
        pass
    
    @abstractmethod
    async def analyze_image(
        self,
        image_path: str,
        prompt: str,
        model: str
    ) -> str:
        """Analyze an image with a prompt."""
        pass
    
    @abstractmethod
    async def analyze_video(
        self,
        video_path: str,
        prompt: str,
        model: str
    ) -> str:
        """Analyze a video with a prompt."""
        pass
