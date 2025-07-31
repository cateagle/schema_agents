"""
Example LLM API implementations for the agent system.
"""

import json
import time
from typing import Any, Dict, List, Iterator, Optional
import requests
import jsonschema
import logging

from agent_system.core.llm_api import LLMApi, Message, LLMResponse, LLMApiError

logger = logging.getLogger(__name__)

class AnthropicLLMApi(LLMApi):
    """
    Anthropic Claude API implementation.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.model = config.get("model", "claude-3-sonnet-20240229")
        self.base_url = config.get("base_url", "https://api.anthropic.com")
        self.max_tokens = config.get("max_tokens", 4000)
        self.temperature = config.get("temperature", 0.7)
        
        if not self.api_key:
            raise LLMApiError("API key is required for Anthropic API")
    
    def _make_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to Anthropic API."""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/messages",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Anthropic API request failed: {str(e)}")
            raise LLMApiError(f"API request failed: {str(e)}")
    
    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """Convert internal message format to Anthropic format."""
        converted = []
        for msg in messages:
            # Anthropic expects 'user' and 'assistant' roles
            role = msg.role if msg.role in ["user", "assistant"] else "user"
            converted.append({"role": role, "content": msg.content})
        return converted
    
    def chat_completion(self, messages: List[Message]) -> LLMResponse:
        # Separate system messages from conversation
        system_messages = [msg for msg in messages if msg.role == "system"]
        conversation_messages = [msg for msg in messages if msg.role != "system"]
        
        # Combine system messages into system parameter
        system_content = "\n\n".join([msg.content for msg in system_messages])
        
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": self._convert_messages(conversation_messages)
        }
        
        if system_content:
            payload["system"] = system_content
        
        response_data = self._make_request(payload)
        
        # Extract response content
        content = ""
        if "content" in response_data:
            for item in response_data["content"]:
                if item.get("type") == "text":
                    content += item.get("text", "")
        
        # Extract usage information
        usage = response_data.get("usage", {})
        token_usage = {
            "prompt_tokens": usage.get("input_tokens", 0),
            "completion_tokens": usage.get("output_tokens", 0),
            "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
        }
        
        return LLMResponse(
            role="assistant",
            content=content,
            token_usage=token_usage,
            finish_reason=response_data.get("stop_reason", "stop")
        )
    
    def chat_completion_stream(self, messages: List[Message]) -> Iterator[LLMResponse]:
        # For now, just return non-streaming response
        # In a full implementation, this would use streaming API
        response = self.chat_completion(messages)
        yield response
    
    def structured_completion(self, messages: List[Message], schema: Dict[str, Any]) -> Dict[str, Any]:
        # Add schema instruction to the conversation
        schema_instruction = f"""
Please respond with a JSON object that conforms to this schema:
{json.dumps(schema, indent=2)}

Respond ONLY with valid JSON that matches the schema exactly.
"""
        
        # Add instruction message
        schema_message = Message(role="user", content=schema_instruction)
        enhanced_messages = messages + [schema_message]
        
        response = self.chat_completion(enhanced_messages)
        
        # Try to parse JSON from response
        try:
            # Extract JSON from response (might be wrapped in markdown)
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            result = json.loads(content)
            
            # Validate against schema
            jsonschema.validate(result, schema)
            return result
            
        except (json.JSONDecodeError, jsonschema.ValidationError) as e:
            logger.error(f"Structured completion validation failed: {str(e)}")
            raise LLMApiError(f"Failed to generate valid structured response: {str(e)}")