"""
Unit tests for the analysis agent.
"""

import pytest
from unittest.mock import Mock

from agent_system.agents import AnalysisAgent
from agent_system.llm_apis import MockLLMApi
from agent_system.tools import JSONAnalysisTool
from agent_system.core import Message


class TestAnalysisAgent:
    """Test analysis agent functionality."""
    
    @pytest.fixture
    def mock_llm_api(self):
        """Create mock LLM API for analysis agent testing."""
        return MockLLMApi({
            "response_delay": 0.01,
            "mock_responses": [
                "I'll analyze this data systematically.",
                '<TOOL>{"tool": "json_analysis", "input": {"data": "[{\"name\": \"test\"}]"}}</TOOL>',
                "The analysis shows interesting patterns in the data.",
                '<RESULT>{"insights": ["Data contains 1 record", "All records have name field"], "summary": "Simple dataset"}</RESULT>',
                "TASK_COMPLETE"
            ]
        })
    
    @pytest.fixture
    def json_analysis_tool(self):
        """Create JSON analysis tool for testing."""
        return JSONAnalysisTool()
    
    def test_agent_initialization(self, mock_llm_api, json_analysis_tool):
        """Test agent initialization."""
        agent = AnalysisAgent(
            llm_api=mock_llm_api,
            tools=[json_analysis_tool]
        )
        
        assert agent.llm_api == mock_llm_api
        assert len(agent.tools) == 2  # json_analysis + calculator from _setup_agent
        assert "json_analysis" in agent.tools
        assert "calculator" in agent.tools
        assert isinstance(agent.tools["json_analysis"], JSONAnalysisTool)
    
    def test_agent_with_custom_analysis_type(self, mock_llm_api, json_analysis_tool):
        """Test agent with custom analysis type."""
        analysis_type = "market"
        
        agent = AnalysisAgent(
            llm_api=mock_llm_api,
            tools=[json_analysis_tool],
            analysis_type=analysis_type
        )
        
        rendered_prompt = agent._render_system_prompt()
        assert f"specialized in {analysis_type} analysis" in rendered_prompt
    
    def test_task_description_setting(self, mock_llm_api, json_analysis_tool):
        """Test setting task description."""
        agent = AnalysisAgent(
            llm_api=mock_llm_api,
            tools=[json_analysis_tool]
        )
        
        task = "Analyze the sales data for patterns and trends"
        agent.set_task_description(task)
        
        assert agent.task_description == task
    
    def test_conversation_initialization(self, mock_llm_api, json_analysis_tool):
        """Test conversation initialization."""
        agent = AnalysisAgent(
            llm_api=mock_llm_api,
            tools=[json_analysis_tool]
        )
        
        agent.set_task_description("Analyze data trends")
        
        # Check that conversation starts with system message
        assert len(agent.conversation) == 1
        assert agent.conversation[0].role == "system"
    
    def test_results_collection(self, mock_llm_api, json_analysis_tool):
        """Test that agent collects results properly."""
        agent = AnalysisAgent(
            llm_api=mock_llm_api,
            tools=[json_analysis_tool]
        )
        
        # Initially no results
        assert len(agent.results) == 0
        
        # After adding a result
        test_result = {"insights": ["Pattern 1", "Pattern 2"], "summary": "Data shows growth"}
        agent.results.append(test_result)
        
        assert len(agent.results) == 1
        assert agent.results[0] == test_result