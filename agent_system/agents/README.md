# Agents Module

Pre-built specialized agents for common use cases. All agents are fully configurable and can be customized with different tools, prompts, and schemas.

## Available Agents

### MathSolverAgent
Specialized agent for solving mathematical problems with step-by-step reasoning.

**Default Tools:** CalculatorTool with 10-digit precision
**Default Schema:** Problem, solution, answer, and steps

**Example:**
```python
from agent_system.agents import MathSolverAgent
from agent_system.llm_apis import MockLLMApi

# Use with defaults
agent = MathSolverAgent(llm_api=MockLLMApi({}))

# Customize configuration
agent = MathSolverAgent(
    llm_api=MockLLMApi({}),
    system_prompt="Custom math prompt",
    tools=[CalculatorTool(config=CalculatorConfig(precision=20))],
    result_schema=custom_schema
)

# Solve a problem
result = agent.solve_problem("Find the roots of x² - 5x + 6 = 0")
```

### ResearchAgent
Agent for conducting research using web search and analysis tools.

**Default Tools:** WebSearchTool with mock search engine
**Default Schema:** Topic, summary, sources, and key findings

**Example:**
```python
from agent_system.agents import ResearchAgent

# Use with defaults
agent = ResearchAgent(llm_api=MockLLMApi({}))

# Customize with multiple search tools
agent = ResearchAgent(
    llm_api=MockLLMApi({}),
    tools=[
        WebSearchTool(config=WebSearchConfig(region="academic"), alias="academic"),
        WebSearchTool(config=WebSearchConfig(region="news"), alias="news")
    ]
)

# Conduct research
result = agent.research_topic(
    "Machine Learning Trends",
    specific_questions=["What are the latest developments?"]
)
```

## Creating Custom Agents

### 1. Basic Agent Structure

```python
from agent_system.core import Agent, register_agent
from agent_system.tools import CalculatorTool

@register_agent(description="Agent for specific domain tasks")
class MyAgent(Agent):
    def __init__(self, llm_api, **kwargs):
        # Define defaults
        default_prompt = """
You are a specialized agent for specific tasks.

Available Tools:
{% for tool in tools %}
- {{ tool.name }}: {{ tool.short_description }}
{% endfor %}

Task: {{ task_description }}

Instructions:
1. Analyze the task carefully
2. Use appropriate tools
3. Provide clear results using <RESULT> tags
4. Include "TASK_COMPLETE" when finished
"""
        
        default_schema = {
            "type": "object",
            "properties": {
                "task": {"type": "string"},
                "result": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1}
            }
        }
        
        # Initialize with defaults or custom values
        super().__init__(
            system_prompt=kwargs.get('system_prompt', default_prompt),
            llm_api=llm_api,
            tools=kwargs.get('tools', [CalculatorTool()]),
            result_schema=kwargs.get('result_schema', default_schema),
            **{k: v for k, v in kwargs.items() 
               if k not in ['system_prompt', 'tools', 'result_schema']}
        )
```

### 2. Advanced Agent with Custom Logic

```python
class AdvancedAgent(Agent):
    def __init__(self, llm_api, domain_knowledge=None, **kwargs):
        self.domain_knowledge = domain_knowledge or {}
        super().__init__(llm_api=llm_api, **kwargs)
    
    def _setup_agent(self):
        """Called after initialization to add domain-specific setup"""
        if self.domain_knowledge:
            # Add domain-specific tools based on knowledge base
            domain_tools = self._create_domain_tools()
            self.register_tools(domain_tools)
    
    def _is_task_complete(self, response):
        """Custom completion detection"""
        return (super()._is_task_complete(response) or
                "analysis complete" in response.content.lower())
    
    def _process_tool_result(self, tool_name, tool_result):
        """Process tool results with domain knowledge"""
        if tool_name in self.domain_knowledge:
            # Apply domain-specific processing
            enhanced_result = self._enhance_with_domain_knowledge(
                tool_result, self.domain_knowledge[tool_name]
            )
            self.add_result(enhanced_result)
    
    def _create_domain_tools(self):
        """Create tools based on domain knowledge"""
        # Implementation specific to domain
        return []
    
    def _enhance_with_domain_knowledge(self, result, knowledge):
        """Enhance results with domain expertise"""
        # Implementation specific to domain
        return result
```

### 3. Agent with Convenience Methods

```python
class ConversationalAgent(Agent):
    def __init__(self, llm_api, **kwargs):
        super().__init__(llm_api=llm_api, **kwargs)
        self.conversation_history = []
    
    def chat(self, message: str) -> str:
        """Simple chat interface"""
        self.set_task_description(f"Respond to: {message}")
        self.reset_conversation()
        self.react_loop()
        
        # Get the latest assistant response
        for msg in reversed(self.conversation):
            if msg.role == "assistant":
                return msg.content
        return "No response generated"
    
    def multi_turn_chat(self, messages: List[str]) -> List[str]:
        """Handle multiple conversation turns"""
        responses = []
        for message in messages:
            response = self.chat(message)
            responses.append(response)
            self.conversation_history.append({"user": message, "assistant": response})
        return responses
```

## Agent Configuration Patterns

### Runtime Reconfiguration
```python
# Create agent
agent = MyAgent(llm_api=llm_api)

# Modify at runtime
agent.set_system_prompt("New specialized prompt")
agent.register_tools([new_tool])
agent.set_result_schema(new_schema)

# Use for different task
agent.set_task_description("New task type")
agent.react_loop()
```

### Multiple Configurations
```python
# Create different configurations of the same agent
research_agent = ResearchAgent(
    llm_api=llm_api,
    tools=[WebSearchTool(config=WebSearchConfig(region="academic"))]
)

news_agent = ResearchAgent(
    llm_api=llm_api,
    tools=[WebSearchTool(config=WebSearchConfig(region="news"))],
    system_prompt="You are a news analysis agent..."
)
```

## Agent Lifecycle Methods

Override these methods to customize behavior:

### Setup and Initialization
- `_setup_agent()` - Called after __init__ for custom setup
- `_initialize_conversation()` - Customize initial conversation

### Loop Control  
- `_should_continue()` - Custom termination conditions
- `_is_task_complete()` - Detect when task is finished

### Response Processing
- `_process_llm_response()` - Handle LLM responses
- `_process_tool_result()` - Process tool outputs
- `_extract_results_from_response()` - Extract structured results

### Error Handling
- `_handle_error()` - Custom error handling logic

## Testing Agents

```python
import pytest
from agent_system.agents import MyAgent
from agent_system.llm_apis import MockLLMApi

def test_my_agent():
    # Create agent with mock LLM
    agent = MyAgent(
        llm_api=MockLLMApi({
            "mock_responses": [
                "I'll solve this step by step...",
                "<RESULT>{'answer': 42}</RESULT> TASK_COMPLETE"
            ]
        })
    )
    
    # Test agent execution
    agent.set_task_description("Test task")
    agent.react_loop()
    
    assert agent.is_complete
    assert len(agent.results) > 0

def test_agent_configuration():
    agent = MyAgent(llm_api=MockLLMApi({}))
    
    # Test runtime configuration
    agent.set_system_prompt("New prompt")
    assert "New prompt" in agent.system_prompt
    
    # Test tool management
    initial_tools = len(agent.tools)
    agent.register_tools([new_tool])
    assert len(agent.tools) == initial_tools + 1
```

## Best Practices

1. **Provide sensible defaults** but allow full customization
2. **Use descriptive system prompts** that guide the LLM effectively
3. **Define clear result schemas** for structured outputs
4. **Implement custom completion detection** for better control
5. **Add domain-specific processing** in `_process_tool_result()`
6. **Keep agents focused** on specific problem domains
7. **Document expected inputs/outputs** clearly
8. **Test with mock LLMs** to verify logic without API calls