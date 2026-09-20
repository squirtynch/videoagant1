"""
AI Video Agent - Whisper API Transcription Provider

Transcription via Whisper-compatible HTTP API (e.g., OpenAI API, local servers).
"""

import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
import structlog
import httpx

from .interfaces import (
    TranscriptionProvider, 
    Transcript, 
    TranscriptSegment,
    TranscriptionError
)

logger = structlog.get_logger(__name__)


class WhisperAPIProvider(TranscriptionProvider):
    """Whisper transcription via HTTP API."""
    
    def __init__(
        self, 
        api_key: str,
        endpoint: str = "https://api.openai.com/v1",
        model: str = "whisper-1",
        timeout: int = 300
    ):
        """
        Initialize Whisper API provider.
        
        Args:
            api_key: API key for authentication
            endpoint: Base API endpoint URL
            model: Model identifier (e.g., 'whisper-1')
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def name(self) -> str:
        return f"Whisper API ({self.model})"
    
    @property
    def supports_languages(self) -> List[str]:
        """API supports same languages as Whisper model."""
        return [
            "en", "zh", "de", "es", "ru", "ko", "fr", "ja", "pt", "tr",
            "pl", "ca", "nl", "ar", "sv", "it", "id", "hi", "fi", "vi",
            "he", "uk", "el", "ms", "cs", "ro", "da", "hu", "ta", "no",
            "th", "ur", "hr", "bg", "lt", "la", "mi", "ml", "cy", "sk",
            "te", "fa", "lv", "bn", "sr", "az", "sl", "kn", "et", "mk",
            "br", "eu", "is", "hy", "ne", "mn", "bs", "kk", "sq", "sw",
        ]
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
            )
        return self._client
    
    async def close(self):
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def transcribe(
        self, 
        audio_path: str, 
        language: Optional[str] = None
    ) -> Transcript:
        """Transcribe audio file via API."""
        
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        client = await self._get_client()
        
        try:
            logger.info(
                f"Starting API transcription",
                file=audio_path,
                language=language or "auto",
                endpoint=self.endpoint
            )
            
            # Prepare form data for file upload
            with open(audio_path, "rb") as f:
                files = {"file": f}
                data = {
                    "model": self.model,
                    "response_format": "verbose_json",  # Get segments with timestamps
                }
                
                if language:
                    data["language"] = language
                
                response = await client.post(
                    f"{self.endpoint}/audio/transcriptions",
                    files=files,
                    data=data,
                )
            
            if response.status_code != 200:
                logger.error(
                    f"API transcription failed: {response.status_code}",
                    body=response.text[:500]
                )
                raise TranscriptionError(
                    f"API error: {response.status_code} - {response.text[:200]}",
                    provider=self.name
                )
            
            result = response.json()
            
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
                    "model": self.model,
                    "endpoint": self.endpoint,
                    "source_file": str(path),
                    "api_provider": "whisper-api",
                }
            )
            
            logger.info(
                f"API transcription completed",
                segments=len(segments),
                duration=transcript.duration
            )
            
            return transcript
            
        except httpx.RequestError as e:
            logger.error(f"API request failed: {e}")
            raise TranscriptionError(
                f"API request failed: {e}",
                provider=self.name
            )
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise TranscriptionError(
                f"Transcription failed: {e}",
                provider=self.name
            )
    
    async def check_health(self) -> bool:
        """Check if API is accessible."""
        try:
            client = await self._get_client()
            
            # Simple health check - try to get models list
            response = await client.get(f"{self.endpoint}/models")
            
            if response.status_code == 200:
                models = response.json().get("data", [])
                # Check if our model is available
                model_ids = [m.get("id") for m in models]
                return any(self.model in mid for mid in model_ids)
            
            return False
            
        except Exception as e:
            logger.warning(f"API health check failed: {e}")
            return False
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return API capabilities."""
        return {
            "provider_type": "cloud",
            "model": self.model,
            "endpoint": self.endpoint,
            "supports_languages": self.supports_languages,
            "auto_language_detection": True,
            "word_timestamps": True,
            "speaker_diarization": False,
            "max_audio_duration": "25MB",  # API limit
            "requires_internet": True,
        }
