"""
Agent System Core Module

This module provides the core components for the agent system:
- Agent: The main agent class that executes tasks
- LLMApi: Interface for LLM API providers
- Tool: Base class for agent tools
- Base models: Pydantic models for configuration and data validation
- Parser: Tag-based parser for tool calls and results
"""

from agent_system.core.agent import Agent
from agent_system.core.llm_api import LLMApi, LLMResponse, Message, LLMApiError
from agent_system.core.tool import Tool, ToolExecutionError
from agent_system.core.base_models import (
    ToolConfig, 
    ToolInputBase, 
    ToolOutputBase,
    AgentConfig,
    LLMApiConfig
)
from agent_system.core.parser import ResponseParser, ParseError
from agent_system.core.registry import (
    get_registry,
    ComponentRegistry,
    ComponentInfo,
    register_tool,
    register_agent,
    register_llm_api,
    register_exception,
    discover_components
)

__all__ = [
    # Core classes
    "Agent", 
    "LLMApi", 
    "Tool",
    # LLM API related
    "LLMResponse",
    "Message",
    "LLMApiError",
    # Tool related
    "ToolExecutionError",
    # Base models
    "ToolConfig",
    "ToolInputBase",
    "ToolOutputBase",
    "AgentConfig",
    "LLMApiConfig",
    # Parser
    "ResponseParser",
    "ParseError",
    # Registry
    "get_registry",
    "ComponentRegistry",
    "ComponentInfo",
    "register_tool",
    "register_agent",
    "register_llm_api",
    "register_exception",
    "discover_components"
]