"""
Tests for individual tools in the agent system.
"""

import pytest
from pydantic import ValidationError

from agent_system.tools import (
    CalculatorTool, CalculatorConfig, CalculatorInput, CalculatorOutput,
    WebSearchTool, WebSearchConfig, WebSearchInput, WebSearchOutput
)
from agent_system.core import ToolExecutionError


class TestCalculatorTool:
    """Test calculator tool functionality."""
    
    def test_default_configuration(self):
        """Test calculator with default configuration."""
        tool = CalculatorTool()
        assert tool.name == "calculator"
        assert tool.config.precision == 10
        assert tool.config.allow_complex == False
        assert tool.alias == "calculator"
    
    def test_custom_configuration(self):
        """Test calculator with custom configuration."""
        config = CalculatorConfig(precision=5, allow_complex=True)
        tool = CalculatorTool(config=config, alias="custom_calc")
        
        assert tool.config.precision == 5
        assert tool.config.allow_complex == True
        assert tool.alias == "custom_calc"
    
    def test_basic_arithmetic(self):
        """Test basic arithmetic operations."""
        tool = CalculatorTool()
        
        # Addition
        result = tool.call({"expression": "2 + 3"})
        assert result["result"] == "5.0000000000"
        
        # Subtraction
        result = tool.call({"expression": "10 - 4"})
        assert result["result"] == "6.0000000000"
        
        # Multiplication
        result = tool.call({"expression": "6 * 7"})
        assert result["result"] == "42.0000000000"
        
        # Division
        result = tool.call({"expression": "15 / 3"})
        assert result["result"] == "5.0000000000"
    
    def test_complex_expressions(self):
        """Test complex mathematical expressions."""
        tool = CalculatorTool()
        
        # Order of operations
        result = tool.call({"expression": "2 + 3 * 4"})
        assert result["result"] == "14.0000000000"
        
        # Parentheses
        result = tool.call({"expression": "(2 + 3) * 4"})
        assert result["result"] == "20.0000000000"
        
        # Power
        result = tool.call({"expression": "2 ** 3"})
        assert result["result"] == "8.0000000000"
    
    def test_precision_settings(self):
        """Test different precision settings."""
        # High precision
        high_precision = CalculatorTool(config=CalculatorConfig(precision=15))
        result = high_precision.call({"expression": "1 / 3"})
        assert len(result["result"].split(".")[1]) >= 15
        
        # Low precision
        low_precision = CalculatorTool(config=CalculatorConfig(precision=2))
        result = low_precision.call({"expression": "1 / 3"})
        expected_length = 2  # "0.33" after decimal
        actual_length = len(result["result"].split(".")[1])
        assert actual_length == expected_length
    
    def test_mathematical_functions(self):
        """Test mathematical functions."""
        tool = CalculatorTool()
        
        # Square root
        result = tool.call({"expression": "sqrt(16)"})
        assert result["result"] == "4.0000000000"
        
        # Sine
        result = tool.call({"expression": "sin(0)"})
        assert result["result"] == "0.0000000000"
        
        # Natural log
        result = tool.call({"expression": "log(1)"})
        assert result["result"] == "0.0000000000"
    
    def test_invalid_expressions(self):
        """Test handling of invalid expressions."""
        tool = CalculatorTool()
        
        # Division by zero
        with pytest.raises(ToolExecutionError):
            tool.call({"expression": "1 / 0"})
        
        # Invalid syntax
        with pytest.raises(ToolExecutionError):
            tool.call({"expression": "2 +"})
        
        # Undefined variable
        with pytest.raises(ToolExecutionError):
            tool.call({"expression": "x + 1"})
    
    def test_input_validation(self):
        """Test input validation."""
        tool = CalculatorTool()
        
        # Valid input
        result = tool.call({"expression": "1 + 1"})
        assert "result" in result
        
        # Missing expression
        with pytest.raises(ValidationError):
            tool.call({})
        
        # Wrong type
        with pytest.raises(ValidationError):
            tool.call({"expression": 123})  # Should be string
        
        # Extra fields
        with pytest.raises(ValidationError):
            tool.call({"expression": "1 + 1", "extra_field": "value"})


class TestWebSearchTool:
    """Test web search tool functionality."""
    
    def test_default_configuration(self):
        """Test web search with default configuration."""
        tool = WebSearchTool()
        assert tool.name == "web_search"
        assert tool.config.search_engine == "mock"
        assert tool.config.region == "us-en"
        assert tool.config.safe_search == True
        assert tool.alias == "web_search"
    
    def test_custom_configuration(self):
        """Test web search with custom configuration."""
        config = WebSearchConfig(
            search_engine="google",
            region="uk-en",
            safe_search=False,
            api_key="test-key"
        )
        tool = WebSearchTool(config=config, alias="google_search")
        
        assert tool.config.search_engine == "google"
        assert tool.config.region == "uk-en"
        assert tool.config.safe_search == False
        assert tool.config.api_key == "test-key"
        assert tool.alias == "google_search"
    
    def test_basic_search(self):
        """Test basic search functionality."""
        tool = WebSearchTool()
        
        result = tool.call({
            "query": "Python programming",
            "max_results": 5
        })
        
        assert "results" in result
        assert "query" in result
        assert "count" in result
        assert result["query"] == "Python programming"
        assert isinstance(result["results"], list)
        assert result["count"] >= 0
        assert len(result["results"]) <= 5
    
    def test_result_limiting(self):
        """Test that max_results is respected."""
        tool = WebSearchTool()
        
        # Request 3 results
        result = tool.call({
            "query": "test query",
            "max_results": 3
        })
        
        assert len(result["results"]) <= 3
        assert result["count"] == len(result["results"])
    
    def test_different_regions(self):
        """Test search with different regions."""
        # US region
        us_tool = WebSearchTool(config=WebSearchConfig(region="us-en"))
        us_result = us_tool.call({"query": "test", "max_results": 3})
        assert "results" in us_result
        
        # UK region  
        uk_tool = WebSearchTool(config=WebSearchConfig(region="uk-en"))
        uk_result = uk_tool.call({"query": "test", "max_results": 3})
        assert "results" in uk_result
        
        # Academic region
        academic_tool = WebSearchTool(config=WebSearchConfig(region="academic"))
        academic_result = academic_tool.call({"query": "test", "max_results": 3})
        assert "results" in academic_result
    
    def test_input_validation(self):
        """Test input validation."""
        tool = WebSearchTool()
        
        # Valid input
        result = tool.call({"query": "test", "max_results": 5})
        assert "results" in result
        
        # Missing query
        with pytest.raises(ValidationError):
            tool.call({"max_results": 5})
        
        # Invalid max_results (too low)
        with pytest.raises(ValidationError):
            tool.call({"query": "test", "max_results": 0})
        
        # Invalid max_results (too high)
        with pytest.raises(ValidationError):
            tool.call({"query": "test", "max_results": 101})
        
        # Wrong type for query
        with pytest.raises(ValidationError):
            tool.call({"query": 123, "max_results": 5})
    
    def test_mock_search_results(self):
        """Test mock search result structure."""
        tool = WebSearchTool()
        result = tool.call({"query": "artificial intelligence", "max_results": 3})
        
        # Check result structure
        assert isinstance(result["results"], list)
        assert isinstance(result["count"], int)
        assert isinstance(result["query"], str)
        
        # Check individual result structure
        if result["results"]:
            first_result = result["results"][0]
            assert isinstance(first_result, dict)
            # Mock results should have basic structure
            assert "title" in first_result or isinstance(first_result, str)
    
    def test_empty_query_handling(self):
        """Test handling of edge cases."""
        tool = WebSearchTool()
        
        # Very short query
        result = tool.call({"query": "a", "max_results": 3})
        assert "results" in result
        
        # Query with special characters
        result = tool.call({"query": "test & search", "max_results": 3})
        assert "results" in result
    
    def test_multiple_tool_instances(self):
        """Test using multiple search tool instances."""
        # Different search engines
        google_tool = WebSearchTool(
            config=WebSearchConfig(search_engine="google"),
            alias="google"
        )
        bing_tool = WebSearchTool(
            config=WebSearchConfig(search_engine="bing"),
            alias="bing"
        )
        
        assert google_tool.alias == "google"
        assert bing_tool.alias == "bing"
        assert google_tool.config.search_engine == "google"
        assert bing_tool.config.search_engine == "bing"
        
        # Both should work independently
        google_result = google_tool.call({"query": "test", "max_results": 3})
        bing_result = bing_tool.call({"query": "test", "max_results": 3})
        
        assert "results" in google_result
        assert "results" in bing_result


class TestToolEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_tool_with_none_config(self):
        """Test tool creation with None config."""
        tool = CalculatorTool(config=None)
        # Should use default config
        assert tool.config.precision == 10
    
    def test_tool_execution_identity_parameter(self):
        """Test tool execution with identity parameter."""
        tool = CalculatorTool()
        
        # Direct call to _execute method
        input_data = CalculatorInput(expression="2 + 2")
        result = tool._execute(input_data, identity="test_identity")
        
        assert isinstance(result, CalculatorOutput)
        assert result.result == "4.0000000000"
    
    def test_tool_class_methods(self):
        """Test tool class methods."""
        # Test class methods return correct types
        assert CalculatorTool._get_config_class() == CalculatorConfig
        assert CalculatorTool._get_input_class() == CalculatorInput
        assert CalculatorTool._get_output_class() == CalculatorOutput
        
        assert WebSearchTool._get_config_class() == WebSearchConfig
        assert WebSearchTool._get_input_class() == WebSearchInput
        assert WebSearchTool._get_output_class() == WebSearchOutput
    
    def test_tool_descriptions(self):
        """Test tool descriptions are set properly."""
        calc_tool = CalculatorTool()
        assert calc_tool.short_description
        assert calc_tool.long_description
        assert len(calc_tool.short_description) < len(calc_tool.long_description)
        
        search_tool = WebSearchTool()
        assert search_tool.short_description
        assert search_tool.long_description
        assert len(search_tool.short_description) < len(search_tool.long_description)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])