"""
Unit tests for the web search tool (mocked, no actual web requests).
"""

import pytest
from unittest.mock import Mock, patch
from pydantic import ValidationError

from agent_system.tools import WebSearchTool, WebSearchConfig, WebSearchInput, WebSearchOutput, WebSearchResult
from agent_system.core import ToolExecutionError


class TestWebSearchTool:
    """Test web search tool functionality with mocked responses."""
    
    def test_default_configuration(self):
        """Test web search tool with default configuration."""
        tool = WebSearchTool()
        assert tool.name == "web_search"
        assert tool.config.search_engine == "mock"
        assert tool.config.safe_search == True
        assert tool.alias == "web_search"
    
    def test_custom_configuration(self):
        """Test web search tool with custom configuration."""
        config = WebSearchConfig(
            search_engine="duckduckgo",
            safe_search=False,
            region="de-de"
        )
        tool = WebSearchTool(config=config, alias="custom_search")
        
        assert tool.config.search_engine == "duckduckgo"
        assert tool.config.safe_search == False
        assert tool.config.region == "de-de"
        assert tool.alias == "custom_search"
    
    def test_mock_search_basic(self):
        """Test basic mock search functionality."""
        tool = WebSearchTool(config=WebSearchConfig(search_engine="mock"))
        
        input_data = WebSearchInput(query="python programming", max_results=3)
        result = tool.call(input_data.model_dump())
        
        assert isinstance(result, dict)
        assert result['query'] == "python programming"
        assert len(result['results']) == 3
        assert result['total_results'] == 3
        assert result['count'] == 3
        
        for search_result in result['results']:
            assert isinstance(search_result, dict)
            assert search_result['title']
            assert search_result['url']
            assert search_result['snippet']
    
    def test_mock_search_different_engines(self):
        """Test mock search with different engine configurations."""
        engines = ["mock", "google", "bing"]
        
        for engine in engines:
            tool = WebSearchTool(config=WebSearchConfig(search_engine=engine))
            input_data = WebSearchInput(query="test query", max_results=2)
            result = tool.call(input_data.model_dump())
            
            assert len(result['results']) == 2
            assert engine.upper() in result['results'][0]['title']
    
    def test_max_results_limit(self):
        """Test that max_results is respected."""
        tool = WebSearchTool(config=WebSearchConfig(search_engine="mock"))
        
        # Test with different limits
        for max_results in [1, 2, 5]:
            input_data = WebSearchInput(query="test", max_results=max_results)
            result = tool.call(input_data.model_dump())
            assert len(result['results']) == min(max_results, 3)  # Mock returns max 3
    
    def test_input_validation(self):
        """Test input validation."""
        tool = WebSearchTool()
        
        # Valid input
        input_data = WebSearchInput(query="valid query", max_results=5)
        result = tool.call(input_data.model_dump())
        assert isinstance(result, dict)
        
        # Empty query
        with pytest.raises(ValidationError):
            WebSearchInput(query="", max_results=5)
        
        # Invalid max_results (too low)
        with pytest.raises(ValidationError):
            WebSearchInput(query="test", max_results=0)
        
        # Invalid max_results (too high)
        with pytest.raises(ValidationError):
            WebSearchInput(query="test", max_results=100)
    
    def test_unsupported_search_engine(self):
        """Test handling of unsupported search engines."""
        tool = WebSearchTool(config=WebSearchConfig(search_engine="unsupported"))
        input_data = WebSearchInput(query="test", max_results=3)
        
        with pytest.raises(ToolExecutionError) as exc_info:
            tool.call(input_data.model_dump())
        
        assert "not implemented" in str(exc_info.value).lower()
    
    @patch('ddgs.DDGS.text')
    def test_duckduckgo_failure(self, mock_text):
        """Test DuckDuckGo search failure handling."""
        # Mock a failed search
        mock_text.side_effect = Exception("Network error")
        
        tool = WebSearchTool(config=WebSearchConfig(search_engine="duckduckgo"))
        input_data = WebSearchInput(query="test", max_results=3)
        
        with pytest.raises(ToolExecutionError) as exc_info:
            tool.call(input_data.model_dump())
        
        assert "DuckDuckGo search failed" in str(exc_info.value)
    
    def test_result_model_validation(self):
        """Test WebSearchResult model validation."""
        # Valid result
        result = WebSearchResult(
            title="Test Title",
            url="https://example.com",
            snippet="Test snippet"
        )
        assert result.title == "Test Title"
        assert result.url == "https://example.com"
        assert result.snippet == "Test snippet"
        
        # Missing required fields
        with pytest.raises(ValidationError):
            WebSearchResult(title="Test")  # Missing url and snippet
    
    def test_output_model_validation(self):
        """Test WebSearchOutput model validation."""
        results = [
            WebSearchResult(
                title="Test 1",
                url="https://example1.com",
                snippet="Snippet 1"
            ),
            WebSearchResult(
                title="Test 2", 
                url="https://example2.com",
                snippet="Snippet 2"
            )
        ]
        
        output = WebSearchOutput(
            query="test query",
            results=results,
            total_results=2,
            count=2
        )
        
        assert output.query == "test query"
        assert len(output.results) == 2
        assert output.total_results == 2
        assert output.count == 2