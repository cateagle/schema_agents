"""
Research Trigger Tool for launching specialized research agents.
"""

import json
import uuid
import logging
from typing import Dict, Any, List, Optional
from pydantic import Field

from agent_system.core import Tool, ToolConfig, ToolInputBase, ToolOutputBase, ToolExecutionError, register_tool
# Import ResearchAgent dynamically to avoid circular imports
from agent_system.tools import WebSearchTool, WebSearchConfig

logger = logging.getLogger(__name__)


class ResearchTriggerConfig(ToolConfig):
    """Configuration for research trigger tool."""
    max_concurrent_agents: int = Field(default=3, description="Maximum number of concurrent research agents")
    agent_timeout: int = Field(default=300, description="Timeout for individual agents in seconds")
    default_max_results: int = Field(default=10, description="Default maximum results per agent")


class ResearchTriggerInput(ToolInputBase):
    """Input for research trigger tool."""
    research_topic: str = Field(..., description="Main research topic or query")
    result_schema: Dict[str, Any] = Field(..., description="JSON schema that results must conform to")
    focus_areas: List[str] = Field(default_factory=list, description="Specific focus areas for research")
    search_regions: List[str] = Field(default=["general", "academic"], description="Search regions to target")
    max_results_per_region: int = Field(default=5, description="Maximum results per search region")
    research_depth: str = Field(default="medium", description="Research depth: shallow, medium, deep")


class ResearchTriggerOutput(ToolOutputBase):
    """Output from research trigger tool."""
    results: List[Dict[str, Any]] = Field(..., description="Clean list of validated research results")


@register_tool(
    config_class=ResearchTriggerConfig,
    input_class=ResearchTriggerInput,
    output_class=ResearchTriggerOutput,
    description="Trigger specialized research agents for specific topics and focus areas"
)
class ResearchTriggerTool(Tool[ResearchTriggerConfig, ResearchTriggerInput, ResearchTriggerOutput]):
    """Tool for triggering specialized research agents."""
    
    def __init__(self, config: Optional[ResearchTriggerConfig] = None, alias: Optional[str] = None):
        super().__init__(
            name="research_trigger",
            short_description="Launch specialized research agents",
            long_description="Trigger and coordinate specialized research agents for focused information gathering on specific topics and areas",
            config=config or ResearchTriggerConfig(),
            alias=alias
        )
        self._llm_api = None  # Will be set by the coordinator
    
    @classmethod
    def _get_config_class(cls):
        return ResearchTriggerConfig
    
    @classmethod
    def _get_input_class(cls):
        return ResearchTriggerInput
    
    @classmethod
    def _get_output_class(cls):
        return ResearchTriggerOutput
    
    def set_llm_api(self, llm_api):
        """Set the LLM API to use for creating research agents."""
        self._llm_api = llm_api
    
    def _execute(self, input_data: ResearchTriggerInput, identity: Optional[Dict[str, Any]] = None) -> ResearchTriggerOutput:
        """Execute research agent triggering."""
        if not self._llm_api:
            raise ToolExecutionError("LLM API not configured for research trigger tool")
        
        try:
            import time
            start_time = time.time()
            
            # Generate unique agent ID
            agent_id = f"research_agent_{uuid.uuid4().hex[:8]}"
            
            print(f"🔍 [ResearchTrigger] Starting research agent {agent_id}")
            print(f"🎯 [ResearchTrigger] Topic: {input_data.research_topic}")
            print(f"🌍 [ResearchTrigger] Search regions: {input_data.search_regions}")
            print(f"📊 [ResearchTrigger] Target schema fields: {list(input_data.result_schema.get('properties', {}).keys())}")
            
            # Create specialized research tools based on regions
            tools = self._create_research_tools(input_data.search_regions)
            print(f"🛠️ [ResearchTrigger] Created {len(tools)} search tools: {[tool.alias for tool in tools]}")
            
            # Create research agent (import dynamically to avoid circular imports)
            from agent_system.agents.research_agent import ResearchAgent
            
            research_agent = ResearchAgent(
                llm_api=self._llm_api,
                tools=tools,
                system_prompt=self._generate_research_prompt(input_data),
                result_schema=input_data.result_schema
            )
            
            # Set research task
            task_description = self._generate_task_description(input_data)
            research_agent.set_task_description(task_description)
            
            # Execute research
            print(f"🚀 [ResearchTrigger] Starting react_loop for agent {agent_id}")
            try:
                research_agent.react_loop()
                agent_status = "completed"
                print(f"✅ [ResearchTrigger] Agent {agent_id} completed successfully")
            except Exception as e:
                agent_status = f"failed: {str(e)}"
                print(f"❌ [ResearchTrigger] Agent {agent_id} failed: {str(e)}")
            
            execution_time = time.time() - start_time
            
            # Log conversation details
            print(f"💬 [ResearchTrigger] Agent {agent_id} conversation length: {len(research_agent.conversation)} messages")
            print(f"📋 [ResearchTrigger] Agent {agent_id} raw results count: {len(research_agent.results)}")
            
            # Log individual results for debugging
            for i, result in enumerate(research_agent.results):
                print(f"📄 [ResearchTrigger] Result {i+1}: {str(result)[:200]}{'...' if len(str(result)) > 200 else ''}")
            
            # Process results - return clean list of validated objects
            research_results = self._extract_clean_results(research_agent.results)
            print(f"🎯 [ResearchTrigger] Agent {agent_id} final results count: {len(research_results)}")
            print(f"⏱️ [ResearchTrigger] Agent {agent_id} execution time: {execution_time:.2f}s")
            
            return ResearchTriggerOutput(
                results=research_results
            )
            
        except Exception as e:
            raise ToolExecutionError(f"Research agent triggering failed: {str(e)}")
    
    def _create_research_tools(self, search_regions: List[str]) -> List[WebSearchTool]:
        """Create specialized search tools for different regions."""
        tools = []
        
        for region in search_regions:
            # Map region names to configurations
            region_config = {
                "general": WebSearchConfig(region="us-en", search_engine="duckduckgo"),
                "academic": WebSearchConfig(region="academic", search_engine="duckduckgo"),
                "news": WebSearchConfig(region="news", search_engine="duckduckgo"),
                "technical": WebSearchConfig(region="technical", search_engine="duckduckgo"),
                "international": WebSearchConfig(region="global", search_engine="duckduckgo")
            }
            
            config = region_config.get(region, WebSearchConfig(region="us-en", search_engine="duckduckgo"))
            
            # Use standardized aliases
            alias_map = {
                "general": "web_search",
                "academic": "academic_search", 
                "news": "news_search",
                "technical": "technical_search",
                "international": "global_search"
            }
            alias = alias_map.get(region, "web_search")
            
            tool = WebSearchTool(
                config=config,
                alias=alias
            )
            tools.append(tool)
        
        return tools
    
    def _generate_research_prompt(self, input_data: ResearchTriggerInput) -> str:
        """Generate a specialized research prompt for the agent."""
        depth_instructions = {
            "shallow": "Focus on quick overview and key facts",
            "medium": "Provide comprehensive coverage with supporting details",
            "deep": "Conduct thorough investigation with multiple perspectives and detailed analysis"
        }
        
        depth_instruction = depth_instructions.get(input_data.research_depth, depth_instructions["medium"])
        
        prompt = f"""You are a specialized Research Agent focused on finding and extracting structured data objects.

Your research capabilities:
- Multiple search regions: {', '.join(input_data.search_regions)}
- Research depth: {input_data.research_depth} ({depth_instruction})
- Maximum results per region: {input_data.max_results_per_region}

{{tools_documentation}}

CRITICAL TOOL USAGE RULES:
- You can ONLY use the tools listed in the documentation above
- DO NOT use tools called "browser", "search", or any other names not listed
- Use the exact tool aliases shown in the tool documentation
- If a tool call fails, do not retry with different tool names

IMPORTANT: You must find and extract actual data objects that match the provided schema, NOT create research summaries or metadata.

Target Schema: {json.dumps(input_data.result_schema, indent=2)}

Research Guidelines:
1. Use ONLY the available search tools to find actual data objects
2. Extract individual objects that match the schema exactly
3. For each object found, use <RESULT> tags with the properly structured JSON
4. Focus on finding multiple individual objects, not research metadata
5. Use "TASK_COMPLETE" when you have found sufficient data objects

TOOL USAGE EXAMPLES:
For web search tools, use ONLY these input fields:
<TOOL>{{"tool": "web_search", "input": {{"query": "laptops 32GB RAM Germany", "max_results": 5}}}}</TOOL>

DO NOT include fields like "region", "search_engine", or other parameters - they are pre-configured.

RESULT EXAMPLES (if schema was for laptops):
<RESULT>{{"brand": "Dell", "modelName": "XPS 13", "price": 999, "ram": 16, "screenSize": 13.3, "availableInGermany": true, "sourceUrl": "https://dell.com/xps13"}}</RESULT>
<RESULT>{{"brand": "HP", "modelName": "Spectre x360", "price": 1299, "ram": 32, "screenSize": 13.5, "availableInGermany": true, "sourceUrl": "https://hp.com/spectre"}}</RESULT>

DO NOT create research summaries like:
<RESULT>{{"topic": "laptops", "summary": "Found laptops...", "sources": [...]}}</RESULT>
"""
        return prompt
    
    def _generate_task_description(self, input_data: ResearchTriggerInput) -> str:
        """Generate a detailed task description for the research agent."""
        task = f"""Research Topic: {input_data.research_topic}

Focus Areas to Investigate:
"""
        
        if input_data.focus_areas:
            for i, area in enumerate(input_data.focus_areas, 1):
                task += f"{i}. {area}\n"
        else:
            task += "- General comprehensive research\n"
        
        task += f"""
Research Requirements:
- Search across regions: {', '.join(input_data.search_regions)}
- Depth level: {input_data.research_depth}
- Target {input_data.max_results_per_region} results per search region
- Prioritize recent and authoritative sources

Expected Deliverables:
1. Comprehensive findings for each focus area
2. Source citations and URLs where available
3. Key insights and patterns identified
4. Gaps or areas needing additional research

Begin your research systematically, starting with the most important focus areas.
"""
        return task
    
    def _extract_clean_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract clean, validated results from the research agent."""
        clean_results = []
        
        for result in results:
            if isinstance(result, dict):
                # Pass through the result as-is if it's already structured correctly
                # The agent should have produced properly validated JSON objects
                clean_results.append(result)
        
        return clean_results