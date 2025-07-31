"""
Web search tool for finding information online.
"""

from typing import Any, Dict, Optional, List, Type
from pydantic import BaseModel, Field
import logging
import requests
import json
from urllib.parse import quote_plus

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
    query: str = Field(..., description="Search query string")
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
        """Perform actual DuckDuckGo search using their HTML search."""
        try:
            # DuckDuckGo HTML search endpoint
            query_encoded = quote_plus(input_data.query)
            url = f"https://duckduckgo.com/html/?q={query_encoded}"
            
            # Set up headers to mimic a real browser with more realistic values
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Use session for better connection handling
            session = requests.Session()
            session.headers.update(headers)
            
            response = session.get(url, timeout=15)
            response.raise_for_status()
            
            # Check if we got redirected or blocked
            if "duckduckgo.com" not in response.url:
                logger.warning(f"DuckDuckGo redirected to: {response.url}")
            
            if len(response.text) < 1000:
                logger.warning(f"DuckDuckGo returned suspiciously short response: {len(response.text)} chars")
            
            # Parse results from HTML (basic extraction)
            results = self._parse_duckduckgo_html(response.text, input_data.max_results)
            
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
    
    def _parse_duckduckgo_html(self, html_content: str, max_results: int) -> List[WebSearchResult]:
        """Parse DuckDuckGo HTML response to extract search results."""
        try:
            import re
            
            results = []
            
            # Try multiple patterns for different DuckDuckGo layouts
            patterns = [
                # Current pattern
                r'<div class="result__body">.*?<a class="result__a" href="([^"]*)"[^>]*>([^<]*)</a>.*?<a class="result__snippet"[^>]*>([^<]*)</a>',
                # Alternative pattern for newer layout
                r'<h2 class="result__title">.*?<a rel="nofollow" href="([^"]*)"[^>]*>([^<]*)</a>.*?<div class="result__snippet">([^<]*)</div>',
                # Simplified pattern
                r'<a rel="nofollow" href="([^"]*)"[^>]*>([^<]*)</a>.*?<div[^>]*snippet[^>]*>([^<]*)</div>',
                # Very basic pattern
                r'href="(https?://[^"]*)"[^>]*>([^<]+)</a>'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
                
                for i, match in enumerate(matches[:max_results]):
                    if len(match) >= 2:
                        url = match[0].strip()
                        title = re.sub(r'<[^>]+>', '', match[1]).strip()
                        snippet = re.sub(r'<[^>]+>', '', match[2]).strip() if len(match) > 2 else "No snippet available"
                        
                        # Filter out internal DuckDuckGo URLs
                        if url and title and not url.startswith('https://duckduckgo.com'):
                            results.append(WebSearchResult(
                                title=title[:200],  # Limit title length
                                url=url,
                                snippet=snippet[:300] if snippet else "No snippet available"
                            ))
                
                # If we found results with this pattern, stop trying others
                if results:
                    break
            
            # If still no results, log the HTML for debugging
            if not results:
                logger.debug(f"DuckDuckGo HTML sample: {html_content[:1000]}...")
                logger.error("DuckDuckGo HTML parsing failed - no results found with any pattern")
                raise Exception("No search results found - HTML parsing failed")
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Error parsing DuckDuckGo HTML: {str(e)}")
            raise Exception(f"DuckDuckGo search parsing failed: {str(e)}")