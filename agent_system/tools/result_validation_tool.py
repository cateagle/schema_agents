"""
Result Validation Tool for validating JSON results against schemas.
"""

import json
import jsonschema
from typing import Dict, Any, List, Optional
from pydantic import Field

from agent_system.core import Tool, ToolConfig, ToolInputBase, ToolOutputBase, ToolExecutionError, register_tool


class ResultValidationConfig(ToolConfig):
    """Configuration for result validation tool."""
    strict_validation: bool = Field(default=False, description="Use strict schema validation")
    auto_fix_minor_issues: bool = Field(default=True, description="Automatically fix minor validation issues")
    max_validation_errors: int = Field(default=100, description="Maximum validation errors to report")


class ResultValidationInput(ToolInputBase):
    """Input for result validation tool."""
    json_data: List[Dict[str, Any]] = Field(..., description="JSON data to validate")
    validation_schema: Dict[str, Any] = Field(..., description="JSON schema to validate against")
    validation_mode: str = Field(default="standard", description="Validation mode: strict, standard, or lenient")


class ResultValidationOutput(ToolOutputBase):
    """Output from result validation tool."""
    total_objects: int = Field(..., description="Total number of objects validated")
    valid_objects: int = Field(..., description="Number of objects that passed validation")
    invalid_objects: int = Field(..., description="Number of objects that failed validation")
    validation_errors: List[Dict[str, Any]] = Field(..., description="List of validation errors found")
    auto_fixed_issues: List[str] = Field(..., description="Issues that were automatically fixed")
    validated_data: List[Dict[str, Any]] = Field(..., description="Validated (and potentially corrected) data")
    validation_summary: str = Field(..., description="Summary of validation results")


@register_tool(
    config_class=ResultValidationConfig,
    input_class=ResultValidationInput,
    output_class=ResultValidationOutput,  
    description="Validate JSON results against schemas with error reporting and auto-fixing"
)
class ResultValidationTool(Tool[ResultValidationConfig, ResultValidationInput, ResultValidationOutput]):
    """Tool for validating JSON results against schemas."""
    
    def __init__(self, config: Optional[ResultValidationConfig] = None, alias: Optional[str] = None):
        super().__init__(
            name="result_validation",
            short_description="Validate JSON data against schemas",
            long_description="Comprehensive validation of JSON data against schemas with error reporting, auto-fixing capabilities, and detailed validation summaries",
            config=config or ResultValidationConfig(),
            alias=alias
        )
    
    @classmethod
    def _get_config_class(cls):
        return ResultValidationConfig
    
    @classmethod
    def _get_input_class(cls):
        return ResultValidationInput
    
    @classmethod
    def _get_output_class(cls):
        return ResultValidationOutput
    
    def _execute(self, input_data: ResultValidationInput, identity: Optional[Dict[str, Any]] = None) -> ResultValidationOutput:
        """Execute result validation."""
        try:
            json_data = input_data.json_data
            schema = input_data.validation_schema
            validation_mode = input_data.validation_mode
            
            if not json_data:
                return ResultValidationOutput(
                    total_objects=0,
                    valid_objects=0,
                    invalid_objects=0,
                    validation_errors=[],
                    auto_fixed_issues=[],
                    validated_data=[],
                    validation_summary="No data provided for validation"
                )
            
            total_objects = len(json_data)
            valid_objects = 0
            invalid_objects = 0
            validation_errors = []
            auto_fixed_issues = []
            validated_data = []
            
            # Create validator
            try:
                validator = jsonschema.Draft7Validator(schema)
            except jsonschema.SchemaError as e:
                raise ToolExecutionError(f"Invalid schema provided: {str(e)}")
            
            # Validate each object
            for i, obj in enumerate(json_data):
                try:
                    # Attempt validation
                    errors = list(validator.iter_errors(obj))
                    
                    if not errors:
                        # Object is valid
                        valid_objects += 1
                        validated_data.append(obj.copy())
                    else:
                        # Object has validation errors
                        invalid_objects += 1
                        
                        # Try to auto-fix if enabled
                        if self.config.auto_fix_minor_issues:
                            fixed_obj, fixes = self._auto_fix_object(obj, errors, schema)
                            auto_fixed_issues.extend(fixes)
                            validated_data.append(fixed_obj)
                        else:
                            validated_data.append(obj.copy())
                        
                        # Record errors (limited by max_validation_errors)
                        if len(validation_errors) < self.config.max_validation_errors:
                            for error in errors:
                                validation_errors.append({
                                    "object_index": i,
                                    "field_path": ".".join(str(p) for p in error.path) if error.path else "root",
                                    "error_message": error.message,
                                    "invalid_value": str(error.instance)[:200],  # Truncate long values
                                    "validator": error.validator,
                                    "validator_value": str(error.validator_value)[:100]
                                })
                
                except Exception as e:
                    # Handle unexpected validation errors
                    invalid_objects += 1
                    validation_errors.append({
                        "object_index": i,
                        "field_path": "unknown",
                        "error_message": f"Validation failed: {str(e)}",
                        "invalid_value": str(obj)[:200],
                        "validator": "general",
                        "validator_value": ""
                    })
                    validated_data.append(obj.copy())
            
            # Generate validation summary
            validation_summary = self._generate_validation_summary(
                total_objects, valid_objects, invalid_objects, 
                validation_errors, auto_fixed_issues
            )
            
            return ResultValidationOutput(
                total_objects=total_objects,
                valid_objects=valid_objects,
                invalid_objects=invalid_objects,
                validation_errors=validation_errors,
                auto_fixed_issues=auto_fixed_issues,
                validated_data=validated_data,
                validation_summary=validation_summary
            )
            
        except Exception as e:
            raise ToolExecutionError(f"Result validation failed: {str(e)}")
    
    def _auto_fix_object(self, obj: Dict[str, Any], errors: List, schema: Dict[str, Any]) -> tuple[Dict[str, Any], List[str]]:
        """Attempt to automatically fix common validation errors."""
        fixed_obj = obj.copy()
        fixes_applied = []
        
        for error in errors:
            try:
                if error.validator == "required":
                    # Add missing required fields with default values
                    missing_field = error.validator_value[0] if error.validator_value else "unknown"
                    default_value = self._get_default_value_for_field(missing_field, schema)
                    if default_value is not None:
                        fixed_obj[missing_field] = default_value
                        fixes_applied.append(f"Added missing required field '{missing_field}' with default value")
                
                elif error.validator == "type":
                    # Try to convert types
                    field_path = ".".join(str(p) for p in error.path) if error.path else "root"
                    expected_type = error.validator_value
                    current_value = error.instance
                    
                    converted_value = self._convert_type(current_value, expected_type)
                    if converted_value is not None:
                        self._set_nested_value(fixed_obj, error.path, converted_value)
                        fixes_applied.append(f"Converted field '{field_path}' from {type(current_value).__name__} to {expected_type}")
                
                elif error.validator == "format":
                    # Try to fix format issues
                    if error.validator_value == "uri" and isinstance(error.instance, str):
                        # Fix common URL issues
                        fixed_url = self._fix_url_format(error.instance)
                        if fixed_url != error.instance:
                            self._set_nested_value(fixed_obj, error.path, fixed_url)
                            fixes_applied.append(f"Fixed URL format for field at path {'.'.join(str(p) for p in error.path)}")
                
                elif error.validator == "additionalProperties" and error.validator_value is False:
                    # Remove additional properties if not allowed
                    if len(error.path) == 0:  # Root level
                        allowed_properties = schema.get("properties", {}).keys()
                        for key in list(fixed_obj.keys()):
                            if key not in allowed_properties:
                                del fixed_obj[key]
                                fixes_applied.append(f"Removed additional property '{key}'")
            
            except Exception:
                # If auto-fix fails for this error, skip it
                continue
        
        return fixed_obj, fixes_applied
    
    def _get_default_value_for_field(self, field_name: str, schema: Dict[str, Any]) -> Any:
        """Get an appropriate default value for a missing field."""
        properties = schema.get("properties", {})
        
        if field_name in properties:
            field_schema = properties[field_name]
            field_type = field_schema.get("type")
            
            # Check if default is specified in schema
            if "default" in field_schema:
                return field_schema["default"]
            
            # Provide type-appropriate defaults
            if field_type == "string":
                return ""
            elif field_type == "number":
                return 0.0
            elif field_type == "integer":
                return 0
            elif field_type == "boolean":
                return False
            elif field_type == "array":
                return []
            elif field_type == "object":
                return {}
        
        # Fallback defaults based on field name patterns
        if "url" in field_name.lower() or "link" in field_name.lower():
            return ""
        elif "count" in field_name.lower() or "number" in field_name.lower():
            return 0
        elif "date" in field_name.lower() or "time" in field_name.lower():
            return ""
        elif "list" in field_name.lower() or field_name.endswith("s"):
            return []
        
        return None  # Don't add default if we can't determine appropriate value
    
    def _convert_type(self, value: Any, expected_type: str) -> Any:
        """Attempt to convert a value to the expected type."""
        try:
            if expected_type == "string":
                return str(value)
            elif expected_type == "number":
                if isinstance(value, str):
                    # Try to parse as float
                    return float(value)
                elif isinstance(value, (int, float)):
                    return float(value)
            elif expected_type == "integer":
                if isinstance(value, str):
                    # Try to parse as int
                    return int(float(value))  # Handle "1.0" -> 1
                elif isinstance(value, float):
                    return int(value)
                elif isinstance(value, int):
                    return value
            elif expected_type == "boolean":
                if isinstance(value, str):
                    return value.lower() in ("true", "1", "yes", "on")
                else:
                    return bool(value)
            elif expected_type == "array":
                if not isinstance(value, list):
                    return [value]  # Wrap single value in list
        except (ValueError, TypeError):
            pass
        
        return None  # Conversion failed
    
    def _fix_url_format(self, url: str) -> str:
        """Attempt to fix common URL format issues."""
        url = url.strip()
        
        # Add protocol if missing
        if url and not url.startswith(("http://", "https://", "ftp://", "mailto:")):
            if "://" not in url:
                url = "https://" + url
        
        # Remove multiple slashes (except after protocol)
        if "://" in url:
            protocol, rest = url.split("://", 1)
            rest = rest.replace("//", "/")
            url = protocol + "://" + rest
        
        return url
    
    def _set_nested_value(self, obj: Dict[str, Any], path: List, value: Any):
        """Set a value at a nested path in an object."""
        current = obj
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        if path:
            current[path[-1]] = value
    
    def _generate_validation_summary(self, total: int, valid: int, invalid: int, 
                                   errors: List[Dict[str, Any]], fixes: List[str]) -> str:
        """Generate a summary of validation results."""
        summary_parts = []
        
        summary_parts.append(f"Validation Results: {valid}/{total} objects passed validation")
        
        if invalid > 0:
            summary_parts.append(f"Invalid objects: {invalid} ({(invalid/total)*100:.1f}%)")
        
        if errors:
            # Summarize common error types
            error_types = {}
            for error in errors:
                validator = error.get("validator", "unknown")
                error_types[validator] = error_types.get(validator, 0) + 1
            
            summary_parts.append("Common validation errors:")
            for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                summary_parts.append(f"  - {error_type}: {count} occurrences")
        
        if fixes:
            summary_parts.append(f"Auto-fixes applied: {len(fixes)}")
            if len(fixes) <= 5:
                for fix in fixes:
                    summary_parts.append(f"  - {fix}")
            else:
                summary_parts.append("  - (Multiple fixes applied - see details)")
        
        if valid == total:
            summary_parts.append("✅ All objects are valid!")
        elif invalid == 0:
            summary_parts.append("✅ No validation errors found")
        else:
            summary_parts.append("⚠️ Some objects require attention")
        
        return "\n".join(summary_parts)