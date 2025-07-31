# LLM APIs Module

LLM API implementations for connecting agents to different language model providers. All APIs implement a common interface for seamless interchangeability.

## Available APIs

### MockLLMApi
Test implementation that returns predefined responses without making actual API calls.

**Configuration:**
- `response_delay`: Simulate API latency (default: 0.5s)
- `mock_responses`: List of predefined responses to cycle through

**Example:**
```python
from agent_system.llm_apis import MockLLMApi

# Basic mock for testing
api = MockLLMApi({
    "response_delay": 0.1,
    "mock_responses": [
        "I'll solve this step by step.",
        "<TOOL>{'tool': 'calculator', 'input': {'expression': '2 + 2'}}</TOOL>",
        "<RESULT>{'answer': 4}</RESULT> TASK_COMPLETE"
    ]
})

# Use with agent
from agent_system.core import Agent
agent = Agent(llm_api=api, task_description="Calculate 2 + 2")
```

### AnthropicLLMApi  
Integration with Anthropic's Claude API for production use.

**Configuration:**
- `api_key`: Anthropic API key (required)
- `model`: Model name (default: "claude-3-sonnet-20240229")
- `base_url`: API endpoint (default: "https://api.anthropic.com")
- `max_tokens`: Maximum response tokens (default: 4000)
- `temperature`: Response randomness (default: 0.7)

**Example:**
```python
from agent_system.llm_apis import AnthropicLLMApi

api = AnthropicLLMApi({
    "api_key": "your-api-key",
    "model": "claude-3-sonnet-20240229",
    "temperature": 0.3
})

agent = Agent(llm_api=api, task_description="Analyze this data")
```

## Creating Custom LLM APIs

### 1. Implement Base Interface

```python
from agent_system.core import LLMApi, Message, LLMResponse, LLMApiError, register_llm_api
from typing import List, Dict, Any, Iterator

@register_llm_api(description="Custom LLM provider")
class CustomLLMApi(LLMApi):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.model = config.get("model", "default-model")
        # Initialize provider-specific settings
    
    def chat_completion(self, messages: List[Message]) -> LLMResponse:
        """Generate single response from conversation history"""
        try:
            # Convert internal format to provider format
            provider_messages = self._convert_messages(messages)
            
            # Make API call
            response = self._make_api_request(provider_messages)
            
            # Convert response to internal format
            return LLMResponse(
                role="assistant",
                content=response["content"],
                token_usage=response.get("usage", {}),
                finish_reason=response.get("finish_reason", "stop")
            )
        except Exception as e:
            raise LLMApiError(f"API call failed: {str(e)}")
    
    def chat_completion_stream(self, messages: List[Message]) -> Iterator[LLMResponse]:
        """Generate streaming responses (optional)"""
        # Implement streaming if provider supports it
        response = self.chat_completion(messages)
        yield response
    
    def structured_completion(self, messages: List[Message], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate JSON response conforming to schema"""
        # Add schema instructions to messages
        enhanced_messages = self._add_schema_instruction(messages, schema)
        
        response = self.chat_completion(enhanced_messages)
        
        # Parse and validate JSON response
        return self._parse_structured_response(response.content, schema)
```

### 2. Helper Methods

```python
def _convert_messages(self, messages: List[Message]) -> List[Dict]:
    """Convert internal message format to provider format"""
    return [{"role": msg.role, "content": msg.content} for msg in messages]

def _make_api_request(self, messages: List[Dict]) -> Dict[str, Any]:
    """Make HTTP request to provider API"""
    import requests
    
    response = requests.post(
        f"{self.base_url}/chat/completions",
        headers={"Authorization": f"Bearer {self.api_key}"},
        json={"model": self.model, "messages": messages}
    )
    response.raise_for_status()
    return response.json()

def _add_schema_instruction(self, messages: List[Message], schema: Dict) -> List[Message]:
    """Add JSON schema instruction to conversation"""
    import json
    instruction = Message(
        role="user",
        content=f"Respond with JSON matching this schema: {json.dumps(schema)}"
    )
    return messages + [instruction]

def _parse_structured_response(self, content: str, schema: Dict) -> Dict[str, Any]:
    """Parse and validate JSON response"""
    import json, jsonschema
    
    # Extract JSON from content (handle markdown wrapping)
    cleaned = content.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:-3]
    
    try:
        result = json.loads(cleaned)
        jsonschema.validate(result, schema)
        return result
    except (json.JSONDecodeError, jsonschema.ValidationError) as e:
        raise LLMApiError(f"Invalid structured response: {str(e)}")
```

## API Interface Methods

### Required Methods

- `chat_completion(messages)` - Generate single response
- `chat_completion_stream(messages)` - Generate streaming responses  
- `structured_completion(messages, schema)` - Generate JSON response

### Message Format

```python
from agent_system.core import Message

message = Message(
    role="user",  # "system", "user", "assistant"
    content="Your message content here"
)
```

### Response Format

```python
from agent_system.core import LLMResponse

response = LLMResponse(
    role="assistant",
    content="AI response content",
    token_usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
    finish_reason="stop"  # "stop", "length", "content_filter"
)
```

## Error Handling

```python
from agent_system.core import LLMApiError

def chat_completion(self, messages):
    try:
        # API call logic
        return response
    except requests.RequestException as e:
        raise LLMApiError(f"Network error: {str(e)}")
    except json.JSONDecodeError as e:
        raise LLMApiError(f"Invalid API response: {str(e)}")
    except Exception as e:
        raise LLMApiError(f"Unexpected error: {str(e)}")
```

## Testing LLM APIs

```python
import pytest
from agent_system.llm_apis import CustomLLMApi
from agent_system.core import Message

def test_custom_llm_api():
    api = CustomLLMApi({"api_key": "test-key"})
    
    messages = [Message(role="user", content="Hello")]
    response = api.chat_completion(messages)
    
    assert response.role == "assistant"
    assert isinstance(response.content, str)
    assert "token_usage" in response.__dict__

def test_structured_completion():
    api = CustomLLMApi({"api_key": "test-key"})
    
    schema = {
        "type": "object",
        "properties": {"answer": {"type": "string"}},
        "required": ["answer"]
    }
    
    messages = [Message(role="user", content="What is 2+2?")]
    result = api.structured_completion(messages, schema)
    
    assert "answer" in result
    assert isinstance(result["answer"], str)
```

## Registry Integration

All LLM APIs are automatically registered:

```python
from agent_system.core import get_registry

registry = get_registry()
llm_apis = registry.get_all_llm_apis()
api_info = registry.get_llm_api("CustomLLMApi")
```

## Best Practices

1. **Handle rate limits** - Implement backoff and retry logic
2. **Validate API keys** - Check authentication during initialization  
3. **Parse responses safely** - Handle malformed JSON and unexpected formats
4. **Log errors appropriately** - Use structured logging for debugging
5. **Support streaming** - Implement streaming for better user experience
6. **Cache responses** - Consider caching for development/testing
7. **Follow provider conventions** - Respect each API's specific requirements
8. **Test thoroughly** - Use mocks to test without API calls