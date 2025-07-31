"""
Research Coordinator Agent for managing comprehensive research workflows.

This agent coordinates multiple research agents and tools to conduct comprehensive
research with JSON analysis, validation, and aggregation capabilities.
"""

import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from agent_system.core import Agent, Message
from agent_system.core.registry import register_agent
# ResearchAgent imported dynamically to avoid circular imports
from agent_system.tools import (
    JSONAnalysisTool, JSONAnalysisConfig,
    ResearchTriggerTool, ResearchTriggerConfig,
    ResultValidationTool, ResultValidationConfig,
    ResultAggregationTool, ResultAggregationConfig
)

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


@register_agent(description="Coordinates comprehensive research using multiple agents and tools")
class ResearchCoordinator(Agent):
    """
    Research Coordinator Agent that manages comprehensive research workflows.
    
    This agent can:
    - Analyze research requirements and break them into focused tasks
    - Coordinate multiple specialized research agents
    - Analyze and validate JSON results against schemas
    - Aggregate and deduplicate findings from multiple sources
    - Ensure research completeness and quality
    """
    
    def __init__(self, llm_api, research_config: Optional[ResearchConfig] = None, **kwargs):
        self.research_config = research_config or ResearchConfig()
        
        # Create specialized tools for research coordination
        tools = self._create_coordination_tools()
        
        # Set up the research trigger tool with the LLM API
        for tool in tools:
            if isinstance(tool, ResearchTriggerTool):
                tool.set_llm_api(llm_api)
        
        super().__init__(
            system_prompt=self._get_coordinator_prompt(),
            task_description=kwargs.get('task_description', "Research coordination task"),
            llm_api=llm_api,
            tools=tools,
            **{k: v for k, v in kwargs.items() if k != 'task_description'}
        )
        
        # Track research progress
        self.research_agents = []
        self.research_results = []
        self.analysis_results = {}
    
    def _create_coordination_tools(self) -> List:
        """Create specialized tools for research coordination."""
        tools = [
            # JSON Analysis Tool
            JSONAnalysisTool(
                config=JSONAnalysisConfig(
                    include_patterns=True,
                    include_quality_checks=True
                ),
                alias="json_analysis"
            ),
            
            # Research Trigger Tool
            ResearchTriggerTool(
                config=ResearchTriggerConfig(
                    max_concurrent_agents=self.research_config.max_agents,
                    agent_timeout=self.research_config.agent_timeout,
                    default_max_results=self.research_config.max_results_per_agent
                ),
                alias="research_trigger"
            ),
            
            # Result Validation Tool
            ResultValidationTool(
                config=ResultValidationConfig(
                    auto_fix_minor_issues=True,
                    max_validation_errors=50
                ),
                alias="result_validation"
            ),
            
            # Result Aggregation Tool
            ResultAggregationTool(
                config=ResultAggregationConfig(
                    deduplication_method="content_hash",
                    merge_similar_results=True,
                    prioritize_sources=self.research_config.prioritize_sources or [],
                    max_results=500
                ),
                alias="result_aggregation"
            )
        ]
        
        return tools
    
    def _get_coordinator_prompt(self) -> str:
        """Generate the system prompt for the research coordinator."""
        return f"""You are a Research Coordinator Agent responsible for managing comprehensive research workflows.

Your Role and Capabilities:
1. **Research Planning**: Analyze research requirements and break them into focused tasks
2. **Agent Coordination**: Launch and coordinate multiple specialized research agents
3. **Data Analysis**: Analyze JSON results for patterns, completeness, and quality
4. **Validation**: Ensure results conform to specified schemas
5. **Aggregation**: Combine and deduplicate results from multiple sources

Research Configuration:
- Maximum agents: {self.research_config.max_agents}
- Research depth: {self.research_config.research_depth}
- Validation enabled: {self.research_config.enable_validation}
- Aggregation enabled: {self.research_config.enable_aggregation}

Workflow Guidelines:
1. **Analysis Phase**: Start by understanding the research requirements and target schema
2. **Planning Phase**: Break down complex research into focused areas and agent tasks
3. **Execution Phase**: Launch research agents systematically, monitoring their progress
4. **Quality Phase**: Analyze results for completeness, validate against schema
5. **Integration Phase**: Aggregate results, remove duplicates, and ensure quality
6. **Final Results**: Return ONLY the clean list of validated data objects

{{tools_documentation}}

CRITICAL GUIDELINES:
- Study the tool documentation above carefully before making any tool calls
- Use the exact field names and structures shown in the input schemas
- Always provide all required fields for each tool
- When you have completed research, use <RESULT> with ONLY the clean list of data objects
- DO NOT wrap results in summaries, metadata, or analysis structures
- Each <RESULT> should contain individual data objects matching the target schema
- End with "TASK_COMPLETE" when research is finished

FINAL OUTPUT FORMAT:
Your final results should be individual data objects like:
<RESULT>{{"brand": "Dell", "modelName": "XPS 13", "price": 999, ...}}</RESULT>
<RESULT>{{"brand": "HP", "modelName": "Spectre", "price": 1299, ...}}</RESULT>

DO NOT create wrapper structures like:
<RESULT>{{"summary": {...}, "matches": [...]}}</RESULT>
"""
    
    def coordinate_research(self, query: str, schema: Dict[str, Any], progress_callback=None) -> Dict[str, Any]:
        """
        Coordinate comprehensive research for a given query and schema.
        
        Args:
            query: Research query/topic
            schema: Target JSON schema for results
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dict containing research results and metadata
        """
        if progress_callback:
            progress_callback("Starting research coordination...")
        
        # Set the task description for the agent
        task_description = f"""Coordinate comprehensive research for: {query}

Target Schema: {json.dumps(schema, indent=2)}

Research Requirements:
- Maximum {self.research_config.max_agents} specialized research agents
- Research depth: {self.research_config.research_depth}
- Results must conform to the provided JSON schema
- Focus on authoritative and recent sources

Your Coordination Tasks:
1. Analyze the research requirements and identify key focus areas
2. Use the research_trigger tool with the target schema to launch research agents
3. IMPORTANT: Always include the "result_schema" field when calling research_trigger
4. Monitor agent progress and collect their results
5. Return the clean list of data objects found by the research agents
6. DO NOT add summaries, metadata, or wrapper structures

CRITICAL: When calling research_trigger, you MUST include:
- research_topic: The search query
- result_schema: The exact schema provided above
- focus_areas: Specific areas to research

Begin by calling research_trigger with the provided schema.
"""
        
        self.set_task_description(task_description)
        
        if progress_callback:
            progress_callback("Executing research coordination workflow...")
        
        # Execute the research coordination workflow
        start_time = time.time()
        self.react_loop()
        execution_time = time.time() - start_time
        
        # Process and return results
        return {
            "status": "completed" if self.is_complete else "failed",
            "results": self.results,
            "execution_time": execution_time,
            "agent_count": len(self.research_agents),
            "total_messages": len(self.conversation),
            "research_config": self.research_config.__dict__
        }
    
    def analyze_research_requirements(self, query: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze research requirements to plan coordination strategy."""
        # Extract focus areas from schema
        focus_areas = []
        if "properties" in schema:
            focus_areas = list(schema["properties"].keys())
        
        # Determine research depth and scope
        complexity_score = len(focus_areas) + (1 if "required" in schema else 0)
        
        if complexity_score <= 3:
            recommended_agents = min(2, self.research_config.max_agents)
            search_regions = ["general", "academic"]
        elif complexity_score <= 6:
            recommended_agents = min(3, self.research_config.max_agents)
            search_regions = ["general", "academic", "news"]
        else:
            recommended_agents = self.research_config.max_agents
            search_regions = ["general", "academic", "news", "technical"]
        
        return {
            "focus_areas": focus_areas,
            "complexity_score": complexity_score,
            "recommended_agents": recommended_agents,
            "search_regions": search_regions,
            "estimated_duration": complexity_score * 30,  # seconds
        }
    
    def _setup_agent(self):
        """Called after initialization to set up the coordinator."""
        # Initialize tracking variables
        self.research_agents = []
        self.research_results = []
        self.analysis_results = {}
        
        # Log coordinator setup
        if hasattr(self, 'conversation') and hasattr(self, 'tools') and self.tools:
            tool_count = len(self.tools) if isinstance(self.tools, dict) else len(self._initial_tools or [])
            setup_message = Message(
                role="system",
                content=f"Research Coordinator initialized with {tool_count} coordination tools and config: {self.research_config.__dict__}"
            )
            self.conversation.append(setup_message)
    
    def _is_task_complete(self, response) -> bool:
        """Check if the research coordination task is complete."""
        # Check for standard completion
        if super()._is_task_complete(response):
            return True
        
        # Check for research-specific completion indicators
        content = response.content.lower()
        completion_indicators = [
            "research coordination complete",
            "final results delivered",
            "comprehensive research finished",
            "aggregation complete"
        ]
        
        return any(indicator in content for indicator in completion_indicators)
    
    def _process_tool_result(self, tool_name: str, tool_result: Dict[str, Any]):
        """Process results from coordination tools."""
        # Store results for tracking
        if tool_name == "research_trigger":
            agent_result = {
                "results": tool_result.get("results", []),
                "status": "completed"
            }
            self.research_agents.append(agent_result)
            self.research_results.extend(tool_result.get("results", []))
        
        elif tool_name == "json_analysis":
            self.analysis_results = tool_result
        
        # Call parent processing
        super()._process_tool_result(tool_name, tool_result)
    
    def get_research_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of the research coordination."""
        total_results = len(self.research_results)
        successful_agents = len([a for a in self.research_agents if a["status"] == "completed"])
        
        return {
            "total_agents_launched": len(self.research_agents),
            "successful_agents": successful_agents,
            "total_results_collected": total_results,
            "analysis_summary": self.analysis_results.get("recommendations", []),
            "completion_status": "completed" if self.is_complete else "in_progress",
            "final_results": self.results
        }