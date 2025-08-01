"""
Web search tool for finding information online.
"""

from typing import Any, Dict, Optional, List, Type
from pydantic import BaseModel, Field
import logging
from ddgs import DDGS

from agent_system.core.tool import Tool, ToolExecutionError
from agent_system.core.base_models import ToolConfig, ToolInputBase, ToolOutputBase
from agent_system.core.registry import register_tool

logger = logging.getLogger(__name__)


class WebSearchConfig(ToolConfig):
    """Configuration for the web search tool."""
    search_engine: str = Field(default="mock", description="Search engine to use (mock, google, bing, etc.)")
    api_key: Optional[str] = Field(default=None, description="API key for the search service")
    safe_search: bool = Field(default=True, description="Enable safe search filtering")
    region: str = Field(default="us-en", description="Region/language for search results")


class WebSearchInput(ToolInputBase):
    """Input schema for web search tool."""
    query: str = Field(..., description="Search query string", min_length=1)
    max_results: int = Field(default=5, description="Maximum number of results to return", ge=1, le=50)


class WebSearchResult(BaseModel):
    """Schema for a single search result."""
    title: str = Field(..., description="Title of the search result")
    url: str = Field(..., description="URL of the search result")
    snippet: str = Field(..., description="Brief excerpt from the content")


class WebSearchOutput(ToolOutputBase):
    """Output schema for web search tool."""
    query: str = Field(..., description="Original search query")
    results: List[WebSearchResult] = Field(..., description="List of search results")
    total_results: int = Field(..., description="Total number of results found")
    count: int = Field(..., description="Number of results returned")


@register_tool(
    config_class=WebSearchConfig,
    input_class=WebSearchInput,
    output_class=WebSearchOutput,
    description="A web search tool for finding information online"
)
class WebSearchTool(Tool[WebSearchConfig, WebSearchInput, WebSearchOutput]):
    """
    A web search tool that can search for information online.
    
    This is currently a mock implementation for demonstration purposes.
    In a real implementation, this would connect to a search API like
    Google, Bing, or DuckDuckGo.
    """
    
    def __init__(
        self,
        config: Optional[WebSearchConfig] = None,
        alias: Optional[str] = None
    ):
        """
        Initialize the web search tool.
        
        Args:
            config: Optional configuration for the search tool
            alias: Optional alias for this tool instance
        """
        super().__init__(
            name="web_search",
            short_description="Searches the web for information",
            long_description="Performs web searches and returns relevant results. Can be configured to use different search engines and regions.",
            config=config,
            alias=alias
        )
    
    @classmethod
    def _get_config_class(cls) -> Type[WebSearchConfig]:
        return WebSearchConfig
    
    @classmethod
    def _get_input_class(cls) -> Type[WebSearchInput]:
        return WebSearchInput
    
    @classmethod
    def _get_output_class(cls) -> Type[WebSearchOutput]:
        return WebSearchOutput
    
    def _execute(self, input_data: WebSearchInput, identity: Optional[Dict[str, Any]] = None) -> WebSearchOutput:
        """
        Execute the web search with validated input.
        
        Args:
            input_data: Validated search input
            identity: Optional identity for access control
            
        Returns:
            WebSearchOutput with search results
            
        Raises:
            ToolExecutionError: If search fails
        """
        # In a real implementation, this would check the config.search_engine
        # and make actual API calls. For now, we'll use mock data.
        
        # For now, all search engines are mocked with slightly different results
        if self.config.search_engine == "duckduckgo":
            return self._search_duckduckgo(input_data)
        elif self.config.search_engine in ["mock", "google", "bing"]:
            # Generate mock results with engine-specific touches
            mock_results = []
            for i in range(min(input_data.max_results, 3)):
                result = WebSearchResult(
                    title=f"[{self.config.search_engine.upper()}] Result {i+1} for '{input_data.query}'",
                    url=f"https://example.com/{self.config.search_engine}/result{i+1}",
                    snippet=f"This is a mock search result snippet for '{input_data.query}' from {self.config.search_engine}. "
                           f"It contains relevant information about the topic from {self.config.region}."
                )
                mock_results.append(result)
            
            logger.info(f"Web search for '{input_data.query}' returned {len(mock_results)} results using {self.config.search_engine}")
            
            return WebSearchOutput(
                query=input_data.query,
                results=mock_results,
                total_results=len(mock_results),
                count=len(mock_results)
            )
        else:
            raise ToolExecutionError(
                f"Search engine '{self.config.search_engine}' is not implemented. "
                "Supported engines: mock, google, bing, duckduckgo"
            )
    
    def _search_duckduckgo(self, input_data: WebSearchInput) -> WebSearchOutput:
        """Perform actual DuckDuckGo search using the ddgs library."""
        try:
            with DDGS() as ddgs:
                # Perform search using the ddgs library
                search_results = list(ddgs.text(
                    query=input_data.query,
                    max_results=input_data.max_results,
                    region=self.config.region,
                    safesearch='moderate' if self.config.safe_search else 'off'
                ))
            
            
            # Convert ddgs results to our WebSearchResult format
            results = []
            for result in search_results:
                if isinstance(result, dict) and result.get('href') and result.get('title'):
                    web_result = WebSearchResult(
                        title=result.get('title', 'No title'),
                        url=result.get('href', ''),
                        snippet=result.get('body', 'No snippet available')
                    )
                    results.append(web_result)
            
            logger.info(f"DuckDuckGo search for '{input_data.query}' returned {len(results)} results")
            
            return WebSearchOutput(
                query=input_data.query,
                results=results,
                total_results=len(results),
                count=len(results)
            )
            
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {str(e)}")
            raise ToolExecutionError(f"DuckDuckGo search failed: {str(e)}")
    
