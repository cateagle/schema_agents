"""
Validation utilities for the Streamlit application.
"""

import json
import jsonschema
from typing import Dict, Any, List, Tuple, Optional


def validate_json_schema(schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate a JSON schema structure."""
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
                prop_errors = validate_property_definition(prop_name, prop_def)
                errors.extend(prop_errors)
        
        # Validate required fields
        if "required" in schema:
            if not isinstance(schema["required"], list):
                errors.append("'required' field must be a list")
            else:
                properties = schema.get("properties", {})
                for req_field in schema["required"]:
                    if req_field not in properties:
                        errors.append(f"Required field '{req_field}' not found in properties")
        
        # Try to validate against JSON Schema meta-schema
        try:
            jsonschema.Draft7Validator.check_schema(schema)
        except jsonschema.SchemaError as e:
            errors.append(f"Schema validation error: {str(e)}")
        
        return len(errors) == 0, errors
        
    except Exception as e:
        errors.append(f"Schema validation error: {str(e)}")
        return False, errors


def validate_property_definition(prop_name: str, prop_def: Dict[str, Any]) -> List[str]:
    """Validate a single property definition."""
    errors = []
    
    if not isinstance(prop_def, dict):
        errors.append(f"Property '{prop_name}' definition must be a dictionary")
        return errors
    
    if "type" not in prop_def:
        errors.append(f"Property '{prop_name}' must have a 'type' field")
        return errors
    
    prop_type = prop_def["type"]
    valid_types = ["string", "number", "integer", "boolean", "array", "object", "null"]
    
    if prop_type not in valid_types:
        errors.append(f"Property '{prop_name}' has invalid type '{prop_type}'. Valid types: {valid_types}")
    
    # Validate type-specific constraints
    if prop_type == "string":
        if "minLength" in prop_def and not isinstance(prop_def["minLength"], int):
            errors.append(f"Property '{prop_name}' minLength must be an integer")
        if "maxLength" in prop_def and not isinstance(prop_def["maxLength"], int):
            errors.append(f"Property '{prop_name}' maxLength must be an integer")
        if "pattern" in prop_def and not isinstance(prop_def["pattern"], str):
            errors.append(f"Property '{prop_name}' pattern must be a string")
    
    elif prop_type in ["number", "integer"]:
        if "minimum" in prop_def and not isinstance(prop_def["minimum"], (int, float)):
            errors.append(f"Property '{prop_name}' minimum must be a number")
        if "maximum" in prop_def and not isinstance(prop_def["maximum"], (int, float)):
            errors.append(f"Property '{prop_name}' maximum must be a number")
    
    elif prop_type == "array":
        if "items" in prop_def and not isinstance(prop_def["items"], dict):
            errors.append(f"Property '{prop_name}' items must be a dictionary")
        if "minItems" in prop_def and not isinstance(prop_def["minItems"], int):
            errors.append(f"Property '{prop_name}' minItems must be an integer")
        if "maxItems" in prop_def and not isinstance(prop_def["maxItems"], int):
            errors.append(f"Property '{prop_name}' maxItems must be an integer")
    
    return errors


def validate_research_result(result: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate a research result against a schema."""
    errors = []
    
    try:
        jsonschema.validate(result, schema)
        return True, []
    except jsonschema.ValidationError as e:
        errors.append(f"Validation error: {str(e)}")
        return False, errors
    except Exception as e:
        errors.append(f"Unexpected validation error: {str(e)}")
        return False, errors


def validate_search_configuration(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate search configuration parameters."""
    errors = []
    
    # Required fields
    if "openrouter_api_key" not in config or not config["openrouter_api_key"]:
        errors.append("OpenRouter API key is required")
    
    # Agent configuration
    num_agents = config.get("num_agents", 0)
    if not isinstance(num_agents, int) or num_agents < 1:
        errors.append("Number of agents must be a positive integer")
    elif num_agents > 10:
        errors.append("Number of agents cannot exceed 10")
    
    # Timeout validation
    timeout = config.get("agent_timeout", 0)
    if not isinstance(timeout, int) or timeout < 10:
        errors.append("Agent timeout must be at least 10 seconds")
    elif timeout > 600:
        errors.append("Agent timeout cannot exceed 600 seconds")
    
    # Results validation
    max_results = config.get("max_results_per_agent", 0)
    if not isinstance(max_results, int) or max_results < 1:
        errors.append("Max results per agent must be a positive integer")
    elif max_results > 50:
        errors.append("Max results per agent cannot exceed 50")
    
    # Model validation
    conversation_model = config.get("conversation_model", "")
    agent_model = config.get("agent_model", "")
    
    if not conversation_model:
        errors.append("Conversation model must be specified")
    if not agent_model:
        errors.append("Agent model must be specified")
    
    return len(errors) == 0, errors


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations."""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    
    # Ensure not empty
    if not filename:
        filename = "untitled"
    
    return filename


def validate_json_string(json_string: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """Validate and parse a JSON string."""
    try:
        parsed = json.loads(json_string)
        return True, parsed, "Valid JSON"
    except json.JSONDecodeError as e:
        return False, None, f"Invalid JSON: {str(e)}"
    except Exception as e:
        return False, None, f"Error parsing JSON: {str(e)}"


def analyze_schema_complexity(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze schema complexity and provide insights."""
    analysis = {
        "complexity_score": 0,
        "total_properties": 0,
        "required_properties": 0,
        "optional_properties": 0,
        "nested_objects": 0,
        "array_properties": 0,
        "property_types": {},
        "suggestions": []
    }
    
    if not isinstance(schema, dict) or "properties" not in schema:
        return analysis
    
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    analysis["total_properties"] = len(properties)
    analysis["required_properties"] = len(required)
    analysis["optional_properties"] = len(properties) - len(required)
    
    # Analyze property types and complexity
    for prop_name, prop_def in properties.items():
        if not isinstance(prop_def, dict):
            continue
        
        prop_type = prop_def.get("type", "unknown")
        analysis["property_types"][prop_type] = analysis["property_types"].get(prop_type, 0) + 1
        
        if prop_type == "object":
            analysis["nested_objects"] += 1
            analysis["complexity_score"] += 2
        elif prop_type == "array":
            analysis["array_properties"] += 1
            analysis["complexity_score"] += 1
        else:
            analysis["complexity_score"] += 0.5
    
    # Generate suggestions
    if analysis["total_properties"] > 15:
        analysis["suggestions"].append("Consider reducing the number of properties for better search performance")
    
    if analysis["required_properties"] > 10:
        analysis["suggestions"].append("Consider making some required fields optional to increase result coverage")
    
    if analysis["nested_objects"] > 3:
        analysis["suggestions"].append("Complex nested objects may be difficult for agents to populate consistently")
    
    if analysis["complexity_score"] > 20:
        analysis["suggestions"].append("This schema is quite complex - consider simplifying for initial searches")
    
    return analysis