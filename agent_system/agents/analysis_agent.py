"""
Example agent implementations for common tasks.
"""

from typing import Any, Dict, List, Optional

from agent_system.core.agent import Agent
from agent_system.core.llm_api import LLMApi, LLMResponse
from agent_system.tools import CalculatorTool, WebSearchTool


class AnalysisAgent(Agent):
    """
    A flexible analysis agent that can be customized for different analysis tasks.
    """
    
    def __init__(
        self,
        llm_api: LLMApi,
        analysis_type: str = "general",
        timeout: float = 300.0,
        token_limit: int = 75000,
        identity: Optional[Dict[str, Any]] = None
    ):
        system_prompt = f"""
You are an analysis agent specialized in {analysis_type} analysis.

Available Tools:
{{% for tool in tools %}}
- {{{{ tool.name }}}}: {{{{ tool.short_description }}}}
  Input schema: {{{{ tool.input_schema }}}}
  Output schema: {{{{ tool.output_schema }}}}
{{% endfor %}}

Task: {{{{ task_description }}}}

Instructions:
1. Break down the analysis into logical steps
2. Use available tools to gather and process information
3. Provide detailed analysis with supporting evidence
4. Use tool calls in this format: {{"tool": "tool_name", "input": {{...}}}}
5. When analysis is complete, include "TASK_COMPLETE" in your response

{{% if result_schema %}}
Expected result format: {{{{ result_schema }}}}
{{% endif %}}
"""
        
        # Generic result schema for analysis
        result_schema = {
            "type": "object",
            "properties": {
                "analysis_type": {"type": "string", "description": "Type of analysis performed"},
                "findings": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key findings from the analysis"
                },
                "conclusion": {"type": "string", "description": "Overall conclusion"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1, "description": "Confidence in analysis"},
                "recommendations": {
                    "type": "array", 
                    "items": {"type": "string"},
                    "description": "Recommendations based on analysis"
                }
            },
            "required": ["analysis_type", "findings", "conclusion", "confidence"]
        }
        
        super().__init__(
            system_prompt=system_prompt,
            task_description="",
            llm_api=llm_api,
            timeout=timeout,
            token_limit=token_limit,
            result_schema=result_schema,
            identity=identity
        )
        
        self.analysis_type = analysis_type
    
    def _setup_agent(self) -> None:
        """Setup tools based on analysis type."""
        # Default tools for analysis
        tools = [CalculatorTool()]
        
        if self.analysis_type in ["research", "market", "competitive"]:
            tools.append(WebSearchTool())
            
        self.register_tools(tools)
    
    def _process_llm_response(self, response: LLMResponse) -> None:
        """Enhanced response processing for analysis tasks."""
        super()._process_llm_response(response)
        
        # Look for analysis patterns in the response
        if any(keyword in response.content.lower() for keyword in 
               ["conclude", "analysis shows", "findings indicate", "recommend"]):
            self._extract_analysis_result(response.content)
    
    def _extract_analysis_result(self, content: str) -> None:
        """Extract structured analysis results from LLM response."""
        # Simple pattern matching for analysis results
        findings = []
        recommendations = []
        
        # Extract findings
        if "findings:" in content.lower():
            findings_section = content.lower().split("findings:")[1].split("\n")[0:3]
            findings = [f.strip("- ").strip() for f in findings_section if f.strip()]
        
        # Extract recommendations  
        if "recommend" in content.lower():
            recommendations = ["Based on analysis, consider the findings above"]
        
        if findings:  # Only create result if we found some analysis
            result = {
                "analysis_type": self.analysis_type,
                "findings": findings,
                "conclusion": "Analysis completed based on available information",
                "confidence": 0.8,  # Default confidence
                "recommendations": recommendations
            }
            self.add_result(result)
    
    def analyze(self, task: str) -> Dict[str, Any]:
        """
        Perform analysis on the given task.
        
        Args:
            task: The analysis task description
            
        Returns:
            Dict containing analysis results and agent status
        """
        self.task_description = f"Perform {self.analysis_type} analysis: {task}"
        
        # Reset agent state
        self.conversation = []
        self.results = []
        self.is_complete = False
        self.total_tokens_used = 0
        self.start_time = None
        
        # Run the agent
        self.react_loop()
        
        return {
            "task": task,
            "analysis_type": self.analysis_type,
            "results": self.results,
            "status": self.get_status(),
            "conversation": [msg.model_dump() for msg in self.conversation]
        }