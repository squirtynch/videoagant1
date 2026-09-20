"""
AI Video Agent - OpenAI-Compatible Provider

Provider for OpenAI API and compatible endpoints (local LLMs, etc.).
"""

import json
from typing import List, Optional, Dict, Any
import httpx
import structlog

from ..interfaces import (
    AIProvider, 
    Message, 
    ModelInfo, 
    AIResponse
)
from ..capabilities import CapabilityRegistry, Capability

logger = structlog.get_logger(__name__)


class OpenAICompatibleProvider(AIProvider):
    """OpenAI-compatible API provider."""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        provider_id: str = "openai",
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None
    ):
        self._api_key = api_key
        self._base_url = base_url.rstrip('/')
        self._provider_id = provider_id
        self._timeout = timeout
        self._custom_headers = headers or {}
        self._models_cache: List[ModelInfo] = []
        self._is_healthy: bool = False
        
    @property
    def name(self) -> str:
        return f"OpenAI Compatible ({self._provider_id})"
    
    @property
    def provider_type(self) -> str:
        return "OPENAI_COMPATIBLE"
    
    async def health_check(self) -> bool:
        """Check if the provider is accessible."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                # Try to list models as a health check
                response = await client.get(
                    f"{self._base_url}/models",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        **self._custom_headers
                    }
                )
                
                if response.status_code == 200:
                    self._is_healthy = True
                    logger.info(f"Provider {self._provider_id} is healthy")
                    return True
                else:
                    logger.warning(f"Provider {self._provider_id} health check failed: {response.status_code}")
                    self._is_healthy = False
                    return False
                    
        except httpx.ConnectError as e:
            logger.error(f"Provider {self._provider_id} connection error: {e}")
            self._is_healthy = False
            return False
        except Exception as e:
            logger.error(f"Provider {self._provider_id} health check error: {e}")
            self._is_healthy = False
            return False
    
    async def list_models(self) -> List[ModelInfo]:
        """List available models from the provider."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(
                    f"{self._base_url}/models",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        **self._custom_headers
                    }
                )
                
                if response.status_code != 200:
                    logger.warning(f"Failed to list models: {response.status_code}")
                    return []
                
                data = response.json()
                models_data = data.get("data", [])
                
                self._models_cache = []
                for model_data in models_data:
                    model_id = model_data.get("id", "unknown")
                    
                    # Infer capabilities based on model ID patterns
                    capabilities = self._infer_capabilities(model_id)
                    
                    model_info = ModelInfo(
                        id=f"{self._provider_id}:{model_id}",
                        name=model_data.get("name", model_id),
                        provider_type=self.provider_type,
                        endpoint=self._base_url,
                        model_identifier=model_id,
                        capabilities=[c.value for c in capabilities],
                        context_limit=self._get_context_limit(model_id),
                        enabled=True,
                        health_status="OK" if self._is_healthy else "UNKNOWN"
                    )
                    self._models_cache.append(model_info)
                
                logger.info(f"Listed {len(self._models_cache)} models from {self._provider_id}")
                return self._models_cache
                
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    def _infer_capabilities(self, model_id: str) -> set[Capability]:
        """Infer model capabilities from model ID."""
        capabilities = {Capability.TEXT_GENERATION}
        
        model_lower = model_id.lower()
        
        # Check for vision capabilities
        if any(x in model_lower for x in ["vision", "gpt-4v", "gpt-4-vision"]):
            capabilities.add(Capability.VISION_ANALYSIS)
        
        # Check for structured output / tool calling
        if any(x in model_lower for x in ["gpt-4", "gpt-3.5-turbo-16k"]):
            capabilities.add(Capability.STRUCTURED_OUTPUT)
            capabilities.add(Capability.TOOL_CALLING)
        
        # Check for large context
        if any(x in model_lower for x in ["16k", "32k", "128k", "long"]):
            pass  # Context limit handled separately
        
        return capabilities
    
    def _get_context_limit(self, model_id: str) -> int:
        """Get context limit for a model."""
        model_lower = model_id.lower()
        
        if "128k" in model_lower:
            return 128000
        elif "32k" in model_lower:
            return 32000
        elif "16k" in model_lower:
            return 16000
        elif "gpt-4" in model_lower:
            return 8192
        elif "gpt-3.5" in model_lower:
            return 4096
        else:
            return 4096
    
    async def chat_completion(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AIResponse:
        """Send chat completion request."""
        # Extract actual model ID (remove provider prefix if present)
        actual_model = model.split(":", 1)[-1] if ":" in model else model
        
        payload = {
            "model": actual_model,
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ],
            "temperature": temperature,
        }
        
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        
        # Add any additional kwargs
        payload.update(kwargs)
        
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                        **self._custom_headers
                    },
                    json=payload
                )
                
                if response.status_code != 200:
                    error_msg = f"API error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
                
                data = response.json()
                
                # Extract response content
                choices = data.get("choices", [])
                if not choices:
                    raise RuntimeError("No choices in response")
                
                content = choices[0].get("message", {}).get("content", "")
                usage = data.get("usage")
                
                ai_response = AIResponse(
                    content=content,
                    model=actual_model,
                    usage=usage,
                    raw_response=data
                )
                
                logger.debug(f"Got response from {actual_model}: {len(content)} chars")
                return ai_response
                
        except httpx.ConnectError as e:
            logger.error(f"Connection error: {e}")
            raise RuntimeError(f"Failed to connect to AI provider: {e}")
        except Exception as e:
            logger.error(f"Chat completion error: {e}")
            raise
    
    async def structured_output(
        self,
        messages: List[Message],
        model: str,
        response_schema: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Request structured JSON output from model."""
        # Add system message to enforce JSON output
        system_message = Message(
            role="system",
            content=(
                "You must respond ONLY with valid JSON that matches the following schema. "
                "Do not include any explanatory text, markdown formatting, or code blocks. "
                f"Schema: {json.dumps(response_schema)}"
            )
        )
        
        all_messages = [system_message] + messages
        
        # Try to use JSON mode if supported
        response = await self.chat_completion(
            messages=all_messages,
            model=model,
            temperature=0.0,  # Use low temperature for structured output
            response_format={"type": "json_object"},
            **kwargs
        )
        
        # Parse and validate JSON
        try:
            # Try to extract JSON from response
            content = response.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1])  # Remove first and last lines
            
            parsed = json.loads(content)
            
            # Basic validation - ensure it's a dict
            if not isinstance(parsed, dict):
                raise ValueError("Response is not a JSON object")
            
            logger.debug(f"Structured output validated: {list(parsed.keys())}")
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise RuntimeError(f"Model returned invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Structured output error: {e}")
            raise
