"""
Base models for the agent system.

This module provides base Pydantic models that all tools, agents, and LLM APIs
should inherit from for consistency and type safety.
"""

from abc import ABC
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class ToolConfig(BaseModel):
    """
    Base configuration class for all tools.
    
    Tools should inherit from this class to define their configuration parameters.
    All configuration should be immutable after initialization.
    """
    model_config = ConfigDict(frozen=True, extra="forbid")


class ToolInputBase(BaseModel):
    """
    Base class for all tool inputs.
    
    All tool input models should inherit from this class.
    This ensures consistent validation and serialization.
    """
    model_config = ConfigDict(extra="forbid")


class ToolOutputBase(BaseModel):
    """
    Base class for all tool outputs.
    
    All tool output models should inherit from this class.
    This ensures consistent validation and serialization.
    """
    model_config = ConfigDict(extra="forbid")


class AgentConfig(BaseModel):
    """
    Base configuration class for agents.
    
    Agents can use this for additional configuration beyond the standard parameters.
    """
    model_config = ConfigDict(frozen=True, extra="forbid")


class LLMApiConfig(BaseModel):
    """
    Base configuration class for LLM APIs.
    
    All LLM API implementations should use a config that inherits from this.
    """
    model_config = ConfigDict(frozen=True, extra="allow")  # LLM configs might need flexibility