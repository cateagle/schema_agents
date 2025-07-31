"""
Component registry for the agent system.

This module provides a centralized registry for all agent system components
including tools, agents, LLM APIs, and their associated models and exceptions.
"""

import inspect
from typing import Dict, Type, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
import logging

from agent_system.core.base_models import (
    ToolConfig, 
    ToolInputBase, 
    ToolOutputBase,
    AgentConfig,
    LLMApiConfig
)

logger = logging.getLogger(__name__)


@dataclass
class ComponentInfo:
    """Information about a registered component."""
    name: str
    component_type: str  # 'tool', 'agent', 'llm_api', etc.
    class_type: Type
    module_path: str
    description: Optional[str] = None
    associated_classes: Dict[str, Type] = None
    
    def __post_init__(self):
        if self.associated_classes is None:
            self.associated_classes = {}


class ComponentRegistry:
    """
    Central registry for all agent system components.
    
    Tracks tools, agents, LLM APIs and their associated configuration,
    input/output models, and exceptions.
    """
    
    def __init__(self):
        # Main component storage
        self._tools: Dict[str, ComponentInfo] = {}
        self._agents: Dict[str, ComponentInfo] = {}
        self._llm_apis: Dict[str, ComponentInfo] = {}
        
        # Model storage (configs, inputs, outputs)
        self._tool_configs: Dict[str, Type[ToolConfig]] = {}
        self._tool_inputs: Dict[str, Type[ToolInputBase]] = {}
        self._tool_outputs: Dict[str, Type[ToolOutputBase]] = {}
        
        self._agent_configs: Dict[str, Type[AgentConfig]] = {}
        self._llm_api_configs: Dict[str, Type[LLMApiConfig]] = {}
        
        # Exception storage
        self._exceptions: Dict[str, Type[Exception]] = {}
        
        # Track all registered class names for validation
        self._all_classes: Set[str] = set()
    
    # ========================================
    # Tool Registration
    # ========================================
    
    def register_tool(
        self, 
        tool_class: Type,
        config_class: Optional[Type[ToolConfig]] = None,
        input_class: Optional[Type[ToolInputBase]] = None,
        output_class: Optional[Type[ToolOutputBase]] = None,
        description: Optional[str] = None
    ) -> None:
        """
        Register a tool and its associated classes.
        
        Args:
            tool_class: The tool class to register
            config_class: The tool's configuration class
            input_class: The tool's input model class
            output_class: The tool's output model class
            description: Optional description of the tool
        """
        name = tool_class.__name__
        
        if name in self._all_classes:
            raise ValueError(f"Class '{name}' is already registered")
        
        # Create component info
        info = ComponentInfo(
            name=name,
            component_type="tool",
            class_type=tool_class,
            module_path=f"{tool_class.__module__}.{name}",
            description=description or tool_class.__doc__
        )
        
        # Register associated classes
        if config_class:
            info.associated_classes['config'] = config_class
            self._tool_configs[config_class.__name__] = config_class
            self._all_classes.add(config_class.__name__)
        
        if input_class:
            info.associated_classes['input'] = input_class
            self._tool_inputs[input_class.__name__] = input_class
            self._all_classes.add(input_class.__name__)
        
        if output_class:
            info.associated_classes['output'] = output_class
            self._tool_outputs[output_class.__name__] = output_class
            self._all_classes.add(output_class.__name__)
        
        self._tools[name] = info
        self._all_classes.add(name)
        logger.info(f"Registered tool: {name}")
    
    # ========================================
    # Agent Registration
    # ========================================
    
    def register_agent(
        self,
        agent_class: Type,
        config_class: Optional[Type[AgentConfig]] = None,
        description: Optional[str] = None
    ) -> None:
        """
        Register an agent and its configuration.
        
        Args:
            agent_class: The agent class to register
            config_class: The agent's configuration class
            description: Optional description of the agent
        """
        name = agent_class.__name__
        
        if name in self._all_classes:
            raise ValueError(f"Class '{name}' is already registered")
        
        info = ComponentInfo(
            name=name,
            component_type="agent",
            class_type=agent_class,
            module_path=f"{agent_class.__module__}.{name}",
            description=description or agent_class.__doc__
        )
        
        if config_class:
            info.associated_classes['config'] = config_class
            self._agent_configs[config_class.__name__] = config_class
            self._all_classes.add(config_class.__name__)
        
        self._agents[name] = info
        self._all_classes.add(name)
        logger.info(f"Registered agent: {name}")
    
    # ========================================
    # LLM API Registration
    # ========================================
    
    def register_llm_api(
        self,
        llm_api_class: Type,
        config_class: Optional[Type[LLMApiConfig]] = None,
        description: Optional[str] = None
    ) -> None:
        """
        Register an LLM API and its configuration.
        
        Args:
            llm_api_class: The LLM API class to register
            config_class: The API's configuration class
            description: Optional description of the API
        """
        name = llm_api_class.__name__
        
        if name in self._all_classes:
            raise ValueError(f"Class '{name}' is already registered")
        
        info = ComponentInfo(
            name=name,
            component_type="llm_api",
            class_type=llm_api_class,
            module_path=f"{llm_api_class.__module__}.{name}",
            description=description or llm_api_class.__doc__
        )
        
        if config_class:
            info.associated_classes['config'] = config_class
            self._llm_api_configs[config_class.__name__] = config_class
            self._all_classes.add(config_class.__name__)
        
        self._llm_apis[name] = info
        self._all_classes.add(name)
        logger.info(f"Registered LLM API: {name}")
    
    # ========================================
    # Exception Registration
    # ========================================
    
    def register_exception(self, exception_class: Type[Exception]) -> None:
        """Register an exception class."""
        name = exception_class.__name__
        
        if name in self._exceptions:
            logger.warning(f"Exception '{name}' is already registered, overwriting")
        
        self._exceptions[name] = exception_class
        self._all_classes.add(name)
        logger.info(f"Registered exception: {name}")
    
    # ========================================
    # Retrieval Methods
    # ========================================
    
    def get_tool(self, name: str) -> Optional[ComponentInfo]:
        """Get tool information by name."""
        return self._tools.get(name)
    
    def get_agent(self, name: str) -> Optional[ComponentInfo]:
        """Get agent information by name."""
        return self._agents.get(name)
    
    def get_llm_api(self, name: str) -> Optional[ComponentInfo]:
        """Get LLM API information by name."""
        return self._llm_apis.get(name)
    
    def get_all_tools(self) -> List[ComponentInfo]:
        """Get all registered tools."""
        return list(self._tools.values())
    
    def get_all_agents(self) -> List[ComponentInfo]:
        """Get all registered agents."""
        return list(self._agents.values())
    
    def get_all_llm_apis(self) -> List[ComponentInfo]:
        """Get all registered LLM APIs."""
        return list(self._llm_apis.values())
    
    def get_tool_models(self, tool_name: str) -> Dict[str, Type]:
        """Get all model classes associated with a tool."""
        tool_info = self._tools.get(tool_name)
        if not tool_info:
            return {}
        return tool_info.associated_classes.copy()
    
    def is_registered(self, class_name: str) -> bool:
        """Check if a class name is registered."""
        return class_name in self._all_classes
    
    # ========================================
    # Validation Methods
    # ========================================
    
    def validate_naming_conventions(self) -> List[str]:
        """
        Validate that all components follow naming conventions.
        
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check tool naming
        for name, info in self._tools.items():
            if not name.endswith('Tool'):
                errors.append(f"Tool class '{name}' should end with 'Tool'")
            
            # Check associated classes
            models = info.associated_classes
            if 'config' in models and not models['config'].__name__.endswith('Config'):
                errors.append(f"Tool config '{models['config'].__name__}' should end with 'Config'")
            if 'input' in models and not models['input'].__name__.endswith('Input'):
                errors.append(f"Tool input '{models['input'].__name__}' should end with 'Input'")
            if 'output' in models and not models['output'].__name__.endswith('Output'):
                errors.append(f"Tool output '{models['output'].__name__}' should end with 'Output'")
        
        # Check agent naming
        for name in self._agents:
            if not name.endswith('Agent'):
                errors.append(f"Agent class '{name}' should end with 'Agent'")
        
        # Check LLM API naming
        for name in self._llm_apis:
            if not name.endswith('LLMApi') and not name.endswith('Api'):
                errors.append(f"LLM API class '{name}' should end with 'LLMApi' or 'Api'")
        
        # Check exception naming
        for name in self._exceptions:
            if not name.endswith('Error') and not name.endswith('Exception'):
                errors.append(f"Exception class '{name}' should end with 'Error' or 'Exception'")
        
        return errors
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive report of all registered components."""
        return {
            "tools": {
                name: {
                    "module": info.module_path,
                    "description": info.description,
                    "config": info.associated_classes.get('config', {}).__name__ if 'config' in info.associated_classes else None,
                    "input": info.associated_classes.get('input', {}).__name__ if 'input' in info.associated_classes else None,
                    "output": info.associated_classes.get('output', {}).__name__ if 'output' in info.associated_classes else None
                }
                for name, info in self._tools.items()
            },
            "agents": {
                name: {
                    "module": info.module_path,
                    "description": info.description,
                    "config": info.associated_classes.get('config', {}).__name__ if 'config' in info.associated_classes else None
                }
                for name, info in self._agents.items()
            },
            "llm_apis": {
                name: {
                    "module": info.module_path,
                    "description": info.description,
                    "config": info.associated_classes.get('config', {}).__name__ if 'config' in info.associated_classes else None
                }
                for name, info in self._llm_apis.items()
            },
            "exceptions": list(self._exceptions.keys()),
            "total_components": len(self._all_classes)
        }


# Global registry instance
_registry = ComponentRegistry()


# ========================================
# Decorator Functions
# ========================================

def register_tool(
    config_class: Optional[Type[ToolConfig]] = None,
    input_class: Optional[Type[ToolInputBase]] = None,
    output_class: Optional[Type[ToolOutputBase]] = None,
    description: Optional[str] = None
):
    """
    Decorator to automatically register a tool class.
    
    Usage:
        @register_tool(
            config_class=MyToolConfig,
            input_class=MyToolInput,
            output_class=MyToolOutput
        )
        class MyTool(Tool):
            ...
    """
    def decorator(cls):
        _registry.register_tool(
            cls,
            config_class=config_class,
            input_class=input_class,
            output_class=output_class,
            description=description
        )
        return cls
    return decorator


def register_agent(
    config_class: Optional[Type[AgentConfig]] = None,
    description: Optional[str] = None
):
    """
    Decorator to automatically register an agent class.
    
    Usage:
        @register_agent(config_class=MyAgentConfig)
        class MyAgent(Agent):
            ...
    """
    def decorator(cls):
        _registry.register_agent(
            cls,
            config_class=config_class,
            description=description
        )
        return cls
    return decorator


def register_llm_api(
    config_class: Optional[Type[LLMApiConfig]] = None,
    description: Optional[str] = None
):
    """
    Decorator to automatically register an LLM API class.
    
    Usage:
        @register_llm_api(config_class=MyApiConfig)
        class MyLLMApi(LLMApi):
            ...
    """
    def decorator(cls):
        _registry.register_llm_api(
            cls,
            config_class=config_class,
            description=description
        )
        return cls
    return decorator


def register_exception(cls):
    """
    Decorator to automatically register an exception class.
    
    Usage:
        @register_exception
        class MyError(Exception):
            ...
    """
    _registry.register_exception(cls)
    return cls


# ========================================
# Public API
# ========================================

def get_registry() -> ComponentRegistry:
    """Get the global component registry."""
    return _registry


def discover_components(module) -> None:
    """
    Automatically discover and register components in a module.
    
    This function inspects a module and automatically registers any
    classes that inherit from Tool, Agent, or LLMApi.
    
    Args:
        module: The module to inspect for components
    """
    import inspect
    from agent_system.core.tool import Tool
    from agent_system.core.agent import Agent
    from agent_system.core.llm_api import LLMApi
    
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and obj.__module__ == module.__name__:
            # Skip base classes
            if obj in [Tool, Agent, LLMApi]:
                continue
            
            # Register based on inheritance
            if issubclass(obj, Tool) and obj != Tool:
                # Try to find associated classes
                config_class = None
                input_class = None
                output_class = None
                
                # Look for associated classes in the same module
                for attr_name, attr_obj in inspect.getmembers(module):
                    if inspect.isclass(attr_obj):
                        if attr_name == f"{obj.__name__[:-4]}Config":  # Remove 'Tool' suffix
                            config_class = attr_obj
                        elif attr_name == f"{obj.__name__[:-4]}Input":
                            input_class = attr_obj
                        elif attr_name == f"{obj.__name__[:-4]}Output":
                            output_class = attr_obj
                
                _registry.register_tool(
                    obj,
                    config_class=config_class,
                    input_class=input_class,
                    output_class=output_class
                )
            
            elif issubclass(obj, Agent) and obj != Agent:
                _registry.register_agent(obj)
            
            elif issubclass(obj, LLMApi) and obj != LLMApi:
                _registry.register_llm_api(obj)
            
            elif issubclass(obj, Exception):
                _registry.register_exception(obj)