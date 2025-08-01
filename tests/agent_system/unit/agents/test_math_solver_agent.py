"""
Unit tests for the math solver agent.
"""

import pytest
from unittest.mock import Mock

from agent_system.agents import MathSolverAgent
from agent_system.llm_apis import MockLLMApi
from agent_system.tools import CalculatorTool, CalculatorConfig
from agent_system.core import Message


class TestMathSolverAgent:
    """Test math solver agent functionality."""
    
    @pytest.fixture
    def mock_llm_api(self):
        """Create mock LLM API for math solver testing."""
        return MockLLMApi({
            "response_delay": 0.01,
            "mock_responses": [
                "I'll solve this mathematical problem step by step.",
                '<TOOL>{"tool": "calculator", "input": {"expression": "2 + 2"}}</TOOL>',
                "The calculation shows that 2 + 2 = 4.",
                '<RESULT>{"problem": "2 + 2", "solution": "4", "steps": ["Add 2 + 2", "Result is 4"]}</RESULT>',
                "TASK_COMPLETE"
            ]
        })
    
    @pytest.fixture
    def calculator_tool(self):
        """Create calculator tool for testing."""
        return CalculatorTool(config=CalculatorConfig(precision=5))
    
    def test_agent_initialization(self, mock_llm_api, calculator_tool):
        """Test agent initialization."""
        agent = MathSolverAgent(
            llm_api=mock_llm_api,
            tools=[calculator_tool]
        )
        
        assert agent.llm_api == mock_llm_api
        assert len(agent.tools) == 1
        assert "calculator" in agent.tools
        assert isinstance(agent.tools["calculator"], CalculatorTool)
    
    def test_agent_with_custom_system_prompt(self, mock_llm_api, calculator_tool):
        """Test agent with custom system prompt."""
        custom_prompt = "You are a specialized math solver."
        
        agent = MathSolverAgent(
            llm_api=mock_llm_api,
            tools=[calculator_tool],
            system_prompt=custom_prompt
        )
        
        rendered_prompt = agent._render_system_prompt()
        assert custom_prompt in rendered_prompt
    
    def test_task_description_setting(self, mock_llm_api, calculator_tool):
        """Test setting task description."""
        agent = MathSolverAgent(
            llm_api=mock_llm_api,
            tools=[calculator_tool]
        )
        
        task = "Solve the equation: 2x + 5 = 15"
        agent.set_task_description(task)
        
        assert agent.task_description == task
    
    def test_conversation_initialization(self, mock_llm_api, calculator_tool):
        """Test conversation initialization."""
        agent = MathSolverAgent(
            llm_api=mock_llm_api,
            tools=[calculator_tool]
        )
        
        agent.set_task_description("Solve: 1 + 1")
        
        # Check that conversation starts with system message
        assert len(agent.conversation) == 1
        assert agent.conversation[0].role == "system"
    
    def test_results_collection(self, mock_llm_api, calculator_tool):
        """Test that agent collects results properly."""
        agent = MathSolverAgent(
            llm_api=mock_llm_api,
            tools=[calculator_tool]
        )
        
        # Initially no results
        assert len(agent.results) == 0
        
        # After adding a result
        test_result = {"problem": "1+1", "solution": "2"}
        agent.results.append(test_result)
        
        assert len(agent.results) == 1
        assert agent.results[0] == test_result