"""
Core Agent class for the agent system.
"""

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from pydantic import BaseModel, ValidationError
import jsonschema
from jinja2 import Template
import logging

from agent_system.core.llm_api import LLMApi, Message, LLMResponse
from agent_system.core.tool import Tool, ToolExecutionError
from agent_system.core.parser import ResponseParser, ParseError
from agent_system.core.base_models import ToolConfig

logger = logging.getLogger(__name__)


@dataclass
class Agent:
    """
    Main agent class that executes tasks using LLM and tools.
    
    The agent follows a ReAct (Reasoning and Acting) loop, using tools
    to gather information and complete tasks while maintaining conversation
    history and managing token/time limits.
    """
    
    # Core configuration
    system_prompt: str
    task_description: str
    llm_api: LLMApi
    timeout: float = 300.0  # 5 minutes default
    token_limit: int = 100000
    max_tokens_per_response: int = 4000
    result_schema: Optional[Dict[str, Any]] = None
    identity: Optional[Dict[str, Any]] = None
    tools: Optional[List[Tool]] = None  # Tools can be provided at initialization
    
    # Runtime state (initialized after creation)
    conversation: List[Message] = field(default_factory=list, init=False)
    results: List[Dict[str, Any]] = field(default_factory=list, init=False)
    start_time: Optional[float] = field(default=None, init=False)
    total_tokens_used: int = field(default=0, init=False)
    is_complete: bool = field(default=False, init=False)
    
    # Tool introduction/removal templates
    TOOL_INTRODUCTION_TEMPLATE = """
NEW TOOL AVAILABLE: {{tool_name}}

Description: {{description}}
Alias: {{alias}}

Usage:
<TOOL>
{
    "tool": "{{alias}}",
    "input": {{input_example}}
}
</TOOL>

Input Schema:
{{input_schema}}

Required fields: {{required_fields}}
"""

    TOOL_REMOVAL_TEMPLATE = """
TOOL REMOVED: {{tool_name}}

The tool '{{alias}}' is no longer available. Do not attempt to use it.
"""
    
    def __post_init__(self):
        """Initialize agent after dataclass creation."""
        if self.identity is None:
            self.identity = {}
        
        # Initialize prompt templates
        self._system_prompt_template = Template(self.system_prompt)
        self._tool_introduction_template = Template(self.TOOL_INTRODUCTION_TEMPLATE)
        self._tool_removal_template = Template(self.TOOL_REMOVAL_TEMPLATE)
        
        # Track tool state for dynamic updates
        self._rendered_system_prompt = None  # Cache rendered prompt
        self._conversation_started = False  # Track if conversation has started
        
        # Initialize tools dictionary
        self._tools: Dict[str, Tool] = {}
        
        # Register initial tools if provided
        if self.tools:
            self.register_tools(self.tools)
        
        # Store original tools list for reference
        self._initial_tools = self.tools
        
        # Now tools is the internal dictionary
        self.tools = self._tools
        
        self._setup_agent()
    
    def _setup_agent(self) -> None:
        """Setup method called after initialization. Override in subclasses."""
        pass
    
    def register_tools(self, tools: List[Tool]) -> None:
        """
        Register a list of tools with the agent.
        
        Tools are registered by their alias, not their base name. This allows
        multiple instances of the same tool with different configurations.
        
        Args:
            tools: List of Tool instances to register
            
        Raises:
            ValueError: If multiple tools have the same alias
        """
        # Check for duplicate aliases
        aliases = [tool.alias for tool in tools]
        if len(aliases) != len(set(aliases)):
            # Find duplicates
            seen = set()
            duplicates = set()
            for alias in aliases:
                if alias in seen:
                    duplicates.add(alias)
                seen.add(alias)
            raise ValueError(f"Duplicate tool aliases found: {duplicates}. Each tool must have a unique alias.")
        
        # Register tools by alias
        # Use _tools if available (during __post_init__), otherwise use tools directly
        tools_dict = getattr(self, '_tools', None) if hasattr(self, '_tools') else self.tools
        if tools_dict is None:
            tools_dict = {}
            self.tools = tools_dict
        
        for tool in tools:
            if tool.alias in tools_dict:
                logger.warning(f"Tool '{tool.alias}' already registered, overwriting")
            tools_dict[tool.alias] = tool
            logger.info(f"Registered tool: {tool.alias} (type: {tool.__class__.__name__})")
            
            # If conversation has started, add introduction message
            if self._conversation_started and self.conversation:
                intro_msg = self._render_tool_introduction(tool)
                self.conversation.append(Message(role="system", content=intro_msg))
        
        # Invalidate cached prompt
        self._rendered_system_prompt = None
    
    def unregister_tool(self, tool_alias: str) -> None:
        """
        Unregister a tool from the agent.
        
        Args:
            tool_alias: The alias of the tool to remove
        """
        if tool_alias in self.tools:
            tool = self.tools[tool_alias]
            del self.tools[tool_alias]
            logger.info(f"Unregistered tool: {tool_alias}")
            
            # If conversation has started, add removal message
            if self._conversation_started and self.conversation:
                removal_msg = self._render_tool_removal(tool)
                self.conversation.append(Message(role="system", content=removal_msg))
            
            # Invalidate cached prompt
            self._rendered_system_prompt = None
        else:
            logger.warning(f"Attempted to unregister non-existent tool: {tool_alias}")
    
    def update_tool_config(self, tool_alias: str, new_config: ToolConfig) -> None:
        """
        Update the configuration of a registered tool.
        
        Args:
            tool_alias: The alias of the tool to update
            new_config: The new configuration for the tool
        """
        if tool_alias in self.tools:
            tool = self.tools[tool_alias]
            # Create new instance with updated config
            new_tool = tool.__class__(
                name=tool.name,
                short_description=tool.short_description,
                long_description=tool.long_description,
                config=new_config,
                alias=tool.alias
            )
            self.tools[tool_alias] = new_tool
            logger.info(f"Updated configuration for tool: {tool_alias}")
            
            # Invalidate cached prompt
            self._rendered_system_prompt = None
        else:
            raise ValueError(f"Tool '{tool_alias}' not found")
    
    def _render_tool_introduction(self, tool: Tool) -> str:
        """Render tool introduction message."""
        example_input = tool.get_example_input()
        input_schema = tool.get_input_schema()
        required_fields = input_schema.get("required", [])
        
        return self._tool_introduction_template.render(
            tool_name=tool.name,
            description=tool.long_description,
            alias=tool.alias,
            input_example=json.dumps(example_input, indent=4),
            input_schema=json.dumps(input_schema, indent=2),
            required_fields=", ".join(required_fields) if required_fields else "None"
        )
    
    def _render_tool_removal(self, tool: Tool) -> str:
        """Render tool removal message."""
        return self._tool_removal_template.render(
            tool_name=tool.name,
            alias=tool.alias
        )
    
    def _render_system_prompt(self) -> str:
        """Render the system prompt with available tools and task info."""
        # If already rendered and no changes, return cached version
        if self._rendered_system_prompt is not None:
            return self._rendered_system_prompt
        
        # Generate comprehensive tool documentation
        tools_documentation = self._generate_tools_documentation()
        
        # Render the system prompt with all context
        rendered_prompt = self._system_prompt_template.render(
            task_description=self.task_description,
            tools=list(self.tools.values()),
            tools_documentation=tools_documentation,
            result_schema=self.result_schema,
            identity=self.identity
        )
        
        # Cache the rendered prompt
        self._rendered_system_prompt = rendered_prompt
        return rendered_prompt
    
    def _generate_tools_documentation(self) -> str:
        """Generate comprehensive documentation for all tools."""
        if not self.tools:
            return "No tools are currently available."
        
        docs = ["## Available Tools\n"]
        docs.append("You have access to the following tools:\n")
        
        for tool in self.tools.values():
            # Get schemas and example
            input_schema = tool.get_input_schema()
            output_schema = tool.get_output_schema()
            example_input = tool.get_example_input()
            required_fields = input_schema.get("required", [])
            
            tool_doc = f"""
### Tool: {tool.alias}
**Name**: {tool.name}
**Description**: {tool.long_description}

**Usage**:
```
<TOOL>
{{
    "tool": "{tool.alias}",
    "input": {json.dumps(example_input, indent=4)}
}}
</TOOL>
```

**Input Schema**:
```json
{json.dumps(input_schema, indent=2)}
```

**Required Fields**: {", ".join(required_fields) if required_fields else "None"}
**Output**: {tool.short_description}
"""
            docs.append(tool_doc)
        
        return "\n".join(docs)
    
    def _check_timeout(self) -> bool:
        """Check if the agent has exceeded its timeout."""
        if self.start_time is None:
            return False
        return time.time() - self.start_time > self.timeout
    
    def _check_token_limit(self) -> bool:
        """Check if the agent has exceeded its token limit."""
        return self.total_tokens_used >= self.token_limit
    
    def _update_token_usage(self, response: LLMResponse) -> None:
        """Update token usage tracking."""
        if response.token_usage:
            tokens = response.token_usage.get('total_tokens', 0)
            self.total_tokens_used += tokens
        else:
            # Fallback estimation
            tokens = self.llm_api.get_token_count(response.content)
            self.total_tokens_used += tokens
    
    def _compact_conversation(self) -> None:
        """
        Compact conversation history to save tokens.
        Keeps system message, recent messages, and important results.
        """
        if len(self.conversation) <= 10:
            return
            
        # Keep system message and last 6 messages
        system_msgs = [msg for msg in self.conversation if msg.role == "system"]
        recent_msgs = self.conversation[-6:]
        
        # Create summary of older messages
        older_msgs = self.conversation[len(system_msgs):-6]
        if older_msgs:
            summary = f"[Earlier conversation summary: {len(older_msgs)} messages exchanged]"
            summary_msg = Message(role="system", content=summary)
            self.conversation = system_msgs + [summary_msg] + recent_msgs
            
        logger.info(f"Compacted conversation to {len(self.conversation)} messages")
    
    # ========================================
    # REACT LOOP STEP METHODS - Override these in subclasses
    # ========================================
    
    def _initialize_conversation(self) -> None:
        """Initialize conversation with system prompt and task. Override in subclasses."""
        # Render system prompt with current tools
        system_prompt = self._render_system_prompt()
        
        # Add instructions about the new tag format
        tag_instructions = """

IMPORTANT: When invoking tools or returning results, use the following XML-like tag format:

For tool calls:
<TOOL>
{
    "tool": "tool_name_or_alias",
    "input": {
        "param1": "value1",
        "param2": "value2"
    }
}
</TOOL>

You can make multiple tool calls in a single response. They will be executed in parallel when possible.

For structured results:
<RESULT>
{
    "key": "value",
    "another_key": "another_value"
}
</RESULT>

Always use proper JSON inside the tags. Tool names should match the registered tool aliases exactly as shown in the tool documentation above."""
        
        system_msg = Message(role="system", content=system_prompt + tag_instructions)
        self.conversation = [system_msg]
        
        # Add initial task message
        task_msg = Message(role="user", content=f"Please complete this task: {self.task_description}")
        self.conversation.append(task_msg)
        
        # Mark conversation as started for dynamic tool management
        self._conversation_started = True
    
    def _should_continue(self, iteration: int) -> bool:
        """Check if the agent should continue the loop. Override in subclasses."""
        max_iterations = 50  # Prevent infinite loops
        
        if iteration >= max_iterations:
            logger.warning(f"Maximum iterations ({max_iterations}) reached")
            return False
            
        if self.is_complete:
            return False
            
        if self._check_timeout():
            logger.warning("Agent timeout reached")
            return False
            
        if self._check_token_limit():
            logger.warning("Token limit reached")
            return False
            
        return True
    
    def _prepare_conversation(self) -> None:
        """Prepare conversation before LLM call. Override in subclasses."""
        # Compact conversation if getting too long
        conv_tokens = self.llm_api.get_conversation_token_count(self.conversation)
        if conv_tokens > self.max_tokens_per_response * 2:
            self._compact_conversation()
    
    def _get_llm_response(self) -> LLMResponse:
        """Get response from LLM. Override in subclasses for custom behavior."""
        response = self.llm_api.chat_completion(self.conversation)
        self._update_token_usage(response)
        return response
    
    def _process_llm_response(self, response: LLMResponse) -> None:
        """
        Process LLM response, extract results, and add to conversation.
        
        This method now also extracts any <RESULT> tags from the response
        and adds them to the agent's results.
        
        Args:
            response: The LLM response to process
        """
        # Add response to conversation
        self.conversation.append(Message(role="assistant", content=response.content))
        
        # Extract and process any results in the response
        self._extract_results_from_response(response)
        
        # Check if agent indicates completion
        if self._is_task_complete(response):
            self.is_complete = True
            logger.info("Agent indicated task completion")
    
    def _extract_results_from_response(self, response: LLMResponse) -> None:
        """
        Extract and validate results from <RESULT> tags in the response.
        
        Args:
            response: The LLM response that may contain result tags
        """
        try:
            results = ResponseParser.parse_results(response.content)
            for result in results:
                if self.add_result(result):
                    logger.info(f"Extracted and added result from response: {result}")
        except ParseError as e:
            logger.warning(f"Failed to parse results from response: {e}")
    
    def _is_task_complete(self, response: LLMResponse) -> bool:
        """Check if the task is complete based on LLM response. Override in subclasses."""
        return ("TASK_COMPLETE" in response.content)
    
    def _parse_tool_calls(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse tool calls from LLM response using the new tag-based format.
        
        Tool calls should be wrapped in <TOOL>...</TOOL> tags.
        
        Args:
            content: The LLM response content
            
        Returns:
            List of tool call dictionaries
        """
        try:
            return ResponseParser.parse_tool_calls(content)
        except ParseError as e:
            logger.warning(f"Failed to parse tool calls: {e}")
            return []
    
    def _execute_tools(self, response: LLMResponse) -> None:
        """
        Execute tools based on LLM response, supporting parallel execution.
        
        Multiple tool calls can be executed in parallel for better performance.
        Results are added to the conversation in the order they complete.
        
        Args:
            response: The LLM response containing tool calls
        """
        tool_calls = self._parse_tool_calls(response.content)
        
        if not tool_calls:
            print(f"🔧 [Agent] No tool calls found in response")
            return
        
        print(f"🔧 [Agent] Found {len(tool_calls)} tool call(s)")
        for i, call in enumerate(tool_calls):
            print(f"   🛠️ Tool {i+1}: {call.get('tool', 'unknown')} with input: {str(call.get('input', {}))[:100]}")
        
        # Execute tools in parallel if multiple calls
        if len(tool_calls) > 1:
            print(f"🔧 [Agent] Executing {len(tool_calls)} tools in parallel")
            self._execute_tools_parallel(tool_calls)
        else:
            print(f"🔧 [Agent] Executing 1 tool sequentially")
            # Single tool call - execute directly
            self._execute_tools_sequential(tool_calls)
    
    def _execute_tools_sequential(self, tool_calls: List[Dict[str, Any]]) -> None:
        """Execute tool calls sequentially (used for single tool or when parallel execution fails)."""
        for tool_call in tool_calls:
            try:
                tool_result = self._execute_single_tool(
                    tool_call["tool"], 
                    tool_call["input"]
                )
                
                # Add tool result to conversation
                result_msg = Message(
                    role="user", 
                    content=f"Tool '{tool_call['tool']}' result: {json.dumps(tool_result)}"
                )
                self.conversation.append(result_msg)
                
                # Process tool result for potential results
                self._process_tool_result(tool_call["tool"], tool_result)
                
            except ToolExecutionError as e:
                error_msg = Message(
                    role="user",
                    content=f"Tool '{tool_call['tool']}' execution error: {str(e)}"
                )
                self.conversation.append(error_msg)
    
    def _execute_tools_parallel(self, tool_calls: List[Dict[str, Any]]) -> None:
        """
        Execute multiple tool calls in parallel for better performance.
        
        Uses ThreadPoolExecutor to run tools concurrently. Results are collected
        as they complete and added to the conversation.
        
        Args:
            tool_calls: List of tool calls to execute
        """
        # Create a thread pool for parallel execution
        with ThreadPoolExecutor(max_workers=min(len(tool_calls), 5)) as executor:
            # Submit all tool executions
            future_to_tool = {}
            for tool_call in tool_calls:
                future = executor.submit(
                    self._execute_single_tool,
                    tool_call["tool"],
                    tool_call["input"]
                )
                future_to_tool[future] = tool_call
            
            # Process results as they complete
            for future in as_completed(future_to_tool):
                tool_call = future_to_tool[future]
                try:
                    tool_result = future.result()
                    
                    # Add tool result to conversation
                    result_msg = Message(
                        role="user", 
                        content=f"Tool '{tool_call['tool']}' result: {json.dumps(tool_result)}"
                    )
                    self.conversation.append(result_msg)
                    
                    # Process tool result for potential results
                    self._process_tool_result(tool_call["tool"], tool_result)
                    
                except Exception as e:
                    # Handle any execution errors
                    error_msg = Message(
                        role="user",
                        content=f"Tool '{tool_call['tool']}' execution error: {str(e)}"
                    )
                    self.conversation.append(error_msg)
                    logger.error(f"Tool '{tool_call['tool']}' failed in parallel execution: {str(e)}")
    
    def _execute_single_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single tool and return its output. Override in subclasses."""
        if tool_name not in self.tools:
            raise ToolExecutionError(f"Tool '{tool_name}' not found")
            
        tool = self.tools[tool_name]
        try:
            result = tool.call(tool_input, self.identity)
            logger.info(f"Tool '{tool_name}' executed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool '{tool_name}' execution failed: {str(e)}")
            raise ToolExecutionError(f"Tool execution failed: {str(e)}")
    
    def _process_tool_result(self, tool_name: str, tool_result: Dict[str, Any]) -> None:
        """Process tool result for potential agent results. Override in subclasses."""
        # Default implementation does nothing
        # Subclasses can override to extract structured results
        pass
    
    def _handle_error(self, error: Exception, iteration: int) -> None:
        """Handle errors during execution. Override in subclasses."""
        logger.error(f"Error in react loop iteration {iteration}: {str(error)}")
        error_msg = Message(
            role="user",
            content=f"System error: {str(error)}. Please continue or indicate completion."
        )
        self.conversation.append(error_msg)
    
    def _finalize_execution(self) -> None:
        """Finalize execution after loop ends. Override in subclasses."""
        self.deduplicate_results()
        
        iteration_count = len([msg for msg in self.conversation if msg.role == "assistant"])
        logger.info(f"Agent completed after {iteration_count} iterations")
        logger.info(f"Total tokens used: {self.total_tokens_used}")
        logger.info(f"Results generated: {len(self.results)}")
    
    # ========================================
    # MAIN REACT LOOP - Generally should not be overridden
    # ========================================
    
    def react_loop(self) -> None:
        """
        Main ReAct loop that runs until task completion, timeout, or token limit.
        This method orchestrates the step methods and should generally not be overridden.
        """
        self.start_time = time.time()
        
        # Initialize conversation
        self._initialize_conversation()
        
        iteration = 0
        print(f"🔄 [Agent] Starting react_loop with {len(self.tools)} tools available")
        
        while self._should_continue(iteration):
            iteration += 1
            print(f"🔄 [Agent] Iteration {iteration} - Results so far: {len(self.results)}")
            
            try:
                # Prepare conversation for LLM call
                self._prepare_conversation()
                
                # Get response from LLM
                response = self._get_llm_response()
                
                # Process LLM response
                self._process_llm_response(response)
                
                # Execute any tools requested
                self._execute_tools(response)
                
            except Exception as e:
                self._handle_error(e, iteration)
        
        print(f"🏁 [Agent] React loop completed after {iteration} iterations")
        print(f"📊 [Agent] Final results count: {len(self.results)}")
        print(f"✅ [Agent] Task completion status: {self.is_complete}")
        
        # Final cleanup
        self._finalize_execution()
    
    # ========================================
    # RUNTIME CONFIGURATION METHODS
    # ========================================
    
    def set_system_prompt(self, system_prompt: str) -> None:
        """
        Update the system prompt template at runtime.
        
        Args:
            system_prompt: New system prompt template (can use Jinja2 syntax)
        """
        self.system_prompt = system_prompt
        self._system_prompt_template = Template(system_prompt)
        self._rendered_system_prompt = None  # Invalidate cache
        logger.info("System prompt updated")
    
    def set_result_schema(self, result_schema: Optional[Dict[str, Any]]) -> None:
        """
        Update the expected result schema at runtime.
        
        Args:
            result_schema: JSON schema for validating results, or None to disable validation
        """
        self.result_schema = result_schema
        logger.info(f"Result schema updated: {result_schema is not None}")
    
    def set_task_description(self, task_description: str) -> None:
        """
        Update the task description.
        
        Args:
            task_description: New task description
        """
        self.task_description = task_description
        logger.info("Task description updated")
    
    
    def update_tool_config(self, tool_alias: str, new_config: ToolConfig) -> bool:
        """
        Update the configuration of an existing tool.
        
        Note: This creates a new instance of the tool with the new config,
        as tool configs are immutable.
        
        Args:
            tool_alias: The alias of the tool to update
            new_config: The new configuration for the tool
            
        Returns:
            True if tool was updated, False if tool was not found
        """
        if tool_alias not in self.tools:
            logger.warning(f"Tool '{tool_alias}' not found for config update")
            return False
        
        old_tool = self.tools[tool_alias]
        tool_class = old_tool.__class__
        
        try:
            # Create new instance with same alias but new config
            new_tool = tool_class(config=new_config, alias=tool_alias)
            self.tools[tool_alias] = new_tool
            logger.info(f"Updated configuration for tool: {tool_alias}")
            return True
        except Exception as e:
            logger.error(f"Failed to update tool config: {e}")
            return False
    
    def get_tool_config(self, tool_alias: str) -> Optional[ToolConfig]:
        """
        Get the current configuration of a tool.
        
        Args:
            tool_alias: The alias of the tool
            
        Returns:
            The tool's configuration, or None if tool not found
        """
        if tool_alias in self.tools:
            return self.tools[tool_alias].config
        return None
    
    def list_tools(self) -> List[Dict[str, str]]:
        """
        List all registered tools with their aliases and types.
        
        Returns:
            List of dictionaries with 'alias' and 'type' keys
        """
        return [
            {
                "alias": alias,
                "type": tool.__class__.__name__,
                "description": tool.short_description
            }
            for alias, tool in self.tools.items()
        ]
    
    def reset_conversation(self) -> None:
        """
        Reset the conversation history while keeping tools and configuration.
        
        This is useful when you want to start a new task with the same agent setup.
        """
        self.conversation = []
        self.results = []
        self.is_complete = False
        self.total_tokens_used = 0
        self.start_time = None
        self._conversation_started = False
        
        # Reinitialize conversation with system prompt
        self._initialize_conversation()
        
        logger.info("Conversation and results reset")
    
    # ========================================
    # RESULT MANAGEMENT METHODS
    # ========================================
    
    def _validate_result(self, result: Dict[str, Any]) -> bool:
        """Validate a result against the result schema."""
        if not self.result_schema:
            return True
            
        try:
            jsonschema.validate(result, self.result_schema)
            return True
        except jsonschema.ValidationError as e:
            logger.warning(f"Result validation failed: {str(e)}")
            return False
    
    def add_result(self, result: Dict[str, Any]) -> bool:
        """Add a validated result to the results list."""
        if self._validate_result(result):
            self.results.append(result)
            logger.info(f"Added result: {result}")
            print(f"✅ [Agent] Result added successfully (total: {len(self.results)})")
            print(f"   📄 Result preview: {str(result)[:150]}{'...' if len(str(result)) > 150 else ''}")
            return True
        else:
            print(f"❌ [Agent] Result validation failed - not added")
            print(f"   📄 Failed result: {str(result)[:150]}{'...' if len(str(result)) > 150 else ''}")
        return False
    
    def deduplicate_results(self) -> None:
        """Remove duplicate results (simple exact match for now)."""
        unique_results = []
        seen = set()
        
        for result in self.results:
            result_str = json.dumps(result, sort_keys=True)
            if result_str not in seen:
                seen.add(result_str)
                unique_results.append(result)
                
        removed_count = len(self.results) - len(unique_results)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} duplicate results")
            self.results = unique_results
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the agent."""
        runtime = 0
        if self.start_time:
            runtime = time.time() - self.start_time
            
        return {
            "is_complete": self.is_complete,
            "runtime_seconds": runtime,
            "total_tokens_used": self.total_tokens_used,
            "conversation_length": len(self.conversation),
            "results_count": len(self.results),
            "tools_registered": len(self.tools)
        }



# I want to be able to inherit from this class and override the methods for the ReAct loop steps.
# Subclasses should implement the specific logic for their tasks while using the core loop.
# Main Things to notice:
# - Every response can have multiple json objects for tool calls or results. We should parse them by getting things sections like <TOOL>...</TOOL> and <RESULT>...</RESULT> while multiple results and tools are allowed per response. Using this will allow us to have multiple tool calls and results per response.
# - all agents that are inherited from this class should not be completely hard coded. Instead, they should be able to be given additional tools and result types at run time or during initialization. We should also be able to remove tools during runtime.
# - The system prompt template will be given to the agent during initialization, but a default template can be given that will be used if none is provided.
# - during initialization, I want to be able to add all the parameters of the agent to configure it. It should also be able to accept a custom parameter dictionary to get additional parameters for the templates.