# Core Module

The core module provides the fundamental building blocks of the agent system: base classes, parsers, registries, and foundational models.

## Components

### Base Classes

- **`Agent`**: Main agent class implementing the ReAct loop
- **`Tool`**: Generic base class for all tools with Pydantic validation
- **`LLMApi`**: Abstract interface for LLM providers

### Supporting Systems

- **`ResponseParser`**: Parses `<TOOL>` and `<RESULT>` tags from agent responses
- **`ComponentRegistry`**: Centralized component tracking and validation
- **Base Models**: Pydantic models for configurations and data validation

## Key Files

- `agent.py` - Core Agent implementation
- `tool.py` - Tool base class and validation
- `llm_api.py` - LLM API interface and models
- `parser.py` - Tag-based response parsing
- `registry.py` - Component registration and discovery
- `base_models.py` - Pydantic base models

## Usage

### Creating a Custom Agent

```python
from agent_system.core import Agent

class MyAgent(Agent):
    def _setup_agent(self):
        # Override to add default tools
        pass
    
    def _is_task_complete(self, response):
        # Override completion detection
        return "done" in response.content.lower()
```

### Implementing a Tool

```python
from agent_system.core import Tool, ToolConfig, ToolInputBase, ToolOutputBase

class MyTool(Tool[MyConfig, MyInput, MyOutput]):
    @classmethod
    def _get_config_class(cls): return MyConfig
    @classmethod  
    def _get_input_class(cls): return MyInput
    @classmethod
    def _get_output_class(cls): return MyOutput
    
    def _execute(self, input_data, identity=None):
        # Tool implementation
        return MyOutput(result="processed")
```

### Using the Parser

```python
from agent_system.core import ResponseParser

# Parse tool calls from agent response
tool_calls = ResponseParser.parse_tool_calls(response_content)

# Parse results 
results = ResponseParser.parse_results(response_content)

# Parse both at once
tool_calls, results = ResponseParser.extract_all(response_content)
```

### Registry Operations

```python
from agent_system.core import get_registry, register_tool

# Get global registry
registry = get_registry()

# Register components with decorators
@register_tool(config_class=MyConfig, input_class=MyInput, output_class=MyOutput)
class MyTool(Tool):
    pass

# Query registry
all_tools = registry.get_all_tools()
tool_info = registry.get_tool("MyTool")
```

## Agent Lifecycle

1. **Initialization**: Agent sets up tools and system prompt
2. **Conversation Start**: System prompt and task sent to LLM
3. **ReAct Loop**: 
   - Get LLM response
   - Parse tool calls and execute in parallel
   - Add results to conversation
   - Check completion criteria
4. **Finalization**: Deduplicate results and generate status

## Tag Format

The parser expects XML-like tags:

```xml
<TOOL>
{"tool": "tool_name", "input": {"param": "value"}}
</TOOL>

<RESULT>
{"key": "value", "data": [1, 2, 3]}
</RESULT>
```

## Extension Points

Override these methods in Agent subclasses:

- `_setup_agent()` - Add default tools/configuration
- `_initialize_conversation()` - Customize initial messages
- `_should_continue()` - Custom termination logic
- `_is_task_complete()` - Custom completion detection
- `_process_tool_result()` - Handle tool outputs
- `_handle_error()` - Custom error handling

## Thread Safety

- Tools should be thread-safe for parallel execution
- Agent conversation history is not thread-safe
- Registry is thread-safe for read operations