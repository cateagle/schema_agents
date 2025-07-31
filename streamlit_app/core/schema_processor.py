"""
Schema building and processing logic using the agent system.
"""

import json
from typing import Dict, Any, Optional, List
from agent_system.llm_apis import OpenRouterLLMApi
from agent_system.core import Message

from streamlit_app.config.prompts.schema_prompts import (
    get_schema_prompt, 
    SCHEMA_EXAMPLES
)


class SchemaProcessor:
    """Handles schema building and validation logic."""
    
    def __init__(self, openrouter_api_key: str, model: str = "anthropic/claude-3.5-sonnet"):
        self.api_key = openrouter_api_key
        self.model = model
        
        # Initialize LLM API
        self.llm_api = OpenRouterLLMApi({
            "api_key": openrouter_api_key,
            "model": model,
            "temperature": 0.3
        })
        
    
    def process_schema_conversation(
        self, 
        conversation_history: List[Dict[str, str]], 
        user_message: str
    ) -> str:
        """Process a schema building conversation using direct LLM calls."""
        try:
            # Build conversation from history with system prompt
            conversation = [Message(role="system", content=get_schema_prompt())]
            
            # Add conversation history
            for msg in conversation_history:
                conversation.append(Message(
                    role=msg["role"], 
                    content=msg["content"]
                ))
            
            # Add current user message
            conversation.append(Message(role="user", content=user_message))
            
            # Get LLM response directly - no agent needed
            response = self.llm_api.chat_completion(conversation)
            response_content = response.content.strip()
            
            # Replace <JSONSCHEMA> tags with markdown for display
            response_content = self._replace_extraction_markers(response_content)
            
            return response_content
            
        except Exception as e:
            return f"Error processing schema conversation: {str(e)}"
    
    def validate_schema(self, schema: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate a JSON schema."""
        errors = []
        
        try:
            # Basic structure validation
            if not isinstance(schema, dict):
                errors.append("Schema must be a dictionary")
                return False, errors
            
            if "type" not in schema:
                errors.append("Schema must have a 'type' field")
            
            if schema.get("type") != "object":
                errors.append("Schema type must be 'object' for research results")
            
            if "properties" not in schema:
                errors.append("Schema must have a 'properties' field")
            elif not isinstance(schema["properties"], dict):
                errors.append("Schema 'properties' must be a dictionary")
            elif len(schema["properties"]) == 0:
                errors.append("Schema must have at least one property")
            
            # Validate properties
            if "properties" in schema and isinstance(schema["properties"], dict):
                for prop_name, prop_def in schema["properties"].items():
                    if not isinstance(prop_def, dict):
                        errors.append(f"Property '{prop_name}' definition must be a dictionary")
                        continue
                    
                    if "type" not in prop_def:
                        errors.append(f"Property '{prop_name}' must have a 'type' field")
            
            # Validate required fields
            if "required" in schema:
                if not isinstance(schema["required"], list):
                    errors.append("'required' field must be a list")
                else:
                    properties = schema.get("properties", {})
                    for req_field in schema["required"]:
                        if req_field not in properties:
                            errors.append(f"Required field '{req_field}' not found in properties")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Schema validation error: {str(e)}")
            return False, errors
    
    def extract_schema_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract schema from LLM response using <JSONSCHEMA> markers or fallback to JSON blocks."""
        try:
            # Primary method: Look for <JSONSCHEMA> tags
            if "<JSONSCHEMA>" in response and "</JSONSCHEMA>" in response:
                start = response.find("<JSONSCHEMA>") + 12
                end = response.find("</JSONSCHEMA>")
                if end != -1:
                    json_str = response[start:end].strip()
                    # Remove any comments (lines starting with //)
                    lines = json_str.split('\n')
                    clean_lines = [line for line in lines if not line.strip().startswith('//')]
                    clean_json = '\n'.join(clean_lines)
                    
                    schema = json.loads(clean_json)
                    return schema
            
            # Fallback: Look for JSON code blocks (for backward compatibility)
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end != -1:
                    json_str = response[start:end].strip()
                    # Try to extract a complete JSON object
                    schema = json.loads(json_str)
                    # Only accept if it looks like a schema (has type and properties)
                    if isinstance(schema, dict) and "type" in schema and "properties" in schema:
                        return schema
            
            return None
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing schema: {e}")
            return None
    
    def _replace_extraction_markers(self, response: str) -> str:
        """Replace <JSONSCHEMA> markers with markdown code blocks for display."""
        import re
        
        # Pattern to find <JSONSCHEMA>...</JSONSCHEMA> blocks
        pattern = r'<JSONSCHEMA>(.*?)</JSONSCHEMA>'
        
        def replace_block(match):
            json_content = match.group(1).strip()
            return f"```json\n{json_content}\n```"
        
        # Replace all occurrences
        return re.sub(pattern, replace_block, response, flags=re.DOTALL)
    
    def get_schema_examples(self) -> Dict[str, Dict[str, Any]]:
        """Get predefined schema examples."""
        return SCHEMA_EXAMPLES
    
    def generate_search_prompt_from_conversation(
        self, 
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """Generate search prompt from conversation context using agent system."""
        if not conversation_history:
            return "research and analysis"
        
        try:
            # Simple extraction - get the most recent substantial user message
            for msg in reversed(conversation_history):
                if msg["role"] == "user" and len(msg["content"]) > 10:
                    return msg["content"]
            
            # Fallback to combining user messages
            user_messages = [msg["content"] for msg in conversation_history if msg["role"] == "user"]
            if user_messages:
                return " ".join(user_messages)
            
            return "research and analysis"
            
        except Exception as e:
            return "research and analysis"
    
    def suggest_schema_improvements(
        self, 
        current_schema: Dict[str, Any], 
        feedback: str
    ) -> str:
        """Suggest improvements to a schema based on feedback."""
        try:
            # Create a simple refinement prompt
            refinement_prompt = f"""You are helping refine a JSON schema based on user feedback.

Current schema: {json.dumps(current_schema, indent=2)}
User feedback: {feedback}

Please suggest improvements and provide an updated schema using <JSONSCHEMA></JSONSCHEMA> tags if you have a concrete suggestion."""
            
            conversation = [
                Message(role="system", content=get_schema_prompt()),
                Message(role="user", content=refinement_prompt)
            ]
            
            # Get response from LLM API
            response = self.llm_api.chat_completion(conversation)
            response_content = response.content.strip()
            
            # Replace markers for display
            response_content = self._replace_extraction_markers(response_content)
            
            return response_content
            
        except Exception as e:
            return f"Error generating schema improvements: {str(e)}"