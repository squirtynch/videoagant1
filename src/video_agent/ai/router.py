"""
AI Video Agent - AI Router

Routes AI requests to appropriate providers based on capabilities and availability.
"""

from typing import Optional, List, Dict, Any
import structlog

from .interfaces import AIProvider, Message, ModelInfo, AIResponse, TranscriptionProvider, TranscriptionResult
from .registry import ProviderRegistry, ModelRegistry
from .capabilities import CapabilityRegistry, Capability
from ..domain.models import ModelConfiguration

logger = structlog.get_logger(__name__)


class AIRouter:
    """
    Routes AI requests to appropriate providers.
    
    Handles provider selection, failover, and capability-based routing.
    """
    
    def __init__(
        self,
        provider_registry: ProviderRegistry,
        model_registry: ModelRegistry,
        capability_registry: CapabilityRegistry
    ):
        self._provider_registry = provider_registry
        self._model_registry = model_registry
        self._capability_registry = capability_registry
        
    async def select_best_provider(
        self,
        required_capability: Capability,
        preferred_provider_type: Optional[str] = None
    ) -> Optional[tuple[AIProvider, ModelConfiguration]]:
        """
        Select the best provider and model for a required capability.
        
        Returns (provider, model) tuple or None if no suitable provider found.
        """
        # Find models with the required capability
        suitable_models = []
        
        for model in self._model_registry.list_models():
            if not model.enabled:
                continue
            
            if required_capability.value in model.capabilities:
                suitable_models.append(model)
        
        if not suitable_models:
            logger.warning(f"No models found with capability: {required_capability.value}")
            return None
        
        # Filter by provider type if specified
        if preferred_provider_type:
            filtered_models = [
                m for m in suitable_models 
                if any(
                    p.provider_type == preferred_provider_type
                    for p in [self._provider_registry.get(m.provider_id)]
                    if p is not None
                )
            ]
            if filtered_models:
                suitable_models = filtered_models
        
        # Try each model until one works
        for model in suitable_models:
            provider = self._provider_registry.get(model.provider_id)
            
            if provider is None:
                logger.warning(f"Provider {model.provider_id} not found")
                continue
            
            # Check provider health
            try:
                is_healthy = await provider.health_check()
                if not is_healthy:
                    logger.warning(f"Provider {provider.name} is unhealthy")
                    continue
            except Exception as e:
                logger.error(f"Health check failed for {provider.name}: {e}")
                continue
            
            logger.info(f"Selected provider {provider.name} with model {model.id}")
            return (provider, model)
        
        logger.warning(f"No healthy providers found for capability: {required_capability.value}")
        return None
    
    async def chat_completion(
        self,
        messages: List[Message],
        required_capability: Capability = Capability.TEXT_GENERATION,
        preferred_provider_type: Optional[str] = None,
        model_override: Optional[str] = None,
        **kwargs
    ) -> AIResponse:
        """
        Send chat completion request using the best available provider.
        
        Args:
            messages: Chat messages
            required_capability: Required capability for the task
            preferred_provider_type: Preferred provider type (OPENAI_COMPATIBLE, LOCAL, etc.)
            model_override: Specific model ID to use (bypasses selection)
            **kwargs: Additional arguments for chat_completion
            
        Returns:
            AIResponse from the selected provider
        """
        # Use specific model if provided
        if model_override:
            model = self._model_registry.get_model(model_override)
            if model is None:
                raise ValueError(f"Model not found: {model_override}")
            
            provider = self._provider_registry.get(model.provider_id)
            if provider is None:
                raise ValueError(f"Provider not found for model: {model.id}")
        else:
            # Select best provider
            result = await self.select_best_provider(
                required_capability,
                preferred_provider_type
            )
            
            if result is None:
                raise RuntimeError(
                    f"No available provider for capability: {required_capability.value}"
                )
            
            provider, model = result
        
        # Execute chat completion
        try:
            response = await provider.chat_completion(
                messages=messages,
                model=model.model_identifier,
                **kwargs
            )
            
            logger.debug(
                f"Chat completion via {provider.name}/{model.id}: "
                f"{len(response.content)} chars"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise
    
    async def structured_output(
        self,
        messages: List[Message],
        response_schema: Dict[str, Any],
        required_capability: Capability = Capability.STRUCTURED_OUTPUT,
        preferred_provider_type: Optional[str] = None,
        model_override: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Request structured JSON output using the best available provider.
        
        Args:
            messages: Chat messages
            response_schema: JSON schema for the expected output
            required_capability: Required capability
            preferred_provider_type: Preferred provider type
            model_override: Specific model ID to use
            **kwargs: Additional arguments
            
        Returns:
            Parsed JSON response
        """
        # Select provider
        if model_override:
            model = self._model_registry.get_model(model_override)
            if model is None:
                raise ValueError(f"Model not found: {model_override}")
            
            provider = self._provider_registry.get(model.provider_id)
            if provider is None:
                raise ValueError(f"Provider not found for model: {model.id}")
        else:
            result = await self.select_best_provider(
                required_capability,
                preferred_provider_type
            )
            
            if result is None:
                raise RuntimeError(
                    f"No available provider for capability: {required_capability.value}"
                )
            
            provider, model = result
        
        # Execute structured output
        try:
            response = await provider.structured_output(
                messages=messages,
                model=model.model_identifier,
                response_schema=response_schema,
                **kwargs
            )
            
            logger.debug(
                f"Structured output via {provider.name}/{model.id}: "
                f"{list(response.keys())}"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Structured output failed: {e}")
            raise
    
    async def transcribe(
        self,
        transcription_provider: TranscriptionProvider,
        audio_path: str,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Transcribe audio using the specified transcription provider.
        
        Args:
            transcription_provider: The transcription provider to use
            audio_path: Path to the audio file
            language: Optional language code
            
        Returns:
            TranscriptionResult with text and segments
        """
        try:
            result = await transcription_provider.transcribe(
                audio_path=audio_path,
                language=language
            )
            
            logger.info(
                f"Transcribed {audio_path}: {len(result.segments)} segments, "
                f"{result.duration:.1f}s, language={result.language}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
    
    def list_available_models(
        self,
        capability_filter: Optional[Capability] = None
    ) -> List[ModelConfiguration]:
        """
        List available models, optionally filtered by capability.
        
        Args:
            capability_filter: Filter models by capability
            
        Returns:
            List of available model configurations
        """
        models = self._model_registry.list_models()
        
        if capability_filter is None:
            return [m for m in models if m.enabled]
        
        return [
            m for m in models 
            if m.enabled and capability_filter.value in m.capabilities
        ]
    
    async def refresh_all_providers(self) -> Dict[str, bool]:
        """
        Refresh health status for all registered providers.
        
        Returns:
            Dict mapping provider_id to health status
        """
        return await self._provider_registry.health_check_all()
