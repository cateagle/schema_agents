"""
Unit tests for the mock LLM API.
"""

import pytest
import time
from unittest.mock import Mock

from agent_system.llm_apis import MockLLMApi
from agent_system.core import Message, LLMResponse


class TestMockLLMApi:
    """Test mock LLM API functionality."""
    
    def test_default_initialization(self):
        """Test default initialization."""
        api = MockLLMApi({})
        
        assert api.response_delay == 0.5
        assert api.mock_responses == []
    
    def test_custom_configuration(self):
        """Test custom configuration."""
        config = {
            "response_delay": 0.5,
            "mock_responses": ["Response 1", "Response 2"],
            "model": "mock-model"
        }
        
        api = MockLLMApi(config)
        
        assert api.config["response_delay"] == 0.5
        assert api.config["mock_responses"] == ["Response 1", "Response 2"]
        assert api.config["model"] == "mock-model"
    
    def test_single_message_response(self):
        """Test single message response."""
        api = MockLLMApi({
            "response_delay": 0.01,
            "mock_responses": ["Test response"]
        })
        
        message = Message(role="user", content="Test message")
        
        start_time = time.time()
        response = api.chat_completion([message])
        end_time = time.time()
        
        assert isinstance(response, LLMResponse)
        assert response.content == "Test response"
        assert response.role == "assistant"
        assert (end_time - start_time) >= 0.01  # Check delay was applied
    
    def test_multiple_messages_conversation(self):
        """Test multiple message conversation."""
        api = MockLLMApi({
            "response_delay": 0.01,
            "mock_responses": ["Response 1", "Response 2", "Response 3"]
        })
        
        messages = [
            Message(role="system", content="System message"),
            Message(role="user", content="User message 1"),
            Message(role="assistant", content="Assistant message 1"),
            Message(role="user", content="User message 2")
        ]
        
        response = api.chat_completion(messages)
        
        assert response.content == "Response 1"  # First unused response
        assert response.role == "assistant"
    
    def test_response_cycling(self):
        """Test that responses are used sequentially then default to generic response."""
        responses = ["Response A", "Response B", "Response C"]
        api = MockLLMApi({
            "response_delay": 0.01,
            "mock_responses": responses
        })
        
        message = Message(role="user", content="Test")
        
        # Test using predefined responses first
        for i in range(3):  # Use all predefined responses
            response = api.chat_completion([message])
            assert response.content == responses[i]
        
        # After exhausting predefined responses, should get default response
        response = api.chat_completion([message])
        assert "I'll help you complete this task" in response.content
    
    def test_response_delay(self):
        """Test response delay functionality."""
        delay = 0.1
        api = MockLLMApi({
            "response_delay": delay,
            "mock_responses": ["Test response"]
        })
        
        message = Message(role="user", content="Test")
        
        start_time = time.time()
        api.chat_completion([message])
        end_time = time.time()
        
        # Allow for some timing variation
        assert (end_time - start_time) >= (delay * 0.8)
    
    def test_empty_messages_list(self):
        """Test handling of empty messages list."""
        api = MockLLMApi({
            "mock_responses": ["Default response"]
        })
        
        response = api.chat_completion([])
        
        assert response.content == "Default response"
        assert response.role == "assistant"
    
    def test_state_preservation(self):
        """Test that mock API preserves state across calls."""
        api = MockLLMApi({
            "response_delay": 0.01,
            "mock_responses": ["First", "Second", "Third"]
        })
        
        message = Message(role="user", content="Test")
        
        # First call
        response1 = api.chat_completion([message])
        assert response1.content == "First"
        
        # Second call should get next response
        response2 = api.chat_completion([message])
        assert response2.content == "Second"
        
        # Third call
        response3 = api.chat_completion([message])
        assert response3.content == "Third"
        
        # Fourth call should use default response
        response4 = api.chat_completion([message])
        assert "I'll help you complete this task" in response4.content