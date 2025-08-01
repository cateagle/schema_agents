"""
Unit tests for the JSON analysis tool.
"""

import pytest
from pydantic import ValidationError

from agent_system.tools import JSONAnalysisTool
from agent_system.core import ToolExecutionError


class TestJSONAnalysisTool:
    """Test JSON analysis tool functionality."""
    
    def test_tool_initialization(self):
        """Test tool initialization."""
        tool = JSONAnalysisTool()
        assert tool.name == "json_analysis"
        assert tool.alias == "json_analysis"
        
    def test_tool_with_alias(self):
        """Test tool with custom alias."""
        tool = JSONAnalysisTool(alias="custom_json")
        assert tool.alias == "custom_json"
    
    # Add specific tests based on the actual JsonAnalysisTool implementation
    # These tests should be updated once we examine the tool's functionality