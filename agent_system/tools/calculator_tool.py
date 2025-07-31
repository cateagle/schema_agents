"""
Calculator tool for mathematical computations.
"""

from typing import Any, Dict, Optional, Type
from pydantic import Field
import math
import logging

from agent_system.core.tool import Tool, ToolExecutionError
from agent_system.core.base_models import ToolConfig, ToolInputBase, ToolOutputBase
from agent_system.core.registry import register_tool

logger = logging.getLogger(__name__)


class CalculatorConfig(ToolConfig):
    """Configuration for the calculator tool."""
    precision: int = Field(default=10, description="Number of decimal places for results")
    allow_complex: bool = Field(default=False, description="Whether to allow complex number operations")


class CalculatorInput(ToolInputBase):
    """Input schema for calculator tool."""
    expression: str = Field(..., description="Mathematical expression to evaluate")


class CalculatorOutput(ToolOutputBase):
    """Output schema for calculator tool."""
    result: str = Field(..., description="Result of the calculation")
    expression: str = Field(..., description="Original expression")


@register_tool(
    config_class=CalculatorConfig,
    input_class=CalculatorInput,
    output_class=CalculatorOutput,
    description="A calculator tool for evaluating mathematical expressions"
)
class CalculatorTool(Tool[CalculatorConfig, CalculatorInput, CalculatorOutput]):
    """
    A simple calculator tool that can evaluate mathematical expressions.
    
    This tool safely evaluates mathematical expressions using a restricted set
    of allowed functions and operators.
    """
    
    def __init__(
        self, 
        config: Optional[CalculatorConfig] = None,
        alias: Optional[str] = None
    ):
        """
        Initialize the calculator tool.
        
        Args:
            config: Optional configuration for the calculator
            alias: Optional alias for this tool instance
        """
        super().__init__(
            name="calculator",
            short_description="Performs mathematical calculations",
            long_description="Evaluates mathematical expressions safely. Supports basic arithmetic, parentheses, and common math functions like sin, cos, sqrt, etc.",
            config=config,
            alias=alias
        )
    
    @classmethod
    def _get_config_class(cls) -> Type[CalculatorConfig]:
        return CalculatorConfig
    
    @classmethod
    def _get_input_class(cls) -> Type[CalculatorInput]:
        return CalculatorInput
    
    @classmethod
    def _get_output_class(cls) -> Type[CalculatorOutput]:
        return CalculatorOutput
    
    def _execute(self, input_data: CalculatorInput, identity: Optional[Dict[str, Any]] = None) -> CalculatorOutput:
        """
        Execute the calculator with validated input.
        
        Args:
            input_data: Validated calculator input
            identity: Not used by this tool
            
        Returns:
            CalculatorOutput with the result
            
        Raises:
            ToolExecutionError: If evaluation fails
        """
        # Safe evaluation - only allow specific functions and operators
        allowed_names = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "log10": math.log10,
            "exp": math.exp,
            "pi": math.pi,
            "e": math.e,
        }
        
        # Remove any potential dangerous functions
        expression = input_data.expression.replace("__", "").replace("import", "")
        
        try:
            # Evaluate expression safely
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            
            # Ensure result is a number
            if not isinstance(result, (int, float)):
                raise ValueError("Expression must evaluate to a number")
            
            # Apply precision from config and format as string
            if self.config.precision is not None:
                result = round(float(result), self.config.precision)
                result_str = f"{result:.{self.config.precision}f}"
            else:
                result_str = str(float(result))
            
            return CalculatorOutput(
                result=result_str,
                expression=input_data.expression
            )
            
        except Exception as e:
            raise ToolExecutionError(f"Math evaluation failed: {str(e)}")