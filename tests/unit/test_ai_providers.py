"""
AI Video Agent - AI Provider Tests

Tests for AI provider implementations.
"""

import pytest
import asyncio
from typing import List

from src.video_agent.ai.interfaces import Message, ModelInfo
from src.video_agent.ai.providers.mock_provider import MockProvider
from src.video_agent.ai.providers.openai_provider import OpenAICompatibleProvider
from src.video_agent.ai.capabilities import Capability


class TestMockProvider:
    """Tests for MockProvider."""
    
    @pytest.fixture
    def mock_provider(self):
        return MockProvider(provider_id="test-mock", delay=0.01)
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_provider):
        """Test mock provider health check."""
        result = await mock_provider.health_check()
        assert result is True
        assert mock_provider.name == "Mock Provider (test-mock)"
        assert mock_provider.provider_type == "MOCK"
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test mock provider simulated failure."""
        provider = MockProvider(provider_id="failing-mock", simulate_failure=True, delay=0.01)
        result = await provider.health_check()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_list_models(self, mock_provider):
        """Test listing models from mock provider."""
        models = await mock_provider.list_models()
        
        assert isinstance(models, list)
        assert len(models) > 0
        
        # Check model structure
        for model in models:
            assert isinstance(model, ModelInfo)
            assert model.id.startswith("test-mock:")
            assert model.enabled is True
            assert isinstance(model.capabilities, list)
    
    @pytest.mark.asyncio
    async def test_chat_completion(self, mock_provider):
        """Test chat completion with mock provider."""
        messages = [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="Hello, how are you?")
        ]
        
        response = await mock_provider.chat_completion(
            messages=messages,
            model="test-mock:mock-text-model",
            temperature=0.7
        )
        
        assert response.content is not None
        assert len(response.content) > 0
        assert "mock" in response.content.lower()
        assert response.usage is not None
        assert "prompt_tokens" in response.usage
    
    @pytest.mark.asyncio
    async def test_structured_output(self, mock_provider):
        """Test structured output from mock provider."""
        messages = [
            Message(role="user", content="Give me data")
        ]
        
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "active": {"type": "boolean"}
            },
            "required": ["name"]
        }
        
        result = await mock_provider.structured_output(
            messages=messages,
            model="test-mock:mock-text-model",
            response_schema=schema
        )
        
        assert isinstance(result, dict)
        assert "name" in result
        assert result["name"] == "mock_name_value"
        assert result["age"] == 42
        assert result["active"] is True
    
    @pytest.mark.asyncio
    async def test_request_counting(self, mock_provider):
        """Test that request counting works."""
        assert mock_provider.get_request_count() == 0
        
        await mock_provider.health_check()
        await mock_provider.list_models()
        
        # Chat completion increments count
        await mock_provider.chat_completion(
            messages=[Message(role="user", content="test")],
            model="test-mock:mock-text-model"
        )
        
        assert mock_provider.get_request_count() == 1
        
        # Structured output increments count
        await mock_provider.structured_output(
            messages=[Message(role="user", content="test")],
            model="test-mock:mock-text-model",
            response_schema={}
        )
        
        assert mock_provider.get_request_count() == 2
    
    @pytest.mark.asyncio
    async def test_reset(self, mock_provider):
        """Test provider reset."""
        await mock_provider.chat_completion(
            messages=[Message(role="user", content="test")],
            model="test-mock:mock-text-model"
        )
        
        assert mock_provider.get_request_count() > 0
        
        mock_provider.reset()
        assert mock_provider.get_request_count() == 0


class TestOpenAICompatibleProvider:
    """Tests for OpenAICompatibleProvider."""
    
    def test_initialization(self):
        """Test provider initialization."""
        provider = OpenAICompatibleProvider(
            api_key="test-key",
            base_url="https://api.example.com/v1",
            provider_id="test-openai",
            timeout=60.0
        )
        
        assert provider.name == "OpenAI Compatible (test-openai)"
        assert provider.provider_type == "OPENAI_COMPATIBLE"
        assert provider._base_url == "https://api.example.com/v1"
        assert provider._timeout == 60.0
    
    def test_base_url_normalization(self):
        """Test that base URL is normalized."""
        provider = OpenAICompatibleProvider(
            api_key="test-key",
            base_url="https://api.example.com/v1/"
        )
        
        assert provider._base_url == "https://api.example.com/v1"
    
    def test_infer_capabilities(self):
        """Test capability inference from model IDs."""
        provider = OpenAICompatibleProvider(api_key="test-key")
        
        # Vision models
        vision_caps = provider._infer_capabilities("gpt-4-vision-preview")
        assert Capability.VISION_ANALYSIS in vision_caps
        
        # GPT-4 models
        gpt4_caps = provider._infer_capabilities("gpt-4-turbo")
        assert Capability.STRUCTURED_OUTPUT in gpt4_caps
        assert Capability.TOOL_CALLING in gpt4_caps
        
        # Basic models
        basic_caps = provider._infer_capabilities("gpt-3.5-turbo")
        assert Capability.TEXT_GENERATION in basic_caps
    
    def test_context_limits(self):
        """Test context limit detection."""
        provider = OpenAICompatibleProvider(api_key="test-key")
        
        assert provider._get_context_limit("gpt-4-128k") == 128000
        assert provider._get_context_limit("gpt-4-32k") == 32000
        assert provider._get_context_limit("gpt-4-16k") == 16000
        assert provider._get_context_limit("gpt-4-turbo") == 8192
        assert provider._get_context_limit("gpt-3.5-turbo") == 4096
        assert provider._get_context_limit("unknown-model") == 4096


class TestCapabilityRegistry:
    """Tests for CapabilityRegistry."""
    
    @pytest.fixture
    def registry(self):
        from src.video_agent.ai.capabilities import CapabilityRegistry
        return CapabilityRegistry()
    
    def test_register_model_capabilities(self, registry):
        """Test registering model capabilities."""
        caps = [Capability.TEXT_GENERATION, Capability.STRUCTURED_OUTPUT]
        registry.register_model_capabilities("model-1", caps)
        
        assert registry.has_capability("model-1", Capability.TEXT_GENERATION)
        assert registry.has_capability("model-1", Capability.STRUCTURED_OUTPUT)
        assert not registry.has_capability("model-1", Capability.VISION_ANALYSIS)
    
    def test_find_models_with_capability(self, registry):
        """Test finding models by capability."""
        registry.register_model_capabilities(
            "model-1", 
            [Capability.TEXT_GENERATION, Capability.VISION_ANALYSIS]
        )
        registry.register_model_capabilities(
            "model-2",
            [Capability.TEXT_GENERATION, Capability.AUDIO_TRANSCRIPTION]
        )
        registry.register_model_capabilities(
            "model-3",
            [Capability.VISION_ANALYSIS]
        )
        
        text_models = registry.find_models_with_capability(Capability.TEXT_GENERATION)
        assert "model-1" in text_models
        assert "model-2" in text_models
        assert "model-3" not in text_models
        
        vision_models = registry.find_models_with_capability(Capability.VISION_ANALYSIS)
        assert "model-1" in vision_models
        assert "model-3" in vision_models
    
    def test_remove_model(self, registry):
        """Test removing a model from registry."""
        registry.register_model_capabilities(
            "model-1",
            [Capability.TEXT_GENERATION]
        )
        
        assert registry.has_capability("model-1", Capability.TEXT_GENERATION)
        
        registry.remove_model("model-1")
        
        assert not registry.has_capability("model-1", Capability.TEXT_GENERATION)
    
    def test_clear_registry(self, registry):
        """Test clearing the registry."""
        registry.register_model_capabilities(
            "model-1",
            [Capability.TEXT_GENERATION]
        )
        registry.register_model_capabilities(
            "model-2",
            [Capability.VISION_ANALYSIS]
        )
        
        registry.clear()
        
        all_caps = registry.list_all_capabilities()
        assert len(all_caps) == 0
