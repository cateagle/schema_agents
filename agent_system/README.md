# Agent System

A modular Python framework for building LLM-powered autonomous agents with configurable tools, parallel execution, and comprehensive component management.

## Key Features

- **ReAct Loop Architecture**: Reasoning and Acting pattern for agent behavior
- **Pydantic-Based Validation**: Type-safe tool inputs/outputs and configurations
- **Tag-Based Parsing**: `<TOOL>` and `<RESULT>` tags for structured communication
- **Parallel Tool Execution**: Multiple tools can run concurrently
- **Runtime Configuration**: Modify agents, tools, and schemas at runtime
- **Component Registry**: Centralized tracking and validation of all components
- **Multiple Tool Instances**: Same tool with different configurations via aliases

## Quick Start

```python
from agent_system.core import Agent
from agent_system.llm_apis import MockLLMApi
from agent_system.tools import CalculatorTool, CalculatorConfig

# Create agent with custom tools
agent = Agent(
    system_prompt="You are a helpful calculator assistant.",
    task_description="Calculate 15 × 8",
    llm_api=MockLLMApi({}),
    tools=[
        CalculatorTool(config=CalculatorConfig(precision=2)),
        CalculatorTool(config=CalculatorConfig(precision=10), alias="precise_calc")
    ]
)

# Run the agent
agent.react_loop()
print(f"Results: {agent.results}")
```

## Architecture

```
agent_system/
├── core/           # Base classes and framework components
├── tools/          # Available tools for agents
├── agents/         # Pre-built specialized agents  
├── llm_apis/       # LLM API implementations
└── examples/       # Usage examples
```

## Creating Components

### 1. Creating a Tool

```python
from agent_system.core import Tool, ToolConfig, ToolInputBase, ToolOutputBase, register_tool
from pydantic import Field

class MyToolConfig(ToolConfig):
    parameter: str = Field(default="default", description="Tool parameter")

class MyToolInput(ToolInputBase):
    query: str = Field(..., description="Input query")

class MyToolOutput(ToolOutputBase):
    result: str = Field(..., description="Tool result")

@register_tool(
    config_class=MyToolConfig,
    input_class=MyToolInput,
    output_class=MyToolOutput
)
class MyTool(Tool[MyToolConfig, MyToolInput, MyToolOutput]):
    def __init__(self, config=None, alias=None):
        super().__init__(
            name="my_tool",
            short_description="Does something useful",
            long_description="Detailed description",
            config=config,
            alias=alias
        )
    
    @classmethod
    def _get_config_class(cls): return MyToolConfig
    @classmethod
    def _get_input_class(cls): return MyToolInput
    @classmethod
    def _get_output_class(cls): return MyToolOutput
    
    def _execute(self, input_data, identity=None):
        return MyToolOutput(result=f"Processed: {input_data.query}")
```

### 2. Creating an Agent

```python
from agent_system.core import Agent, register_agent

@register_agent(description="Specialized agent for specific tasks")
class MyAgent(Agent):
    def __init__(self, llm_api, **kwargs):
        # Use defaults or custom configuration
        super().__init__(
            system_prompt=kwargs.get('system_prompt', "Default prompt"),
            llm_api=llm_api,
            tools=kwargs.get('tools', [MyTool()]),
            **kwargs
        )
```

## Agent Communication Protocol

Agents use XML-like tags for structured communication:

**Tool Calls:**
```xml
<TOOL>
{
    "tool": "calculator",
    "input": {"expression": "2 + 2"}
}
</TOOL>
```

**Results:**
```xml
<RESULT>
{
    "answer": 42,
    "explanation": "The calculation result"
}
</RESULT>
```

## Runtime Configuration

```python
# Modify agents at runtime
agent.set_system_prompt("New system prompt")
agent.register_tools([new_tool])
agent.unregister_tool("old_tool")
agent.update_tool_config("calc", new_config)
agent.set_result_schema(new_schema)
```

## Component Registry

```python
from agent_system.core import get_registry

registry = get_registry()

# Discover available components
tools = registry.get_all_tools()
agents = registry.get_all_agents()

# Get component information
tool_info = registry.get_tool("CalculatorTool")
print(f"Config class: {tool_info.associated_classes['config']}")

# Validate naming conventions
errors = registry.validate_naming_conventions()
```

## Development

### Structure Validation
```bash
python dev/check_agent_system_structure.py --registry
```

### Running Examples
```bash
python agent_system/examples/runtime_configuration_example.py
```

## Best Practices

1. **Always use Pydantic models** for tool inputs/outputs and configurations
2. **Register components** with appropriate decorators
3. **Follow naming conventions**: `MyTool`, `MyToolConfig`, `MyToolInput`, `MyToolOutput`
4. **Use aliases** when registering multiple instances of the same tool
5. **Implement proper error handling** in tool `_execute()` methods
6. **Keep tool operations atomic** and thread-safe for parallel execution

## Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test category
python -m pytest tests/test_tools.py
python -m pytest tests/test_agents.py
python -m pytest tests/test_registry.py
```