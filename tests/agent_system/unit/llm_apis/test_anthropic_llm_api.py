"""
Unit tests for the Anthropic LLM API (mocked, no actual API calls).
"""

import pytest
from unittest.mock import Mock, patch

from agent_system.llm_apis import AnthropicLLMApi
from agent_system.core import Message, LLMResponse, LLMApiError


class TestAnthropicLLMApi:
    """Test Anthropic LLM API functionality with mocked requests."""
    
    def test_initialization_with_config(self):
        """Test API initialization with configuration."""
        config = {
            "api_key": "test-key",
            "model": "claude-3-sonnet-20240229",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        api = AnthropicLLMApi(config)
        
        assert api.config["api_key"] == "test-key"
        assert api.config["model"] == "claude-3-sonnet-20240229"
        assert api.config["temperature"] == 0.7
        assert api.config["max_tokens"] == 1000
    
    def test_initialization_missing_api_key(self):
        """Test that missing API key raises appropriate error."""
        with pytest.raises(LLMApiError) as exc_info:
            AnthropicLLMApi({})
        
        assert "api key" in str(exc_info.value).lower()
    
    def test_initialization_missing_model(self):
        """Test that missing model uses default."""
        api = AnthropicLLMApi({"api_key": "test-key"})
        
        assert api.model == "claude-3-sonnet-20240229"
    
    # Add tests similar to OpenRouter but for Anthropic API specifics
    # These tests should be updated based on the actual AnthropicLLMApi implementation