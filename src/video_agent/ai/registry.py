"""
AI Video Agent - Provider and Model Registries

Manages AI providers and available models.
"""

from typing import Dict, List, Optional
import structlog

from .interfaces import AIProvider, ModelInfo
from ..domain.models import ModelProvider, ModelConfiguration, Capability

logger = structlog.get_logger(__name__)


class ProviderRegistry:
    """Registry for AI providers."""
    
    def __init__(self):
        self._providers: Dict[str, AIProvider] = {}
    
    def register(self, provider_id: str, provider: AIProvider):
        """Register an AI provider."""
        self._providers[provider_id] = provider
        logger.info(f"Registered AI provider: {provider_id} ({provider.provider_type})")
    
    def get(self, provider_id: str) -> Optional[AIProvider]:
        """Get a provider by ID."""
        return self._providers.get(provider_id)
    
    def list_providers(self) -> Dict[str, AIProvider]:
        """List all registered providers."""
        return dict(self._providers)
    
    def unregister(self, provider_id: str):
        """Unregister a provider."""
        if provider_id in self._providers:
            del self._providers[provider_id]
            logger.info(f"Unregistered provider: {provider_id}")
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all registered providers."""
        results = {}
        for provider_id, provider in self._providers.items():
            try:
                is_healthy = await provider.health_check()
                results[provider_id] = is_healthy
                logger.info(f"Provider {provider_id} health: {'OK' if is_healthy else 'UNHEALTHY'}")
            except Exception as e:
                results[provider_id] = False
                logger.error(f"Provider {provider_id} health check failed: {e}")
        return results
    
    def clear(self):
        """Clear all registrations."""
        self._providers.clear()


class ModelRegistry:
    """Registry for AI models."""
    
    def __init__(self):
        self._models: Dict[str, ModelConfiguration] = {}
        self._provider_models: Dict[str, List[str]] = {}  # provider_id -> [model_ids]
    
    def register_model(self, model: ModelConfiguration, provider_id: str):
        """Register a model configuration."""
        self._models[model.id] = model
        
        if provider_id not in self._provider_models:
            self._provider_models[provider_id] = []
        self._provider_models[provider_id].append(model.id)
        
        logger.info(f"Registered model: {model.id} ({model.model_identifier})")
    
    def get_model(self, model_id: str) -> Optional[ModelConfiguration]:
        """Get a model by ID."""
        return self._models.get(model_id)
    
    def list_models(self) -> List[ModelConfiguration]:
        """List all registered models."""
        return list(self._models.values())
    
    def list_models_by_provider(self, provider_id: str) -> List[ModelConfiguration]:
        """List models for a specific provider."""
        model_ids = self._provider_models.get(provider_id, [])
        return [
            self._models[model_id] 
            for model_id in model_ids 
            if model_id in self._models
        ]
    
    def find_model_by_capability(
        self, 
        capability: Capability
    ) -> Optional[ModelConfiguration]:
        """Find a model that supports a specific capability."""
        for model in self._models.values():
            if not model.enabled:
                continue
            if capability in model.capabilities:
                return model
        return None
    
    def update_model_health(
        self, 
        model_id: str, 
        health_status: str
    ):
        """Update model health status."""
        if model_id in self._models:
            # Note: ModelConfiguration doesn't have health_status field directly
            # This would need to be tracked separately or added to the model
            logger.info(f"Updated health for model {model_id}: {health_status}")
    
    def unregister_model(self, model_id: str):
        """Unregister a model."""
        if model_id in self._models:
            del self._models[model_id]
            
            # Remove from provider lists
            for provider_id in self._provider_models:
                if model_id in self._provider_models[provider_id]:
                    self._provider_models[provider_id].remove(model_id)
            
            logger.info(f"Unregistered model: {model_id}")
    
    def clear(self):
        """Clear all registrations."""
        self._models.clear()
        self._provider_models.clear()
