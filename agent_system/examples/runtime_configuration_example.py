#!/usr/bin/env python3
"""
Example demonstrating runtime configuration of agents.

This example shows how to:
1. Create agents with custom configurations
2. Register multiple tool instances with different configs
3. Modify agent settings at runtime
4. Update tool configurations dynamically
"""

from typing import Dict, Any

from agent_system.core import Agent
from agent_system.llm_apis import MockLLMApi
from agent_system.tools import (
    CalculatorTool, 
    CalculatorConfig,
    WebSearchTool,
    WebSearchConfig
)
from agent_system.agents import MathSolverAgent, ResearchAgent


def example_multiple_tool_instances():
    """Example: Using multiple instances of the same tool with different configs."""
    print("\n=== Example 1: Multiple Tool Instances ===\n")
    
    # Create LLM API
    llm_api = MockLLMApi({"response_delay": 0.1})
    
    # Create agent with multiple calculator instances
    agent = Agent(
        system_prompt="You are a precision calculation assistant with multiple calculators.",
        task_description="Perform calculations with different precision levels",
        llm_api=llm_api,
        tools=[
            CalculatorTool(
                config=CalculatorConfig(precision=2),
                alias="calc_low"
            ),
            CalculatorTool(
                config=CalculatorConfig(precision=10),
                alias="calc_high"
            ),
            CalculatorTool(
                config=CalculatorConfig(precision=50),
                alias="calc_ultra"
            )
        ]
    )
    
    # List available tools
    print("Available tools:")
    for tool_info in agent.list_tools():
        print(f"  - {tool_info['alias']}: {tool_info['description']}")
    
    # Get tool configurations
    print("\nTool configurations:")
    for alias in ["calc_low", "calc_high", "calc_ultra"]:
        config = agent.get_tool_config(alias)
        print(f"  - {alias}: precision={config.precision}")


def example_runtime_modification():
    """Example: Modifying agent configuration at runtime."""
    print("\n=== Example 2: Runtime Modification ===\n")
    
    # Create a basic math agent
    llm_api = MockLLMApi({"response_delay": 0.1})
    agent = MathSolverAgent(llm_api=llm_api)
    
    print("Initial configuration:")
    print(f"  - Tools: {[t['alias'] for t in agent.list_tools()]}")
    print(f"  - Task: '{agent.task_description}'")
    
    # Add a web search tool at runtime
    agent.register_tools([
        WebSearchTool(
            config=WebSearchConfig(
                search_engine="mock",
                region="us-en"
            ),
            alias="research_tool"
        )
    ])
    
    print("\nAfter adding web search:")
    print(f"  - Tools: {[t['alias'] for t in agent.list_tools()]}")
    
    # Update task description
    agent.set_task_description("Research mathematical concepts and solve problems")
    print(f"  - New task: '{agent.task_description}'")
    
    # Update system prompt
    new_prompt = """
You are an advanced mathematical research assistant capable of both calculations and web research.

Available Tools:
{% for tool in tools %}
- {{ tool.name }}: {{ tool.short_description }}
{% endfor %}

Task: {{ task_description }}

Use both calculation and research tools to provide comprehensive answers.
"""
    agent.set_system_prompt(new_prompt)
    print("  - System prompt updated")
    
    # Update tool configuration
    new_calc_config = CalculatorConfig(precision=20)
    agent.update_tool_config("calculator", new_calc_config)
    print(f"  - Calculator precision updated to: {agent.get_tool_config('calculator').precision}")


def example_custom_agent():
    """Example: Creating a fully custom agent."""
    print("\n=== Example 3: Custom Agent Configuration ===\n")
    
    # Create LLM API
    llm_api = MockLLMApi({"response_delay": 0.1})
    
    # Custom system prompt
    custom_prompt = """
You are a data analysis agent that can perform calculations and research.

Tools available:
{% for tool in tools %}
- {{ tool.name }}: {{ tool.short_description }}
{% endfor %}

Task: {{ task_description }}

Focus on:
1. Statistical calculations
2. Data interpretation
3. Research for context

Return results using <RESULT> tags.
"""
    
    # Custom result schema
    custom_schema = {
        "type": "object",
        "properties": {
            "analysis_type": {"type": "string"},
            "calculations": {"type": "array", "items": {"type": "object"}},
            "interpretation": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1}
        },
        "required": ["analysis_type", "interpretation"]
    }
    
    # Create agent with custom everything
    agent = Agent(
        system_prompt=custom_prompt,
        task_description="Analyze statistical data",
        llm_api=llm_api,
        tools=[
            CalculatorTool(
                config=CalculatorConfig(precision=15),
                alias="stats_calc"
            ),
            WebSearchTool(
                config=WebSearchConfig(
                    search_engine="mock",
                    region="academic"
                ),
                alias="research"
            )
        ],
        result_schema=custom_schema,
        timeout=300.0,
        token_limit=50000
    )
    
    print("Custom agent created with:")
    print(f"  - Tools: {[t['alias'] for t in agent.list_tools()]}")
    print(f"  - Custom result schema: {list(custom_schema['properties'].keys())}")
    print(f"  - Timeout: {agent.timeout}s")
    print(f"  - Token limit: {agent.token_limit}")


def example_dynamic_tool_management():
    """Example: Dynamic tool management during agent lifecycle."""
    print("\n=== Example 4: Dynamic Tool Management ===\n")
    
    # Create research agent
    llm_api = MockLLMApi({"response_delay": 0.1})
    agent = ResearchAgent(llm_api=llm_api)
    
    print("Initial tools:")
    for tool in agent.list_tools():
        print(f"  - {tool['alias']}: {tool['type']}")
    
    # Add specialized search tools
    agent.register_tools([
        WebSearchTool(
            config=WebSearchConfig(search_engine="mock", region="academic"),
            alias="academic_search"
        ),
        WebSearchTool(
            config=WebSearchConfig(search_engine="mock", region="news"),
            alias="news_search"
        )
    ])
    
    print("\nAfter adding specialized tools:")
    for tool in agent.list_tools():
        print(f"  - {tool['alias']}: {tool['type']}")
    
    # Remove the default search
    agent.unregister_tool("web_search")
    
    print("\nAfter removing default search:")
    for tool in agent.list_tools():
        print(f"  - {tool['alias']}: {tool['type']}")
    
    # Reset for a new task
    agent.reset_conversation()
    agent.set_task_description("Research recent developments in AI")
    print(f"\nReset for new task: '{agent.task_description}'")


if __name__ == "__main__":
    print("Agent System Runtime Configuration Examples")
    print("=" * 50)
    
    # Run all examples
    example_multiple_tool_instances()
    example_runtime_modification()
    example_custom_agent()
    example_dynamic_tool_management()
    
    print("\n" + "=" * 50)
    print("Examples completed!")