"""
Unit tests for the result aggregation tool.
"""

import pytest
from pydantic import ValidationError

from agent_system.tools import ResultAggregationTool
from agent_system.core import ToolExecutionError


class TestResultAggregationTool:
    """Test result aggregation tool functionality."""
    
    def test_tool_initialization(self):
        """Test tool initialization."""
        tool = ResultAggregationTool()
        assert tool.name == "result_aggregation"
        assert tool.alias == "result_aggregation"
        
    def test_tool_with_alias(self):
        """Test tool with custom alias."""
        tool = ResultAggregationTool(alias="custom_aggregation")
        assert tool.alias == "custom_aggregation"
    
    # Add specific tests based on the actual ResultAggregationTool implementation
    # These tests should be updated once we examine the tool's functionality