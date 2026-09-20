"""
AI Video Agent - AI Router Tests

Tests for the AI routing system.
"""

import pytest
import asyncio

from src.video_agent.ai.router import AIRouter
from src.video_agent.ai.registry import ProviderRegistry, ModelRegistry
from src.video_agent.ai.capabilities import CapabilityRegistry, Capability
from src.video_agent.ai.providers.mock_provider import MockProvider
from src.video_agent.ai.interfaces import Message
from src.video_agent.domain.models import ModelConfiguration


@pytest.fixture
def registries():
    """Create fresh registries for testing."""
    provider_registry = ProviderRegistry()
    model_registry = ModelRegistry()
    capability_registry = CapabilityRegistry()
    
    return provider_registry, model_registry, capability_registry


@pytest.fixture
def router_with_mock_provider(registries):
    """Create router with a mock provider registered."""
    provider_registry, model_registry, capability_registry = registries
    
    # Create and register mock provider
    mock_provider = MockProvider(provider_id="test-router", delay=0.01)
    provider_registry.register("test-router", mock_provider)
    
    # Register models
    models_data = [
        {
            "id": "test-router:text-model",
            "provider_id": "test-router",
            "model_identifier": "mock-text-v1",
            "capabilities": [
                Capability.TEXT_GENERATION.value,
                Capability.STRUCTURED_OUTPUT.value,
            ],
        },
        {
            "id": "test-router:vision-model",
            "provider_id": "test-router",
            "model_identifier": "mock-vision-v1",
            "capabilities": [
                Capability.TEXT_GENERATION.value,
                Capability.VISION_ANALYSIS.value,
            ],
        },
    ]
    
    for model_data in models_data:
        model = ModelConfiguration(
            id=model_data["id"],
            provider_id=model_data["provider_id"],
            model_identifier=model_data["model_identifier"],
            name=f"Mock {model_data['model_identifier']}",
            capabilities=[Capability(c) for c in model_data["capabilities"]],
            context_limit=8192,
            enabled=True
        )
        model_registry.register_model(model, model_data["provider_id"])
        
        # Register capabilities
        capability_registry.register_model_capabilities(
            model.id,
            [Capability(c) for c in model.capabilities]
        )
    
    router = AIRouter(
        provider_registry=provider_registry,
        model_registry=model_registry,
        capability_registry=capability_registry
    )
    
    return router, provider_registry, model_registry, capability_registry


class TestAIRouter:
    """Tests for AIRouter."""
    
    @pytest.mark.asyncio
    async def test_select_best_provider(self, router_with_mock_provider):
        """Test selecting best provider for a capability."""
        router, *_ = router_with_mock_provider
        
        result = await router.select_best_provider(Capability.TEXT_GENERATION)
        
        assert result is not None
        provider, model = result
        assert isinstance(provider, MockProvider)
        assert model.id == "test-router:text-model"
    
    @pytest.mark.asyncio
    async def test_select_best_provider_no_capability(self, registries):
        """Test selection when no provider has required capability."""
        provider_registry, model_registry, capability_registry = registries
        
        # Register provider without needed capability
        mock_provider = MockProvider(provider_id="limited", delay=0.01)
        provider_registry.register("limited", mock_provider)
        
        model = ModelConfiguration(
            id="limited:basic",
            provider_id="limited",
            model_identifier="basic-v1",
            name="Basic Model",
            capabilities=[Capability.TEXT_GENERATION],
            context_limit=4096,
            enabled=True
        )
        model_registry.register_model(model, "limited")
        
        router = AIRouter(
            provider_registry=provider_registry,
            model_registry=model_registry,
            capability_registry=capability_registry
        )
        
        # Try to find provider with vision capability (doesn't exist)
        result = await router.select_best_provider(Capability.VISION_ANALYSIS)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_chat_completion(self, router_with_mock_provider):
        """Test chat completion through router."""
        router, *_ = router_with_mock_provider
        
        messages = [
            Message(role="user", content="Hello!")
        ]
        
        response = await router.chat_completion(
            messages=messages,
            required_capability=Capability.TEXT_GENERATION
        )
        
        assert response.content is not None
        assert len(response.content) > 0
        assert "mock" in response.content.lower()
    
    @pytest.mark.asyncio
    async def test_chat_completion_with_override(self, router_with_mock_provider):
        """Test chat completion with model override."""
        router, *_ = router_with_mock_provider
        
        messages = [Message(role="user", content="Test")]
        
        response = await router.chat_completion(
            messages=messages,
            model_override="test-router:text-model"
        )
        
        assert response is not None
    
    @pytest.mark.asyncio
    async def test_chat_completion_invalid_model(self, router_with_mock_provider):
        """Test chat completion with invalid model override."""
        router, *_ = router_with_mock_provider
        
        messages = [Message(role="user", content="Test")]
        
        with pytest.raises(ValueError, match="Model not found"):
            await router.chat_completion(
                messages=messages,
                model_override="nonexistent-model"
            )
    
    @pytest.mark.asyncio
    async def test_structured_output(self, router_with_mock_provider):
        """Test structured output through router."""
        router, *_ = router_with_mock_provider
        
        messages = [Message(role="user", content="Give me data")]
        
        schema = {
            "type": "object",
            "properties": {
                "result": {"type": "string"}
            },
            "required": ["result"]
        }
        
        result = await router.structured_output(
            messages=messages,
            response_schema=schema,
            required_capability=Capability.STRUCTURED_OUTPUT
        )
        
        assert isinstance(result, dict)
        assert "result" in result
    
    @pytest.mark.asyncio
    async def test_list_available_models(self, router_with_mock_provider):
        """Test listing available models."""
        router, *_ = router_with_mock_provider
        
        # List all models
        all_models = router.list_available_models()
        assert len(all_models) == 2
        
        # Filter by capability
        text_models = router.list_available_models(Capability.TEXT_GENERATION)
        assert len(text_models) == 2
        
        vision_models = router.list_available_models(Capability.VISION_ANALYSIS)
        assert len(vision_models) == 1
    
    @pytest.mark.asyncio
    async def test_refresh_providers(self, router_with_mock_provider):
        """Test refreshing provider health status."""
        router, *_ = router_with_mock_provider
        
        health_status = await router.refresh_all_providers()
        
        assert "test-router" in health_status
        assert health_status["test-router"] is True
    
    @pytest.mark.asyncio
    async def test_preferred_provider_type(self, registries):
        """Test filtering by preferred provider type."""
        provider_registry, model_registry, capability_registry = registries
        
        # Register two providers
        mock1 = MockProvider(provider_id="provider1", delay=0.01)
        mock2 = MockProvider(provider_id="provider2", delay=0.01)
        
        provider_registry.register("provider1", mock1)
        provider_registry.register("provider2", mock2)
        
        # Register models for both
        for pid in ["provider1", "provider2"]:
            model = ModelConfiguration(
                id=f"{pid}:model",
                provider_id=pid,
                model_identifier="model-v1",
                name=f"Model {pid}",
                capabilities=[Capability.TEXT_GENERATION],
                context_limit=4096,
                enabled=True
            )
            model_registry.register_model(model, pid)
        
        router = AIRouter(
            provider_registry=provider_registry,
            model_registry=model_registry,
            capability_registry=capability_registry
        )
        
        # Should work with either provider
        result = await router.select_best_provider(
            Capability.TEXT_GENERATION,
            preferred_provider_type="MOCK"
        )
        
        assert result is not None
        provider, model = result
        assert provider.provider_type == "MOCK"


class TestRouterFailover:
    """Tests for provider failover behavior."""
    
    @pytest.mark.asyncio
    async def test_failover_on_unhealthy_provider(self, registries):
        """Test that router fails over to healthy provider."""
        provider_registry, model_registry, capability_registry = registries
        
        # Create one failing and one healthy provider
        failing_provider = MockProvider(
            provider_id="failing",
            simulate_failure=True,
            delay=0.01
        )
        healthy_provider = MockProvider(
            provider_id="healthy",
            simulate_failure=False,
            delay=0.01
        )
        
        provider_registry.register("failing", failing_provider)
        provider_registry.register("healthy", healthy_provider)
        
        # Register models
        for pid in ["failing", "healthy"]:
            model = ModelConfiguration(
                id=f"{pid}:model",
                provider_id=pid,
                model_identifier="model-v1",
                name=f"Model {pid}",
                capabilities=[Capability.TEXT_GENERATION],
                context_limit=4096,
                enabled=True
            )
            model_registry.register_model(model, pid)
        
        router = AIRouter(
            provider_registry=provider_registry,
            model_registry=model_registry,
            capability_registry=capability_registry
        )
        
        # Should select healthy provider
        result = await router.select_best_provider(Capability.TEXT_GENERATION)
        
        assert result is not None
        provider, model = result
        assert provider._provider_id == "healthy"
