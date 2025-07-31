"""
Math solver agent implementation.
"""

from typing import Any, Dict, List, Optional

from agent_system.core.agent import Agent
from agent_system.core.llm_api import LLMApi, LLMResponse
from agent_system.core.tool import Tool
from agent_system.core.registry import register_agent
from agent_system.tools import CalculatorTool, CalculatorConfig


# Default system prompt for math solving
DEFAULT_MATH_SYSTEM_PROMPT = """
You are a mathematical problem-solving agent. Your task is to solve mathematical problems step by step using the available tools.

{{tools_documentation}}

Instructions:
1. Break down complex problems into smaller steps
2. Use available tools for computations when needed
3. Show your reasoning process clearly
4. When you have a final answer, use the <RESULT> tag to return it
5. When the task is complete, include "TASK_COMPLETE" in your response

{% if result_schema %}
Expected result format: {{result_schema}}
{% endif %}
"""

# Default result schema for math problems
DEFAULT_MATH_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "problem": {"type": "string", "description": "Original problem statement"},
        "solution": {"type": "string", "description": "Step-by-step solution"},
        "answer": {"type": "number", "description": "Final numerical answer"},
        "steps": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of solution steps"
        }
    },
    "required": ["problem", "solution", "answer"]
}



@register_agent(description="An agent specialized in solving mathematical problems")
class MathSolverAgent(Agent):
    """
    An agent specialized in solving mathematical problems.
    
    This agent can be fully configured with custom tools, prompts, and schemas.
    By default, it includes a calculator tool and uses a math-focused prompt.
    """
    
    def __init__(
        self,
        llm_api: LLMApi,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Tool]] = None,
        result_schema: Optional[Dict[str, Any]] = None,
        timeout: float = 180.0,  # 3 minutes
        token_limit: int = 50000,
        max_tokens_per_response: int = 4000,
        identity: Optional[Dict[str, Any]] = None,
        task_description: str = ""
    ):
        """
        Initialize a math solver agent.
        
        Args:
            llm_api: The LLM API to use
            system_prompt: Custom system prompt (uses default if None)
            tools: List of tools to use (uses CalculatorTool if None)
            result_schema: Custom result schema (uses default if None)
            timeout: Maximum time for task completion
            token_limit: Maximum tokens to use
            max_tokens_per_response: Maximum tokens per LLM response
            identity: Identity information for tool access
            task_description: Initial task description
        """
        # Use defaults if not provided
        if system_prompt is None:
            system_prompt = DEFAULT_MATH_SYSTEM_PROMPT
        
        if tools is None:
            # Default to calculator tool with standard precision
            tools = [CalculatorTool(config=CalculatorConfig(precision=10))]
        
        if result_schema is None:
            result_schema = DEFAULT_MATH_RESULT_SCHEMA
        
        super().__init__(
            system_prompt=system_prompt,
            task_description=task_description,
            llm_api=llm_api,
            tools=tools,
            timeout=timeout,
            token_limit=token_limit,
            max_tokens_per_response=max_tokens_per_response,
            result_schema=result_schema,
            identity=identity
        )
    
    def _process_tool_result(self, tool_name: str, tool_result: Dict[str, Any]) -> None:
        """Process calculator results to extract mathematical solutions."""
        if tool_name == "calculator" and "result" in tool_result:
            # Look for patterns that indicate this might be a final answer
            conversation_text = " ".join([msg.content for msg in self.conversation[-5:]])
            
            if any(keyword in conversation_text.lower() for keyword in 
                   ["final", "answer", "solution", "result", "equals"]):
                
                # Try to construct a result object
                # Convert string result to number for schema validation
                try:
                    answer_num = float(tool_result["result"])
                except (ValueError, TypeError):
                    answer_num = 0.0
                
                result = {
                    "problem": self.task_description,
                    "solution": "Mathematical solution computed using calculator",
                    "answer": answer_num,
                    "steps": [f"Calculated: {tool_result['expression']} = {tool_result['result']}"]
                }
                self.add_result(result)
    
    def _is_task_complete(self, response: LLMResponse) -> bool:
        """Check if math problem is solved."""
        return (super()._is_task_complete(response) or
                "final answer" in response.content.lower() or
                "solution is" in response.content.lower())
    
    def solve_problem(self, problem: str) -> Dict[str, Any]:
        """
        Solve a specific mathematical problem.
        
        Args:
            problem: The mathematical problem to solve
            
        Returns:
            Dict containing the solution and agent status
        """
        self.task_description = f"Solve this mathematical problem: {problem}"
        
        # Reset agent state
        self.conversation = []
        self.results = []
        self.is_complete = False
        self.total_tokens_used = 0
        self.start_time = None
        
        # Run the agent
        self.react_loop()
        
        return {
            "problem": problem,
            "results": self.results,
            "status": self.get_status(),
            "conversation": [msg.model_dump() for msg in self.conversation]
        }
