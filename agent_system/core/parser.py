"""
Parser module for extracting structured data from agent responses.

This module provides functionality to parse tool calls and results from
agent responses using XML-like tags.
"""

import json
import re
from typing import List, Dict, Any, Tuple, Optional
import logging

from agent_system.core.registry import register_exception

logger = logging.getLogger(__name__)


@register_exception
class ParseError(Exception):
    """Exception raised when parsing fails."""
    pass


class ResponseParser:
    """
    Parser for extracting tool calls and results from agent responses.
    
    Supports parsing:
    - <TOOL>...</TOOL> tags for tool invocations
    - <RESULT>...</RESULT> tags for structured results
    """
    
    # Regex patterns for tag extraction
    # Original patterns - we'll handle nested tags differently
    TOOL_PATTERN = re.compile(r'<TOOL>(.*?)</TOOL>', re.DOTALL)
    RESULT_PATTERN = re.compile(r'<RESULT>(.*?)</RESULT>', re.DOTALL)
    
    @classmethod
    def _extract_json_between_tags(cls, content: str, start_tag: str, end_tag: str) -> List[str]:
        """
        Extract JSON content between tags, handling nested tags in strings correctly.
        
        This method finds matching tag pairs and extracts valid JSON between them.
        """
        results = []
        start_pos = 0
        
        while True:
            # Find next start tag
            start_idx = content.find(start_tag, start_pos)
            if start_idx == -1:
                break
                
            # Start looking for JSON after the start tag
            json_start = start_idx + len(start_tag)
            
            # Find the matching end tag by counting braces
            brace_count = 0
            in_string = False
            escape_next = False
            json_end = json_start
            
            for i in range(json_start, len(content)):
                char = content[i]
                
                # Handle string escaping
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\':
                    escape_next = True
                    continue
                
                # Track if we're inside a JSON string
                if char == '"' and not escape_next:
                    in_string = not in_string
                
                # Only count braces outside of strings
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        
                        # If we've closed all braces, we found the end of JSON
                        if brace_count == 0 and i > json_start:
                            json_end = i + 1
                            # Now find the end tag
                            end_idx = content.find(end_tag, json_end)
                            if end_idx != -1:
                                json_content = content[json_start:json_end].strip()
                                results.append(json_content)
                                start_pos = end_idx + len(end_tag)
                                break
                            else:
                                # No matching end tag, skip this
                                start_pos = json_end
                                break
            else:
                # Couldn't find valid JSON, move past this start tag
                start_pos = json_start
                
        return results
    
    @classmethod
    def parse_tool_calls(cls, content: str) -> List[Dict[str, Any]]:
        """
        Extract tool calls from response content.
        
        Tool calls should be in the format:
        <TOOL>
        {
            "tool": "tool_name",
            "input": {
                "param1": "value1",
                "param2": "value2"
            }
        }
        </TOOL>
        
        Args:
            content: The response content to parse
            
        Returns:
            List of tool call dictionaries, each containing 'tool' and 'input'
            
        Raises:
            ParseError: If parsing fails
        """
        tool_calls = []
        
        # Find all TOOL tags using the improved extraction
        matches = cls._extract_json_between_tags(content, '<TOOL>', '</TOOL>')
        
        for json_content in matches:
            try:
                # JSON content is already extracted and cleaned
                json_content = json_content.strip()
                
                # Parse the JSON
                tool_data = json.loads(json_content)
                
                # Validate structure
                if not isinstance(tool_data, dict):
                    raise ParseError(f"Tool call must be a JSON object, got {type(tool_data)}")
                
                if "tool" not in tool_data:
                    raise ParseError("Tool call missing 'tool' field")
                
                if "input" not in tool_data:
                    raise ParseError("Tool call missing 'input' field")
                
                if not isinstance(tool_data["input"], dict):
                    raise ParseError(f"Tool input must be a dictionary, got {type(tool_data['input'])}")
                
                tool_calls.append({
                    "tool": tool_data["tool"],
                    "input": tool_data["input"]
                })
                
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping malformed tool call JSON: {e}")
                logger.debug(f"Content was: {json_content}")
                continue  # Skip malformed JSON and continue with next match
            except Exception as e:
                logger.warning(f"Skipping invalid tool call: {e}")
                logger.debug(f"Content was: {json_content}")
                continue  # Skip invalid tool calls and continue with next match
        
        return tool_calls
    
    @classmethod
    def parse_results(cls, content: str) -> List[Dict[str, Any]]:
        """
        Extract results from response content.
        
        Results should be in the format:
        <RESULT>
        {
            "key": "value",
            ...
        }
        </RESULT>
        
        Args:
            content: The response content to parse
            
        Returns:
            List of result dictionaries
            
        Raises:
            ParseError: If parsing fails
        """
        results = []
        
        # Find all RESULT tags using the improved extraction
        matches = cls._extract_json_between_tags(content, '<RESULT>', '</RESULT>')
        
        for json_content in matches:
            try:
                # JSON content is already extracted and cleaned
                json_content = json_content.strip()
                
                # Parse the JSON
                result_data = json.loads(json_content)
                
                # Results can be any valid JSON structure
                results.append(result_data)
                
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping malformed result JSON: {e}")
                logger.debug(f"Content was: {json_content}")
                continue  # Skip malformed JSON and continue with next match
            except Exception as e:
                logger.warning(f"Skipping invalid result: {e}")
                logger.debug(f"Content was: {json_content}")
                continue  # Skip invalid results and continue with next match
        
        return results
    
    @classmethod
    def extract_all(cls, content: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Extract both tool calls and results from content.
        
        Args:
            content: The response content to parse
            
        Returns:
            Tuple of (tool_calls, results)
        """
        tool_calls = cls.parse_tool_calls(content)
        results = cls.parse_results(content)
        return tool_calls, results
    
    @classmethod
    def has_tool_calls(cls, content: str) -> bool:
        """
        Check if content contains any tool calls.
        
        Args:
            content: The response content to check
            
        Returns:
            True if tool calls are present
        """
        return bool(cls.TOOL_PATTERN.search(content))
    
    @classmethod
    def has_results(cls, content: str) -> bool:
        """
        Check if content contains any results.
        
        Args:
            content: The response content to check
            
        Returns:
            True if results are present
        """
        return bool(cls.RESULT_PATTERN.search(content))
    
    @classmethod
    def remove_parsed_content(cls, content: str) -> str:
        """
        Remove all parsed tags from content, leaving only the text.
        
        This is useful for displaying the response to users without
        the structured data tags.
        
        Args:
            content: The response content
            
        Returns:
            Content with all tags removed
        """
        # Remove TOOL tags
        content = cls.TOOL_PATTERN.sub('', content)
        # Remove RESULT tags
        content = cls.RESULT_PATTERN.sub('', content)
        # Clean up extra whitespace
        content = re.sub(r'\n\s*\n', '\n\n', content)
        return content.strip()