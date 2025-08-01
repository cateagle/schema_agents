"""
Unit tests for the research agent.
"""

import pytest
from unittest.mock import Mock

from agent_system.agents import ResearchAgent
from agent_system.llm_apis import MockLLMApi
from agent_system.tools import WebSearchTool, WebSearchConfig
from agent_system.core import Message


class TestResearchAgent:
    """Test research agent functionality."""
    
    @pytest.fixture
    def mock_llm_api(self):
        """Create mock LLM API for research agent testing."""
        return MockLLMApi({
            "response_delay": 0.01,
            "mock_responses": [
                "I'll search for information on this topic.",
                '<TOOL>{"tool": "web_search", "input": {"query": "python programming", "max_results": 3}}</TOOL>',
                "I found some relevant information about Python programming.",
                '<RESULT>{"title": "Python Tutorial", "url": "https://python.org", "summary": "Learn Python basics"}</RESULT>',
                "TASK_COMPLETE"
            ]
        })
    
    @pytest.fixture
    def web_search_tool(self):
        """Create web search tool for testing."""
        return WebSearchTool(config=WebSearchConfig(search_engine="mock"))
    
    def test_agent_initialization(self, mock_llm_api, web_search_tool):
        """Test agent initialization."""
        agent = ResearchAgent(
            llm_api=mock_llm_api,
            tools=[web_search_tool]
        )
        
        assert agent.llm_api == mock_llm_api
        assert len(agent.tools) == 1
        assert "web_search" in agent.tools
        assert isinstance(agent.tools["web_search"], WebSearchTool)
    
    def test_agent_with_result_schema(self, mock_llm_api, web_search_tool):
        """Test agent with result schema."""
        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "url": {"type": "string"}
            }
        }
        
        agent = ResearchAgent(
            llm_api=mock_llm_api,
            tools=[web_search_tool],
            result_schema=schema
        )
        
        assert agent.result_schema == schema
    
    def test_agent_with_custom_system_prompt(self, mock_llm_api, web_search_tool):
        """Test agent with custom system prompt."""
        custom_prompt = "You are a specialized research agent focused on technology."
        
        agent = ResearchAgent(
            llm_api=mock_llm_api,
            tools=[web_search_tool],
            system_prompt=custom_prompt
        )
        
        rendered_prompt = agent._render_system_prompt()
        assert custom_prompt in rendered_prompt
    
    def test_task_description_setting(self, mock_llm_api, web_search_tool):
        """Test setting task description."""
        agent = ResearchAgent(
            llm_api=mock_llm_api,
            tools=[web_search_tool]
        )
        
        task = "Research the latest developments in AI"
        agent.set_task_description(task)
        
        assert agent.task_description == task
    
    def test_conversation_initialization(self, mock_llm_api, web_search_tool):
        """Test conversation initialization."""
        agent = ResearchAgent(
            llm_api=mock_llm_api,
            tools=[web_search_tool]
        )
        
        agent.set_task_description("Research AI developments")
        
        # Check that conversation starts with system message
        assert len(agent.conversation) == 1
        assert agent.conversation[0].role == "system"
    
    def test_results_collection(self, mock_llm_api, web_search_tool):
        """Test that agent collects results properly."""
        agent = ResearchAgent(
            llm_api=mock_llm_api,
            tools=[web_search_tool]
        )
        
        # Initially no results
        assert len(agent.results) == 0
        
        # After adding a result
        test_result = {"title": "AI News", "url": "https://example.com"}
        agent.results.append(test_result)
        
        assert len(agent.results) == 1
        assert agent.results[0] == test_result