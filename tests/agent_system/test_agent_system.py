"""
Comprehensive test suite for the agent system.
Tests core functionality with mock LLM APIs without making actual API calls.
"""

import pytest
import json
from unittest.mock import Mock, patch
from typing import Dict, Any

from agent_system.core import (
    Agent, Tool, ToolConfig, ToolInputBase, ToolOutputBase, 
    ResponseParser, get_registry, Message, LLMResponse
)
from agent_system.llm_apis import MockLLMApi
from agent_system.tools import CalculatorTool, CalculatorConfig, WebSearchTool, WebSearchConfig
from agent_system.agents import MathSolverAgent, ResearchAgent

# Test Fixtures
@pytest.fixture
def mock_llm_api():
    """Create a mock LLM API with predefined responses."""
    return MockLLMApi({
        "response_delay": 0.01,  # Fast for testing
        "mock_responses": [
            "I'll help you with this task.",
            '<TOOL>{"tool": "calculator", "input": {"expression": "2 + 2"}}</TOOL>',
            "The calculation result is 4.",
            '<RESULT>{"answer": 4, "explanation": "2 + 2 equals 4"}</RESULT>',
            "TASK_COMPLETE"
        ]
    })

@pytest.fixture 
def basic_agent(mock_llm_api):
    """Create a basic agent for testing."""
    return Agent(
        system_prompt="You are a helpful test agent. {{tools_documentation}}",
        task_description="Test task",
        llm_api=mock_llm_api,
        tools=[CalculatorTool()]
    )

class MockTestTool(Tool):
    """Simple test tool for testing."""
    
    class TestConfig(ToolConfig):
        test_param: str = "default"
    
    class TestInput(ToolInputBase):
        message: str
    
    class TestOutput(ToolOutputBase):
        response: str
    
    def __init__(self, config=None, alias=None):
        super().__init__(
            name="test_tool",
            short_description="Test tool",
            long_description="Tool for testing purposes",
            config=config or self.TestConfig(),
            alias=alias
        )
    
    @classmethod
    def _get_config_class(cls):
        return cls.TestConfig
    
    @classmethod
    def _get_input_class(cls):
        return cls.TestInput
    
    @classmethod
    def _get_output_class(cls):
        return cls.TestOutput
    
    def _execute(self, input_data, identity=None):
        return self.TestOutput(response=f"Test response: {input_data.message}")


class TestTools:
    """Test tool functionality."""
    
    def test_calculator_tool_creation(self):
        """Test creating a calculator tool."""
        tool = CalculatorTool()
        assert tool.name == "calculator"
        assert tool.alias == "calculator"
        assert isinstance(tool.config, CalculatorConfig)
    
    def test_calculator_tool_with_config(self):
        """Test calculator tool with custom configuration."""
        config = CalculatorConfig(precision=5)
        tool = CalculatorTool(config=config, alias="precise_calc")
        assert tool.config.precision == 5
        assert tool.alias == "precise_calc"
    
    def test_calculator_tool_execution(self):
        """Test calculator tool execution."""
        tool = CalculatorTool()
        result = tool.call({"expression": "2 + 2"})
        assert "result" in result
        assert result["result"] == "4.0000000000"
    
    def test_web_search_tool_creation(self):
        """Test creating a web search tool."""
        tool = WebSearchTool()
        assert tool.name == "web_search"
        assert isinstance(tool.config, WebSearchConfig)
    
    def test_web_search_tool_execution(self):
        """Test web search tool execution."""
        tool = WebSearchTool()
        result = tool.call({"query": "test query", "max_results": 3})
        assert "results" in result
        assert "query" in result
        assert isinstance(result["results"], list)
    
    def test_tool_with_alias(self):
        """Test tool with alias."""
        tool1 = CalculatorTool(alias="calc1")
        tool2 = CalculatorTool(alias="calc2")
        assert tool1.alias == "calc1"
        assert tool2.alias == "calc2"
    
    def test_custom_test_tool(self):
        """Test custom test tool."""
        tool = MockTestTool()
        result = tool.call({"message": "hello world"})
        assert result["response"] == "Test response: hello world"
    
    def test_tool_input_validation(self):
        """Test tool input validation."""
        tool = CalculatorTool()
        
        # Valid input should work
        result = tool.call({"expression": "1 + 1"})
        assert "result" in result
        
        # Invalid input should raise error
        with pytest.raises(Exception):
            tool.call({"invalid_field": "value"})


class TestResponseParser:
    """Test response parser functionality."""
    
    def test_parse_tool_calls(self):
        """Test parsing tool calls from response."""
        response = '''
        I need to calculate something.
        <TOOL>{"tool": "calculator", "input": {"expression": "2 + 2"}}</TOOL>
        Let me also search for information.
        <TOOL>{"tool": "web_search", "input": {"query": "test", "max_results": 5}}</TOOL>
        '''
        
        tool_calls = ResponseParser.parse_tool_calls(response)
        assert len(tool_calls) == 2
        assert tool_calls[0]["tool"] == "calculator"
        assert tool_calls[1]["tool"] == "web_search"
    
    def test_parse_results(self):
        """Test parsing results from response."""
        response = '''
        Here are the results:
        <RESULT>{"answer": 4, "explanation": "2 + 2 = 4"}</RESULT>
        And another result:
        <RESULT>{"data": [1, 2, 3]}</RESULT>
        '''
        
        results = ResponseParser.parse_results(response)
        assert len(results) == 2
        assert results[0]["answer"] == 4
        assert results[1]["data"] == [1, 2, 3]
    
    def test_extract_all(self):
        """Test extracting both tool calls and results."""
        response = '''
        <TOOL>{"tool": "test", "input": {"param": "value"}}</TOOL>
        <RESULT>{"output": "result"}</RESULT>
        '''
        
        tool_calls, results = ResponseParser.extract_all(response)
        assert len(tool_calls) == 1
        assert len(results) == 1
        assert tool_calls[0]["tool"] == "test"
        assert results[0]["output"] == "result"
    
    def test_parse_empty_response(self):
        """Test parsing response with no tags."""
        response = "This is just a regular response with no special tags."
        
        tool_calls = ResponseParser.parse_tool_calls(response)
        results = ResponseParser.parse_results(response)
        
        assert len(tool_calls) == 0
        assert len(results) == 0
    
    def test_parse_malformed_json(self):
        """Test parsing response with malformed JSON."""
        response = '<TOOL>{"tool": "test", "invalid": json}</TOOL>'
        
        tool_calls = ResponseParser.parse_tool_calls(response)
        assert len(tool_calls) == 0  # Should skip malformed JSON


class TestAgent:
    """Test agent functionality."""
    
    def test_agent_creation(self, mock_llm_api):
        """Test creating an agent."""
        agent = Agent(
            system_prompt="Test prompt",
            task_description="Test task",
            llm_api=mock_llm_api,
            tools=[CalculatorTool()]
        )
        assert agent.system_prompt == "Test prompt"
        assert agent.task_description == "Test task"
        assert len(agent.tools) == 1
        assert not agent.is_complete
    
    def test_agent_tool_registration(self, mock_llm_api):
        """Test registering tools with agent."""
        agent = Agent(
            system_prompt="Test",
            task_description="Test",
            llm_api=mock_llm_api
        )
        
        # Register tools
        tools = [CalculatorTool(), WebSearchTool(alias="search")]
        agent.register_tools(tools)
        
        assert len(agent.tools) == 2
        assert any(tool.alias == "calculator" for tool in agent.tools.values())
        assert any(tool.alias == "search" for tool in agent.tools.values())
    
    def test_agent_duplicate_alias_error(self, mock_llm_api):
        """Test that duplicate aliases raise an error."""
        agent = Agent(
            system_prompt="Test",
            task_description="Test", 
            llm_api=mock_llm_api
        )
        
        # Try to register tools with duplicate aliases
        tools = [
            CalculatorTool(alias="calc"),
            CalculatorTool(alias="calc")  # Duplicate alias
        ]
        
        with pytest.raises(ValueError, match="Duplicate tool aliases"):
            agent.register_tools(tools)
    
    def test_agent_runtime_configuration(self, mock_llm_api):
        """Test runtime agent configuration."""
        agent = Agent(
            system_prompt="Original prompt {{tools_documentation}}",
            task_description="Original task",
            llm_api=mock_llm_api
        )
        
        # Modify configuration
        agent.set_system_prompt("New prompt {{tools_documentation}}")
        agent.set_task_description("New task")
        
        assert agent.system_prompt == "New prompt {{tools_documentation}}"
        assert agent.task_description == "New task"
        
        # Test that cached prompt is invalidated
        assert agent._rendered_system_prompt is None
    
    def test_agent_conversation_reset(self, mock_llm_api):
        """Test resetting agent conversation."""
        agent = Agent(
            system_prompt="Test {{tools_documentation}}",
            task_description="Test",
            llm_api=mock_llm_api
        )
        
        # Initialize conversation
        agent._initialize_conversation()
        initial_count = len(agent.conversation)
        
        # Add some conversation history
        agent.conversation.append(Message(role="user", content="Test message"))
        assert len(agent.conversation) == initial_count + 1
        
        # Reset conversation
        agent.reset_conversation()
        assert len(agent.conversation) >= 1  # Should have system message(s)
        assert agent.conversation[0].role == "system"
    
    def test_agent_tool_execution(self, mock_llm_api):
        """Test agent tool execution."""
        agent = Agent(
            system_prompt="Test {{tools_documentation}}",
            task_description="Test", 
            llm_api=mock_llm_api,
            tools=[MockTestTool()]
        )
        
        # Execute single tool using current API
        result = agent._execute_single_tool("test_tool", {"message": "test"})
        
        assert result["response"] == "Test response: test"
    
    def test_agent_parallel_tool_execution(self, mock_llm_api):
        """Test parallel tool execution."""
        agent = Agent(
            system_prompt="Test {{tools_documentation}}",
            task_description="Test",
            llm_api=mock_llm_api,
            tools=[MockTestTool(alias="tool1"), MockTestTool(alias="tool2")]
        )
        
        # Create mock LLM response with multiple tool calls
        mock_response = LLMResponse(
            role="assistant",
            content='<TOOL>{"tool": "tool1", "input": {"message": "first"}}</TOOL><TOOL>{"tool": "tool2", "input": {"message": "second"}}</TOOL>',
            token_usage={"total_tokens": 100}
        )
        
        # Execute tools using the current parallel execution method
        agent._execute_tools(mock_response)
        
        # Check that tools were executed (conversation should contain results)
        tool_results = [msg for msg in agent.conversation if "Tool" in msg.content and "result" in msg.content]
        assert len(tool_results) == 2


class TestDynamicToolManagement:
    """Test dynamic tool management features."""
    
    def test_tool_documentation_generation(self, mock_llm_api):
        """Test comprehensive tool documentation generation."""
        agent = Agent(
            system_prompt="Test {{tools_documentation}}",
            task_description="Test",
            llm_api=mock_llm_api,
            tools=[CalculatorTool(), MockTestTool(alias="test")]
        )
        
        # Test documentation generation
        docs = agent._generate_tools_documentation()
        assert "Available Tools" in docs
        assert "calculator" in docs
        assert "test" in docs
        assert "Input Schema" in docs
        assert "Usage" in docs
    
    def test_system_prompt_rendering_with_tools(self, mock_llm_api):
        """Test system prompt rendering includes tool documentation."""
        agent = Agent(
            system_prompt="You are a test agent. {{tools_documentation}}",
            task_description="Test task",  
            llm_api=mock_llm_api,
            tools=[CalculatorTool()]
        )
        
        rendered = agent._render_system_prompt()
        assert "You are a test agent" in rendered
        assert "Available Tools" in rendered
        assert "calculator" in rendered
        assert '"tool": "calculator"' in rendered
    
    def test_dynamic_tool_registration(self, mock_llm_api):
        """Test adding tools after agent creation."""
        agent = Agent(
            system_prompt="Test {{tools_documentation}}",
            task_description="Test",
            llm_api=mock_llm_api
        )
        
        # Start with no tools
        assert len(agent.tools) == 0
        
        # Add tools dynamically
        agent.register_tools([CalculatorTool(), MockTestTool(alias="test")])
        assert len(agent.tools) == 2
        assert "calculator" in agent.tools
        assert "test" in agent.tools
        
        # System prompt should be invalidated
        assert agent._rendered_system_prompt is None
    
    def test_dynamic_tool_removal(self, mock_llm_api):
        """Test removing tools after agent creation."""
        agent = Agent(
            system_prompt="Test {{tools_documentation}}",
            task_description="Test",
            llm_api=mock_llm_api,
            tools=[CalculatorTool(), MockTestTool(alias="test")]
        )
        
        assert len(agent.tools) == 2
        
        # Remove a tool
        agent.unregister_tool("calculator")
        assert len(agent.tools) == 1
        assert "calculator" not in agent.tools
        assert "test" in agent.tools
        
        # System prompt should be invalidated
        assert agent._rendered_system_prompt is None
    
    def test_tool_introduction_during_conversation(self, mock_llm_api):
        """Test tool introduction messages during active conversation."""
        agent = Agent(
            system_prompt="Test {{tools_documentation}}",
            task_description="Test",
            llm_api=mock_llm_api
        )
        
        # Start conversation
        agent._initialize_conversation()
        initial_count = len(agent.conversation)
        
        # Add tool during conversation
        agent.register_tools([CalculatorTool()])
        
        # Should have introduction message
        assert len(agent.conversation) > initial_count
        intro_msgs = [msg for msg in agent.conversation if "NEW TOOL AVAILABLE" in msg.content]
        assert len(intro_msgs) == 1
        assert "calculator" in intro_msgs[0].content
    
    def test_tool_removal_during_conversation(self, mock_llm_api):
        """Test tool removal messages during active conversation."""
        agent = Agent(
            system_prompt="Test {{tools_documentation}}",
            task_description="Test",
            llm_api=mock_llm_api,
            tools=[CalculatorTool()]
        )
        
        # Start conversation
        agent._initialize_conversation()
        initial_count = len(agent.conversation)
        
        # Remove tool during conversation
        agent.unregister_tool("calculator")
        
        # Should have removal message
        assert len(agent.conversation) > initial_count
        removal_msgs = [msg for msg in agent.conversation if "TOOL REMOVED" in msg.content]
        assert len(removal_msgs) == 1
        assert "calculator" in removal_msgs[0].content
    
    def test_tool_schema_extraction(self, mock_llm_api):
        """Test tool schema extraction methods."""
        tool = CalculatorTool()
        
        # Test schema extraction
        input_schema = tool.get_input_schema()
        output_schema = tool.get_output_schema()
        example_input = tool.get_example_input()
        
        assert "properties" in input_schema
        assert "expression" in input_schema["properties"]
        assert "properties" in output_schema
        assert "result" in output_schema["properties"]
        assert "expression" in example_input
        assert isinstance(example_input["expression"], str)
    
    def test_prompt_caching(self, mock_llm_api):
        """Test system prompt caching behavior."""
        agent = Agent(
            system_prompt="Test {{tools_documentation}}",
            task_description="Test",
            llm_api=mock_llm_api,
            tools=[CalculatorTool()]
        )
        
        # First render should cache the prompt
        prompt1 = agent._render_system_prompt()
        assert agent._rendered_system_prompt is not None
        
        # Second render should return cached version
        prompt2 = agent._render_system_prompt()
        assert prompt1 == prompt2
        
        # Adding tool should invalidate cache
        agent.register_tools([MockTestTool(alias="test")])
        assert agent._rendered_system_prompt is None
        
        # New render should include new tool
        prompt3 = agent._render_system_prompt()
        assert "test" in prompt3
        assert prompt3 != prompt1


class TestSpecializedAgents:
    """Test specialized agent implementations."""
    
    def test_math_solver_agent_creation(self, mock_llm_api):
        """Test creating a math solver agent."""
        agent = MathSolverAgent(llm_api=mock_llm_api)
        assert "mathematical" in agent.system_prompt.lower()
        assert len(agent.tools) > 0
        assert any(tool.name == "calculator" for tool in agent.tools.values())
    
    def test_research_agent_creation(self, mock_llm_api):
        """Test creating a research agent."""
        agent = ResearchAgent(llm_api=mock_llm_api)
        assert "research" in agent.system_prompt.lower()
        assert len(agent.tools) > 0
        assert any(tool.name == "web_search" for tool in agent.tools.values())
    
    def test_math_solver_with_custom_tools(self, mock_llm_api):
        """Test math solver with custom tools."""
        custom_calc = CalculatorTool(
            config=CalculatorConfig(precision=15),
            alias="precise_calc"
        )
        
        agent = MathSolverAgent(
            llm_api=mock_llm_api,
            tools=[custom_calc]
        )
        
        assert len(agent.tools) == 1
        assert "precise_calc" in agent.tools
        precise_calc = agent.tools["precise_calc"]
        assert precise_calc.config.precision == 15
    
    def test_research_agent_with_multiple_search_tools(self, mock_llm_api):
        """Test research agent with multiple search configurations."""
        tools = [
            WebSearchTool(config=WebSearchConfig(region="academic"), alias="academic"),
            WebSearchTool(config=WebSearchConfig(region="news"), alias="news")
        ]
        
        agent = ResearchAgent(llm_api=mock_llm_api, tools=tools)
        
        assert len(agent.tools) == 2
        assert any(tool.alias == "academic" for tool in agent.tools.values())
        assert any(tool.alias == "news" for tool in agent.tools.values())


class TestRegistry:
    """Test component registry functionality."""
    
    def test_registry_singleton(self):
        """Test that registry is a singleton."""
        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2
    
    def test_registry_tool_discovery(self):
        """Test discovering registered tools."""
        registry = get_registry()
        tools = registry.get_all_tools()
        
        # Should find built-in tools
        tool_names = [info.name for info in tools]
        assert "CalculatorTool" in tool_names
        assert "WebSearchTool" in tool_names
    
    def test_registry_agent_discovery(self):
        """Test discovering registered agents."""
        registry = get_registry()
        agents = registry.get_all_agents()
        
        # Should find specialized agents
        agent_names = [info.name for info in agents]
        assert "MathSolverAgent" in agent_names
        assert "ResearchAgent" in agent_names
    
    def test_registry_get_tool_info(self):
        """Test getting specific tool information."""
        registry = get_registry()
        tool_info = registry.get_tool("CalculatorTool")
        
        assert tool_info is not None
        assert tool_info.name == "CalculatorTool"
        assert "config" in tool_info.associated_classes
        assert "input" in tool_info.associated_classes
        assert "output" in tool_info.associated_classes


class TestMockLLMApi:
    """Test mock LLM API functionality."""
    
    def test_mock_llm_creation(self):
        """Test creating mock LLM API."""
        api = MockLLMApi({
            "response_delay": 0.1,
            "mock_responses": ["Test response"]
        })
        assert api.response_delay == 0.1
        assert len(api.mock_responses) == 1
    
    def test_mock_llm_chat_completion(self):
        """Test mock LLM chat completion."""
        api = MockLLMApi({
            "response_delay": 0.01,
            "mock_responses": ["Mock response"]
        })
        
        messages = [Message(role="user", content="Test message")]
        response = api.chat_completion(messages)
        
        assert isinstance(response, LLMResponse)
        assert response.role == "assistant"
        assert response.content == "Mock response"
        assert "total_tokens" in response.token_usage
    
    def test_mock_llm_structured_completion(self):
        """Test mock LLM structured completion."""
        api = MockLLMApi({"response_delay": 0.01})
        
        schema = {
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
                "confidence": {"type": "number"}
            }
        }
        
        messages = [Message(role="user", content="Test")]
        result = api.structured_completion(messages, schema)
        
        assert isinstance(result, dict)
        assert "answer" in result or "status" in result
    
    def test_mock_llm_response_cycling(self):
        """Test that mock LLM cycles through responses."""
        api = MockLLMApi({
            "response_delay": 0.01,
            "mock_responses": ["Response 1", "Response 2"]
        })
        
        messages = [Message(role="user", content="Test")]
        
        response1 = api.chat_completion(messages)
        assert response1.content == "Response 1"
        
        response2 = api.chat_completion(messages)
        assert response2.content == "Response 2"
        
        # Should generate default after exhausting responses
        response3 = api.chat_completion(messages)
        assert response3.content != "Response 1"
        assert response3.content != "Response 2"


class TestIntegration:
    """Integration tests combining multiple components."""
    
    def test_full_agent_workflow(self, mock_llm_api):
        """Test complete agent workflow with mocked LLM."""
        # Create agent with specific mock responses
        llm_api = MockLLMApi({
            "response_delay": 0.01,
            "mock_responses": [
                "I need to calculate this.",
                '<TOOL>{"tool": "calculator", "input": {"expression": "10 + 5"}}</TOOL>',
                "The result is 15.",
                '<RESULT>{"answer": 15}</RESULT>',
                "TASK_COMPLETE"
            ]
        })
        
        agent = Agent(
            system_prompt="You are a helpful calculator.",
            task_description="Calculate 10 + 5",
            llm_api=llm_api,
            tools=[CalculatorTool()]
        )
        
        # Run the agent
        agent.react_loop()
        
        # Verify completion
        assert agent.is_complete
        assert len(agent.results) > 0
        
        # Check that calculator was used
        conversation_text = " ".join([msg.content for msg in agent.conversation])
        assert "calculator" in conversation_text.lower()
    
    def test_agent_with_multiple_tools(self, mock_llm_api):
        """Test agent using multiple different tools.""" 
        llm_api = MockLLMApi({
            "response_delay": 0.01,
            "mock_responses": [
                "I'll use both tools.",
                '<TOOL>{"tool": "calculator", "input": {"expression": "2 * 3"}}</TOOL>',
                '<TOOL>{"tool": "web_search", "input": {"query": "test", "max_results": 2}}</TOOL>',
                "Got results from both tools.",
                '<RESULT>{"calculation": 6, "search_count": 2}</RESULT>',
                "TASK_COMPLETE"
            ]
        })
        
        agent = Agent(
            system_prompt="Use multiple tools.",
            task_description="Calculate and search.",
            llm_api=llm_api,
            tools=[CalculatorTool(), WebSearchTool()]
        )
        
        agent.react_loop()
        
        assert agent.is_complete
        assert len(agent.results) > 0
    
    def test_specialized_agent_workflow(self):
        """Test specialized agent with appropriate tools."""
        llm_api = MockLLMApi({
            "response_delay": 0.01,
            "mock_responses": [
                "I'll solve this mathematical problem step by step.",
                '<TOOL>{"tool": "calculator", "input": {"expression": "sqrt(16)"}}</TOOL>',
                "The square root of 16 is 4.",
                '<RESULT>{"problem": "sqrt(16)", "solution": "4", "steps": ["Calculate square root", "Result is 4"]}</RESULT>',
                "TASK_COMPLETE"
            ]
        })
        
        agent = MathSolverAgent(llm_api=llm_api)
        agent.set_task_description("Find the square root of 16")
        agent.react_loop()
        
        assert agent.is_complete
        assert len(agent.results) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])