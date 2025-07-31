"""
Tools module for the agent system.

This module contains various tools that agents can use to complete tasks.
"""

from agent_system.tools.calculator_tool import (
    CalculatorTool,
    CalculatorConfig,
    CalculatorInput,
    CalculatorOutput
)
from agent_system.tools.web_search_tool import (
    WebSearchTool,
    WebSearchConfig,
    WebSearchInput,
    WebSearchOutput,
    WebSearchResult
)

# Research coordination tools
from agent_system.tools.json_analysis_tool import (
    JSONAnalysisTool,
    JSONAnalysisConfig,
    JSONAnalysisInput,
    JSONAnalysisOutput
)
from agent_system.tools.research_trigger_tool import (
    ResearchTriggerTool,
    ResearchTriggerConfig,
    ResearchTriggerInput,
    ResearchTriggerOutput
)
from agent_system.tools.result_validation_tool import (
    ResultValidationTool,
    ResultValidationConfig,
    ResultValidationInput,
    ResultValidationOutput
)
from agent_system.tools.result_aggregation_tool import (
    ResultAggregationTool,
    ResultAggregationConfig,
    ResultAggregationInput,
    ResultAggregationOutput
)

__all__ = [
    # Calculator Tool
    "CalculatorTool",
    "CalculatorConfig",
    "CalculatorInput", 
    "CalculatorOutput",
    # Web Search Tool
    "WebSearchTool",
    "WebSearchConfig",
    "WebSearchInput",
    "WebSearchOutput",
    "WebSearchResult",
    # Research coordination tools
    "JSONAnalysisTool",
    "JSONAnalysisConfig",
    "JSONAnalysisInput",
    "JSONAnalysisOutput",
    "ResearchTriggerTool",
    "ResearchTriggerConfig",
    "ResearchTriggerInput",
    "ResearchTriggerOutput",
    "ResultValidationTool",
    "ResultValidationConfig",
    "ResultValidationInput",
    "ResultValidationOutput",
    "ResultAggregationTool",
    "ResultAggregationConfig",
    "ResultAggregationInput",
    "ResultAggregationOutput"
]