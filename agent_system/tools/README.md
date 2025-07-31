# Tools Module

Tools provide specific capabilities to agents. Each tool is self-contained with Pydantic validation and can be configured for different use cases.

## Available Tools

### CalculatorTool
Mathematical expression evaluator with configurable precision.

**Configuration:**
- `precision`: Number of decimal places (default: 10)
- `allow_complex`: Enable complex number operations (default: False)

**Example:**
```python
from agent_system.tools import CalculatorTool, CalculatorConfig

# High precision calculator
calc = CalculatorTool(
    config=CalculatorConfig(precision=20),
    alias="precise_calc"
)
```

### WebSearchTool
Web search functionality with configurable search engines.

**Configuration:**
- `search_engine`: Search provider ("mock", "google", "bing")
- `region`: Search region/language (default: "us-en")
- `safe_search`: Enable safe search filtering (default: True)
- `api_key`: API key for the search service

**Example:**
```python
from agent_system.tools import WebSearchTool, WebSearchConfig

# Academic search tool
search = WebSearchTool(
    config=WebSearchConfig(
        search_engine="mock",
        region="academic"
    ),
    alias="academic_search"
)
```

## Creating Custom Tools

### 1. Define Models

```python
from agent_system.core import ToolConfig, ToolInputBase, ToolOutputBase
from pydantic import Field

class MyToolConfig(ToolConfig):
    api_key: str = Field(..., description="API key for the service")
    timeout: int = Field(default=30, description="Request timeout in seconds")

class MyToolInput(ToolInputBase):
    query: str = Field(..., description="Search query")
    max_results: int = Field(default=10, ge=1, le=100)

class MyToolOutput(ToolOutputBase):
    results: List[str] = Field(..., description="Search results")
    count: int = Field(..., description="Number of results found")
```

### 2. Implement Tool

```python
from agent_system.core import Tool, ToolExecutionError, register_tool

@register_tool(
    config_class=MyToolConfig,
    input_class=MyToolInput,
    output_class=MyToolOutput,
    description="Custom search tool"
)
class MyTool(Tool[MyToolConfig, MyToolInput, MyToolOutput]):
    def __init__(self, config=None, alias=None):
        super().__init__(
            name="my_tool",
            short_description="Performs custom searches",
            long_description="Detailed description of functionality",
            config=config,
            alias=alias
        )
    
    @classmethod
    def _get_config_class(cls):
        return MyToolConfig
    
    @classmethod
    def _get_input_class(cls):
        return MyToolInput
    
    @classmethod
    def _get_output_class(cls):
        return MyToolOutput
    
    def _execute(self, input_data: MyToolInput, identity=None) -> MyToolOutput:
        try:
            # Tool implementation here
            results = self._perform_search(input_data.query, input_data.max_results)
            return MyToolOutput(results=results, count=len(results))
        except Exception as e:
            raise ToolExecutionError(f"Search failed: {str(e)}")
    
    def _perform_search(self, query: str, max_results: int) -> List[str]:
        # Implementation details
        pass
```

### 3. Register and Use

```python
# Tool is automatically registered via decorator
from agent_system.tools import MyTool, MyToolConfig

# Use with different configurations
tool1 = MyTool(config=MyToolConfig(api_key="key1"))
tool2 = MyTool(config=MyToolConfig(api_key="key2"), alias="backup_search")

# Register with agent
agent.register_tools([tool1, tool2])
```

## Tool Design Guidelines

### Configuration
- Use `ToolConfig` base class for all configurations
- Make configurations immutable (`frozen=True`)
- Provide sensible defaults
- Use Pydantic validators for complex validation

### Input/Output Models
- Inherit from `ToolInputBase` and `ToolOutputBase`
- Use descriptive field names and descriptions
- Add validation constraints (`ge`, `le`, `regex`, etc.)
- Keep models focused and minimal

### Implementation
- Implement `_execute()` method, not `call()`
- Raise `ToolExecutionError` for operational failures
- Keep operations atomic and stateless
- Ensure thread safety for parallel execution

### Error Handling
```python
def _execute(self, input_data, identity=None):
    try:
        # Tool logic
        return output
    except SpecificError as e:
        raise ToolExecutionError(f"Specific error: {str(e)}")
    except Exception as e:
        raise ToolExecutionError(f"Unexpected error: {str(e)}")
```

## Testing Tools

```python
import pytest
from agent_system.tools import MyTool, MyToolConfig, MyToolInput

def test_my_tool():
    tool = MyTool(config=MyToolConfig(api_key="test"))
    
    # Test valid input
    result = tool.call({"query": "test", "max_results": 5})
    assert "results" in result
    assert isinstance(result["count"], int)
    
    # Test invalid input
    with pytest.raises(ValidationError):
        tool.call({"invalid": "input"})
```

## Tool Registry

All tools are automatically registered when imported:

```python
from agent_system.core import get_registry

registry = get_registry()
tool_info = registry.get_tool("MyTool")
print(f"Associated classes: {tool_info.associated_classes}")
```

## Best Practices

1. **Keep tools focused** - One tool, one responsibility
2. **Use type hints** - Helps with IDE support and validation
3. **Document thoroughly** - Clear descriptions for AI agents
4. **Handle errors gracefully** - Use appropriate exception types
5. **Test edge cases** - Validate input boundaries and error conditions
6. **Make thread-safe** - Tools may execute in parallel