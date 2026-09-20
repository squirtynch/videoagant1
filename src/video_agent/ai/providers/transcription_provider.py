"""
AI Video Agent - Transcription Provider (Whisper-compatible)

Supports local Whisper and Whisper-compatible APIs.
"""

import os
from typing import Optional, List, Dict, Any
import asyncio
import structlog
import httpx

from ..interfaces import TranscriptionProvider, TranscriptionResult

logger = structlog.get_logger(__name__)


class WhisperTranscriptionProvider(TranscriptionProvider):
    """Whisper-based transcription provider."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:8000",  # Local Whisper API
        model: str = "whisper-1",
        provider_id: str = "whisper",
        timeout: float = 300.0,  # Long timeout for transcription
        language: Optional[str] = None
    ):
        self._api_key = api_key
        self._base_url = base_url.rstrip('/')
        self._model = model
        self._provider_id = provider_id
        self._timeout = timeout
        self._default_language = language
        self._is_healthy: bool = False
        
    @property
    def name(self) -> str:
        return f"Whisper Transcription ({self._provider_id})"
    
    async def health_check(self) -> bool:
        """Check if Whisper service is accessible."""
        try:
            # For local Whisper, check if the endpoint is reachable
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Try a simple GET request to the base URL
                response = await client.get(self._base_url)
                
                # If we get any response (even 404), the service is running
                self._is_healthy = True
                logger.info(f"Whisper provider {self._provider_id} is accessible")
                return True
                
        except httpx.ConnectError:
            logger.warning(f"Whisper provider {self._provider_id} not accessible at {self._base_url}")
            self._is_healthy = False
            return False
        except Exception as e:
            logger.error(f"Whisper health check error: {e}")
            self._is_healthy = False
            return False
    
    async def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """Transcribe an audio file using Whisper API."""
        
        target_language = language or self._default_language
        
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                # Prepare the file for upload
                with open(audio_path, 'rb') as audio_file:
                    files = {
                        'file': (os.path.basename(audio_path), audio_file, 'audio/wav'),
                        'model': (None, self._model),
                        'response_format': (None, 'verbose_json'),
                    }
                    
                    if target_language:
                        files['language'] = (None, target_language)
                    
                    headers = {}
                    if self._api_key:
                        headers['Authorization'] = f'Bearer {self._api_key}'
                    
                    response = await client.post(
                        f"{self._base_url}/v1/audio/transcriptions",
                        headers=headers,
                        files=files
                    )
                
                if response.status_code != 200:
                    error_msg = f"Transcription API error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
                
                data = response.json()
                
                # Parse the verbose JSON response
                text = data.get('text', '')
                duration = data.get('duration', 0.0)
                detected_language = data.get('language', target_language or 'unknown')
                
                # Process segments with timestamps
                segments_data = data.get('segments', [])
                segments = []
                
                for seg in segments_data:
                    segment = {
                        'start': seg.get('start', 0.0),
                        'end': seg.get('end', 0.0),
                        'text': seg.get('text', ''),
                        'confidence': seg.get('confidence', 1.0)
                    }
                    segments.append(segment)
                
                result = TranscriptionResult(
                    language=detected_language,
                    duration=duration,
                    segments=segments,
                    text=text
                )
                
                logger.info(
                    f"Transcribed {os.path.basename(audio_path)}: "
                    f"{len(segments)} segments, {duration:.1f}s, language={detected_language}"
                )
                
                return result
                
        except httpx.ConnectError as e:
            logger.error(f"Cannot connect to Whisper service: {e}")
            raise RuntimeError(f"Whisper service unavailable: {e}")
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise RuntimeError(f"Transcription failed: {e}")


class LocalWhisperProvider(TranscriptionProvider):
    """
    Local Whisper using the whisper library directly.
    
    This provider uses the whisper Python package for offline transcription.
    """
    
    def __init__(
        self,
        model_size: str = "base",
        provider_id: str = "whisper-local",
        device: str = "cpu",
        language: Optional[str] = None
    ):
        self._model_size = model_size
        self._provider_id = provider_id
        self._device = device
        self._default_language = language
        self._model = None
        self._is_loaded = False
        
    @property
    def name(self) -> str:
        return f"Local Whisper ({self._model_size})"
    
    def _load_model(self):
        """Load the Whisper model lazily."""
        if self._model is not None:
            return
        
        try:
            import whisper
            self._model = whisper.load_model(self._model_size, device=self._device)
            self._is_loaded = True
            logger.info(f"Loaded Whisper model: {self._model_size} on {self._device}")
        except ImportError:
            logger.error("Whisper library not installed. Install with: pip install openai-whisper")
            raise RuntimeError("Whisper library not available")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if Whisper model can be loaded."""
        try:
            # Try to import whisper
            import whisper
            
            # Don't actually load the model during health check (it's slow)
            # Just verify the library is available
            self._is_healthy = True
            logger.info(f"Whisper library available for {self._provider_id}")
            return True
            
        except ImportError:
            logger.warning(f"Whisper library not available for {self._provider_id}")
            self._is_healthy = False
            return False
    
    async def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """Transcribe audio using local Whisper model."""
        
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Load model if not already loaded
        await asyncio.get_event_loop().run_in_executor(None, self._load_model)
        
        try:
            # Run transcription in executor to avoid blocking
            def run_transcription():
                import whisper
                
                options = {
                    'task': 'transcribe',
                }
                
                if language:
                    options['language'] = language
                elif self._default_language:
                    options['language'] = self._default_language
                
                # Transcribe
                result = self._model.transcribe(audio_path, **options)
                return result
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, run_transcription)
            
            # Parse result
            text = result.get('text', '')
            detected_language = result.get('language', language or self._default_language or 'unknown')
            
            # Process segments
            segments_data = result.get('segments', [])
            segments = []
            
            for seg in segments_data:
                segment = {
                    'start': float(seg.get('start', 0.0)),
                    'end': float(seg.get('end', 0.0)),
                    'text': seg.get('text', ''),
                    'confidence': 1.0  # Local whisper doesn't always provide confidence
                }
                segments.append(segment)
            
            # Calculate duration from segments or file
            duration = 0.0
            if segments:
                duration = max(seg['end'] for seg in segments)
            
            transcription_result = TranscriptionResult(
                    language=detected_language or 'unknown',
                    duration=duration,
                    segments=segments,
                    text=text
                )
            
            logger.info(
                f"Transcribed {os.path.basename(audio_path)} with local Whisper: "
                f"{len(segments)} segments, {duration:.1f}s"
            )
            
            return transcription_result
            
        except Exception as e:
            logger.error(f"Local Whisper transcription error: {e}")
            raise RuntimeError(f"Transcription failed: {e}")
