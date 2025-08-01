"""
Unit tests for the calculator tool.
"""

import pytest
from pydantic import ValidationError

from agent_system.tools import CalculatorTool, CalculatorConfig, CalculatorInput, CalculatorOutput
from agent_system.core import ToolExecutionError


class TestCalculatorTool:
    """Test calculator tool functionality."""
    
    def test_default_configuration(self):
        """Test calculator with default configuration."""
        tool = CalculatorTool()
        assert tool.name == "calculator"
        assert tool.config.precision == 10
        assert tool.config.allow_complex == False
        assert tool.alias == "calculator"
    
    def test_custom_configuration(self):
        """Test calculator with custom configuration."""
        config = CalculatorConfig(precision=5, allow_complex=True)
        tool = CalculatorTool(config=config, alias="custom_calc")
        
        assert tool.config.precision == 5
        assert tool.config.allow_complex == True
        assert tool.alias == "custom_calc"
    
    def test_basic_arithmetic(self):
        """Test basic arithmetic operations."""
        tool = CalculatorTool()
        
        # Addition
        result = tool.call({"expression": "2 + 3"})
        assert result["result"] == "5.0000000000"
        
        # Subtraction
        result = tool.call({"expression": "10 - 4"})
        assert result["result"] == "6.0000000000"
        
        # Multiplication
        result = tool.call({"expression": "6 * 7"})
        assert result["result"] == "42.0000000000"
        
        # Division
        result = tool.call({"expression": "15 / 3"})
        assert result["result"] == "5.0000000000"
    
    def test_complex_expressions(self):
        """Test complex mathematical expressions."""
        tool = CalculatorTool()
        
        # Order of operations
        result = tool.call({"expression": "2 + 3 * 4"})
        assert result["result"] == "14.0000000000"
        
        # Parentheses
        result = tool.call({"expression": "(2 + 3) * 4"})
        assert result["result"] == "20.0000000000"
        
        # Power
        result = tool.call({"expression": "2 ** 3"})
        assert result["result"] == "8.0000000000"
    
    def test_precision_settings(self):
        """Test different precision settings."""
        # High precision
        high_precision = CalculatorTool(config=CalculatorConfig(precision=15))
        result = high_precision.call({"expression": "1 / 3"})
        assert len(result["result"].split(".")[1]) >= 15
        
        # Low precision
        low_precision = CalculatorTool(config=CalculatorConfig(precision=2))
        result = low_precision.call({"expression": "1 / 3"})
        expected_length = 2  # "0.33" after decimal
        actual_length = len(result["result"].split(".")[1])
        assert actual_length == expected_length
    
    def test_mathematical_functions(self):
        """Test mathematical functions."""
        tool = CalculatorTool()
        
        # Square root
        result = tool.call({"expression": "sqrt(16)"})
        assert result["result"] == "4.0000000000"
        
        # Sine
        result = tool.call({"expression": "sin(0)"})
        assert result["result"] == "0.0000000000"
        
        # Natural log
        result = tool.call({"expression": "log(1)"})
        assert result["result"] == "0.0000000000"
    
    def test_invalid_expressions(self):
        """Test handling of invalid expressions."""
        tool = CalculatorTool()
        
        # Division by zero
        with pytest.raises(ToolExecutionError):
            tool.call({"expression": "1 / 0"})
        
        # Invalid syntax
        with pytest.raises(ToolExecutionError):
            tool.call({"expression": "2 +"})
        
        # Undefined variable
        with pytest.raises(ToolExecutionError):
            tool.call({"expression": "x + 1"})
    
    def test_input_validation(self):
        """Test input validation."""
        tool = CalculatorTool()
        
        # Valid input
        result = tool.call({"expression": "1 + 1"})
        assert "result" in result
        
        # Missing expression
        with pytest.raises(ValidationError):
            tool.call({})
        
        # Wrong type
        with pytest.raises(ValidationError):
            tool.call({"expression": 123})  # Should be string
        
        # Extra fields
        with pytest.raises(ValidationError):
            tool.call({"expression": "1 + 1", "extra_field": "value"})