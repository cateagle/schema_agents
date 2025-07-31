"""
Base Tool class for the agent system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar, Generic
from pydantic import BaseModel, ValidationError
import logging

from agent_system.core.base_models import ToolConfig, ToolInputBase, ToolOutputBase
from agent_system.core.registry import register_exception

logger = logging.getLogger(__name__)

# Type variables for generic tool typing
TConfig = TypeVar('TConfig', bound=ToolConfig)
TInput = TypeVar('TInput', bound=ToolInputBase)
TOutput = TypeVar('TOutput', bound=ToolOutputBase)


class Tool(ABC, Generic[TConfig, TInput, TOutput]):
    """
    Base class for all tools that can be used by agents.
    
    Tools provide specific capabilities to agents and handle their own
    input/output validation through Pydantic models.
    
    Type Parameters:
        TConfig: The configuration model type (must inherit from ToolConfig)
        TInput: The input model type (must inherit from ToolInputBase)
        TOutput: The output model type (must inherit from ToolOutputBase)
    """
    
    def __init__(
        self,
        name: str,
        short_description: str,
        long_description: str,
        config: Optional[TConfig] = None,
        alias: Optional[str] = None
    ):
        """
        Initialize a tool.
        
        Args:
            name: The default name of the tool
            short_description: Brief description of what the tool does
            long_description: Detailed description of the tool's functionality
            config: Optional configuration object (must be a Pydantic model)
            alias: Optional alias for this tool instance (used when registering multiple instances)
        """
        self.name = name
        self.short_description = short_description
        self.long_description = long_description
        self.config = config or self._get_default_config()
        self.alias = alias or name
        
        # Validate config type
        if not isinstance(self.config, ToolConfig):
            raise TypeError(f"Config must be an instance of ToolConfig, got {type(self.config)}")
    
    @classmethod
    @abstractmethod
    def _get_config_class(cls) -> Type[TConfig]:
        """
        Return the configuration class for this tool.
        Must be implemented by subclasses.
        """
        pass
    
    @classmethod
    @abstractmethod
    def _get_input_class(cls) -> Type[TInput]:
        """
        Return the input model class for this tool.
        Must be implemented by subclasses.
        """
        pass
    
    @classmethod
    @abstractmethod
    def _get_output_class(cls) -> Type[TOutput]:
        """
        Return the output model class for this tool.
        Must be implemented by subclasses.
        """
        pass
    
    def _get_default_config(self) -> TConfig:
        """
        Get the default configuration for this tool.
        Can be overridden by subclasses to provide custom defaults.
        """
        config_class = self._get_config_class()
        return config_class()
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        """
        Returns the JSON schema for the tool's input.
        Automatically derived from the input Pydantic model.
        """
        input_class = self._get_input_class()
        return input_class.model_json_schema()
    
    @property
    def output_schema(self) -> Dict[str, Any]:
        """
        Returns the JSON schema for the tool's output.
        Automatically derived from the output Pydantic model.
        """
        output_class = self._get_output_class()
        return output_class.model_json_schema()
    
    @abstractmethod
    def _execute(self, input_data: TInput, identity: Optional[Dict[str, Any]] = None) -> TOutput:
        """
        Execute the tool with validated input.
        
        This method should be implemented by subclasses and work with the typed
        Pydantic models directly.
        
        Args:
            input_data: Validated input data as a Pydantic model
            identity: Identity information for permission checking
            
        Returns:
            Output data as a Pydantic model
            
        Raises:
            ToolExecutionError: If tool execution fails
        """
        pass
    
    def call(self, input_data: Dict[str, Any], identity: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the tool with the provided input.
        
        This method handles validation and conversion between dictionaries and
        Pydantic models, then delegates to _execute for the actual implementation.
        
        Args:
            input_data: Input data dictionary that must conform to input_schema
            identity: Identity information for permission checking (hidden from LLM)
            
        Returns:
            Output data dictionary that conforms to output_schema
            
        Raises:
            ValidationError: If input doesn't match schema
            ToolExecutionError: If tool execution fails
        """
        try:
            # Validate and parse input
            input_class = self._get_input_class()
            validated_input = input_class(**input_data)
            
            # Execute tool with validated input
            output = self._execute(validated_input, identity)
            
            # Validate output type
            output_class = self._get_output_class()
            if not isinstance(output, output_class):
                raise TypeError(f"Tool must return {output_class.__name__}, got {type(output)}")
            
            # Convert output to dictionary
            return output.model_dump()
            
        except ValidationError as e:
            logger.error(f"Tool '{self.alias}' input validation failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Tool '{self.alias}' execution failed: {str(e)}")
            if isinstance(e, ToolExecutionError):
                raise
            raise ToolExecutionError(f"Tool execution failed: {str(e)}")
    
    def get_tool_description(self) -> Dict[str, Any]:
        """
        Returns a complete description of the tool for the LLM.
        """
        return {
            "name": self.alias,  # Use alias in description
            "short_description": self.short_description,
            "long_description": self.long_description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema
        }
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for input validation."""
        return self.input_schema
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Get JSON schema for output."""
        return self.output_schema
    
    def get_example_input(self) -> Dict[str, Any]:
        """
        Generate example input based on schema.
        Uses field descriptions and defaults to create a meaningful example.
        """
        input_class = self._get_input_class()
        schema = input_class.model_json_schema()
        
        example = {}
        properties = schema.get("properties", {})
        required_fields = schema.get("required", [])
        
        for field_name, field_info in properties.items():
            # Generate example based on type and description
            field_type = field_info.get("type")
            field_description = field_info.get("description", "")
            
            if "default" in field_info:
                example[field_name] = field_info["default"]
            elif field_type == "string":
                if "enum" in field_info:
                    example[field_name] = field_info["enum"][0]
                elif "format" in field_info and field_info["format"] == "uri":
                    example[field_name] = "https://example.com"
                else:
                    example[field_name] = f"example_{field_name}"
            elif field_type == "integer":
                example[field_name] = 10
            elif field_type == "number":
                example[field_name] = 10.0
            elif field_type == "boolean":
                example[field_name] = True
            elif field_type == "array":
                items_type = field_info.get("items", {}).get("type", "string")
                if items_type == "string":
                    example[field_name] = ["item1", "item2"]
                else:
                    example[field_name] = []
            elif field_type == "object":
                example[field_name] = {}
            else:
                # For required fields without clear type, use a placeholder
                if field_name in required_fields:
                    example[field_name] = f"<{field_name}>"
        
        return example


@register_exception
class ToolExecutionError(Exception):
    """Exception raised when tool execution fails."""
    pass