"""
Mock LLM API implementation for testing and demonstration.
"""

import json
import time
from typing import Any, Dict, List, Iterator, Optional
import requests
import jsonschema
import logging

from agent_system.core.llm_api import LLMApi, Message, LLMResponse, LLMApiError
from agent_system.core.base_models import LLMApiConfig
from agent_system.core.registry import register_llm_api

logger = logging.getLogger(__name__)


@register_llm_api(description="Mock LLM API for testing and demonstration")
class MockLLMApi(LLMApi):
    """
    Mock LLM API for testing and demonstration.
    Returns predefined responses and simulates real API behavior.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.response_delay = config.get("response_delay", 0.5)
        self.mock_responses = config.get("mock_responses", [])
        self.response_index = 0
    
    def chat_completion(self, messages: List[Message]) -> LLMResponse:
        # Simulate API delay
        time.sleep(self.response_delay)
        
        # Get mock response or generate default
        if self.response_index < len(self.mock_responses):
            content = self.mock_responses[self.response_index]
            self.response_index += 1
        else:
            # Generate a default response based on the last message
            last_message = messages[-1] if messages else None
            if last_message and "calculator" in last_message.content.lower():
                content = '{"tool": "calculator", "input": {"expression": "2 + 2"}}'
            elif last_message and "search" in last_message.content.lower():
                content = '{"tool": "web_search", "input": {"query": "example search", "max_results": 3}}'
            else:
                content = "I'll help you complete this task. Let me start by understanding what needs to be done."
        
        # Estimate token usage
        token_count = len(content) // 4  # Simple estimation
        
        return LLMResponse(
            role="assistant",
            content=content,
            token_usage={"total_tokens": token_count, "prompt_tokens": token_count // 2, "completion_tokens": token_count // 2},
            finish_reason="stop"
        )
    
    def chat_completion_stream(self, messages: List[Message]) -> Iterator[LLMResponse]:
        # For mock, just return single response
        response = self.chat_completion(messages)
        yield response
    
    def structured_completion(self, messages: List[Message], schema: Dict[str, Any]) -> Dict[str, Any]:
        # Mock structured response
        time.sleep(self.response_delay)
        
        # Generate a mock response that conforms to the schema
        if "properties" in schema:
            mock_data = {}
            for prop, prop_schema in schema["properties"].items():
                if prop_schema.get("type") == "string":
                    mock_data[prop] = f"mock_{prop}_value"
                elif prop_schema.get("type") == "number":
                    mock_data[prop] = 42.0
                elif prop_schema.get("type") == "integer":
                    mock_data[prop] = 42
                elif prop_schema.get("type") == "boolean":
                    mock_data[prop] = True
                elif prop_schema.get("type") == "array":
                    mock_data[prop] = ["mock_item"]
                else:
                    mock_data[prop] = "mock_value"
            
            # Validate against schema
            try:
                jsonschema.validate(mock_data, schema)
                return mock_data
            except jsonschema.ValidationError:
                # Fallback to minimal valid response
                return {"status": "completed"}
        
        return {"status": "completed"}