"""
Tests for specialized agents in the agent system.
"""

import pytest
from unittest.mock import Mock, patch

from agent_system.agents import MathSolverAgent, ResearchAgent
from agent_system.llm_apis import MockLLMApi
from agent_system.tools import CalculatorTool, CalculatorConfig, WebSearchTool, WebSearchConfig
from agent_system.core import Agent, Message


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
    
    def test_creation_with_defaults(self, mock_llm_api):
        """Test creating math solver with default configuration."""
        agent = MathSolverAgent(llm_api=mock_llm_api)
        
        # Check system prompt contains math-related content
        assert "mathematical" in agent.system_prompt.lower() or "math" in agent.system_prompt.lower()
        
        # Should have calculator tool by default
        assert len(agent.tools) >= 1
        assert "calculator" in agent.tools
        
        # Check default precision
        calc_tool = agent.tools["calculator"]
        assert calc_tool.config.precision == 10
    
    def test_creation_with_custom_prompt(self, mock_llm_api):
        """Test creating math solver with custom system prompt."""
        custom_prompt = "You are a specialized algebra tutor."
        agent = MathSolverAgent(
            llm_api=mock_llm_api,
            system_prompt=custom_prompt
        )
        
        assert agent.system_prompt == custom_prompt
    
    def test_creation_with_custom_tools(self, mock_llm_api):
        """Test creating math solver with custom tools."""
        custom_calc = CalculatorTool(
            config=CalculatorConfig(precision=15, allow_complex=True),
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
        assert precise_calc.config.allow_complex == True
    
    def test_creation_with_custom_schema(self, mock_llm_api):
        """Test creating math solver with custom result schema."""
        custom_schema = {
            "type": "object",
            "properties": {
                "equation": {"type": "string"},
                "answer": {"type": "number"},
                "method": {"type": "string"}
            }
        }
        
        agent = MathSolverAgent(
            llm_api=mock_llm_api,
            result_schema=custom_schema
        )
        
        assert agent.result_schema == custom_schema
    
    def test_solve_problem_workflow(self, mock_llm_api):
        """Test complete problem-solving workflow."""
        agent = MathSolverAgent(llm_api=mock_llm_api)
        agent.set_task_description("Calculate the square root of 16")
        
        # Run the agent
        agent.react_loop()
        
        # Verify completion
        assert agent.is_complete
        assert len(agent.results) > 0
        
        # Check conversation mentions calculator
        conversation_text = " ".join([msg.content for msg in agent.conversation])
        assert "calculator" in conversation_text.lower()
    
    def test_runtime_reconfiguration(self, mock_llm_api):
        """Test runtime reconfiguration of math solver."""
        agent = MathSolverAgent(llm_api=mock_llm_api)
        
        # Add another calculator with different precision
        high_precision_calc = CalculatorTool(
            config=CalculatorConfig(precision=20),
            alias="high_precision"
        )
        agent.register_tools([high_precision_calc])
        
        # Should now have multiple calculator tools
        calc_tools = [tool for tool in agent.tools.values() if tool.name == "calculator"]
        assert len(calc_tools) >= 2
        
        # Check aliases are different
        aliases = [tool.alias for tool in calc_tools]
        assert len(aliases) == len(set(aliases))  # All unique
    
    def test_multiple_calculation_steps(self, mock_llm_api):
        """Test agent handling multiple calculation steps."""
        multi_step_api = MockLLMApi({
            "response_delay": 0.01,
            "mock_responses": [
                "I need to solve this in multiple steps.",
                '<TOOL>{"tool": "calculator", "input": {"expression": "3 * 4"}}</TOOL>',
                "First step gives us 12, now I'll calculate the next part.",
                '<TOOL>{"tool": "calculator", "input": {"expression": "12 + 8"}}</TOOL>',
                "The final answer is 20.",
                '<RESULT>{"problem": "3 * 4 + 8", "solution": "20", "steps": ["Calculate 3 * 4 = 12", "Add 12 + 8 = 20"]}</RESULT>',
                "TASK_COMPLETE"
            ]
        })
        
        agent = MathSolverAgent(llm_api=multi_step_api)
        agent.set_task_description("Calculate 3 * 4 + 8")
        agent.react_loop()
        
        assert agent.is_complete
        assert len(agent.results) > 0
        
        # Should have used calculator multiple times
        conversation_text = " ".join([msg.content for msg in agent.conversation])
        calculator_mentions = conversation_text.lower().count("calculator")
        assert calculator_mentions >= 2


class TestResearchAgent:
    """Test research agent functionality."""
    
    @pytest.fixture
    def mock_llm_api(self):
        """Create mock LLM API for research agent testing."""
        return MockLLMApi({
            "response_delay": 0.01,
            "mock_responses": [
                "I'll research this topic for you.",
                '<TOOL>{"tool": "web_search", "input": {"query": "artificial intelligence trends", "max_results": 5}}</TOOL>',
                "I found several relevant sources about AI trends.",
                '<RESULT>{"title": "AI Trend: Neural Networks", "description": "Latest developments in neural network architectures", "url": "http://example.com/1"}</RESULT>',
                '<RESULT>{"title": "AI Trend: Machine Learning", "description": "Current applications of ML in industry", "url": "http://example.com/2"}</RESULT>',
                "TASK_COMPLETE"
            ]
        })
    
    def test_creation_with_defaults(self, mock_llm_api):
        """Test creating research agent with default configuration."""
        agent = ResearchAgent(llm_api=mock_llm_api)
        
        # Check system prompt contains research-related content
        assert "research" in agent.system_prompt.lower()
        
        # Should have web search tool by default
        assert len(agent.tools) >= 1
        search_tools = [tool for tool in agent.tools.values() if tool.name == "web_search"]
        assert len(search_tools) >= 1
        
        # Check default configuration
        search_tool = search_tools[0]
        assert search_tool.config.search_engine == "mock"
    
    def test_creation_with_custom_search_tools(self, mock_llm_api):
        """Test creating research agent with custom search tools."""
        academic_search = WebSearchTool(
            config=WebSearchConfig(region="academic", search_engine="mock"),
            alias="academic"
        )
        news_search = WebSearchTool(
            config=WebSearchConfig(region="news", search_engine="mock"),
            alias="news"
        )
        
        agent = ResearchAgent(
            llm_api=mock_llm_api,
            tools=[academic_search, news_search]
        )
        
        assert len(agent.tools) == 2
        aliases = [tool.alias for tool in agent.tools.values()]
        assert "academic" in aliases
        assert "news" in aliases
    
    def test_research_topic_workflow(self, mock_llm_api):
        """Test complete research workflow."""
        agent = ResearchAgent(llm_api=mock_llm_api)
        agent.set_task_description("Research machine learning applications in healthcare")
        
        # Run the agent
        agent.react_loop()
        
        # Verify completion
        assert agent.is_complete
        assert len(agent.results) > 0
        
        # Check conversation mentions web search
        conversation_text = " ".join([msg.content for msg in agent.conversation])
        assert "web_search" in conversation_text.lower() or "search" in conversation_text.lower()
    
    def test_multiple_search_strategies(self, mock_llm_api):
        """Test research agent using multiple search strategies."""
        multi_search_api = MockLLMApi({
            "response_delay": 0.01,
            "mock_responses": [
                "I'll search multiple sources for comprehensive research.",
                '<TOOL>{"tool": "academic", "input": {"query": "machine learning research", "max_results": 3}}</TOOL>',
                '<TOOL>{"tool": "news", "input": {"query": "machine learning news", "max_results": 3}}</TOOL>',
                "I've gathered information from both academic and news sources.",
                '<RESULT>{"title": "ML Research Paper", "description": "Latest algorithms in machine learning research", "url": "http://academic.com/ml"}</RESULT>',
                '<RESULT>{"title": "ML News Article", "description": "Industry applications of machine learning", "url": "http://news.com/ml"}</RESULT>',
                "TASK_COMPLETE"
            ]
        })
        
        # Create agent with multiple search tools
        academic_tool = WebSearchTool(
            config=WebSearchConfig(region="academic"),
            alias="academic"
        )
        news_tool = WebSearchTool(
            config=WebSearchConfig(region="news"),
            alias="news"
        )
        
        agent = ResearchAgent(
            llm_api=multi_search_api,
            tools=[academic_tool, news_tool]
        )
        agent.set_task_description("Research machine learning from multiple perspectives")
        agent.react_loop()
        
        assert agent.is_complete
        assert len(agent.results) > 0
        
        # Should have used both search tools
        conversation_text = " ".join([msg.content for msg in agent.conversation])
        assert "academic" in conversation_text
        assert "news" in conversation_text
    
    def test_research_with_specific_questions(self, mock_llm_api):
        """Test research agent with specific research questions."""
        specific_api = MockLLMApi({
            "response_delay": 0.01,
            "mock_responses": [
                "I'll address each specific question in my research.",
                '<TOOL>{"tool": "web_search", "input": {"query": "blockchain scalability solutions", "max_results": 5}}</TOOL>',
                '<TOOL>{"tool": "web_search", "input": {"query": "blockchain energy consumption", "max_results": 5}}</TOOL>',
                "I've researched both scalability and energy aspects.",
                '<RESULT>{"title": "Blockchain Scalability Solutions", "description": "Layer 2 solutions for blockchain scalability", "url": "http://example.com/scalability"}</RESULT>',
                '<RESULT>{"title": "Blockchain Energy Improvements", "description": "Proof of stake improvements for energy efficiency", "url": "http://example.com/energy"}</RESULT>',
                "TASK_COMPLETE"
            ]
        })
        
        agent = ResearchAgent(llm_api=specific_api)
        task = """Research blockchain technology focusing on:
        1. Scalability solutions
        2. Energy consumption issues"""
        agent.set_task_description(task)
        agent.react_loop()
        
        assert agent.is_complete
        assert len(agent.results) > 0
    
    def test_research_agent_runtime_modification(self, mock_llm_api):
        """Test runtime modification of research agent."""
        agent = ResearchAgent(llm_api=mock_llm_api)
        
        # Add specialized search tool
        specialized_search = WebSearchTool(
            config=WebSearchConfig(
                region="technical",
                search_engine="mock"
            ),
            alias="technical"
        )
        agent.register_tools([specialized_search])
        
        # Should now have multiple search tools
        search_tools = [tool for tool in agent.tools.values() if tool.name == "web_search"]
        assert len(search_tools) >= 2
        
        # Change system prompt for specialized research
        agent.set_system_prompt("You are a technical research specialist focusing on deep technical analysis.")
        assert "technical" in agent.system_prompt.lower()


class TestAgentComparison:
    """Test comparing different agent types."""
    
    def test_agent_specialization_differences(self):
        """Test that different agents have appropriate specializations."""
        mock_api = MockLLMApi({"response_delay": 0.01})
        
        math_agent = MathSolverAgent(llm_api=mock_api)
        research_agent = ResearchAgent(llm_api=mock_api)
        
        # Different system prompts
        assert math_agent.system_prompt != research_agent.system_prompt
        assert "math" in math_agent.system_prompt.lower() or "calculation" in math_agent.system_prompt.lower()
        assert "research" in research_agent.system_prompt.lower()
        
        # Different default tools
        math_tools = [tool.name for tool in math_agent.tools.values()]
        research_tools = [tool.name for tool in research_agent.tools.values()]
        
        assert "calculator" in math_tools
        assert "web_search" in research_tools
    
    def test_agents_inherit_from_base(self):
        """Test that specialized agents inherit from base Agent class."""
        mock_api = MockLLMApi({"response_delay": 0.01})
        
        math_agent = MathSolverAgent(llm_api=mock_api)
        research_agent = ResearchAgent(llm_api=mock_api)
        
        # Both should be instances of Agent
        assert isinstance(math_agent, Agent)
        assert isinstance(research_agent, Agent)
        
        # Both should have Agent methods
        assert hasattr(math_agent, 'react_loop')
        assert hasattr(math_agent, 'set_task_description')
        assert hasattr(research_agent, 'react_loop')
        assert hasattr(research_agent, 'set_task_description')
    
    def test_agents_support_runtime_configuration(self):
        """Test that all agents support runtime configuration."""
        mock_api = MockLLMApi({"response_delay": 0.01})
        
        for AgentClass in [MathSolverAgent, ResearchAgent]:
            agent = AgentClass(llm_api=mock_api)
            
            # Test runtime configuration methods exist and work
            original_prompt = agent.system_prompt
            agent.set_system_prompt("Modified prompt")
            assert agent.system_prompt == "Modified prompt"
            assert agent.system_prompt != original_prompt
            
            # Test task modification
            agent.set_task_description("New task")
            assert agent.task_description == "New task"
            
            # Test tool registration
            original_tool_count = len(agent.tools)
            from agent_system.tools import CalculatorTool
            agent.register_tools([CalculatorTool(alias="additional_calc")])
            assert len(agent.tools) == original_tool_count + 1


class TestAgentEdgeCases:
    """Test edge cases and error conditions for agents."""
    
    def test_agent_with_no_tools(self):
        """Test agent behavior with no tools."""
        mock_api = MockLLMApi({
            "response_delay": 0.01,
            "mock_responses": [
                "I don't have any tools available, but I can still provide guidance.",
                '<RESULT>{"response": "General advice without tool usage"}</RESULT>',
                "TASK_COMPLETE"
            ]
        })
        
        # Create math agent with empty tools list
        agent = MathSolverAgent(llm_api=mock_api, tools=[])
        assert len(agent.tools) == 0
        
        agent.set_task_description("Provide general math advice")
        agent.react_loop()
        
        assert agent.is_complete
        # Should still complete even without tools
    
    def test_agent_with_duplicate_tool_aliases(self):
        """Test that agents reject duplicate tool aliases."""
        mock_api = MockLLMApi({"response_delay": 0.01})
        
        # Try to create agent with duplicate aliases
        tool1 = CalculatorTool(alias="calc")
        tool2 = CalculatorTool(alias="calc")  # Same alias
        
        with pytest.raises(ValueError, match="Duplicate tool aliases"):
            MathSolverAgent(llm_api=mock_api, tools=[tool1, tool2])
    
    def test_agent_conversation_history_management(self):
        """Test agent conversation history is managed properly."""
        mock_api = MockLLMApi({
            "response_delay": 0.01,
            "mock_responses": ["Response 1", "Response 2", "TASK_COMPLETE"]
        })
        
        agent = MathSolverAgent(llm_api=mock_api)
        
        # Initial conversation should be empty until initialized
        initial_count = len(agent.conversation)
        assert initial_count == 0
        
        # Initialize conversation
        agent._initialize_conversation()
        assert len(agent.conversation) >= 1
        assert any(msg.role == "system" for msg in agent.conversation)
        
        # After setting task, should have task message
        agent.set_task_description("Test task")
        agent.reset_conversation()  # This should reinitialize with system + task
        
        # Should have system message
        assert any(msg.role == "system" for msg in agent.conversation)
        assert any("Test task" in msg.content for msg in agent.conversation)
    
    def test_agent_max_iterations_safety(self):
        """Test agent has safety mechanism for infinite loops."""
        # Create an API that never says TASK_COMPLETE
        infinite_api = MockLLMApi({
            "response_delay": 0.01,
            "mock_responses": [
                "I'm working on it...",
                "Still working...",
                "Making progress...",
                "Almost there...",
                "Just a bit more..."
            ] * 10  # Repeat to simulate infinite loop
        })
        
        agent = MathSolverAgent(llm_api=infinite_api)
        agent.set_task_description("Simple calculation")
        
        # Run agent - should eventually stop due to max iterations
        agent.react_loop()
        
        # Should not run indefinitely (exact behavior depends on implementation)
        # This test mainly ensures the system doesn't hang
        assert len(agent.conversation) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])