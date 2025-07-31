"""
Data models for the Streamlit research application.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class AgentResult:
    """Data model for individual agent search results."""
    agent_id: int
    summary: str
    results: List[Dict[str, Any]]
    error: Optional[str] = None
    execution_time: float = 0.0
    
    def __post_init__(self) -> None:
        """Validate agent result data."""
        if not isinstance(self.results, list):
            self.results = []


@dataclass
class SchemaSession:
    """Schema building session data."""
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    current_schema: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []
    
    def add_message(self, role: str, content: str) -> None:
        """Add message to conversation history."""
        self.conversation_history.append({"role": role, "content": content})
    
    def clear_conversation(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []


@dataclass
class ResearchSession:
    """Research session data."""
    query: str = ""
    schema: Optional[Dict[str, Any]] = None
    search_results: List[AgentResult] = field(default_factory=list)
    
    def __post_init__(self):
        if self.search_results is None:
            self.search_results = []
    
    def reset_search_results(self) -> None:
        """Clear previous search results."""
        self.search_results = []
    
    def get_total_results(self) -> int:
        """Get total number of valid results across all agents."""
        return sum(len(agent.results) for agent in self.search_results)
    
    def is_ready_for_research(self) -> bool:
        """Check if session is ready for research execution."""
        if not self.schema:
            return False
        
        # Basic validation - could add more sophisticated checks
        return (isinstance(self.schema, dict) and 
                "type" in self.schema and 
                "properties" in self.schema)


@dataclass
class ResearchConfig:
    """Configuration for research coordination."""
    max_agents: int = 5
    agent_timeout: int = 300
    max_results_per_agent: int = 10
    research_depth: str = "medium"  # shallow, medium, deep
    enable_validation: bool = True
    enable_aggregation: bool = True
    prioritize_sources: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.prioritize_sources is None:
            self.prioritize_sources = ["academic", "news", "technical"]