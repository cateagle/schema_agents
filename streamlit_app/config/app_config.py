"""
Application configuration for the Streamlit research tool.
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ModelProvider(Enum):
    """Available model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MISTRAL = "mistralai"
    META = "meta-llama"


@dataclass
class AppConfig:
    """Main application configuration."""
    
    # API Configuration
    openrouter_api_key: str = field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))
    
    # Model Configuration
    conversation_model: str = field(default_factory=lambda: os.getenv("DEFAULT_CONVERSATION_MODEL", "anthropic/claude-3.5-sonnet"))
    agent_model: str = field(default_factory=lambda: os.getenv("DEFAULT_AGENT_MODEL", "anthropic/claude-3.5-sonnet"))
    
    # Agent Configuration
    num_agents: int = field(default_factory=lambda: int(os.getenv("DEFAULT_NUM_AGENTS", "3")))
    max_results_per_agent: int = field(default_factory=lambda: int(os.getenv("DEFAULT_MAX_RESULTS_PER_AGENT", "10")))
    agent_timeout: int = field(default_factory=lambda: int(os.getenv("DEFAULT_AGENT_TIMEOUT", "300")))
    
    # Search Configuration
    max_total_results: int = 50
    search_timeout: int = 600
    enable_website_scraping: bool = True
    
    # UI Configuration
    show_agent_details: bool = True
    auto_copy_results: bool = False
    
    def __post_init__(self) -> None:
        """Validate configuration values."""
        if self.num_agents < 1:
            self.num_agents = 1
        if self.num_agents > 10:
            self.num_agents = 10
            
        if self.max_results_per_agent < 1:
            self.max_results_per_agent = 1
        if self.max_results_per_agent > 50:
            self.max_results_per_agent = 50
            
        if self.agent_timeout < 10:
            self.agent_timeout = 10
        if self.agent_timeout > 600:
            self.agent_timeout = 600
    
    @property
    def is_valid(self) -> bool:
        """Check if configuration is valid for running searches."""
        return bool(self.openrouter_api_key.strip())
    
    def get_model_display_name(self, model: str) -> str:
        """Get user-friendly model name."""
        model_names = {
            "openai/gpt-3.5-turbo": "GPT-3.5 Turbo",
            "openai/gpt-4": "GPT-4",
            "openai/gpt-4-turbo": "GPT-4 Turbo",
            "anthropic/claude-3-haiku": "Claude 3 Haiku",
            "anthropic/claude-3.5-sonnet": "Claude 3.5 Sonnet",
            "anthropic/claude-3-sonnet": "Claude 3 Sonnet",
            "anthropic/claude-3-opus": "Claude 3 Opus",
            "mistralai/mixtral-8x7b-instruct": "Mixtral 8x7B",
            "mistralai/mistral-7b-instruct": "Mistral 7B",
            "meta-llama/llama-2-70b-chat": "Llama 2 70B",
        }
        return model_names.get(model, model)


# Available models for different tasks
CONVERSATION_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3-sonnet",
    "anthropic/claude-3-haiku",
    "anthropic/claude-3-opus",
    "openai/gpt-3.5-turbo",
    "openai/gpt-4",
    "openai/gpt-4-turbo",
]

AGENT_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3-sonnet", 
    "anthropic/claude-3-haiku",
    "mistralai/mixtral-8x7b-instruct",
    "mistralai/mistral-7b-instruct",
    "openai/gpt-3.5-turbo",
    "meta-llama/llama-2-70b-chat",
]

# Default JSON schema template
DEFAULT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "url": {"type": "string", "format": "uri"},
        "snippet": {"type": "string"},
        "relevance_score": {"type": "number", "minimum": 0, "maximum": 10}
    },
    "required": ["title", "url", "snippet"]
}

# Error messages
ERROR_MESSAGES = {
    "no_api_key": "Please provide an OpenRouter API key to use the research tool.",
    "invalid_schema": "The JSON schema is invalid. Please check the format.",
    "search_timeout": "Search operation timed out. Try reducing the number of agents or timeout duration.",
    "no_results": "No valid results found. Try refining your search prompt or schema.",
    "agent_error": "One or more agents encountered errors during the search.",
}

# CSS Styles
APP_CSS = """
<style>
    /* Hide Streamlit's default header and menu */
    .stApp [data-testid="stHeader"] {
        display: none;
    }
    
    /* Remove ALL top padding from main container */
    .block-container {
        padding-top: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }
    
    /* Remove default Streamlit margins */
    .main .block-container {
        padding-top: 0rem !important;
    }
    
    /* Fixed header at very top */
    .fixed-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 999999;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.75rem 1rem;
        font-size: 1.1rem;
        font-weight: 600;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: none;
        margin: 0;
    }
    
    /* Add top margin to content to account for fixed header */
    .main-content {
        margin-top: 50px !important;
        padding-top: 0 !important;
    }
    
    /* Chat message styling */
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
    }
    .user-message {
        background-color: #f0f2f6;
        border-left-color: #4CAF50;
    }
    .assistant-message {
        background-color: #fff;
        border-left-color: #667eea;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        transition: all 0.3s;
        width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
"""