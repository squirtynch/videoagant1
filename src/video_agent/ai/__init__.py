"""
AI Video Agent - AI Layer

Provides AI capabilities through various providers.
"""

from .interfaces import (
    AIProvider,
    TranscriptionProvider,
    VisionProvider,
    Message,
    ModelInfo,
    AIResponse,
    TranscriptionResult,
)
from .registry import ProviderRegistry, ModelRegistry
from .capabilities import CapabilityRegistry, Capability
from .router import AIRouter
from .providers import (
    OpenAICompatibleProvider,
    MockProvider,
    WhisperTranscriptionProvider,
    LocalWhisperProvider,
)

__all__ = [
    # Interfaces
    "AIProvider",
    "TranscriptionProvider",
    "VisionProvider",
    "Message",
    "ModelInfo",
    "AIResponse",
    "TranscriptionResult",
    # Registries
    "CapabilityRegistry",
    "Capability",
    "ProviderRegistry",
    "ModelRegistry",
    # Router
    "AIRouter",
    # Providers
    "OpenAICompatibleProvider",
    "MockProvider",
    "WhisperTranscriptionProvider",
    "LocalWhisperProvider",
]