"""
Research service for managing research operations.
"""

from typing import Dict, Any, List, Optional, Callable
from streamlit_app.core.research_orchestrator import ResearchOrchestrator
from streamlit_app.config.models import ResearchConfig


class ResearchService:
    """Service for managing research operations."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.orchestrator = None
        self.current_research = None
    
    def create_orchestrator(self) -> ResearchOrchestrator:
        """Create and configure research orchestrator."""
        if not self.orchestrator:
            self.orchestrator = ResearchOrchestrator(self.api_key)
        return self.orchestrator
    
    def execute_research(
        self, 
        query: str, 
        schema: Dict[str, Any],
        config: Dict[str, Any],
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """Execute comprehensive research."""
        try:
            # Validate configuration first
            is_valid, errors = self.validate_research_config(config)
            if not is_valid:
                return {
                    "success": False,
                    "error": f"Configuration errors: {', '.join(errors)}",
                    "results": []
                }
            
            # Create orchestrator if needed
            if not self.orchestrator:
                self.create_orchestrator()
            
            # Execute research
            result = self.orchestrator.execute_research(
                query=query,
                schema=schema,
                config=config,
                progress_callback=progress_callback
            )
            
            # Store current research for reference
            self.current_research = {
                "query": query,
                "schema": schema,
                "config": config,
                "result": result
            }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Research execution failed: {str(e)}",
                "results": []
            }
    
    def get_research_status(self) -> Dict[str, Any]:
        """Get current research status."""
        if not self.orchestrator:
            return {"status": "not_initialized"}
        
        return self.orchestrator.get_research_status()
    
    def get_research_summary(self) -> Dict[str, Any]:
        """Get comprehensive research summary."""
        if not self.orchestrator:
            return {}
        
        return self.orchestrator.get_research_summary()
    
    def validate_research_config(self, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate research configuration."""
        errors = []
        
        # Check API key
        if not self.api_key:
            errors.append("OpenRouter API key is required")
        
        # Validate agent configuration
        num_agents = config.get("num_agents", 0)
        if num_agents < 1:
            errors.append("Number of agents must be at least 1")
        elif num_agents > 10:
            errors.append("Number of agents cannot exceed 10")
        
        # Validate timeout
        timeout = config.get("agent_timeout", 0)
        if timeout < 10:
            errors.append("Agent timeout must be at least 10 seconds")
        elif timeout > 600:
            errors.append("Agent timeout cannot exceed 600 seconds")
        
        # Validate results per agent
        max_results = config.get("max_results_per_agent", 0)
        if max_results < 1:
            errors.append("Max results per agent must be at least 1")
        elif max_results > 50:
            errors.append("Max results per agent cannot exceed 50")
        
        # Validate model
        model = config.get("agent_model", "")
        if not model:
            errors.append("Agent model must be specified")
        
        return len(errors) == 0, errors
    
    def cancel_research(self) -> bool:
        """Cancel ongoing research (placeholder for future implementation)."""
        # This would need to be implemented in the orchestrator
        # For now, just reset the orchestrator
        self.orchestrator = None
        return True
    
    def get_supported_research_depths(self) -> List[str]:
        """Get supported research depth levels."""
        return ["shallow", "medium", "deep"]
    
    def get_supported_search_regions(self) -> List[str]:
        """Get supported search regions."""
        return ["general", "academic", "news", "technical", "international"]
    
    def estimate_research_time(self, config: Dict[str, Any]) -> int:
        """Estimate research time in seconds based on configuration."""
        base_time = 30  # Base time per agent
        
        num_agents = config.get("num_agents", 3)
        max_results = config.get("max_results_per_agent", 10)
        depth = config.get("research_depth", "medium")
        
        # Depth multipliers
        depth_multipliers = {
            "shallow": 0.7,
            "medium": 1.0,
            "deep": 1.5
        }
        
        depth_multiplier = depth_multipliers.get(depth, 1.0)
        result_multiplier = max_results / 10  # Scale with results
        
        estimated_time = int(base_time * num_agents * depth_multiplier * result_multiplier)
        
        # Add some buffer time
        return min(estimated_time + 30, 600)  # Cap at 10 minutes