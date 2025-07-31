"""
Simplified session management without phases.
"""

from typing import Dict, Any
from streamlit_app.config.app_config import AppConfig


class SimpleSessionManager:
    """Simplified session manager for non-phase based application."""
    
    def __init__(self, st_session_state):
        self.st_session = st_session_state
    
    def initialize_session(self) -> None:
        """Initialize session with default values."""
        if "app_config" not in self.st_session:
            self.st_session.app_config = AppConfig()
    
    def get_app_config(self) -> AppConfig:
        """Get current app configuration."""
        return self.st_session.app_config
    
    def update_app_config(self, **updates) -> None:
        """Update app configuration."""
        config = self.st_session.app_config
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary for components."""
        config = self.get_app_config()
        return {
            'num_agents': config.num_agents,
            'max_results_per_agent': config.max_results_per_agent,
            'agent_timeout': config.agent_timeout,
            'agent_model': config.agent_model,
            'conversation_model': config.conversation_model,
            'research_depth': getattr(config, 'research_depth', 'medium'),
            'temperature': getattr(config, 'temperature', 0.3),
            'enable_validation': getattr(config, 'enable_validation', True),
            'enable_aggregation': getattr(config, 'enable_aggregation', True)
        }