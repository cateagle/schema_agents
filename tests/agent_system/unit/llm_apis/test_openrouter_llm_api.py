"""
Unit tests for the OpenRouter LLM API (mocked, no actual API calls).
"""

import pytest
from unittest.mock import Mock, patch
import json

from agent_system.llm_apis import OpenRouterLLMApi
from agent_system.core import Message, LLMResponse, LLMApiError


class TestOpenRouterLLMApi:
    """Test OpenRouter LLM API functionality with mocked requests."""
    
    def test_initialization_with_config(self):
        """Test API initialization with configuration."""
        config = {
            "api_key": "test-key",
            "model": "anthropic/claude-3-sonnet",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        api = OpenRouterLLMApi(config)
        
        assert api.config["api_key"] == "test-key"
        assert api.config["model"] == "anthropic/claude-3-sonnet"
        assert api.config["temperature"] == 0.7
        assert api.config["max_tokens"] == 1000
    
    def test_initialization_missing_api_key(self):
        """Test that missing API key raises appropriate error."""
        with pytest.raises(LLMApiError) as exc_info:
            OpenRouterLLMApi({})
        
        assert "api key" in str(exc_info.value).lower()
    
    def test_initialization_missing_model(self):
        """Test that missing model uses default."""
        api = OpenRouterLLMApi({"api_key": "test-key"})
        
        assert api.model == "anthropic/claude-3.5-sonnet"
    
    @patch('agent_system.llm_apis.openrouter_llm_api.requests.post')
    def test_successful_chat_completion(self, mock_post):
        """Test successful chat completion."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "This is a test response from OpenRouter."
                }
            }]
        }
        mock_post.return_value = mock_response
        
        api = OpenRouterLLMApi({
            "api_key": "test-key",
            "model": "anthropic/claude-3-sonnet"
        })
        
        messages = [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="Hello!")
        ]
        
        response = api.chat_completion(messages)
        
        assert isinstance(response, LLMResponse)
        assert response.content == "This is a test response from OpenRouter."
        assert response.role == "assistant"
        
        # Verify request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Check URL - it should be the first positional argument
        url = call_args[0][0] if call_args[0] else call_args.kwargs.get("url")
        assert "openrouter.ai" in url
        
        # Check headers
        headers = call_args[1].get("headers") or call_args.kwargs.get("headers", {})
        assert "Authorization" in headers
        assert "Bearer test-key" in headers["Authorization"]
        assert headers["Content-Type"] == "application/json"
        
        # Check payload - it could be in 'data' or 'json' kwargs
        if "data" in call_args[1]:
            payload = json.loads(call_args[1]["data"])
        elif "json" in call_args[1]:
            payload = call_args[1]["json"]
        else:
            # Try kwargs
            payload = call_args.kwargs.get("json") or json.loads(call_args.kwargs.get("data", "{}"))
        
        assert payload["model"] == "anthropic/claude-3-sonnet"
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][1]["role"] == "user"
    
    @patch('agent_system.llm_apis.openrouter_llm_api.requests.post')
    def test_api_error_handling(self, mock_post):
        """Test API error handling."""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {
                "message": "Invalid request",
                "code": "invalid_request"
            }
        }
        mock_post.return_value = mock_response
        
        api = OpenRouterLLMApi({
            "api_key": "test-key",
            "model": "anthropic/claude-3-sonnet"
        })
        
        messages = [Message(role="user", content="Test")]
        
        with pytest.raises(Exception) as exc_info:
            api.chat_completion(messages)
        
        assert "OpenRouter API error" in str(exc_info.value) or "400" in str(exc_info.value)
    
    @patch('agent_system.llm_apis.openrouter_llm_api.requests.post')
    def test_network_error_handling(self, mock_post):
        """Test network error handling."""
        # Mock network error
        mock_post.side_effect = Exception("Network connection failed")
        
        api = OpenRouterLLMApi({
            "api_key": "test-key",
            "model": "anthropic/claude-3-sonnet"
        })
        
        messages = [Message(role="user", content="Test")]
        
        with pytest.raises(Exception) as exc_info:
            api.chat_completion(messages)
        
        assert "Network connection failed" in str(exc_info.value)
    
    def test_message_formatting(self):
        """Test message formatting for API."""
        api = OpenRouterLLMApi({
            "api_key": "test-key",
            "model": "anthropic/claude-3-sonnet"
        })
        
        messages = [
            Message(role="system", content="System prompt"),
            Message(role="user", content="User message"),
            Message(role="assistant", content="Assistant response")
        ]
        
        formatted = api._convert_messages(messages)
        
        assert len(formatted) == 3
        assert formatted[0]["role"] == "system"
        assert formatted[0]["content"] == "System prompt"
        assert formatted[1]["role"] == "user"
        assert formatted[1]["content"] == "User message"
        assert formatted[2]["role"] == "assistant"
        assert formatted[2]["content"] == "Assistant response"
    
    def test_custom_parameters(self):
        """Test custom API parameters."""
        config = {
            "api_key": "test-key",
            "model": "anthropic/claude-3-sonnet",
            "temperature": 0.9,
            "max_tokens": 2000,
            "top_p": 0.95
        }
        
        api = OpenRouterLLMApi(config)
        
        assert api.config["temperature"] == 0.9
        assert api.config["max_tokens"] == 2000
        assert api.config["top_p"] == 0.95