"""
Base LLM API class for the agent system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Iterator, Optional
from pydantic import BaseModel
import logging

from agent_system.core.registry import register_exception

logger = logging.getLogger(__name__)


class Message(BaseModel):
    """Represents a message in the conversation."""
    role: str  # "user", "assistant", "system"
    content: str


class LLMResponse(BaseModel):
    """Response from the LLM API."""
    role: str
    content: str
    token_usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None


class LLMApi(ABC):
    """
    Base class for all LLM API providers.
    
    Handles communication with different LLM services and provides
    a unified interface for agents to interact with language models.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    @abstractmethod
    def chat_completion(self, messages: List[Message]) -> LLMResponse:
        """
        Perform a chat completion with the LLM.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            LLMResponse with the model's reply
            
        Raises:
            LLMApiError: If the API call fails
        """
        pass
    
    @abstractmethod
    def chat_completion_stream(self, messages: List[Message]) -> Iterator[LLMResponse]:
        """
        Perform a streaming chat completion with the LLM.
        
        Args:
            messages: List of conversation messages
            
        Yields:
            LLMResponse chunks as they arrive
            
        Raises:
            LLMApiError: If the API call fails
        """
        pass
    
    @abstractmethod
    def structured_completion(
        self, 
        messages: List[Message], 
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform a structured completion that returns JSON conforming to schema.
        
        Args:
            messages: List of conversation messages
            schema: JSON schema for the expected output
            
        Returns:
            Structured data conforming to the schema
            
        Raises:
            LLMApiError: If the API call fails
            ValidationError: If response doesn't match schema
        """
        pass
    
    def get_token_count(self, text: str) -> int:
        """
        Estimate token count for the given text.
        Default implementation uses a simple heuristic.
        Override for provider-specific tokenization.
        """
        # Simple heuristic: ~4 characters per token
        return len(text) // 4
    
    def get_conversation_token_count(self, messages: List[Message]) -> int:
        """
        Calculate total token count for a conversation.
        """
        total = 0
        for message in messages:
            total += self.get_token_count(message.content)
            # Add some overhead for message formatting
            total += 10
        return total


@register_exception
class LLMApiError(Exception):
    """Exception raised when LLM API calls fail."""
    pass