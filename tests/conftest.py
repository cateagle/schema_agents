"""
Shared test fixtures and configuration for agent system tests.
"""

import pytest
from agent_system.llm_apis import MockLLMApi
from agent_system.core import Agent
from agent_system.tools import CalculatorTool, WebSearchTool


@pytest.fixture
def mock_llm_api():
    """Create a basic mock LLM API for testing."""
    return MockLLMApi({
        "response_delay": 0.01,  # Fast for testing
        "mock_responses": [
            "I'll help you with this task.",
            '<TOOL>{"tool": "calculator", "input": {"expression": "2 + 2"}}</TOOL>',
            "The calculation result is 4.",
            '<RESULT>{"answer": 4, "explanation": "Calculation completed"}</RESULT>',
            "TASK_COMPLETE"
        ]
    })


@pytest.fixture
def math_llm_api():
    """Create a mock LLM API with math-focused responses."""
    return MockLLMApi({
        "response_delay": 0.01,
        "mock_responses": [
            "I'll solve this mathematical problem step by step.",
            '<TOOL>{"tool": "calculator", "input": {"expression": "sqrt(16)"}}</TOOL>',
            "The square root of 16 is 4.",
            '<RESULT>{"problem": "sqrt(16)", "solution": "4", "method": "square_root"}}</RESULT>',
            "TASK_COMPLETE"
        ]
    })


@pytest.fixture
def research_llm_api():
    """Create a mock LLM API with research-focused responses."""
    return MockLLMApi({
        "response_delay": 0.01,
        "mock_responses": [
            "I'll research this topic for you.",
            '<TOOL>{"tool": "web_search", "input": {"query": "AI research", "max_results": 5}}</TOOL>',
            "I found several relevant sources about AI research.",
            '<RESULT>{"topic": "AI research", "sources": 5, "summary": "Recent developments in AI"}}</RESULT>',
            "TASK_COMPLETE"
        ]
    })


@pytest.fixture
def basic_agent(mock_llm_api):
    """Create a basic agent for testing."""
    return Agent(
        system_prompt="You are a helpful test agent.",
        task_description="Test task",
        llm_api=mock_llm_api,
        tools=[CalculatorTool()]
    )


@pytest.fixture
def multi_tool_agent(mock_llm_api):
    """Create an agent with multiple tools."""
    return Agent(
        system_prompt="You are a multi-tool agent.",
        task_description="Use multiple tools",
        llm_api=mock_llm_api,
        tools=[
            CalculatorTool(alias="calc"),
            WebSearchTool(alias="search")
        ]
    )


@pytest.fixture
def calculator_tool():
    """Create a calculator tool for testing."""
    return CalculatorTool()


@pytest.fixture
def web_search_tool():
    """Create a web search tool for testing."""
    return WebSearchTool()


# Test configuration
def pytest_configure(config):
    """Configure pytest settings."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


# Test collection customization
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add 'unit' marker to all tests by default
        if not any(marker.name in ['integration', 'slow'] for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)
        
        # Add 'slow' marker to tests that might be slower
        if 'workflow' in item.name or 'integration' in item.name:
            item.add_marker(pytest.mark.slow)