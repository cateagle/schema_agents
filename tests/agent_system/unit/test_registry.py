"""
Tests for the component registry system.
"""

import pytest
from unittest.mock import Mock

from agent_system.core import (
    get_registry, ComponentRegistry, register_tool, register_agent, register_llm_api,
    Tool, Agent, LLMApi, ToolConfig, ToolInputBase, ToolOutputBase
)
from agent_system.tools import CalculatorTool, WebSearchTool
from agent_system.agents import MathSolverAgent, ResearchAgent
from agent_system.llm_apis import MockLLMApi


class TestComponentRegistry:
    """Test component registry functionality."""
    
    def test_registry_singleton(self):
        """Test that registry follows singleton pattern."""
        registry1 = get_registry()
        registry2 = get_registry()
        
        assert registry1 is registry2
        assert isinstance(registry1, ComponentRegistry)
    
    def test_registry_tool_discovery(self):
        """Test registry discovers built-in tools."""
        registry = get_registry()
        tools = registry.get_all_tools()
        
        # Should find built-in tools
        tool_names = [info.name for info in tools]
        assert "CalculatorTool" in tool_names
        assert "WebSearchTool" in tool_names
        
        # Check tool info structure
        calc_info = registry.get_tool("CalculatorTool")
        assert calc_info is not None
        assert calc_info.name == "CalculatorTool"
        assert "config" in calc_info.associated_classes
        assert "input" in calc_info.associated_classes
        assert "output" in calc_info.associated_classes
    
    def test_registry_agent_discovery(self):
        """Test registry discovers built-in agents."""
        registry = get_registry()
        agents = registry.get_all_agents()
        
        # Should find specialized agents
        agent_names = [info.name for info in agents]
        assert "MathSolverAgent" in agent_names
        assert "ResearchAgent" in agent_names
        
        # Check agent info structure
        math_info = registry.get_agent("MathSolverAgent")
        assert math_info is not None
        assert math_info.name == "MathSolverAgent"
        assert math_info.description is not None
    
    def test_registry_llm_api_discovery(self):
        """Test registry discovers LLM APIs."""
        registry = get_registry()
        llm_apis = registry.get_all_llm_apis()
        
        # Should find mock LLM API
        api_names = [info.name for info in llm_apis]
        assert "MockLLMApi" in api_names
        
        # Check LLM API info structure
        mock_info = registry.get_llm_api("MockLLMApi")
        assert mock_info is not None
        assert mock_info.name == "MockLLMApi"
        assert mock_info.description is not None
    
    def test_registry_naming_convention_validation(self):
        """Test registry validates naming conventions."""
        registry = get_registry()
        errors = registry.validate_naming_conventions()
        
        # Built-in components should follow naming conventions
        # This test ensures the validation method works, 
        # specific errors depend on current implementation
        assert isinstance(errors, list)
        
        # If there are errors, they should be descriptive
        for error in errors:
            assert isinstance(error, str)
            assert len(error) > 0


class TestToolRegistration:
    """Test tool registration functionality."""
    
    def test_register_tool_decorator(self):
        """Test @register_tool decorator functionality."""
        
        class TestConfig(ToolConfig):
            param: str = "default"
        
        class TestInput(ToolInputBase):
            data: str
        
        class TestOutput(ToolOutputBase):
            result: str
        
        @register_tool(
            config_class=TestConfig,
            input_class=TestInput,
            output_class=TestOutput,
            description="Test tool for registration"
        )
        class TestRegistrationTool(Tool):
            def __init__(self, config=None, alias=None):
                super().__init__(
                    name="test_registration",
                    short_description="Test tool",
                    long_description="Test tool for registration testing",
                    config=config or TestConfig(),
                    alias=alias
                )
            
            @classmethod
            def _get_config_class(cls):
                return TestConfig
            
            @classmethod
            def _get_input_class(cls):
                return TestInput
            
            @classmethod
            def _get_output_class(cls):
                return TestOutput
            
            def _execute(self, input_data, identity=None):
                return TestOutput(result=f"Processed: {input_data.data}")
        
        # Check that tool was registered
        registry = get_registry()
        tool_info = registry.get_tool("TestRegistrationTool")
        
        assert tool_info is not None
        assert tool_info.name == "TestRegistrationTool"
        assert tool_info.description == "Test tool for registration"
        assert tool_info.associated_classes["config"] == TestConfig
        assert tool_info.associated_classes["input"] == TestInput
        assert tool_info.associated_classes["output"] == TestOutput
    
    def test_tool_registration_without_decorator(self):
        """Test that unregistered tools are not in registry."""
        
        class UnregisteredTool(Tool):
            def __init__(self):
                super().__init__(
                    name="unregistered",
                    short_description="Not registered",
                    long_description="Tool not registered with decorator"
                )
            
            def _execute(self, input_data, identity=None):
                return {"result": "unregistered"}
        
        registry = get_registry()
        tool_info = registry.get_tool("UnregisteredTool")
        
        # Should not be found since it wasn't registered
        assert tool_info is None


class TestAgentRegistration:
    """Test agent registration functionality."""
    
    def test_register_agent_decorator(self):
        """Test @register_agent decorator functionality."""
        
        @register_agent(description="Test agent for registration testing")
        class TestRegistrationAgent(Agent):
            def __init__(self, llm_api, **kwargs):
                super().__init__(
                    system_prompt="Test agent prompt",
                    task_description="Test task",
                    llm_api=llm_api,
                    **kwargs
                )
        
        # Check that agent was registered
        registry = get_registry()
        agent_info = registry.get_agent("TestRegistrationAgent")
        
        assert agent_info is not None
        assert agent_info.name == "TestRegistrationAgent"
        assert agent_info.description == "Test agent for registration testing"
    
    def test_agent_registration_without_decorator(self):
        """Test that unregistered agents are not in registry."""
        
        class UnregisteredAgent(Agent):
            def __init__(self, llm_api):
                super().__init__(
                    system_prompt="Unregistered agent",
                    task_description="Test",
                    llm_api=llm_api
                )
        
        registry = get_registry()
        agent_info = registry.get_agent("UnregisteredAgent")
        
        # Should not be found since it wasn't registered
        assert agent_info is None


class TestLLMApiRegistration:
    """Test LLM API registration functionality."""
    
    def test_register_llm_api_decorator(self):
        """Test @register_llm_api decorator functionality."""
        
        @register_llm_api(description="Test LLM API for registration testing")
        class TestRegistrationLLMApi(LLMApi):
            def __init__(self, config):
                super().__init__(config)
            
            def chat_completion(self, messages):
                from agent_system.core import LLMResponse
                return LLMResponse(
                    role="assistant",
                    content="Test response",
                    token_usage={"total_tokens": 10},
                    finish_reason="stop"
                )
            
            def chat_completion_stream(self, messages):
                response = self.chat_completion(messages)
                yield response
            
            def structured_completion(self, messages, schema):
                return {"status": "test"}
        
        # Check that LLM API was registered
        registry = get_registry()
        api_info = registry.get_llm_api("TestRegistrationLLMApi")
        
        assert api_info is not None
        assert api_info.name == "TestRegistrationLLMApi"
        assert api_info.description == "Test LLM API for registration testing"
    
    def test_llm_api_registration_without_decorator(self):
        """Test that unregistered LLM APIs are not in registry."""
        
        class UnregisteredLLMApi(LLMApi):
            def __init__(self, config):
                super().__init__(config)
            
            def chat_completion(self, messages):
                pass
            
            def chat_completion_stream(self, messages):
                pass
            
            def structured_completion(self, messages, schema):
                pass
        
        registry = get_registry()
        api_info = registry.get_llm_api("UnregisteredLLMApi")
        
        # Should not be found since it wasn't registered
        assert api_info is None


class TestRegistryQueries:
    """Test registry query functionality."""
    
    def test_get_nonexistent_components(self):
        """Test querying for components that don't exist."""
        registry = get_registry()
        
        # Should return None for non-existent components
        assert registry.get_tool("NonExistentTool") is None
        assert registry.get_agent("NonExistentAgent") is None
        assert registry.get_llm_api("NonExistentLLMApi") is None
    
    def test_get_all_components_returns_lists(self):
        """Test that get_all_* methods return proper lists."""
        registry = get_registry()
        
        tools = registry.get_all_tools()
        agents = registry.get_all_agents()
        llm_apis = registry.get_all_llm_apis()
        
        assert isinstance(tools, list)
        assert isinstance(agents, list)
        assert isinstance(llm_apis, list)
        
        # Lists should not be empty (built-ins should be registered)
        assert len(tools) > 0
        assert len(agents) > 0
        assert len(llm_apis) > 0
    
    def test_component_info_structure(self):
        """Test that component info objects have expected structure."""
        registry = get_registry()
        
        # Test tool info structure
        tool_info = registry.get_tool("CalculatorTool")
        assert hasattr(tool_info, 'name')
        assert hasattr(tool_info, 'description')
        assert hasattr(tool_info, 'associated_classes')
        assert isinstance(tool_info.associated_classes, dict)
        
        # Test agent info structure
        agent_info = registry.get_agent("MathSolverAgent")
        assert hasattr(agent_info, 'name')
        assert hasattr(agent_info, 'description')
        
        # Test LLM API info structure
        api_info = registry.get_llm_api("MockLLMApi")
        assert hasattr(api_info, 'name')
        assert hasattr(api_info, 'description')


class TestRegistryThreadSafety:
    """Test registry thread safety for read operations."""
    
    def test_concurrent_registry_access(self):
        """Test that multiple threads can safely access registry."""
        import threading
        import time
        
        results = []
        errors = []
        
        def access_registry():
            try:
                registry = get_registry()
                tools = registry.get_all_tools()
                agents = registry.get_all_agents()
                apis = registry.get_all_llm_apis()
                
                # Simulate some processing time
                time.sleep(0.01)
                
                results.append({
                    'tools': len(tools),
                    'agents': len(agents),
                    'apis': len(apis)
                })
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=access_registry)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        
        # All threads should get the same counts
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result


class TestRegistryValidation:
    """Test registry validation functionality."""
    
    def test_naming_convention_validation_format(self):
        """Test the format of naming convention validation."""
        registry = get_registry()
        errors = registry.validate_naming_conventions()
        
        # Should return a list
        assert isinstance(errors, list)
        
        # Each error should be a string
        for error in errors:
            assert isinstance(error, str)
            # Error messages should be informative
            assert len(error) > 10
    
    def test_registry_state_consistency(self):
        """Test that registry maintains consistent state."""
        registry = get_registry()
        
        # Get counts multiple times - should be consistent
        tools1 = registry.get_all_tools()
        tools2 = registry.get_all_tools()
        
        assert len(tools1) == len(tools2)
        
        # Component info should be identical
        for tool1, tool2 in zip(tools1, tools2):
            assert tool1.name == tool2.name
            assert tool1.description == tool2.description


if __name__ == "__main__":
    pytest.main([__file__, "-v"])