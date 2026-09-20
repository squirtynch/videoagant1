"""
AI Video Agent - Mock Provider for Testing

A mock AI provider for testing without external dependencies.
"""

import json
from typing import List, Optional, Dict, Any
import asyncio
import structlog

from ..interfaces import (
    AIProvider, 
    Message, 
    ModelInfo, 
    AIResponse
)
from ..capabilities import Capability

logger = structlog.get_logger(__name__)


class MockProvider(AIProvider):
    """Mock AI provider for testing."""
    
    def __init__(
        self,
        provider_id: str = "mock",
        simulate_failure: bool = False,
        delay: float = 0.1
    ):
        self._provider_id = provider_id
        self._simulate_failure = simulate_failure
        self._delay = delay
        self._request_count = 0
        
    @property
    def name(self) -> str:
        return f"Mock Provider ({self._provider_id})"
    
    @property
    def provider_type(self) -> str:
        return "MOCK"
    
    async def health_check(self) -> bool:
        """Mock health check - always passes unless configured to fail."""
        await asyncio.sleep(self._delay)
        
        if self._simulate_failure:
            logger.warning(f"Mock provider {self._provider_id} simulating failure")
            return False
        
        logger.info(f"Mock provider {self._provider_id} is healthy")
        return True
    
    async def list_models(self) -> List[ModelInfo]:
        """Return mock models."""
        await asyncio.sleep(self._delay)
        
        models = [
            ModelInfo(
                id=f"{self._provider_id}:mock-text-model",
                name="Mock Text Model",
                provider_type=self.provider_type,
                endpoint="mock://localhost",
                model_identifier="mock-text-v1",
                capabilities=[
                    Capability.TEXT_GENERATION.value,
                    Capability.STRUCTURED_OUTPUT.value,
                    Capability.TOOL_CALLING.value,
                ],
                context_limit=8192,
                enabled=True,
                health_status="OK"
            ),
            ModelInfo(
                id=f"{self._provider_id}:mock-vision-model",
                name="Mock Vision Model",
                provider_type=self.provider_type,
                endpoint="mock://localhost",
                model_identifier="mock-vision-v1",
                capabilities=[
                    Capability.TEXT_GENERATION.value,
                    Capability.VISION_ANALYSIS.value,
                ],
                context_limit=4096,
                enabled=True,
                health_status="OK"
            ),
            ModelInfo(
                id=f"{self._provider_id}:mock-transcribe-model",
                name="Mock Transcription Model",
                provider_type=self.provider_type,
                endpoint="mock://localhost",
                model_identifier="mock-transcribe-v1",
                capabilities=[
                    Capability.TEXT_GENERATION.value,
                    Capability.AUDIO_TRANSCRIPTION.value,
                ],
                context_limit=16000,
                enabled=True,
                health_status="OK"
            ),
        ]
        
        logger.info(f"Mock provider listed {len(models)} models")
        return models
    
    async def chat_completion(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AIResponse:
        """Return mock chat completion."""
        self._request_count += 1
        await asyncio.sleep(self._delay)
        
        if self._simulate_failure:
            raise RuntimeError("Mock provider simulated failure")
        
        # Generate a simple mock response based on the last user message
        user_messages = [m for m in messages if m.role == "user"]
        last_message = user_messages[-1].content if user_messages else ""
        
        mock_content = (
            f"This is a mock response from {model}. "
            f"I received your message: '{last_message[:50]}...' "
            f"This is simulated output for testing purposes."
        )
        
        response = AIResponse(
            content=mock_content,
            model=model,
            usage={
                "prompt_tokens": len(messages) * 10,
                "completion_tokens": 20,
                "total_tokens": len(messages) * 10 + 20
            },
            raw_response={
                "id": f"mock-{self._request_count}",
                "object": "chat.completion",
                "choices": [
                    {
                        "message": {"role": "assistant", "content": mock_content},
                        "finish_reason": "stop"
                    }
                ]
            }
        )
        
        logger.debug(f"Mock provider returned response for {model}")
        return response
    
    async def structured_output(
        self,
        messages: List[Message],
        model: str,
        response_schema: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Return mock structured output matching the schema."""
        self._request_count += 1
        await asyncio.sleep(self._delay)
        
        if self._simulate_failure:
            raise RuntimeError("Mock provider simulated failure")
        
        # Generate mock data that matches the schema structure
        mock_data = self._generate_mock_schema(response_schema)
        
        logger.debug(f"Mock provider returned structured output: {list(mock_data.keys())}")
        return mock_data
    
    def _generate_mock_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock data based on a JSON schema."""
        if not schema:
            return {"result": "mock_data"}
        
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        result = {}
        for key, prop_schema in properties.items():
            prop_type = prop_schema.get("type", "string")
            
            if prop_type == "string":
                result[key] = f"mock_{key}_value"
            elif prop_type == "integer":
                result[key] = 42
            elif prop_type == "number":
                result[key] = 3.14
            elif prop_type == "boolean":
                result[key] = True
            elif prop_type == "array":
                result[key] = []
            elif prop_type == "object":
                result[key] = {}
            else:
                result[key] = "mock_value"
        
        # Ensure required fields are present
        for req_field in required:
            if req_field not in result:
                result[req_field] = "required_mock_value"
        
        return result
    
    def get_request_count(self) -> int:
        """Get the number of requests made to this provider."""
        return self._request_count
    
    def reset(self):
        """Reset the provider state."""
        self._request_count = 0
        logger.info(f"Reset mock provider {self._provider_id}")
