# Creating Custom Agents

This guide shows you how to create custom agents by inheriting from the base `Agent` class and overriding specific step methods in the ReAct loop.

## Base Agent Architecture

The base `Agent` class is now a dataclass with a well-defined ReAct loop that calls specific step methods. You can override these methods to customize agent behavior:

### Key Step Methods You Can Override

1. **`_setup_agent()`** - Called after initialization to register tools and configure the agent
2. **`_initialize_conversation()`** - Sets up the initial conversation with system prompt and task
3. **`_should_continue(iteration)`** - Determines if the agent should continue the loop
4. **`_prepare_conversation()`** - Prepares conversation before each LLM call
5. **`_get_llm_response()`** - Gets response from LLM (override for custom behavior)
6. **`_process_llm_response(response)`** - Processes the LLM response
7. **`_is_task_complete(response)`** - Checks if the task is complete
8. **`_parse_tool_calls(content)`** - Parses tool calls from LLM response
9. **`_execute_tools(response)`** - Executes tools based on LLM response
10. **`_process_tool_result(tool_name, tool_result)`** - Processes individual tool results
11. **`_handle_error(error, iteration)`** - Handles errors during execution
12. **`_finalize_execution()`** - Cleanup after loop completion

## Example 1: Simple Specialized Agent

```python
from dataclasses import dataclass
from typing import Dict, Any, Optional
from agent_system.core.agent import Agent
from agent_system.core.llm_api import LLMApi, LLMResponse
from agent_system.tools import CalculatorTool

@dataclass
class StatisticsAgent(Agent):
    """Agent specialized in statistical calculations."""
    
    def __init__(
        self,
        llm_api: LLMApi,
        timeout: float = 180.0,
        identity: Optional[Dict[str, Any]] = None
    ):
        system_prompt = """
You are a statistics expert. Calculate statistical measures and provide insights.

Available Tools:
{% for tool in tools %}
- {{ tool.name }}: {{ tool.short_description }}
{% endfor %}

Task: {{ task_description }}

Use {"tool": "calculator", "input": {"expression": "..."}} for calculations.
When complete, say "STATS_COMPLETE".
"""
        
        super().__init__(
            system_prompt=system_prompt,
            task_description="",
            llm_api=llm_api,
            timeout=timeout,
            identity=identity
        )
    
    def _setup_agent(self) -> None:
        """Setup with calculator tool only."""
        self.register_tools([CalculatorTool()])
    
    def _is_task_complete(self, response: LLMResponse) -> bool:
        """Custom completion check."""
        return (super()._is_task_complete(response) or
                "STATS_COMPLETE" in response.content)
    
    def _process_tool_result(self, tool_name: str, tool_result: Dict[str, Any]) -> None:
        """Store statistical calculations as results."""
        if tool_name == "calculator":
            result = {
                "calculation": tool_result["expression"],
                "value": tool_result["result"],
                "type": "statistical_measure"
            }
            self.add_result(result)
```

## Example 2: Multi-Phase Agent

```python
@dataclass
class ResearchAndAnalysisAgent(Agent):
    """Agent that conducts research then performs analysis."""
    
    def __init__(self, llm_api: LLMApi, **kwargs):
        super().__init__(
            system_prompt="You are a research and analysis agent...",
            task_description="",
            llm_api=llm_api,
            **kwargs
        )
        self.current_phase = "research"
        self.research_complete = False
    
    def _setup_agent(self) -> None:
        self.register_tools([WebSearchTool(), CalculatorTool()])
    
    def _should_continue(self, iteration: int) -> bool:
        """Continue until both phases are complete."""
        if self.current_phase == "research" and self.research_complete:
            self.current_phase = "analysis"
            # Add phase transition message
            phase_msg = Message(role="user", content="Research phase complete. Begin analysis phase.")
            self.conversation.append(phase_msg)
        
        return super()._should_continue(iteration)
    
    def _process_tool_result(self, tool_name: str, tool_result: Dict[str, Any]) -> None:
        """Track progress through phases."""
        if self.current_phase == "research" and tool_name == "web_search":
            # Check if we have enough research
            search_count = len([msg for msg in self.conversation 
                              if "web_search" in msg.content])
            if search_count >= 3:
                self.research_complete = True
        
        elif self.current_phase == "analysis" and tool_name == "calculator":
            # Store analysis results
            result = {
                "phase": "analysis",
                "calculation": tool_result["expression"],
                "result": tool_result["result"]
            }
            self.add_result(result)
```

## Example 3: Custom Tool Call Format

```python
@dataclass
class XMLFormatAgent(Agent):
    """Agent that uses XML format for tool calls instead of JSON."""
    
    def _parse_tool_calls(self, content: str) -> List[Dict[str, Any]]:
        """Parse XML-style tool calls: <tool name="calculator"><input>2+2</input></tool>"""
        import re
        
        tool_calls = []
        pattern = r'<tool name="([^"]+)"><input>([^<]+)</input></tool>'
        matches = re.findall(pattern, content)
        
        for tool_name, input_expr in matches:
            if tool_name == "calculator":
                tool_calls.append({
                    "tool": tool_name,
                    "input": {"expression": input_expr}
                })
        
        return tool_calls
    
    def _initialize_conversation(self) -> None:
        """Custom system prompt for XML format."""
        system_prompt = """
You are an agent that uses XML format for tool calls.

Use this format: <tool name="calculator"><input>2+2</input></tool>

Task: {{ task_description }}
"""
        template = Template(system_prompt)
        rendered = template.render(task_description=self.task_description)
        
        self.conversation = [
            Message(role="system", content=rendered),
            Message(role="user", content=f"Complete: {self.task_description}")
        ]
```

## Example 4: Streaming Response Handler

```python
@dataclass
class StreamingAgent(Agent):
    """Agent that processes streaming LLM responses."""
    
    def _get_llm_response(self) -> LLMResponse:
        """Handle streaming responses."""
        full_content = ""
        
        for chunk in self.llm_api.chat_completion_stream(self.conversation):
            full_content += chunk.content
            # Process partial responses for real-time tool calls
            if '{"tool":' in chunk.content:
                self._handle_partial_tool_call(chunk.content)
        
        return LLMResponse(
            role="assistant",
            content=full_content,
            token_usage={"total_tokens": len(full_content) // 4}
        )
    
    def _handle_partial_tool_call(self, partial_content: str) -> None:
        """Handle tool calls as they come in from streaming."""
        # Implementation for real-time tool execution
        pass
```

## Example 5: Validation and Error Recovery

```python
@dataclass
class RobustAgent(Agent):
    """Agent with enhanced error handling and validation."""
    
    def _handle_error(self, error: Exception, iteration: int) -> None:
        """Enhanced error handling with recovery strategies."""
        if isinstance(error, ToolExecutionError):
            # Try alternative approach for tool errors
            recovery_msg = Message(
                role="user",
                content="The tool call failed. Please try a different approach or simpler calculation."
            )
            self.conversation.append(recovery_msg)
        else:
            # Use default error handling
            super()._handle_error(error, iteration)
    
    def _process_llm_response(self, response: LLMResponse) -> None:
        """Validate response before processing."""
        if len(response.content.strip()) < 10:
            # Response too short, ask for elaboration
            clarification_msg = Message(
                role="user",
                content="Please provide a more detailed response."
            )
            self.conversation.append(clarification_msg)
            return
        
        super()._process_llm_response(response)
```

## Best Practices

1. **Always call `super().__init__()`** when creating custom agents
2. **Override `_setup_agent()`** to register tools specific to your agent
3. **Use `_process_tool_result()`** to extract structured results from tool outputs
4. **Override `_is_task_complete()`** for custom completion logic
5. **Keep the main `react_loop()` unchanged** unless you have very specific needs
6. **Use dataclass decorators** for clean inheritance
7. **Add type hints** for better code clarity
8. **Document your custom step methods** clearly

## Testing Custom Agents

```python
def test_custom_agent():
    from agent_system.llm_apis import MockLLMApi
    
    llm_api = MockLLMApi({
        "response_delay": 0.1,
        "mock_responses": [
            "I'll calculate the statistics.",
            '{"tool": "calculator", "input": {"expression": "sum([1,2,3,4,5])/5"}}',
            "The mean is 3.0. STATS_COMPLETE"
        ]
    })
    
    agent = StatisticsAgent(llm_api=llm_api)
    agent.task_description = "Calculate the mean of [1,2,3,4,5]"
    agent.react_loop()
    
    assert agent.is_complete
    assert len(agent.results) > 0
```

This modular approach makes it easy to create specialized agents for different domains while maintaining the robust ReAct loop infrastructure.