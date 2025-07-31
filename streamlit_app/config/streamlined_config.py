"""
Streamlined configuration for the simplified research tool.
Removes redundant components and consolidates settings.
"""

import os
from dataclasses import dataclass
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class StreamlinedConfig:
    """Simplified configuration with only essential settings."""
    
    # API Settings
    openrouter_api_key: str = ""
    
    # Model Settings
    conversation_model: str = "anthropic/claude-3.5-sonnet"
    agent_model: str = "anthropic/claude-3.5-sonnet"
    
    # Research Settings
    num_agents: int = 3
    max_results_per_agent: int = 10
    agent_timeout: int = 300
    
    def __post_init__(self) -> None:
        """Load from environment if not set."""
        if not self.openrouter_api_key:
            self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
        
        # Validate and constrain values
        self.num_agents = max(1, min(10, self.num_agents))
        self.max_results_per_agent = max(1, min(50, self.max_results_per_agent))
        self.agent_timeout = max(10, min(600, self.agent_timeout))
    
    @property
    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return bool(self.openrouter_api_key.strip())


# Available models
CONVERSATION_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3-sonnet",
    "anthropic/claude-3-haiku",
    "openai/gpt-4",
    "openai/gpt-3.5-turbo",
]

AGENT_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3-sonnet",
    "anthropic/claude-3-haiku",
    "mistralai/mixtral-8x7b-instruct",
    "openai/gpt-3.5-turbo",
]

# Default schema template
DEFAULT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "url": {"type": "string", "format": "uri"},
        "content": {"type": "string"},
        "relevance": {"type": "number", "minimum": 0, "maximum": 10}
    },
    "required": ["title", "url"]
}