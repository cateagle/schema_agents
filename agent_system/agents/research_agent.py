"""
Research agent implementation.
"""

from typing import Any, Dict, List, Optional
import logging

from agent_system.core.agent import Agent
from agent_system.core.llm_api import LLMApi, LLMResponse
from agent_system.core.tool import Tool
from agent_system.core.registry import register_agent
from agent_system.tools import WebSearchTool, WebSearchConfig

logger = logging.getLogger(__name__)


# Default system prompt for research
DEFAULT_RESEARCH_SYSTEM_PROMPT = """
You are a research agent specialized in finding and extracting structured data from various sources.

{{tools_documentation}}

Task: {{task_description}}

Your goal is to find actual data objects that match the expected schema, not to create research summaries or metadata.

Instructions:
1. Break down the research topic into specific search queries to find actual data
2. Use available tools to search for information
3. Extract and structure the actual data objects you find (not research metadata)
4. For each valid data object found, use <RESULT> tags with the properly structured JSON
5. Focus on finding multiple individual objects that match the schema
6. When you have found sufficient data objects, include "TASK_COMPLETE" in your response

{% if result_schema %}
Expected data object format: {{result_schema}}

IMPORTANT: Each <RESULT> should contain a single data object matching this schema, NOT research metadata or summaries.
{% endif %}

Example:
If searching for laptops, return individual laptop objects like:
<RESULT>{"brand": "Dell", "model": "XPS 13", "price": 999, "ram": 16}</RESULT>
<RESULT>{"brand": "HP", "model": "Spectre x360", "price": 1299, "ram": 32}</RESULT>

NOT research summaries like:
<RESULT>{"topic": "laptops", "summary": "Found laptops...", "sources": [...]}</RESULT>
"""

# Default result schema for research - generic data object
DEFAULT_RESEARCH_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "description": "Unique identifier"},
        "title": {"type": "string", "description": "Title or name"},
        "description": {"type": "string", "description": "Description or details"}, 
        "url": {"type": "string", "description": "Source URL if available"}
    },
    "required": ["title"]
}


@register_agent(description="An agent specialized in conducting research using available tools")
class ResearchAgent(Agent):
    """
    An agent specialized in conducting research using available tools.
    
    This agent can be fully configured with custom tools, prompts, and schemas.
    By default, it includes a web search tool and uses a research-focused prompt.
    """
    
    def __init__(
        self,
        llm_api: LLMApi,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Tool]] = None,
        result_schema: Optional[Dict[str, Any]] = None,
        timeout: float = 600.0,  # 10 minutes
        token_limit: int = 100000,
        max_tokens_per_response: int = 4000,
        identity: Optional[Dict[str, Any]] = None,
        task_description: str = ""
    ):
        """
        Initialize a research agent.
        
        Args:
            llm_api: The LLM API to use
            system_prompt: Custom system prompt (uses default if None)
            tools: List of tools to use (uses WebSearchTool if None)
            result_schema: Custom result schema (uses default if None)
            timeout: Maximum time for task completion
            token_limit: Maximum tokens to use
            max_tokens_per_response: Maximum tokens per LLM response
            identity: Identity information for tool access
            task_description: Initial task description
        """
        # Use defaults if not provided
        if system_prompt is None:
            system_prompt = DEFAULT_RESEARCH_SYSTEM_PROMPT
        
        if tools is None:
            # Default to web search tool
            tools = [WebSearchTool(config=WebSearchConfig(search_engine="mock"))]
        
        if result_schema is None:
            result_schema = DEFAULT_RESEARCH_RESULT_SCHEMA
        
        super().__init__(
            system_prompt=system_prompt,
            task_description=task_description,
            llm_api=llm_api,
            tools=tools,
            timeout=timeout,
            token_limit=token_limit,
            max_tokens_per_response=max_tokens_per_response,
            result_schema=result_schema,
            identity=identity
        )
        
        # Track search queries and results for synthesis
        self.search_queries: List[str] = []
        self.search_results: List[Dict[str, Any]] = []
    
    def _process_tool_result(self, tool_name: str, tool_result: Dict[str, Any]) -> None:
        """Process search results and build research findings."""
        print(f"🔧 [ResearchAgent] Tool '{tool_name}' returned result")
        
        if tool_name in ["web_search", "academic_search", "news_search", "technical_search", "global_search"]:
            # Store search information
            query = tool_result.get("query", "unknown")
            results = tool_result.get("results", [])
            self.search_queries.append(query)
            self.search_results.extend(results)
            
            print(f"🔍 [ResearchAgent] Search query: '{query}' returned {len(results)} results")
            
            # Log individual search results for debugging
            for i, result in enumerate(results[:3]):  # Show first 3 results
                print(f"   📄 Search result {i+1}: {result.get('title', 'No title')[:100]}")
            
            print(f"📊 [ResearchAgent] Total search queries so far: {len(self.search_queries)}")
            print(f"📊 [ResearchAgent] Total search results collected: {len(self.search_results)}")
            
            # After multiple searches, try to synthesize results
            if len(self.search_queries) >= 2:
                self._synthesize_research_results()
        else:
            print(f"🔧 [ResearchAgent] Processing non-search tool: {tool_name}")
    
    def _synthesize_research_results(self) -> None:
        """Synthesize search results into domain objects based on the result schema."""
        if not self.search_results:
            return
            
        # Don't create research metadata - the agent should produce domain objects
        # based on what it finds and the expected schema in its results
        # This method is now just a placeholder - the actual results should come
        # from the agent's <RESULT> tags during the conversation
    
    def _should_continue(self, iteration: int) -> bool:
        """Continue research until sufficient information is gathered."""
        # Complete if we have sufficient results (at least 5-10 objects)
        if len(self.results) >= 5:
            print(f"🎯 [ResearchAgent] Stopping - found {len(self.results)} results (target: 5+)")
            return False
        
        # Also check if we've done enough searches but still have few results    
        if len(self.search_queries) >= 5 and len(self.results) > 0:
            print(f"🎯 [ResearchAgent] Stopping - completed {len(self.search_queries)} searches with {len(self.results)} results")
            return False
            
        return super()._should_continue(iteration)
    
    def _is_task_complete(self, response: LLMResponse) -> bool:
        """Check if research is complete."""
        content_lower = response.content.lower()
        return (super()._is_task_complete(response) or
                "research complete" in content_lower or
                "task_complete" in content_lower)
    
    def research_topic(self, topic: str, specific_questions: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Research a specific topic.
        
        Args:
            topic: The topic to research
            specific_questions: Optional list of specific questions to investigate
            
        Returns:
            Dict containing the research results and agent status
        """
        task_desc = f"Research the topic: {topic}"
        if specific_questions:
            task_desc += f"\n\nSpecific questions to investigate:\n"
            for i, question in enumerate(specific_questions, 1):
                task_desc += f"{i}. {question}\n"
        
        self.task_description = task_desc
        
        # Reset agent state
        self.conversation = []
        self.results = []
        self.is_complete = False
        self.total_tokens_used = 0
        self.start_time = None
        self.search_queries = []
        self.search_results = []
        
        # Run the agent
        self.react_loop()
        
        return {
            "topic": topic,
            "questions": specific_questions,
            "results": self.results,
            "status": self.get_status(),
            "conversation": [msg.model_dump() for msg in self.conversation]
        }
