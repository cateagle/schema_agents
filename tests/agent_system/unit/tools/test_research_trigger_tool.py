"""
Unit tests for the research trigger tool.
"""

import pytest
from unittest.mock import Mock, MagicMock
from pydantic import ValidationError

from agent_system.tools import ResearchTriggerTool, ResearchTriggerConfig, ResearchTriggerInput, ResearchTriggerOutput
from agent_system.core import ToolExecutionError


class TestResearchTriggerTool:
    """Test research trigger tool functionality."""
    
    def test_default_configuration(self):
        """Test research trigger tool with default configuration."""
        tool = ResearchTriggerTool()
        assert tool.name == "research_trigger"
        assert tool.config.max_concurrent_agents == 3
        assert tool.config.agent_timeout == 300
        assert tool.config.default_max_results == 10
        assert tool.alias == "research_trigger"
    
    def test_custom_configuration(self):
        """Test research trigger tool with custom configuration."""
        config = ResearchTriggerConfig(
            max_concurrent_agents=5,
            agent_timeout=600,
            default_max_results=20
        )
        tool = ResearchTriggerTool(config=config, alias="custom_research")
        
        assert tool.config.max_concurrent_agents == 5
        assert tool.config.agent_timeout == 600
        assert tool.config.default_max_results == 20
        assert tool.alias == "custom_research"
    
    def test_input_validation(self):
        """Test input validation."""
        # Valid input
        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "url": {"type": "string"}
            }
        }
        
        input_data = ResearchTriggerInput(
            research_topic="test topic",
            result_schema=schema,
            focus_areas=["area1", "area2"],
            search_regions=["general"],
            max_results_per_region=5,
            research_depth="medium"
        )
        
        assert input_data.research_topic == "test topic"
        assert input_data.result_schema == schema
        assert input_data.focus_areas == ["area1", "area2"]
        assert input_data.search_regions == ["general"]
        assert input_data.max_results_per_region == 5
        assert input_data.research_depth == "medium"
        
        # Missing required fields
        with pytest.raises(ValidationError):
            ResearchTriggerInput(research_topic="test")  # Missing result_schema
    
    def test_llm_api_not_set(self):
        """Test execution without LLM API set."""
        tool = ResearchTriggerTool()
        
        schema = {"type": "object", "properties": {"title": {"type": "string"}}}
        input_data = ResearchTriggerInput(
            research_topic="test",
            result_schema=schema
        )
        
        with pytest.raises(ToolExecutionError) as exc_info:
            tool.call(input_data.model_dump())
        
        assert "LLM API not configured" in str(exc_info.value)
    
    def test_set_llm_api(self):
        """Test setting LLM API."""
        tool = ResearchTriggerTool()
        mock_llm_api = Mock()
        
        tool.set_llm_api(mock_llm_api)
        assert tool._llm_api == mock_llm_api
    
    @pytest.fixture
    def mock_research_agent(self):
        """Create a mock research agent."""
        mock_agent = Mock()
        mock_agent.results = [
            {"title": "Test Result 1", "url": "https://example1.com"},
            {"title": "Test Result 2", "url": "https://example2.com"}
        ]
        mock_agent.conversation = ["msg1", "msg2"]
        return mock_agent
    
    def test_create_research_tools(self):
        """Test research tool creation."""
        tool = ResearchTriggerTool()
        
        search_regions = ["general", "academic"]
        tools = tool._create_research_tools(search_regions)
        
        assert len(tools) == 2
        assert tools[0].alias == "web_search"
        assert tools[1].alias == "academic_search"
    
    def test_extract_clean_results(self):
        """Test clean results extraction."""
        tool = ResearchTriggerTool()
        
        raw_results = [
            {"title": "Result 1", "url": "https://example1.com"},
            {"title": "Result 2", "url": "https://example2.com"},
            "invalid_result",  # Should be filtered out
            {"title": "Result 3", "url": "https://example3.com"}
        ]
        
        clean_results = tool._extract_clean_results(raw_results)
        
        assert len(clean_results) == 3
        assert all(isinstance(result, dict) for result in clean_results)
        assert clean_results[0]["title"] == "Result 1"
        assert clean_results[1]["title"] == "Result 2"
        assert clean_results[2]["title"] == "Result 3"