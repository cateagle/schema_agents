"""
OpenRouter API implementation for the agent system.
"""

import json
import time
from typing import Any, Dict, List, Iterator, Optional
import requests
import jsonschema
import logging

from agent_system.core.llm_api import LLMApi, Message, LLMResponse, LLMApiError
from agent_system.core.registry import register_llm_api

logger = logging.getLogger(__name__)


@register_llm_api(description="OpenRouter API for accessing multiple LLM models")
class OpenRouterLLMApi(LLMApi):
    """
    OpenRouter API implementation for accessing multiple LLM models.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.model = config.get("model", "anthropic/claude-3.5-sonnet")
        self.base_url = config.get("base_url", "https://openrouter.ai/api/v1")
        self.max_tokens = config.get("max_tokens", 4000)
        self.temperature = config.get("temperature", 0.7)
        self.site_url = config.get("site_url", "https://github.com/user/schema-agents")
        self.app_name = config.get("app_name", "Schema Research Agents")
        
        if not self.api_key:
            raise LLMApiError("API key is required for OpenRouter API")
    
    def _make_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to OpenRouter API."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": self.site_url,
            "X-Title": self.app_name
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120  # OpenRouter can be slower for some models
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"OpenRouter API request failed: {str(e)}")
            # Try to get more details from the response
            try:
                error_details = response.json() if response else {}
                raise LLMApiError(f"API request failed: {str(e)}. Details: {error_details}")
            except:
                raise LLMApiError(f"API request failed: {str(e)}")
    
    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """Convert internal message format to OpenRouter format."""
        converted = []
        for msg in messages:
            # OpenRouter follows OpenAI format with 'system', 'user', 'assistant' roles
            role = msg.role
            if role not in ["system", "user", "assistant"]:
                # Map unknown roles to 'user'
                role = "user"
            converted.append({"role": role, "content": msg.content})
        return converted
    
    def chat_completion(self, messages: List[Message]) -> LLMResponse:
        """Generate a chat completion using OpenRouter API."""
        # Convert messages to OpenRouter format
        openrouter_messages = self._convert_messages(messages)
        
        payload = {
            "model": self.model,
            "messages": openrouter_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": False
        }
        
        response_data = self._make_request(payload)
        
        # Parse OpenRouter response (follows OpenAI format)
        if "error" in response_data:
            raise LLMApiError(f"OpenRouter API error: {response_data['error']}")
        
        if "choices" not in response_data or not response_data["choices"]:
            raise LLMApiError("No response choices returned from OpenRouter API")
        
        choice = response_data["choices"][0]
        message = choice.get("message", {})
        content = message.get("content", "")
        
        # Extract usage information
        usage = response_data.get("usage", {})
        token_usage = {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0)
        }
        
        # Get finish reason
        finish_reason = choice.get("finish_reason", "stop")
        
        return LLMResponse(
            role="assistant",
            content=content,
            token_usage=token_usage,
            finish_reason=finish_reason
        )
    
    def chat_completion_stream(self, messages: List[Message]) -> Iterator[LLMResponse]:
        """Generate streaming chat completion using OpenRouter API."""
        # Convert messages to OpenRouter format
        openrouter_messages = self._convert_messages(messages)
        
        payload = {
            "model": self.model,
            "messages": openrouter_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": True
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": self.site_url,
            "X-Title": self.app_name
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120,
                stream=True
            )
            response.raise_for_status()
            
            # Process streaming response
            content_buffer = ""
            total_tokens = 0
            
            for line in response.iter_lines():
                if not line:
                    continue
                
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data_str = line[6:]  # Remove 'data: ' prefix
                    
                    if data_str.strip() == '[DONE]':
                        break
                    
                    try:
                        data = json.loads(data_str)
                        
                        if "choices" in data and data["choices"]:
                            delta = data["choices"][0].get("delta", {})
                            content_chunk = delta.get("content", "")
                            
                            if content_chunk:
                                content_buffer += content_chunk
                                
                                # Estimate token usage (rough approximation)
                                total_tokens = len(content_buffer) // 4
                                
                                yield LLMResponse(
                                    role="assistant",
                                    content=content_buffer,
                                    token_usage={
                                        "prompt_tokens": total_tokens // 2,
                                        "completion_tokens": total_tokens // 2,
                                        "total_tokens": total_tokens
                                    },
                                    finish_reason=data["choices"][0].get("finish_reason", "")
                                )
                    
                    except json.JSONDecodeError:
                        continue  # Skip malformed JSON lines
            
        except requests.RequestException as e:
            logger.error(f"OpenRouter streaming request failed: {str(e)}")
            raise LLMApiError(f"Streaming request failed: {str(e)}")
    
    def structured_completion(self, messages: List[Message], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured JSON response conforming to schema."""
        # Add schema instruction to the conversation
        schema_instruction = f"""
Please respond with a valid JSON object that conforms exactly to this schema:
{json.dumps(schema, indent=2)}

Requirements:
- Respond ONLY with valid JSON
- Do not include any explanatory text before or after the JSON
- Ensure all required fields are present
- Follow the data types and constraints specified in the schema
"""
        
        # Add instruction message
        schema_message = Message(role="user", content=schema_instruction)
        enhanced_messages = messages + [schema_message]
        
        response = self.chat_completion(enhanced_messages)
        
        # Try to parse and validate JSON from response
        try:
            # Clean the response content
            content = response.content.strip()
            
            # Remove potential markdown code blocks
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            content = content.strip()
            
            # Parse JSON
            result = json.loads(content)
            
            # Validate against schema
            jsonschema.validate(result, schema)
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from response: {content[:200]}...")
            raise LLMApiError(f"Failed to parse JSON response: {str(e)}")
        except jsonschema.ValidationError as e:
            logger.error(f"JSON validation failed: {str(e)}")
            raise LLMApiError(f"Response does not conform to schema: {str(e)}")
    
    def get_available_models(self) -> List[str]:
        """Get list of available models from OpenRouter."""
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            models_data = response.json()
            return [model["id"] for model in models_data.get("data", [])]
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch available models: {str(e)}")
            return []
    
    def estimate_cost(self, messages: List[Message]) -> Dict[str, float]:
        """Estimate the cost of the API call (if pricing info is available)."""
        # This would require OpenRouter pricing API or hardcoded pricing
        # For now, return a placeholder
        total_chars = sum(len(msg.content) for msg in messages)
        estimated_tokens = total_chars // 4  # Rough estimate
        
        return {
            "estimated_prompt_tokens": estimated_tokens,
            "estimated_cost_usd": 0.0,  # Would need actual pricing data
            "model": self.model
        }