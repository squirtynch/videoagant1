"""
AI Video Agent - Capability Registry

Manages AI capabilities across providers and models.
"""

from typing import Dict, List, Optional, Set
from enum import Enum
import structlog

from ..domain.models import Capability

logger = structlog.get_logger(__name__)


class CapabilityRegistry:
    """Registry for tracking AI capabilities across providers."""
    
    def __init__(self):
        self._capabilities: Dict[str, Set[Capability]] = {}  # model_id -> capabilities
        self._provider_capabilities: Dict[str, Set[Capability]] = {}  # provider_id -> capabilities
    
    def register_model_capabilities(
        self, 
        model_id: str, 
        capabilities: List[Capability]
    ):
        """Register capabilities for a model."""
        self._capabilities[model_id] = set(capabilities)
        logger.info(f"Registered {len(capabilities)} capabilities for model {model_id}")
    
    def register_provider_capabilities(
        self,
        provider_id: str,
        capabilities: List[Capability]
    ):
        """Register capabilities for a provider."""
        self._provider_capabilities[provider_id] = set(capabilities)
        logger.info(f"Registered {len(capabilities)} capabilities for provider {provider_id}")
    
    def get_capabilities(self, model_id: str) -> Set[Capability]:
        """Get capabilities for a model."""
        return self._capabilities.get(model_id, set())
    
    def has_capability(self, model_id: str, capability: Capability) -> bool:
        """Check if a model has a specific capability."""
        model_caps = self._capabilities.get(model_id, set())
        return capability in model_caps
    
    def find_models_with_capability(
        self, 
        capability: Capability
    ) -> List[str]:
        """Find all models that have a specific capability."""
        return [
            model_id for model_id, caps in self._capabilities.items()
            if capability in caps
        ]
    
    def list_all_capabilities(self) -> Set[Capability]:
        """List all registered capabilities."""
        all_caps = set()
        for caps in self._capabilities.values():
            all_caps.update(caps)
        return all_caps
    
    def remove_model(self, model_id: str):
        """Remove a model from the registry."""
        if model_id in self._capabilities:
            del self._capabilities[model_id]
            logger.info(f"Removed model {model_id} from capability registry")
    
    def clear(self):
        """Clear all registrations."""
        self._capabilities.clear()
        self._provider_capabilities.clear()
        logger.info("Cleared capability registry")
